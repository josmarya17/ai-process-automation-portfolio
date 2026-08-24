# Xara IA: Asistente de IA Flotante para Odoo v17 (v1.0)

Este repositorio contiene la arquitectura completa de **Xara IA**, un copilot o asistente virtual corporativo diseñado para integrarse como una burbuja de chat flotante sobre la interfaz de **Odoo v17**. Asiste al personal en dudas funcionales, consulta manuales internos (RAG), busca contactos y gestiona reuniones de Google Calendar.

> [!IMPORTANT]
> **Esta versión omite por completo el uso de n8n.** La comunicación es directa entre la extensión de Chrome (Frontend) y un servidor local en FastAPI (Backend) que consume directamente los servicios de Google Gemini y las APIs de Google Workspace.

---

## 1. Arquitectura General y Flujo de Datos

El sistema está dividido en dos grandes componentes comunicados a través de HTTP:

```mermaid
graph TD
    subgraph Cliente (Navegador Chrome - Odoo)
        Odoo[Interfaz de Odoo v17] <--> |DOM & MAIN World| Injector[session_injector.js]
        Content[content.js] <--> |Message Passing| Injector
        Content <--> |Identity API| Background[background.js]
        Content --> |Renderiza UI| UI[Burbuja de Chat HTML/CSS]
    end
    
    subgraph Servidor (Backend FastAPI)
        API[FastAPI /app.py] <--> |HTTPS POST /webhook| Content
        RAG[Triaje RAG / app.py] <--> Cache[knowledge_cache.json]
        Gemini[Google Gemini API] <--> API
        Calendar[Google Calendar API] <--> API
    end
    
    GoogleDrive[Google Drive / Sheets] -.-> |POST /refresh| Cache
```

1. **Frontend (Extensión de Chrome - Manifest V3)**:
   - `session_injector.js` se inyecta en el contexto principal de la página (`MAIN` world) para esquivar restricciones de seguridad (CSP) y leer la variable global `window.odoo.session_info`.
   - Si Odoo aún no ha cargado o falla, `background.js` actúa como respaldo consultando el correo del perfil firmado en Google Chrome.
   - `content.js` dibuja la interfaz de chat (burbuja flotante y panel lateral) y envía la consulta al backend.
2. **Backend (FastAPI - Python)**:
   - `/refresh`: Descarga recursiva de PDFs de Google Drive y del Sheets de contactos, extrayendo texto y guardándolo en un caché local (`knowledge_cache.json`) para inicializaciones ultrarrápidas (<1s).
   - `/webhook`: Recibe la pregunta del usuario, valida que pertenezca al dominio corporativo, ejecuta un motor de RAG simple por palabras clave, inyecta el contexto horario de Venezuela (`America/Caracas`, UTC-4), invoca herramientas (Tools) del calendario y devuelve la respuesta al frontend formateada estrictamente en HTML.

---

## 2. Estructura del Proyecto

El directorio se organiza de la siguiente manera:

```text
Agente IA/
├── manifest.json         # Configuración de la extensión de Chrome (Manifest V3)
├── content.js            # Lógica de interfaz en Odoo y peticiones al backend
├── styles.css            # Estilos aislados y animaciones premium de la UI
├── session_injector.js   # Extractor seguro de credenciales de sesión en Odoo
├── background.js         # Service Worker para lectura del perfil de Chrome
├── iniciar_xara.bat      # Script automatizado para arrancar backend en Windows
├── manual_tecnico_xara.md# Manual de funcionamiento interno y fallbacks
├── plan_despliegue_produccion.md # Guía para el despliegue cloud en producción
├── diccionario_archivos.md# Diccionario detallado de cada archivo del proyecto
├── Logo_Enterprise SGC.jpg         # Asset: Logotipo en cabecera del chat
├── icono_chat.png        # Asset: Icono del botón flotante
├── backend/
│   ├── app.py            # Servidor FastAPI y lógica de IA (Gemini + RAG + APIs)
│   ├── requirements.txt  # Librerías de Python requeridas
│   ├── agenteia.json     # Credenciales de la Cuenta de Servicio de Google (Ignorar en Git)
│   ├── knowledge_cache.json # Caché local del RAG (Autogenerado / Refresh)
│   └── .env              # Clave privada GEMINI_API_KEY (Confidencial)
```

