"""
EU FUNDING RADAR — Bilbao Misión Climática
============================================
Consulta la API pública de la Comisión Europea (SEDIA),
filtra convocatorias relevantes para el Ayuntamiento de Bilbao
y genera un informe HTML + Excel con fichas + alertas por email.

Uso:  python eu_funding_radar.py
Requisitos:  pip install openpyxl
"""

import json
import os
import re
import sys
import smtplib
import urllib.request
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from pathlib import Path

# Intentar importar openpyxl
try:
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    HAS_OPENPYXL = True
except ImportError:
    HAS_OPENPYXL = False
    print("⚠️  openpyxl no instalado. Ejecuta: pip install openpyxl")
    print("   El Excel no se generará, pero el HTML sí.\n")

# ──────────────────────────────────────────────
# CONFIGURACIÓN
# ──────────────────────────────────────────────

CONFIG = {
    "keywords": [
        "climate neutral cities",
        "smart cities climate",
        "sustainable urban mobility",
        "energy efficiency buildings cities",
        "nature-based solutions urban",
        "circular economy cities",
        "clean energy transition local",
        "green infrastructure urban",
        "climate adaptation cities",
        "zero emission transport urban",
        "biodiversity urban nature",
        "net zero cities mission",
        "LIFE climate action local",
        "renewable energy communities",
        "urban resilience climate",
        "URBACT action planning",
        "INTERREG climate cooperation",
        "building renovation energy",
        "Innovation Fund decarbonisation",
        "Innovation Fund energy storage",
        "CEF transport sustainable",
        "CEF energy infrastructure",
        "Digital Europe smart cities AI",
        "digital twin urban",
        "hydrogen cities",
        "heat pump district heating",
        "electric bus public transport",
        "waste management circular",
        "water management urban climate",
        "flood risk adaptation",
        "coastal resilience cities",
        "green deal local authorities",
        "just transition fund",
        "cohesion policy climate",
        "ERDF sustainable urban development",
        "social climate fund",
        "mission ocean coastal cities",
        "mission soil land restoration",
    ],

    "email_to": os.environ.get("EMAIL_TO", ""),
    "email_from": os.environ.get("EMAIL_FROM", ""),
    "smtp_server": os.environ.get("SMTP_SERVER", "smtp.gmail.com"),
    "smtp_port": int(os.environ.get("SMTP_PORT") or "587"),
    "smtp_user": os.environ.get("SMTP_USER", ""),
    "smtp_pass": os.environ.get("SMTP_PASS", ""),

    "seen_file": "seen_calls.json",
    "output_file": "resultados_convocatorias.json",
    "output_html": "resultados_convocatorias.html",
    "output_excel": "resultados_convocatorias.xlsx",
}

