# Manual Técnico: Asistenta Xara IA (v1.0)

Este manual documenta la arquitectura, estructura de archivos, detalles de desarrollo y funcionamiento del asistente virtual corporativo **Xara**, diseñado para integrarse con Odoo v17, consultar manuales corporativos y gestionar el calendario de Google Workspace.

---

## 1. Arquitectura General
El sistema se compone de dos partes principales que se comunican a través de HTTP:
1. **Frontend (Extensión de Chrome - Manifest V3)**: Se ejecuta directamente en el navegador del usuario. Detecta la sesión en Odoo, valida el dominio, renderiza la interfaz visual flotante de chat y envía las peticiones al backend.
2. **Backend (FastAPI - Python)**: Se ejecuta localmente o en la nube. Procesa las peticiones, realiza la búsqueda de documentos relevantes (RAG), se conecta con el API de Google (Drive, Sheets y Calendar) y genera respuestas usando modelos de Gemini.

```mermaid
graph TD
    subgraph Cliente (Navegador)
        Odoo[Interfaz de Odoo v17] <--> |DOM & Main World| Injector[session_injector.js]
        Content[content.js] <--> |Message Passing| Injector
        Content <--> |Identity API| Background[background.js]
        Content --> |Renderiza UI| HTML[Burbuja de Chat HTML/CSS]
    end
    subgraph Servidor (Backend)
        API[FastAPI /app.py] <--> |HTTPS /webhook| Content
        RAG[RAG Simple / app.py] <--> Cache[knowledge_cache.json]
        Calendar[Google Calendar API] <--> API
        Gemini[Gemini API] <--> API
    end
    GoogleDrive[Google Drive / Sheets] -.-> |/refresh| Cache
```

---

## 2. Estructura del Código

### A. Archivos del Directorio Raíz (Chrome Extension)
* **[manifest.json](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/manifest.json)**: Define los metadatos de la extensión, permisos (`identity`, `identity.email`), scripts de contenido (`content.js`), service worker de fondo (`background.js`) y los recursos accesibles por páginas externas (`web_accessible_resources`).
* **[content.js](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/content.js)**: Script principal de interfaz. Inyecta la interfaz flotante (FAB y Panel de chat), maneja el cambio de pestañas, carga sugerencias inteligentes y envía solicitudes al endpoint `/webhook` del backend.
* **[session_injector.js](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/session_injector.js)**: Script inyectado en el contexto de página (`MAIN` world) para extraer la información de sesión (`window.odoo.session_info`) y enviarla de vuelta a `content.js` de manera segura, eludiendo restricciones de seguridad (CSP).
* **[background.js](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/background.js)**: Service worker que consulta el correo del perfil de Chrome firmado en el navegador como método de validación de identidad alternativo.
* **[styles.css](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/styles.css)**: Archivo de estilos con estética moderna, animaciones sutiles y diseño responsivo para la interfaz de chat en Odoo.

