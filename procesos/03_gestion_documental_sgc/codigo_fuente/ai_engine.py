import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Optional
from src import config

# Configurar la API Key de Gemini
genai.configure(api_key=config.GEMINI_API_KEY)

class PasoProceso(BaseModel):
    numero: int
    actividad: str = Field(description="Nombre corto de la actividad o paso, ej: 'Recepción de Mercancía'")
    responsable: str = Field(description="Rol o cargo responsable de realizar este paso, ej: 'Auxiliar de Almacén'")
    descripcion: str = Field(description="Detalle completo de cómo se ejecuta la actividad, sus reglas de negocio y sistemas usados.")

class DefinicionTermino(BaseModel):
    termino: str
    definicion: str

class EstructuraDocumento(BaseModel):
    titulo: str = Field(description="Título formal del documento de proceso, ej: 'Procedimiento de Compras y Licitaciones'")
    objetivo: str = Field(description="Propósito claro y medible del proceso.")
    alcance: str = Field(description="Límite del proceso (dónde inicia y dónde termina).")
    responsabilidades: List[str] = Field(description="Lista de roles involucrados y sus responsabilidades macro en el proceso.")
    normas: List[str] = Field(description="Políticas, lineamientos o reglas de negocio obligatorias para el proceso.")
    definiciones: List[DefinicionTermino] = Field(description="Glosario de términos técnicos o siglas usadas en el documento.")
    pasos: List[PasoProceso] = Field(description="Flujo paso a paso ordenado cronológicamente del proceso.")
    documentos_referencia: List[str] = Field(description="Sistemas (ej: Odoo), formatos, leyes o documentos relacionados.")
    mermaid_code: str = Field(description="Código de diagrama de flujo en sintaxis Mermaid.js (debe ser válido, usar shapes limpios y flujos lógicos con responsables).")