# Relevancia por keywords para Bilbao
BILBAO_RELEVANCE = {
    "climate neutral cities": ("MUY ALTA", "Bilbao es ciudad Mission de neutralidad climática 2030. Acceso prioritario vía NetZeroCities."),
    "net zero cities mission": ("MUY ALTA", "Directamente vinculado al Climate City Contract de Bilbao."),
    "smart cities climate": ("ALTA", "Encaja con estrategia Smart City de Bilbao (AS Fabrik, Zorrotzaurre)."),
    "sustainable urban mobility": ("MUY ALTA", "Bilbao es nodo TEN-T. Metro, tranvía, BizkaiBus. Proyecto SuperIsla."),
    "energy efficiency buildings": ("MUY ALTA", "Parque edificatorio antiguo (Casco Viejo, Bilbao La Vieja). Plan rehabilitación activo."),
    "building renovation energy": ("MUY ALTA", "Alineado con Estrategia de Rehabilitación Energética municipal."),
    "nature-based solutions": ("ALTA", "Proyectos de renaturalización en Zorrotzaurre y Abandoibarra. Plan Verde municipal."),
    "green infrastructure": ("ALTA", "Anillo Verde de Bilbao y corredores ecológicos en desarrollo."),
    "circular economy": ("ALTA", "Bilbao tiene Plan de Economía Circular y proyectos en Mercabilbao."),
    "clean energy transition": ("ALTA", "Comunidades energéticas en desarrollo (Otxarkoaga, Txurdinaga)."),
    "renewable energy communities": ("ALTA", "Estrategia energética municipal incluye comunidades energéticas locales."),
    "climate adaptation": ("ALTA", "Plan de Adaptación al Cambio Climático de Bilbao vigente."),
    "zero emission transport": ("ALTA", "Flota municipal en electrificación. Zona bajas emisiones en estudio."),
    "biodiversity urban": ("MEDIA", "Urdaibai cerca. Biodiversidad urbana en parques y ría."),
    "LIFE climate action": ("ALTA", "LIFE es programa clave para acción climática local. Bilbao elegible."),
    "URBACT action planning": ("MUY ALTA", "Bilbao tiene experiencia previa en redes URBACT. Ideal para intercambio."),
    "INTERREG climate cooperation": ("ALTA", "Elegible SUDOE e INTERREG Atlantic. Socios potenciales: Burdeos, Oporto."),
    "Innovation Fund": ("MEDIA", "Aplicable a Petronor/Repsol (Muskiz) y Puerto de Bilbao."),
    "CEF transport": ("MUY ALTA", "Bilbao es nodo TEN-T. Infraestructuras de transporte elegibles."),
    "CEF energy": ("MEDIA", "Infraestructuras energéticas del País Vasco potencialmente elegibles."),
    "Digital Europe": ("ALTA", "Experiencia en gemelo digital urbano. Complementa estrategia Smart City."),
    "digital twin": ("ALTA", "Proyecto BIM/GIS de Bilbao. Complementa estrategia digital."),
    "hydrogen": ("MEDIA", "Corredor Vasco del Hidrógeno. Petronor y Puerto de Bilbao involucrados."),
    "heat pump": ("MEDIA", "Aplicable a rehabilitación de edificios municipales."),
    "electric bus": ("ALTA", "BizkaiBus en proceso de electrificación de flota."),
    "waste management": ("ALTA", "Garbiker y gestión de residuos municipal. Plan de residuos activo."),
    "water management": ("MEDIA", "Consorcio de Aguas Bilbao Bizkaia. Gestión de ría y pluviales."),
    "flood risk": ("ALTA", "Bilbao tiene historial de inundaciones (ría del Nervión). Planes activos."),
    "coastal resilience": ("MEDIA", "Proximidad costera. Impacto indirecto vía estuario del Nervión."),
    "green deal local": ("ALTA", "Pacto Verde aplicable a nivel local. Bilbao comprometida."),
    "just transition": ("MEDIA", "Margen izquierda con pasado industrial. Potencial reconversión."),
    "cohesion policy": ("MEDIA", "País Vasco es región en transición. Fondos FEDER disponibles."),
    "ERDF sustainable urban": ("ALTA", "Bilbao es elegible para EDUSI/FEDER urbano sostenible."),
    "social climate fund": ("MEDIA", "Aplicable a pobreza energética y movilidad sostenible asequible."),
    "mission ocean coastal": ("MEDIA", "Estuario del Nervión y proximidad al Cantábrico."),
    "mission soil": ("MEDIA", "Suelos contaminados industriales en Zorrotzaurre y Margen Izquierda."),
}


# ──────────────────────────────────────────────
# API DE LA COMISIÓN EUROPEA (SEDIA)
# ──────────────────────────────────────────────

BASE_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"