### B. Directorio `backend/` (Servidor)
* **[app.py](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/backend/app.py)**: Núcleo de la aplicación. Contiene los endpoints `/webhook` y `/refresh`, inicializa el SDK de Gemini, define las herramientas para Google Calendar e implementa el triaje RAG.
* **[agenteia.json](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/backend/agenteia.json)**: Credenciales de la Cuenta de Servicio de Google.
* **[knowledge_cache.json](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/backend/knowledge_cache.json)**: Archivo caché local en disco que almacena el texto extraído de los 99 PDFs de Google Drive y del Sheets de contactos, evitando llamadas repetidas y agilizando el arranque del backend a menos de 1 segundo.
* **[.env](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/backend/.env)**: Contiene la clave del API de Gemini (`GEMINI_API_KEY`).
* **[requirements.txt](file:///c:/Users/Sist-JPinto/Desktop/Agente%20IA/backend/requirements.txt)**: Lista de dependencias del servidor en Python.

---

## 3. Detalles de Desarrollo y Mecanismos de Control

### A. Autenticación y Control de Acceso
* **Validación de Dominio Corporativo**: Tanto el frontend (`content.js`) como el backend (`app.py`) validan que el correo electrónico del usuario termine estrictamente en `@Empresa Demo.com` o `@Enterprise SGC.com`. Si no cumple, el acceso es revocado de forma inmediata.
* **Detección Dinámica de Identidad**: Para evitar que el usuario deba loguearse manualmente, la extensión intenta leer los metadatos de sesión activos en Odoo. Si Odoo aún no ha cargado, realiza una consulta al perfil de Chrome del navegador usando las APIs de identidad. 
* **Personalización**: La IA extrae el primer nombre del usuario a partir del correo o la cuenta y personaliza dinámicamente las respuestas de saludo ("Hola Josmary...").

### B. Conversational RAG (Búsqueda sobre PDFs)
* **Filtro Inteligente de Palabras Clave**: Para procesar consultas sobre 99 manuales corporativos sin agotar la cuota de tokens gratuitos de Gemini (límite de 250k TPM), se implementó una búsqueda de triaje de palabras clave (`buscar_manuales_relevantes`).
* **Combinación de Historial**: El backend une la consulta actual con el mensaje anterior del usuario para conservar el contexto conversacional de la búsqueda RAG (por ejemplo, si el usuario dice *"¿dónde está el manual de caja?"* y luego *"¿y el de arqueo?"*, RAG buscará arqueo y caja).
* **Inyección de URLs**: Xara incluye enlaces en formato HTML (`<a href="..." target="_blank">`) apuntando directamente a los PDFs almacenados en Google Drive cuando se menciona algún manual corporativo.

### C. Gestión de Agenda y Zona Horaria
* **Referencia Temporal Absoluta**: Se inyecta la fecha y hora actual en la zona horaria de Venezuela (`America/Caracas`, UTC-4) de forma dinámica en el System Prompt en cada petición. Esto evita que el modelo use fechas de entrenamiento desactualizadas para interpretar términos como "hoy" o "mañana".
* **Normalización de Fechas**: La herramienta de disponibilidad normaliza las peticiones agregando el offset `-04:00` requerido por la API de Google.
* **Traducción de Timezones en Respuestas**: La API de Google Calendar devuelve la disponibilidad ocupada (`busy_periods`) en formato UTC. El backend las traduce a la zona horaria local de Venezuela antes de entregarlas a Gemini, previniendo distorsiones horarias en el chat.

### D. Flujos de Contingencia (Fallback) para Calendario
Para asegurar el funcionamiento continuo del agendamiento, se programó un sistema de fallbacks automáticos:
1. **Delegación de Dominio (DWD)**: Intenta crear el evento con permisos impersonados (creando el enlace de Google Meet e invitando a participantes en sus agendas).
2. **Falla DWD -> Cuenta de Servicio con Asistentes**: Si DWD no está activo, intenta escribir directamente en el calendario del usuario principal (compartido previamente con permisos de escritura) e invitar a los demás participantes.
3. **Falla Asistentes -> Cuenta de Servicio Simple**: Google restringe la invitación de externos a cuentas de servicio independientes. Si falla, intenta registrar el evento en el calendario compartido del usuario sin asistentes y sin Meet.
4. **Falla Calendario del Usuario -> Calendario de la Cuenta de Servicio**: Si el usuario no ha compartido su calendario, el evento se crea de forma segura dentro del calendario propio de la cuenta de servicio y se le da aviso al usuario.

### E. Restricción estricta de Formato HTML
El widget de chat de Odoo v17 no renderiza marcado Markdown estándar (asteriscos `*`). Por ello, Xara tiene instrucciones de sistema estrictas que prohíben su uso y la obligan a formatear sus respuestas únicamente usando etiquetas HTML válidas: `<strong>`, `<em>`, `<p>`, `<ul>`, `<ol>`, `<li>`.
