import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de Credenciales
# Mapeo de cuentas a archivos de credenciales
CREDENTIALS_MAP = {
    'WAC': 'service_account.json',
    'WAC2': 'conexion-service-account.json', # Asumiendo que esta es la otra cuenta, ajustar según la columna del sheet
    'DEFAULT': 'service_account.json'
}

# Cargar API Keys de Gemini
GEMINI_API_KEYS = []
i = 1
while True:
    key = os.getenv(f'GEMINI_API_KEY_{i}')
    if not key:
        # Fallback for old single key format if exists
        if i == 1 and os.getenv('GEMINI_API_KEY'):
            GEMINI_API_KEYS.append(os.getenv('GEMINI_API_KEY'))
        break
    GEMINI_API_KEYS.append(key)
    i += 1

if not GEMINI_API_KEYS:
    GEMINI_API_KEYS = [None] # Avoid empty list errors

# IDs de Hojas de Cálculo
SHEET_ID_LOOKER_LINKS = '1igmuV15uHc0zmmoXTcjQbymOKjCtz4A8fxIP-0lY5d0'
SHEET_ID_PROPIEDADES = '1z6TiZ7VvQ5zCHJCAOZS_8QuFingwfsw_pI8hsZ-LopI'
SHEET_ID_METRICS = '1q58x292G-oCqdHlMwEyikHrtYY8GuPzjZ8qKIFK_fkw'
TAB_NAME_METRICS = 'metricas_top'

# Nombres de Hojas (Tabs)
TAB_NAME_PROPIEDADES = 'inventario_propiedades'

# Mapeo de Columnas (Indices o Nombres)
COL_CLIENTE = 'Marca'
COL_GA4 = 'propiedad ga4'
COL_GSC = 'propiedad gsc'
COL_CUENTA = 'Cuenta de google'
COL_DOC = 'documento'
COL_URL = 'Url'
COL_ACTIVO = 'Activo'

# Valor de cuenta a filtrar
CUENTA_FILTRO = 'wac'

# Configuración de Fechas
TIMEZONE = 'America/Sao_Paulo'

