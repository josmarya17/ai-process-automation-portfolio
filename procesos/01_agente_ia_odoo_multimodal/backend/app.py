import os
import io
import json
import logging
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import pandas as pd
from pypdf import PdfReader
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import google.generativeai as genai
from dotenv import load_dotenv
import re
import contextvars
from datetime import datetime, timezone, timedelta

# Mapeo de días y meses en español para la fecha de referencia
DIAS_ESPANOL = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
MESES_ESPANOL = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

def obtener_fecha_hora_actual_venezuela() -> str:
    """Retorna la fecha y hora actual en Venezuela (UTC-4) formateada en español."""
    tz_venezuela = timezone(timedelta(hours=-4))
    ahora = datetime.now(tz_venezuela)
    dia_semana = DIAS_ESPANOL[ahora.weekday()]
    mes = MESES_ESPANOL[ahora.month - 1]
    hora_12 = ahora.strftime("%I:%M %p")
    return f"{dia_semana}, {ahora.day} de {mes} de {ahora.year}, a las {hora_12} (Hora de Venezuela)"

def utc_to_local_venezuela(dt_str: str) -> str:
    """Convierte una cadena de fecha/hora ISO UTC (o con offset) a la zona horaria local de Venezuela (UTC-4)."""
    if not dt_str:
        return dt_str
    # Reemplazar Z por +00:00 para soporte de Python < 3.11
    if dt_str.endswith("Z"):
        dt_str = dt_str[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(dt_str)
        tz_venezuela = timezone(timedelta(hours=-4))
        dt_local = dt.astimezone(tz_venezuela)
        return dt_local.isoformat()
    except Exception as e:
        logger.warning(f"Error convirtiendo fecha {dt_str} a local de Venezuela: {str(e)}")
        return dt_str

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("XaraBackend")

# Variable de contexto para almacenar el correo de la petición actual
current_user_email: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_user_email", default=None)

# =========================================================================
# ⚙️ CONFIGURACIÓN DE APIS Y CREDENCIALES
# Reemplaza con tus IDs reales de Google Drive y Sheets
# =========================================================================
DRIVE_FOLDER_ID = "1eI5iPTNKVPXWjMS3EBy5fPu56TEzy2Z3" # ID de la carpeta de PDFs
SPREADSHEET_ID = "1c_0LOad3vqzMW6LM1SX8XER_ulPc5Vg6FVv46g6u6vw" # ID del Sheet de contactos
CREDENTIALS_FILE = "agenteia.json"             # Nombre del archivo JSON de credenciales de Google

app = FastAPI(title="Xara IA Backend", version="1.0")

# Permitir CORS para llamadas directas desde Odoo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales para almacenamiento en caché de conocimiento
manuals_cache: Dict[str, str] = {}
contacts_cache: str = ""
chat_histories: Dict[str, List[Dict]] = {} # Memoria de chat por sessionId

CACHE_FILE = os.path.join(os.path.dirname(__file__), "knowledge_cache.json")

# Intentar cargar caché persistente desde disco
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            _cache = json.load(f)
            manuals_cache = _cache.get("manuals_cache", {})
            contacts_cache = _cache.get("contacts_cache", "")
            logger.info(f"Caché cargada desde disco: {len(manuals_cache)} manuales y directorio de contactos.")
    except Exception as _e:
        logger.error(f"Error al cargar caché desde disco: {str(_e)}")

# Inicializar Google Gemini SDK
api_key = os.getenv("GEMINI_API_KEY") or "os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")"
genai.configure(api_key=api_key)

def get_google_credentials(delegate_email: str = None):
    """Carga las credenciales de la cuenta de servicio, con delegación de dominio opcional."""
    if not os.path.exists(CREDENTIALS_FILE):
        raise FileNotFoundError(f"No se encontró el archivo de credenciales '{CREDENTIALS_FILE}'. Asegúrate de descargarlo e incluirlo en la carpeta.")
    
    scopes = [
        "https://www.googleapis.com/auth/drive.readonly",
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events"
    ]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
    if delegate_email:
        try:
            logger.info(f"Aplicando delegación de dominio para impersonar a: {delegate_email}")
            creds = creds.with_subject(delegate_email)
        except Exception as e:
            logger.warning(f"No se pudo aplicar la delegación de dominio en credenciales: {str(e)}")
    return creds