def search_eu_api(keyword, page_size=50):
    params = urllib.parse.urlencode({
        "apiKey": "SEDIA",
        "text": keyword,
        "pageSize": str(page_size),
        "pageNumber": "1",
    })
    url = f"{BASE_URL}?{params}"
    try:
        req = urllib.request.Request(
            url,
            data=b"",
            headers={"User-Agent": "Mozilla/5.0 (EU-Funding-Radar-Bilbao/2.0)"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return None


def get_relevance_for_call(call):
    """Determina la relevancia para Bilbao basándose en keywords."""
    best_level = "INFO"
    best_note = "Revisar relevancia para el Ayuntamiento de Bilbao."
    level_order = {"MUY ALTA": 4, "ALTA": 3, "MEDIA": 2, "BAJA": 1, "INFO": 0}

    call_text = f"{call.get('id','')} {call.get('title','')} {call.get('description','')}".lower()

    for keyword_fragment, (level, note) in BILBAO_RELEVANCE.items():
        if keyword_fragment.lower() in call_text:
            if level_order.get(level, 0) > level_order.get(best_level, 0):
                best_level = level
                best_note = note
    return best_level, best_note


def parse_results(api_response):
    calls = []
    if not api_response or "results" not in api_response:
        return calls

    for item in api_response.get("results", []):
        try:
            ref = item.get("reference", "")
            url = item.get("url", "")
            content = item.get("content", "")
            title = item.get("title", "")
            summary = item.get("summary", "")

            topic_id = ""
            if url:
                parts = url.rstrip("/").split("/")
                if parts:
                    topic_id = parts[-1]
            # Limpiar .json del final del topic_id
            if topic_id.endswith(".json"):
                topic_id = topic_id[:-5]
            if not topic_id:
                match = re.search(r'(HORIZON-[A-Z0-9\-]+|LIFE-[A-Z0-9\-]+|CEF-[A-Z0-9\-]+|DIGITAL-[A-Z0-9\-]+|INTERREG-[A-Z0-9\-]+|INNOVFUND-[A-Z0-9\-]+)', ref)
                if match:
                    topic_id = match.group(1)
                else:
                    topic_id = ref[:60] if ref else ""
            if not topic_id and not title:
                continue

            # Limpiar HTML de todos los campos
            clean_title = re.sub(r'<[^>]+>', '', str(title or "")).strip()
            clean_summary = re.sub(r'<[^>]+>', '', str(summary or "")).strip()[:500]
            clean_content = re.sub(r'<[^>]+>', '', str(content or "")).strip()[:300]

            # Si el titulo es vacio o None, usar el summary o content
            if not clean_title or clean_title == "None":
                # Intentar extraer titulo del contenido
                first_line = (clean_summary or clean_content).split(".")[0].strip()
                clean_title = first_line[:150] if first_line else topic_id

            status = "Unknown"
            text_lower = (clean_content + clean_summary + str(item)).lower()
            if "forthcoming" in text_lower or "upcoming" in text_lower:
                status = "Forthcoming"
            elif "open" in text_lower or "submission" in text_lower:
                status = "Open"
            elif "closed" in text_lower:
                status = "Closed"

            programme = ""
            tid_upper = topic_id.upper()
            if "HORIZON" in tid_upper:
                programme = "Horizon Europe"
            elif "LIFE" in tid_upper:
                programme = "LIFE"
            elif "CEF" in tid_upper:
                programme = "CEF"
            elif "DIGITAL" in tid_upper:
                programme = "Digital Europe"
            elif "INTERREG" in tid_upper:
                programme = "INTERREG"
            elif "INNOVFUND" in tid_upper:
                programme = "Innovation Fund"
            elif "URBACT" in tid_upper:
                programme = "URBACT"

            deadline = ""
            date_match = re.search(r'(\d{1,2}\s+\w+\s+20\d{2})', clean_content + clean_summary)
            if date_match:
                deadline = date_match.group(1)

            if not url or "topic-details" not in url:
                if "calls-for-proposals" not in url and "competitive-calls" not in url:
                    continue

            # Saltar URLs duplicadas que terminan en .json
            if url.endswith(".json"):
                continue

            call_data = {
                "id": topic_id,
                "title": clean_title or topic_id,
                "status": status,
                "programme": programme,
                "deadline": deadline,
                "description": clean_summary or clean_content,
                "url": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

            # Añadir relevancia para Bilbao
            rel_level, rel_note = get_relevance_for_call(call_data)
            call_data["relevance_level"] = rel_level
            call_data["relevance_note"] = rel_note

            calls.append(call_data)
        except Exception:
            continue
    return calls


# ──────────────────────────────────────────────
# LÓGICA PRINCIPAL
# ──────────────────────────────────────────────

def load_seen():
    path = Path(CONFIG["seen_file"])
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_seen(seen):
    with open(CONFIG["seen_file"], "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=2)


def fetch_all_calls():
    all_calls = {}
    total = len(CONFIG["keywords"])

    print(f"\n🇪🇺 EU FUNDING RADAR — Bilbao Misión Climática")
    print(f"{'='*50}")
    print(f"📅 {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print(f"🔍 Buscando en {total} categorías...\n")

    for i, keyword in enumerate(CONFIG["keywords"], 1):
        print(f"  [{i}/{total}] {keyword}...", end=" ", flush=True)
        response = search_eu_api(keyword)
        if response:
            total_hits = response.get("totalResults", 0)
            calls = parse_results(response)
            new = 0
            for call in calls:
                if call["id"] not in all_calls:
                    all_calls[call["id"]] = call
                    new += 1
            print(f"✓ {total_hits} hits, {new} convocatorias nuevas")
        else:
            print("✗ error")

    open_calls = {k: v for k, v in all_calls.items() if v["status"] != "Closed"}
    print(f"\n📊 Total convocatorias únicas: {len(all_calls)}")
    print(f"📊 Abiertas/Próximas/Sin estado: {len(open_calls)}")
    return open_calls


# ──────────────────────────────────────────────
# GENERACIÓN EXCEL
# ──────────────────────────────────────────────

def generate_excel(all_calls, new_calls):
    if not HAS_OPENPYXL:
        print("⚠️  Saltando Excel (openpyxl no instalado)")
        return

    wb = Workbook()

    # Colors
    DARK_BLUE = "1B2A4A"
    HEADER_BLUE = "0057B7"
    LIGHT_BLUE = "E8F0FE"
    LIGHT_GREEN = "E6F4EA"
    LIGHT_RED = "FCE8E6"
    LIGHT_YELLOW = "FFF8E1"
    WHITE = "FFFFFF"
    BORDER_GRAY = "D1D5DB"

    thin_border = Border(
        left=Side(style='thin', color=BORDER_GRAY),
        right=Side(style='thin', color=BORDER_GRAY),
        top=Side(style='thin', color=BORDER_GRAY),
        bottom=Side(style='thin', color=BORDER_GRAY),
    )
    header_font = Font(name='Arial', bold=True, color=WHITE, size=11)
    header_fill = PatternFill('solid', fgColor=HEADER_BLUE)
    title_font = Font(name='Arial', bold=True, size=16, color=DARK_BLUE)
    subtitle_font = Font(name='Arial', size=11, color="6B7280")

    calls_sorted = sorted(all_calls.values(), key=lambda x: (
        0 if x["status"] == "Open" else 1 if x["status"] == "Forthcoming" else 2,
        0 if x.get("relevance_level") == "MUY ALTA" else 1 if x.get("relevance_level") == "ALTA" else 2,
    ))

    # ─── SHEET 1: RESUMEN ───
    ws = wb.active
    ws.title = "Resumen"

    ws.merge_cells('A1:J1')
    ws['A1'] = "EU FUNDING RADAR — AYUNTAMIENTO DE BILBAO"
    ws['A1'].font = title_font
    ws['A1'].alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[1].height = 40

    ws.merge_cells('A2:J2')
    ws['A2'] = f"Mision Climatica - Neutralidad 2030 - Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')} - {len(all_calls)} convocatorias - {len(new_calls)} nuevas"
    ws['A2'].font = subtitle_font
    ws.row_dimensions[2].height = 22

    headers = [
        ("ID Convocatoria", 30),
        ("Titulo", 55),
        ("Programa", 18),
        ("Estado", 14),
        ("Deadline", 20),
        ("Relevancia Bilbao", 18),
        ("Nota Relevancia", 45),
        ("Descripcion", 50),
        ("Nueva?", 10),
        ("Link", 12),
    ]

    for col, (name, width) in enumerate(headers, 1):
        cell = ws.cell(row=4, column=col, value=name)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
        ws.column_dimensions[get_column_letter(col)].width = width
    ws.row_dimensions[4].height = 32

    status_fills = {
        "Open": PatternFill('solid', fgColor=LIGHT_GREEN),
        "Forthcoming": PatternFill('solid', fgColor=LIGHT_BLUE),
        "Closed": PatternFill('solid', fgColor=LIGHT_RED),
    }
    relevance_fills = {
        "MUY ALTA": PatternFill('solid', fgColor="DCFCE7"),
        "ALTA": PatternFill('solid', fgColor=LIGHT_BLUE),
        "MEDIA": PatternFill('solid', fgColor=LIGHT_YELLOW),
    }

    for i, call in enumerate(calls_sorted):
        row = 5 + i
        ws.row_dimensions[row].height = 40
        is_new = call["id"] in new_calls

        values = [
            call["id"],
            call["title"],
            call["programme"],
            call["status"],
            call.get("deadline", ""),
            call.get("relevance_level", "INFO"),
            call.get("relevance_note", ""),
            call["description"][:200],
            "NUEVA" if is_new else "",
            "Ver",
        ]

        for col, val in enumerate(values, 1):
            cell = ws.cell(row=row, column=col, value=val)
            cell.font = Font(name='Arial', size=10)
            cell.alignment = Alignment(vertical='center', wrap_text=True)
            cell.border = thin_border

            if col == 4:  # Status
                cell.fill = status_fills.get(val, PatternFill())
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.font = Font(name='Arial', size=10, bold=True)
            elif col == 6:  # Relevance
                cell.fill = relevance_fills.get(val, PatternFill())
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.font = Font(name='Arial', size=10, bold=True)
            elif col == 9 and is_new:  # New badge
                cell.font = Font(name='Arial', size=10, bold=True, color="DC2626")
                cell.fill = PatternFill('solid', fgColor="FEF2F2")
                cell.alignment = Alignment(horizontal='center', vertical='center')
            elif col == 10:  # Link
                cell.font = Font(name='Arial', size=10, color="0057B7", underline='single')
                cell.hyperlink = call["url"]
                cell.alignment = Alignment(horizontal='center', vertical='center')

        if i % 2 == 1:
            for col in range(1, 11):
                c = ws.cell(row=row, column=col)
                if not c.fill or c.fill.fgColor.rgb == "00000000":
                    c.fill = PatternFill('solid', fgColor="F9FAFB")

    ws.auto_filter.ref = f"A4:J{4 + len(calls_sorted)}"
    ws.freeze_panes = "A5"

    # ─── SHEET 2: FICHAS DETALLADAS ───
    ws2 = wb.create_sheet("Fichas Detalladas")

    row = 1
    for i, call in enumerate(calls_sorted):
        # Header
        ws2.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
        cell = ws2.cell(row=row, column=1, value=f"FICHA {i+1}: {call['id']}")
        cell.font = Font(name='Arial', bold=True, size=12, color=WHITE)
        cell.fill = header_fill
        for c in range(1, 7):
            ws2.cell(row=row, column=c).fill = header_fill
            ws2.cell(row=row, column=c).border = thin_border
        ws2.row_dimensions[row].height = 30
        row += 1

        fields = [
            ("Titulo", call["title"]),
            ("ID", call["id"]),
            ("Programa", call["programme"]),
            ("Estado", call["status"]),
            ("Deadline", call.get("deadline", "No disponible")),
            ("Descripcion", call["description"]),
            ("Relevancia Bilbao", f"{call.get('relevance_level', 'INFO')} — {call.get('relevance_note', '')}"),
            ("Enlace al portal", call["url"]),
        ]

        for label, value in fields:
            ws2.cell(row=row, column=1, value=label)
            ws2.cell(row=row, column=1).font = Font(name='Arial', bold=True, size=10, color=DARK_BLUE)
            ws2.cell(row=row, column=1).fill = PatternFill('solid', fgColor="F1F5F9")
            ws2.cell(row=row, column=1).alignment = Alignment(vertical='top')
            ws2.cell(row=row, column=1).border = thin_border

            ws2.merge_cells(start_row=row, start_column=2, end_row=row, end_column=6)
            cell = ws2.cell(row=row, column=2, value=value)
            cell.font = Font(name='Arial', size=10)
            cell.alignment = Alignment(wrap_text=True, vertical='top')
            cell.border = thin_border
            for c in range(2, 7):
                ws2.cell(row=row, column=c).border = thin_border

            if label == "Relevancia Bilbao":
                if "MUY ALTA" in str(value):
                    cell.font = Font(name='Arial', size=10, bold=True, color="166534")
                elif "ALTA" in str(value):
                    cell.font = Font(name='Arial', size=10, bold=True, color="1E40AF")
            elif label == "Enlace al portal":
                cell.font = Font(name='Arial', size=10, color="0057B7", underline='single')
                cell.hyperlink = value

            ws2.row_dimensions[row].height = 20 if len(str(value)) < 80 else 45
            row += 1
        row += 1

    ws2.column_dimensions['A'].width = 22
    for c in 'BCDEF':
        ws2.column_dimensions[c].width = 20

    # ─── SHEET 3: SEGUIMIENTO ───
    ws3 = wb.create_sheet("Seguimiento")

    track_headers = [
        ("ID Convocatoria", 30),
        ("Titulo corto", 40),
        ("Programa", 16),
        ("Estado", 14),
        ("Deadline", 18),
        ("Relevancia", 14),
        ("Responsable", 20),
        ("Estado interno", 22),
        ("Socios identificados", 30),
        ("Notas / Proximos pasos", 40),
    ]

    for col, (name, width) in enumerate(track_headers, 1):
        cell = ws3.cell(row=1, column=col, value=name)
        cell.font = header_font
        cell.fill = PatternFill('solid', fgColor="7C3AED")
        cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
        cell.border = thin_border
        ws3.column_dimensions[get_column_letter(col)].width = width
    ws3.row_dimensions[1].height = 32

    for i, call in enumerate(calls_sorted):
        row = 2 + i
        ws3.cell(row=row, column=1, value=call["id"]).font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=2, value=call["title"][:60]).font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=3, value=call["programme"]).font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=4, value=call["status"]).font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=5, value=call.get("deadline", "")).font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=6, value=call.get("relevance_level", "")).font = Font(name='Arial', size=10, bold=True)
        ws3.cell(row=row, column=7, value="").font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=8, value="Por revisar").font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=9, value="").font = Font(name='Arial', size=10)
        ws3.cell(row=row, column=10, value="").font = Font(name='Arial', size=10)
        for col in range(1, 11):
            ws3.cell(row=row, column=col).border = thin_border
            ws3.cell(row=row, column=col).alignment = Alignment(vertical='center', wrap_text=True)
        ws3.row_dimensions[row].height = 28

    ws3.auto_filter.ref = f"A1:J{1 + len(calls_sorted)}"
    ws3.freeze_panes = "A2"

    # ─── SHEET 4: RECURSOS ───
    ws4 = wb.create_sheet("Recursos")

    resources = [
        ("Portal EU Funding & Tenders", "https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals", "Portal principal de convocatorias europeas"),
        ("NetZeroCities (Mission Cities)", "https://netzerocities.eu", "Plataforma ciudades Mission. Bilbao es miembro."),
        ("URBACT", "https://urbact.eu/calls-for-proposals", "Redes de ciudades europeas"),
        ("INTERREG SUDOE", "https://interreg-sudoe.eu", "Cooperacion ES-FR-PT"),
        ("INTERREG Atlantic", "https://www.atlanticarea.eu", "Cooperacion Arco Atlantico"),
        ("LIFE Programme (CINEA)", "https://cinea.ec.europa.eu/programmes/life_en", "Programa medioambiental y climatico"),
        ("Innovation Fund", "https://climate.ec.europa.eu/eu-action/eu-funding-climate-action/innovation-fund_en", "Descarbonizacion industrial"),
        ("CEF Transport", "https://cinea.ec.europa.eu/programmes/connecting-europe-facility/transport_en", "Connecting Europe - Transporte"),
        ("Digital Europe", "https://digital-strategy.ec.europa.eu/en/activities/digital-programme", "IA, datos, ciberseguridad"),
        ("CORDIS", "https://cordis.europa.eu", "Base de datos de proyectos financiados"),
    ]

    ws4.merge_cells('A1:C1')
    ws4['A1'] = "RECURSOS Y ENLACES UTILES"
    ws4['A1'].font = Font(name='Arial', bold=True, size=14, color=DARK_BLUE)
    ws4.row_dimensions[1].height = 35

    for col, (name, width) in enumerate([("Recurso", 35), ("Enlace", 75), ("Descripcion", 50)], 1):
        cell = ws4.cell(row=3, column=col, value=name)
        cell.font = header_font
        cell.fill = PatternFill('solid', fgColor="059669")
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
        ws4.column_dimensions[get_column_letter(col)].width = width

    for i, (name, url, desc) in enumerate(resources):
        row = 4 + i
        ws4.cell(row=row, column=1, value=name).font = Font(name='Arial', bold=True, size=10)
        link_cell = ws4.cell(row=row, column=2, value=url)
        link_cell.font = Font(name='Arial', size=10, color="0057B7", underline='single')
        link_cell.hyperlink = url
        ws4.cell(row=row, column=3, value=desc).font = Font(name='Arial', size=10)
        for col in range(1, 4):
            ws4.cell(row=row, column=col).border = thin_border
            ws4.cell(row=row, column=col).alignment = Alignment(vertical='center', wrap_text=True)
        ws4.row_dimensions[row].height = 28

    wb.save(CONFIG["output_excel"])
    print(f"📊 Excel generado: {CONFIG['output_excel']}")


