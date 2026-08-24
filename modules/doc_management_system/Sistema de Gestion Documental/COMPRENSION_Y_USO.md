# Guía de Comprensión, Uso y Configuración del Proyecto
## (Para Despliegue en Nuevas PCs y Pair Programming con Antigravity)

Este documento sirve como manual interactivo y técnico para comprender la estructura de este proyecto, cómo configurarlo y ejecutarlo en cualquier otra computadora desde cero, y cómo apoyarse en **Antigravity** (tu asistente de IA) para modificarlo en el futuro.

---

## 1. ¿Qué es este Proyecto y Qué Hace?

Este proyecto, denominado **Enterprise SGC BPM Automator**, es una suite de automatización dividida en dos pilares principales:

1.  **Generación de Documentación y Flujos BPM (Streamlit Web App):**
    *   Toma apuntes, diagramas de Draw.io o minutas de reuniones y utiliza la IA de Gemini para redactar de forma automática manuales de procedimientos y normas de calidad oficiales.
    *   Genera entregables en Word (`.docx`) basados en plantillas institucionales de Farmacia Enterprise SGC y diagramas editables `.drawio`.
    *   Registra y sincroniza de forma automática cada documento en una matriz centralizada de Google Sheets y los sube a carpetas organizadas en Google Drive.
2.  **Generador Visual de Organigramas (Enterprise SGC y Empresa Demo):**
    *   Lee la base de datos de personal y responsabilidades directamente desde un archivo de Excel (`Matriz_RACI_y_Directorio_Equipo Copia LD.xlsx`).
    *   Genera dos tipos de salidas:
        *   **Versión Interactiva (Navegador):** Un sitio web interactivo HTML5 con animaciones, zoom y buscador de personal en tiempo real.
        *   **Versión Figma (Aplanada):** Un archivo HTML estructurado con la metodología limpia de Figma que conserva el árbol visual de auto-layout y los vectores SVG de las líneas de conexión perfectamente centrados para que los diseñadores lo importen sin descuadres.

---

## 2. Mapa Detallado de la Carpeta del Proyecto

A continuación se detalla la función de cada archivo y subcarpeta clave dentro del proyecto:

```
[Raíz del Proyecto]
├── .env                       # Configuración de variables de entorno (API keys de Gemini, IDs de Google Sheets/Drive).
├── requirements.txt           # Lista de dependencias de Python necesarias.
├── iniciar_sistema.bat        # Archivo ejecutable por lotes (doble clic) para encender el servidor Streamlit local.
├── registrar_token.bat        # Archivo ejecutable por lotes para iniciar el enlace OAuth de Google.
├── register_token.py          # Script de Python que genera el "token.json" para interactuar con Google API.
├── app.py                     # Archivo principal de la aplicación web Streamlit (Interfaz de usuario).
├── credentials.json           # Credenciales OAuth obtenidas de Google Cloud Console.
├── token.json                 # Token de sesión autenticado generado dinámicamente con Google.
├── MANUAL.md                  # Manual técnico profundo y guía de despliegue en la nube (producción).
├── Matriz_RACI_y_Directorio_Equipo Copia LD.xlsx   # Base de datos en Excel que nutre a los organigramas.
│
├── organigrama/               # GENERADOR DEL ORGANIGRAMA Empresa Demo
│   ├── generate_organigrama.py # Script principal que procesa el Excel y genera el HTML del organigrama.
│   ├── dump_figma.py           # Script optimizado que simula el DOM en un navegador para exportar a Figma.
│   ├── styles.css              # Estilos CSS específicos (colores por niveles y comportamiento interactivo).
│   ├── organigrama_Empresa Demo.html       # HTML final interactivo generado para Empresa Demo.
│   └── organigrama_figma_Empresa Demo.html # HTML aplanado final listo para importar a Figma para Empresa Demo.
│
├── salidas/                   # GENERADOR DEL ORGANIGRAMA Enterprise SGC
│   ├── organigrama.html        # HTML interactivo generado para Enterprise SGC.
│   ├── organigrama_figma.html  # HTML aplanado final listo para importar a Figma para Enterprise SGC.
│   ├── styles.css              # Estilos CSS específicos para el organigrama de Enterprise SGC.
│   └── *.pdf                   # Respaldos de organigramas exportados a formato PDF.
│
├── src/                       # MÓDULOS DE CÓDIGO FUENTE (BACKEND)
│   ├── ai_engine.py            # Orquestador de la IA de Gemini para la redacción de procesos.
│   ├── docx_generator.py       # Generador de documentos Word utilizando plantillas y docxtpl.
│   ├── drawio_generator.py     # Generador de diagramas de Draw.io en formato XML.
│   ├── google_client.py        # Conector a las APIs de Google Drive y Sheets.
│   └── inventory_manager.py    # Control del inventario de nomenclatura documental en Sheets.
│
└── templates/                 # PLANTILLAS DE DOCUMENTOS DE WORD (.docx)
```