def get_calendar_service(delegate_email: str = None):
    """Construye el cliente de la API de Google Calendar."""
    creds = get_google_credentials(delegate_email)
    return build("calendar", "v3", credentials=creds)

def normalizar_fecha_iso(fecha_iso: str) -> str:
    """Asegura que la fecha/hora en formato ISO tenga un offset de zona horaria (por defecto Venezuela -04:00)."""
    fecha_iso = fecha_iso.strip()
    if not fecha_iso:
        return fecha_iso
    # Si ya tiene offset o Z, la dejamos tal cual
    if fecha_iso.endswith("Z") or "+" in fecha_iso or (len(fecha_iso) > 10 and "-" in fecha_iso[10:]):
        return fecha_iso
    # De lo contrario, asumimos que es hora local de Venezuela y añadimos el offset
    return f"{fecha_iso}-04:00"

def verificar_disponibilidad(email: str, fecha_inicio_iso: str, fecha_fin_iso: str) -> str:
    """Verifica los bloques de tiempo ocupados (busy) en el calendario de un usuario en un rango de tiempo.
    
    Args:
        email: El correo del usuario a consultar.
        fecha_inicio_iso: Fecha/hora de inicio en formato ISO 8601 (ej. '2026-06-19T09:00:00').
        fecha_fin_iso: Fecha/hora de fin en formato ISO 8601 (ej. '2026-06-19T18:00:00').
    """
    fecha_inicio_normalizada = normalizar_fecha_iso(fecha_inicio_iso)
    fecha_fin_normalizada = normalizar_fecha_iso(fecha_fin_iso)
    
    logger.info(f"Herramienta: Consultando disponibilidad para {email} de {fecha_inicio_normalizada} a {fecha_fin_normalizada}")
    body = {
        "timeMin": fecha_inicio_normalizada,
        "timeMax": fecha_fin_normalizada,
        "items": [{"id": email}]
    }
    
    delegate_email = current_user_email.get()
    try:
        service = get_calendar_service(delegate_email)
        try:
            response = service.freebusy().query(body=body).execute()
        except Exception as delegation_err:
            if delegate_email:
                logger.warning(f"Fallo en verificar_disponibilidad con delegación ({str(delegation_err)}). Reintentando sin delegación...")
                service = get_calendar_service(None)
                response = service.freebusy().query(body=body).execute()
            else:
                raise delegation_err
                
        busy_periods = response.get("calendars", {}).get(email, {}).get("busy", [])
        
        # Convertir todos los bloques ocupados a la zona horaria local de Venezuela (-04:00)
        local_busy_periods = []
        for period in busy_periods:
            start_local = utc_to_local_venezuela(period.get("start", ""))
            end_local = utc_to_local_venezuela(period.get("end", ""))
            local_busy_periods.append({
                "start": start_local,
                "end": end_local
            })
            
        return json.dumps({
            "status": "success",
            "email": email,
            "busy_periods": local_busy_periods
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en verificar_disponibilidad: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"No se pudo consultar la disponibilidad del calendario: {str(e)}. Recuerda que el usuario debe compartir su calendario con el correo de la cuenta de servicio."
        }, ensure_ascii=False)

