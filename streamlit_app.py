import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import json
from datetime import datetime

# Librerías de Machine Learning
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

# =====================================================================
# CONFIGURACIÓN DE PÁGINA Y ESTILOS CSS
# =====================================================================
st.set_page_config(
    page_title="Dalia Pro Autonomous Agent v3.5",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #e2e8f0; }
    .metric-card {
        background-color: #1e293b;
        border-radius: 8px;
        padding: 15px;
        border: 1px solid #334155;
        margin-bottom: 10px;
    }
    .status-bullish { color: #22c55e; font-weight: bold; }
    .status-bearish { color: #ef4444; font-weight: bold; }
    .status-neutral { color: #eab308; font-weight: bold; }
    .roadmap-card {
        background: #1e293b;
        border-left: 4px solid #6366f1;
        padding: 15px;
        margin-bottom: 12px;
        border-radius: 0 8px 8px 0;
    }
</style>
""", unsafe_allow_html=True)

# Inicialización de Session State
if 'cash_balance' not in st.session_state:
    st.session_state['cash_balance'] = 100000.0
if 'paper_positions' not in st.session_state:
    st.session_state['paper_positions'] = []
if 'execution_log' not in st.session_state:
    st.session_state['execution_log'] = []

# =====================================================================
# 1. MOTOR DE PROCESAMIENTO DE DATOS & INDICADORES TÉCNICOS
# =====================================================================
@st.cache_data(ttl=60)
def obtener_datos(ticker, interval="5m", period="5d"):
    try:
        df = yf.download(ticker, period=period, interval=interval, progress=False)
        if df.empty:
            return pd.DataFrame()
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df = df.dropna().copy()
        
        # Indicadores Básicos
        df['EMA_200'] = df['Close'].ewm(span=200).mean()
        df['EMA_50'] = df['Close'].ewm(span=50).mean()
        
        # VWAP
        v = df['Volume']
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * v).cumsum() / (v.cumsum() + 1e-9)
        
        # RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))
        
        # ATR & Bollinger
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(14).mean()
        df['BB_Mid'] = df['Close'].rolling(20).mean()
        df['BB_Std'] = df['Close'].rolling(20).std()
        df['BB_Upper'] = df['BB_Mid'] + (2 * df['BB_Std'])
        df['BB_Lower'] = df['BB_Mid'] - (2 * df['BB_Std'])
        
        # ADX / DMI
        up_move = df['High'].diff()
        down_move = df['Low'].shift(1) - df['Low']
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        tr14 = df['TR'].rolling(14).sum()
        plus_di = 100 * (pd.Series(plus_dm).rolling(14).sum() / (tr14 + 1e-9))
        minus_di = 100 * (pd.Series(minus_dm).rolling(14).sum() / (tr14 + 1e-9))
        dx = 100 * (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
        
        df['Plus_DI'] = plus_di
        df['Minus_DI'] = minus_di
        df['ADX'] = dx.rolling(14).mean()
        
        # MACD
        ema12 = df['Close'].ewm(span=12).mean()
        ema26 = df['Close'].ewm(span=26).mean()
        df['MACD'] = ema12 - ema26
        df['MACD_Signal'] = df['MACD'].ewm(span=9).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # Point of Control (POC) aproximado
        prices = df['Close']
        volumes = df['Volume']
        bins = np.linspace(prices.min(), prices.max(), 30)
        hist, edge = np.histogram(prices, bins=bins, weights=volumes)
        df['POC'] = edge[np.argmax(hist)]
        
        return df.dropna()
    except Exception as e:
        st.error(f"Error descargando datos para {ticker}: {e}")
        return pd.DataFrame()

# =====================================================================
# 2. MÓDULO NLP SENTIMIENTO DE NOTICIAS DIARIAS
# =====================================================================
def obtener_sentimiento_noticias(ticker):
    try:
        palabras_alcistas = ['growth', 'record', 'profit', 'surpass', 'bullish', 'upgrade', 'buy', 'dividend', 'partnership']
        palabras_bajistas = ['loss', 'decline', 'lawsuit', 'bearish', 'downgrade', 'sell', 'inflation', 'drop', 'warning']
        
        ticker_obj = yf.Ticker(ticker)
        news_list = ticker_obj.news if hasattr(ticker_obj, 'news') else []
        
        if not news_list:
            return 0.0, "Sin noticias recientes disponibles"
        
        score_total = 0
        conteo = 0
        titulares_resumen = []
        
        for item in news_list[:5]:
            title = item.get('title', '')
            titulares_resumen.append(title)
            title_lower = title.lower()
            score_item = 0
            for w in palabras_alcistas:
                if w in title_lower: score_item += 0.25
            for w in palabras_bajistas:
                if w in title_lower: score_item -= 0.25
            score_total += score_item
            conteo += 1
            
        sentimiento_final = float(np.clip(score_total / max(conteo, 1), -1.0, 1.0))
        resumen_txt = titulares_resumen[0] if titulares_resumen else "Neutro"
        return sentimiento_final, resumen_txt
    except Exception:
        return 0.0, "API de noticias no disponible"

# =====================================================================
# 3. MOTOR DE MACHINE LEARNING ENTRENABLE EN TIEMPO REAL (5 AÑOS)
# =====================================================================
@st.cache_resource(ttl=3600)
def entrenar_modelo_ia_5y(ticker):
    df = yf.download(ticker, period="5y", interval="1d", progress=False)
    if df.empty or len(df) < 200:
        return None, 0.0, []

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df['Returns'] = df['Close'].pct_change()
    df['EMA_50'] = df['Close'].ewm(span=50).mean()
    df['EMA_200'] = df['Close'].ewm(span=200).mean()
    df['Dist_EMA50'] = (df['Close'] - df['EMA_50']) / (df['EMA_50'] + 1e-9)
    df['Dist_EMA200'] = (df['Close'] - df['EMA_200']) / (df['EMA_200'] + 1e-9)
    df['Volatilidad'] = df['Returns'].rolling(window=20).std()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))

    df['Target'] = np.where(df['Close'].shift(-1) > df['Close'], 1, 0)
    df = df.dropna()

    features = ['Dist_EMA50', 'Dist_EMA200', 'Volatilidad', 'RSI', 'Returns']
    X = df[features]
    y = df['Target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    model = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    return model, accuracy, features

def evaluar_ia_y_sentimiento(ticker, df_actual):
    model, accuracy, feature_names = entrenar_modelo_ia_5y(ticker)
    sentimiento_noticias, titular = obtener_sentimiento_noticias(ticker)
    
    if model is None or df_actual.empty:
        return 50.0, 0.50, sentimiento_noticias, titular, "Modelo Indisponible"

    c_close = float(df_actual['Close'].iloc[-1])
    c_ema50 = float(df_actual['EMA_50'].iloc[-1])
    c_ema200 = float(df_actual['EMA_200'].iloc[-1])
    
    dist_ema50 = (c_close - c_ema50) / (c_ema50 + 1e-9)
    dist_ema200 = (c_close - c_ema200) / (c_ema200 + 1e-9)
    ret = float(df_actual['Close'].pct_change().iloc[-1])
    vol = float(df_actual['Close'].pct_change().rolling(20).std().iloc[-1]) if len(df_actual) >= 20 else 0.01
    rsi = float(df_actual['RSI'].iloc[-1])

    x_live = pd.DataFrame([[dist_ema50, dist_ema200, vol, rsi, ret]], columns=feature_names)
    prob_ml_pure = float(model.predict_proba(x_live)[0][1] * 100.0)

    # Combinación: 85% Modelo ML Técnico + 15% Sentimiento de Noticias
    ajuste_news = sentimiento_noticias * 15.0
    prob_final = np.clip(prob_ml_pure + ajuste_news, 10.0, 95.0)

    return float(prob_final), float(accuracy), sentimiento_noticias, titular, "Modelo Calibrado (5Y)"

# =====================================================================
# 4. MOTOR DE BACKTESTING HISTÓRICO 5Y
# =====================================================================
def ejecutar_backtest(df):
    if df.empty or len(df) < 50:
        return pd.DataFrame(), {}
    
    bt_df = df.copy()
    bt_df['Signal'] = np.where((bt_df['Close'] > bt_df['EMA_200']) & (bt_df['RSI'] < 45), 1, 
                       np.where((bt_df['Close'] < bt_df['EMA_200']) & (bt_df['RSI'] > 55), -1, 0))
    
    bt_df['Market_Return'] = bt_df['Close'].pct_change()
    bt_df['Strategy_Return'] = bt_df['Signal'].shift(1) * bt_df['Market_Return']
    
    bt_df['Equity_Market'] = (1 + bt_df['Market_Return'].fillna(0)).cumprod() * 10000
    bt_df['Equity_Strategy'] = (1 + bt_df['Strategy_Return'].fillna(0)).cumprod() * 10000
    
    win_trades = bt_df[bt_df['Strategy_Return'] > 0]
    loss_trades = bt_df[bt_df['Strategy_Return'] < 0]
    
    win_rate = (len(win_trades) / max(len(win_trades) + len(loss_trades), 1)) * 100
    profit_factor = win_trades['Strategy_Return'].sum() / abs(loss_trades['Strategy_Return'].sum() + 1e-9)
    max_drawdown = ((bt_df['Equity_Strategy'].cummax() - bt_df['Equity_Strategy']) / (bt_df['Equity_Strategy'].cummax() + 1e-9)).max() * 100
    
    stats = {
        "Win Rate": f"{win_rate:.1f}%",
        "Profit Factor": f"{profit_factor:.2f}",
        "Max Drawdown": f"{max_drawdown:.2f}%",
        "Retorno Final": f"${bt_df['Equity_Strategy'].iloc[-1]:,.2f}"
    }
    
    return bt_df, stats

# =====================================================================
# 5. FUNCIONES DE INTERFAZ BROKERS & HARDWARE
# =====================================================================
def emitir_alerta_sonora(tipo="chime", titulo="Notificación", mensaje="Alerta de Sistema"):
    js_code = f"""
    <script>
        function playSound() {{
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            
            if ("{tipo}" === "alarma") {{
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(880, ctx.currentTime);
                osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.3);
            }} else {{
                osc.type = 'sine';
                osc.frequency.setValueAtTime(587.33, ctx.currentTime);
                osc.frequency.setValueAtTime(880, ctx.currentTime + 0.1);
            }}
            
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + 0.4);
            osc.start();
            osc.stop(ctx.currentTime + 0.4);
            
            if ("vibrate" in navigator) {{
                navigator.vibrate([200, 100, 200]);
            }}
        }}
        playSound();
    </script>
    """
    st.components.v1.html(js_code, height=0)
    st.toast(f"{titulo}: {mensaje}", icon="⚡")

def ejecutar_orden_alpaca(symbol, qty, side, order_type="market", take_profit=None, stop_loss=None):
    base_url = "https://paper-api.alpaca.markets" if "Paper" in st.session_state.get("alpaca_env", "Paper") else "https://api.alpaca.markets"
    headers = {
        "APCA-API-KEY-ID": st.session_state.get("alpaca_key", ""),
        "APCA-API-SECRET-KEY": st.session_state.get("alpaca_secret", ""),
        "Content-Type": "application/json"
    }
    payload = {
        "symbol": symbol,
        "qty": qty,
        "side": side.lower(),
        "type": order_type,
        "time_in_force": "gtc"
    }
    if take_profit and stop_loss:
        payload["order_class"] = "bracket"
        payload["take_profit"] = {"limit_price": round(take_profit, 2)}
        payload["stop_loss"] = {"stop_price": round(stop_loss, 2)}
        
    try:
        res = requests.post(f"{base_url}/v2/orders", json=payload, headers=headers, timeout=10)
        if res.status_code in [200, 201]:
            return True, res.json()
        else:
            return False, f"Error {res.status_code}: {res.text}"
    except Exception as e:
        return False, str(e)

def ejecutar_orden_tradingview(symbol, qty, side, price):
    webhook_url = st.session_state.get("tv_url", "")
    if not webhook_url:
        return False, "URL de Webhook no configurada."
        
    payload = {
        "passphrase": st.session_state.get("tv_pass", ""),
        "ticker": symbol,
        "action": side.lower(),
        "quantity": qty,
        "price": price,
        "timestamp": datetime.now().isoformat()
    }
    try:
        res = requests.post(webhook_url, json=payload, headers={"Content-Type": "application/json"}, timeout=8)
        if res.status_code in [200, 201, 202]:
            return True, "Payload enviado al Webhook exitosamente."
        else:
            return False, f"Respuesta servidor: {res.status_code}"
    except Exception as e:
        return False, str(e)

def ejecutar_orden_robinhood(symbol, qty, side):
    try:
        import robin_stocks.robinhood as r
        user = st.session_state.get("rh_user", "")
        password = st.session_state.get("rh_pass", "")
        if not user or not password:
            return False, "Credenciales de Robinhood incompletas."
        r.login(user, password, expiresIn=86400, by_sms=True)
        res = r.orders.order_buy_market(symbol, qty) if side.lower() == "buy" else r.orders.order_sell_market(symbol, qty)
        r.logout()
        return True, res
    except Exception as e:
        return False, f"Error Robinhood: {str(e)}"

# =====================================================================
# 6. DIÁLOGO MODAL HITL CON VALIDACIÓN DE SALDO
# =====================================================================
@st.dialog("⚠️ CONFIRMACIÓN DE EJECUCIÓN DE ORDEN")
def modal_confirmacion_orden(ticker, accion, cantidad, precio, stop_loss, take_profit, broker):
    costo_total = cantidad * precio
    saldo_actual = st.session_state['cash_balance']
    
    st.markdown(f"### Detalle de la Operación - {ticker}")
    st.write(f"* **Acción:** {accion}")
    st.write(f"* **Cantidad:** `{cantidad} acciones` @ `${precio:.2f}`")
    st.write(f"* **Costo Total Estimado:** `${costo_total:,.2f}`")
    st.write(f"* **Take Profit:** `${take_profit:.2f}` | **Stop Loss:** `${stop_loss:.2f}`")
    st.write(f"* **Broker Destino:** `{broker}`")
    
    st.markdown("---")
    st.write(f"**Saldo Disponible en Cuenta:** `${saldo_actual:,.2f}`")
    
    if costo_total > saldo_actual and "Paper" in broker:
        st.error("❌ SALDO INSUFICIENTE: El margen requerido supera el capital disponible en tu cuenta Paper Trading.")
        if st.button("Cerrar"):
            st.rerun()
        return

    confirm_check = st.checkbox("Confirmo la revisión de riesgo y autorizo el envío de la orden.")
    
    c1, c2 = st.columns(2)
    if c1.button("✅ EJECUTAR ORDEN AHORA", disabled=not confirm_check, type="primary"):
        side = "buy" if "BUY" in accion or "CALL" in accion else "sell"
        éxito = False
        respuesta = ""
        
        with st.spinner("Conectando con la API del Broker..."):
            if "Alpaca" in broker:
                éxito, respuesta = ejecutar_orden_alpaca(ticker, cantidad, side, take_profit=take_profit, stop_loss=stop_loss)
            elif "TradingView" in broker:
                éxito, respuesta = ejecutar_orden_tradingview(ticker, cantidad, side, precio)
            elif "Robinhood" in broker:
                éxito, respuesta = ejecutar_orden_robinhood(ticker, cantidad, side)
            else: # Paper Engine Local
                éxito = True
                respuesta = {"id": f"PAPER-{datetime.now().strftime('%H%M%S')}", "status": "FILLED"}
                st.session_state['cash_balance'] -= costo_total

        if éxito:
            emitir_alerta_sonora("chime", "Orden Ejecutada", f"{accion} en {ticker}")
            st.session_state['execution_log'].append({
                "Hora": datetime.now().strftime("%H:%M:%S"),
                "Ticker": ticker,
                "Acción": accion,
                "Precio": f"${precio:.2f}",
                "Cantidad": cantidad,
                "Broker": broker,
                "Estado": "FILLED"
            })
            st.success("¡Orden ejecutada y registrada correctamente!")
            st.rerun()
        else:
            st.error(f"Fallo en la ejecución: {respuesta}")

    if c2.button("❌ Cancelar"):
        st.rerun()

# =====================================================================
# 7. BARRA LATERAL & METRICAS DE CONTROL
# =====================================================================
with st.sidebar:
    st.title("⚡ Dalia Pro v3.5")
    st.caption("Engine Cuantitativo & Autonomous Agent HITL")
    
    ticker_input = st.text_input("Ticker del Activo", value="AAPL").upper()
    timeframe = st.selectbox("Temporalidad Intradiaria", ["1m", "5m", "15m", "1h", "1d"], index=1)
    
    st.markdown("---")
    st.subheader("🛡️ Gestión de Riesgo (HITL)")
    account_capital = st.number_input("Capital Cuenta ($)", value=st.session_state['cash_balance'], step=5000.0)
    max_risk_pct = st.slider("Riesgo por Operación (%)", 0.5, 3.0, 1.0, 0.1)

    with st.expander("🔑 Credenciales de Brokers", expanded=False):
        st.text_input("Alpaca API Key", type="password", key="alpaca_key")
        st.text_input("Alpaca Secret Key", type="password", key="alpaca_secret")
        st.radio("Entorno Alpaca", ["Paper (Simulado)", "Live (Real)"], key="alpaca_env")
        st.text_input("Webhook URL (TradingView)", key="tv_url")
        st.text_input("Passphrase Webhook", type="password", key="tv_pass")
        st.text_input("Robinhood Email", key="rh_user")
        st.text_input("Robinhood Password", type="password", key="rh_pass")

df_ticker = obtener_datos(ticker_input, interval=timeframe)

if df_ticker.empty:
    st.error(f"No se pudieron cargar datos para {ticker_input}. Revisa la conexión o el Ticker.")
    st.stop()

# Evaluación de IA Entrenada + Noticias
prob_final, accuracy_5y, sentiment_news, news_headline, model_status = evaluar_ia_y_sentimiento(ticker_input, df_ticker)

# Cálculo de Posición HITL
c_price = float(df_ticker['Close'].iloc[-1])
c_atr = float(df_ticker['ATR'].iloc[-1])
risk_amount = account_capital * (max_risk_pct / 100.0)
stop_distance = c_atr * 1.5
shares_to_trade = int(risk_amount / stop_distance) if stop_distance > 0 else 1

st.sidebar.markdown("---")
st.sidebar.metric("Posición Sugerida", f"{shares_to_trade} Acciones")
st.sidebar.caption(f"Stop Loss estimado: ${c_price - stop_distance:.2f} (-1.5x ATR)")

# =====================================================================
# 8. PANEL PRINCIPAL & PESTAÑAS DIVERSIFICADAS
# =====================================================================
st.title(f"📊 Dashboard de Operaciones: {ticker_input}")

(tab_chart, tab_ml, tab_options, tab_montecarlo, 
 tab_backtest, tab_radar, tab_hardware, tab_journal, tab_roadmap) = st.tabs([
    "📈 Gráfico & Confluencia",
    "🧠 IA ML & Noticias NLP",
    "🎯 Opciones & GEX",
    "🎲 Monte Carlo & VaR",
    "📜 Backtesting 5Y",
    "👁️ Radar MTF",
    "🔊 Alertas Hardware",
    "📒 Diario & Cartera",
    "🗺️ Roadmap"
])

# ---------------------------------------------------------------------
# PESTAÑA 1: GRÁFICO & CONFLUENCIA TÉCNICA
# ---------------------------------------------------------------------
with tab_chart:
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.6, 0.2, 0.2])
    
    fig.add_trace(go.Candlestick(x=df_ticker.index, open=df_ticker['Open'], high=df_ticker['High'], low=df_ticker['Low'], close=df_ticker['Close'], name="Precio"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ticker.index, y=df_ticker['EMA_200'], line=dict(color='orange', width=1.5), name="EMA 200"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df_ticker.index, y=df_ticker['VWAP'], line=dict(color='cyan', width=1.5), name="VWAP"), row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df_ticker.index, y=df_ticker['RSI'], line=dict(color='purple', width=1.5), name="RSI"), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)
    
    fig.add_trace(go.Bar(x=df_ticker.index, y=df_ticker['MACD_Hist'], name="MACD Hist"), row=3, col=1)
    
    fig.update_layout(template="plotly_dark", height=600, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------
# PESTAÑA 2: IA ML REAL ENTRENADA & CONTROL HITL
# ---------------------------------------------------------------------
with tab_ml:
    st.subheader("🧠 Motor de Inferencia Estadístico ML & Sentimiento")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Probabilidad Modelo ML + NLP", f"{prob_final:.1f}%")
        status_txt = "🟢 CALL / ALCISTA" if prob_final >= 60 else ("🔴 PUT / BAJISTA" if prob_final <= 40 else "🟡 NEUTRO")
        st.markdown(f"**Sesgo Sugerido:** {status_txt}")
        
    with col2:
        st.metric("Precisión Histórica ML (5Y Out-of-Sample)", f"{accuracy_5y*100:.1f}%")
        st.caption(f"Estado del Modelo: {model_status}")
        
    with col3:
        st.metric("Score Sentimiento Noticias", f"{sentiment_news:+.2f}")
        st.caption(f"Titular: {news_headline[:50]}...")
        
    st.markdown("---")
    st.markdown("### ⚡ Panel de Control Operativo HITL")
    
    m_col1, m_col2 = st.columns(2)
    broker_seleccionado = m_col1.selectbox(
        "Seleccionar Broker de Ejecución",
        ["Paper Trading Engine Local", "Alpaca Markets (API)", "TradingView Webhook", "Robinhood (API)"]
    )
    
    tp_target = c_price + (c_atr * 3.0) if prob_final >= 50 else c_price - (c_atr * 3.0)
    sl_target = c_price - (c_atr * 1.5) if prob_final >= 50 else c_price + (c_atr * 1.5)
    accion_sugerida = "BUY CALL (COMPRA)" if prob_final >= 50 else "BUY PUT (VENTA)"
    
    if m_col2.button("🚨 ABRIR MODAL DE CONFIRMACIÓN DE ORDEN", type="primary"):
        modal_confirmacion_orden(
            ticker=ticker_input,
            accion=accion_sugerida,
            cantidad=shares_to_trade,
            precio=c_price,
            stop_loss=sl_target,
            take_profit=tp_target,
            broker=broker_seleccionado
        )

# ---------------------------------------------------------------------
# PESTAÑA 3: OPCIONES & MAX PAIN
# ---------------------------------------------------------------------
with tab_options:
    st.subheader("🎯 Cadena de Opciones & Estructura de Volatilidad")
    try:
        tk_obj = yf.Ticker(ticker_input)
        expirations = tk_obj.expirations
        if expirations:
            exp_selected = st.selectbox("Fecha de Vencimiento Opciones", expirations[:4])
            opt_chain = tk_obj.option_chain(exp_selected)
            calls = opt_chain.calls[['strike', 'openInterest']].rename(columns={'openInterest': 'Call_OI'})
            puts = opt_chain.puts[['strike', 'openInterest']].rename(columns={'openInterest': 'Put_OI'})
            
            merged_opts = pd.merge(calls, puts, on='strike', how='inner').fillna(0)
            
            fig_opt = go.Figure()
            fig_opt.add_trace(go.Bar(x=merged_opts['strike'], y=merged_opts['Call_OI'], name="Call Open Interest", marker_color='green'))
            fig_opt.add_trace(go.Bar(x=merged_opts['strike'], y=merged_opts['Put_OI'], name="Put Open Interest", marker_color='red'))
            fig_opt.update_layout(barmode='group', template="plotly_dark", height=400, title="Distribución de Open Interest por Strike")
            st.plotly_chart(fig_opt, use_container_width=True)
        else:
            st.warning("No se encontraron cadenas de opciones activas para este activo.")
    except Exception:
        st.info("Cadena de opciones no disponible para este ticker.")

# ---------------------------------------------------------------------
# PESTAÑA 4: MONTE CARLO & VAR
# ---------------------------------------------------------------------
with tab_montecarlo:
    st.subheader("🎲 Proyección Monte Carlo & Value at Risk (VaR 95%)")
    returns = df_ticker['Close'].pct_change().dropna()
    mu = returns.mean()
    sigma = returns.std()
    
    simulations = 100
    days = 30
    simulation_results = np.zeros((days, simulations))
    
    for i in range(simulations):
        prices = [c_price]
        for _ in range(days - 1):
            prices.append(prices[-1] * (1 + np.random.normal(mu, sigma)))
        simulation_results[:, i] = prices
        
    fig_mc = go.Figure()
    for i in range(simulations):
        fig_mc.add_trace(go.Scatter(y=simulation_results[:, i], mode='lines', line=dict(width=0.5), showlegend=False))
    fig_mc.update_layout(template="plotly_dark", height=400, title="100 Rutas Simuladas (Próximas 30 Velas)")
    st.plotly_chart(fig_mc, use_container_width=True)
    
    final_prices = simulation_results[-1, :]
    var_95 = np.percentile(final_prices, 5)
    st.metric("Value at Risk (VaR 95% Limite Inferior Proyectado)", f"${var_95:.2f}")

# ---------------------------------------------------------------------
# PESTAÑA 5: BACKTESTING HISTÓRICO
# ---------------------------------------------------------------------
with tab_backtest:
    st.subheader("📜 Backtesting de Estrategia Cuantitativa (5 Años Históricos)")
    df_5y = yf.download(ticker_input, period="5y", interval="1d", progress=False)
    if isinstance(df_5y.columns, pd.MultiIndex):
        df_5y.columns = df_5y.columns.get_level_values(0)
        
    df_5y['EMA_200'] = df_5y['Close'].ewm(span=200).mean()
    delta_5y = df_5y['Close'].diff()
    gain_5y = (delta_5y.where(delta_5y > 0, 0)).rolling(14).mean()
    loss_5y = (-delta_5y.where(delta_5y < 0, 0)).rolling(14).mean()
    rs_5y = gain_5y / (loss_5y + 1e-9)
    df_5y['RSI'] = 100 - (100 / (1 + rs_5y))
    
    bt_res, stats = ejecutar_backtest(df_5y)
    
    if not bt_res.empty:
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        b_col1.metric("Win Rate", stats["Win Rate"])
        b_col2.metric("Profit Factor", stats["Profit Factor"])
        b_col3.metric("Max Drawdown", stats["Max Drawdown"])
        b_col4.metric("Capital Final Est.", stats["Retorno Final"])
        
        fig_bt = go.Figure()
        fig_bt.add_trace(go.Scatter(x=bt_res.index, y=bt_res['Equity_Strategy'], name="Estrategia Dalia", line=dict(color='indigo', width=2)))
        fig_bt.add_trace(go.Scatter(x=bt_res.index, y=bt_res['Equity_Market'], name="Buy & Hold Mercado", line=dict(color='gray', dash='dash')))
        fig_bt.update_layout(template="plotly_dark", height=400, title="Curva de Equidad ($10,000 Iniciales)")
        st.plotly_chart(fig_bt, use_container_width=True)

# ---------------------------------------------------------------------
# PESTAÑA 6: RADAR SCREENER MTF
# ---------------------------------------------------------------------
with tab_radar:
    st.subheader("👁️ Auto-Screener Radar MTF Multi-Activo")
    radar_tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "SPY", "QQQ"]
    
    if st.button("🔄 Ejecutar Escáner Multi-Activo"):
        radar_results = []
        prog_bar = st.progress(0)
        for idx, t_sym in enumerate(radar_tickers):
            df_t = obtener_datos(t_sym, "5m")
            if not df_t.empty:
                c_p = float(df_t['Close'].iloc[-1])
                ema_p = float(df_t['EMA_200'].iloc[-1])
                rsi_p = float(df_t['RSI'].iloc[-1])
                bias_p = "🟢 CALL" if c_p > ema_p else "🔴 PUT"
                radar_results.append({
                    "Ticker": t_sym,
                    "Precio": f"${c_p:.2f}",
                    "Sesgo 5m": bias_p,
                    "RSI": f"{rsi_p:.1f}",
                    "Estado": "⚡ En Tendencia" if rsi_p > 60 or rsi_p < 40 else "💤 Consolidación"
                })
            prog_bar.progress((idx + 1) / len(radar_tickers))
        st.table(pd.DataFrame(radar_results))

# ---------------------------------------------------------------------
# PESTAÑA 7: HARDWARE ALERTAS
# ---------------------------------------------------------------------
with tab_hardware:
    st.subheader("🔊 Módulo de Alertas Hardware Directas")
    h_col1, h_col2, h_col3 = st.columns(3)
    if h_col1.button("🔔 Probar Chime Ejecución"):
        emitir_alerta_sonora("chime", "⚡ Orden Ejecutada", "Prueba de tono de confirmación.")
    if h_col2.button("🚨 Probar Alarma Institucional"):
        emitir_alerta_sonora("alarma", "🚨 Alerta Crítica", "Prueba de tono de alta prioridad.")
    if h_col3.button("🎵 Probar Tono Genérico"):
        emitir_alerta_sonora("info", "ℹ️ Notificación Dalia", "Prueba de tono estándar.")

# ---------------------------------------------------------------------
# PESTAÑA 8: DIARIO, CARTERA & CORRELACIÓN
# ---------------------------------------------------------------------
with tab_journal:
    st.subheader("📒 Diario de Operaciones & Análisis de Riesgo de Cartera")
    j_col1, j_col2 = st.columns(2)
    
    with j_col1:
        st.markdown("### 📊 Balance de Cuenta Paper Trading")
        st.metric("Balance Disponible", f"${st.session_state['cash_balance']:,.2f}")
        st.metric("Posiciones Activas Log", len(st.session_state['execution_log']))
        
    with j_col2:
        st.markdown("### 📜 Historial de Ejecuciones")
        if st.session_state['execution_log']:
            st.dataframe(pd.DataFrame(st.session_state['execution_log']))
        else:
            st.info("No hay registros de ejecuciones en esta sesión.")
            
    st.markdown("---")
    st.markdown("### 🔗 Matriz de Correlación Multi-Activo (Riesgo Sistémico)")
    df_corr = yf.download(radar_tickers, period="1mo", interval="1d", progress=False)['Close']
    if not df_corr.empty:
        corr_matrix = df_corr.corr()
        fig_corr = go.Figure(data=go.Heatmap(z=corr_matrix.values, x=corr_matrix.columns, y=corr_matrix.index, colorscale='Viridis'))
        fig_corr.update_layout(template="plotly_dark", height=400, title="Matriz de Correlación de Retornos Diarios")
        st.plotly_chart(fig_corr, use_container_width=True)

# ---------------------------------------------------------------------
# PESTAÑA 9: ROADMAP TECNOLÓGICO
# ---------------------------------------------------------------------
with tab_roadmap:
    st.subheader("🗺️ Hoja de Ruta Tecnológica Dalia Pro Engine")
    st.markdown("""
        <div class="roadmap-card">
            <h3 style="color:#a5b4fc; margin-top:0;">🚀 Fase 1: Integración Fix API & IBKR TWS Bridge</h3>
            <p style="color:#cbd5e1;">Conexión directa vía sockets TCP/FIX para transmisión sub-milisegundo de órdenes bracket.</p>
        </div>
        <div class="roadmap-card">
            <h3 style="color:#a5b4fc; margin-top:0;">🧠 Fase 2: Redes Neuronales LSTM & Transformer Signal Engine</h3>
            <p style="color:#cbd5e1;">Implementación de aprendizaje profundo supervisado para predicción de volatilidad implícita en 0DTE.</p>
        </div>
        <div class="roadmap-card">
            <h3 style="color:#a5b4fc; margin-top:0;">🌐 Fase 3: Cluster Multi-Agente Distribuido</h3>
            <p style="color:#cbd5e1;">Despliegue de agentes autónomos especializados coordinados por consenso síncrono.</p>
        </div>
    """, unsafe_allow_html=True)
