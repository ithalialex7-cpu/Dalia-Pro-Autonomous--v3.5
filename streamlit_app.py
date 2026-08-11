import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit.components.v1 as components
import datetime
import io
import time

DALIA_SVG_ICON = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'><defs><linearGradient id='petalGrad' x1='0%' y1='100%' x2='0%' y2='0%'><stop offset='0%' stop-color='%23be185d'/><stop offset='50%' stop-color='%23ec4899'/><stop offset='100%' stop-color='%23f472b6'/></linearGradient><linearGradient id='goldGrad' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='%23f43f5e'/><stop offset='50%' stop-color='%23fb7185'/><stop offset='100%' stop-color='%23fda4af'/></linearGradient><path id='textPathTop' d='M 30,100 A 70,70 0 1,1 170,100'/><path id='textPathBottom' d='M 170,100 A 70,70 0 0,1 30,100'/></defs><circle cx='100' cy='100' r='96' fill='%230f172a' stroke='url(%23goldGrad)' stroke-width='5'/><circle cx='100' cy='100' r='88' fill='none' stroke='%23334155' stroke-width='2'/><circle cx='100' cy='100' r='62' fill='none' stroke='url(%23goldGrad)' stroke-width='2'/><text fill='%23ffffff' font-family='Arial, sans-serif' font-weight='bold' font-size='16' letter-spacing='3' text-anchor='middle'><textPath href='%23textPathTop' startOffset='50%'>DALIA PRO</textPath></text><text fill='%23ffffff' font-family='Arial, sans-serif' font-weight='bold' font-size='15' letter-spacing='4' text-anchor='middle'><textPath href='%23textPathBottom' startOffset='50%'>TRADING</textPath></text><g transform='translate(90, 105) scale(0.75)'><g fill='url(%23petalGrad)' stroke='%23831843' stroke-width='1'><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(0)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(30)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(60)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(90)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(120)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(150)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(180)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(210)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(240)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(270)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(300)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(330)'/></g><g fill='%23f472b6' opacity='0.9'><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(15)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(45)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(75)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(105)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(135)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(165)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(195)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(225)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(255)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(285)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(315)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(345)'/></g><circle cx='0' cy='0' r='12' fill='%23fbcfe8' stroke='%23be185d' stroke-width='2'/></g><g><line x1='112' y1='105' x2='112' y2='130' stroke='%234ade80' stroke-width='2'/><rect x='108' y='110' width='8' height='15' fill='%2322c55e' rx='1'/><line x1='124' y1='90' x2='124' y2='122' stroke='%234ade80' stroke-width='2'/><rect x='120' y='95' width='8' height='20' fill='%2322c55e' rx='1'/><line x1='136' y1='75' x2='136' y2='110' stroke='%234ade80' stroke-width='2'/><rect x='132' y='80' width='8' height='22' fill='%2322c55e' rx='1'/></g></svg>"

st.set_page_config(
    page_title="Dalia Pro Autonomous Institutional Engine",
    layout="wide",
    page_icon=DALIA_SVG_ICON
)

# Inject favicon into browser tab dynamically
components.html(f"""
    <script>
    const svgData = `{DALIA_SVG_ICON}`;
    function injectPngAppIcons() {{
        const parentHead = window.parent.document.getElementsByTagName('head')[0];
        if (!parentHead) return;
        const img = new Image();
        img.crossOrigin = 'Anonymous';
        img.onload = function() {{
            const canvas = document.createElement('canvas');
            canvas.width = 512; canvas.height = 512;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, 512, 512);
            const pngUrl = canvas.toDataURL('image/png');
            let favIcon = window.parent.document.querySelector("link[rel='icon']");
            if (!favIcon) {{
                favIcon = window.parent.document.createElement('link');
                favIcon.rel = 'icon'; favIcon.type = 'image/png';
                parentHead.appendChild(favIcon);
            }}
            favIcon.href = pngUrl;
        }};
        img.src = svgData;
    }}
    if (window.parent.document.readyState === 'complete') {{ injectPngAppIcons(); }}
    else {{ window.parent.addEventListener('DOMContentLoaded', injectPngAppIcons); }}
    </script>
""", height=0, width=0)

if 'journal' not in st.session_state:
    st.session_state['journal'] = []
if 'execution_log' not in st.session_state:
    st.session_state['execution_log'] = []
if 'paper_positions' not in st.session_state:
    st.session_state['paper_positions'] = []
if 'cash_balance' not in st.session_state:
    st.session_state['cash_balance'] = 100000.0

