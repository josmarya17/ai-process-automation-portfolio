import os
import json

def main():
    base_dir = r"c:\Users\Sist-JPinto\Desktop\Sistema de Gestion Documental"
    target_dir = os.path.join(base_dir, "organigrama")
    os.makedirs(target_dir, exist_ok=True)

    # 1. Define Empresa Demo Nodes in Enterprise SGC's Exact Methodology with Legend Colors
    # Colors:
    # Strategic: #8B5CF6 (Purple) -> bg_color: #8B5CF6, text_color: #FFFFFF
    # Tactical: #3B82F6 (Blue) -> bg_color: #3B82F6, text_color: #FFFFFF
    # Definition: #0EA5E9 (Sky Blue) -> bg_color: #0EA5E9, text_color: #FFFFFF
    #   Reports: bg_color: #FFFFFF, border_left_color: #0EA5E9, text_color: #0F172A, area_color: #0EA5E9
    # Functional: #FBBF24 (Yellow/Orange) -> bg_color: #FBBF24, text_color: #FFFFFF
    #   Reports: bg_color: #FFFFFF, border_left_color: #F59E0B, text_color: #0F172A, area_color: #F59E0B
    # Control & Quality: #10B981 (Green) -> bg_color: #10B981, text_color: #FFFFFF
    #   Reports: bg_color: #FFFFFF, border_left_color: #10B981, text_color: #0F172A, area_color: #10B981
    # Secondary: border: 2px dashed #94A3B8, bg_color: #FFFFFF
    
    nodes_raw = [
        # --- STRATEGIC (PURPLE FILL) ---
        {
            "id": "u0",
            "parent": None,
            "name": "Mikel Aizpurua",
            "role": "Sponsor",
            "area": "Dirección",
            "bg_color": "#8B5CF6",
            "border_left_color": "#7C3AED",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u1",
            "parent": "u0",
            "name": "José Contreras",
            "role": "Sponsor Técnico",
            "area": "Dirección de TI",
            "bg_color": "#8B5CF6",
            "border_left_color": "#7C3AED",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        
        # --- TACTICAL (BLUE FILL) ---
        {
            "id": "u2",
            "parent": "u1",
            "name": "Estefany Goncalves",
            "role": "Gerente de Proyecto",
            "area": "Gestión del Proyecto",
            "bg_color": "#3B82F6",
            "border_left_color": "#2563EB",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u3",
            "parent": "u2",
            "name": "Andrea Peña",
            "role": "Project Manager (PM)",
            "area": "Gestión del Proyecto",
            "bg_color": "#3B82F6",
            "border_left_color": "#2563EB",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        
        # --- OPERATIONAL / DEFINITION (SKY BLUE FILL) ---
        {
            "id": "u4",
            "parent": "u3",
            "name": "Franyelys Caraballo",
            "role": "Líder de Procesos",
            "area": "Definición y Procesos",
            "bg_color": "#0EA5E9",
            "border_left_color": "#0284C7",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF",
            "combined_with": "u5"
        },
        {
            "id": "u5",
            "parent": "u3",
            "name": "Andreina Cuicas",
            "role": "Líder de Procesos",
            "area": "Definición y Procesos",
            "bg_color": "#0EA5E9",
            "border_left_color": "#0284C7",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u6",
            "parent": "u3",
            "name": "Renier Ferrer",
            "role": "Consultor Odoo Líder",
            "area": "Odoo Consultoría",
            "bg_color": "#0EA5E9",
            "border_left_color": "#0284C7",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u7",
            "parent": "u3",
            "name": "Enkys Perez",
            "role": "Líder de Demanda",
            "area": "Demanda",
            "bg_color": "#0EA5E9",
            "border_left_color": "#0284C7",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        
        # --- DEFINITION REPORTS (WHITE CARD, SKY BLUE BORDER) ---
        {
            "id": "u14",
            "parent": "u4",
            "name": "Diana Soto",
            "role": "Consultor de Procesos de Negocio",
            "area": "Definición y Procesos",
            "bg_color": "#FFFFFF",
            "border_left_color": "#0EA5E9",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#0EA5E9"
        },
        {
            "id": "u15",
            "parent": "u7",
            "name": "Sarahí Chirinos",
            "role": "Analista Funcional",
            "area": "Demanda",
            "bg_color": "#FFFFFF",
            "border_left_color": "#0EA5E9",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#0EA5E9"
        },
        {
            "id": "u37",
            "parent": "u6",
            "name": "Jose Acosta",
            "role": "Consultor Odoo Funcional",
            "area": "Odoo Consultoría",
            "bg_color": "#FFFFFF",
            "border_left_color": "#0EA5E9",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#0EA5E9"
        },
        {
            "id": "u38",
            "parent": "u6",
            "name": "Oswaldo Gimenez",
            "role": "Consultor Odoo Funcional",
            "area": "Odoo Consultoría",
            "bg_color": "#FFFFFF",
            "border_left_color": "#0EA5E9",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#0EA5E9"
        },

        # --- OPERATIONAL / FUNCIONAL (YELLOW / ORANGE FILL) ---
        {
            "id": "u16",
            "parent": "u4",
            "name": "Marilyn Rivas",
            "role": "Líder de Contabilidad",
            "area": "Finanzas y Administración",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u17",
            "parent": "u4",
            "name": "Marielangel Rivero",
            "role": "Líder de Tributos",
            "area": "Finanzas y Administración",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u18",
            "parent": "u4",
            "name": "Karen Torres",
            "role": "Líder de Planifi. Financiera",
            "area": "Finanzas y Administración",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u19",
            "parent": "u4",
            "name": "Paola Gil",
            "role": "Líder de Tesorería",
            "area": "Finanzas y Administración",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u20",
            "parent": "u4",
            "name": "Francelys Pernalete",
            "role": "Líder de Pagos",
            "area": "Finanzas y Administración",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u21",
            "parent": "u4",
            "name": "Elvira Sanchez",
            "role": "Líder de Cobranza",
            "area": "Finanzas y Administración",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u22",
            "parent": "u4",
            "name": "Carmen Sánchez",
            "role": "Líder de Administración",
            "area": "Finanzas y Administración",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u22_sub",
            "parent": "u22",
            "name": "Karemlyg Marin",
            "role": "Administración",
            "area": "Finanzas y Administración",
            "bg_color": "#FFFFFF",
            "border_left_color": "#F59E0B",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#F59E0B"
        },
        {
            "id": "u29",
            "parent": "u4",
            "name": "Irielys Salom",
            "role": "Líder de Compras y Suministros",
            "area": "Cadena de Suministros y Compras",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u23",
            "parent": "u4",
            "name": "Olmary Freitez",
            "role": "Líder de Mercadeo",
            "area": "Mercadeo",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u31",
            "parent": "u4",
            "name": "Miguel Gomez",
            "role": "Líder de Mtto. e Infraestructura",
            "area": "Mantenimiento e Infraestructura",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u36_aud",
            "parent": "u4",
            "name": "Francia González",
            "role": "Auditoría Interna",
            "area": "Auditoría",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u36_aud_sub",
            "parent": "u36_aud",
            "name": "Claudia Rangel",
            "role": "Auditoría Interna",
            "area": "Auditoría",
            "bg_color": "#FFFFFF",
            "border_left_color": "#F59E0B",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#F59E0B"
        },
        {
            "id": "u32_bien",
            "parent": "u4",
            "name": "Carla Sanchez",
            "role": "Líder de Bienestar y Reclutamiento",
            "area": "Gestión Humana",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u32_bien_sub1",
            "parent": "u32_bien",
            "name": "Jesus Suarez",
            "role": "Bienestar",
            "area": "Gestión Humana",
            "bg_color": "#FFFFFF",
            "border_left_color": "#F59E0B",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#F59E0B"
        },
        {
            "id": "u32_bien_sub2",
            "parent": "u32_bien",
            "name": "Skarling Silva",
            "role": "Reclutamiento",
            "area": "Gestión Humana",
            "bg_color": "#FFFFFF",
            "border_left_color": "#F59E0B",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#F59E0B"
        },
        {
            "id": "u34",
            "parent": "u4",
            "name": "Marlene López",
            "role": "Líder de Nómina",
            "area": "Nómina",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u35",
            "parent": "u4",
            "name": "Gloriannys Vargas",
            "role": "Líder de SSL",
            "area": "Seguridad y Salud Laboral",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u36_dist",
            "parent": "u4",
            "name": "Luis Hernandez",
            "role": "Líder de Distribución",
            "area": "Distribución",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u36_dist_sub",
            "parent": "u36_dist",
            "name": "Reinaldo Flores",
            "role": "Distribución",
            "area": "Distribución",
            "bg_color": "#FFFFFF",
            "border_left_color": "#F59E0B",
            "text_color": "#0F172A",
            "role_color": "#64748B",
            "area_color": "#F59E0B"
        },
        {
            "id": "u28",
            "parent": "u4",
            "name": "Johnny Soto",
            "role": "Seguridad Física",
            "area": "Seguridad Física",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u24_cal",
            "parent": "u4",
            "name": "Aida Pineda",
            "role": "Líder de Calidad y Servicio",
            "area": "Calidad y Servicio",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u30_comp",
            "parent": "u4",
            "name": "Franklin Materano",
            "role": "Líder de Compras",
            "area": "Compras",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u25_flot",
            "parent": "u4",
            "name": "Luis Vielma",
            "role": "Líder de Flota",
            "area": "Operaciones y Distribución",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u26_reg",
            "parent": "u4",
            "name": "Jhilmer Betancourt",
            "role": "Líder de Regencia",
            "area": "Regencia",
            "bg_color": "#FBBF24",
            "border_left_color": "#F59E0B",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },

        # --- CONTROL & QUALITY (GREEN FILL) ---
        {
            "id": "u8",
            "parent": "u3",
            "name": "Anaís Chávez",
            "role": "Líder de Desarrollo",
            "area": "Desarrollo y TI",
            "bg_color": "#10B981",
            "border_left_color": "#059669",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u9",
            "parent": "u3",
            "name": "Ángel Manzano",
            "role": "Líder de Data Hub",
            "area": "Datos y TI",
            "bg_color": "#10B981",
            "border_left_color": "#059669",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u10",
            "parent": "u3",
            "name": "Franyelys Caraballo",
            "role": "Líder de QA",
            "area": "QA y TI",
            "bg_color": "#10B981",
            "border_left_color": "#059669",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF",
            "combined_with": "u11"
        },
        {
            "id": "u11",
            "parent": "u3",
            "name": "Arianna Colmenarez",
            "role": "Líder de QA",
            "area": "QA y TI",
            "bg_color": "#10B981",
            "border_left_color": "#059669",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u12",
            "parent": "u3",
            "name": "Nelson Gimenez",
            "role": "Líder de Soporte",
            "area": "Soporte y TI",
            "bg_color": "#10B981",
            "border_left_color": "#059669",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        {
            "id": "u13",
            "parent": "u3",
            "name": "Junnes Hemming",
            "role": "Líder de Arquitectura",
            "area": "Infraestructura y TI",
            "bg_color": "#10B981",
            "border_left_color": "#059669",
            "text_color": "#FFFFFF",
            "role_color": "#FFFFFF",
            "area_color": "#FFFFFF"
        },
        
        # --- CONTROL & QUALITY REPORTS (WHITE CARD, GREEN BORDER) ---
        {
            "id": "u8_devs_primary",
            "parent": "u8",
            "names": ["Yenny Colmenarez", "Johan Alvarado", "Roberto Torres"],
            "role": "Desarrollador",
            "area": "Desarrollo y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "is_multiple_names": True
        },
        {
            "id": "u8_devs_secondary",
            "parent": "u8",
            "names": ["Renier Ferrer", "Jose Acosta", "Jose Alvarez"],
            "role": "Desarrollador (Secundario)",
            "area": "Desarrollo y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#94A3B8",
            "text_color": "#475569",
            "role_color": "#94A3B8",
            "is_multiple_names": True,
            "is_secondary": True
        },
        {
            "id": "u9_data_primary",
            "parent": "u9",
            "name": "Douglas Torrealba",
            "role": "Ingeniero de Datos",
            "area": "Datos y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "area_color": "#10B981"
        },
        {
            "id": "u9_data_secondary",
            "parent": "u9",
            "name": "José Alvarez",
            "role": "Ingeniero de Datos (Secundario)",
            "area": "Datos y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#94A3B8",
            "text_color": "#475569",
            "role_color": "#94A3B8",
            "is_secondary": True,
            "area_color": "#94A3B8"
        },
        {
            "id": "u10_qa_primary",
            "parent": "u10",
            "names": ["Joselyn Aponte", "Franklin Camacho"],
            "role": "QA Funcional",
            "area": "QA y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "is_multiple_names": True
        },
        {
            "id": "u10_qa_secondary",
            "parent": "u10",
            "names": ["Darli Espinoza", "Karen Amaro"],
            "role": "QA Funcional (Secundario)",
            "area": "QA y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#94A3B8",
            "text_color": "#475569",
            "role_color": "#94A3B8",
            "is_multiple_names": True,
            "is_secondary": True
        },
        {
            "id": "u10_qa_auto",
            "parent": "u10",
            "name": "Juan Carlos Pacheco",
            "role": "Automatización y Rendimiento",
            "area": "QA y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "area_color": "#10B981"
        },
        {
            "id": "u12_sop_sub",
            "parent": "u12",
            "name": "Keiber Araujo",
            "role": "Especialista de Soporte",
            "area": "Soporte y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "area_color": "#10B981"
        },
        {
            "id": "u13_arch_sub1",
            "parent": "u13",
            "name": "Aldo Garcia",
            "role": "Gerente Servicios Tecnológicos (Cloud)",
            "area": "Infraestructura y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "area_color": "#10B981"
        },
        {
            "id": "u13_arch_sub2",
            "parent": "u13",
            "name": "Aldo Garcia",
            "role": "Ingeniero de Infraestructura Cloud",
            "area": "Infraestructura y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "area_color": "#10B981"
        },
        {
            "id": "u13_arch_sub3",
            "parent": "u13",
            "name": "Jesús Ramírez",
            "role": "Ingeniero DevOps",
            "area": "Infraestructura y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "area_color": "#10B981"
        },
        {
            "id": "u13_arch_sub4",
            "parent": "u13",
            "name": "Daniel Rodríguez",
            "role": "Gerente de Aplicaciones",
            "area": "Infraestructura y TI",
            "bg_color": "#FFFFFF",
            "border_left_color": "#10B981",
            "text_color": "#0F172A",
            "role_color": "#10B981",
            "area_color": "#10B981"
        }
    ]

    # Reconstruct parent-child mapping
    node_map = {}
    combined_pairs = {}
    
    for n in nodes_raw:
        node_map[n["id"]] = n
        if "combined_with" in n:
            combined_pairs[n["combined_with"]] = n["id"]

    for n in nodes_raw:
        n["children"] = []

    root_nodes = []
    for n in nodes_raw:
        pid = n.get("parent")
        if n["id"] in combined_pairs:
            continue
            
        if pid:
            if pid in combined_pairs:
                pid = combined_pairs[pid];
            if pid in node_map:
                node_map[pid]["children"].append(n)
        else:
            root_nodes.append(n)

    # Render Card HTML function
    def render_card_html(n):
        border_style = "border: 2px dashed #94A3B8; border-left: 4px dashed #94A3B8 !important;" if n.get("is_secondary") else f"border-left-color: {n.get('border_left_color')};"
        bg_style = f"background-color: {n.get('bg_color')};"
        
        name_color = n.get("text_color", "#0F172A")
        role_color = n.get("role_color", "#64748B")
        area_color = n.get("area_color", "#94A3B8")
        
        # Opacity variables matching Enterprise SGC
        role_opacity = "0.8" if n.get("text_color") == "#FFFFFF" else "1.0"
        area_opacity = "0.9" if n.get("text_color") == "#FFFFFF" else "1.0"
        
        if n.get("is_multiple_names"):
            names_html = []
            for i, name in enumerate(n["names"]):
                sub_style = ' style="margin-top: 4px; border-top: 1px solid #F1F5F9; padding-top: 4px;"' if i > 0 else ''
                names_html.append(f'<div class="card-name"{sub_style}>{name}</div>')
            names_str = "\n".join(names_html)
            
            return f"""<div class="card" id="card-{n["id"]}" style="{bg_style} {border_style}">
            <div class="card-body">
                {names_str}
                <div class="card-role" style="color: {role_color}; opacity: {role_opacity}; margin-top: 6px;">{n["role"]}</div>
            </div>
        </div>"""
        else:
            # Check if there is an area string to render
            area_html = ""
            if n.get("area"):
                area_html = f'<div class="card-area" style="color: {area_color}; opacity: {area_opacity};">{n["area"]}</div>'
                
            return f"""<div class="card" id="card-{n["id"]}" style="{bg_style} {border_style}">
            <div class="card-body">
                <div class="card-name" style="color: {name_color};">{n["name"]}</div>
                <div class="card-role" style="color: {role_color}; opacity: {role_opacity};">{n["role"]}</div>
                {area_html}
            </div>
        </div>"""

    # Render Node recursively
    def render_tree_node(n):
        if "combined_with" in n:
            secondary_node = node_map[n["combined_with"]]
            card1_html = render_card_html(n)
            card2_html = render_card_html(secondary_node)
            
            all_children = n.get("children", [])
            has_children = len(all_children) > 0
            
            toggle_html = '<button class="toggle-btn">−</button>' if has_children else ''
            
            children_rendered = ""
            if has_children:
                child_nodes = "\n".join([render_tree_node(c) for c in all_children])
                children_rendered = f'<div class="children-container">\n{child_nodes}\n</div>'
                
            return f"""<div class="tree-node" id="node-{n["id"]}_{secondary_node["id"]}">
    <div class="combined-node-container" id="combined-{n["id"]}_{secondary_node["id"]}">
        {card1_html}
        {card2_html}
        {toggle_html}
    </div>
    {children_rendered}
</div>"""
        else:
            card_html = render_card_html(n)
            children = n.get("children", [])
            has_children = len(children) > 0
            
            toggle_html = '<button class="toggle-btn">−</button>' if has_children else ''
            
            children_rendered = ""
            if has_children:
                child_nodes = "\n".join([render_tree_node(c) for c in children])
                children_rendered = f'<div class="children-container">\n{child_nodes}\n</div>'
                
            return f"""<div class="tree-node" id="node-{n["id"]}">
    {card_html}
    {toggle_html}
    {children_rendered}
</div>"""

    tree_nodes_html = "\n".join([render_tree_node(r) for r in root_nodes])

    js_nodes = []
    for n in nodes_raw:
        n_copy = n.copy()
        if "children" in n_copy:
            del n_copy["children"]
        if n["id"] in combined_pairs:
            n_copy["parent"] = node_map[combined_pairs[n["id"]]]["parent"]
        js_nodes.append(n_copy)

    nodes_json_str = json.dumps(js_nodes, indent=4, ensure_ascii=False)

    # 2. Base HTML Template
    template_html = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Organigrama de Recursos - Odoo Empresa Demo</title>
    <link rel="stylesheet" href="styles.css">
</head>
<body>

    <!-- Header / Nav -->
    <div class="header">
        <div class="header-title-container">
            <div class="header-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/></svg>
            </div>
            <div class="header-title">
                <h1>Organigrama de Recursos</h1>
                <p>Proyecto Odoo Empresa Demo • Estructura Jerárquica Completa</p>
            </div>
        </div>

        <div class="controls">
            <div class="search-container">
                <svg class="search-icon-svg" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
                <input type="text" class="search-input" id="search-input" placeholder="Buscar recurso, cargo o área...">
            </div>

            <div class="btn-group">
                <button class="btn" id="layout-horiz-btn">Horizontal</button>
                <button class="btn btn-active" id="layout-vert-btn">Vertical</button>
            </div>

            <div class="btn-group">
                <button class="btn" id="zoom-out-btn" title="Alejar">-</button>
                <button class="btn" id="zoom-reset-btn" title="Restablecer Zoom">100%</button>
                <button class="btn" id="zoom-in-btn" title="Acercar">+</button>
            </div>

            <button class="btn" id="collapse-btn">Contraer Todo</button>
            <button class="btn" id="expand-btn">Expandir Todo</button>
            
            <button class="btn btn-primary" id="print-btn">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><path d="M6 9V3a1 1 0 0 1 1-1h10a1 1 0 0 1 1 1v6"/><rect x="6" y="14" width="12" height="8" rx="1"/></svg>
                Imprimir a PDF
            </button>
        </div>
    </div>

    <!-- Workspace -->
    <div class="workspace" id="workspace">
        <div class="tree-container layout-vertical" id="tree-container">
            <svg id="svg-connectors">
                <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                        <path d="M 0 2 L 6 5 L 0 8 z" fill="#000000" vector-effect="non-scaling-stroke" />
                    </marker>
                </defs>
            </svg>
            <div id="tree-root-anchor">
                __TREE_NODES_HTML__
            </div>
        </div>
    </div>

    <script>
        // Inject Nodes Data
        const nodesData = __NODES_JSON_STR__;
        const combinedPairs = {};
        
        nodesData.forEach(n => {
            if (n.combined_with) {
                combinedPairs[n.combined_with] = n.id;
            }
        });

        const nodeMap = {};
        nodesData.forEach(n => {
            n.children = [];
            n.expanded = true;
            nodeMap[n.id] = n;
        });

        nodesData.forEach(n => {
            if (n.id in combinedPairs) return;
            let pid = n.parent;
            if (pid) {
                if (pid in combinedPairs) {
                    pid = combinedPairs[pid];
                }
                if (nodeMap[pid]) {
                    nodeMap[pid].children.push(n);
                }
            }
        });

        const treeContainer = document.getElementById('tree-container');
        const svgConnectors = document.getElementById('svg-connectors');
        const searchInput = document.getElementById('search-input');
        const workspace = document.getElementById('workspace');

        let isVertical = true;
        let zoomScale = 0.85;

        function applyZoom() {
            document.documentElement.style.setProperty('--zoom-scale', zoomScale);
            const reflow = treeContainer.offsetHeight;
            drawConnections();
        }

        function bindToggleListeners() {
            nodesData.forEach(node => {
                if (node.id in combinedPairs) return;
                const hasChildren = node.children && node.children.length > 0;
                if (!hasChildren) return;
                
                let domId = `node-${node.id}`;
                if (node.combined_with) {
                    domId = `node-${node.id}_${node.combined_with}`;
                }
                
                const nodeEl = document.getElementById(domId);
                if (!nodeEl) return;
                
                let toggle;
                if (node.combined_with) {
                    toggle = nodeEl.querySelector(`:scope > .combined-node-container > .toggle-btn`);
                } else {
                    toggle = nodeEl.querySelector(`:scope > .toggle-btn`);
                }
                
                if (toggle) {
                    const newToggle = toggle.cloneNode(true);
                    toggle.parentNode.replaceChild(newToggle, toggle);
                    
                    newToggle.addEventListener('click', (e) => {
                        e.stopPropagation();
                        node.expanded = !node.expanded;
                        newToggle.innerHTML = node.expanded ? '−' : '+';
                        
                        const childContainer = nodeEl.querySelector(`:scope > .children-container`);
                        if (childContainer) {
                            if (node.expanded) {
                                childContainer.classList.remove('collapsed-children');
                            } else {
                                childContainer.classList.add('collapsed-children');
                            }
                        }
                        drawConnections();
                    });
                }
            });
        }

        function initTree() {
            nodesData.forEach(node => {
                if (node.id in combinedPairs) return;
                
                let domId = `node-${node.id}`;
                if (node.combined_with) {
                    domId = `node-${node.id}_${node.combined_with}`;
                }
                
                const nodeEl = document.getElementById(domId);
                if (!nodeEl) return;
                
                const childContainer = nodeEl.querySelector(`:scope > .children-container`);
                let toggle;
                if (node.combined_with) {
                    toggle = nodeEl.querySelector(`:scope > .combined-node-container > .toggle-btn`);
                } else {
                    toggle = nodeEl.querySelector(`:scope > .toggle-btn`);
                }
                
                if (childContainer) {
                    if (node.expanded) {
                        childContainer.classList.remove('collapsed-children');
                    } else {
                        childContainer.classList.add('collapsed-children');
                    }
                }
                if (toggle) {
                    toggle.innerHTML = node.expanded ? '−' : '+';
                }
            });
            
            bindToggleListeners();
            const reflow = treeContainer.offsetHeight;
            drawConnections();
        }

        function getUnscaledRect(el) {
            let left = 0;
            let top = 0;
            const width = el.offsetWidth;
            const height = el.offsetHeight;
            
            let current = el;
            while (current current !== treeContainer) {
                left += current.offsetLeft;
                top += current.offsetTop;
                
                if (current.offsetParent && current.offsetParent !== treeContainer) {
                    left += current.offsetParent.clientLeft || 0;
                    top += current.offsetParent.clientTop || 0;
                }
                
                current = current.offsetParent;
            }
            
            return { left, top, width, height };
        }

        function drawConnections() {
            const existingPaths = svgConnectors.querySelectorAll(':scope > path');
            existingPaths.forEach(p => p.remove());

            const scrollWidth = treeContainer.scrollWidth;
            const scrollHeight = treeContainer.scrollHeight;
            svgConnectors.setAttribute('width', scrollWidth);
            svgConnectors.setAttribute('height', scrollHeight);
            svgConnectors.setAttribute('viewBox', `0 0 ${scrollWidth} ${scrollHeight}`);

            nodesData.forEach(node => {
                if (node.id in combinedPairs) return;
                if (!node.parent) return;

                let parentId = node.parent;
                if (parentId in combinedPairs) {
                    parentId = combinedPairs[parentId];
                }
                const parentNodeObj = nodeMap[parentId];
                if (!parentNodeObj || !parentNodeObj.expanded) return;

                let parentEl;
                if (parentNodeObj.combined_with) {
                    parentEl = document.getElementById(`combined-${parentNodeObj.id}_${parentNodeObj.combined_with}`);
                } else {
                    parentEl = document.getElementById(`card-${parentNodeObj.id}`);
                }

                let childEl;
                if (node.combined_with) {
                    childEl = document.getElementById(`combined-${node.id}_${node.combined_with}`);
                } else {
                    childEl = document.getElementById(`card-${node.id}`);
                }

                if (!parentEl || !childEl) return;

                const parentRect = getUnscaledRect(parentEl);
                const childRect = getUnscaledRect(childEl);

                let x1, y1, x2, y2;

                if (isVertical) {
                    x1 = parentRect.left + parentRect.width / 2;
                    y1 = parentRect.top + parentRect.height;
                    x2 = childRect.left + childRect.width / 2;
                    y2 = childRect.top;
                } else {
                    x1 = parentRect.left + parentRect.width;
                    y1 = parentRect.top + parentRect.height / 2;
                    x2 = childRect.left;
                    y2 = childRect.top + childRect.height / 2;
                }

                const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                
                let d;
                if (isVertical) {
                    const midY = y1 + (y2 - y1) * 0.5;
                    d = `M ${x1} ${y1} V ${midY} H ${x2} V ${y2}`;
                } else {
                    const midX = x1 + (x2 - x1) * 0.5;
                    d = `M ${x1} ${y1} H ${midX} V ${y2} H ${x2}`;
                }

                path.setAttribute('d', d);
                path.setAttribute('fill', 'none');
                
                let isChildHighlighted = childEl.classList.contains('highlighted');
                let isChildDimmed = childEl.classList.contains('dimmed');

                if (isChildHighlighted) {
                    path.setAttribute('stroke', '#3B82F6');
                    path.setAttribute('stroke-width', '3');
                } else if (isChildDimmed) {
                    path.setAttribute('stroke', '#E2E8F0');
                    path.setAttribute('stroke-width', '1');
                } else {
                    path.setAttribute('stroke', '#000000');
                    path.setAttribute('stroke-width', '3');
                }
                
                path.setAttribute('vector-effect', 'non-scaling-stroke');
                path.setAttribute('marker-end', 'url(#arrow)');
                svgConnectors.appendChild(path);
            });
        }

        document.getElementById('layout-horiz-btn').addEventListener('click', function() {
            if (isVertical) {
                isVertical = false;
                this.classList.add('btn-active');
                document.getElementById('layout-vert-btn').classList.remove('btn-active');
                treeContainer.classList.remove('layout-vertical');
                treeContainer.classList.add('layout-horizontal');
                drawConnections();
            }
        });

        document.getElementById('layout-vert-btn').addEventListener('click', function() {
            if (!isVertical) {
                isVertical = true;
                this.classList.add('btn-active');
                document.getElementById('layout-horiz-btn').classList.remove('btn-active');
                treeContainer.classList.remove('layout-horizontal');
                treeContainer.classList.add('layout-vertical');
                drawConnections();
            }
        });

        document.getElementById('zoom-in-btn').addEventListener('click', () => {
            if (zoomScale < 2.0) {
                zoomScale += 0.075;
                applyZoom();
            }
        });

        document.getElementById('zoom-out-btn').addEventListener('click', () => {
            if (zoomScale > 0.4) {
                zoomScale -= 0.075;
                applyZoom();
            }
        });

        document.getElementById('zoom-reset-btn').addEventListener('click', () => {
            zoomScale = 0.85;
            applyZoom();
        });

        document.getElementById('collapse-btn').addEventListener('click', () => {
            nodesData.forEach(n => {
                if (n.parent) n.expanded = false;
            });
            initTree();
        });

        document.getElementById('expand-btn').addEventListener('click', () => {
            nodesData.forEach(n => {
                n.expanded = true;
            });
            initTree();
        });

        searchInput.addEventListener('input', function(e) {
            const query = e.target.value.toLowerCase().trim();
            const cards = document.querySelectorAll('.card');
            const combinedContainers = document.querySelectorAll('.combined-node-container');

            if (!query) {
                cards.forEach(c => c.classList.remove('dimmed', 'highlighted'));
                combinedContainers.forEach(cc => cc.classList.remove('dimmed', 'highlighted'));
                drawConnections();
                return;
            }

            const matchedIds = new Set();
            
            nodesData.forEach(n => {
                const searchString = n.is_multiple_names 
                    ? n.names.join(' ').toLowerCase() + ' ' + n.role.toLowerCase()
                    : `${n.name} ${n.role} ${n.area}`.toLowerCase();

                if (searchString.includes(query)) {
                    matchedIds.add(n.id);
                    
                    let curr = n;
                    while (curr.parent) {
                        let pid = curr.parent;
                        if (pid in combinedPairs) {
                            pid = combinedPairs[pid];
                        }
                        const parentNodeObj = nodeMap[pid];
                        if (parentNodeObj && !parentNodeObj.expanded) {
                            parentNodeObj.expanded = true;
                        }
                        curr = parentNodeObj;
                    }
                }
            });

            initTree();

            setTimeout(() => {
                const updatedCards = document.querySelectorAll('.card');
                updatedCards.forEach(c => {
                    const id = c.id.replace('card-', '');
                    if (matchedIds.has(id)) {
                        c.classList.add('highlighted');
                        c.classList.remove('dimmed');
                    } else {
                        c.classList.add('dimmed');
                        c.classList.remove('highlighted');
                    }
                });
                
                const updatedCombined = document.querySelectorAll('.combined-node-container');
                updatedCombined.forEach(cc => {
                    const parts = cc.id.replace('combined-', '').split('_');
                    if (parts.some(id => matchedIds.has(id))) {
                        cc.classList.add('highlighted');
                        cc.classList.remove('dimmed');
                    } else {
                        cc.classList.add('dimmed');
                        cc.classList.remove('highlighted');
                    }
                });
                
                drawConnections();
            }, 150);
        });

        let savedZoom = 0.85;
        let savedStates = [];

        window.addEventListener('beforeprint', () => {
            savedZoom = zoomScale;
            savedStates = nodesData.map(n => ({ id: n.id, expanded: n.expanded }));
            nodesData.forEach(n => {
                n.expanded = true;
            });
            initTree();
            
            zoomScale = 1.0;
            document.documentElement.style.setProperty('--zoom-scale', 1.0);
            
            let reflow = treeContainer.offsetHeight;
            const treeWidth = treeContainer.scrollWidth;
            const treeHeight = treeContainer.scrollHeight;
            
            const scaleX = 1300 / treeWidth;
            const scaleY = 700 / treeHeight;
            let printScale = Math.min(scaleX, scaleY, 1.0);
            
            zoomScale = printScale;
            document.documentElement.style.setProperty('--zoom-scale', printScale);
            
            reflow = treeContainer.offsetHeight;
            drawConnections();
        });

        window.addEventListener('afterprint', () => {
            zoomScale = savedZoom;
            document.documentElement.style.setProperty('--zoom-scale', zoomScale);
            savedStates.forEach(s => {
                const node = nodeMap[s.id];
                if (node) node.expanded = s.expanded;
            });
            initTree();
        });

        document.getElementById('print-btn').addEventListener('click', () => {
            window.print();
        });

        window.addEventListener('load', () => {
            applyZoom();
            initTree();
            setTimeout(drawConnections, 100);
        });

        window.addEventListener('resize', drawConnections);
        workspace.addEventListener('scroll', drawConnections);
        
        treeContainer.addEventListener('input', (e) => {
            if (e.target.hasAttribute('contenteditable')) {
                drawConnections();
            }
        });
    </script>
</body>
</html>
"""

    # Wait, there was a tiny syntax error in base HTML around while (current current !== treeContainer) - it should be current !== treeContainer
    # Let's fix that!
    template_html = template_html.replace("while (current current !== treeContainer)", "while (current && current !== treeContainer)")

    full_html = template_html.replace("__TREE_NODES_HTML__", tree_nodes_html).replace("__NODES_JSON_STR__", nodes_json_str)

    output_path = os.path.join(target_dir, "organigrama_Empresa Demo.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(full_html)
        
    print(f"Organigrama Empresa Demo HTML generated successfully at: {output_path}")

if __name__ == "__main__":
    main()
