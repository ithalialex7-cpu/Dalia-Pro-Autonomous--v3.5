import base64
import json
import sqlite3
import threading
import time
import uuid
import numpy as np
import pandas as pd
import streamlit as st

# =====================================================================
# 1. CONFIGURACIÓN Y ESTILOS CSS
# =====================================================================
DALIA_SVG = "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><circle cx='50' cy='50' r='45' fill='#9C27B0'/></svg>"
b64_svg = base64.b64encode(DALIA_SVG.encode("utf-8")).decode()
DALIA_SVG_ICON = f"data:image/svg+xml;base64,{b64_svg}"

st.set_page_config(
    page_title="Dalia Pro Autonomous Agent v3.5",
    layout="wide",
    page_icon=DALIA_SVG_ICON,
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .metric-card {
        background-color: #1e293b;
        border-left: 4px solid #6366f1;
        padding: 15px;
        margin-bottom: 12px;
        border-radius: 0px 8px 8px 0px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# =====================================================================
# 2. IMPORTS CONDICIONALES Y BASE DE DATOS
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
    import websocket

    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False

try:
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import (
        MarketOrderRequest,
        StopLossRequest,
        TakeProfitRequest,
    )

    ALPACA_SDK_AVAILABLE = True
except ImportError:
    ALPACA_SDK_AVAILABLE = False


def init_db():
    conn = sqlite3.connect("dalia_trading.db", timeout=10)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS ordenes (
            id TEXT PRIMARY KEY, symbol TEXT, qty INTEGER, precio REAL, 
            sl REAL, tp REAL, broker TEXT, modo TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS detected_signals (
            id TEXT PRIMARY KEY, symbol TEXT, precio REAL, rsi REAL, 
            vwap REAL, sl REAL, tp REAL, timestamp TEXT, status TEXT DEFAULT 'PENDING'
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


# =====================================================================
# 3. MOTOR DE DATOS E INDICADORES
# =====================================================================
@st.cache_data(ttl=60)
def obtener_datos_tecnicos(ticker, interval="5m", period="5d"):
    if not YFINANCE_AVAILABLE:
        return None
    try:
        ticker_obj = yf.Ticker(ticker)
        df = ticker_obj.history(period=period, interval=interval)
        if df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.dropna()

        df["EMA20"] = df["Close"].ewm(span=20).mean()
        df["EMA50"] = df["Close"].ewm(span=50).mean()
        tp = (df["High"] + df["Low"] + df["Close"]) / 3
        df["VWAP"] = (tp * df["Volume"]).cumsum() / df["Volume"].cumsum()

        delta = df["Close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-6)
        df["RSI"] = 100 - (100 / (1 + rs))
        return df
    except Exception:
        return None


def construir_grafico_velas(df, symbol):
    if not PLOTLY_AVAILABLE or df is None:
        return None
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.7, 0.3],
    )
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name="Precio",
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["VWAP"],
            mode="lines",
            name="VWAP",
            line=dict(color="#9C27B0", width=2),
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df["RSI"],
            mode="lines",
            name="RSI",
            line=dict(color="#00E676", width=2),
        ),
        row=2,
        col=1,
    )
    fig.add_hline(y=70, line_dash="dash", line_color="#FF5252", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00E676", row=2, col=1)
    fig.update_layout(
        height=500,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=10, r=10, t=30, b=10),
    )
    return fig


# =====================================================================
# 4. INTERFAZ DE USUARIO (SIDEBAR Y TABS)
# =====================================================================
st.sidebar.title("DALIA PRO TRADING")
st.sidebar.caption("Panel Institucional Autónomo")

LISTA_ACTIVOS = ["NVDA", "AAPL", "TSLA", "MSFT", "AMZN", "SPY"]

with st.sidebar.expander("🔑 Credenciales API"):
    alpaca_key = st.text_input("Alpaca Key", type="password")
    alpaca_secret = st.text_input("Alpaca Secret", type="password")

modo_real = st.sidebar.toggle("🚨 MODO PRODUCCIÓN", value=False)

tab1, tab2, tab3 = st.tabs(
    ["📈 Gráfico & Análisis", "🚨 Cola de Señales", "📊 Historial"]
)

with tab1:
    st.subheader("Análisis Técnico en Tiempo Real")
    activo = st.selectbox("Selecciona el Activo", options=LISTA_ACTIVOS)

    df = obtener_datos_tecnicos(activo)
    if df is not None and not df.empty:
        precio_act = df["Close"].iloc[-1]
        rsi_act = df["RSI"].iloc[-1]
        vwap_act = df["VWAP"].iloc[-1]

        c1, c2, c3 = st.columns(3)
        c1.metric("Precio Actual", f"${precio_act:.2f}")
        c2.metric("RSI (14)", f"{rsi_act:.1f}")
        c3.metric("VWAP", f"${vwap_act:.2f}")

        fig = construir_grafico_velas(df, activo)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Cargando datos de mercado o sin conexión a yfinance...")

with tab2:
    st.subheader("Señales de Entrada Pendientes")
    if st.button("🔄 Actualizar Señales"):
        st.rerun()

    conn = sqlite3.connect("dalia_trading.db", timeout=10)
    df_senales = pd.read_sql_query(
        "SELECT * FROM detected_signals WHERE status = 'PENDING'", conn
    )
    conn.close()

    if df_senales.empty:
        st.info("No hay señales pendientes en este momento.")
    else:
        st.dataframe(df_senales, use_container_width=True)

with tab3:
    st.subheader("Historial de Órdenes Ejecutadas")
    conn = sqlite3.connect("dalia_trading.db", timeout=10)
    df_ord = pd.read_sql_query("SELECT * FROM ordenes", conn)
    conn.close()
    st.dataframe(df_ord, use_container_width=True)