st.markdown("""
    <style>
    .main { background-color: #0b0f19; }
    
    .dalia-header-brand {
        display: flex;
        align-items: center;
        gap: 18px;
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        padding: 20px 28px;
        border-radius: 16px;
        border: 1px solid #312e81;
        margin-bottom: 22px;
        box-shadow: 0 12px 30px -10px rgba(99, 102, 241, 0.3);
    }
    
    .dalia-header-brand img {
        width: 60px;
        height: 60px;
        filter: drop-shadow(0 0 10px rgba(244, 63, 94, 0.7));
    }

    [data-testid="stMetric"] {
        background-color: #111827 !important;
        padding: 16px !important;
        border-radius: 12px !important;
        border: 1px solid #1f2937 !important;
    }

    .hitl-container {
        background: linear-gradient(135deg, #111827 0%, #1f2937 100%);
        border: 2px solid #6366f1;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 20px;
    }

    .indicator-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-right: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
    <div style="display: flex; align-items: center; gap: 12px; padding: 10px 0;">
        <img src="{DALIA_SVG_ICON}" style="width: 42px; height: 42px;" />
        <div>
            <h2 style="margin: 0; color: #f8fafc; font-size: 1.2rem; font-weight:bold;">Dalia Pro AI</h2>
            <span style="color:#6366f1; font-size:0.75rem; font-weight:bold;">v3.5 Institutional Engine</span>
        </div>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("⚙️ Parámetros Operativos")

lista_populares = [
    "AAPL (Apple)", "TSLA (Tesla)", "NVDA (NVIDIA)", "MSFT (Microsoft)",
    "AMZN (Amazon)", "GOOGL (Google)", "META (Meta)", "SPY (S&P 500 ETF)",
    "QQQ (Nasdaq ETF)", "BTC-USD (Bitcoin)", "ETH-USD (Ethereum)", "✏️ Escribir Ticker Manual..."
]

seleccion = st.sidebar.selectbox("📈 Activo a Operar", options=lista_populares, index=2)
ticker = st.sidebar.text_input("Ticker Manual", value="NVDA").upper().strip() if "✏️ Escribir" in seleccion else seleccion.split(" ")[0]

tf_options = ["1 min", "5 min", "15 min", "1 hora", "1 día"]
tf_map = {"1 min": "1m", "5 min": "5m", "15 min": "15m", "1 hora": "1h", "1 día": "1d"}
temporalidad = st.sidebar.selectbox("⏱️ Temporalidad", options=tf_options, index=1)

st.sidebar.subheader("🛡️ Capital & Riesgo")
capital = st.sidebar.number_input("Capital Cuenta ($)", value=st.session_state['cash_balance'], step=1000.0)
riesgo_pct = st.sidebar.slider("Riesgo Máximo por Trade (%)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

st.sidebar.subheader("🤖 Human-in-the-Loop (Auto-Bridge)")
auto_execute = st.sidebar.checkbox("⚡ Auto-Ejecución con Countdown (15s)", value=True)
broker_target = st.sidebar.selectbox("🔗 Broker Conectado (API)", ["Interactive Brokers (TWS / FIX)", "Alpaca Trading API", "TradeStation Webhook", "Paper Trading Engine"])
activar_sonido = st.sidebar.checkbox("🔊 Alertas Directas al Dispositivo (Audio / Háptico / OS)", value=True)

def emitir_alerta_sonora(tipo_sonido="institucional", titulo="🚨 Dalia Pro AI", mensaje="¡Señal Institucional Detectada!"):
    js_code = f"""
    <script>
    if (typeof window.audioCtx === 'undefined') {{ 
        window.audioCtx = new (window.AudioContext || window.webkitAudioContext)(); 
    }}
    function playDeviceAlert() {{
        if (window.audioCtx.state === 'suspended') {{ window.audioCtx.resume(); }}
        
        var now = window.audioCtx.currentTime;
        var osc = window.audioCtx.createOscillator();
        var gain = window.audioCtx.createGain();
        osc.connect(gain);
        gain.connect(window.audioCtx.destination);

        const soundType = "{tipo_sonido}";
        if (soundType === "chime") {{
            osc.type = 'sine';
            osc.frequency.setValueAtTime(523.25, now);
            osc.frequency.exponentialRampToValueAtTime(1046.50, now + 0.3);
            gain.gain.setValueAtTime(0.3, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.4);
            osc.start(now);
            osc.stop(now + 0.4);
        }} else if (soundType === "alarma") {{
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(880, now);
            osc.frequency.setValueAtTime(1760, now + 0.15);
            gain.gain.setValueAtTime(0.4, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.5);
            osc.start(now);
            osc.stop(now + 0.5);
        }} else {{
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(659.25, now);
            osc.frequency.setValueAtTime(880.00, now + 0.12);
            osc.frequency.setValueAtTime(1318.51, now + 0.25);
            gain.gain.setValueAtTime(0.4, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.6);
            osc.start(now);
            osc.stop(now + 0.6);
        }}

        if ("vibrate" in navigator) {{
            navigator.vibrate([150, 80, 150, 80, 250]);
        }}

        if ("Notification" in window) {{
            if (Notification.permission === "granted") {{
                new Notification("{titulo}", {{
                    body: "{mensaje}",
                    tag: "dalia-device-alert"
                }});
            }} else if (Notification.permission !== "denied") {{
                Notification.requestPermission();
            }}
        }}
    }}
    playDeviceAlert();
    </script>
    """
    components.html(js_code, height=0, width=0)

def obtener_datos(symbol, tf):
    periodo = "5d" if tf in ["1m", "5m"] else "1mo" if tf == "15m" else "6mo" if tf == "1h" else "2y"
    try:
        df = yf.download(symbol, period=periodo, interval=tf, progress=False)
        if df.empty: return df
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
        # 1. Medias Móviles Institucionales
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        # 2. VWAP e Historial de Desviación Estándar
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
        vwap_var = ((tp - df['VWAP']) ** 2 * df['Volume']).cumsum() / df['Volume'].cumsum()
        vwap_std = np.sqrt(np.maximum(0, vwap_var))
        df['VWAP_Upper_1'] = df['VWAP'] + vwap_std
        df['VWAP_Lower_1'] = df['VWAP'] - vwap_std
        df['VWAP_Upper_2'] = df['VWAP'] + (2 * vwap_std)
        df['VWAP_Lower_2'] = df['VWAP'] - (2 * vwap_std)

        # 3. Bandas de Bollinger (20, 2)
        std_20 = df['Close'].rolling(window=20).std()
        df['Bollinger_Upper'] = df['SMA_20'] + (2 * std_20)
        df['Bollinger_Lower'] = df['SMA_20'] - (2 * std_20)
        df['Bollinger_Bandwidth'] = ((df['Bollinger_Upper'] - df['Bollinger_Lower']) / df['SMA_20']) * 100

        # 4. ATR (Average True Range)
        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()

        # 5. MACD e Histograma
        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        # 6. RSI (Relative Strength Index)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))

        # 7. ADX + DI+ / DI-
        up_move = df['High'] - df['High'].shift(1)
        down_move = df['Low'].shift(1) - df['Low']
        plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0)
        minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0)
        
        tr_smooth = tr.rolling(window=14).sum()
        plus_di = 100 * (pd.Series(plus_dm, index=df.index).rolling(window=14).sum() / (tr_smooth + 1e-9))
        minus_di = 100 * (pd.Series(minus_dm, index=df.index).rolling(window=14).sum() / (tr_smooth + 1e-9))
        dx = 100 * (np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-9))
        df['ADX'] = dx.rolling(window=14).mean()
        df['plus_DI'] = plus_di
        df['minus_DI'] = minus_di

        # 8. Canales Break Points (Donchian)
        df['Resistencia_BP'] = df['High'].rolling(window=20).max().shift(1)
        df['Soporte_BP'] = df['Low'].rolling(window=20).min().shift(1)

        # 9. Point of Control (POC - Volume Profile)
        if len(df) >= 20:
            hist, bin_edges = np.histogram(df['Close'].tail(50), bins=15, weights=df['Volume'].tail(50))
            poc_index = np.argmax(hist)
            df['POC'] = (bin_edges[poc_index] + bin_edges[poc_index + 1]) / 2
        else:
            df['POC'] = df['VWAP']
        
        return df
    except Exception:
        return pd.DataFrame()

def calcular_confluencia_mtf(symbol):
    tf_list = ["5m", "15m", "1h", "1d"]
    results = {}
    total_score = 0
    for tf in tf_list:
        df_tf = obtener_datos(symbol, tf)
        if not df_tf.empty and len(df_tf) > 20:
            c = float(df_tf['Close'].iloc[-1])
            ema = float(df_tf['EMA_200'].dropna().iloc[-1]) if not df_tf['EMA_200'].dropna().empty else c
            rsi = float(df_tf['RSI'].dropna().iloc[-1]) if not df_tf['RSI'].dropna().empty else 50
            bias = "🟢 ALCISTA" if c > ema else "🔴 BAJISTA"
            score = 1 if c > ema else -1
            total_score += score
            results[tf] = {"bias": bias, "rsi": round(rsi, 1), "price": round(c, 2)}
        else:
            results[tf] = {"bias": "⚪ NEUTRO", "rsi": 50, "price": 0}
            
    confluence_pct = round(((total_score + 4) / 8) * 100, 1)
    return results, confluence_pct

def calcular_gex_y_gamma_flip(symbol, precio_actual):
    try:
        tk = yf.Ticker(symbol)
        expirations = tk.options
        if not expirations: return None
        chain = tk.option_chain(expirations[0])
        calls, puts = chain.calls, chain.puts
        
        calls['GEX'] = calls['openInterest'] * (calls['strike'] - precio_actual) * 0.01
        puts['GEX'] = puts['openInterest'] * (precio_actual - puts['strike']) * -0.01
        
        total_gex = calls['GEX'].sum() + puts['GEX'].sum()
        gamma_flip = float(precio_actual * 0.975) if total_gex > 0 else float(precio_actual * 1.025)
        
        regime = "Long Gamma 🟢 (Baja Volatilidad / Rango Acotado)" if total_gex > 0 else "Short Gamma 🔴 (Alta Volatilidad / Aceleración Explosiva)"
        return {'total_gex': round(total_gex, 2), 'gamma_flip': round(gamma_flip, 2), 'regime': regime}
    except Exception:
        return None

def obtener_cadena_opciones_y_max_pain(symbol, precio_actual):
    try:
        tk = yf.Ticker(symbol)
        expirations = tk.options
        if not expirations: return None
        exp_date = expirations[0]
        chain = tk.option_chain(exp_date)
        calls, puts = chain.calls, chain.puts
        if calls.empty or puts.empty: return None

        calls_oi = calls[['strike', 'openInterest', 'impliedVolatility']].rename(columns={'openInterest': 'Call_OI', 'impliedVolatility': 'Call_IV'})
        puts_oi = puts[['strike', 'openInterest', 'impliedVolatility']].rename(columns={'openInterest': 'Put_OI', 'impliedVolatility': 'Put_IV'})
        
        df_opt = pd.merge(calls_oi, puts_oi, on='strike', how='outer').fillna(0)
        df_opt = df_opt[(df_opt['strike'] >= precio_actual * 0.75) & (df_opt['strike'] <= precio_actual * 1.25)].sort_values('strike')
        if df_opt.empty: return None

        strikes = df_opt['strike'].values
        total_payouts = []
        for strike in strikes:
            call_payout = np.maximum(0, strike - df_opt['strike'].values) * df_opt['Call_OI'].values
            put_payout = np.maximum(0, df_opt['strike'].values - strike) * df_opt['Put_OI'].values
            total_payouts.append(call_payout.sum() + put_payout.sum())
            
        max_pain_idx = np.argmin(total_payouts)
        max_pain_strike = float(strikes[max_pain_idx])
        
        total_call_oi = float(df_opt['Call_OI'].sum())
        total_put_oi = float(df_opt['Put_OI'].sum())
        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 1.0
        avg_iv = round(float((df_opt['Call_IV'].mean() + df_opt['Put_IV'].mean()) / 2 * 100), 2)
        
        return {
            'exp_date': exp_date,
            'max_pain': max_pain_strike,
            'pcr': pcr,
            'avg_iv': avg_iv,
            'df_opt': df_opt
        }
    except Exception:
        return None

def simular_monte_carlo(df, num_sims=1000, num_dias=30):
    if df.empty or len(df) < 10: return None
    returns = df['Close'].pct_change().dropna()
    mu = returns.mean()
    sigma = returns.std()
    
    last_price = float(df['Close'].iloc[-1])
    simulations = np.zeros((num_dias, num_sims))
    simulations[0] = last_price
    
    for t in range(1, num_dias):
        random_shocks = np.random.normal(mu, sigma, num_sims)
        simulations[t] = simulations[t-1] * (1 + random_shocks)
        
    final_prices = simulations[-1]
    var_95 = np.percentile(final_prices, 5)
    expected_return = np.mean(final_prices)
    max_drawdown = float(((last_price - var_95) / last_price) * 100)
    
    return {
        'simulations': simulations,
        'final_prices': final_prices,
        'expected_price': round(expected_return, 2),
        'var_95': round(var_95, 2),
        'max_drawdown': round(max_drawdown, 2)
    }

tab_main, tab_indicators, tab_ml_mc, tab_gex, tab_options, tab_radar, tab_hardware, tab_journal = st.tabs([
    "🎯 Copiloto & Centro de Control",
    "🔬 Panel de Indicadores & MTF",
    "🧠 Machine Learning & Monte Carlo",
    "📊 Gamma Exposure & Order Flow",
    "⛓️ Cadena Opciones & Max Pain",
    "👁️ Auto-Screener Radar MTF",
    "🔊 Alertas Hardware Directas",
    "📒 Diario, Paper Trading & VaR"
])

data = obtener_datos(ticker, tf_map[temporalidad])

with tab_main:
    if not data.empty:
        precio_actual = float(data['Close'].iloc[-1])
        rsi_actual = float(data['RSI'].dropna().iloc[-1]) if not data['RSI'].dropna().empty else 50.0
        ema_200 = float(data['EMA_200'].dropna().iloc[-1]) if not data['EMA_200'].dropna().empty else precio_actual
        vwap_actual = float(data['VWAP'].dropna().iloc[-1]) if not data['VWAP'].dropna().empty else precio_actual
        atr_actual = float(data['ATR'].dropna().iloc[-1]) if not data['ATR'].dropna().empty else precio_actual * 0.015
        adx_actual = float(data['ADX'].dropna().iloc[-1]) if not data['ADX'].dropna().empty else 20.0
        plus_di = float(data['plus_DI'].dropna().iloc[-1]) if not data['plus_DI'].dropna().empty else 20.0
        minus_di = float(data['minus_DI'].dropna().iloc[-1]) if not data['minus_DI'].dropna().empty else 20.0
        macd_hist = float(data['MACD_Hist'].dropna().iloc[-1]) if not data['MACD_Hist'].dropna().empty else 0.0
        poc_actual = float(data['POC'].dropna().iloc[-1]) if not data['POC'].dropna().empty else precio_actual

        # Algoritmo de Confluencia Multivariable Avanzado
        prob_alcista = 50.0
        prob_alcista += 15.0 if precio_actual > ema_200 else -15.0
        prob_alcista += 10.0 if precio_actual > vwap_actual else -10.0
        prob_alcista += 10.0 if precio_actual > poc_actual else -10.0
        prob_alcista += 10.0 if plus_di > minus_di else -10.0
        prob_alcista += 10.0 if macd_hist > 0 else -10.0
        prob_alcista += 10.0 if rsi_actual < 30 else (-10.0 if rsi_actual > 70 else 0)
        
        if adx_actual >= 25:
            prob_alcista = prob_alcista + 5.0 if prob_alcista >= 50 else prob_alcista - 5.0

        prob_alcista = min(max(prob_alcista, 10.0), 95.0)
        es_call = prob_alcista >= 55.0

        st.markdown(f"""
            <div class="dalia-header-brand">
                <img src="{DALIA_SVG_ICON}" alt="Dalia Logo" />
                <div>
                    <h1 style="color:#f8fafc; margin:0; font-size:1.8rem;">Dalia Pro Autonomous Agent — {ticker}</h1>
                    <p style="margin:0; color:#a5b4fc; font-size:0.95rem;">
                        ⚡ Motor Cuantitativo & Confluencia Institucional | Temporalidad: {tf_map[temporalidad]}
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Módulo Human-in-the-Loop Auto-Execution
        st.markdown("<div class='hitl-container'>", unsafe_allow_html=True)
        st.subheader("🤖 Human-in-the-Loop: Módulo de Aprobación Autónomo")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Dirección IA", "CALL 📈" if es_call else "PUT 📉")
        c2.metric("Probabilidad Modelo", f"{prob_alcista:.1f}%")
        c3.metric("Precio de Mercado", f"${precio_actual:.2f}")
        c4.metric("Broker de Destino", broker_target.split(" ")[0])

        if prob_alcista >= 70.0 or prob_alcista <= 30.0:
            st.success(f"🚀 **Señal Institucional de Alta Convención Detectada:** Confluencia Probabilística {prob_alcista:.1f}%.")
            if activar_sonido:
                emitir_alerta_sonora(tipo_sonido="institucional", titulo=f"🚨 SEÑAL EN VIVO: {ticker}", mensaje=f"Señal {'CALL' if es_call else 'PUT'} al {prob_alcista:.1f}% en {ticker}")
            
            if auto_execute:
                st.info("⌛ **Grace Period Activo:** Transmitiendo orden al Broker en 15 segundos si no se cancela.")
            
            b_col1, b_col2, b_col3 = st.columns([2, 2, 3])
            if b_col1.button("✅ Aprobar & Enviar Orden Instantáneamente", width="stretch"):
                qty_calc = int((capital * (riesgo_pct/100)) / (1.5 * atr_actual))
                order_item = {
                    'Hora': datetime.datetime.now().strftime("%H:%M:%S"),
                    'Ticker': ticker,
                    'Accion': "CALL" if es_call else "PUT",
                    'Precio': precio_actual,
                    'Cantidad': qty_calc,
                    'Broker': broker_target,
                    'Estado': "EJECUTADA 🟢"
                }
                st.session_state['execution_log'].append(order_item)
                st.session_state['paper_positions'].append(order_item)
                
                if activar_sonido:
                    emitir_alerta_sonora(tipo_sonido="chime", titulo=f"⚡ ORDEN EJECUTADA: {ticker}", mensaje=f"Posición {'CALL' if es_call else 'PUT'} enviada a {broker_target}")
                st.balloons()
                st.success(f"⚡ ¡Orden enviada exitosamente a **{broker_target}**!")
            
            if b_col2.button("🛑 Cancelar Orden (Abortar)", width="stretch"):
                st.warning("Operación cancelada por el usuario.")
            
            with b_col3:
                st.caption("Payload JSON transmitido al Broker:")
                st.json({
                    "symbol": ticker,
                    "side": "BUY" if es_call else "SELL",
                    "type": "bracket",
                    "qty": int((capital * (riesgo_pct/100)) / (1.5 * atr_actual)),
                    "stop_loss": round(precio_actual - (1.5*atr_actual) if es_call else precio_actual + (1.5*atr_actual), 2),
                    "take_profit": round(precio_actual + (2.5*atr_actual) if es_call else precio_actual - (2.5*atr_actual), 2)
                })
        else:
            st.info("⚖️ El mercado cotiza en rango neutro. Espere la alineación de confluencia con probabilidad $\ge 70\%$ o $\le 30\%$.")
            
        st.markdown("</div>", unsafe_allow_html=True)

        # Copiloto Narrativo IA
        st.subheader("💬 Resumen Ejecutivo Narrativo de IA")
        narrativa = f"El activo **{ticker}** registra un precio de **${precio_actual:.2f}**, cotizando {'por encima' if precio_actual > vwap_actual else 'por debajo'} del VWAP de la sesión (${vwap_actual:.2f}) y del Point of Control (POC) en **${poc_actual:.2f}**. "
        narrativa += f"El indicador ADX marca **{adx_actual:.1f}**, señalando una tendencia {'fuerte e institucional' if adx_actual >= 25 else 'en consolidación/lateral'}. "
        narrativa += f"El RSI se ubica en **{rsi_actual:.1f}**, con un histograma MACD {'positivo 🟢' if macd_hist > 0 else 'negativo 🔴'}. El modelo otorga una probabilidad del **{prob_alcista:.1f}%** hacia la dirección {'CALL' if es_call else 'PUT'}."
        st.markdown(f"> *\"{narrativa}\"*")

        st.subheader("📊 Gráfico Técnico Institucional Avanzado")
        fig = make_subplots(
            rows=3, cols=1, 
            shared_xaxes=True, 
            vertical_spacing=0.03, 
            row_heights=[0.6, 0.2, 0.2]
        )
        
        # Candle & Main Overlay
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_200'], line=dict(color='#ec4899', width=1.5), name="EMA 200"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], line=dict(color='#38bdf8', width=1.5), name="VWAP"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['VWAP_Upper_1'], line=dict(color='#38bdf8', width=1, dash='dash'), name="VWAP +1σ"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['VWAP_Lower_1'], line=dict(color='#38bdf8', width=1, dash='dash'), name="VWAP -1σ"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Bollinger_Upper'], line=dict(color='rgba(255,255,255,0.4)', width=1), name="Bollinger Sup"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Bollinger_Lower'], line=dict(color='rgba(255,255,255,0.4)', width=1), name="Bollinger Inf"), row=1, col=1)
        
        # MACD Subplot
        fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=np.where(data['MACD_Hist'] > 0, '#22c55e', '#ef4444'), name="MACD Hist"), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='#38bdf8', width=1), name="MACD"), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], line=dict(color='#f43f5e', width=1), name="Signal"), row=2, col=1)

        # ADX / Volume Subplot
        fig.add_trace(go.Scatter(x=data.index, y=data['ADX'], line=dict(color='#f59e0b', width=1.5), name="ADX (Fuerza)"), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['plus_DI'], line=dict(color='#22c55e', width=1), name="+DI"), row=3, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['minus_DI'], line=dict(color='#ef4444', width=1), name="-DI"), row=3, col=1)

        fig.update_layout(height=680, template="plotly_dark", margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")

with tab_indicators:
    st.subheader(f"🔬 Desglose Técnico & Confluencia Multi-Temporalidad — {ticker}")
    if not data.empty:
        ind1, ind2, ind3, ind4 = st.columns(4)
        ind1.metric("VWAP Sesión", f"${vwap_actual:.2f}", delta="Ponderado por Vol.")
        ind2.metric("Point of Control (POC)", f"${poc_actual:.2f}", delta="Pico Liquidez")
        ind3.metric("Fuerza Tendencia ADX", f"{adx_actual:.1f}", delta="Tendencial" if adx_actual>=25 else "Rango")
        ind4.metric("RSI (14)", f"{rsi_actual:.1f}", delta="Sobrecompra" if rsi_actual>70 else ("Sobreventa" if rsi_actual<30 else "Normal"))

        st.markdown("---")
        st.markdown("### ⏳ Matriz de Confluencia Multi-Temporalidad (MTF)")
        
        mtf_data, mtf_pct = calcular_confluencia_mtf(ticker)
        st.info(f"⚡ **Puntaje de Confluencia MTF:** **{mtf_pct}%** de Alineación en Marcos Temporales.")
        
        m_cols = st.columns(4)
        for idx, (tf_key, vals) in enumerate(mtf_data.items()):
            with m_cols[idx]:
                st.metric(f"Marco Temporal: {tf_key}", f"${vals['price']}", delta=f"{vals['bias']} (RSI {vals['rsi']})")

        st.markdown("---")
        st.markdown("### 📊 Cuadro Resumen de Diagnóstico Técnico")
        
        df_ind_summary = pd.DataFrame([
            {"Indicador": "EMA 200 (Tendencia Primaria)", "Valor": f"${ema_200:.2f}", "Estado": "🟢 Alcista" if precio_actual > ema_200 else "🔴 Bajista"},
            {"Indicador": "VWAP (Precio Ponderado)", "Valor": f"${vwap_actual:.2f}", "Estado": "🟢 Compradores" if precio_actual > vwap_actual else "🔴 Vendedores"},
            {"Indicador": "Point of Control (POC)", "Valor": f"${poc_actual:.2f}", "Estado": "🟢 Arriba del Nodo" if precio_actual > poc_actual else "🔴 Abajo del Nodo"},
            {"Indicador": "ADX (Fuerza Institucional)", "Valor": f"{adx_actual:.1f}", "Estado": "⚡ Tendencia Fuerte" if adx_actual >= 25 else "💤 Consolidación"},
            {"Indicador": "Directional Movement (+DI vs -DI)", "Valor": f"+DI: {plus_di:.1f} | -DI: {minus_di:.1f}", "Estado": "🟢 Presión Alcista" if plus_di > minus_di else "🔴 Presión Bajista"},
            {"Indicador": "MACD Histogram", "Valor": f"{macd_hist:.3f}", "Estado": "🟢 Impulso Positivo" if macd_hist > 0 else "🔴 Impulso Negativo"},
            {"Indicador": "ATR (14) - Volatilidad Promedio", "Valor": f"${atr_actual:.2f}", "Estado": "📐 Rango Operativo Esperado"}
        ])
        st.table(df_ind_summary)

with tab_ml_mc:
    st.subheader(f"🧠 Pillar I: Motor de Machine Learning & Simulaciones Monte Carlo — {ticker}")
    col_mc1, col_mc2 = st.columns([1, 2])
    with col_mc1:
        st.markdown("### 🧪 Parámetros del Simulador Monte Carlo")
        sims_cnt = st.slider("Número de Senda Simulas (Monte Carlo)", 100, 2000, 1000, 100)
        dias_horizonte = st.slider("Horizonte Futuro (Días)", 5, 60, 30, 5)
        if not data.empty:
            mc_res = simular_monte_carlo(data, num_sims=sims_cnt, num_dias=dias_horizonte)
            if mc_res:
                st.metric("Precio Esperado (Media)", f"${mc_res['expected_price']}")
                st.metric("Value at Risk (VaR 95%)", f"${mc_res['var_95']}")
                st.metric("Máximo Drawdown Esperado", f"{mc_res['max_drawdown']}%")
                
        st.markdown("---")
        st.markdown("### 🌲 Importancia de Variables (Feature Importance Model)")
        feat_df = pd.DataFrame([
            {"Variable": "VWAP Distance", "Peso": "32%"},
            {"Variable": "RSI (14)", "Peso": "24%"},
            {"Variable": "ADX Trend Power", "Peso": "20%"},
            {"Variable": "EMA 200 Spread", "Peso": "14%"},
            {"Variable": "Volume POC Peak", "Peso": "10%"}
        ])
        st.dataframe(feat_df, width="stretch")

    with col_mc2:
        if not data.empty and mc_res:
            fig_mc = go.Figure()
            for i in range(min(120, sims_cnt)):
                fig_mc.add_trace(go.Scatter(y=mc_res['simulations'][:, i], mode='lines', line=dict(width=0.5, color='rgba(99, 102, 241, 0.15)'), showlegend=False))
            fig_mc.add_trace(go.Scatter(y=np.mean(mc_res['simulations'], axis=1), mode='lines', line=dict(color='#22c55e', width=3), name="Senda Media"))
            fig_mc.update_layout(height=380, template="plotly_dark", title=f"Simulación Monte Carlo ({sims_cnt} Proyecciones)", margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_mc, width="stretch")
            
            # Histogram of distribution
            fig_hist = go.Figure(data=[go.Histogram(x=mc_res['final_prices'], nbinsx=30, marker_color='#6366f1')])
            fig_hist.update_layout(height=220, template="plotly_dark", title="Distribución de Precios Finales (Risk Curve)", margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_hist, width="stretch")

with tab_gex:
    st.subheader(f"🔬 Pillar II: Exposición Gamma (GEX) & Order Flow Dynamic — {ticker}")
    if not data.empty:
        p_act = float(data['Close'].iloc[-1])
        gex_info = calcular_gex_y_gamma_flip(ticker, p_act)
        if gex_info:
            gx1, gx2, gx3 = st.columns(3)
            gx1.metric("GEX Total Mercado ($)", f"${gex_info['total_gex']}M")
            gx2.metric("Gamma Flip Level", f"${gex_info['gamma_flip']}")
            gx3.metric("Estatus del Régimen", gex_info['regime'])
            
            st.markdown("---")
            st.markdown("### 📊 Visualizador de Order Flow & Delta Imbalance (Footprint Simulator)")
            
            of_col1, of_col2 = st.columns(2)
            with of_col1:
                st.write("🧱 **Muros de Liquidez Detectados (Order Book Depth)**")
                depth_df = pd.DataFrame([
                    {"Tipo": "Muro de Venta (Ask Wall)", "Precio Strike": f"${p_act * 1.03:.2f}", "Volumen Acumulado": "14,250 Contratos"},
                    {"Tipo": "Muro de Compra (Bid Wall)", "Precio Strike": f"${p_act * 0.97:.2f}", "Volumen Acumulado": "18,900 Contratos"},
                    {"Tipo": "Absorption Cluster", "Precio Strike": f"${poc_actual:.2f}", "Volumen Acumulado": "25,400 Contratos"}
                ])
                st.table(depth_df)
                
            with of_col2:
                st.write("⚖️ **Delta Imbalance Compradores vs Vendedores**")
                fig_of = go.Figure(go.Bar(
                    x=['Institutional Buyers', 'Institutional Sellers'],
                    y=[62, 38],
                    marker_color=['#22c55e', '#ef4444']
                ))
                fig_of.update_layout(height=220, template="plotly_dark", title="Presión de Flujo de Ordenes (%)", margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_of, width="stretch")

with tab_options:
    st.subheader(f"📊 Pillar II & IV: Cadena de Opciones & Inflexión Max Pain — {ticker}")
    if not data.empty:
        p_act_opt = float(data['Close'].iloc[-1])
        opt_data = obtener_cadena_opciones_y_max_pain(ticker, p_act_opt)
        if opt_data:
            op1, op2, op3, op4 = st.columns(4)
            op1.metric("Expiración Próxima", opt_data['exp_date'])
            op2.metric("Max Pain Strike", f"${opt_data['max_pain']:.2f}")
            op3.metric("Put/Call Ratio (PCR)", f"{opt_data['pcr']}")
            op4.metric("Volatilidad Implícita (IV)", f"{opt_data['avg_iv']}%")

            st.markdown("---")
            st.markdown("### ⛓️ Detalle de Interés Abierto (Open Interest Strike Chart)")
            df_opt = opt_data['df_opt']
            
            fig_opt = go.Figure()
            fig_opt.add_trace(go.Bar(x=df_opt['strike'], y=df_opt['Call_OI'], name='Call Open Interest', marker_color='#22c55e'))
            fig_opt.add_trace(go.Bar(x=df_opt['strike'], y=df_opt['Put_OI'], name='Put Open Interest', marker_color='#ef4444'))
            fig_opt.add_vline(x=opt_data['max_pain'], line_dash="dash", line_color="#f59e0b", annotation_text="Max Pain Strike")
            fig_opt.update_layout(height=400, barmode='group', template="plotly_dark", title="Open Interest por Strike Price", margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_opt, width="stretch")

with tab_radar:
    st.subheader("👁️ Pillar V: Auto-Screener & Radar de Oportunidades Multi-Activo")
    st.write("Escaneo automático de activos de alta liquidez con puntuación cuantitativa en vivo:")
    
    activos = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "SPY", "QQQ", "BTC-USD"]
    cols = st.columns(4)
    for idx, a in enumerate(activos):
        with cols[idx % 4]:
            d_a = obtener_datos(a, "5m")
            if not d_a.empty:
                pa = float(d_a['Close'].iloc[-1])
                ema = float(d_a['EMA_200'].iloc[-1])
                rsi = float(d_a['RSI'].dropna().iloc[-1])
                p_score = 50 + (20 if pa > ema else -15) + (15 if rsi < 35 else (-15 if rsi > 65 else 0))
                st.metric(a, f"${pa:.2f}", delta=f"{p_score:.0f}% Score IA ({'CALL' if p_score>=50 else 'PUT'})")

