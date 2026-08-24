import os
import json
from report_generator import GeminiClient
import config

def distill_pdf_to_json(pdf_path):
    """
    Usa Gemini únicamente para extraer la DATA CRUDA del PDF (todas las hojas) 
    en un formato JSON que Antigravity pueda analizar sin sesgos de redacción.
    """
    distill_prompt = """
    Analiza este archivo PDF de Looker Studio (que contiene varias páginas, incluyendo rendimiento SEO y SEO Técnico).
    Extrae toda la información numérica y descriptiva clave agrupada por secciones.
    Es vital que extraigas los datos de la sección de 'SEO TÉCNICO' (Core Web Vitals, errores de indexación, 404s, etc.).
    
    Devuelve un JSON con esta estructura:
    {
      "resumen_general": { "clics": 0, "impresiones": 0, "ctr": "0%", "posicion": 0.0 },
      "paginas_top": [ {"url": "", "clics": 0, "impresiones": 0, "ctr": ""} ],
      "technical_seo": {
        "lcp": "", "cls": "", "inp": "",
        "errores_indexacion": "",
        "otros_hallazgos": ""
      },
      "queries_oportunidad": ["kw1", "kw2"],
      "observaciones_looker": ""
    }
    
    NO generes análisis redactado. Solo devuelve el JSON puro.
    """
    
    print(f"DEBUG: Destilando contenido de {pdf_path} a JSON...")
    gemini = GeminiClient(config.GEMINI_API_KEYS)
    # Usamos Gemini para la visión y extracción estructurada
    raw_json_str = gemini.generate_report(distill_prompt, image_path=pdf_path)
    
    try:
        # Limpiar posible formato markdown del JSON si Gemini lo incluye
        clean_json = raw_json_str.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        return data
    except Exception as e:
        print(f"Error al parsear JSON de destilación: {e}")
        return {"raw_text": raw_json_str}

if __name__ == "__main__":
    # Test stub
    pass
