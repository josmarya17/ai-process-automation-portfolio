# 📋 Instructivo de Proceso: Análisis SEO Mensual con Antigravity

Este documento detalla el procedimiento paso a paso que debe seguir el asistente de IA para realizar el análisis SEO mensual, interpretación de Looker Studio y publicación del reporte en Google Docs para cualquier cliente activo de WeAreContent.

---

## 🔍 Paso 1: Localización del Cliente y Metadatos

Antes de iniciar, se deben buscar los datos de conexión del cliente en la hoja de cálculo del inventario de propiedades:
* **ID del Inventario**: `1z6TiZ7VvQ5zCHJCAOZS_8QuFingwfsw_pI8hsZ-LopI`
* **Tab / Hoja**: `inventario_propiedades`

Se debe extraer la siguiente información:
1. **Marca**: Nombre exacto del cliente (ej. `109app`, `FANOSA`, `DIABETRICs`).
2. **Propiedad GSC**: URL de la propiedad en Google Search Console.
3. **Propiedad GA4**: ID de la propiedad de Google Analytics 4.
4. **Documento**: Enlace al Google Doc del cliente donde se publicará el reporte.
5. **Cuenta de Google**: La cuenta asignada para la autenticación (`wac` o `wac2`).

---

## 📦 Paso 2: Extracción Automática de Métricas y Looker PDF

Para recopilar los datos numéricos y descargar el reporte de Looker Studio en formato PDF, ejecuta el siguiente comando en la terminal desde la raíz del proyecto:

```bash
python main.py --mode context --client "<Marca_del_Cliente>"
```

* **Resultado**:
  * Se mostrará un resumen de clics, impresiones, sesiones, engagement y conversiones en la terminal.
  * Se descargará el PDF del reporte en la raíz del proyecto como `looker_report_<Marca_del_Cliente>.pdf`.

---

## 📄 Paso 3: Extracción de Texto del PDF

Dado que el reporte de Looker Studio contiene información visual detallada sobre linkbuilding, salud técnica y rankings, se debe extraer el texto del PDF utilizando `pdfplumber`.

1. Crea un script temporal de inspección (ej. `scratch/inspect_pdf_temp.py`) con el siguiente contenido:

```python
import pdfplumber

def inspect_pdf(pdf_path, output_path):
    with pdfplumber.open(pdf_path) as pdf:
        with open(output_path, "w", encoding="utf-8") as f:
            for i, page in enumerate(pdf.pages):
                f.write(f"\n--- Page {i+1} ---\n")
                text = page.extract_text()
                if text:
                    f.write(text)
                else:
                    f.write("[No text extracted]")
                f.write("\n")

if __name__ == "__main__":
    inspect_pdf("looker_report_<Marca_del_Cliente>.pdf", "scratch/pdf_text_temp.txt")
```

2. Ejecútalo y lee el archivo generado (`scratch/pdf_text_temp.txt`) para cruzar y analizar todos los datos.

---

## ✍️ Paso 4: Redacción del Reporte SEO

El análisis y la redacción del reporte se basan en las pautas y la estructura del archivo [prompt analisis.txt](file:///c:/Users/Sist-JPinto/Documents/WAC_IMPLEMENTACIONES/Proyecto_data_analisis_antigravity/prompt%20analisis.txt). Redacta el informe analítico siguiendo estrictamente estas directrices:
* **Rol**: Consultor Senior SEO y Analista de Datos.
* **Idioma**: Español neutro.
* **Tono**: Profesional, directo y crítico.
* **Formato**: Listas simples con guiones, sin emojis, sin hashtags y sin código HTML.
* **Encabezados**: Respetar exactamente los encabezados en mayúsculas seguidos de dos puntos, con un salto de línea antes de la lista.

### Estructura Obligatoria:

```text
RESUMEN EJECUTIVO: ASPECTOS POSITIVOS (WINS):

- [Punto fuerte 1 con datos concretos (crecimiento, CTR, clics)]
- [Punto fuerte 2 (URL principal o cluster de mejor rendimiento)]
- [Punto fuerte 3 (métricas de comportamiento o comportamiento en IA)]

DIAGNOSTICO: ASPECTOS NEGATIVOS Y RIESGOS (RED FLAGS):

- [Caídas de tráfico orgánico relevantes o pérdida de posiciones]
- [Problemas técnicos de velocidad o Core Web Vitals (especialmente móvil)]
- [Páginas huérfanas, errores 404 críticos o problemas de indexación en GSC]
- [Brecha de autoridad frente a competidores directos]

PLAN DE ACCION: LADO DEL CLIENTE (TECNICO, UX Y NEGOCIO):

Prioridad: [Alta/Media/Baja]
Accion: [Descripción clara y específica de la tarea]
Justificacion: [Por qué se debe hacer y qué impacto tiene en base a los datos]

PLAN DE ACCION: EQUIPO WEARECONTENT (ESTRATEGIA EDITORIAL):

ACTUALIZACION (CONTENT REFRESH):
- URL: [Enlace completo]
  Tipo de actualización: [Ampliación, intención de búsqueda, FAQ, etc.]

NUEVOS CLUSTERS:
- Tema principal: [Tema]
  - Subtema 1: [Idea de artículo]
  - Subtema 2: [Idea de artículo]

OPTIMIZACION ON-PAGE:
- [Integración de palabras clave secundarias, FAQs, microdatos o estructura H2/H3]

LINK BUILDING INTERNO:
- [Oportunidades de enlazado desde páginas con alto tráfico hacia páginas de conversión o nuevas]
```

---

## 🚀 Paso 5: Publicación en Google Docs

Para subir el reporte directamente al Google Doc del cliente, crea y ejecuta un script de publicación temporal (ej. `scratch/publish_temp.py`):

```python
import sys
sys.path.append('.')
from direct_publisher import publish_to_doc

doc_url = "<URL_del_Documento_del_Cliente>"
report_text = """[Texto Completo del Reporte Redactado]"""
month_name = "Mayo 2026"  # O el mes de análisis correspondiente
account_key = "<Cuenta_de_Google>"  # wac o wac2

success = publish_to_doc(doc_url, report_text, month_name, account_key=account_key)
if success:
    print("PUBLISH_SUCCESS")
else:
    print("PUBLISH_FAILED")
```

---

## 🧹 Paso 6: Limpieza Final de Archivos

Al terminar la publicación exitosa, elimina todos los archivos temporales creados para evitar contaminar el entorno de trabajo:
* `looker_report_<Marca_del_Cliente>.pdf`
* `looker_report_<Marca_del_Cliente>_modal.png` (si se generó)
* `scratch/inspect_pdf_temp.py`
* `scratch/pdf_text_temp.txt`
* `scratch/publish_temp.py`
* Cualquier script de búsqueda creado en `scratch/`

---
*Nota: Este instructivo debe ser seguido por la IA al recibir la instrucción simple: "Sigue las instrucciones del archivo INSTRUCTIVO_ANALISIS_SEO.md para el cliente [Nombre_Cliente]".*