# ──────────────────────────────────────────────
# INFORME HTML (actualizado con enlace a Excel)
# ──────────────────────────────────────────────

def generate_html(all_calls, new_calls):
    calls_sorted = sorted(all_calls.values(), key=lambda x: (
        0 if x["status"] == "Open" else 1 if x["status"] == "Forthcoming" else 2,
        0 if x.get("relevance_level") == "MUY ALTA" else 1 if x.get("relevance_level") == "ALTA" else 2,
    ))

    rows = ""
    for call in calls_sorted:
        is_new = call["id"] in new_calls
        new_badge = ' <span style="color:#DC2626;font-weight:700;font-size:10px;background:#FEF2F2;padding:1px 6px;border-radius:3px">NUEVA</span>' if is_new else ""

        s = call["status"]
        if s == "Open":
            badge = '<span style="color:#065F46;background:#ECFDF5;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">Abierta</span>'
        elif s == "Forthcoming":
            badge = '<span style="color:#1E40AF;background:#EFF6FF;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">Proximamente</span>'
        else:
            badge = '<span style="color:#6B7280;background:#F3F4F6;padding:2px 8px;border-radius:4px;font-size:11px">Info</span>'

        prog = call.get("programme", "")
        prog_badge = f'<span style="color:#7C3AED;background:#F5F3FF;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:600;margin-left:4px">{prog}</span>' if prog else ""

        rel = call.get("relevance_level", "")
        rel_colors = {"MUY ALTA": ("#166534", "#DCFCE7"), "ALTA": ("#1E40AF", "#EFF6FF"), "MEDIA": ("#92400E", "#FFF8E1")}
        rc = rel_colors.get(rel, ("#6B7280", "#F3F4F6"))
        rel_badge = f'<span style="color:{rc[0]};background:{rc[1]};padding:2px 6px;border-radius:3px;font-size:10px;font-weight:600;margin-left:4px">{rel}</span>' if rel and rel != "INFO" else ""

        desc = call["description"][:200]
        if len(call["description"]) > 200:
            desc += "..."

        rel_note = call.get("relevance_note", "")
        rel_html = f'<div style="font-size:11px;color:#166534;margin-top:4px;font-style:italic">{rel_note}</div>' if rel_note and rel != "INFO" else ""

        rows += f"""
        <tr style="border-bottom:1px solid #F1F5F9">
            <td style="padding:12px;vertical-align:top">
                <div style="font-weight:600;color:#1E293B;font-size:13px;margin-bottom:4px">
                    {call['title'][:120]}{new_badge}{prog_badge}{rel_badge}
                </div>
                <div style="font-size:11px;color:#64748B;font-family:monospace">{call['id'][:60]}</div>
                {f'<div style="font-size:12px;color:#475569;margin-top:6px;line-height:1.5">{desc}</div>' if desc else ''}
                {rel_html}
            </td>
            <td style="padding:12px;vertical-align:top;white-space:nowrap">{badge}</td>
            <td style="padding:12px;vertical-align:top;font-size:12px;color:#334155;white-space:nowrap">
                {call.get('deadline','—') or '—'}
            </td>
            <td style="padding:12px;vertical-align:top;text-align:right">
                <a href="{call['url']}" target="_blank" style="color:#0057B7;text-decoration:none;font-size:12px;font-weight:500">Ver &rarr;</a>
            </td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>EU Funding Radar — Bilbao</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, 'Segoe UI', sans-serif; background: #F8FAFC; color: #1E293B; }}
        a:hover {{ text-decoration: underline !important; }}
        tr:hover {{ background: #F8FAFC; }}
    </style>
</head>
<body>
    <div style="max-width:960px;margin:0 auto;padding:24px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:24px">
            <div style="width:44px;height:44px;border-radius:10px;background:linear-gradient(135deg,#FFD700,#FFA500);display:flex;align-items:center;justify-content:center;font-size:22px">🇪🇺</div>
            <div>
                <h1 style="font-size:22px;font-weight:700;letter-spacing:-0.02em">EU Funding Radar</h1>
                <div style="font-size:12px;color:#64748B">Bilbao · Mision Climatica · Neutralidad 2030 · {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px">
            <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:16px">
                <div style="font-size:11px;color:#64748B;text-transform:uppercase;font-weight:600">Total</div>
                <div style="font-size:28px;font-weight:700">{len(all_calls)}</div>
            </div>
            <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:16px">
                <div style="font-size:11px;color:#DC2626;text-transform:uppercase;font-weight:600">Nuevas</div>
                <div style="font-size:28px;font-weight:700;color:#DC2626">{len(new_calls)}</div>
            </div>
            <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:16px">
                <div style="font-size:11px;color:#059669;text-transform:uppercase;font-weight:600">Abiertas</div>
                <div style="font-size:28px;font-weight:700;color:#059669">{sum(1 for c in all_calls.values() if c['status']=='Open')}</div>
            </div>
            <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:16px">
                <div style="font-size:11px;color:#166534;text-transform:uppercase;font-weight:600">Muy Alta Relev.</div>
                <div style="font-size:28px;font-weight:700;color:#166534">{sum(1 for c in all_calls.values() if c.get('relevance_level')=='MUY ALTA')}</div>
            </div>
        </div>

        <div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px;padding:12px 16px;margin-bottom:20px;display:flex;align-items:center;gap:8px">
            <span style="font-size:18px">📊</span>
            <span style="font-size:13px"><strong>Descargar Excel con fichas detalladas:</strong>
            <a href="resultados_convocatorias.xlsx" style="color:#0057B7;font-weight:600">resultados_convocatorias.xlsx</a></span>
        </div>

        {'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:16px;margin-bottom:20px"><strong style="color:#DC2626">' + str(len(new_calls)) + ' convocatorias nuevas detectadas</strong></div>' if new_calls else '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;padding:16px;margin-bottom:20px;color:#166534"><strong>Sin novedades desde la ultima ejecucion</strong></div>'}

        <table style="width:100%;background:white;border:1px solid #E2E8F0;border-radius:10px;border-collapse:collapse;overflow:hidden">
            <thead>
                <tr style="background:#F8FAFC;border-bottom:2px solid #E2E8F0">
                    <th style="padding:10px 12px;text-align:left;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase">Convocatoria</th>
                    <th style="padding:10px 12px;text-align:left;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase">Estado</th>
                    <th style="padding:10px 12px;text-align:left;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase">Deadline</th>
                    <th style="padding:10px 12px;text-align:right;font-size:11px;color:#64748B;font-weight:600;text-transform:uppercase">Link</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>

        <div style="margin-top:20px;padding:16px;background:#EFF6FF;border:1px solid #BFDBFE;border-radius:10px">
            <strong style="color:#1E40AF">Buscar manualmente:</strong>
            <div style="margin-top:8px;font-size:13px;line-height:2">
                <a href="https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals" target="_blank" style="color:#0057B7">Portal EU</a> ·
                <a href="https://netzerocities.eu" target="_blank" style="color:#0057B7">NetZeroCities</a> ·
                <a href="https://urbact.eu/calls-for-proposals" target="_blank" style="color:#0057B7">URBACT</a> ·
                <a href="https://interreg-sudoe.eu" target="_blank" style="color:#0057B7">INTERREG SUDOE</a> ·
                <a href="https://www.atlanticarea.eu" target="_blank" style="color:#0057B7">INTERREG Atlantic</a> ·
                <a href="https://cinea.ec.europa.eu/programmes/life_en" target="_blank" style="color:#0057B7">LIFE</a>
            </div>
        </div>

        <div style="text-align:center;margin-top:20px;font-size:11px;color:#94A3B8">
            EU Funding Radar · Ayuntamiento de Bilbao · API SEDIA (Comision Europea)
        </div>
    </div>
</body>
</html>"""

    with open(CONFIG["output_html"], "w", encoding="utf-8") as f:
        f.write(html)
    return html


