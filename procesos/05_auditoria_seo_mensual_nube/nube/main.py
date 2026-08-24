import os
import sys
import json
import functions_framework
import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest,
    DateRange,
    Dimension,
    Metric,
    OrderBy,
)
import google.generativeai as genai
import gspread
import datetime
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import streamlit as st

# Intentar cargar configuración
try:
    from .config import *
except (ImportError, ValueError):
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.append(current_dir)
        from config import *
    except:
        # Fallback si todo falla, aunque debería existir
        pass

# Configuración de Logging
logging.basicConfig(level=logging.INFO)

def get_secret(key, default=None):
    """Obtiene de forma segura un valor de st.secrets evitando StreamlitSecretNotFoundError"""
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return default


def get_service_account_credentials():
    """Carga las credenciales de Service Account desde Secrets o archivo local"""
    sa_secret = get_secret("gcp_service_account")
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/webmasters",
        "https://www.googleapis.com/auth/analytics.readonly",
    ]
    if sa_secret:
        return service_account.Credentials.from_service_account_info(dict(sa_secret), scopes=scopes)
    sa_path = f"cloud/{SERVICE_ACCOUNT_FILE}"
    if os.path.exists(sa_path):
        return service_account.Credentials.from_service_account_file(sa_path, scopes=scopes)
    return None


def get_credentials(token_name="token_wac.json"):
    token_path = f"cloud/{token_name}"
    
    possible_keys = [
        token_name,                             # "token_wac.json"
        token_name.replace(".json", ""),        # "token_wac"
        f"token_{token_name}",                  # "token_token_wac.json"
        f"token_{token_name.replace('.json', '')}" # "token_token_wac"
    ]
    
    creds_dict = None
    # 1. Streamlit Secrets
    for key in possible_keys:
        val = get_secret(key)
        if val:
            creds_dict = dict(val)
            break

    # 2. Environment Variables (Para GitHub Actions)
    if not creds_dict:
        env_key = token_name.replace(".json", "").upper()
        token_env = os.environ.get(env_key) or os.environ.get(f"{env_key}_JSON")
        if token_env:
            try:
                creds_dict = json.loads(token_env)
            except Exception as e:
                logging.warning(f"Error parseando env var {env_key}: {e}")

    creds = None
    if creds_dict:
        try:
            creds = Credentials.from_authorized_user_info(creds_dict)
        except Exception as e:
            logging.warning(f"Error parseando credenciales de usuario: {e}")

    # 3. Archivo Local
    if not creds and os.path.exists(token_path):
        try:
            creds = Credentials.from_authorized_user_file(token_path)
        except Exception as e:
            logging.warning(f"Error cargando token local ({token_path}): {e}")

    # 4. Refrescar si es necesario
    if creds and creds.expired and creds.refresh_token:
        try:
            client_config = get_secret("client_secret")
            if not client_config:
                cs_env = os.environ.get("CLIENT_SECRET_JSON")
                if cs_env:
                    client_config = json.loads(cs_env)
                elif os.path.exists("cloud/client_secret.json"):
                    with open("cloud/client_secret.json", "r") as f:
                        client_config = json.load(f)
            
            creds.refresh(Request())
            if get_secret(f"token_{token_name}") is None and os.path.exists(token_path):
                with open(token_path, 'w') as token_file:
                    token_file.write(creds.to_json())
        except Exception as e:
            logging.warning(f"⚠️ No se pudo refrescar token OAuth ({token_name}): {e}. Utilizando Service Account como fallback...")
            creds = None

    # 5. Fallback a Service Account si OAuth falló o expiró
    if not creds:
        creds = get_service_account_credentials()

    if not creds:
        st.error(f"⚠️ No se encontraron credenciales válidas en Secrets ni en archivos locales.")
        raise Exception(f"Falta configuración de autenticación para {token_name} y Service Account")

    return creds



