import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from src import config

# Permisos requeridos para leer/escribir en Drive y Sheets
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

class GoogleAuthError(Exception):
    """Excepción para errores de autenticación con Google."""
    pass

def get_credentials():
    """
    Carga o genera las credenciales OAuth2.
    Si token.json existe, lo usa. Si no, o si expiró, intenta refrescarlo.
    Si no puede refrescarlo o no existe, usa credentials.json para iniciar el login web.
    """
    creds = None
    
    # 1. Cargar el token local si existe
    if os.path.exists(config.TOKEN_FILE):
        config.logger.info("Cargando token de autenticación desde token.json...")
        try:
            creds = Credentials.from_authorized_user_file(config.TOKEN_FILE, SCOPES)
        except Exception as e:
            config.logger.error(f"Error al cargar token.json: {e}")
            creds = None

    # 2. Si no hay credenciales válidas, intentar refrescar o iniciar sesión de cero
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            config.logger.info("El token ha expirado. Intentando refrescarlo automáticamente...")
            try:
                creds.refresh(Request())
            except Exception as e:
                config.logger.warning(f"No se pudo refrescar el token: {e}. Se requiere login nuevo.")
                creds = None
        
        if not creds:
            # Validar que exista el archivo credentials.json
            if not os.path.exists(config.CREDENTIALS_FILE):
                error_msg = (
                    "No se encontró el archivo 'credentials.json' en la raíz del proyecto.\n"
                    "Por favor, descarga tus credenciales OAuth de tipo 'Desktop Application' desde "
                    "Google Cloud Console y colócalas en la carpeta de trabajo del proyecto."
                )
                config.logger.error(error_msg)
                raise GoogleAuthError(error_msg)
            
            config.logger.info("Iniciando flujo de autenticación OAuth de Google a través del navegador...")
            try:
                flow = InstalledAppFlow.from_client_secrets_file(config.CREDENTIALS_FILE, SCOPES)
                # Ejecutar servidor local en un puerto aleatorio para recibir el token de redirección
                creds = flow.run_local_server(port=0)
                
                # Guardar las credenciales autorizadas en token.json
                with open(config.TOKEN_FILE, 'w') as token:
                    token.write(creds.to_json())
                config.logger.info("¡Sesión iniciada correctamente! Credenciales guardadas en token.json.")
            except Exception as e:
                raise GoogleAuthError(f"Error durante el proceso de autenticación por navegador: {e}")
                
    return creds

def get_sheets_service():
    """Retorna el cliente de servicio para Google Sheets API."""
    creds = get_credentials()
    return build('sheets', 'v4', credentials=creds)

def get_drive_service():
    """Retorna el cliente de servicio para Google Drive API."""
    creds = get_credentials()
    return build('drive', 'v3', credentials=creds)
