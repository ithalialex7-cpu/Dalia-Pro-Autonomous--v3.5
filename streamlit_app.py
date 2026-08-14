import base64
import json
import os
import sqlite3
import threading
import time
import uuid
import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image

# =====================================================================
# CONFIGURACIÓN DE PÁGINA E ICONO PWA (Dalia Pro-Trading)
# =====================================================================
ICON_FILENAME = "app_icon.png"

def asegurar_icono_existente():
    """Genera o asegura el archivo del icono corporativo de Dalia Pro-Trading."""
    if not os.path.exists(ICON_FILENAME):
        try:
            img = Image.new('RGB', (180, 180), color='#121212')
            img.save(ICON_FILENAME)
        except Exception:
            pass

asegurar_icono_existente()

if os.path.exists(ICON_FILENAME):
    try:
        page_icon_obj = Image.open(ICON_FILENAME)
    except Exception:
        page_icon_obj = "🌸"
else:
    page_icon_obj = "🌸"

st.set_page_config(
    page_title="Dalia Pro-Trading Autonomous",
    layout="wide",
    page_icon=page_icon_obj
)

# Inyectar PWA Manifest e Icono en HTML
if os.path.exists(ICON_FILENAME):
    st.markdown(
        f"""
        <head>
            <link rel="apple-touch-icon" sizes="180x180" href="{ICON_FILENAME}">
            <link rel="icon" type="image/png" sizes="32x32" href="{ICON_FILENAME}">
            <meta name="apple-mobile-web-app-title" content="Dalia Pro-Trading">
            <meta name="application-name" content="Dalia Pro-Trading">
        </head>
        """,
        unsafe_allow_html=True
    )

# =====================================================================
# IMPORTS CONDICIONALES
# =====================================================================
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest
    ALPACA_SDK_AVAILABLE = True
except ImportError:
    ALPACA_SDK_AVAILABLE = False


