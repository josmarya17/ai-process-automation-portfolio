# Diccionario de Archivos: Xara IA (v1.0)

Este documento detalla la estructura y el propósito de cada uno de los archivos activos en la versión actual del proyecto **Xara IA** (después de realizar la limpieza de scripts y archivos obsoletos de n8n).

---

## 1. Archivos en la Raíz del Proyecto (Extensión de Chrome)

| Archivo | Tipo / Formato | Función / Propósito |
| :--- | :--- | :--- |
| **`manifest.json`** | Configuración JSON | Manifiesto de la extensión en **Manifest V3**. Define permisos (identidad del usuario), scripts de contenido (`content.js`), service worker de fondo (`background.js`), archivos CSS (`styles.css`) y recursos accesibles desde páginas web externas (`web_accessible_resources`). |
| **`content.js`** | JavaScript (Client-side) | Script de contenido principal que se inyecta en Odoo. Crea y gestiona la burbuja flotante del chat (FAB) y el panel lateral. Se comunica con el backend de FastAPI a través de fetch para enviar y recibir mensajes del chat, y maneja el triaje de sugerencias por pestañas. |
| **`session_injector.js`** | JavaScript (Client-side) | Script inyectado en el contexto de ejecución principal (`MAIN` world) de la página web. Lee de forma directa la variable global `window.odoo.session_info` para extraer el nombre y correo del usuario activo y lo transmite de vuelta a la extensión de manera segura, eludiendo bloqueos de CSP. |
| **`background.js`** | JavaScript (Service Worker) | Script en segundo plano de la extensión. Provee soporte alternativo de identidad (Fallback) consultando el correo del perfil logueado en Google Chrome en caso de que Odoo no provea sesión. |
| **`styles.css`** | CSS | Contiene todos los estilos visuales del chat, incluyendo la paleta de colores de Empresa Demo y Farmacias Enterprise SGC, el diseño de la caja de chat, estados activos, avatares y micro-animaciones premium de carga y transición. |
| **`iniciar_xara.bat`** | Script de Windows | Script ejecutable de un solo clic que comprueba la existencia e instala las dependencias de Python y arranca el servidor local de desarrollo (`FastAPI`) de manera automática. |
| **`manual_tecnico_xara.md`** | Documentación Markdown | Manual de arquitectura técnica que detalla el flujo RAG, timezone offsets, contingencias del calendario y consideraciones del formato de respuesta HTML. |
| **`plan_despliegue_produccion.md`** | Documentación Markdown | Guía estratégica paso a paso para el despliegue del backend en AWS (EC2/Load Balancers), seguridad del endpoint, configuración en Google Workspace (DWD) y distribución de la extensión. |
| **`system_prompt.txt`** | Texto de Referencia | Documento de texto con las instrucciones de comportamiento y límites iniciales que sirvió de base para construir el prompt final del agente. |
| **`MANUAL_PROYECTO.md`** | Documentación Markdown | Guía general inicial del proyecto que describe los objetivos del negocio y el triaje operativo. |
| **`Logo_Enterprise SGC.jpg`** | Imagen (Asset) | Logotipo de Farmacias Enterprise SGC utilizado como avatar del asistente en la cabecera del chat de Odoo. |
| **`icono_chat.png`** | Imagen (Asset) | Icono de chat flotante que se muestra en el botón de activación (FAB) en la esquina inferior derecha de Odoo. |
| **`call-center-customer-support-vector-600nw-2285364015.webp`** | Imagen (Asset) | Recurso gráfico de soporte al cliente utilizado en la UI. |

---

## 2. Archivos en la Carpeta `backend/` (Servidor de IA)

| Archivo | Tipo / Formato | Función / Propósito |
| :--- | :--- | :--- |
| **`backend/app.py`** | Python | Núcleo del servidor desarrollado en **FastAPI**. Contiene los endpoints `/webhook` para el chat y `/refresh` para actualizar conocimientos. Gestiona la lógica de búsqueda RAG conversacional, el cálculo dinámico de zona horaria local, el fallback de modelos de Gemini y registra las herramientas para interactuar con Google Calendar. |
| **`backend/agenteia.json`** | Credenciales JSON | Clave privada de la Cuenta de Servicio de Google. Permite al backend interactuar directamente con Google Drive (para leer PDFs), Google Sheets (para el directorio de contactos) y Google Calendar (para disponibilidad y eventos). |
| **`backend/knowledge_cache.json`** | Almacén JSON | Base de datos local en disco que almacena el texto ya extraído de los 99 manuales de Google Drive y el directorio de contactos. Evita tener que descargar y procesar los PDFs en cada reinicio del servidor, bajando el tiempo de boot de 3 minutos a menos de 1 segundo. |
| **`backend/requirements.txt`** | Dependencias Python | Listado de librerías de Python requeridas para ejecutar el backend (FastAPI, Uvicorn, SDK de Gemini, pypdf, pandas, google-api-python-client, etc.). |
| **`backend/.env`** | Variables de Entorno | Archivo de configuración confidencial que almacena la variable de entorno `GEMINI_API_KEY`. |
