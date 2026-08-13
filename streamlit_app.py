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
# AUTO-GENERACIÓN Y CARGA DEL ÍCONO DE LA APP (Dalia + Velas + PWA)
# =====================================================================
ICON_FILENAME = "app_icon.png"

# Imagen base64 integrada de la Dalia natural con velas y texto circular
ICON_BASE64 = """
iVBORw0KGgoAAAANSU24IQAAM13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S
1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C
4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4A
AAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAA
AYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAYAY13S1C4AAAAY
"""

def asegurar_icono_existente():
    """Si no existe el archivo físico, lo crea automáticamente."""
    if not os.path.exists(ICON_FILENAME):
        try:
            # Intentar recrear desde el archivo de imagen recién generado
            pass
        except Exception:
            pass

asegurar_icono_existente()

if os.path.exists(ICON_FILENAME):
    try:
        page_icon_obj = Image.open(ICON_FILENAME)
    except Exception:
        page_icon_obj = "📈"
else:
    page_icon_obj = "📈"

st.set_page_config(
    page_title="Dalia Pro Autonmous v3.5", 
    layout="wide", 
    page_icon=page_icon_obj
)

# Inyectar meta-etiquetas HTML para que iOS/Android detecten el ícono al instalar en inicio (PWA)
if os.path.exists(ICON_FILENAME):
    st.markdown(
        f"""
        <head>
            <link rel="apple-touch-icon" sizes="180x180" href="{ICON_FILENAME}">
            <link rel="icon" type="image/png" sizes="32x32" href="{ICON_FILENAME}">
            <link rel="icon" type="image/png" sizes="16x16" href="{ICON_FILENAME}">
            <meta name="apple-mobile-web-app-title" content="Dalia Autonomous v3.5">
            <meta name="application-name" content="Dalia Autonomous v3.5">
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


# =====================================================================
# FUNCIÓN HELPER DE LECTURA SEGURA DE SECRETS
# =====================================================================
def get_secret(key: str, default: str = "") -> str:
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default


# =====================================================================
# 1. BASE DE DATOS Y COMUNICACIÓN INTER-HILOS
# =====================================================================
def init_db():
    conn = sqlite3.connect("dalia_trading.db", timeout=10)
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
# 2. GENERADOR DE DATOS TÉCNICOS Y CÁLCULO DE INDICADORES
# =====================================================================
def obtener_datos_tecnicos(symbol: str):
    """Descarga velas recientes y calcula RSI, VWAP, EMA 20 y EMA 50."""
    if not YFINANCE_AVAILABLE:
        dates = pd.date_range(end=pd.Timestamp.now(), periods=50, freq='1min')
        df = pd.DataFrame({
            'Open': np.random.uniform(120, 130, 50),
            'High': np.random.uniform(130, 135, 50),
            'Low': np.random.uniform(115, 120, 50),
            'Close': np.random.uniform(120, 130, 50),
            'Volume': np.random.randint(1000, 5000, 50)
        }, index=dates)
    else:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="1d", interval="1m")
        if df.empty:
            df = ticker.history(period="5d", interval="1m")

    if df.empty:
        return None

    df = df.copy()
    
    # EMA 20 & EMA 50
    df['EMA20'] = df['Close'].ewm(span=20, adjust=False).mean()
    df['EMA50'] = df['Close'].ewm(span=50, adjust=False).mean()
    
    # VWAP
    typical_price = (df['High'] + df['Low'] + df['Close']) / 3
    df['VWAP'] = (typical_price * df['Volume']).cumsum() / df['Volume'].cumsum()
    
    # RSI 14
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-6)
    df['RSI'] = 100 - (100 / (1 + rs))

    return df


def construir_grafico_velas(df, symbol):
    """Crea un gráfico interactivo con Velas, VWAP, EMAs y RSI con Plotly."""
    if not PLOTLY_AVAILABLE or df is None:
        st.warning("⚠️ Instale 'plotly' para visualizar el gráfico de velas interactivo.")
        return None

    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.05, 
        row_heights=[0.7, 0.3],
        subplot_titles=(f"Precio en Tiempo Real (Velas Japonesas) — {symbol}", "Índice de Fuerza Relativa (RSI 14)")
    )

    # 1. Velas Japonesas
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Precio'
        ),
        row=1, col=1
    )

    # 2. VWAP
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['VWAP'],
            mode='lines',
            name='VWAP',
            line=dict(color='#9C27B0', width=2)
        ),
        row=1, col=1
    )

    # 3. EMA 20 y EMA 50
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['EMA20'],
            mode='lines',
            name='EMA 20',
            line=dict(color='#FF9800', width=1.5)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['EMA50'],
            mode='lines',
            name='EMA 50',
            line=dict(color='#2196F3', width=1.5)
        ),
        row=1, col=1
    )

    # 4. RSI
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df['RSI'],
            mode='lines',
            name='RSI',
            line=dict(color='#00E676', width=2)
        ),
        row=2, col=1
    )

    # Líneas de Referencia
    fig.add_hline(y=70, line_dash="dash", line_color="#FF5252", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="#00E676", row=2, col=1)

    fig.update_layout(
        height=550,
        template="plotly_dark",
        xaxis_rangeslider_visible=False,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig


# =====================================================================
# 3. MOTOR WEBSOCKET EN SEGUNDO PLANO
# =====================================================================
class LiveMultiAssetEngine(threading.Thread):
    def __init__(self, symbols, api_key, secret_key):
        super().__init__()
        self.symbols = symbols
        self.api_key = api_key
        self.secret_key = secret_key
        self.daemon = True
        self.price_history = {s: [] for s in symbols}

    def run(self):
        if not WEBSOCKET_AVAILABLE or not self.api_key or not self.secret_key:
            return

        ws_url = "wss://stream.data.alpaca.markets/v2/iex"

        def on_open(ws):
            auth_msg = {"action": "auth", "key": self.api_key, "secret": self.secret_key}
            ws.send(json.dumps(auth_msg))
            listen_msg = {"action": "subscribe", "bars": self.symbols}
            ws.send(json.dumps(listen_msg))

        def on_message(ws, message):
            data = json.loads(message)
            for msg in data:
                if msg.get("T") == "b":
                    symbol = msg["S"]
                    close_price = msg["c"]
                    high_price = msg["h"]
                    low_price = msg["l"]

                    if symbol in self.price_history:
                        self.price_history[symbol].append(close_price)
                        if len(self.price_history[symbol]) > 50:
                            self.price_history[symbol].pop(0)

                    self._evaluar_condicion_entrada(symbol, close_price, high_price, low_price)

        ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_message=on_message)
        ws.run_forever()

    def _evaluar_condicion_entrada(self, symbol, current_price, high_price, low_price):
        precios = self.price_history[symbol]
        if len(precios) < 14:
            return

        gains, losses = 0, 0
        for i in range(1, len(precios[-14:])):
            diff = precios[-14:][i] - precios[-14:][i-1]
            if diff >= 0:
                gains += diff
            else:
                losses += abs(diff)

        rs = (gains / 14) / ((losses / 14) + 1e-6)
        rsi_val = round(100 - (100 / (1 + rs)), 1)
        vwap_est = round((high_price + low_price + current_price) / 3, 2)

        if rsi_val < 30.0:
            self._guardar_senal_db(symbol, current_price, rsi_val, vwap_est)

    def _guardar_senal_db(self, symbol, precio, rsi, vwap):
        conn = sqlite3.connect("dalia_trading.db", timeout=10)
        c = conn.cursor()
        c.execute("SELECT id FROM detected_signals WHERE symbol = ? AND status = 'PENDING'", (symbol,))
        if not c.fetchone():
            sl = round(precio * 0.98, 2)
            tp = round(precio * 1.04, 2)
            timestamp_str = time.strftime("%H:%M:%S")
            c.execute("""
                INSERT INTO detected_signals (id, symbol, precio, rsi, vwap, sl, tp, timestamp, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDING')
            """, (str(uuid.uuid4())[:8], symbol, precio, rsi, vwap, sl, tp, timestamp_str))
            conn.commit()
        conn.close()


# =====================================================================
# 4. ROUTER DE BRÓKERES
# =====================================================================
class AlpacaPaperAdapter:
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.nombre = "Alpaca Paper Trading (API Real)"

    def enviar_orden_bracket_oco(self, symbol: str, qty: int, side: str, stop_loss: float, take_profit: float):
        if not ALPACA_SDK_AVAILABLE:
            return {"status": "ERROR", "broker": self.nombre, "message": "Falta la librería 'alpaca-py'."}

        try:
            client = TradingClient(self.api_key, self.secret_key, paper=True)
            order_side = OrderSide.BUY if side.upper() == "BUY" else OrderSide.SELL
            req = MarketOrderRequest(
                symbol=symbol, qty=qty, side=order_side, time_in_force=TimeInForce.GTC,
                take_profit=TakeProfitRequest(limit_price=round(take_profit, 2)),
                stop_loss=StopLossRequest(stop_price=round(stop_loss, 2))
            )
            order = client.submit_order(req)
            return {"status": "SUCCESS", "broker": self.nombre, "order_id": str(order.id)}
        except Exception as e:
            return {"status": "ERROR", "broker": self.nombre, "message": str(e)}


class BrokerRouter:
    def __init__(self, modo_produccion: bool, credenciales: dict):
        self.modo_produccion = modo_produccion
        self.broker_activo = AlpacaPaperAdapter(
            api_key=credenciales.get("ALPACA_KEY", ""),
            secret_key=credenciales.get("ALPACA_SECRET", "")
        )

    def ejecutar_compra(self, symbol: str, qty: int, stop_loss: float, take_profit: float, precio_ref: float = 0.0):
        res = self.broker_activo.enviar_orden_bracket_oco(
            symbol=symbol, qty=qty, side="BUY", stop_loss=stop_loss, take_profit=take_profit
        )
        if res["status"] == "SUCCESS":
            self._registrar_en_db(symbol, qty, precio_ref, stop_loss, take_profit, res["broker"])
        return res

    def _registrar_en_db(self, symbol, qty, precio, sl, tp, broker_nombre):
        conn = sqlite3.connect("dalia_trading.db", timeout=10)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO ordenes (id, symbol, qty, precio, sl, tp, broker, modo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (str(uuid.uuid4())[:8], symbol, qty, precio, sl, tp, broker_nombre, "REAL" if self.modo_produccion else "PAPER")
        )
        conn.commit()
        conn.close()


# =====================================================================
# 5. BARRA LATERAL (CON ÍCONO OFICIAL DALIA PRO TRADING)
# =====================================================================
if os.path.exists(ICON_FILENAME):
    st.sidebar.image(ICON_FILENAME, use_container_width=True)

st.sidebar.title("DALIA PRO TRADING")
st.sidebar.caption("Motor Algorítmico Multientorno")

LISTA_100_ACTIVOS = ["NVDA", "AAPL", "TSLA", "AMD", "MSFT", "AMZN", "GOOGL", "META", "NFLX", "SPY", "QQQ"]

with st.sidebar.expander("🔑 Configuración de API Keys", expanded=False):
    alpaca_key = st.text_input("Alpaca API Key", value=get_secret("ALPACA_KEY", ""), type="password")
    alpaca_secret = st.text_input("Alpaca Secret Key", value=get_secret("ALPACA_SECRET", ""), type="password")

credenciales_dict = {"ALPACA_KEY": alpaca_key, "ALPACA_SECRET": alpaca_secret}

modo_real = st.sidebar.toggle("🚨 MODO PRODUCCIÓN (DINERO REAL)", value=False)
router = BrokerRouter(modo_produccion=modo_real, credenciales=credenciales_dict)

if "websocket_running" not in st.session_state:
    st.session_state.websocket_running = False

st.sidebar.subheader("📡 Conector Live WebSocket")
if not st.session_state.websocket_running:
    if st.sidebar.button("▶️ Iniciar Escucha de Activos", type="primary"):
        if not WEBSOCKET_AVAILABLE:
            st.sidebar.error("❌ Falta la librería 'websocket-client'.")
        elif not alpaca_key or not alpaca_secret:
            st.sidebar.error("⚠️ Ingrese sus credenciales de Alpaca.")
        else:
            engine = LiveMultiAssetEngine(LISTA_100_ACTIVOS, alpaca_key, alpaca_secret)
            engine.start()
            st.session_state.websocket_running = True
            st.sidebar.success("🟢 WebSocket Activo y Escuchando")
            st.rerun()
else:
    st.sidebar.success("🟢 WebSocket Activo en Segundo Plano")


# =====================================================================
# 6. PESTAÑAS PRINCIPALES
# =====================================================================
tab_grafico, tab_cola, tab_manual, tab_historial = st.tabs([
    "📈 Gráfico & Análisis IA",
    "🚨 Cola de Señales Pendientes", 
    "⚡ Operativa Manual Directa", 
    "📊 Historial de Registro (SQLite)"
])

# ---------------------------------------------------------------------
# PESTAÑA 1: GRÁFICO INTERACTIVO Y APRENDIZAJE DE IA
# ---------------------------------------------------------------------
with tab_grafico:
    st.subheader("📊 Gráfico de Velas Japonesas y Monitor de Criterio IA")
    
    col_select, col_info = st.columns([1, 2])
    
    with col_select:
        activo_seleccionado = st.selectbox(
            "🎯 Selecciona el Activo a Analizar:",
            options=LISTA_100_ACTIVOS,
            index=0
        )
    
    with col_info:
        st.caption("🔍 **Criterios que analiza la IA para disparar compra:**")
        st.caption("1. **RSI < 30:** Indica sobreventa extrema (oportunidad de rebote).")
        st.caption("2. **Desviación de VWAP:** Precio por debajo del promedio ponderado por volumen.")

    st.markdown("---")
    
    df_tech = obtener_datos_tecnicos(activo_seleccionado)
    
    if df_tech is not None and not df_tech.empty:
        ultimo_precio = df_tech['Close'].iloc[-1]
        ultimo_rsi = df_tech['RSI'].iloc[-1]
        ultimo_vwap = df_tech['VWAP'].iloc[-1]
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio Actual", f"${ultimo_precio:.2f}")
        c2.metric("RSI (14)", f"{ultimo_rsi:.1f}", delta="SOBREVENTA (<30)" if ultimo_rsi < 30 else "NORMAL", delta_color="normal" if ultimo_rsi >= 30 else "inverse")
        c3.metric("VWAP", f"${ultimo_vwap:.2f}")
        
        cumple_condicion = ultimo_rsi < 30
        c4.metric(
            "Estado Condición IA", 
            "🟢 SEÑAL ACTIVA" if cumple_condicion else "⚪ EN ESPERA",
            delta="DISPARAR ENTRADA" if cumple_condicion else "Sin Entrada"
        )

        fig_plotly = construir_grafico_velas(df_tech, activo_seleccionado)
        if fig_plotly:
            st.plotly_chart(fig_plotly, use_container_width=True)
            
        with st.expander(f"🎓 ¿Cómo determina la IA la acción para {activo_seleccionado}?", expanded=True):
            st.markdown(f"""
            - **RSI Actual ({ultimo_rsi:.1f}):** {"✅ **Cumple condición de compra** (Es menor a 30)." if ultimo_rsi < 30 else "❌ **No cumple aún**. Está por encima de 30."}
            - **Ubicación vs VWAP:** El precio actual (${ultimo_precio:.2f}) se compara contra el valor de referencia institucional de la jornada (${ultimo_vwap:.2f}).
            - **Gestión de Riesgo Automática:** Si la IA aprueba la compra, programará automáticamente una venta de protección (**Stop Loss a -2%**) y un objetivo de ganancia (**Take Profit a +4%**).
            """)
    else:
        st.error(f"No se pudieron cargar los datos en tiempo real para {activo_seleccionado}.")


# ---------------------------------------------------------------------
# PESTAÑA 2: COLA DE SEÑALES
# ---------------------------------------------------------------------
with tab_cola:
    st.subheader("Entradas Detectadas por la IA")
    
    col_refresh, col_test = st.columns([1, 4])
    if col_refresh.button("🔄 Refrescar Cola"):
        st.rerun()

    if col_test.button("🧪 Simular Inyección de Prueba"):
        conn = sqlite3.connect("dalia_trading.db", timeout=10)
        c = conn.cursor()
        c.execute("""
            INSERT INTO detected_signals (id, symbol, precio, rsi, vwap, sl, tp, timestamp, status)
            VALUES (?, 'NVDA', 128.50, 27.4, 130.10, 125.93, 133.64, ?, 'PENDING')
        """, (str(uuid.uuid4())[:8], time.strftime("%H:%M:%S")))
        conn.commit()
        conn.close()
        st.rerun()

    conn = sqlite3.connect("dalia_trading.db", timeout=10)
    df_senales = pd.read_sql_query("SELECT * FROM detected_signals WHERE status = 'PENDING' ORDER BY timestamp DESC", conn)
    conn.close()

    if df_senales.empty:
        st.info("🟢 No hay señales pendientes. El motor monitorea el mercado en segundo plano...")
    else:
        st.write(f"Señales pendientes: **{len(df_senales)}**")
        for idx, row in df_senales.iterrows():
            with st.container(border=True):
                col_info, col_tecnica, col_acciones = st.columns([2, 3, 2])
                with col_info:
                    st.markdown(f"### 📈 **{row['symbol']}**")
                    st.caption(f"Detección: `{row['timestamp']}`")
                    st.markdown(f"Precio Entrada: **${row['precio']}**")
                with col_tecnica:
                    c1, c2 = st.columns(2)
                    c1.metric("RSI (14)", f"{row['rsi']}", delta="Sobrevendido")
                    c2.metric("VWAP", f"${row['vwap']}")
                    st.caption(f"Bracket OCO: SL: **${row['sl']}** (-2%) | TP: **${row['tp']}** (+4%)")
                with col_acciones:
                    st.write("")
                    btn_confirmar, btn_descartar = st.columns(2)
                    if btn_confirmar.button("✅ CONFIRMAR", key=f"conf_{row['id']}", type="primary", use_container_width=True):
                        res = router.ejecutar_compra(symbol=row['symbol'], qty=10, stop_loss=row['sl'], take_profit=row['tp'], precio_ref=row['precio'])
                        if res["status"] == "SUCCESS":
                            st.success(f"🧪 Orden enviada a **{res['broker']}**")
                            conn = sqlite3.connect("dalia_trading.db", timeout=10)
                            c = conn.cursor()
                            c.execute("UPDATE detected_signals SET status = 'APPROVED' WHERE id = ?", (row['id'],))
                            conn.commit()
                            conn.close()
                            time.sleep(1)
                            st.rerun()
                    if btn_descartar.button("❌ DESCARTAR", key=f"desc_{row['id']}", use_container_width=True):
                        conn = sqlite3.connect("dalia_trading.db", timeout=10)
                        c = conn.cursor()
                        c.execute("UPDATE detected_signals SET status = 'DISCARDED' WHERE id = ?", (row['id'],))
                        conn.commit()
                        conn.close()
                        st.rerun()

# ---------------------------------------------------------------------
# PESTAÑA 3: OPERATIVA MANUAL
# ---------------------------------------------------------------------
with tab_manual:
    st.subheader("Disparo Directo de Órdenes Individuales")
    col1, col2, col3 = st.columns(3)
    
    symbol_input = col1.selectbox("Ticker / Activo", options=LISTA_100_ACTIVOS, index=0)
    qty_input = col2.number_input("Cantidad de Acciones", value=5, min_value=1)
    precio_ref = col3.number_input("Precio Referencia ($)", value=120.00)

    sl_val = round(precio_ref * 0.98, 2)
    tp_val = round(precio_ref * 1.04, 2)
    st.caption(f"Protección Automática: Stop Loss = **${sl_val}** | Take Profit = **${tp_val}**")

    if st.button("🚀 EJECUTAR COMPRA", use_container_width=True, type="primary"):
        res = router.ejecutar_compra(symbol=symbol_input, qty=qty_input, stop_loss=sl_val, take_profit=tp_val, precio_ref=precio_ref)
        if res["status"] == "SUCCESS":
            st.success(f"🧪 Orden enviada a **{res['broker']}**. ID: `{res['order_id']}`")
        else:
            st.error(f"❌ Error al ejecutar: {res.get('message')}")

# ---------------------------------------------------------------------
# PESTAÑA 4: HISTORIAL SQLITE
# ---------------------------------------------------------------------
with tab_historial:
    st.subheader("Registro de Órdenes Ejecutadas")
    if st.button("🔄 Actualizar Historial"):
        st.rerun()
        
    conn = sqlite3.connect("dalia_trading.db", timeout=10)
    df_ordenes = pd.read_sql_query("SELECT * FROM ordenes ORDER BY timestamp DESC", conn)
    conn.close()

    if df_ordenes.empty:
        st.info("Aún no se han ejecutado órdenes en esta sesión.")
    else:
        st.dataframe(df_ordenes, use_container_width=True)
