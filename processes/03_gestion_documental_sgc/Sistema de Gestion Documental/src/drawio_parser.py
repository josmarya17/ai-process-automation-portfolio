import base64
import zlib
import urllib.parse
import xml.etree.ElementTree as ET
import re

class DrawIOParser:
    @staticmethod
    def decompress_diagram(xml_str: str) -> str:
        """
        Decomprime un diagrama de Draw.io si está comprimido (formato estándar de exportación de draw.io).
        Si ya está descomprimido, lo devuelve tal cual.
        """
        try:
            # Intentar parsear como XML
            root = ET.fromstring(xml_str.strip())
            
            # Buscar nodos diagram
            diagram_nodes = root.findall(".//diagram")
            if not diagram_nodes:
                # Comprobar si el xml_str mismo es un mxGraphModel
                if "<mxGraphModel" in xml_str:
                    return xml_str
                return xml_str
            
            diagram_node = diagram_nodes[0]
            compressed_data = diagram_node.text
            
            if not compressed_data:
                # El nodo diagram no tiene texto, puede estar sin comprimir dentro de mxGraphModel
                mxmodel = diagram_node.find(".//mxGraphModel")
                if mxmodel is not None:
                    # Devolver el sub-XML completo del mxGraphModel
                    return ET.tostring(mxmodel, encoding="utf-8").decode("utf-8")
                return xml_str
            
            # Decompress Draw.io format: Base64 decode -> Decompress zlib (deflate raw) -> URL decode
            decoded = base64.b64decode(compressed_data.strip())
            decompressed = zlib.decompress(decoded, -15)
            url_decoded = urllib.parse.unquote(decompressed.decode('utf-8'))
            return url_decoded
        except Exception:
            # Fallback en caso de error, devolver original
            return xml_str

    @staticmethod
    def clean_html(html_str: str) -> str:
        """
        Elimina las etiquetas HTML de un texto para obtener solo el contenido limpio.
        """
        if not html_str:
            return ""
        # Reemplazar saltos de línea HTML por saltos reales
        text = re.sub(r'<\s*br\s*/?\s*>', '\n', html_str)
        text = re.sub(r'<\s*p\s*/?\s*>', '\n', text)
        text = re.sub(r'<\s*/\s*div\s*>', '\n', text)
        text = re.sub(r'<\s*hr\s*/?\s*>', '\n---\n', text)
        # Eliminar cualquier otra etiqueta
        text = re.sub(r'<[^>]+>', '', text)
        # Decodificar entidades HTML básicas
        text = (text.replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                    .replace("&quot;", '"')
                    .replace("&apos;", "'")
                    .replace("&nbsp;", " "))
        
        # Limpiar saltos de línea repetidos
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return " \n ".join(lines)

    @staticmethod
    def parse_drawio(file_content: str) -> dict:
        """
        Parsea un archivo .drawio (comprimido o descomprimido).
        Retorna un diccionario estructurado con los roles, actividades, decisiones y conexiones encontradas.
        """
        uncompressed_xml = DrawIOParser.decompress_diagram(file_content)
        
        try:
            # Envolver en un nodo raíz si el XML descomprimido no lo tiene
            if not uncompressed_xml.strip().startswith("<"):
                # No es XML válido
                return {"error": "El archivo no contiene un XML válido de Draw.io o está vacío."}
            
            # Buscar mxGraphModel
            if "<mxGraphModel" in uncompressed_xml:
                # Extraer solo desde mxGraphModel para evitar problemas de namespaces y etiquetas outer
                start_idx = uncompressed_xml.find("<mxGraphModel")
                end_idx = uncompressed_xml.find("</mxGraphModel>") + len("</mxGraphModel>")
                mxgraph_xml = uncompressed_xml[start_idx:end_idx]
                root = ET.fromstring(mxgraph_xml)
            else:
                root = ET.fromstring(uncompressed_xml.strip())
                
            cells = root.findall(".//mxCell")
            
            nodes = {}
            connections = []
            
            for cell in cells:
                cell_id = cell.get("id")
                is_vertex = cell.get("vertex") == "1"
                is_edge = cell.get("edge") == "1"
                value = cell.get("value", "")
                
                if is_vertex and value:
                    cleaned_val = DrawIOParser.clean_html(value)
                    
                    # Identificar si es un carril (swimlane) o cabecera de carril
                    style = cell.get("style", "")
                    is_swimlane = "swimlane" in style or "dashed=1" in style or "fillColor=#F85000" in style or "fillColor=#FAF9F6" in style
                    
                    # Ignorar el nodo cajetín y celdas de logotipo si las hay
                    if "código" in cleaned_val.lower() or "versión" in cleaned_val.lower() or "fecha" in cleaned_val.lower() or "farmacia" in cleaned_val.lower() or "Enterprise SGC" in cleaned_val.lower():
                        if is_swimlane:
                            continue
                            
                    nodes[cell_id] = {
                        "id": cell_id,
                        "raw_value": value,
                        "value": cleaned_val,
                        "parent": cell.get("parent"),
                        "is_swimlane": is_swimlane,
                        "style": style
                    }
                elif is_edge:
                    connections.append({
                        "id": cell_id,
                        "source": cell.get("source"),
                        "target": cell.get("target"),
                        "value": DrawIOParser.clean_html(value)
                    })
                    
            # Agrupar actividades por su swimlane
            swimlanes = {nid: n for nid, n in nodes.items() if n["is_swimlane"]}
            activities = {nid: n for nid, n in nodes.items() if not n["is_swimlane"]}
            
            # Asociar actividades a roles
            structured_steps = []
            for aid, act in activities.items():
                parent_id = act["parent"]
                role = "General / No Asignado"
                
                # Buscar en swimlanes
                if parent_id in swimlanes:
                    role = swimlanes[parent_id]["value"]
                else:
                    # Buscar el ancestro más cercano que sea swimlane
                    curr_parent = parent_id
                    while curr_parent and curr_parent != "1" and curr_parent != "0":
                        if curr_parent in swimlanes:
                            role = swimlanes[curr_parent]["value"]
                            break
                        # ir al siguiente parent
                        if curr_parent in nodes:
                            curr_parent = nodes[curr_parent]["parent"]
                        else:
                            break
                
                # Limpiar cualquier texto de rol largo o nulo
                role = role.split('\n')[0].strip() # Tomar primera línea si hay saltos
                
                structured_steps.append({
                    "id": aid,
                    "text": act["value"],
                    "role": role
                })
                
            # Mapear conexiones con nombres
            mapped_connections = []
            for conn in connections:
                src_node = nodes.get(conn["source"])
                tgt_node = nodes.get(conn["target"])
                
                if src_node and tgt_node:
                    src_clean = src_node['value'].replace('\n', ' ').strip()
                    tgt_clean = tgt_node['value'].replace('\n', ' ').strip()
                    if len(src_clean) > 50:
                        src_clean = src_clean[:47] + "..."
                    if len(tgt_clean) > 50:
                        tgt_clean = tgt_clean[:47] + "..."
                        
                    mapped_connections.append(
                        f"De '{src_clean}' a '{tgt_clean}'" + 
                        (f" (Condición: {conn['value']})" if conn["value"] else "")
                    )
            
            return {
                "steps": structured_steps,
                "connections": mapped_connections,
                "raw_nodes": [n["value"] for n in nodes.values() if not n["is_swimlane"]]
            }
            
        except Exception as e:
            return {"error": f"Error al procesar la estructura del XML de Draw.io: {e}"}