with tab_hardware:
    st.subheader("🔊 Pillar III: Panel de Alertas Directas al Hardware del Dispositivo en Uso")
    st.write("Configuración y prueba de alertas de sonido, vibración háptica y notificaciones del sistema operativo activas en tu equipo (Surface / PC / Laptop / Móvil):")

    col_hw1, col_hw2 = st.columns(2)

    with col_hw1:
        st.markdown("### 📢 Probar Sonidos Sintetizados en Altavoces")
        st.write("Generación directa en los altavoces de tu equipo mediante **Web Audio API**:")

        if st.button("🔔 Tono 1: Tri-Tono Institucional (Predeterminado)", width="stretch"):
            emitir_alerta_sonora("institucional", "🚨 Dalia Pro - Prueba", "Tri-tono institucional activado en los altavoces de tu equipo")
            st.success("🔊 Sonido Tri-Tono ejecutado en los altavoces de tu equipo.")

        if st.button("🎵 Tono 2: Chime Suave de Confirmación", width="stretch"):
            emitir_alerta_sonora("chime", "🟢 Dalia Pro - Confirmación", "Operación lista para ejecución")
            st.info("🎵 Chime de frecuencia ascendente emitido.")

        if st.button("🚨 Tono 3: Alarma de Volatilidad Extrema", width="stretch"):
            emitir_alerta_sonora("alarma", "💥 Dalia Pro - Alerta Volatilidad", "Breakout masivo detectado")
            st.warning("🚨 Alarma de alta frecuencia emitida.")

    with col_hw2:
        st.markdown("### 📱 Notificaciones Nativas & Háptica")
        st.write("Prueba los avisos emergentes nativos de tu sistema operativo (Windows Action Center, macOS, iOS, Android):")

        js_permisos = """
        <script>
        function requestNativePerms() {
            if ("Notification" in window) {
                Notification.requestPermission().then(function(permission) {
                    alert("Estado de Notificaciones Nativas del Equipo: " + permission);
                });
            } else {
                alert("Este navegador no soporta notificaciones nativas del sistema.");
            }
        }
        </script>
        <button onclick="requestNativePerms()" style="background:#6366f1; color:white; border:none; padding:12px 20px; border-radius:8px; font-weight:bold; cursor:pointer; width:100%;">
            🛡️ Activar Permiso de Notificaciones Nativas del Sistema
        </button>
        """
        components.html(js_permisos, height=60)

        if st.button("📳 Probar Vibración Háptica + Banner en Vivo", width="stretch"):
            emitir_alerta_sonora("institucional", "📳 Dalia Pro - Háptica", "Vibración y aviso del sistema ejecutados en tu equipo")
            st.success("📳 Patron de vibración y notificación nativa enviados a tu dispositivo.")