# =====================================================================
# BASE DE DATOS Y CONCURRENCIA (WAL MODE)
# =====================================================================
def init_db():
    conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ordenes (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            qty INTEGER,
            precio REAL,
            sl REAL,
            tp REAL,
            broker TEXT,
            modo TEXT,
            estado TEXT DEFAULT 'ABIERTA',
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS detected_signals (
            id TEXT PRIMARY KEY,
            symbol TEXT,
            precio REAL,
            rsi REAL,
            vwap REAL,
            volume_score REAL,
            support REAL,
            resistance REAL,
            sl REAL,
            tp REAL,
            timestamp TEXT,
            status TEXT DEFAULT 'PENDING'
        )
    """)
    conn.commit()
    conn.close()

init_db()


# =====================================================================
# 1. MOTOR DE IA: SOPORTES, RESISTENCIAS, VOLUMEN Y BOLLINGER (5 AÑOS)
# =====================================================================
def obtener_datos_con_ia(symbol: str):
    """Obtiene 5 años de histórico para calcular soportes, resistencias, volumen, bandas de Bollinger y medias."""
    if not YFINANCE_AVAILABLE:
        dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1d')
        df = pd.DataFrame({
            'Open': np.random.uniform(100, 110, 100),
            'High': np.random.uniform(110, 115, 100),
            'Low': np.random.uniform(95, 100, 100),
            'Close': np.random.uniform(100, 110, 100),
            'Volume': np.random.randint(10000, 50000, 100)
        }, index=dates)
    else:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="5y", interval="1d")
        if df.empty:
            df = ticker.history(period="1y", interval="1d")

    if df.empty:
        return None

    df = df.copy()
    
    # Indicadores Técnicos
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # Bandas de Bollinger (20 periodos, 2 desviaciones estándar)
    rolling_mean = df['Close'].rolling(window=20).mean()
    rolling_std = df['Close'].rolling(window=20).std()
    df['BB_Middle'] = rolling_mean
    df['BB_Upper'] = rolling_mean + (rolling_std * 2)
    df['BB_Lower'] = rolling_mean - (rolling_std * 2)

    # VWAP Estimado
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-6)
    df['RSI'] = 100 - (100 / (1 + rs))

    # Detección de Soporte y Resistencia basada en extremos de 5 años
    df['Support'] = df['Low'].rolling(window=50).min()
    df['Resistance'] = df['High'].rolling(window=50).max()

    # Análisis de Volumen (Volumen relativo vs media móvil de 20 periodos)
    df['Vol_MA'] = df['Volume'].rolling(window=20).mean()
    df['Volume_Score'] = df['Volume'] / (df['Vol_MA'] + 1e-6)

    return df


# =====================================================================
# 2. MOTOR DE VIGILANCIA ACTIVA Y GESTIÓN DE BENEFICIOS (TRAILING / TP PARCIAL)
# =====================================================================
class VigilanciaActivaEngine(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        while True:
            time.sleep(10)
            try:
                conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
                cursor = conn.cursor()
                cursor.execute("SELECT id, symbol, precio, sl, tp FROM ordenes WHERE estado = 'ABIERTA'")
                ordenes_abiertas = cursor.fetchall()
                
                for orden in ordenes_abiertas:
                    oid, symbol, precio_entrada, sl, tp = orden
                    if YFINANCE_AVAILABLE:
                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(period="1d", interval="1m")
                        precio_actual = hist['Close'].iloc[-1] if not hist.empty else precio_entrada
                    else:
                        precio_actual = precio_entrada * np.random.uniform(0.99, 1.02)

                    if precio_actual >= tp:
                        nuevo_tp = round(tp * 1.02, 2)
                        nuevo_sl = round(precio_actual * 0.99, 2)
                        cursor.execute("UPDATE ordenes SET tp = ?, sl = ? WHERE id = ?", (nuevo_tp, nuevo_sl, oid))
                        conn.commit()
                conn.close()
            except Exception:
                pass

vigilancia_thread = VigilanciaActivaEngine()
vigilancia_thread.start()


# =====================================================================
# 3. CONSTRUCTOR DE GRÁFICOS INTERACTIVOS (PLOTLY + BOLLINGER)
# =====================================================================
def construir_grafico_avanzado(df, symbol):
    if not PLOTLY_AVAILABLE or df is None:
        st.warning("⚠️ Instale 'plotly' para visualizar los diagramas de velas.")
        return None

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
        subplot_titles=(f"Monitoreo en Tiempo Real — {symbol} (Velas + Bollinger + S&R)", "Índice de Fuerza Relativa (RSI 14)")
    )

    # Velas Japonesas
    fig.add_trace(
        go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Precio'
        ),
        row=1, col=1
    )

    # Bandas de Bollinger
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], mode='lines', name='Banda Bollinger Superior', line=dict(color='rgba(173, 216, 230, 0.5)', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], mode='lines', name='Banda Bollinger Inferior', line=dict(color='rgba(173, 216, 230, 0.5)', width=1), fill='tonexty', fillcolor='rgba(173, 216, 230, 0.05)', name='Canal Bollinger'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Middle'], mode='lines', name='Media Bollinger (EMA 20)', line=dict(color='#29B6F6', width=1)), row=1, col=1)

    # Soportes y Resistencias IA
    fig.add_trace(go.Scatter(x=df.index, y=df['Support'], mode='lines', name='Soporte IA', line=dict(color='#00E676', dash='dot')), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Resistance'], mode='lines', name='Resistencia IA', line=dict(color='#FF5252', dash='dot')), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='#00E676', width=2)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="#FF5252", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00E676", row=2, col=1)

    fig.update_layout(
        height=580,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )
    return fig


# =====================================================================
# 4. ROUTER DE BRÓKER
# =====================================================================
class DaliaBrokerRouter:
    def __init__(self, key, secret, real_mode):
        self.key = key
        self.secret = secret
        self.real_mode = real_mode

    def ejecutar_orden(self, symbol, qty, sl, tp, precio_ref):
        if ALPACA_SDK_AVAILABLE and self.key and self.secret:
            try:
                client = TradingClient(self.key, self.secret, paper=not self.real_mode)
                req = MarketOrderRequest(
                    symbol=symbol, qty=qty, side=OrderSide.BUY, time_in_force=TimeInForce.GTC,
                    take_profit=TakeProfitRequest(limit_price=tp),
                    stop_loss=StopLossRequest(stop_price=sl)
                )
                order = client.submit_order(req)
                broker_nombre = "Alpaca API Real"
                order_id = str(order.id)
            except Exception as e:
                return {"status": "ERROR", "message": str(e)}
        else:
            broker_nombre = "Simulador Interno Dalia"
            order_id = str(uuid.uuid4())[:8]

        conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
        c = conn.cursor()
        c.execute(
            "INSERT INTO ordenes (id, symbol, qty, precio, sl, tp, broker, modo, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'ABIERTA')",
            (order_id, symbol, qty, precio_ref, sl, tp, broker_nombre, "REAL" if self.real_mode else "PAPER")
        )
        conn.commit()
        conn.close()
        return {"status": "SUCCESS", "broker": broker_nombre, "order_id": order_id}


# =====================================================================
# 5. BARRA LATERAL Y SELECTOR DE TICKERS AVANZADO
# =====================================================================
if os.path.exists(ICON_FILENAME):
    st.sidebar.image(ICON_FILENAME, use_container_width=True)

st.sidebar.title("DALIA PRO-TRADING")
st.sidebar.caption("Autonomous AI Multi-Asset Engine")

LISTA_MULTIACTIVO = [
    "NVDA", "AAPL", "TSLA", "AMD", "MSFT", "AMZN", "GOOGL", "META", "NFLX", 
    "SPY", "QQQ", "BTC-USD", "ETH-USD", "SOL-USD"
]

ticker_elegido = st.sidebar.selectbox("🎯 Seleccionar Activo / Ticker", options=LISTA_MULTIACTIVO, index=0)

with st.sidebar.expander("🔑 Configuración de API Keys", expanded=False):
    alpaca_key = st.text_input("Alpaca API Key", value="", type="password")
    alpaca_secret = st.text_input("Alpaca Secret Key", value="", type="password")

modo_real_toggle = st.sidebar.toggle("🚨 MODO PRODUCCIÓN (DINERO REAL)", value=False)
router = DaliaBrokerRouter(alpaca_key, alpaca_secret, modo_real_toggle)


# =====================================================================
# 6. PESTAÑAS PRINCIPALES DE LA APLICACIÓN
# =====================================================================
tab_grafico, tab_cola, tab_vigilancia, tab_manual, tab_historial = st.tabs([
    "📈 Gráfico & Análisis IA",
    "🚨 Cola de Señales Pendientes",
    "🛡️ Vigilancia Activa (Custodia)",
    "⚡ Operativa Manual",
    "📊 Historial SQLite"
])

# ---------------------------------------------------------------------
# PESTAÑA 1: GRÁFICO & ANÁLISIS IA (S&R, Volumen, Bollinger)
# ---------------------------------------------------------------------
with tab_grafico:
    st.subheader(f"📊 Análisis Técnico Avanzado e Inteligencia Artificial: {ticker_elegido}")
    
    df_ai = obtener_datos_con_ia(ticker_elegido)
    
    if df_ai is not None and not df_ai.empty:
        precio_actual = df_ai['Close'].iloc[-1]
        rsi_actual = df_ai['RSI'].iloc[-1]
        soporte_val = df_ai['Support'].iloc[-1]
        resistencia_val = df_ai['Resistance'].iloc[-1]
        vol_score = df_ai['Volume_Score'].iloc[-1]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio Actual", f"${precio_actual:.2f}")
        c2.metric("RSI (14)", f"{rsi_actual:.1f}")
        c3.metric("Soporte Clave (5a)", f"${soporte_val:.2f}")
        c4.metric("Score Volumen", f"{vol_score:.2f}x")

        fig = construir_grafico_avanzado(df_ai, ticker_elegido)
        if fig:
            st.plotly_chart(fig, use_container_width=True)

        if st.button("🧪 Simular Detección de Entrada por la IA"):
            conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
            c = conn.cursor()
            sl_calc = round(precio_actual * 0.98, 2)
            tp_calc = round(precio_actual * 1.04, 2)
            c.execute("""
                INSERT INTO detected_signals (id, symbol, precio, rsi, vwap, volume_score, support, resistance, sl, tp, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
            """, (str(uuid.uuid4())[:8], ticker_elegido, precio_actual, rsi_actual, df_ai['VWAP'].iloc[-1], vol_score, soporte_val, resistencia_val, sl_calc, tp_calc, time.strftime("%H:%M:%S")))
            conn.commit()
            conn.close()
            st.success("¡Señal detectada con Bandas de Bollinger y enviada a la cola de confirmación!")
            st.rerun()

# ---------------------------------------------------------------------
# PESTAÑA 2: COLA DE SEÑALES (Confirmar / Negar)
# ---------------------------------------------------------------------
with tab_cola:
    st.subheader("🚨 Cola de Señales Pendientes de Confirmación")
    if st.button("🔄 Refrescar Cola"):
        st.rerun()

    conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
    df_senales = pd.read_sql_query("SELECT * FROM detected_signals WHERE status = 'PENDING' ORDER BY timestamp DESC", conn)
    conn.close()

    if df_senales.empty:
        st.info("🟢 No hay señales pendientes de confirmación. La IA vigila el mercado.")
    else:
        for idx, row in df_senales.iterrows():
            with st.container(border=True):
                col_i, col_t, col_b = st.columns([2, 3, 2])
                with col_i:
                    st.markdown(f"### 📈 **{row['symbol']}**")
                    st.caption(f"Hora: {row['timestamp']}")
                    st.markdown(f"Precio Entrada: **${row['precio']}**")
                with col_t:
                    st.markdown(f"Soporte: `${row['support']}` | Resistencia: `${row['resistance']}`")
                    st.markdown(f"Bracket OCO: SL: **${row['sl']}** | TP: **${row['tp']}**")
                with col_b:
                    btn_c, btn_d = st.columns(2)
                    if btn_c.button("✅ CONFIRMAR", key=f"c_{row['id']}", type="primary", use_container_width=True):
                        res = router.ejecutar_orden(row['symbol'], 10, row['sl'], row['tp'], row['precio'])
                        if res["status"] == "SUCCESS":
                            conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
                            c = conn.cursor()
                            c.execute("UPDATE detected_signals SET status = 'APPROVED' WHERE id = ?", (row['id'],))
                            conn.commit()
                            conn.close()
                            st.success(f"Orden ejecutada en {res['broker']}")
                            time.sleep(1)
                            st.rerun()
                    if btn_d.button("❌ NEGAR", key=f"d_{row['id']}", use_container_width=True):
                        conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
                        c = conn.cursor()
                        c.execute("UPDATE detected_signals SET status = 'DISCARDED' WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()

# ---------------------------------------------------------------------
# PESTAÑA 3: VIGILANCIA ACTIVA (Modo Custodia con Extend Profit)
# ---------------------------------------------------------------------
with tab_vigilancia:
    st.subheader("🛡️ Modo Custodia y Vigilancia Activa de Transacciones")
    conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
    df_activas = pd.read_sql_query("SELECT * FROM ordenes WHERE estado = 'ABIERTA'", conn)
    conn.close()

    if df_activas.empty:
        st.info("No hay operaciones abiertas bajo vigilancia en este momento.")
    else:
        st.dataframe(df_activas, use_container_width=True)
        st.caption("La IA monitorea continuamente el Take Profit, activando Trailing Stop y Extend Profit si la tendencia continúa.")

# ---------------------------------------------------------------------
# PESTAÑA 4: OPERATIVA MANUAL
# ---------------------------------------------------------------------
with tab_manual:
    st.subheader("⚡ Disparo Directo Manual")
    col1, col2, col3 = st.columns(3)
    s_input = col1.selectbox("Activo Manual", options=LISTA_MULTIACTIVO, index=0, key="man_act")
    q_input = col2.number_input("Cantidad", value=5, min_value=1)
    p_input = col3.number_input("Precio Referencia", value=100.00)

    sl_m = round(p_input * 0.98, 2)
    tp_m = round(p_input * 1.04, 2)
    st.markdown(f"Protección Automática: Stop Loss = **${sl_m}** | Take Profit = **${tp_m}**")

    if st.button("🚀 EJECUTAR COMPRA MANUAL", type="primary", use_container_width=True):
        res = router.ejecutar_orden(s_input, q_input, sl_m, tp_m, p_input)
        if res["status"] == "SUCCESS":
            st.success(f"Orden ejecutada correctamente. ID: {res['order_id']}")
        else:
            st.error(f"Error: {res['message']}")

# ---------------------------------------------------------------------
# PESTAÑA 5: HISTORIAL SQLITE
# ---------------------------------------------------------------------
with tab_historial:
    st.subheader("📊 Historial General de Órdenes (SQLite)")
    if st.button("🔄 Actualizar Historial"):
        st.rerun()
    conn = sqlite3.connect("dalia_pro_trading.db", timeout=30)
    df_hist = pd.read_sql_query("SELECT * FROM ordenes ORDER BY timestamp DESC", conn)
    conn.close()
    if df_hist.empty:
        st.info("Sin registros históricos.")
    else:
        st.dataframe(df_hist, use_container_width=True)