def fetch_gsc_data(service, property_uri):
    """Extrae datos de GSC para el MES ANTERIOR completo"""
    today = datetime.date.today()
    # Calcular primer día de este mes y restar uno para ir al mes anterior
    first_day_this_month = today.replace(day=1)
    last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)
    
    start_date = first_day_prev_month
    end_date = last_day_prev_month
    
    request = {
        'startDate': start_date.strftime('%Y-%m-%d'),
        'endDate': end_date.strftime('%Y-%m-%d'),
        'dimensions': ['date']
    }
    
    response = service.searchanalytics().query(siteUrl=property_uri, body=request).execute()
    if 'rows' not in response:
        return pd.DataFrame()
    
    df = pd.DataFrame([
        {
            'date': r['keys'][0],
            'clicks': r['clicks'],
            'impressions': r['impressions'],
            'ctr': r['ctr'],
            'position': r['position']
        } for r in response['rows']
    ])
    return df

def fetch_ga4_data(client, property_id):
    """Extrae datos de GA4 para el MES ANTERIOR completo"""
    today = datetime.date.today()
    first_day_this_month = today.replace(day=1)
    last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
    first_day_prev_month = last_day_prev_month.replace(day=1)
    
    start_date = first_day_prev_month
    end_date = last_day_prev_month
    
    request = RunReportRequest(
        property=f"properties/{property_id}",
        dimensions=[Dimension(name="sessionDefaultChannelGroup")],
        metrics=[
            Metric(name="activeUsers"),
            Metric(name="newUsers"),
            Metric(name="sessions"),
            Metric(name="conversions"),
        ],
        date_ranges=[DateRange(start_date=start_date.strftime('%Y-%m-%d'), end_date=end_date.strftime('%Y-%m-%d'))],
    )
    
    response = client.run_report(request)
    
    data = []
    for row in response.rows:
        data.append({
            'channel': row.dimension_values[0].value,
            'activeUsers': int(row.metric_values[0].value),
            'newUsers': int(row.metric_values[1].value),
            'sessions': int(row.metric_values[2].value),
            'conversions': float(row.metric_values[3].value),
        })
    
    return pd.DataFrame(data)

