# Configuración del Sistema SEO Auto Analyst
PROJECT_ID = "wearecontent-gsc-391421"

# IDs de Google Sheets
SHEET_INVENTARIO = "1z6TiZ7VvQ5zCHJCAOZS_8QuFingwfsw_pI8hsZ-LopI"  # Control de Marcas
SHEET_BITACORA = "1igmuV15uHc0zmmoXTcjQbymOKjCtz4A8fxIP-0lY5d0"    # Migración/Bitácora
SHEET_BACKLINKS = "1agHhOqJUmL2qwHcv4QidvsEokYU8pcFMOlZq_NUFt0I"   # BBDD Backlinks
SHEET_TECH = "1VBeCqrksZwnN37uGP6BPncKsggxysGBq57IeQh4NrLw"        # BBDD Data_SEO Tecnico
SHEET_MOZ = "1HWPiyHibPgtQ1w52yHO5sEP-W_8tXhMGn5Fi1z4VXpc"         # BBDD Registro_DA

# Nombres de Hojas (Tabs)
TAB_INVENTARIO = "inventario_propiedades"
TAB_BITACORA = "Bitacora"
TAB_BACKLINKS = "backlinks_seranking"
TAB_COMPETIDORES = "competidores"
TAB_PAGESPEED = "data_pagespeed"
TAB_MOZ = "data"

# Nombre del archivo de credenciales (Service Account)
SERVICE_ACCOUNT_FILE = "service_account.json"

# API Key de Gemini (Obtener en aistudio.google.com)
GEMINI_API_KEY = "os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")"