def crear_evento_calendario(titulo: str, inicio_iso: str, fin_iso: str, participantes: list[str], descripcion: str = "") -> str:
    """Crea un evento/reunión en Google Calendar e invita a los participantes.
    
    Args:
        titulo: Asunto o título de la reunión.
        inicio_iso: Fecha/hora de inicio en formato ISO 8601 (ej. '2026-06-19T10:00:00').
        fin_iso: Fecha/hora de fin en formato ISO 8601 (ej. '2026-06-19T11:00:00').
        participantes: Lista de correos electrónicos de los invitados.
        descripcion: Opcional. Descripción detallada del evento.
    """
    logger.info(f"Herramienta: Creando evento '{titulo}' para participantes: {participantes}")
    try:
        delegate_email = current_user_email.get()
        inicio_normalizada = normalizar_fecha_iso(inicio_iso)
        fin_normalizada = normalizar_fecha_iso(fin_iso)
        
        # 1. Intentar con delegación de dominio (Domain-Wide Delegation) si está disponible
        if delegate_email:
            try:
                service = get_calendar_service(delegate_email)
                attendees_list = [{"email": email.strip()} for email in participantes if email.strip()]
                
                event = {
                    "summary": titulo,
                    "description": descripcion,
                    "start": {
                        "dateTime": inicio_normalizada,
                        "timeZone": "America/Caracas"
                    },
                    "end": {
                        "dateTime": fin_normalizada,
                        "timeZone": "America/Caracas"
                    },
                    "attendees": attendees_list,
                    "conferenceData": {
                        "createRequest": {
                            "requestId": f"xara-{int(pd.Timestamp.now().timestamp())}",
                            "conferenceSolutionKey": {"type": "hangoutsMeet"}
                        }
                    }
                }
                
                logger.info(f"Intentando crear con delegación para {delegate_email} (Meet + Invitados)...")
                created_event = service.events().insert(
                    calendarId="primary",
                    body=event,
                    sendUpdates="all",
                    conferenceDataVersion=1
                ).execute()
                
                meet_link = created_event.get("hangoutLink", "No generado")
                return json.dumps({
                    "status": "success",
                    "event_id": created_event.get("id"),
                    "html_link": created_event.get("htmlLink"),
                    "meet_link": meet_link,
                    "message": "Reunión agendada exitosamente (con delegación de dominio)."
                }, ensure_ascii=False)
                
            except Exception as delegation_err:
                logger.warning(f"Fallo al crear evento con delegación de dominio para {delegate_email}: {str(delegation_err)}. Cayendo a flujos de cuenta de servicio...")

        # 2. Flujo de cuenta de servicio estándar (sin delegación)
        service = get_calendar_service(None)
        
        # Determinar el calendario destino: Priorizar el del organizador (usuario que chatea)
        # ya que es quien comparte su calendario con la cuenta de servicio.
        target_calendar = "primary"
        if delegate_email:
            target_calendar = delegate_email.strip()
        elif participantes:
            target_calendar = participantes[0].strip()
            
        # Determinar quiénes serán invitados (asistentes)
        emails_to_invite = set(email.strip() for email in participantes if email.strip())
        
        # Si la agenda destino no es la del organizador, invitar al organizador
        if delegate_email and delegate_email.lower() != target_calendar.lower():
            emails_to_invite.add(delegate_email.strip())
            
        # Filtrar al dueño del calendario destino para evitar auto-invitación
        attendees_list = [{"email": email} for email in emails_to_invite if email.lower() != target_calendar.lower()]
        
        event = {
            "summary": titulo,
            "description": descripcion,
            "start": {
                "dateTime": inicio_normalizada,
                "timeZone": "America/Caracas"
            },
            "end": {
                "dateTime": fin_normalizada,
                "timeZone": "America/Caracas"
            },
            "attendees": attendees_list,
            "conferenceData": {
                "createRequest": {
                    "requestId": f"xara-{int(pd.Timestamp.now().timestamp())}",
                    "conferenceSolutionKey": {"type": "hangoutsMeet"}
                }
            }
        }
        
        created_event = None
        
        try:
            logger.info(f"Intentando crear evento en el calendario de {target_calendar} con asistentes y Meet...")
            created_event = service.events().insert(
                calendarId=target_calendar,
                body=event,
                sendUpdates="all",
                conferenceDataVersion=1
            ).execute()
        except Exception as insert_err:
            logger.warning(f"No se pudo crear en {target_calendar} con asistentes y Meet ({str(insert_err)}).")
            
            # Si target_calendar no es primary, intentar otras variantes en el calendario del usuario
            if target_calendar != "primary":
                try:
                    logger.info(f"Reintentando en {target_calendar} con asistentes pero sin Meet...")
                    event_no_meet = event.copy()
                    event_no_meet.pop("conferenceData", None)
                    created_event = service.events().insert(
                        calendarId=target_calendar,
                        body=event_no_meet,
                        sendUpdates="all"
                    ).execute()
                except Exception as insert_err_b1:
                    logger.warning(f"No se pudo crear en {target_calendar} con asistentes y sin Meet ({str(insert_err_b1)}).")
                    
                    try:
                        logger.info(f"Reintentando en {target_calendar} sin asistentes y sin Meet...")
                        event_simple = event.copy()
                        event_simple.pop("attendees", None)
                        event_simple.pop("conferenceData", None)
                        created_event = service.events().insert(
                            calendarId=target_calendar,
                            body=event_simple,
                            sendUpdates="all"
                        ).execute()
                    except Exception as insert_err_b2:
                        logger.warning(f"Tampoco se pudo crear en {target_calendar} sin asistentes ni Meet ({str(insert_err_b2)}).")
 
            # Fallback final: Si sigue sin poder crearse en el calendario del usuario, caer al 'primary' de la cuenta de servicio
            if not created_event:
                try:
                    logger.info("Reintentando en 'primary' de la cuenta de servicio con asistentes y con Meet...")
                    emails_to_invite_cs = set(email.strip() for email in participantes if email.strip())
                    if delegate_email:
                        emails_to_invite_cs.add(delegate_email.strip())
                    
                    event_cs = event.copy()
                    event_cs["attendees"] = [{"email": email} for email in emails_to_invite_cs]
                    
                    created_event = service.events().insert(
                        calendarId="primary",
                        body=event_cs,
                        sendUpdates="all",
                        conferenceDataVersion=1
                    ).execute()
                except Exception as insert_err3:
                    logger.warning(f"Fallo en 'primary' con Meet ({str(insert_err3)}). Creando evento simple en 'primary' sin Meet ni asistentes...")
                    event_simple = event.copy()
                    event_simple.pop("attendees", None)
                    event_simple.pop("conferenceData", None)
                    created_event = service.events().insert(
                        calendarId="primary",
                        body=event_simple
                    ).execute()
            
        meet_link = created_event.get("hangoutLink", "No generado")
        
        return json.dumps({
            "status": "success",
            "event_id": created_event.get("id"),
            "html_link": created_event.get("htmlLink"),
            "meet_link": meet_link,
            "message": "Reunión agendada exitosamente."
        }, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Error en crear_evento_calendario: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": f"No se pudo crear el evento en el calendario: {str(e)}"
        }, ensure_ascii=False)

