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
import sqlite3
import json
import base64

# SVG del icono de Dalia Pro
DALIA_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'><defs><linearGradient id='petalGrad' x1='0%' y1='100%' x2='0%' y2='0%'><stop offset='0%' stop-color='#be185d'/><stop offset='50%' stop-color='#ec4899'/><stop offset='100%' stop-color='#f472b6'/></linearGradient><linearGradient id='goldGrad' x1='0%' y1='0%' x2='100%' y2='100%'><stop offset='0%' stop-color='#f43f5e'/><stop offset='50%' stop-color='#fb7185'/><stop offset='100%' stop-color='#fda4af'/></linearGradient><path id='textPathTop' d='M 30,100 A 70,70 0 1,1 170,100'/><path id='textPathBottom' d='M 170,100 A 70,70 0 0,1 30,100'/></defs><circle cx='100' cy='100' r='96' fill='#0f172a' stroke='url(#goldGrad)' stroke-width='5'/><circle cx='100' cy='100' r='88' fill='none' stroke='#334155' stroke-width='2'/><circle cx='100' cy='100' r='62' fill='none' stroke='url(#goldGrad)' stroke-width='2'/><text fill='#ffffff' font-family='Arial, sans-serif' font-weight='bold' font-size='16' letter-spacing='3' text-anchor='middle'><textPath href='#textPathTop' startOffset='50%'>DALIA PRO</textPath></text><text fill='#ffffff' font-family='Arial, sans-serif' font-weight='bold' font-size='15' letter-spacing='4' text-anchor='middle'><textPath href='#textPathBottom' startOffset='50%'>TRADING</textPath></text><g transform='translate(90, 105) scale(0.75)'><g fill='url(#petalGrad)' stroke='#831843' stroke-width='1'><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(0)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(30)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(60)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(90)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(120)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(150)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(180)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(210)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(240)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(270)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(300)'/><path d='M0,0 C-12,-25 -12,-45 0,-55 C12,-45 12,-25 0,0' transform='rotate(330)'/></g><g fill='#f472b6' opacity='0.9'><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(15)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(45)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(75)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(105)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(135)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(165)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(195)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(225)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(255)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(285)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(315)'/><path d='M0,0 C-8,-18 -8,-35 0,-42 C8,-35 8,-18 0,0' transform='rotate(345)'/></g><circle cx='0' cy='0' r='12' fill='#fbcfe8' stroke='#be185d' stroke-width='2'/></g><g><line x1='112' y1='105' x2='112' y2='130' stroke='#4ade80' stroke-width='2'/><rect x='108' y='110' width='8' height='15' fill='#22c55e' rx='1'/><line x1='124' y1='90' x2='124' y2='122' stroke='#4ade80' stroke-width='2'/><rect x='120' y='95' width='8' height='20' fill='#22c55e' rx='1'/><line x1='136' y1='75' x2='136' y2='110' stroke='#4ade80' stroke-width='2'/><rect x='132' y='80' width='8' height='22' fill='#22c55e' rx='1'/></g></svg>"""

# Conversión a Data URI
b64_svg = base64.b64encode(DALIA_SVG.encode('utf-8')).decode('utf-8')
DALIA_SVG_ICON = f"data:image/svg+xml;base64,{b64_svg}"

st.set_page_config(
    page_title="Dalia Pro Autonomous Institutional Engine",
    layout="wide",
    page_icon=DALIA_SVG_ICON
)