# Prompt de Gemini (Cargado desde prompt analisis.txt)
GEMINI_PROMPT_TEMPLATE = """
Actúa como un Consultor Senior de SEO y Analista de Datos con más de diez años de experiencia.
Tu especialidad es la interpretación cruzada de datos entre rendimiento técnico (PageSpeed), comportamiento del usuario (Google Analytics 4) y visibilidad en búsqueda (Google Search Console).
Conoces bien a la agencia WeAreContent, que trabaja estrategias de contenido SEO de alto impacto.

Se te proporciona el siguiente JSON e imágenes/PDF con el reporte de looker (POR FAVOR, ANALIZA EL ARCHIVO ADJUNTO QUE EL USUARIO ENVIARÁ JUNTO A ESTE PROMPT) y datos de:

Google Search Console: Rendimiento, Consultas y Páginas.
Google Analytics 4: Adquisición, Engagement y Landing Pages.
Google PageSpeed Insights: métricas de Core Web Vitals (LCP, CLS, INP).

Tu tarea es analizar estos datos y generar un informe ejecutivo y técnico. No te limites a describir los datos: interpreta el por qué de lo que está pasando y qué decisiones se deben tomar.

Debes cruzar la información de las tres fuentes de esta forma:
GSC + GA4: identifica
- páginas con alto tráfico orgánico pero bajo engagement (baja tasa de interacción, bajo tiempo de permanencia, alta tasa de rebote),
- páginas con muchas impresiones pero sin conversiones o con muy pocas conversiones.
GSC + PageSpeed: detecta si las principales páginas (Top 10 por tráfico orgánico) tienen problemas de Core Web Vitals (LCP, CLS, INP) que puedan afectar su posicionamiento.
Oportunidades de contenido: identifica
- keywords en posiciones 4 a 10 (low hanging fruits),
- posibles canibalizaciones entre URLs que compiten por las mismas consultas.

DATOS DEL CLIENTE: {cliente} - {dominio}

DATOS EXTRAÍDOS:
{data_summary}

TOP URLs:
{top_urls_text}

Keywords destacadas:
{top_keywords_text}

Total keywords indexadas: {total_keywords}

El resultado debe estar redactado en español neutro, con tono profesional, directo y crítico cuando sea necesario. Evita cualquier símbolo raro, emojis, hashtags o código. Solo texto plano con saltos de línea, en formato de lista, ordenado, y en un lenguaje que sea comprensible para el cliente, textos breves para mejor comprensión del cliente.

Estructura obligatoria del informe:
Debes respetar exactamente estos encabezados, escritos tal cual, en mayúsculas y seguidos de dos puntos. Después de cada encabezado, deja una línea en blanco y luego desarrolla el contenido en listas simples con guiones, entendibles para el lector cliente.

RESUMEN EJECUTIVO: ASPECTOS POSITIVOS (WINS)

En esta sección:
Incluye entre 3 y 5 puntos fuertes.
Menciona si existe crecimiento en clics o impresiones orgánicas.
Identifica las URLs o clusters de contenido que están generando la mayor parte del tráfico orgánico.
Destaca métricas de comportamiento positivas, como mejoras en engagement rate, tiempo promedio de sesión o profundidad de scroll, cuando aplique.

DIAGNOSTICO: ASPECTOS NEGATIVOS Y RIESGOS (RED FLAGS)

En esta sección:
Señala caídas de tráfico orgánico relevantes o pérdida de posiciones en keywords clave.
Destaca problemas técnicos de Core Web Vitals que afecten especialmente a URLs de negocio o de conversión.
Identifica páginas con alta tasa de rebote o bajo engagement que estén desaprovechando el tráfico orgánico que reciben.
En cada punto, explica brevemente el posible motivo y el impacto en negocio o en visibilidad SEO.

PLAN DE ACCION: LADO DEL CLIENTE (TECNICO, UX Y NEGOCIO)

En esta sección, escribe acciones concretas que deban ejecutar desarrolladores, equipo de UX o responsables de negocio del cliente.
Cada acción debe seguir este formato, en texto plano:

Prioridad: (Alta, Media o Baja)
Accion: (Describe de forma clara y específica lo que se debe hacer).
Justificacion: (Explica brevemente, apoyado en datos, por qué se debe hacer y qué impacto tiene).

PLAN DE ACCION: EQUIPO WEARECONTENT (ESTRATEGIA EDITORIAL)

En esta seccion, define instrucciones claras para el equipo de contenidos y SEO on-page de WeAreContent.
Divide el contenido internamente en los siguientes bloques (usando estos subtitulos en mayusculas dentro de esta misma seccion):

ACTUALIZACION (CONTENT REFRESH):

Lista las URLs que muestren sintomas de content decay, perdida de clics, caida de posiciones o desalineacion con la intencion de busqueda actual.
Indica que tipo de actualización requiere cada URL: ampliacion del contenido, mejora de ejemplos, inclusion de datos recientes, mejor alineacion con queries informacionales, transaccionales, etc.

NUEVOS CLUSTERS:

Propón tres nuevos temas o articulos basados en consultas de oportunidad: keywords con impresiones altas y pocos clics, o temas que la web aún no cubre bien.
Para cada cluster, sugiere un tema principal y 2 o 3 ideas de subtemas o articulos satelite.

OPTIMIZACION ON-PAGE:

Indica que palabras clave secundarias deberian incluirse mejor en titulos, subtitulos o cuerpo del texto de las paginas top.
Señala si faltan variaciones semanticas, FAQ, o mejor uso de H2 y H3 para cubrir la intencion de busqueda detectada en las queries de GSC.

LINK BUILDING INTERNO:

Sugiere oportunidades de enlazado interno desde articulos con buena autoridad o alto trafico hacia:
- contenidos nuevos,
- contenidos de alta conversion,
- contenidos estrategicos que necesiten impulso SEO.
Siempre que sea posible, menciona tipos de paginas origen (ejemplo: guias completas, blogs informativos) y tipos de paginas destino (ejemplo: landing de servicio, categoria de producto, articulo nuevo del cluster).

Indicaciones finales:
No incluyas codigo, tablas complejas ni formatos especiales, solo texto plano con guiones cuando uses listas.
No uses emojis ni simbolos extraños.
Asegurate de que las secciones y subtitulos se vean claramente separados por saltos de linea, para que al pegar el contenido en Word se mantenga la estructura del informe y sea facil de leer.
"""

# Headers esperados
HEADERS_HISTORICO = [
    'Marca', 'Mes', 'Fecha', 'Clicks', 'Δ%', 'Impresiones', 'Δ%', 'CTR', 'Δ%', 'Sesiones Org', 'Δ%', 'Usuarios Nuevos', 'Δ%',
    'URL1', 'Clicks1', 'Imp1', 'Pos1', 'URL2', 'Clicks2', 'Imp2', 'Pos2', 'URL3', 'Clicks3', 'Imp3', 'Pos3',
    'Keywords_Total', 'KW1', 'Pos1', 'KW2', 'Pos2', 'KW3', 'Pos3'
]