def get_all_pdfs_recursive(drive_service, folder_id: str) -> List[Dict]:
    """Busca recursivamente todos los archivos PDF en una carpeta y sus subcarpetas."""
    files_found = []
    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = drive_service.files().list(q=query, fields="files(id, name, mimeType)").execute()
        items = results.get("files", [])
        for item in items:
            if item["mimeType"] == "application/pdf":
                files_found.append(item)
            elif item["mimeType"] == "application/vnd.google-apps.folder":
                logger.info(f"Explorando subcarpeta de Drive: {item['name']} (ID: {item['id']})")
                files_found.extend(get_all_pdfs_recursive(drive_service, item["id"]))
    except Exception as e:
        logger.error(f"Error recorriendo la carpeta {folder_id}: {str(e)}")
    return files_found

# =========================================================================
# 📥 DESCARGA Y EXTRACCIÓN DE CONOCIMIENTO (DRIVE & SHEETS)
# =========================================================================

@app.post("/refresh")
def refresh_knowledge():
    """Descarga de Google Drive todos los PDFs y de Sheets la hoja de contactos para actualizar la caché en RAM."""
    global manuals_cache, contacts_cache
    try:
        creds = get_google_credentials()
        
        # 1. Descargar y procesar manuales desde Google Drive Folder (recursivo)
        logger.info(f"Conectando a Google Drive Folder ID: {DRIVE_FOLDER_ID}")
        drive_service = build("drive", "v3", credentials=creds)
        
        files = get_all_pdfs_recursive(drive_service, DRIVE_FOLDER_ID)
        
        if not files:
            logger.warning("No se encontraron archivos PDF en la carpeta de Google Drive ni en sus subcarpetas.")
        
        temp_manuals = {}
        for file in files:
            file_id = file["id"]
            file_name = file["name"]
            logger.info(f"Procesando PDF: {file_name} (ID: {file_id})")
            
            try:
                # Descargar archivo a memoria
                request = drive_service.files().get_media(fileId=file_id, acknowledgeAbuse=True)
                file_stream = io.BytesIO()
                downloader = MediaIoBaseDownload(file_stream, request)
                done = False
                while not done:
                    _, done = downloader.next_chunk()
                    
                # Extraer texto del PDF
                file_stream.seek(0)
                pdf_reader = PdfReader(file_stream)
                pdf_text = ""
                for page in pdf_reader.pages:
                    pdf_text += page.extract_text() or ""
                
                temp_manuals[file_name] = {
                    "text": pdf_text,
                    "url": f"https://drive.google.com/file/d/{file_id}/view?usp=sharing"
                }
                logger.info(f"Texto extraído con éxito ({len(pdf_text)} caracteres) de: {file_name}")
            except Exception as file_err:
                logger.error(f"Error al descargar o extraer texto del archivo {file_name} (ID: {file_id}): {str(file_err)}")
                
        manuals_cache = temp_manuals

        # 2. Descargar contactos de Google Sheets
        logger.info(f"Conectando a Google Sheets ID: {SPREADSHEET_ID}")
        sheets_service = build("sheets", "v4", credentials=creds)
        
        # Obtener metadatos de la hoja de cálculo para leer dinámicamente la primera pestaña
        sheet_meta = sheets_service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
        first_sheet_name = sheet_meta["sheets"][0]["properties"]["title"]
        logger.info(f"Leyendo la primera pestaña del Google Sheet: '{first_sheet_name}'")
        
        sheet_result = sheets_service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=f"'{first_sheet_name}'!A:Z"
        ).execute()
        
        values = sheet_result.get("values", [])
        if not values:
            logger.warning("La hoja de cálculo de Google Sheets está vacía.")
            contacts_cache = "No hay contactos registrados."
        else:
            # Convertir la lista de listas en un formato de texto estructurado entendible para Gemini
            headers = values[0]
            rows = values[1:]
            df = pd.DataFrame(rows, columns=headers)
            contacts_cache = df.to_string(index=False)
            logger.info("Directorio de contactos de Google Sheets cargado exitosamente.")

        # Guardar en disco para evitar esperas y re-descargas en reboots
        try:
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "manuals_cache": manuals_cache,
                    "contacts_cache": contacts_cache
                }, f, ensure_ascii=False, indent=2)
            logger.info("Caché guardada en disco exitosamente.")
        except Exception as save_err:
            logger.error(f"Error guardando caché en disco: {str(save_err)}")

        return {
            "status": "success",
            "message": "Base de conocimientos actualizada con éxito.",
            "manuales_cargados": list(manuals_cache.keys()),
            "contactos_longitud": len(contacts_cache)
        }

    except Exception as e:
        logger.error(f"Error al actualizar la base de conocimientos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error cargando conocimiento: {str(e)}")