---

## 3. Instalación y Configuración Paso a Paso

Sigue estos pasos para desplegar el proyecto localmente en otra computadora:

### Requisitos Previos
- **Python 3.10** o superior instalado y agregado al PATH.
- Navegador **Google Chrome**.

### Paso 1: Configurar Variables de Entorno del Backend
1. Entra a la carpeta `backend/`.
2. Crea o edita el archivo `.env` y añade tu clave de API de Gemini:
   ```env
   GEMINI_API_KEY=Tu_Clave_Aqui
   ```
3. Coloca el archivo JSON de credenciales de Google Cloud (`agenteia.json`) dentro del directorio `backend/`. Este archivo debe corresponder a una Cuenta de Servicio con acceso a las APIs de Drive, Sheets y Calendar.

### Paso 2: Iniciar el Servidor Backend
1. En la raíz del proyecto, haz doble clic en el archivo [iniciar_xara.bat](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/iniciar_xara.bat).
2. El script de procesamiento:
   - Instalará automáticamente todas las dependencias listadas en `requirements.txt`.
   - Inicializará el servidor local de desarrollo en `http://localhost:8000`.
   - Si es el primer arranque, descargará la base de conocimientos desde Google Drive y Sheets creando el archivo `knowledge_cache.json`.
3. Mantén abierta esta ventana para ver los logs en tiempo real.

### Paso 3: Cargar la Extensión de Chrome
1. Abre Google Chrome y navega a `chrome://extensions/`.
2. Habilita el **"Modo de desarrollador"** (Developer mode) en la esquina superior derecha.
3. Haz clic en **"Cargar descomprimida"** (Load unpacked) arriba a la izquierda.
4. Selecciona la carpeta raíz del proyecto (`c:\Users\Sist-JPinto\Desktop\Agente IA`).
5. La extensión "Odoo Copilot - Pharmacy AI" ya estará activa.

---

## 4. Mecanismos Críticos del Proyecto

Para la correcta mantención del sistema, es vital comprender las siguientes mecánicas internas:

### A. RAG Conversacional Optimizado
- Para evitar re-procesar los 99 PDFs de manuales en cada pregunta (lo que agotaría cuotas de tokens y crearía latencias de minutos), la base de conocimientos se lee del archivo local `knowledge_cache.json`.
- Al recibir una pregunta, el backend combina la consulta actual con el último mensaje del historial del usuario (para no perder contexto como: *"¿dónde está el manual de caja?"* y luego *"¿y el de arqueo?"*).
- Se ejecuta un triaje ágil por palabras clave en Python (`buscar_manuales_relevantes`) que selecciona los **3 manuales más puntuados** y los inyecta dinámicamente en el System Prompt.

### B. Herramientas de Calendar y Envío de Invitaciones (Cruencial)
El backend tiene registradas dos herramientas que Gemini puede invocar dinámicamente:
1. `verificar_disponibilidad`: Consulta disponibilidad de tiempo y la traduce de UTC a la hora de Caracas (UTC-4).
2. `crear_evento_calendario`: Registra reuniones y genera enlaces de Meet. 
   - **Parámetro `sendUpdates="all"`**: Se incluye obligatoriamente en las llamadas de inserción del API. Sin esto, Google Calendar creará el evento pero no enviará el correo de invitación ni agregará el evento a la agenda de los invitados.
   - **Delegación de Dominio (DWD)**: Por restricciones anti-spam de Google, **las cuentas de servicio no pueden invitar personas externas ni agregar asistentes a reuniones a menos que tengan habilitada la delegación de dominio** configurada en la consola de Google Workspace Admin (`admin.google.com`). 
   - En caso de fallar la delegación, la API aplica un sistema secuencial de fallbacks: intenta escribir en el calendario compartido del usuario invitando a los participantes $\rightarrow$ luego escribe sin invitados $\rightarrow$ finalmente escribe solo en la agenda propia de la cuenta de servicio.