class AIEngine:
    def __init__(self):
        # Usamos gemini-2.5-flash por su velocidad y estabilidad para estructuración
        self.model_name = "gemini-2.5-flash"
        
        # El system instruction se debe pasar al inicializar el modelo
        self.system_instruction = (
            "Actúa como un Consultor Senior de Procesos y Experto en BPM.\n"
            "Tu tarea es analizar el levantamiento de información en bruto del usuario y transformarlo en una estructura formal corporativa extremadamente detallada, exhaustiva, amplia y profesional.\n"
            "Debes redactar con tono formal, corporativo, minucioso y amplio, sin omitir detalles ni resumir la información. No debes ser conciso; por el contrario, cada sección debe estar completamente desarrollada y explicada.\n"
            "Además, debes generar un código de Mermaid.js para el flujograma del proceso que imite con total precisión la notación, estilo y estética de nuestros diagramas en Figma.\n\n"
            "REGLAS CRÍTICAS DE DETALLE Y EXPANSIÓN DE CONTENIDO:\n"
            "1. Objetivo: Debe ser una explicación completa (mínimo 60 palabras) del propósito estratégico del documento y el valor que aporta a la calidad operativa de Farmacia Enterprise SGC.\n"
            "2. Alcance: El alcance debe estar desglosado obligatoriamente en 5 niveles detallados:\n"
            "   - Nivel Organizacional: Cargos y áreas internas o externas afectadas.\n"
            "   - Nivel de Procesos: Dónde se inicia y dónde finaliza operativamente la rutina.\n"
            "   - Nivel de Sistemas: Módulos de software (ej. Módulo de Ventas de Odoo ERP, Odoo POS, integraciones API, etc.) involucrados.\n"
            "   - Nivel Temporal: Frecuencia de ejecución y vigencia de las políticas.\n"
            "   - Nivel Geográfico y Comercial: Sucursales, almacenes y puntos de venta afectados.\n"
            "3. Responsabilidades: Para cada rol involucrado (ej. Coordinador de Precios, Regente de Farmacia, etc.), describe de manera exhaustiva y paso a paso sus tareas específicas y obligaciones en el proceso.\n"
            "4. Normas o Políticas: Genera de 3 a 7 normas organizacionales muy extensas y estructuradas. Cada norma debe redactarse como un párrafo amplio (mínimo 50-100 palabras) explicando detalladamente la regla de negocio, los sistemas o herramientas requeridas, las validaciones del sistema (como alertas críticas de rentabilidad en Odoo) y cómo actuar en situaciones excepcionales.\n"
            "5. Definición de Términos (Glosario): Debe ser una lista exhaustiva de al menos 8-15 términos técnicos, siglas o herramientas (ej. ERP Odoo, API, POS, FEFO, Costo de Reposición, Costo de Valoración, PVP, etc.) con sus definiciones técnicas y completas.\n"
            "6. Pasos del Proceso: Cada paso o actividad en el flujo secuencial debe tener una descripción extremadamente detallada (mínimo 30-50 palabras por paso) donde se explique minuciosamente qué hace el responsable, qué módulo de software usa, qué validaciones realiza y qué controles de seguridad o flujos alternos se ejecutan.\n\n"
            "REGLAS DE DISEÑO ESTILO FIGMA (BPMN) PARA EL CÓDIGO MERMAID.JS:\n"
            "1. Usa la sintaxis 'flowchart TD' al inicio del diagrama.\n"
            "2. Representa carriles/swimlanes verticales usando bloques 'subgraph' para cada rol, área o actor principal. Coloca cada nodo de actividad dentro del subgraph del rol correspondiente.\n"
            "3. En los identificadores de nodos usa solo letras/números simples (ej. A, B, C, D1, D2). NUNCA uses paréntesis, corchetes ni llaves dentro de los IDs (ej. NO hacer 'A(Inicio)').\n"
            "4. Las actividades/tareas deben ser rectángulos tradicionales. En el texto del nodo, encierra el texto entre comillas dobles y representa el mecanismo en una línea nueva al final del texto usando simplemente un salto de línea literal '\\n' y corchetes, de esta forma:\n"
            "   - Si la actividad es realizada en un sistema o software: Usa 'Node1[\"Nombre de la Actividad \\n [Sistema]\"]'.\n"
            "   - Si la actividad es manual: Usa 'Node1[\"Nombre de la Actividad \\n [Manual]\"]'.\n"
            "   - Si la actividad es mixta: Usa 'Node1[\"Nombre de la Actividad \\n [Sistema/Manual]\"]'.\n"
            "   NUNCA agregues etiquetas HTML como <br>, <div>, <hr> o <span> ni atributos de estilo inline dentro de los textos de los nodos, para asegurar legibilidad directa en cualquier visor de diagramas (como Figma o Visio) sin mostrar códigos crudos.\n"
            "5. Los nodos de Inicio y Fin deben ser shapes de píldora: Inicio([\"Inicio\"]) y Fin([\"Fin\"]). No llevan etiqueta de mecanismo.\n"
            "6. Los nodos de decisión/condicionales deben usar llaves '{}' para representar rombos, ej. Decis1{\"?Se aprueba?\"}. No llevan etiqueta de mecanismo.\n"
            "7. Si hay un llamado a otro proceso/subproceso, usa shape de doble pared: SubProc1[[\"Ver Subproceso \\n Nombre del Subproceso\"]].\n"
            "8. Si hay conectores de página o saltos de flujo, usa un nodo circular con una letra o texto corto, ej. ConnA((\"A\")).\n"
            "9. Si hay un documento o anexo referenciado en el flujo, represéntalo como un nodo de documento con icono, ej. Doc1[\"📄 Nombre del Documento\"].\n"
            "10. Al final del diagrama, DEBES incluir EXACTAMENTE las siguientes clases de definición (classDef) para reproducir el esquema de colores de Figma:\n"
            "    classDef inicioFin fill:#E9ECEF,stroke:#ADB5BD,stroke-width:1.5px,color:#000;\n"
            "    classDef manual fill:#FFFFFF,stroke:#000000,stroke-width:1.5px,color:#000;\n"
            "    classDef sistema fill:#FFEADB,stroke:#000000,stroke-width:1.5px,color:#000;\n"
            "    classDef mixto fill:#FFFFFF,stroke:#000000,stroke-width:1.5px,color:#000;\n"
            "    classDef decision fill:#FFFFFF,stroke:#000000,stroke-width:1.5px,color:#000;\n"
            "    classDef conector fill:#E9ECEF,stroke:#495057,stroke-width:1px,color:#000;\n"
            "    classDef subproceso fill:#FFFFFF,stroke:#000000,stroke-width:1.5px,color:#000;\n"
            "    classDef documento fill:#F8FAFC,stroke:#94A3B8,stroke-width:1px,stroke-dasharray:5 5,color:#475569;\n\n"
            "    Asigna las clases a cada nodo según su tipo (separando con comas):\n"
            "    class Inicio,Fin inicioFin;\n"
            "    class NodeManual1,NodeManual2 manual;\n"
            "    class NodeSistema1,NodeSistema2 sistema;\n"
            "    class NodeMixto1,NodeMixto2 mixto;\n"
            "    class Decis1 decision;\n"
            "    class ConnA conector;\n"
            "    class SubProc1 subproceso;\n"
            "    class Doc1 documento;\n"
            "11. Para que los carriles (subgraphs) parezcan columnas delimitadas por líneas discontinuas color naranja (estilo Figma), DEBES aplicar el siguiente estilo al final del código para cada subgraph ID:\n"
            "    style SubgraphID fill:#FAF9F6,stroke:#F85000,stroke-width:1px,stroke-dasharray: 5 5;\n"
            "12. Conecta los nodos con flechas limpias, ej. A --> B. Las decisiones deben tener etiquetas de condición claras, ej. Decis1 -->|Sí| B.\n"
            "13. NO incluyas bloques de código Markdown (```mermaid) en la variable 'mermaid_code', solo devuelve el código de diagrama de flujo puro."
        )
        
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self.system_instruction
        )

    def analyze_raw_process(self, raw_text: str, doc_type: str = "Procedimiento") -> EstructuraDocumento:
        """
        Toma una entrada en bruto del usuario y la procesa usando Gemini, con un sistema de
        reintentos y fallback secuencial a través de múltiples modelos disponibles si se encuentra
        un error de límite de cuota (429) o de otro tipo. Develviendo un objeto estructurado
        garantizado por Pydantic.
        """
        prompt = (
            f"Analiza el siguiente levantamiento de información en bruto y estructúralo como una '{doc_type}' corporativa en formato JSON.\n"
            f"Exigencia estricta: Redacta de forma sumamente detallada, extensa y completa cada uno de los campos.\n\n"
            f"El JSON devuelto DEBE tener obligatoriamente y de manera exacta la siguiente estructura de campos:\n"
            f"{{\n"
            f"  \"titulo\": \"Título formal del documento (ej. Normas sobre la gestión de precios)\",\n"
            f"  \"objetivo\": \"Explicación amplia y estratégica del propósito del documento (mínimo 60 palabras)\",\n"
            f"  \"alcance\": \"Alcance exhaustivo desglosado explícitamente en: Nivel Organizacional, Nivel de Procesos, Nivel de Sistemas, Nivel Temporal y Nivel Geográfico/Comercial\",\n"
            f"  \"responsabilidades\": [\n"
            f"    \"Desglose detallado del cargo X y sus obligaciones específicas en el flujo\",\n"
            f"    \"Desglose detallado del cargo Y y sus obligaciones específicas en el flujo\"\n"
            f"  ],\n"
            f"  \"normas\": [\n"
            f"    \"Norma 1: Párrafo amplio y robusto (mínimo 50-100 palabras) que explique detalladamente la regla de negocio, controles, validaciones del software (ej. Odoo) y el flujo por excepción\",\n"
            f"    \"Norma 2: Párrafo amplio y robusto (mínimo 50-100 palabras) sobre otra política estratégica...\"\n"
            f"  ],\n"
            f"  \"definiciones\": [\n"
            f"    {{\"termino\": \"ERP Odoo / API / POS / FEFO / etc.\", \"definicion\": \"Explicación técnica detallada y formal (mínimo 15 palabras)\"}}\n"
            f"  ],\n"
            f"  \"pasos\": [\n"
            f"    {{\n"
            f"      \"numero\": 1,\n"
            f"      \"actividad\": \"Nombre corto de la actividad\",\n"
            f"      \"responsable\": \"Cargo responsable\",\n"
            f"      \"descripcion\": \"Descripción minuciosa y exhaustiva de cómo se ejecuta este paso, qué se valida, qué software o portal se utiliza y qué controles de seguridad se aplican (mínimo 30-50 palabras)\"\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"documentos_referencia\": [\n"
            f"    \"Sistemas, formatos o leyes reguladoras involucradas\"\n"
            f"  ],\n"
            f"  \"mermaid_code\": \"Código Mermaid.js del diagrama sin el bloque ```mermaid\"\n"
            f"}}\n\n"
            f"REGLAS CRÍTICAS PARA EL 'mermaid_code' (ESTILO FIGMA BPMN):\n"
            f"- Inicia con 'flowchart TD'.\n"
            f"- Agrupa obligatoriamente los nodos por responsables/roles usando bloques 'subgraph'.\n"
            f"- Representa actividades en rectángulos tradicionales usando un salto de línea '\\n' y el mecanismo entre corchetes, ej. 'Node1[\"Nombre de la Actividad \\n [Sistema]\"]'.\n"
            f"- NUNCA uses etiquetas HTML como <br>, <div>, <hr> o <span> dentro de los textos de los nodos para asegurar legibilidad directa en cualquier herramienta.\n"
            f"- Aplica las clases de estilo de Figma (inicioFin, manual, sistema, mixto, decision, conector, subproceso, documento) a los respectivos nodos.\n"
            f"- Aplica el estilo 'style SubgraphID fill:#FAF9F6,stroke:#F85000,stroke-width:1px,stroke-dasharray: 5 5;' para cada subgraph.\n"
            f"- NUNCA uses paréntesis, corchetes ni llaves directamente dentro de los identificadores de nodos.\n\n"
            f"Levantamiento de información en bruto del usuario:\n"
            f"\"\"\"\n{raw_text}\n\"\"\""
        )

        # Modelos de texto ordenados por preferencia de uso para el fallback de cuota
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-3.5-flash",
            "gemini-3-flash",
            "gemini-3.1-flash-lite",
            "gemini-1.5-flash"
        ]

        last_exception = None

        for model_name in models_to_try:
            config.logger.info(f"Intentando estructuración con el modelo Gemini: {model_name}...")
            try:
                # Inicializar el modelo dinámicamente con las instrucciones de sistema
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=self.system_instruction
                )

                # Llamar a Gemini solicitando salida JSON. Forzamos JSON con response_mime_type
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.2  # Temperatura baja para mayor consistencia
                    ),
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                )

                # Cargar el JSON y validarlo a través de Pydantic
                response_json = json.loads(response.text)
                
                # Sanitizar el código Mermaid de forma robusta
                if "mermaid_code" in response_json:
                    response_json["mermaid_code"] = self.clean_mermaid_code(response_json["mermaid_code"])
                    
                # Sanitizar y re-indexar los números de paso secuencialmente como enteros
                if "pasos" in response_json and isinstance(response_json["pasos"], list):
                    for index, paso in enumerate(response_json["pasos"]):
                        paso["numero"] = index + 1
                    
                structured_data = EstructuraDocumento(**response_json)
                config.logger.info(f"¡Estructura de proceso generada con éxito usando {model_name}!")
                return structured_data

            except Exception as e:
                last_exception = e
                config.logger.warning(f"Error o límite de cuota excedido con el modelo {model_name}: {e}")
                continue

        # Si se agotaron todos los modelos sin éxito
        config.logger.error("Todos los modelos de Gemini fallaron o excedieron su límite de cuota.")
        raise last_exception

    def clean_mermaid_code(self, mermaid_str: str) -> str:
        """
        Limpia y sanitiza el código Mermaid para garantizar que no contenga errores de sintaxis, 
        especialmente en la declaración y estilo de subgraphs con espacios o caracteres especiales.
        """
        import re
        
        # Eliminar bloques markdown en caso de que vengan
        mermaid_str = mermaid_str.replace("```mermaid", "").replace("```", "").strip()
        
        # Sanitizar símbolos matemáticos que interfieren con el parser de HTML de Mermaid
        # 1. Ocultar temporalmente las conexiones de flechas de Mermaid para protegerlas
        mermaid_str = mermaid_str.replace("-->", "__ARROW_LONG__")
        mermaid_str = mermaid_str.replace("-.->", "__ARROW_DASH__")
        mermaid_str = mermaid_str.replace("==>", "__ARROW_THICK__")
        mermaid_str = mermaid_str.replace("->", "__ARROW_SHORT__")
        
        # 2. Ocultar temporalmente etiquetas <br> válidas con un placeholder único
        mermaid_str = re.sub(r'<\s*br\s*/?\s*>', '__BR_PLACEHOLDER__', mermaid_str, flags=re.IGNORECASE)
        
        # 3. Reemplazar operadores matemáticos sueltos y ampersands que romperían el parser HTML/XML de Mermaid
        mermaid_str = mermaid_str.replace("<=", " menor o igual a ").replace(">=", " mayor o igual a ")
        mermaid_str = mermaid_str.replace("<", " menor a ").replace(">", " mayor a ")
        mermaid_str = mermaid_str.replace("&", " y ")
        
        # 4. Restaurar los saltos de línea como saltos reales \n para evitar código HTML crudo
        mermaid_str = mermaid_str.replace("__BR_PLACEHOLDER__", "\n")
        
        # 5. Restaurar conexiones de flechas de Mermaid originales
        mermaid_str = mermaid_str.replace("__ARROW_SHORT__", "->")
        mermaid_str = mermaid_str.replace("__ARROW_THICK__", "==>")
        mermaid_str = mermaid_str.replace("__ARROW_DASH__", "-.->")
        mermaid_str = mermaid_str.replace("__ARROW_LONG__", "-->")
        
        lines = mermaid_str.split("\n")
        cleaned_lines = []
        subgraph_map = {} # Mapeo de nombre original a ID limpio
        
        # 1. Primera pasada para identificar y normalizar subgraphs
        for line in lines:
            strip_line = line.strip()
            if strip_line.startswith("subgraph "):
                content = strip_line[len("subgraph "):].strip()
                
                # Caso A: subgraph ID["Label"]
                match_labeled = re.match(r'^([a-zA-Z0-9_\-]+)\s*\["([^"]+)"\]', content)
                if match_labeled:
                    sub_id = match_labeled.group(1)
                    label = match_labeled.group(2)
                    subgraph_map[sub_id] = sub_id
                    cleaned_lines.append(f"    subgraph {sub_id}[\"{label}\"]")
                    continue
                
                # Caso B: subgraph "Label" o subgraph Label (con espacios o caracteres especiales)
                label = content
                if label.startswith('"') and label.endswith('"'):
                    label = label[1:-1]
                
                # Generar un ID alfanumérico limpio (reemplazando espacios por guiones bajos)
                id_label = label.lower().replace(' ', '_')
                for a, b in [('á', 'a'), ('é', 'e'), ('í', 'i'), ('ó', 'o'), ('ú', 'u'), ('ñ', 'n')]:
                    id_label = id_label.replace(a, b)
                clean_id = re.sub(r'[^a-zA-Z0-9_]', '', id_label)
                if not clean_id:
                    clean_id = f"sub_{len(subgraph_map)}"
                
                subgraph_map[content] = clean_id
                subgraph_map[label] = clean_id
                subgraph_map[f'"{label}"'] = clean_id
                
                cleaned_lines.append(f"    subgraph {clean_id}[\"{label}\"]")
            else:
                cleaned_lines.append(line)
                
        # 2. Segunda pasada para reemplazar los nombres antiguos de subgraph en los estilos y remover punto y coma al final de declaraciones de estilo/classDef/class
        final_lines = []
        for line in cleaned_lines:
            new_line = line
            strip_line = line.strip()
            
            # Quitar punto y coma al final de líneas de estilo, classDef o class
            if strip_line.startswith("style ") or strip_line.startswith("classDef ") or strip_line.startswith("class "):
                if strip_line.endswith(";"):
                    # Eliminar la última ocurrencia del punto y coma
                    idx_semicolon = new_line.rfind(";")
                    if idx_semicolon != -1:
                        new_line = new_line[:idx_semicolon] + new_line[idx_semicolon+1:]
            
            strip_line = new_line.strip()
            if strip_line.startswith("style "):
                # Buscar si hace referencia a algún subgraph antiguo del mapa
                for orig_name, clean_id in subgraph_map.items():
                    # Reemplazar con comillas exactas primero
                    new_line = new_line.replace(f'"{orig_name}"', clean_id)
                    # Reemplazar sin comillas
                    new_line = new_line.replace(orig_name, clean_id)
            final_lines.append(new_line)
            
        return "\n".join(final_lines)

    def generate_html_mermaid_code(self, clean_code: str) -> str:
        """
        Toma el código Mermaid limpio y compatible con Figma y lo transforma en un código
        con etiquetas HTML estilizadas para que se renderice exactamente igual que la
        Plantilla de ejemplo .pdf (cajas divididas con encabezados de mecanismo).
        """
        import re
        
        html_code = clean_code
        
        # Expresión regular para encontrar declaraciones de nodo con mecanismo (admite \n y <br>)
        pattern = r'([a-zA-Z0-9_\-]+)\["((?:[^"]|\n)+?)\s*(?:\n|<\s*br\s*/?>)\s*\[([^\]]+)\]"\]'
        
        def replace_node(match):
            node_id = match.group(1)
            activity_text = match.group(2).strip()
            mechanism = match.group(3).strip()
            
            # Reemplazar saltos de línea reales (\n) por <br> para que el HTML del navegador los entienda
            activity_text_html = activity_text.replace("\n", "<br>")
            
            # Determinar estilos basados en el mecanismo
            mech_lower = mechanism.lower()
            if "sistema/manual" in mech_lower or "mixto" in mech_lower or "manual/sistema" in mech_lower:
                bg_bottom = "#F1F5F9"
                text_color_bottom = "#475569"
                font_weight_bottom = "700"
                display_mech = "Sistema/Manual"
            elif "sistema" in mech_lower or "automatica" in mech_lower or "automática" in mech_lower:
                bg_bottom = "#FFEADB"
                text_color_bottom = "#F85000"
                font_weight_bottom = "900"
                display_mech = "Sistema"
            else: # Manual
                bg_bottom = "#FFFFFF"
                text_color_bottom = "#64748B"
                font_weight_bottom = "700"
                display_mech = "Manual"
                
            # HTML premium idéntico al PDF de Farmacia Enterprise SGC (cajas divididas tipo Figma)
            html_label = (
                f"<div style='"
                f"border: 1.5px solid #000000; "
                f"border-radius: 6px; "
                f"width: 195px; "
                f"overflow: hidden; "
                f"background-color: #FFFFFF; "
                f"font-family: Outfit, sans-serif; "
                f"box-shadow: 0 2px 4px rgba(0,0,0,0.03);"
                f"'>"
                f"<div style='"
                f"padding: 12px 14px; "
                f"font-size: 0.8rem; "
                f"font-weight: 600; "
                f"color: #1E293B; "
                f"min-height: 48px; "
                f"display: flex; "
                f"align-items: center; "
                f"justify-content: center; "
                f"text-align: center; "
                f"line-height: 1.3;"
                f"'>"
                f"{activity_text_html}"
                f"</div>"
                f"<div style='"
                f"background-color: {bg_bottom}; "
                f"border-top: 1.5px solid #000000; "
                f"padding: 5px; "
                f"font-size: 0.65rem; "
                f"font-weight: {font_weight_bottom}; "
                f"color: {text_color_bottom}; "
                f"text-transform: uppercase; "
                f"text-align: center; "
                f"letter-spacing: 0.5px; "
                f"line-height: 1;"
                f"'>"
                f"{display_mech}"
                f"</div>"
                f"</div>"
            )
            return f'{node_id}["{html_label}"]'
            
        html_code = re.sub(pattern, replace_node, html_code)
        return html_code

    def generate_from_drawio(self, drawio_data: dict, doc_type: str = "Procedimiento") -> EstructuraDocumento:
        """
        Recibe la estructura parseada de un archivo Draw.io y genera un documento formal BPMN completo
        (con objetivos, alcances, glosario de definiciones, normas, descripciones detalladas de los pasos,
        y un código Mermaid.js regenerado y compatible).
        """
        # Convertir los pasos y conexiones en un texto comprensible para Gemini
        steps_text = []
        for s in drawio_data.get("steps", []):
            steps_text.append(f"- Responsable: {s['role']} | Actividad/Texto: {s['text']}")
            
        conn_text = []
        for c in drawio_data.get("connections", []):
            conn_text.append(f"- {c}")
            
        steps_str = "\n".join(steps_text)
        conn_str = "\n".join(conn_text)
        
        prompt = (
            f"Actúa como un Consultor Senior de Procesos y Experto en BPM.\n"
            f"Se ha extraído la estructura de un diagrama de flujo directamente desde un archivo de Draw.io.\n"
            f"Tu tarea es reconstruir y formalizar este proceso como un documento de tipo '{doc_type}' corporativo completo en formato JSON, con un nivel de detalle y profundidad excepcional.\n\n"
            f"A continuación tienes la estructura del diagrama parseado:\n"
            f"PASOS / NODOS EXTRAÍDOS:\n"
            f"{steps_str}\n\n"
            f"CONEXIONES / FLUJO LÓGICO EXTRAÍDO:\n"
            f"{conn_str}\n\n"
            "INSTRUCCIONES DE REDACCIÓN EXHAUSTIVA:\n"
            "1. **Título**: Crea un título formal apropiado (ej: 'Procedimiento de Adquisición de Bienes').\n"
            "2. **Objetivo**: Redacta un propósito amplio, estratégico y detallado (mínimo 60 palabras) que fundamente el proceso.\n"
            "3. **Alcance**: Desglosa el alcance obligatoriamente en 5 niveles detallados (Nivel Organizacional, de Procesos, de Sistemas, Temporal, y Geográfico/Comercial).\n"
            "4. **Responsabilidades**: Para cada rol involucrado en el diagrama, describe detalladamente y de forma extensa sus funciones y responsabilidades en este flujo.\n"
            "5. **Descripción Detallada de los Pasos**: Para cada paso extraído, conserva el número y el responsable, pero **amplía y redacta una descripción detallada, profesional y muy extensa** (mínimo 30-50 palabras por paso) de cómo se ejecuta esa tarea, especificando sistemas (ej: Odoo ERP), pantallas, botones, validaciones de seguridad y flujos alternativos.\n"
            "6. **Normas y Políticas**: Genera de 3 a 7 normas corporativas muy completas y extensas. Cada norma debe ser un párrafo robusto (mínimo 50-100 palabras) detallando las reglas a seguir, alertas del sistema y control de excepciones.\n"
            "7. **Glosario**: Define exhaustivamente todos los términos técnicos, siglas o herramientas que aparecen en el diagrama (mínimo 8 definiciones completas).\n"
            "8. **Mermaid Code**: Regenera el código Mermaid.js optimizado, 100% compatible con Figma, limpio de HTML, usando subgraphs verticales para cada responsable, cajas con mecanismo '[Manual]', '[Sistema]' o '[Sistema/Manual]', rombos de decisión '{}' y las clases classDef/style oficiales de Farmacia Enterprise SGC.\n\n"
            "El JSON devuelto DEBE tener obligatoriamente y de manera exacta la siguiente estructura de campos:\n"
            "{\n"
            "  \"titulo\": \"Título formal del documento\",\n"
            "  \"objetivo\": \"Propósito estratégico amplio y estructurado\",\n"
            "  \"alcance\": \"Alcance exhaustivo desglosado en los 5 niveles (Organizacional, Procesos, Sistemas, Temporal, Geográfico)\",\n"
            "  \"responsabilidades\": [\n"
            "    \"Desglose detallado del cargo X y sus obligaciones específicas en el flujo\",\n"
            "    \"Desglose detallado del cargo Y y sus obligaciones específicas en el flujo\"\n"
            "  ],\n"
            "  \"normas\": [\n"
            "    \"Norma 1: Párrafo amplio y robusto (mínimo 50-100 palabras) con la regla, sistemas y controles...\",\n"
            "    \"Norma 2: Párrafo amplio y robusto (mínimo 50-100 palabras)...\"\n"
            "  ],\n"
            "  \"definiciones\": [\n"
            "    {\"termino\": \"Término\", \"definicion\": \"Explicación técnica detallada y formal (mínimo 15 palabras)\"}\n"
            "  ],\n"
            "  \"pasos\": [\n"
            "    {\n"
            "      \"numero\": 1,\n"
            "      \"actividad\": \"Nombre corto de la actividad\",\n"
            "      \"responsable\": \"Cargo responsable\",\n"
            "      \"descripcion\": \"Descripción minuciosa y exhaustiva de cómo se ejecuta este paso, validaciones y software usado (mínimo 30-50 palabras)\"\n"
            "    }\n"
            "  ],\n"
            "  \"documentos_referencia\": [\n"
            "    \"Sistemas, formatos o leyes reguladoras involucradas\"\n"
            "  ],\n"
            "  \"mermaid_code\": \"Código Mermaid.js del diagrama sin el bloque ```mermaid\"\n"
            "}\n"
        )
        
        # Reutilizar el sistema robusto de fallback secuencial de modelos
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-3.5-flash",
            "gemini-3-flash",
            "gemini-3.1-flash-lite",
            "gemini-1.5-flash"
        ]
        
        last_exception = None
        
        for model_name in models_to_try:
            config.logger.info(f"Intentando generación desde Draw.io con el modelo Gemini: {model_name}...")
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=self.system_instruction
                )
                
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.2
                    ),
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                )
                
                response_json = json.loads(response.text)
                
                if "mermaid_code" in response_json:
                    response_json["mermaid_code"] = self.clean_mermaid_code(response_json["mermaid_code"])
                    
                if "pasos" in response_json and isinstance(response_json["pasos"], list):
                    for index, paso in enumerate(response_json["pasos"]):
                        paso["numero"] = index + 1
                        
                structured_data = EstructuraDocumento(**response_json)
                config.logger.info(f"¡Procedimiento regenerado con éxito desde Draw.io usando {model_name}!")
                return structured_data
                
            except Exception as e:
                last_exception = e
                config.logger.warning(f"Error o límite de cuota excedido en generación desde Draw.io con el modelo {model_name}: {e}")
                continue
                
        config.logger.error("Todos los modelos fallaron al intentar regenerar desde Draw.io.")
        raise last_exception

    def get_chat_response(self, chat_history: list, user_message: str, doc_type: str = "Procedimiento") -> str:
        """
        Genera la siguiente respuesta del consultor BPM de forma conversacional y guiada.
        """
        transcript = ""
        for msg in chat_history:
            role_name = "Usuario" if msg["role"] == "user" else "Consultor BPM"
            transcript += f"{role_name}: {msg['content']}\n\n"
            
        prompt = (
            f"Actúas como un Consultor Senior de Procesos BPM de Farmacia Enterprise SGC.\n"
            f"Tu tarea es guiar al usuario en la definición, aclaración o diseño de su proceso operativo de tipo '{doc_type}'.\n"
            f"Sé profesional, educado, empático y directo en español.\n"
            f"Si el usuario sube notas, minutas o el texto de un PDF, hazle preguntas inteligentes si consideras que faltan datos clave (roles responsables, sistemas de software usados, reglas de negocio, o pasos del flujo).\n"
            f"NO generes ni respondas con el JSON de proceso o el código Mermaid aquí en la conversación. Tu objetivo es conversar y acordar los detalles del proceso con el usuario.\n"
            f"Recuérdale amigablemente al usuario que en cualquier momento puede hacer clic en el botón '⚡ Generar Estructura y Flujograma BPM' en el panel derecho para ver y exportar el flujograma y documento formal en Word.\n\n"
            f"Historial de conversación anterior:\n"
            f"\"\"\"\n{transcript}\"\"\"\n"
            f"Nuevo mensaje del Usuario:\n"
            f"\"{user_message}\"\n\n"
            f"Respuesta del Consultor BPM:"
        )
        
        # Modelos de texto ordenados por preferencia para el chat
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-3.5-flash",
            "gemini-3-flash",
            "gemini-3.1-flash-lite",
            "gemini-1.5-flash"
        ]
        
        last_exception = None
        for model_name in models_to_try:
            try:
                model = genai.GenerativeModel(
                    model_name=model_name
                )
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7 # Mayor creatividad para conversar de forma fluida
                    ),
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                )
                return response.text.strip()
            except Exception as e:
                last_exception = e
                config.logger.warning(f"Error en chat con el modelo {model_name}: {e}")
                continue
                
        raise last_exception

    def analyze_chat_conversation(self, chat_history: list, doc_type: str = "Procedimiento") -> EstructuraDocumento:
        """
        Analiza todo el historial de conversación del chat (que puede incluir PDFs y texto)
        y genera la estructura de proceso BPM formal completa (EstructuraDocumento).
        """
        transcript = ""
        for msg in chat_history:
            role_name = "Usuario" if msg["role"] == "user" else "Consultor BPM"
            transcript += f"{role_name}: {msg['content']}\n\n"

        prompt = (
            f"Analiza detalladamente todo el historial de la conversación entre el usuario y el Consultor BPM "
            f"y consolidalo estructurando una '{doc_type}' corporativa formal en formato JSON.\n"
            f"Exigencia estricta: Redacta de forma sumamente detallada, extensa y completa cada uno de los campos.\n\n"
            f"Esta conversación contiene la definición y refinamientos de un proceso de negocio. "
            f"Asegúrate de incorporar e integrar todos los ajustes, cambios y correcciones que el usuario haya solicitado "
            f"a lo largo del chat (por ejemplo, si pidió cambiar un rol, renombrar un paso, agregar políticas o especificar Odoo ERP).\n\n"
            f"El JSON devuelto DEBE tener obligatoriamente y de manera exacta la siguiente estructura de campos:\n"
            f"{{\n"
            f"  \"titulo\": \"Título formal del documento (ej. Normas sobre la gestión de precios)\",\n"
            f"  \"objetivo\": \"Explicación amplia y estratégica del propósito del documento (mínimo 60 palabras)\",\n"
            f"  \"alcance\": \"Alcance exhaustivo desglosado explícitamente en: Nivel Organizacional, Nivel de Procesos, Nivel de Sistemas, Nivel Temporal y Nivel Geográfico/Comercial\",\n"
            f"  \"responsabilidades\": [\n"
            f"    \"Desglose detallado del cargo X y sus obligaciones específicas en el flujo\",\n"
            f"    \"Desglose detallado del cargo Y y sus obligaciones específicas en el flujo\"\n"
            f"  ],\n"
            f"  \"normas\": [\n"
            f"    \"Norma 1: Párrafo amplio y robusto (mínimo 50-100 palabras) que explique detalladamente la regla de negocio, controles, validaciones del software (ej. Odoo) y el flujo por excepción\",\n"
            f"    \"Norma 2: Párrafo amplio y robusto (mínimo 50-100 palabras) sobre otra política estratégica...\"\n"
            f"  ],\n"
            f"  \"definiciones\": [\n"
            f"    {{\"termino\": \"ERP Odoo / API / POS / FEFO / etc.\", \"definicion\": \"Explicación técnica detallada y formal (mínimo 15 palabras)\"}}\n"
            f"  ],\n"
            f"  \"pasos\": [\n"
            f"    {{\n"
            f"      \"numero\": 1,\n"
            f"      \"actividad\": \"Nombre corto de la actividad\",\n"
            f"      \"responsable\": \"Cargo responsable\",\n"
            f"      \"descripcion\": \"Descripción minuciosa y exhaustiva de cómo se ejecuta este paso, qué se valida, qué software o portal se utiliza y qué controles de seguridad se aplican (mínimo 30-50 palabras)\"\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"documentos_referencia\": [\n"
            f"    \"Sistemas, formatos o leyes reguladoras involucradas\"\n"
            f"  ],\n"
            f"  \"mermaid_code\": \"Código Mermaid.js del diagrama sin el bloque ```mermaid\"\n"
            f"}}\n\n"
            f"REGLAS CRÍTICAS PARA EL 'mermaid_code' (ESTILO FIGMA BPMN):\n"
            f"- Inicia con 'flowchart TD'.\n"
            f"- Agrupa obligatoriamente los nodos por responsables/roles usando bloques 'subgraph'.\n"
            f"- Representa actividades en rectángulos tradicionales usando un salto de línea '\\n' y el mecanismo entre corchetes, ej. 'Node1[\"Nombre de la Actividad \\n [Sistema]\"]'.\n"
            f"- NUNCA uses etiquetas HTML como <br>, <div>, <hr> o <span> dentro de los textos de los nodos para asegurar legibilidad directa en cualquier herramienta.\n"
            f"- Aplica las clases de estilo de Figma (inicioFin, manual, sistema, mixto, decision, conector, subproceso, documento) a los respectivos nodos.\n"
            f"- Aplica el estilo 'style SubgraphID fill:#FAF9F6,stroke:#F85000,stroke-width:1px,stroke-dasharray: 5 5;' para cada subgraph.\n"
            f"- NUNCA uses paréntesis, corchetes ni llaves directamente dentro de los identificadores de nodos.\n\n"
            f"Historial de conversación a consolidar:\n"
            f"\"\"\"\n{transcript}\n\"\"\""
        )

        # Modelos de texto ordenados por preferencia para la estructuración
        models_to_try = [
            "gemini-2.5-flash",
            "gemini-2.5-flash-lite",
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-3.5-flash",
            "gemini-3-flash",
            "gemini-3.1-flash-lite",
            "gemini-1.5-flash"
        ]

        last_exception = None
        for model_name in models_to_try:
            config.logger.info(f"Consolidando conversación de chat con el modelo: {model_name}...")
            try:
                model = genai.GenerativeModel(
                    model_name=model_name,
                    system_instruction=self.system_instruction
                )

                # Llamar a Gemini solicitando salida JSON. Forzamos JSON con response_mime_type
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        response_mime_type="application/json",
                        temperature=0.2  # Temperatura baja para estructuración consistente
                    ),
                    safety_settings=[
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
                    ]
                )

                # Cargar el JSON y validarlo a través de Pydantic
                response_json = json.loads(response.text)
                
                # Sanitizar el código Mermaid de forma robusta
                if "mermaid_code" in response_json:
                    response_json["mermaid_code"] = self.clean_mermaid_code(response_json["mermaid_code"])
                    
                # Sanitizar y re-indexar los números de paso secuencialmente como enteros
                if "pasos" in response_json and isinstance(response_json["pasos"], list):
                    for index, paso in enumerate(response_json["pasos"]):
                        paso["numero"] = index + 1
                    
                structured_data = EstructuraDocumento(**response_json)
                config.logger.info(f"¡Estructura de proceso consolidada con éxito desde chat usando {model_name}!")
                return structured_data

            except Exception as e:
                last_exception = e
                config.logger.warning(f"Error o límite de cuota excedido con el modelo {model_name} al consolidar chat: {e}")
                continue

        config.logger.error("Todos los modelos de Gemini fallaron al intentar consolidar el chat.")
        raise last_exception