# =========================================================================
# 💬 ENDPOINT DEL CHAT WEBHOOK
# =========================================================================

def buscar_manuales_relevantes(query: str, manuals: dict, top_n: int = 3) -> dict:
    """Busca y filtra los manuales más relevantes para la consulta usando un score de palabras clave."""
    if not query:
        return {}
        
    # Limpiar y tokenizar la consulta
    words = re.findall(r'\w+', query.lower())
    # Filtrar stopwords comunes en español de longitud <= 2
    words = [w for w in words if len(w) > 2]
    
    if not words:
        return {}
        
    scored_manuals = []
    for name, content in manuals.items():
        score = 0
        pdf_text = content.get("text", "").lower() if isinstance(content, dict) else str(content).lower()
        title_lower = name.lower()
        
        # Puntuación por coincidencia de palabras clave
        for word in words:
            # Coincidencias en el título tienen mucho peso
            if word in title_lower:
                score += 20
            # Coincidencias en el texto
            score += pdf_text.count(word)
            
        # Coincidencia de frases de 2 o más palabras consecutivas de la consulta
        for i in range(len(words) - 1):
            phrase = f"{words[i]} {words[i+1]}"
            if phrase in title_lower:
                score += 50
            if phrase in pdf_text:
                score += 15
                
        if score > 0:
            scored_manuals.append((score, name, content))
            
    # Ordenar por puntuación descendente
    scored_manuals.sort(key=lambda x: x[0], reverse=True)
    
    # Tomar las mejores
    top_results = scored_manuals[:top_n]
    
    # Devolver como dict
    return {name: content for _, name, content in top_results}