def fetch_sheets_data(creds, client_name):
    """Recopila data de los Sheets de apoyo"""
    import os
    import logging
    gc = gspread.authorize(creds)
    
    # 1. Backlinks y Competidores
    try:
        sh_backlinks = gc.open_by_key(SHEET_BACKLINKS)
        # Detective: Si falla, listar lo que sí hay
        try:
            df_backlinks = pd.DataFrame(sh_backlinks.worksheet(TAB_BACKLINKS).get_all_records())
        except:
            available = [w.title for w in sh_backlinks.worksheets()]
            logging.error(f"❌ No se halló pestaña '{TAB_BACKLINKS}'. Disponibles: {available}")
            df_backlinks = pd.DataFrame()
            
        try:
            df_comp = pd.DataFrame(sh_backlinks.worksheet(TAB_COMPETIDORES).get_all_records())
        except:
            available = [w.title for w in sh_backlinks.worksheets()]
            logging.error(f"❌ No se halló pestaña '{TAB_COMPETIDORES}'. Disponibles: {available}")
            df_comp = pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Error total accediendo a SHEET_BACKLINKS: {e}")
        df_backlinks, df_comp = pd.DataFrame(), pd.DataFrame()
    
    # 2. SEO Técnico
    try:
        sh_tech = gc.open_by_key(SHEET_TECH)
        try:
            df_ps = pd.DataFrame(sh_tech.worksheet(TAB_PAGESPEED).get_all_records())
        except:
            available = [w.title for w in sh_tech.worksheets()]
            logging.error(f"❌ No se halló pestaña '{TAB_PAGESPEED}'. Disponibles: {available}")
            df_ps = pd.DataFrame()
            
        # Intentar buscar pestaña específica del cliente
        try:
            df_audit = pd.DataFrame(sh_tech.worksheet(client_name).get_all_records())
        except:
            df_audit = pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Error total accediendo a SHEET_TECH: {e}")
        df_ps, df_audit = pd.DataFrame(), pd.DataFrame()
        
    # 3. Moz DA
    try:
        sh_moz = gc.open_by_key(SHEET_MOZ)
        try:
            df_moz = pd.DataFrame(sh_moz.worksheet(TAB_MOZ).get_all_records())
        except:
            available = [w.title for w in sh_moz.worksheets()]
            logging.error(f"❌ No se halló pestaña '{TAB_MOZ}'. Disponibles: {available}")
            df_moz = pd.DataFrame()
    except Exception as e:
        logging.error(f"❌ Error total accediendo a SHEET_MOZ: {e}")
        df_moz = pd.DataFrame()
    
    return {
        'backlinks': df_backlinks,
        'competitors': df_comp,
        'pagespeed': df_ps,
        'audit': df_audit,
        'moz': df_moz
    }

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def generate_seo_insights(client_name, gsc_df, ga4_df, other_data):
    """Utiliza Gemini (AI Studio) para generar 2 insights estratégicos"""
    # Priorizar API Key de Entorno (GitHub Actions), Secrets (Streamlit) o config.py
    api_key = os.environ.get("API_GEMINI") or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        api_key = get_secret("API_GEMINI") or get_secret("GEMINI_API_KEY")
    if not api_key:
        api_key = GEMINI_API_KEY

    
    # Debug: Mostrar ultimos 4 digitos para validar en logs
    if api_key:
        masked_key = f"***{api_key[-4:]}"
        logging.info(f"Usando Gemini con API Key: {masked_key}")
    else:
        logging.error("❌ GEMINI_API_KEY está vacía.")
        return "Error: API Key no configurada.", "Revisa tus Secrets en GitHub/Streamlit."

    genai.configure(api_key=api_key)
    
    # --- EXPLORACIÓN DE MODELOS DISPONIBLES ---
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        logging.info(f"Modelos disponibles en tu cuenta: {available_models}")
    except Exception as e:
        logging.warning(f"No se pudo listar modelos: {e}")
        available_models = ["models/gemini-2.5-flash", "models/gemini-3.6-flash", "models/gemini-flash-latest"]

    if not available_models:
        available_models = ["models/gemini-2.5-flash", "models/gemini-3.6-flash", "models/gemini-flash-latest"]

    # Elegir el mejor modelo disponible
    # Prioridad: 3.6-flash -> 3.5-flash -> 3.1-flash -> 2.5-flash -> flash-latest
    ordered_priority = ["3.6-flash", "3.5-flash", "3.1-flash", "2.5-flash", "flash-latest", "flash-lite"]

    
    target_models = []
    for pref in ordered_priority:
        for name in available_models:
            if pref in name.lower() and name not in target_models:
                target_models.append(name)
    
    # Añadir el resto por si acaso
    for name in available_models:
        if name not in target_models:
            target_models.append(name)

    model = None
    last_err = ""
    
    for model_name in target_models:
        try:
            logging.info(f"Probando modelo: {model_name}...")
            m = genai.GenerativeModel(model_name)
            # Prueba rápida de generación
            m.generate_content("Responde 'ok'")
            model = m
            logging.info(f"✅ Modelo {model_name} aceptado y con cuota disponible.")
            break
        except Exception as e:
            last_err = str(e)
            if "429" in last_err or "Quota" in last_err:
                logging.warning(f"⚠️ Modelo {model_name} sin cuota (429). Saltando al siguiente...")
            else:
                logging.warning(f"⚠️ Modelo {model_name} dio error: {last_err}. Saltando...")
            continue
            
    if not model:
        raise Exception(f"No se pudo conectar con ningún modelo. (Último error: {last_err})")
    
    # Resumen de datos para el prompt (Limpieza exhaustiva)
    gsc_summary = gsc_df.describe().to_string() if not gsc_df.empty else "Sin datos"
    ga4_summary = ga4_df.to_string()[:1500] if not ga4_df.empty else "Sin datos"
    
    # Reducir peso de other_data
    other_summary = str(other_data)[:1000] if other_data else "Sin datos"
    
    prompt = f"""
    ERES EL DIRECTOR ESTRATÉGICO SEO DE UNA AGENCIA TOP. 
    Analiza los datos del último mes para el cliente '{client_name}' y genera una interpretación ejecutiva.
    
    CONTEXTO DE DATOS:
    - GSC (Tendencias): {gsc_summary}
    - GA4 (Tráfico/Conversión): {ga4_summary}
    - OTROS (Tech/Backlinks): {other_summary}
    
    REQUISITOS DE SALIDA (ESTRICTO):
    Debes devolver exactamente dos bloques de texto, cada uno de máximo 40 palabras, con este formato:
    IMPACTO: [Tu análisis sobre el impacto del contenido y rendimiento actual]
    RETOS: [Tu análisis sobre oportunidades perdidas, retos técnicos o pasos a seguir]
    
    TONO: Profesional, estratégico, basado en datos, directo al punto. Evita obviedades como "el tráfico subió". Explica "por qué" o qué significa para el negocio.
    """
    
    response = model.generate_content(prompt)
    full_text = response.text
    
    # Parsing inteligente de la respuesta
    impacto = "No se pudo generar análisis de impacto."
    retos = "No se pudieron identificar retos estratégicos."
    
    if "IMPACTO:" in full_text and "RETOS:" in full_text:
        parts = full_text.split("RETOS:")
        impacto = parts[0].replace("IMPACTO:", "").strip()
        retos = parts[1].strip()
    elif "\n" in full_text:
        lines = [l.strip() for l in full_text.split("\n") if l.strip()]
        if len(lines) >= 2:
            impacto = lines[0]
            retos = lines[1]
    else:
        impacto = full_text

    return impacto, retos