# ──────────────────────────────────────────────
# EMAIL
# ──────────────────────────────────────────────

def send_email(new_calls, all_calls):
    if not CONFIG["email_to"] or not CONFIG["smtp_user"]:
        print("\n📧 Email no configurado.")
        return
    if not new_calls:
        return

    subject = f"EU Funding Radar: {len(new_calls)} nuevas — {datetime.now().strftime('%d/%m/%Y')}"
    items = ""
    for c in sorted(new_calls.values(), key=lambda x: x.get("deadline", "9999")):
        items += f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px;margin-bottom:8px"><strong>{c["title"][:100]}</strong><br><span style="font-size:11px;color:#64748B">{c["id"]}</span><br><span style="font-size:12px;color:#475569">{c["description"][:150]}</span><br><a href="{c["url"]}" style="color:#0057B7;font-size:12px">Ver en portal</a></div>'

    body = f'<div style="font-family:sans-serif;max-width:600px;margin:0 auto"><div style="background:#0C1220;color:white;padding:20px;border-radius:12px 12px 0 0"><h1 style="font-size:18px;margin:0">EU Funding Radar</h1><p style="font-size:12px;color:#94A3B8;margin:4px 0 0">Bilbao · {datetime.now().strftime("%d/%m/%Y")}</p></div><div style="padding:20px;background:white;border:1px solid #E2E8F0;border-radius:0 0 12px 12px"><p style="margin-bottom:16px"><strong style="color:#DC2626">{len(new_calls)} convocatorias nuevas</strong></p>{items}</div></div>'

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = CONFIG["email_from"]
        msg["To"] = CONFIG["email_to"]
        msg.attach(MIMEText(body, "html", "utf-8"))
        with smtplib.SMTP(CONFIG["smtp_server"], CONFIG["smtp_port"]) as s:
            s.starttls()
            s.login(CONFIG["smtp_user"], CONFIG["smtp_pass"])
            s.sendmail(CONFIG["email_from"], CONFIG["email_to"].split(","), msg.as_string())
        print(f"\n📧 Email enviado a {CONFIG['email_to']}")
    except Exception as e:
        print(f"\n⚠️  Error email: {e}")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    all_calls = fetch_all_calls()

    if not all_calls:
        print("\n❌ No se encontraron convocatorias.")
        return 1

    seen = load_seen()
    new_calls = {k: v for k, v in all_calls.items() if k not in seen}
    print(f"🆕 Nuevas desde ultima ejecucion: {len(new_calls)}")

    # Guardar JSON
    with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
        json.dump(list(all_calls.values()), f, ensure_ascii=False, indent=2)

    # Generar HTML
    generate_html(all_calls, new_calls)

    # Generar Excel
    generate_excel(all_calls, new_calls)

    # Email
    if new_calls:
        send_email(new_calls, all_calls)

    # Actualizar vistos
    seen.update({k: datetime.now(timezone.utc).isoformat() for k in all_calls})
    save_seen(seen)

    print(f"\n{'='*50}")
    print(f"✅ COMPLETADO")
    print(f"   📊 {len(all_calls)} convocatorias")
    print(f"   🆕 {len(new_calls)} nuevas")
    print(f"   📄 HTML: {CONFIG['output_html']}")
    print(f"   📊 Excel: {CONFIG['output_excel']}")
    print(f"{'='*50}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