class WebhookPayload(BaseModel):
    message: str
    category: str
    user: str
    email: Optional[str] = None
    timestamp: str
    sessionId: Optional[str] = "default"

@app.post("/webhook")
async def chat_webhook(payload: WebhookPayload):
    global manuals_cache, contacts_cache, chat_histories
    
    # Almacenar el correo del usuario en el contexto de la petición actual
    current_user_email.set(payload.email)
    
    # Validar dominios corporativos autorizados
    user_email = payload.email
    if user_email:
        email_lower = user_email.lower()
        if not (email_lower.endswith("@Empresa Demo.com") or email_lower.endswith("@Enterprise SGC.com")):
            return {
                "output": "⚠️ Acceso denegado: El dominio de tu cuenta no está autorizado para usar Xara."
            }
            
    # Validar API Key
    if not api_key:
        return {
            "output": "⚠️ El servidor no tiene configurada la variable de entorno GEMINI_API_KEY o una clave válida. Configúrala para continuar."
        }

    # Si la caché está vacía en la primera consulta, intentar cargarla
    if not manuals_cache and not contacts_cache:
        logger.info("La caché de conocimiento está vacía. Ejecutando refresh automático...")
        try:
            refresh_knowledge()
        except Exception as e:
            logger.error(f"Fallo el refresh automático en la primera consulta: {str(e)}")
            # Continuamos, el agente responderá con su conocimiento estándar si no hay acceso a Drive/Sheets

    # 1. Recuperar o inicializar historial de chat por sesión
    session_id = payload.sessionId or "default"
    if session_id not in chat_histories:
        chat_histories[session_id] = []
    
    history = chat_histories[session_id]

    # 2. Filtrar manuales relevantes usando RAG simple
    # Combinar la consulta actual con el último mensaje del usuario para mantener el contexto conversacional en RAG
    search_query = payload.message
    if history:
        last_user_msg = next((msg["text"] for msg in reversed(history) if msg["role"] == "user"), "")
        if last_user_msg:
            search_query += " " + last_user_msg

    manuals_text = ""
    relevant_manuals = buscar_manuales_relevantes(search_query, manuals_cache, top_n=3)
    if relevant_manuals:
        logger.info(f"RAG: Seleccionados {len(relevant_manuals)} manuales relevantes para la consulta.")
        for name, content in relevant_manuals.items():
            if isinstance(content, dict):
                pdf_text = content.get("text", "")
                pdf_url = content.get("url", "")
            else:
                pdf_text = content
                pdf_url = ""
            manuals_text += f"\n--- INICIO MANUAL: {name} (Enlace: {pdf_url}) ---\n{pdf_text}\n--- FIN MANUAL: {name} ---\n"
    else:
        logger.info("RAG: No se encontraron manuales relevantes para la consulta.")

    # 3. Diseñar el System Prompt Estricto (Guardrails de Alcance, Idioma, No Multimedia y Formato HTML)
    system_prompt = f"""Eres "Xara", una asistenta de IA corporativa altamente capacitada y especializada en el ecosistema de Odoo v17 y el soporte de procesos internos para nuestra cadena de farmacias (Empresa Demo o Farmacias Enterprise SGC).

Te estás comunicando con {payload.user} (correo: {payload.email if payload.email else "No proporcionado"}). Dirígete a {payload.user} por su nombre de pila de forma natural, amistosa y profesional en tus saludos y respuestas.

## FECHA Y HORA ACTUAL DE REFERENCIA (CRÍTICO)
- Fecha y hora actual en Venezuela: {obtener_fecha_hora_actual_venezuela()}
- Usa esta fecha y hora como la referencia absoluta para resolver "hoy", "mañana", "ayer", "la próxima semana", o para agendar/consultar la disponibilidad en el calendario. No asumas ninguna otra fecha.

## LÍMITES Y GUARDRAILS ESTRICTOS (CRÍTICO)
* **IDIOMA OBLIGATORIO**: Todas tus respuestas, comentarios y explicaciones deben estar escritos estrictamente en Español. NUNCA respondas en inglés, a menos que el usuario lo solicite explícitamente en inglés.
* **Alcance Exclusivo**: Solo responderás preguntas relacionadas con:
  1. Funcionamiento de Odoo v17 Estándar (Compras, Ventas, Inventario, Punto de Venta, Contabilidad, etc.).
  2. Procesos, normas y manuales corporativos de Empresa Demo o Farmacias Enterprise SGC (recuperados de la sección de Manuales abajo).
  3. Directorio, extensiones y disponibilidad de agenda del equipo (recuperados de la sección de Contactos abajo).
* **Restricción de Preguntas Fuera de Alcance**: Si el usuario te hace preguntas sobre otros temas (programación que no sea de Odoo, consejos personales, cultura general, recetas, etc.), debes rechazar responder de forma profesional y educada:
  "Lo siento, como asistenta Xara, solo puedo ayudarte con dudas sobre Odoo v17, procesos internos de Empresa Demo o Farmacias Enterprise SGC, y directorio/disponibilidad del equipo."
* **Enlaces de Documentación (CRÍTICO)**: Siempre que hables de un manual, norma, procedimiento o flujo de la empresa, debes incluir su enlace de Google Drive (indicado como "Enlace" al inicio de cada manual) en la respuesta usando una etiqueta HTML de enlace clásica (por ejemplo: <a href="URL" target="_blank">Nombre del Manual</a>). Tienes prohibido inventar o incluir enlaces externos que no sean los indicados en la base de conocimientos para la documentación.
* **Gestión de Calendario y Zona Horaria (Caracas)**: Tienes acceso a herramientas para verificar la disponibilidad (`verificar_disponibilidad`) y crear eventos de Google Calendar (`crear_evento_calendario`).
  - La zona horaria corporativa y de trabajo es la de Venezuela (America/Caracas, UTC-4).
  - Todas las horas que uses para agendar o comprobar disponibilidad deben ser tratadas e interpretadas en la hora local de Venezuela (ej. si el usuario dice "a las 11:00 am", es hora de Caracas).
  - Al ejecutar herramientas, proporciona las fechas/horas en formato ISO 8601 local sin el sufijo 'Z' (ej: '2026-06-19T11:00:00') para asegurar la correcta interpretación local.
  - Si el usuario solicita agendar una reunión, verificar disponibilidad o coordinar una cita:
    1. Si no conoces el correo del participante, búscalo en el directorio corporativo de contactos de Google Sheets.
    2. Utiliza la herramienta para comprobar el rango horario solicitado.
    3. Procede a agendar la reunión e informa al usuario sobre el enlace del evento y el enlace de Google Meet si se genera.
* **Consultoría de Odoo v17 (Precisión Contable)**: Cuando guíes al usuario en el sistema Odoo v17 (especialmente en la conciliación bancaria y el tablero contable), sé exhaustivo y preciso. Explica detalladamente que en el tablero de Contabilidad no se debe buscar una opción genérica llamada "Banco", sino que deben hacer clic en el nombre del diario bancario específico correspondiente (por ejemplo, el banco de la cuenta a conciliar: Banesco, Mercantil, etc., ya que existen múltiples diarios de tipo Banco configurados para cada farmacia) o pulsar el botón de 'Conciliar apuntes' (o 'Reconcile') que se muestra en la tarjeta del diario respectivo.
* **Prohibición de Multimedia**: Tienes estrictamente prohibido generar o intentar mostrar imágenes, animaciones complejas, GIFs o videos.
* **Respuestas Exactas**: Cuando te pregunten sobre un procedimiento o manual (por ejemplo: diferencias de caja, arqueo sorpresa, conciliación, etc.), busca detalladamente en la sección de Manuales abajo y entrega el paso a paso exacto leído del texto de forma redactada y profesional.
* **Prohibición de Markdown y Formato de Respuesta (CRÍTICO - ESTRICTO)**:
  - Tienes ESTRICTAMENTE PROHIBIDO usar caracteres de markdown como asteriscos (* o **) o guiones sueltos en tus respuestas para formatear texto (como negritas, cursivas o viñetas). El chat de Odoo no renderiza Markdown y mostrará estos caracteres literalmente en la pantalla, dañando el diseño visual.
  - En su lugar, usa únicamente HTML válido para estructurar la respuesta.
  - Para poner texto en negrita, usa exclusivamente las etiquetas `<strong>texto</strong>` (o `<b>texto</b>`).
  - Para poner texto en cursiva, usa exclusivamente `<em>texto</em>` (o `<i>texto</i>`).
  - Para listas numeradas, usa estrictamente las etiquetas `<ol>` y `<li>`.
  - Para listas con viñetas, usa estrictamente `<ul>` y `<li>`. Cada elemento de la lista debe ir dentro de su etiqueta `<li>` en una línea nueva.
  - Usa `<p>` para párrafos.

## BASE DE CONOCIMIENTOS (MANUALES DE LA EMPRESA)
{manuals_text if manuals_text else "No hay manuales relevantes en caché para esta consulta."}

## DIRECTORIO DE CONTACTOS DE LA EMPRESA
{contacts_cache if contacts_cache else "No hay contactos registrados en el directorio."}
"""


    # 4. Intentar procesar la consulta iterando sobre modelos con cuota disponible (multi-model fallback)
    models_to_try = ["gemini-3.1-flash-lite", "gemini-2.5-flash-lite", "gemini-2.5-flash"]
    response_text = None
    last_error = None

    # Estructurar el formato de historial compatible con el SDK de Gemini
    # El SDK de Gemini espera una lista de objetos Content del tipo: {'role': 'user'|'model', 'parts': [text]}
    gemini_history = []
    for msg in history:
        gemini_history.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [msg["text"]]
        })

    logger.info(f"[{session_id}] Consulta recibida ({payload.category}): {payload.message}")

    for model_name in models_to_try:
        try:
            logger.info(f"Intentando procesar con modelo: {model_name}")
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt,
                tools=[verificar_disponibilidad, crear_evento_calendario]
            )

            # Iniciar chat de Gemini con el historial acumulado y soporte de herramientas automáticas
            chat = model.start_chat(
                history=gemini_history,
                enable_automatic_function_calling=True
            )
            
            # Enviar el nuevo mensaje a la sesión de Gemini
            response = chat.send_message(payload.message)
            response_text = response.text
            logger.info(f"Éxito procesando con modelo: {model_name}")
            break  # Éxito, salir del bucle
        except Exception as e:
            logger.warning(f"Fallo con el modelo {model_name}: {str(e)}")
            last_error = e

    if response_text is not None:
        # Guardar en memoria local el nuevo par de mensajes (Historial)
        history.append({"role": "user", "text": payload.message})
        history.append({"role": "model", "text": response_text})
        
        # Limitar historial para no sobrecargar de forma innecesaria en RAM (guardamos las últimas 20 interacciones)
        if len(history) > 40:
            chat_histories[session_id] = history[-40:]

        return {
            "output": response_text
        }
    else:
        error_msg = str(last_error) if last_error else "Todos los modelos de Gemini fallaron."
        logger.error(f"Error procesando la consulta en todos los modelos: {error_msg}")
        return {
            "output": f"<div style='color: #ef4444;'>⚠️ Error en el cerebro de Xara IA (Todos los modelos fallaron): {error_msg}</div>"
        }

# Arrancar servidor uvicorn local
if __name__ == "__main__":
    logger.info("Iniciando Xara Backend local en http://localhost:8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