@functions_framework.http
def main_http(request):
    """Punto de entrada compatible con Cloud Functions (HTTP)"""
    request_json = request.get_json(silent=True)
    client_to_process = request_json.get('client_name') if request_json else None
    return main_execution(client_to_process)

def main_execution(client_to_process=None, token_name="token_wac.json"):
    """Lógica central de ejecución (puede llamarse localmente o por HTTP)"""
    import os
    import logging
    import pandas as pd
    creds = get_credentials(token_name=token_name)
    gsc_service = build('webmasters', 'v3', credentials=creds)
    ga4_client = BetaAnalyticsDataClient(credentials=creds)
    gc = gspread.authorize(creds)
    
    # Leer inventario
    sh_inv = gc.open_by_key(SHEET_INVENTARIO)
    inventory = pd.DataFrame(sh_inv.worksheet(TAB_INVENTARIO).get_all_records())
    
    # Normalizar inventario
    # Normalizar inventario: Nombres de columnas
    inventory.columns = [c.lower().strip().replace(" ", "_").replace("-", "_") for c in inventory.columns]
    
    # Debug: Ver columnas y primeras filas
    logging.info(f"Columnas detectadas en Inventario: {list(inventory.columns)}")
    
    # Filtrar clientes activos (más robusto: strip y lower)
    inventory['activo_str'] = inventory['activo'].astype(str).str.lower().str.strip()
    active_clients = inventory[inventory['activo_str'].isin(['true', 'verdadero', 'si', 'yes', '1'])]
    
    logging.info(f"Total clientes activos encontrados (antes de filtro token): {len(active_clients)}")
    
    # Filtro inteligente por Token (Columna 'Cuenta de google' o 'Acceso')
    # Extraer el ID del token (wac, wac2, etc) desde el nombre del archivo
    token_id = token_name.lower().replace("token_", "").replace(".json", "").strip() 
    
    # Buscar el nombre de la columna (normalizado)
    col_token = None
    for c in ['cuenta_de_google', 'acceso', 'token']:
        if c in active_clients.columns:
            col_token = c
            break
            
    if col_token:
        # Limpiar la columna para comparar
        active_clients['token_clean'] = active_clients[col_token].astype(str).str.lower().str.strip()
        logging.info(f"Filtrando clientes usando columna '{col_token}' para el ID: '{token_id}'")
        
        # Mostrar valores únicos para debug
        valores_unicos = active_clients['token_clean'].unique()
        logging.info(f"Valores únicos en columna '{col_token}': {valores_unicos}")
        
        active_clients = active_clients[active_clients['token_clean'] == token_id]
        logging.info(f"Clientes finales encontrados para esta cuenta: {len(active_clients)}")
    else:
        logging.warning("⚠️ No se encontró columna de filtrado ('Cuenta de google' o 'acceso'). Procesando todo.")
    
    if client_to_process:
        active_clients = active_clients[active_clients['marca'] == client_to_process]
        
    results = []
    for _, row in active_clients.iterrows():
        client_name = row['marca']
        gsc_uri = row['propiedad_gsc'] 
        ga4_id = row['propiedad_ga4']  
        
        logging.info(f"--- Iniciando procesamiento para: {client_name} ---")
        
        # 1. Extraer data con manejo de errores individual
        try:
            logging.info("Extrayendo GSC...")
            gsc_df = fetch_gsc_data(gsc_service, gsc_uri)
        except Exception as e:
            logging.error(f"Error GSC: {e}")
            gsc_df = pd.DataFrame()

        try:
            logging.info("Extrayendo GA4...")
            ga4_df = fetch_ga4_data(ga4_client, ga4_id)
        except Exception as e:
            logging.error(f"Error GA4: {e}")
            ga4_df = pd.DataFrame()

        try:
            logging.info("Extrayendo Sheets de apoyo...")
            other_data = fetch_sheets_data(creds, client_name)
        except Exception as e:
            logging.error(f"Error Sheets: {e}")
            other_data = {}
        
        # 2. Generar Insight con Gemini (Nivel Senior)
        try:
            logging.info("Consultando a Gemini (Nivel Estratégico)...")
            impacto, retos = generate_seo_insights(client_name, gsc_df, ga4_df, other_data)
        except Exception as e:
            msg_err = f"Error en Gemini: {str(e)}"
            logging.error(msg_err)
            impacto = "Error en el motor de IA."
            retos = str(e)[:100]
        
        # 3. Guardar en Bitácora (Estructura Estratégica)
        try:
            logging.info("Escribiendo en Bitácora...")
            sh_bit = gc.open_by_key(SHEET_BITACORA)
            ws_bit = sh_bit.worksheet(TAB_BITACORA)
            
            # Calcular Fecha del mes analizado (01 del mes anterior)
            today = datetime.date.today()
            first_day_this_month = today.replace(day=1)
            last_day_prev_month = first_day_this_month - datetime.timedelta(days=1)
            fecha_analisis = last_day_prev_month.replace(day=1)
            
            # Formato de Bitácora: Fecha | Marca | Impacto (Positivo) | Retos (Negativo) | Periodo
            periodo = fecha_analisis.strftime("%m-%Y")
            ws_bit.append_row([
                fecha_analisis.strftime('%Y-%m-%d'),
                client_name,
                impacto,
                retos,
                periodo
            ])
            results.append({"client": client_name, "status": "success"})
        except Exception as e:
            logging.error(f"Error escribiendo bitacora: {e}")
            results.append({"client": client_name, "status": "partial_error", "details": str(e)})
        
    return {"status": "completed", "processed": results}

if __name__ == "__main__":
    # Ejecución manual para GitHub Actions o Pruebas locales
    import sys
    import os
    
    client_arg = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Identificar todos los tokens disponibles en el entorno (TOKEN_WAC, TOKEN_WAC2, etc)
    tokens_to_process = [k for k in os.environ.keys() if k.startswith("TOKEN_")]
    
    if not tokens_to_process:
        # Si no hay variables de entorno, intentar con el default local
        print(f"🚀 Iniciando ejecución local/manual...")
        res = main_execution(client_arg)
        print(f"📊 Resultado: {res}")
    else:
        print(f"🚀 Iniciando ejecución automática MULTI-CUENTA ({len(tokens_to_process)} tokens detectados)")
        for token_env_name in tokens_to_process:
            # Reconstruir el nombre de archivo virtual para la lógica de get_credentials
            virtual_filename = token_env_name.lower().replace("_json", "") + ".json"
            print(f"--- Procesando cuenta: {token_env_name} (asociada a {virtual_filename}) ---")
            try:
                res = main_execution(client_to_process=client_arg, token_name=virtual_filename)
                print(f"✅ Resultado para {token_env_name}: {res}")
            except Exception as e:
                print(f"❌ Error procesando {token_env_name}: {e}")