### C. Guardrails de Seguridad y Formato HTML
- **Validación estricta de Dominio**: El sistema rechaza cualquier solicitud proveniente de un correo que no pertenezca a los dominios `@Empresa Demo.com` o `@Enterprise SGC.com`.
- **Prohibición Absoluta de Markdown**: El chat flotante en Odoo v17 no renderiza marcado Markdown (asteriscos `*`, guiones `-`). Por ende, el System Prompt de Gemini prohíbe taxativamente su uso y obliga a formatear las respuestas únicamente con etiquetas HTML válidas: `<strong>`, `<em>`, `<ul>`, `<ol>`, `<li>`, `<p>`, y `<a href="..." target="_blank">`.

---

## 5. Guía de Pruebas Locales (Bypass Temporal)

Si estás probando la extensión en un entorno de desarrollo sin estar logueado en Odoo con una cuenta corporativa `@Empresa Demo.com` o `@Enterprise SGC.com`:

1. **Permitir pruebas en otras páginas**: Modifica la propiedad `"matches"` en [manifest.json](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/manifest.json) para incluir un dominio común de pruebas (ej: `"https://*.google.com/*"`).
2. **Forzar credenciales simuladas**: En [content.js](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/content.js) (alrededor de la línea 107), fuerza el inicio de sesión del frontend inyectando un correo de pruebas:
   ```javascript
   setTimeout(() => {
     if (!chatInitialized) {
       console.log("Xara Test: Forzando usuario local...");
       tryInitialize("usuario.prueba@Empresa Demo.com", "Usuario Prueba");
     }
   }, 1500);
   ```
3. **Compartir calendario**: Para probar la agenda, copia el `client_email` de tu `agenteia.json` y compártele permisos de escritura ("Hacer cambios en eventos") en el Google Calendar personal que ques para las pruebas.

---

## 6. Instrucciones Especiales para Agentes de IA (Guía Antigravity)

Si eres un agente de desarrollo de IA (como **Antigravity**) trabajando en este repositorio, ten en cuenta las siguientes reglas operativas estrictas:

1. **No rompas la compatibilidad HTML**: Al modificar las respuestas predefinidas del backend o retocar el System Prompt de Gemini, nunca introduzcas asteriscos (`**`) o guiones de Markdown. Asegúrate de que el modelo devuelva exclusivamente etiquetas `<strong>`, `<ul>`, etc.
2. **Usa `sendUpdates="all"` en inserciones de Google Calendar**: Cualquier modificación en la API de eventos que involucre invitaciones a terceros debe llevar este parámetro, de lo contrario la API omitirá las notificaciones.
3. **No borres `knowledge_cache.json` de forma innecesaria**: Es la base de RAG en disco. Si necesitas limpiarla o reconstruirla, invoca directamente al endpoint `/refresh` enviando un POST desde herramientas HTTP de pruebas.
4. **CORS en Producción vs Local**: Actualmente, el servidor FastAPI tiene habilitado `allow_origins=["*"]` para pruebas locales fáciles. En un despliegue de producción real, este valor debe acotarse estrictamente al dominio de Odoo de la empresa.
5. **Comportamiento del Fallback del Calendario**: El backend está programado para ser resiliente. Si una petición de calendario da error de permisos, no debes lanzar un `HTTPException` inmediato; debes capturar la excepción y tratar de guardar el evento utilizando los flujos alternativos (sin Meet, sin asistentes, o en el calendario de la Cuenta de Servicio).
