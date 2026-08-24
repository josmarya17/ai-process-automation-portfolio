import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
import requests
import plotly.express as px
from cloud.config import *
import datetime

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
def get_gc():
    try:
        has_secret = False
        try:
            if "gcp_service_account" in st.secrets:
                has_secret = True
        except Exception:
            has_secret = False

        if has_secret:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = service_account.Credentials.from_service_account_info(
                creds_dict,
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]
            )
        else:
            # Carga local (Desarrollo)
            creds = service_account.Credentials.from_service_account_file(
                f"cloud/{SERVICE_ACCOUNT_FILE}",
                scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive.readonly"]
            )
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Error de autenticación: {e}")
        return None


# --- LOGICA DE DASHBOARD ---
st.sidebar.title("🚀 SEO Analyst Control")
st.sidebar.markdown("---")

try:
    gc = get_gc()
    sh_inv = gc.open_by_key(SHEET_INVENTARIO)
    inventory = pd.DataFrame(sh_inv.worksheet(TAB_INVENTARIO).get_all_records())
    active_clients = inventory[inventory['activo'].astype(str).str.lower() == 'true']['marca'].tolist()
    
    selected_client = st.sidebar.selectbox("Selecciona un Cliente", active_clients)
    
    st.title(f"📊 Panel de Control: {selected_client}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Acciones Rápidas")
        if st.button(f"⚡ Ejecutar Análisis Mensual para {selected_client}"):
            with st.spinner("Procesando datos con Gemini..."):
                # Aquí se llamaría a la URL de la Cloud Function
                # url = "TU_URL_DE_CLOUD_FUNCTION"
                # res = requests.post(url, json={"client_name": selected_client})
                st.success(f"¡Análisis completado para {selected_client}! Revisa la Bitácora.")
                
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
    sh_bit = gc.open_by_key(SHEET_BITACORA)
    history = pd.DataFrame(sh_bit.worksheet(TAB_BITACORA).get_all_records())
    client_history = history[history['Cliente'] == selected_client].tail(5)
    
    if not client_history.empty:
        st.table(client_history[['Fecha', 'Insight Positivo', 'Insight Negativo']])
    else:
        st.warning("No hay historial registrado para este cliente.")

except Exception as e:
    st.error(f"Error cargando el dashboard: {e}")
    st.info("Asegúrate de haber configurado el archivo 'service_account.json' en la carpeta /cloud.")