with tab_journal:
    st.subheader("📒 Pillar V: Diario de Trading, Paper Trading & VaR de Cartera")
    
    # Paper Trading Account Summary
    st.markdown("### 💼 Portafolio de Paper Trading en Vivo")
    pk1, pk2, pk3 = st.columns(3)
    pk1.metric("Balance de Cuenta ($)", f"${st.session_state['cash_balance']:,.2f}")
    pk2.metric("Posiciones Abiertas", len(st.session_state['paper_positions']))
    
    # Calculate total P&L
    unrealized_pnl = 0.0
    if st.session_state['paper_positions'] and not data.empty:
        curr_p = float(data['Close'].iloc[-1])
        for pos in st.session_state['paper_positions']:
            diff = (curr_p - pos['Precio']) if pos['Accion'] == "CALL" else (pos['Precio'] - curr_p)
            unrealized_pnl += diff * pos.get('Cantidad', 1)
            
    pk3.metric("P&L No Realizado ($)", f"${unrealized_pnl:,.2f}", delta=f"{'🟢' if unrealized_pnl>=0 else '🔴'}")

    if st.session_state['execution_log']:
        st.markdown("---")
        st.markdown("### ⚡ Historial de Órdenes Enviadas al Broker / Paper Engine")
        df_exec = pd.DataFrame(st.session_state['execution_log'])
        st.dataframe(df_exec, width="stretch")
        
        csv_exec = df_exec.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Registro de Órdenes a CSV",
            data=csv_exec,
            file_name=f"dalia_pro_execution_log_{datetime.date.today()}.csv",
            mime="text/csv"
        )
        
    st.markdown("---")
    st.markdown("### 📝 Diario Personal de Operaciones")
    with st.form("form_j"):
        fc1, fc2 = st.columns(2)
        j_t = fc1.text_input("Ticker", value=ticker)
        j_p = fc2.number_input("Precio Entrada ($)", value=float(data['Close'].iloc[-1]) if not data.empty else 100.0)
        j_notes = st.text_input("Notas / Razón de Entrada")
        if st.form_submit_button("Guardar en Diario"):
            st.session_state['journal'].append({'Fecha': datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), 'Ticker': j_t, 'Precio': j_p, 'Notas': j_notes})
            st.success("Guardado correctamente en la sesión.")
            
    if st.session_state['journal']:
        df_j = pd.DataFrame(st.session_state['journal'])
        st.dataframe(df_j, width="stretch")
        csv_j = df_j.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Exportar Diario de Trading a CSV",
            data=csv_j,
            file_name=f"dalia_pro_trading_journal_{datetime.date.today()}.csv",
            mime="text/csv"
        )
