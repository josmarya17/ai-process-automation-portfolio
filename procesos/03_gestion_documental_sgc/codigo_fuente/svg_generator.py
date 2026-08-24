import os
import re
import base64

class SVGGenerator:
    @staticmethod
    def sanitize_text(text: str) -> str:
        """
        Escapa caracteres especiales para evitar errores de sintaxis XML en el SVG final.
        Especialmente traduce operadores matemáticos a palabras comprensibles.
        """
        if not text:
            return ""
        # Traducir operadores matemáticos que rompen el parser de XML/HTML
        text = text.replace("<=", " menor o igual a ").replace(">=", " mayor o igual a ")
        text = text.replace("<", " menor a ").replace(">", " mayor a ")
        text = text.replace("&", " y ")
        # Escapar comillas y apóstrofes por seguridad
        text = text.replace('"', '&quot;').replace("'", "&apos;")
        return text.strip()

    @staticmethod
    def generate_svg(doc, code: str, version: str, date_str: str) -> str:
        """
        Genera un flujograma vectorial en formato SVG nativo, con la paleta de colores
        de Farmacia Enterprise SGC, el cajetín de especificación alineado y columnas de responsabilidades.
        El archivo generado es 100% vectorial, libre de códigos HTML crudos y totalmente
        editable en Figma/FigJam mediante Drag and Drop.
        """
        # Sanitizar entradas principales
        code = SVGGenerator.sanitize_text(code)
        version = SVGGenerator.sanitize_text(version)
        date_str = SVGGenerator.sanitize_text(date_str)
        
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
        
        # 1. Obtener la lista ordenada y única de responsables (roles) para las columnas
        seen = set()
        roles = []
        for p in doc.pasos:
            resp = SVGGenerator.sanitize_text(p.responsable)
            if resp not in seen:
                seen.add(resp)
                roles.append(resp)
                
        # Asegurar al menos una columna
        if not roles:
            roles = ["Responsable"]
            
        num_columns = len(roles)
        column_width = 250
        margin_left = 50
        margin_right = 50
        width = margin_left + (num_columns * column_width) + margin_right
        
        # Calcular el alto dinámico según la cantidad de pasos
        num_steps = len(doc.pasos)
        y_start_steps = 180
        y_spacing = 150
        flowchart_height = (num_steps * y_spacing) + 120
        height = y_start_steps + flowchart_height
        
        # Iniciar la cadena SVG
        svg = []
        svg.append(f'<?xml version="1.0" standalone="no"?>')
        svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" viewBox="0 0 {width} {height}" width="100%" height="{height}" style="background-color: #FAFAFC;">')
        
        # Estilos CSS embebidos para tipografía premium y elementos
        svg.append('  <defs>')
        svg.append('    <style type="text/css">')
        svg.append("      @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900');")
        svg.append('      text {')
        svg.append("        font-family: 'Outfit', sans-serif;")
        svg.append('      }')
        svg.append('    </style>')
        
        # Marcador de punta de flecha para las conexiones
        svg.append('    <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">')
        svg.append('      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#475569"/>')
        svg.append('    </marker>')
        svg.append('  </defs>')
        
        # ==========================================
        # 1. CAJETÍN (ENCABEZADO DE PROCESO)
        # ==========================================
        # Fondo y bordes del Cajetín
        svg.append(f'  <!-- Cajetin -->')
        svg.append(f'  <rect x="0" y="0" width="{width}" height="100" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5"/>')
        
        # Logotipo Oficial "farmacia Enterprise SGC" o imagen embebida
        if logo_base64:
            svg.append(f'  <image href="data:image/jpeg;base64,{logo_base64}" x="25" y="15" width="210" height="70"/>')
        else:
            svg.append(f'  <text x="30" y="58" font-size="30" font-weight="900" fill="#F85000" letter-spacing="-1.5">farmacia<tspan fill="#475569">Enterprise SGC</tspan></text>')
        
        # Línea divisoria
        svg.append(f'  <line x1="260" y1="20" x2="260" y2="80" stroke="#CBD5E1" stroke-width="1.5"/>')
        
        # Título del Procedimiento (truncado si es muy largo)
        title_display = SVGGenerator.sanitize_text(doc.titulo)
        if len(title_display) > 60:
            title_display = title_display[:57] + "..."
        svg.append(f'  <text x="290" y="56" font-size="16" font-weight="700" fill="#1E293B">{title_display}</text>')
        
        # Tabla de Especificaciones a la derecha
        t_x = width - 340
        svg.append(f'  <g transform="translate({t_x}, 15)">')
        svg.append(f'    <rect x="0" y="0" width="290" height="70" fill="#F8FAFC" stroke="#CBD5E1" stroke-width="1.5" rx="6"/>')
        svg.append(f'    <line x1="100" y1="0" x2="100" y2="70" stroke="#CBD5E1" stroke-width="1.5"/>')
        svg.append(f'    <line x1="0" y1="23" x2="290" y2="23" stroke="#CBD5E1" stroke-width="1.5"/>')
        svg.append(f'    <line x1="0" y1="46" x2="290" y2="46" stroke="#CBD5E1" stroke-width="1.5"/>')
        
        # Columnas de etiquetas
        svg.append(f'    <text x="10" y="16" font-size="10" font-weight="700" fill="#475569">Código</text>')
        svg.append(f'    <text x="110" y="16" font-size="11" font-weight="800" fill="#1E293B" letter-spacing="0.5">{code}</text>')
        
        svg.append(f'    <text x="10" y="39" font-size="10" font-weight="700" fill="#475569">Versión</text>')
        svg.append(f'    <text x="110" y="39" font-size="11" font-weight="700" fill="#1E293B">{version}</text>')
        
        svg.append(f'    <text x="10" y="62" font-size="10" font-weight="700" fill="#475569">Fecha</text>')
        svg.append(f'    <text x="110" y="62" font-size="11" font-weight="500" fill="#1E293B">{date_str}</text>')
        svg.append(f'  </g>')
        
        # ==========================================
        # 2. CARRILES / SWIMLANES (ROLES)
        # ==========================================
        svg.append(f'  <!-- Carriles -->')
        for j, role in enumerate(roles):
            x_start = margin_left + (j * column_width)
            
            # Fondo del carril
            svg.append(f'  <rect x="{x_start}" y="100" width="{column_width}" height="{flowchart_height}" fill="#FAF9F6" stroke="#E2E8F0" stroke-width="1"/>')
            
            # Línea discontinua naranja estilo Figma
            svg.append(f'  <line x1="{x_start}" y1="100" x2="{x_start}" y2="{100 + flowchart_height}" stroke="#F85000" stroke-width="1.2" stroke-dasharray="5 5"/>')
            if j == num_columns - 1:
                # Línea derecha de cierre del último carril
                svg.append(f'  <line x1="{x_start + column_width}" y1="100" x2="{x_start + column_width}" y2="{100 + flowchart_height}" stroke="#F85000" stroke-width="1.2" stroke-dasharray="5 5"/>')
            
            # Cabecera sólida naranja del Rol
            svg.append(f'  <rect x="{x_start + 6}" y="110" width="{column_width - 12}" height="36" fill="#F85000" rx="6"/>')
            svg.append(f'  <text x="{x_start + column_width/2}" y="132" font-size="11" font-weight="800" fill="#FFFFFF" text-anchor="middle">{role.upper()}</text>')
            
        # ==========================================
        # 3. NODOS Y PASOS DEL FLUJO
        # ==========================================
        svg.append(f'  <!-- Nodos -->')
        node_coords = {} # Guardar (x, y) de cada nodo
        
        # Añadir Nodo Inicio
        first_role = roles[0]
        x_init = margin_left + (column_width / 2)
        y_init = y_start_steps
        node_coords["Inicio"] = (x_init, y_init)
        
        # Dibujar Inicio
        svg.append(f'  <!-- Nodo Inicio -->')
        svg.append(f'  <rect x="{x_init - 50}" y="{y_init - 18}" width="100" height="36" rx="18" fill="#E9ECEF" stroke="#94A3B8" stroke-width="1.5"/>')
        svg.append(f'  <text x="{x_init}" y="{y_init + 5}" font-size="11" font-weight="800" fill="#1E293B" text-anchor="middle">Inicio</text>')
        
        # Posicionar y dibujar cada paso
        for idx, paso in enumerate(doc.pasos):
            paso_num = paso.numero
            actividad = SVGGenerator.sanitize_text(paso.actividad)
            responsable = SVGGenerator.sanitize_text(paso.responsable)
            desc = SVGGenerator.sanitize_text(paso.descripcion)
            
            # Buscar columna de este responsable
            try:
                col_idx = roles.index(responsable)
            except ValueError:
                col_idx = 0
                
            x_node = margin_left + (col_idx * column_width) + (column_width / 2)
            y_node = y_start_steps + ((idx + 1) * y_spacing)
            node_coords[paso_num] = (x_node, y_node)
            
            # Determinar si es una decisión (si la actividad termina en "?" o contiene "Si " o "No")
            is_decision = actividad.strip().endswith("?") or "¿" in actividad or "si " in actividad.lower()
            
            svg.append(f'  <!-- Paso {paso_num} -->')
            if is_decision:
                # Dibujar Rombo de Decisión
                svg.append(f'  <polygon points="{x_node},{y_node - 32} {x_node + 65},{y_node} {x_node},{y_node + 32} {x_node - 65},{y_node}" fill="#FFFFFF" stroke="#000000" stroke-width="1.5"/>')
                
                # Ajustar texto dentro del rombo
                words = actividad.split()
                lines = []
                curr = ""
                for w in words:
                    if len(curr + " " + w) < 18:
                        curr = (curr + " " + w).strip()
                    else:
                        lines.append(curr)
                        curr = w
                if curr:
                    lines.append(curr)
                    
                # Centrado del texto vertical
                start_y = y_node - (len(lines) - 1) * 6
                for l_idx, line in enumerate(lines[:3]): # max 3 lineas
                    svg.append(f'  <text x="{x_node}" y="{start_y + l_idx * 13 + 3}" font-size="9" font-weight="700" fill="#1E293B" text-anchor="middle">{line}</text>')
            else:
                # Dibujar Rectángulo con división de Farmacia Enterprise SGC (caja split)
                box_w = 190
                box_h = 66
                top_h = 44
                bot_h = 22
                
                # Determinar mecanismo
                desc_lower = desc.lower()
                act_lower = actividad.lower()
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
                
                # Rectángulo exterior
                x_box = x_node - (box_w / 2)
                y_box = y_node - (box_h / 2)
                svg.append(f'  <rect x="{x_box}" y="{y_box}" width="{box_w}" height="{box_h}" rx="6" fill="#FFFFFF" stroke="#000000" stroke-width="1.5"/>')
                
                # Línea separadora
                svg.append(f'  <line x1="{x_box}" y1="{y_box + top_h}" x2="{x_box + box_w}" y2="{y_box + top_h}" stroke="#000000" stroke-width="1.5"/>')
                
                # Relleno inferior del mecanismo
                svg.append(f'  <path d="M {x_box} {y_box + top_h} l 0 {bot_h - 6} a 6 6 0 0 0 6 6 l {box_w - 12} 0 a 6 6 0 0 0 6 -6 l 0 {-bot_h + 6} Z" fill="{bg_bot}"/>')
                
                # Texto de la Actividad (con ajuste de líneas)
                words = actividad.split()
                lines = []
                curr = ""
                for w in words:
                    if len(curr + " " + w) < 26:
                        curr = (curr + " " + w).strip()
                    else:
                        lines.append(curr)
                        curr = w
                if curr:
                    lines.append(curr)
                
                # Centrado del texto de actividad
                start_y = y_node - (box_h / 2) + (top_h / 2) - ((len(lines) - 1) * 6) + 4
                for l_idx, line in enumerate(lines[:3]):
                    svg.append(f'  <text x="{x_node}" y="{start_y + l_idx * 13}" font-size="9" font-weight="600" fill="#1E293B" text-anchor="middle">{line}</text>')
                
                # Texto del Mecanismo (abajo)
                svg.append(f'  <text x="{x_node}" y="{y_node + box_h/2 - 7}" font-size="8.5" font-weight="{weight_bot}" fill="{fg_bot}" text-anchor="middle" letter-spacing="0.5">{mech.upper()}</text>')
                
        # Añadir Nodo Fin
        x_fin = x_node
        y_fin = y_node + y_spacing
        node_coords["Fin"] = (x_fin, y_fin)
        
        svg.append(f'  <!-- Nodo Fin -->')
        svg.append(f'  <rect x="{x_fin - 50}" y="{y_fin - 18}" width="100" height="36" rx="18" fill="#E9ECEF" stroke="#94A3B8" stroke-width="1.5"/>')
        svg.append(f'  <text x="{x_fin}" y="{y_fin + 5}" font-size="11" font-weight="800" fill="#1E293B" text-anchor="middle">Fin</text>')
        
        # ==========================================
        # 4. CONEXIONES Y FLECHAS DE FLUJO
        # ==========================================
        svg.append(f'  <!-- Conexiones -->')
        
        # Conectar Inicio al Paso 1
        x1, y1 = node_coords["Inicio"]
        x2, y2 = node_coords[1]
        svg.append(f'  <line x1="{x1}" y1="{y1 + 18}" x2="{x2}" y2="{y2 - 33}" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>')
        
        # Conectar secuencialmente los pasos
        for idx in range(1, num_steps):
            p1 = doc.pasos[idx - 1]
            p2 = doc.pasos[idx]
            
            x1, y1 = node_coords[p1.numero]
            x2, y2 = node_coords[p2.numero]
            
            # Verificar si el nodo de origen es una decisión
            is_decision = p1.actividad.strip().endswith("?") or "¿" in p1.actividad
            
            if is_decision:
                # Para compuerta de decisión, la flecha hacia el paso siguiente de la lista
                # es la rama del "Sí" (o el flujo principal)
                # Dibujar etiqueta de "SÍ"
                label_x = x1 + 15 if x1 == x2 else (x1 + x2) / 2
                label_y = y1 + 25 if x1 == x2 else y1 - 8
                svg.append(f'  <text x="{label_x}" y="{label_y}" font-size="9" font-weight="800" fill="#22C55E">SÍ</text>')
                
                # Comprobar si hay salto de carril para hacer una línea ortogonal
                if x1 != x2:
                    svg.append(f'  <path d="M {x1 + 65} {y1} L {x2} {y1} L {x2} {y2 - 33}" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>')
                else:
                    svg.append(f'  <line x1="{x1}" y1="{y1 + 32}" x2="{x2}" y2="{y2 - 33}" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>')
                    
                # Buscar si hay una rama de "NO" que retroceda a un paso anterior
                # Haremos un bucle de feedback ortogonal muy estético
                # Por simplicidad, si la decisión es el paso i, y hay un paso que represente recalcular,
                # dibujamos una flecha de retorno "NO" hacia el paso anterior
                target_p_num = max(1, p1.numero - 1)
                x_target, y_target = node_coords[target_p_num]
                
                # Dibujar camino del "NO" por la izquierda y hacia arriba
                svg.append(f'  <path d="M {x1 - 65} {y1} L {x1 - 110} {y1} L {x1 - 110} {y_target} L {x_target - 95} {y_target}" fill="none" stroke="#EF4444" stroke-width="1.5" stroke-dasharray="3 3" marker-end="url(#arrow)"/>')
                svg.append(f'  <text x="{x1 - 95}" y="{y1 - 8}" font-size="9" font-weight="800" fill="#EF4444">NO</text>')
            else:
                # Conexión estándar entre actividades secuenciales
                if x1 != x2:
                    # Línea ortogonal de salto de carril (Visio style)
                    svg.append(f'  <path d="M {x1} {y1 + 33} L {x1} {y1 + 55} L {x2} {y1 + 55} L {x2} {y2 - 33}" fill="none" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>')
                else:
                    svg.append(f'  <line x1="{x1}" y1="{y1 + 33}" x2="{x2}" y2="{y2 - 33}" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>')
                    
        # Conectar el último paso a Fin
        x1, y1 = node_coords[num_steps]
        x2, y2 = node_coords["Fin"]
        svg.append(f'  <line x1="{x1}" y1="{y1 + 33}" x2="{x2}" y2="{y2 - 18}" stroke="#475569" stroke-width="1.5" marker-end="url(#arrow)"/>')
        
        # Cerrar el SVG
        svg.append('</svg>')
        
        # Combinar todo
        svg_content = "\n".join(svg)
        
        # Guardar en local en la carpeta salidas para persistencia
        filepath = os.path.join("salidas", f"{code}_Diagrama_Enterprise SGC.svg")
        os.makedirs("salidas", exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(svg_content)
            
        return filepath
