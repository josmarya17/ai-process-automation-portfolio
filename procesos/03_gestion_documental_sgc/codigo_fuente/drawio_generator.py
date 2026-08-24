import os
import base64

class DrawIOGenerator:
    @staticmethod
    def escape_xml(text: str) -> str:
        """
        Escapa caracteres especiales para que sean válidos en atributos XML de draw.io.
        """
        if not text:
            return ""
        return (text.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                    .replace('"', "&quot;")
                    .replace("'", "&apos;"))

    @staticmethod
    def sanitize_text_for_html(text: str) -> str:
        """
        Sanitiza el texto para evitar que rompa las etiquetas HTML embebidas en draw.io.
        """
        if not text:
            return ""
        return text.replace("<", "&lt;").replace(">", "&gt;")

    @staticmethod
    def generate_drawio(doc, code: str, version: str, date_str: str) -> str:
        """
        Genera un diagrama de flujo totalmente editable y ajustable para Draw.io/Diagrams.net (.drawio).
        Mantiene el mismo cajetín premium, carriles por responsable, colores de Farmacia Enterprise SGC,
        y hace que los bloques y flechas sean 100% interactivos y auto-ajustables al moverlos.
        """
        code = DrawIOGenerator.escape_xml(code)
        version = DrawIOGenerator.escape_xml(version)
        date_str = DrawIOGenerator.escape_xml(date_str)
        title_display = DrawIOGenerator.escape_xml(doc.titulo)

        # 1. Obtener responsables únicos para las columnas
        seen = set()
        roles = []
        for p in doc.pasos:
            resp = p.responsable
            if resp not in seen:
                seen.add(resp)
                roles.append(resp)
        if not roles:
            roles = ["Responsable"]

        num_columns = len(roles)
        column_width = 250
        margin_left = 50
        margin_right = 50
        width = margin_left + (num_columns * column_width) + margin_right

        # Altura dinámica
        num_steps = len(doc.pasos)
        y_start_steps = 180
        y_spacing = 150
        flowchart_height = (num_steps * y_spacing) + 120
        height = y_start_steps + flowchart_height

        # Cargar Logotipo Oficial en Base64
        logo_base64 = ""
        possible_paths = [
            "Logo_Enterprise SGC.jpg",
            os.path.join(os.path.dirname(__file__), "..", "Logo_Enterprise SGC.jpg"),
            os.path.join(os.getcwd(), "Logo_Enterprise SGC.jpg"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "rb") as img_f:
                        logo_base64 = base64.b64encode(img_f.read()).decode('utf-8')
                    break
                except Exception:
                    pass

        # Construir XML
        xml = []
        xml.append('<?xml version="1.0" encoding="UTF-8"?>')
        xml.append('<mxfile host="Electron" modified="2026-05-28T00:00:00.000Z" agent="Antigravity" version="21.6.8" type="device">')
        xml.append(f'  <diagram id="Enterprise SGCDiagram" name="{title_display}">')
        xml.append(f'    <mxGraphModel dx="1200" dy="1000" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="{width + 100}" pageHeight="{height + 100}" math="0" shadow="0">')
        xml.append('      <root>')
        xml.append('        <mxCell id="0"/>')
        xml.append('        <mxCell id="1" parent="0"/>')

        cell_id = 2

        # ==========================================
        # 1. CAJETÍN (ENCABEZADO DE PROCESO)
        # ==========================================
        # Fondo del Cajetín
        xml.append(f'        <mxCell id="{cell_id}" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#E2E8F0;strokeWidth=1.5;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="0" y="0" width="{width}" height="100" as="geometry"/>')
        xml.append('        </mxCell>')
        cajetin_parent_id = cell_id
        cell_id += 1

        # Logotipo Oficial Enterprise SGC o Fallback
        if logo_base64:
            logo_val = DrawIOGenerator.escape_xml(f'<img src="data:image/jpeg;base64,{logo_base64}" width="210" height="70"/>')
        else:
            logo_val = DrawIOGenerator.escape_xml('<div style="font-family:\'Outfit\'; font-size:30px; font-weight:900; color:#F85000; letter-spacing:-1.5px;">farmacia<span style="color:#475569;">Enterprise SGC</span></div>')
        
        xml.append(f'        <mxCell id="{cell_id}" value="{logo_val}" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;overflow=hidden;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="25" y="15" width="210" height="70" as="geometry"/>')
        xml.append('        </mxCell>')
        cell_id += 1

        # Línea divisoria
        xml.append(f'        <mxCell id="{cell_id}" value="" style="line;strokeColor=#CBD5E1;strokeWidth=1.5;direction=south;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="260" y="20" width="1" height="60" as="geometry"/>')
        xml.append('        </mxCell>')
        cell_id += 1

        # Título
        title_val = DrawIOGenerator.escape_xml(f'<div style="font-family:\'Outfit\'; font-size:16px; font-weight:700; color:#1E293B; text-align:left;">{doc.titulo}</div>')
        xml.append(f'        <mxCell id="{cell_id}" value="{title_val}" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=middle;whiteSpace=wrap;rounded=0;overflow=hidden;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="290" y="20" width="{width - 650}" height="60" as="geometry"/>')
        xml.append('        </mxCell>')
        cell_id += 1

        # Tabla de Especificaciones
        specs_html = f"""<table border="1" cellpadding="4" cellspacing="0" style="width:100%; height:100%; border-collapse:collapse; border:1px solid #CBD5E1; font-family:'Outfit', sans-serif; font-size:10px; color:#475569; background-color:#F8FAFC;">
          <tr>
            <td style="width:35%; font-weight:700; border:1px solid #CBD5E1; padding:3px;">Código</td>
            <td style="width:65%; font-weight:800; color:#1E293B; border:1px solid #CBD5E1; font-size:11px; letter-spacing:0.5px; padding:3px;">{code}</td>
          </tr>
          <tr>
            <td style="font-weight:700; border:1px solid #CBD5E1; padding:3px;">Versión</td>
            <td style="font-weight:700; color:#1E293B; border:1px solid #CBD5E1; font-size:11px; padding:3px;">{version}</td>
          </tr>
          <tr>
            <td style="font-weight:700; border:1px solid #CBD5E1; padding:3px;">Fecha</td>
            <td style="font-weight:500; color:#1E293B; border:1px solid #CBD5E1; font-size:11px; padding:3px;">{date_str}</td>
          </tr>
        </table>"""
        specs_val = DrawIOGenerator.escape_xml(specs_html)
        xml.append(f'        <mxCell id="{cell_id}" value="{specs_val}" style="text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;overflow=hidden;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{width - 340}" y="15" width="290" height="70" as="geometry"/>')
        xml.append('        </mxCell>')
        cell_id += 1

        # ==========================================
        # 2. CARRILES / SWIMLANES (ROLES)
        # ==========================================
        for j, role in enumerate(roles):
            x_start = margin_left + (j * column_width)
            
            # Fondo/Borde del Carril
            xml.append(f'        <mxCell id="{cell_id}" value="" style="rounded=0;whiteSpace=wrap;html=1;fillColor=#FAF9F6;strokeColor=#F85000;strokeWidth=1;dashed=1;dashPattern=5 5;" vertex="1" parent="1">')
            xml.append(f'          <mxGeometry x="{x_start}" y="100" width="{column_width}" height="{flowchart_height}" as="geometry"/>')
            xml.append('        </mxCell>')
            cell_id += 1
            
            # Cabecera Sólida Naranja
            role_val = DrawIOGenerator.escape_xml(f'<div style="font-family:\'Outfit\'; font-size:11px; font-weight:800; color:#FFFFFF; text-align:center; letter-spacing:0.5px;">{role.upper()}</div>')
            xml.append(f'        <mxCell id="{cell_id}" value="{role_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#F85000;strokeColor=none;arcSize=15;" vertex="1" parent="1">')
            xml.append(f'          <mxGeometry x="{x_start + 6}" y="110" width="{column_width - 12}" height="36" as="geometry"/>')
            xml.append('        </mxCell>')
            cell_id += 1

        # ==========================================
        # 3. NODOS Y PASOS DEL FLUJO
        # ==========================================
        node_cell_ids = {} # Guardar cell_id de cada nodo para conectar
        
        # Nodo Inicio
        x_init = margin_left + (column_width / 2)
        y_init = y_start_steps
        init_val = DrawIOGenerator.escape_xml('<div style="font-family:\'Outfit\'; font-size:11px; font-weight:800; color:#1E293B; text-align:center;">Inicio</div>')
        xml.append(f'        <mxCell id="{cell_id}" value="{init_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E9ECEF;strokeColor=#94A3B8;strokeWidth=1.5;arcSize=50;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{x_init - 50}" y="{y_init - 18}" width="100" height="36" as="geometry"/>')
        xml.append('        </mxCell>')
        node_cell_ids["Inicio"] = cell_id
        cell_id += 1

        # Dibujar cada paso
        for idx, paso in enumerate(doc.pasos):
            paso_num = paso.numero
            actividad = paso.actividad
            responsable = paso.responsable
            desc = paso.descripcion
            
            try:
                col_idx = roles.index(responsable)
            except ValueError:
                col_idx = 0
                
            x_node = margin_left + (col_idx * column_width) + (column_width / 2)
            y_node = y_start_steps + ((idx + 1) * y_spacing)
            
            is_decision = actividad.strip().endswith("?") or "¿" in actividad or "si " in actividad.lower()
            
            if is_decision:
                # Decisión (Rombo)
                dec_val = DrawIOGenerator.escape_xml(f'<div style="font-family:\'Outfit\'; font-size:9.5px; font-weight:700; color:#1E293B; text-align:center; padding:5px;">{actividad}</div>')
                xml.append(f'        <mxCell id="{cell_id}" value="{dec_val}" style="rhombus;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;" vertex="1" parent="1">')
                xml.append(f'          <mxGeometry x="{x_node - 65}" y="{y_node - 32}" width="130" height="64" as="geometry"/>')
                xml.append('        </mxCell>')
            else:
                # Actividad (Caja dividida de Farmacia Enterprise SGC)
                desc_lower = desc.lower()
                act_lower = actividad.lower()
                
                # Determinar mecanismo
                if "sistema" in desc_lower or "odoo" in desc_lower or "erp" in desc_lower or "[sistema]" in act_lower:
                    mech = "Sistema"
                    bg_bot = "#FFEADB" # Peach
                    fg_bot = "#F85000" # Orange
                    weight_bot = "900"
                elif "sistema/manual" in desc_lower or "mixto" in desc_lower or "[sistema/manual]" in act_lower:
                    mech = "Sistema/Manual"
                    bg_bot = "#F1F5F9"
                    fg_bot = "#475569"
                    weight_bot = "700"
                else:
                    mech = "Manual"
                    bg_bot = "#FFFFFF"
                    fg_bot = "#64748B"
                    weight_bot = "700"
                
                # HTML premium para el interior de la caja de actividad
                act_clean = DrawIOGenerator.sanitize_text_for_html(actividad)
                box_html = f"""<div style="font-family:'Outfit', sans-serif; height:100%; display:flex; flex-direction:column; justify-content:space-between; margin:0; padding:0;">
                  <div style="padding:6px; font-weight:600; font-size:9.5px; color:#1E293B; text-align:center; height:38px; display:flex; align-items:center; justify-content:center;">
                    {act_clean}
                  </div>
                  <div style="border-top:1.5px solid #000000; background-color:{bg_bot}; color:{fg_bot}; font-weight:{weight_bot}; font-size:8px; text-align:center; padding:3px; letter-spacing:0.5px; text-transform:uppercase;">
                    {mech}
                  </div>
                </div>"""
                box_val = DrawIOGenerator.escape_xml(box_html)
                
                xml.append(f'        <mxCell id="{cell_id}" value="{box_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#FFFFFF;strokeColor=#000000;strokeWidth=1.5;arcSize=8;overflow=hidden;" vertex="1" parent="1">')
                xml.append(f'          <mxGeometry x="{x_node - 95}" y="{y_node - 33}" width="190" height="66" as="geometry"/>')
                xml.append('        </mxCell>')
                
            node_cell_ids[paso_num] = cell_id
            cell_id += 1

        # Nodo Fin
        x_fin = x_node
        y_fin = y_node + y_spacing
        fin_val = DrawIOGenerator.escape_xml('<div style="font-family:\'Outfit\'; font-size:11px; font-weight:800; color:#1E293B; text-align:center;">Fin</div>')
        xml.append(f'        <mxCell id="{cell_id}" value="{fin_val}" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#E9ECEF;strokeColor=#94A3B8;strokeWidth=1.5;arcSize=50;" vertex="1" parent="1">')
        xml.append(f'          <mxGeometry x="{x_fin - 50}" y="{y_fin - 18}" width="100" height="36" as="geometry"/>')
        xml.append('        </mxCell>')
        node_cell_ids["Fin"] = cell_id
        cell_id += 1

        # ==========================================
        # 4. CONEXIONES Y FLECHAS DE FLUJO
        # ==========================================
        # Conectar Inicio a Paso 1
        xml.append(f'        <mxCell id="{cell_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="{node_cell_ids["Inicio"]}" target="{node_cell_ids[1]}">')
        xml.append('          <mxGeometry relative="1" as="geometry"/>')
        xml.append('        </mxCell>')
        cell_id += 1

        # Conectar secuencialmente los pasos
        for idx in range(1, num_steps):
            p1 = doc.pasos[idx - 1]
            p2 = doc.pasos[idx]
            
            src_id = node_cell_ids[p1.numero]
            tgt_id = node_cell_ids[p2.numero]
            
            is_decision = p1.actividad.strip().endswith("?") or "¿" in p1.actividad
            
            if is_decision:
                # Flecha del "SÍ" (al paso siguiente)
                xml.append(f'        <mxCell id="{cell_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="{src_id}" target="{tgt_id}">')
                xml.append('          <mxGeometry relative="1" as="geometry"/>')
                xml.append('        </mxCell>')
                
                # Etiqueta "SÍ" asociada a esta flecha
                label_id = cell_id
                cell_id += 1
                
                si_label = DrawIOGenerator.escape_xml('<div style="font-family:\'Outfit\'; font-size:9px; font-weight:800; color:#22C55E; background-color:#FAF9F6; padding:2px;">SÍ</div>')
                xml.append(f'        <mxCell id="{cell_id}" value="{si_label}" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" vertex="1" connectable="0" parent="{label_id}">')
                xml.append('          <mxGeometry x="-0.3" relative="1" as="geometry">')
                xml.append('            <mxPoint as="offset"/>')
                xml.append('          </mxGeometry>')
                xml.append('        </mxCell>')
                cell_id += 1
                
                # Flecha del "NO" (al paso anterior de feedback)
                target_p_num = max(1, p1.numero - 1)
                fb_tgt_id = node_cell_ids[target_p_num]
                
                xml.append(f'        <mxCell id="{cell_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#EF4444;strokeWidth=1.5;strokeDasharray=3 3;endArrow=block;endFill=1;entryX=0;entryY=0.5;" edge="1" parent="1" source="{src_id}" target="{fb_tgt_id}">')
                xml.append('          <mxGeometry relative="1" as="geometry"/>')
                xml.append('        </mxCell>')
                
                # Etiqueta "NO" asociada a esta flecha
                label_no_id = cell_id
                cell_id += 1
                
                no_label = DrawIOGenerator.escape_xml('<div style="font-family:\'Outfit\'; font-size:9px; font-weight:800; color:#EF4444; background-color:#FAF9F6; padding:2px;">NO</div>')
                xml.append(f'        <mxCell id="{cell_id}" value="{no_label}" style="edgeLabel;html=1;align=center;verticalAlign=middle;resizable=0;points=[];" vertex="1" connectable="0" parent="{label_no_id}">')
                xml.append('          <mxGeometry x="-0.4" relative="1" as="geometry">')
                xml.append('            <mxPoint as="offset"/>')
                xml.append('          </mxGeometry>')
                xml.append('        </mxCell>')
                cell_id += 1
            else:
                # Flecha secuencial normal
                xml.append(f'        <mxCell id="{cell_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="{src_id}" target="{tgt_id}">')
                xml.append('          <mxGeometry relative="1" as="geometry"/>')
                xml.append('        </mxCell>')
                cell_id += 1

        # Conectar el último paso a Fin
        xml.append(f'        <mxCell id="{cell_id}" value="" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#475569;strokeWidth=1.5;endArrow=block;endFill=1;" edge="1" parent="1" source="{node_cell_ids[num_steps]}" target="{node_cell_ids["Fin"]}">')
        xml.append('          <mxGeometry relative="1" as="geometry"/>')
        xml.append('        </mxCell>')
        cell_id += 1

        # Cerrar XML
        xml.append('      </root>')
        xml.append('    </mxGraphModel>')
        xml.append('  </diagram>')
        xml.append('</mxfile>')

        xml_content = "\n".join(xml)

        # Guardar local en la carpeta salidas para persistencia
        filepath = os.path.join("salidas", f"{code}_Diagrama_Enterprise SGC.drawio")
        os.makedirs("salidas", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml_content)

        return filepath
