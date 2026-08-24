import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import requests
import plotly.express as px
import os
from cloud.config import *
import datetime
from cloud.main import main_execution

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="SEO Auto Analyst | wearecontent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILOS PERSONALIZADOS (Rich Aesthetics) ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #ff4b4b;
        color: white;
        font-weight: bold;
    }
    .stMetric {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3e4251;
    }
    </style>
    """, unsafe_allow_html=True)

# --- AUTENTICACIÓN ---
from cloud.main import get_credentials

def get_gc(token_name="token_wac.json"):
    try:
        import os
        # Debugging: verify os is available
        _ = os.name 
        creds = get_credentials(token_name=token_name)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return None

# --- FUNCIONES CON CACHÉ ---
@st.cache_data(ttl=600) # Guardar en memoria por 10 minutos
def load_inventory_data(token_name):
    gc = get_gc(token_name)
    if not gc: return pd.DataFrame()
    sh = gc.open_by_key(SHEET_INVENTARIO)
    df = pd.DataFrame(sh.worksheet(TAB_INVENTARIO).get_all_records())
    # Normalización universal
    df.columns = [c.lower().strip().replace(" ", "_").replace("-", "_") for c in df.columns]
    return df

@st.cache_data(ttl=300) # Guardar en memoria por 5 minutos
def load_history_data(token_name):
    gc = get_gc(token_name)
    if not gc: return pd.DataFrame()
    sh = gc.open_by_key(SHEET_BITACORA)
    ws = sh.worksheet(TAB_BITACORA)
    data = ws.get_all_values()
    if len(data) > 0:
        df = pd.DataFrame(data[1:], columns=data[0])
    else:
        df = pd.DataFrame()
    # Normalización universal
    df.columns = [c.lower().strip().replace(" ", "_").replace("-", "_") for c in df.columns]
    return df

# --- LOGICA DE DASHBOARD ---
st.sidebar.title("🚀 SEO Analyst Control")

# Selector de Cuenta (Tokens)
token_options = {
    "Cuenta Principal (WAC 1)": "token_wac.json",
    "Cuenta Secundaria (WAC 2)": "token_wac2.json"
}
selected_token_label = st.sidebar.selectbox("Selecciona Cuenta de Google", list(token_options.keys()))
selected_token_file = token_options[selected_token_label]

st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refrescar Datos (Limpiar Caché)"):
    st.cache_data.clear()
    st.sidebar.success("¡Caché limpiada! Cargando datos frescos...")
    st.rerun()

st.sidebar.markdown("---")

try:
    inventory = load_inventory_data(selected_token_file)
    
    if inventory.empty:
        st.warning(f"No se pudieron cargar datos del inventario para la cuenta seleccionada ({selected_token_label}).")
        st.info("Esto puede deberse a un error de autenticación previo o a que la hoja de Google Sheets está vacía.")
        st.stop()
    
    # Verificar columnas críticas
    required_cols = ['marca', 'activo', 'propiedad_gsc', 'propiedad_ga4']
    missing_cols = [col for col in required_cols if col not in inventory.columns]
    
    if missing_cols:
        st.error(f"Faltan columnas críticas en la pestaña '{TAB_INVENTARIO}': {missing_cols}")
        st.info(f"Columnas detectadas: {list(inventory.columns)}")
        st.stop()
        
    active_clients = inventory[inventory['activo'].astype(str).str.lower() == 'true']['marca'].tolist()
    
    if not active_clients:
        st.warning("No hay clientes marcados como 'true' en la columna 'activo'.")
        st.stop()
        
    selected_client = st.sidebar.selectbox("Selecciona un Cliente", active_clients)
    
    st.title(f"📊 Panel de Control: {selected_client}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Acciones Rápidas")
        if st.button(f"⚡ Ejecutar Análisis Mensual para {selected_client}"):
            with st.spinner(f"Procesando datos de {selected_client} con Gemini..."):
                try:
                    result = main_execution(client_to_process=selected_client, token_name=selected_token_file)
                    if result.get("status") == "completed":
                        st.success(f"¡Análisis estratégico completado para {selected_client}!")
                        st.markdown(f"**Impacto del Contenido:** {result.get('impacto', 'N/A')}")
                        st.markdown(f"**Oportunidades y Retos:** {result.get('retos', 'N/A')}")
                        st.balloons()
                    else:
                        st.error("Hubo un problema al procesar el análisis.")
                except Exception as e:
                    st.error(f"Error ejecutando análisis: {e}")
                
    with col2:
        st.subheader("Información del Cliente")
        client_info = inventory[inventory['marca'] == selected_client].iloc[0]
        st.info(f"**Propiedad GSC:** {client_info['propiedad_gsc']}\n\n**ID GA4:** {client_info['propiedad_ga4']}")

    st.markdown("---")
    st.subheader("📈 Resumen de Desempeño (Looker Live)")
    
    # Simulación de datos para visualización
    chart_data = pd.DataFrame({
        'Mes': ['Ene', 'Feb', 'Mar'],
        'Clics': [1200, 1500, 1850],
        'Usuarios': [4500, 5200, 6100]
    })
    
    fig = px.line(chart_data, x='Mes', y=['Clics', 'Usuarios'], title="Tendencia Reciente", template="plotly_dark")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📜 Últimos Insights (Bitácora)")
    
    history = load_history_data(selected_token_file)
    
    # Intentar encontrar la columna del cliente (puede ser 'cliente' o 'marca')
    col_cliente = None
    if 'cliente' in history.columns:
        col_cliente = 'cliente'
    elif 'marca' in history.columns:
        col_cliente = 'marca'
        
    if col_cliente:
        client_history = history[history[col_cliente] == selected_client].tail(5)
        
        if not client_history.empty:
            # Mostrar solo si las columnas existen
            cols_map = {
                'fecha': 'Fecha',
                'insight_positivo': 'Impacto del Contenido',
                'insight_negativo': 'Oportunidades y Retos',
                'periodo': 'Periodo'
            }
            # Filtrar columnas que existen en el dataframe
            cols_to_show = [c for c in cols_map.keys() if c in history.columns]
            display_df = client_history[cols_to_show].rename(columns={k: v for k, v in cols_map.items() if k in cols_to_show})
            st.table(display_df)
        else:
            st.warning("No hay historial registrado para este cliente en la Bitácora.")
    else:
        st.error(f"No se encontró una columna de 'cliente' o 'marca' en la pestaña '{TAB_BITACORA}'")
        st.info(f"Columnas detectadas en Bitácora: {list(history.columns)}")

except Exception as e:
    st.error(f"Error cargando el dashboard: {e}")
    st.info("Asegúrate de haber configurado el archivo 'service_account.json' en la carpeta /cloud.")