---

## 3. Guía de Configuración en una Nueva Computadora

Para ejecutar este sistema en otra PC, sigue estos pasos secuenciales:

### Paso 1: Instalar Python
Asegúrate de descargar e instalar **Python 3.10 o superior** desde el sitio web oficial de Python. Durante la instalación, marca la casilla **"Add Python to PATH"** (imprescindible).

### Paso 2: Instalar las Dependencias de Python
1. Abre una terminal (CMD o PowerShell) en la carpeta del proyecto.
2. Ejecuta el comando para instalar todas las dependencias necesarias:
   ```bash
   pip install -r requirements.txt
   ```

### Paso 3: Configurar las Credenciales de Google API
El sistema requiere acceso a Google Drive y Sheets. En la nueva PC:
1. Coloca tu archivo `credentials.json` (obtenido de tu Google Cloud Console) en la raíz del proyecto.
2. Ejecuta haciendo doble clic en el archivo: registrar_token.bat.
3. Se abrirá una pestaña en tu navegador web pidiendo autorización. Inicia sesión con la cuenta de Google correspondiente y otorga los permisos necesarios.
4. Esto creará automáticamente un archivo token.json en la raíz, que mantendrá activa la conexión de la API sin tener que iniciar sesión de nuevo.

### Paso 4: Crear el Archivo de Configuración de Entorno (`.env`)
Crea un archivo llamado `.env` en la raíz del proyecto con la siguiente estructura de variables:
```ini
GEMINI_API_KEY=tu_api_key_de_gemini
SPREADSHEET_ID=el_id_de_tu_hoja_de_google_sheets
DRIVE_FOLDER_ID=el_id_de_la_carpeta_de_google_drive
```

### Paso 5: Iniciar el Sistema
Para encender el sistema, simplemente haz doble clic en iniciar_sistema.bat.
*   Se abrirá una ventana de comando negra que iniciará el servidor Streamlit en el puerto local **8510**.
*   El navegador abrirá automáticamente el panel del sistema en: **`http://localhost:8510`**.

---

## 4. Guía para Pair Programming con Antigravity

**Antigravity** es tu copiloto de desarrollo y mantenimiento. Cuando lleves este proyecto a otra PC y necesites realizar cambios, puedes interactuar con él directamente.

### ¿Qué tareas puede realizar Antigravity de forma autónoma?

*   **Actualizar Datos o Colores de Tarjetas:** Si deseas cambiar la paleta de colores de algún nivel jerárquico o agregar una regla especial para un usuario, pídeselo directamente a Antigravity. Él modificará los archivos `styles.css` u `organigrama_figma.html` al instante.
*   **Regenerar los Archivos de Figma:** Si realizas cambios en el archivo de Excel y quieres que las versiones HTML se actualicen y se aplanen con las coordenadas perfectas para Figma, pídele:
    > *"Antigravity, corre el generador de organigrama y exporta la versión aplanada para Figma de Empresa Demo (o Enterprise SGC)"*.
    Él ejecutará de fondo los scripts `generate_organigrama.py` y `dump_figma.py` usando Google Chrome Headless para dejarte los entregables listos para descargar.
*   **Resolver Problemas de Puertos Bloqueados:** Si te aparece un error indicando que el puerto está ocupado (como el error `Port 8510 is not available`), pídele ayuda y él identificará cuál es la aplicación que lo está bloqueando.

### Comandos de Ejecución de Organigramas (Para referencia técnica):
Si deseas correr los scripts generadores a mano desde la terminal en cualquier PC:
*   **Para generar la base interactiva de Empresa Demo:**
    ```bash
    python "organigrama/generate_organigrama.py"
    ```
*   **Para aplanar y exportar el organigrama para Figma (Metodología de alineación de coordenadas):**
    ```bash
    python "organigrama/dump_figma.py"
    ```
    *(Este comando levantará un servidor temporal, inyectará los estilos absolutos limpios sin dañar las etiquetas de auto-layout y guardará el archivo listo para Figma).*