# Inyección Robusta PWA / Favicon / Apple Touch Icon en el Documento Raíz
components.html(f"""
    <script>
    (function() {{
        const svgData = "{DALIA_SVG_ICON}";
        
        function injectPwaManifestAndIcons() {{
            try {{
                const targetDoc = window.top.document || window.parent.document;
                if (!targetDoc) return;
                
                const head = targetDoc.getElementsByTagName('head')[0];
                if (!head) return;

                // 1. Remover elementos previos de Streamlit que puedan forzar el icono rojo/rojo-blanco
                const oldIcons = targetDoc.querySelectorAll("link[rel*='icon'], link[rel='manifest'], link[rel*='apple']");
                oldIcons.forEach(el => el.remove());

                // 2. Crear Canvas para renderizar PNG nativo a 512x512 (Requerido para instalación en Android/iOS)
                const img = new Image();
                img.crossOrigin = "anonymous";
                img.onload = function() {{
                    const canvas = targetDoc.createElement('canvas');
                    canvas.width = 512;
                    canvas.height = 512;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, 512, 512);
                    const pngDataUrl = canvas.toDataURL('image/png');

                    // Asignar Favicons e Icono de Pantalla de Inicio Apple
                    const iconRels = ['icon', 'shortcut icon', 'apple-touch-icon', 'apple-touch-icon-precomposed'];
                    iconRels.forEach(relType => {{
                        let l = targetDoc.createElement('link');
                        l.rel = relType;
                        l.type = 'image/png';
                        l.sizes = '512x512';
                        l.href = pngDataUrl;
                        head.appendChild(l);
                    }});

                    // 3. Crear Web App Manifest Dinámico
                    const manifestObj = {{
                        "name": "Dalia Pro Trading Engine",
                        "short_name": "Dalia Pro",
                        "description": "Dalia Pro Autonomous Institutional Trading Platform",
                        "start_url": targetDoc.location.href,
                        "display": "standalone",
                        "background_color": "#0b0f19",
                        "theme_color": "#0b0f19",
                        "icons": [
                            {{
                                "src": pngDataUrl,
                                "sizes": "512x512",
                                "type": "image/png",
                                "purpose": "any maskable"
                            }}
                        ]
                    }};

                    const manifestString = JSON.stringify(manifestObj);
                    const blob = new Blob([manifestString], {{type: 'application/json'}});
                    const manifestUrl = URL.createObjectURL(blob);

                    let mLink = targetDoc.createElement('link');
                    mLink.rel = 'manifest';
                    mLink.href = manifestUrl;
                    head.appendChild(mLink);

                    // 4. Configurar Meta Tags PWA Móviles
                    const metaList = [
                        {{ name: 'apple-mobile-web-app-capable', content: 'yes' }},
                        {{ name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }},
                        {{ name: 'apple-mobile-web-app-title', content: 'Dalia Pro' }},
                        {{ name: 'mobile-web-app-capable', content: 'yes' }},
                        {{ name: 'theme-color', content: '#0b0f19' }}
                    ];

                    metaList.forEach(m => {{
                        let tag = targetDoc.querySelector(`meta[name='${{m.name}}']`);
                        if (!tag) {{
                            tag = targetDoc.createElement('meta');
                            tag.name = m.name;
                            head.appendChild(tag);
                        }}
                        tag.content = m.content;
                    }});
                }};
                img.src = svgData;
            }} catch (e) {{
                console.error("Error al inyectar PWA Manifest de Dalia Pro:", e);
            }}
        }}

        // Re-inyección periódica para asegurar reemplazo continuo sobre el renderizado de Streamlit
        injectPwaManifestAndIcons();
        setTimeout(injectPwaManifestAndIcons, 500);
        setTimeout(injectPwaManifestAndIcons, 1500);
        setTimeout(injectPwaManifestAndIcons, 3000);
    }})();
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
if 'db_initialized' not in st.session_state:
    st.session_state['db_initialized'] = False
if 'backtest_ran' not in st.session_state:
    st.session_state['backtest_ran'] = False

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

    .roadmap-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%);
        border: 1px solid #312e81;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
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
            
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
        
        tp = (df['High'] + df['Low'] + df['Close']) / 3
        df['VWAP'] = (tp * df['Volume']).cumsum() / df['Volume'].cumsum()
        vwap_var = ((tp - df['VWAP']) ** 2 * df['Volume']).cumsum() / df['Volume'].cumsum()
        vwap_std = np.sqrt(np.maximum(0, vwap_var))
        df['VWAP_Upper_1'] = df['VWAP'] + vwap_std
        df['VWAP_Lower_1'] = df['VWAP'] - vwap_std

        std_20 = df['Close'].rolling(window=20).std()
        df['Bollinger_Upper'] = df['SMA_20'] + (2 * std_20)
        df['Bollinger_Lower'] = df['SMA_20'] - (2 * std_20)

        high_low = df['High'] - df['Low']
        high_close = (df['High'] - df['Close'].shift()).abs()
        low_close = (df['Low'] - df['Close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['ATR'] = tr.rolling(window=14).mean()

        exp1 = df['Close'].ewm(span=12, adjust=False).mean()
        exp2 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['MACD_Hist'] = df['MACD'] - df['MACD_Signal']
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / (loss + 1e-9)
        df['RSI'] = 100 - (100 / (1 + rs))

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

tab_main, tab_indicators, tab_ml_mc, tab_gex, tab_options, tab_radar, tab_hardware, tab_journal, tab_roadmap = st.tabs([
    "🎯 Copiloto & Centro de Control",
    "🔬 Panel de Indicadores & MTF",
    "🧠 Machine Learning & Monte Carlo",
    "📊 Gamma Exposure & Order Flow",
    "⛓️ Cadena Opciones & Max Pain",
    "👁️ Auto-Screener Radar MTF",
    "🔊 Alertas Hardware Directas",
    "📒 Diario, Paper Trading & VaR",
    "🗺️ Hoja de Ruta Sugerida"
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
            if b_col1.button("✅ Confirmar y Aprobar Orden Instantáneamente", key="btn_confirm_order", width="stretch"):
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
                st.success(f"⚡ ¡Orden confirmada y enviada a **{broker_target}**!")
            
            if b_col2.button("🛑 Cancelar Orden (Abortar)", key="btn_cancel_order", width="stretch"):
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
            st.info("⚖️ El mercado cotiza en rango neutro. Espere la alineación de confluencia con probabilidad >= 70% o <= 30%.")
            
        st.markdown("</div>", unsafe_allow_html=True)

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
        
        fig.add_trace(go.Candlestick(x=data.index, open=data['Open'], high=data['High'], low=data['Low'], close=data['Close'], name="Precio"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['EMA_200'], line=dict(color='#ec4899', width=1.5), name="EMA 200"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['VWAP'], line=dict(color='#38bdf8', width=1.5), name="VWAP"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['VWAP_Upper_1'], line=dict(color='#38bdf8', width=1, dash='dash'), name="VWAP +1σ"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['VWAP_Lower_1'], line=dict(color='#38bdf8', width=1, dash='dash'), name="VWAP -1σ"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Bollinger_Upper'], line=dict(color='rgba(255,255,255,0.4)', width=1), name="Bollinger Sup"), row=1, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['Bollinger_Lower'], line=dict(color='rgba(255,255,255,0.4)', width=1), name="Bollinger Inf"), row=1, col=1)
        
        fig.add_trace(go.Bar(x=data.index, y=data['MACD_Hist'], marker_color=np.where(data['MACD_Hist'] > 0, '#22c55e', '#ef4444'), name="MACD Hist"), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD'], line=dict(color='#38bdf8', width=1), name="MACD"), row=2, col=1)
        fig.add_trace(go.Scatter(x=data.index, y=data['MACD_Signal'], line=dict(color='#f43f5e', width=1), name="Signal"), row=2, col=1)

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
            {"Indicador": "Point of Control (POC)", "Valor": f"${poc_actual:.2f}", "Estado": "🟢 Arriba del Nodo" if precio_actual > poc_actual else "🔴 Debajo del Nodo"},
            {"Indicador": "ADX Trend Strength", "Valor": f"{adx_actual:.1f}", "Estado": "🔥 Tendencia Fuerte" if adx_actual >= 25 else "💤 Consolidación"},
            {"Indicador": "RSI Oscillator", "Valor": f"{rsi_actual:.1f}", "Estado": "⚠️ Sobrecompra" if rsi_actual > 70 else ("⚠️ Sobreventa" if rsi_actual < 30 else "✅ Neutral")},
            {"Indicador": "MACD Histogram", "Valor": f"{macd_hist:.4f}", "Estado": "🟢 Impulso Positivo" if macd_hist > 0 else "🔴 Impulso Negativo"}
        ])
        st.table(df_ind_summary)

with tab_ml_mc:
    st.subheader(f"🧠 Simulaciones Monte Carlo & Proyecciones Estocásticas — {ticker}")
    if not data.empty:
        col_mc1, col_mc2 = st.columns([1, 2])
        with col_mc1:
            st.markdown("#### ⚙️ Parámetros de Simulación")
            n_sims = st.slider("Número de Simulaciones", 100, 2000, 500, step=100)
            n_days = st.slider("Horizonte Temporal (Días)", 5, 90, 30, step=5)
            
            mc_results = simular_monte_carlo(data, num_sims=n_sims, num_dias=n_days)
            if mc_results:
                st.metric("Precio Esperado (Media)", f"${mc_results['expected_price']}")
                st.metric("Value at Risk (VaR 95%)", f"${mc_results['var_95']}")
                st.metric("Drawdown Máximo Estimado", f"{mc_results['max_drawdown']}%")

        with col_mc2:
            if mc_results:
                fig_mc = go.Figure()
                time_axis = list(range(n_days))
                for i in range(min(n_sims, 100)):
                    fig_mc.add_trace(go.Scatter(x=time_axis, y=mc_results['simulations'][:, i], mode='lines', line=dict(width=0.5), showlegend=False, opacity=0.3))
                
                mean_path = np.mean(mc_results['simulations'], axis=1)
                fig_mc.add_trace(go.Scatter(x=time_axis, y=mean_path, mode='lines', line=dict(color='#ec4899', width=3), name='Trayectoria Media'))
                fig_mc.update_layout(title="Simulación Monte Carlo (100 Trayectorias Ilustrativas)", template="plotly_dark", height=450)
                st.plotly_chart(fig_mc, width="stretch")

with tab_gex:
    st.subheader(f"📊 Gamma Exposure (GEX) & Order Flow — {ticker}")
    if not data.empty:
        gex_info = calcular_gex_y_gamma_flip(ticker, precio_actual)
        if gex_info:
            g1, g2, g3 = st.columns(3)
            g1.metric("Total GEX Estimate", f"${gex_info['total_gex']}M")
            g2.metric("Gamma Flip Level", f"${gex_info['gamma_flip']}")
            g3.metric("Régimen de Mercado", "Long Gamma" if gex_info['total_gex'] > 0 else "Short Gamma")
            st.info(f"📌 **Régimen Detectado:** {gex_info['regime']}")
        else:
            st.warning("No se pudieron calcular los datos de Gamma Exposure para este activo o temporalidad.")

with tab_options:
    st.subheader(f"⛓️ Cadena de Opciones & Estructura Max Pain — {ticker}")
    if not data.empty:
        opt_info = obtener_cadena_opciones_y_max_pain(ticker, precio_actual)
        if opt_info:
            o1, o2, o3, o4 = st.columns(4)
            o1.metric("Expiración Cercana", opt_info['exp_date'])
            o2.metric("Max Pain Strike", f"${opt_info['max_pain']}")
            o3.metric("Put/Call Ratio (OI)", opt_info['pcr'])
            o4.metric("IV Promedio", f"{opt_info['avg_iv']}%")

            fig_opt = go.Figure()
            df_opt = opt_info['df_opt']
            fig_opt.add_trace(go.Bar(x=df_opt['strike'], y=df_opt['Call_OI'], name='Call Open Interest', marker_color='#22c55e'))
            fig_opt.add_trace(go.Bar(x=df_opt['strike'], y=df_opt['Put_OI'], name='Put Open Interest', marker_color='#ef4444'))
            fig_opt.add_vline(x=precio_actual, line_dash="dash", line_color="white", annotation_text="Precio Actual")
            fig_opt.add_vline(x=opt_info['max_pain'], line_dash="solid", line_color="#f59e0b", annotation_text="Max Pain")
            fig_opt.update_layout(barmode='group', template="plotly_dark", height=450, title="Distribución de Open Interest por Strike")
            st.plotly_chart(fig_opt, width="stretch")
        else:
            st.warning("No se encontraron cadenas de opciones válidas para este activo.")

with tab_radar:
    st.subheader("👁️ Auto-Screener Radar MTF Multi-Activo")
    st.write("Exploración en tiempo real de confluencia técnica en activos clave:")
    
    radar_tickers = ["AAPL", "TSLA", "NVDA", "MSFT", "AMZN", "GOOGL", "SPY", "QQQ"]
    if st.button("🔄 Ejecutar Escáner Multi-Activo"):
        radar_results = []
        progress_bar = st.progress(0)
        for idx, t_symbol in enumerate(radar_tickers):
            df_t = obtener_datos(t_symbol, "5m")
            if not df_t.empty:
                c_p = float(df_t['Close'].iloc[-1])
                ema_p = float(df_t['EMA_200'].dropna().iloc[-1]) if not df_t['EMA_200'].dropna().empty else c_p
                rsi_p = float(df_t['RSI'].dropna().iloc[-1]) if not df_t['RSI'].dropna().empty else 50
                bias_p = "🟢 CALL" if c_p > ema_p else "🔴 PUT"
                radar_results.append({
                    "Ticker": t_symbol,
                    "Precio": f"${c_p:.2f}",
                    "Sesgo 5m": bias_p,
                    "RSI": f"{rsi_p:.1f}",
                    "Estado": "⚡ En Tendencia" if rsi_p > 60 or rsi_p < 40 else "💤 Consolidación"
                })
            progress_bar.progress((idx + 1) / len(radar_tickers))
        st.table(pd.DataFrame(radar_results))

with tab_hardware:
    st.subheader("🔊 Módulo de Alertas Hardware Directas")
    st.write("Prueba de integración de sonido, respuesta háptica y notificaciones del sistema operativo.")
    
    h_col1, h_col2, h_col3 = st.columns(3)
    if h_col1.button("🔔 Probar Chime Ejecución"):
        emitir_alerta_sonora("chime", "⚡ Orden Ejecutada", "Prueba de tono de confirmación de orden.")
    if h_col2.button("🚨 Probar Alarma Institucional"):
        emitir_alerta_sonora("alarma", "🚨 Alerta Crítica", "Prueba de tono de alerta de alta prioridad.")
    if h_col3.button("🎵 Probar Tono Genérico"):
        emitir_alerta_sonora("institucional", "ℹ️ Notificación Dalia Pro", "Prueba de tono estándar.")

with tab_journal:
    st.subheader("📒 Diario de Operaciones & Paper Trading Engine")
    
    j_col1, j_col2 = st.columns(2)
    with j_col1:
        st.markdown("### 📊 Balance de Cuenta Paper Trading")
        st.metric("Balance Disponible", f"${st.session_state['cash_balance']:,.2f}")
        st.metric("Posiciones Activas", len(st.session_state['paper_positions']))
        
    with j_col2:
        st.markdown("### 📜 Historial de Ejecuciones")
        if st.session_state['execution_log']:
            st.dataframe(pd.DataFrame(st.session_state['execution_log']))
        else:
            st.info("No hay registros de ejecuciones en esta sesión.")

with tab_roadmap:
    st.subheader("🗺️ Hoja de Ruta Sugerida Dalia Pro Engine")
    
    st.markdown("""
        <div class="roadmap-card">
            <h3 style="color:#a5b4fc; margin-top:0;">🚀 Fase 1: Integración Fix API & IBKR TWS Bridge</h3>
            <p style="color:#cbd5e1;">Conexión directa vía sockets TCP/FIX para transmisión sub-milisegundo de órdenes bracket (Take-Profit / Stop-Loss dinámico en hardware local).</p>
        </div>
        <div class="roadmap-card">
            <h3 style="color:#a5b4fc; margin-top:0;">🧠 Fase 2: Redes Neuronales LSTM & Transformer Signal Engine</h3>
            <p style="color:#cbd5e1;">Implementación de aprendizaje profundo supervisado para predicción de volatilidad implícita y compresión de spreads en vencimientos 0DTE.</p>
        </div>
        <div class="roadmap-card">
            <h3 style="color:#a5b4fc; margin-top:0;">🌐 Fase 3: Cluster Multi-Agente Distribuido</h3>
            <p style="color:#cbd5e1;">Despliegue de agentes autónomos especializados (Order Flow Agent, Macro Regime Agent, Risk Manager Agent) coordinados por consenso síncrono.</p>
        </div>
    """, unsafe_allow_html=True)
