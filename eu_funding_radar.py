"""
EU FUNDING RADAR — Bilbao Misión Climática
============================================
Consulta la API pública de la Comisión Europea (SEDIA),
filtra convocatorias relevantes para el Ayuntamiento de Bilbao
y genera un informe HTML + alertas por email.

Uso:  python eu_funding_radar.py
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
}

# ──────────────────────────────────────────────
# API DE LA COMISIÓN EUROPEA (SEDIA)
# ──────────────────────────────────────────────

BASE_URL = "https://api.tech.ec.europa.eu/search-api/prod/rest/search"

def search_eu_api(keyword, page_size=50):
    """
    Consulta la API SEDIA de la Comisión Europea.
    IMPORTANTE: usa POST con body vacío y parámetros en la URL.
    """
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
            data=b"",  # Body vacío = POST automático
            headers={"User-Agent": "Mozilla/5.0 (EU-Funding-Radar-Bilbao/2.0)"},
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        return None


def parse_results(api_response):
    """Extrae convocatorias de la respuesta de la API SEDIA."""
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

            # Extraer el topic ID de la URL o referencia
            topic_id = ""
            if url:
                # URL tipo: .../topic-details/HORIZON-MISS-2023-CIT-01-01
                parts = url.rstrip("/").split("/")
                if parts:
                    topic_id = parts[-1]

            if not topic_id:
                # Intentar extraer de la referencia
                match = re.search(r'(HORIZON-[A-Z0-9\-]+|LIFE-[A-Z0-9\-]+|CEF-[A-Z0-9\-]+|DIGITAL-[A-Z0-9\-]+|INTERREG-[A-Z0-9\-]+|INNOVFUND-[A-Z0-9\-]+)', ref)
                if match:
                    topic_id = match.group(1)
                else:
                    topic_id = ref[:60] if ref else ""

            if not topic_id and not title:
                continue

            # Limpiar HTML
            clean_title = re.sub(r'<[^>]+>', '', str(title)).strip()
            clean_summary = re.sub(r'<[^>]+>', '', str(summary)).strip()[:500]
            clean_content = re.sub(r'<[^>]+>', '', str(content)).strip()[:300]

            # Detectar status del contenido
            status = "Unknown"
            text_lower = (clean_content + clean_summary + str(item)).lower()
            if "forthcoming" in text_lower or "upcoming" in text_lower:
                status = "Forthcoming"
            elif "open" in text_lower or "submission" in text_lower:
                status = "Open"
            elif "closed" in text_lower:
                status = "Closed"

            # Detectar programa
            programme = ""
            if "HORIZON" in topic_id.upper():
                programme = "Horizon Europe"
            elif "LIFE" in topic_id.upper():
                programme = "LIFE"
            elif "CEF" in topic_id.upper():
                programme = "CEF"
            elif "DIGITAL" in topic_id.upper():
                programme = "Digital Europe"
            elif "INTERREG" in topic_id.upper():
                programme = "INTERREG"
            elif "INNOVFUND" in topic_id.upper():
                programme = "Innovation Fund"

            # Extraer deadline si aparece en el contenido
            deadline = ""
            date_match = re.search(r'(\d{1,2}\s+\w+\s+20\d{2})', clean_content + clean_summary)
            if date_match:
                deadline = date_match.group(1)

            # Filtrar: solo convocatorias (no proyectos ni documentos)
            if not url or "topic-details" not in url:
                # También aceptar si es una call-for-proposals
                if "calls-for-proposals" not in url and "competitive-calls" not in url:
                    continue

            calls.append({
                "id": topic_id,
                "title": clean_title or topic_id,
                "status": status,
                "programme": programme,
                "deadline": deadline,
                "description": clean_summary or clean_content,
                "url": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            })

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

    # Filtrar: quitar las cerradas
    open_calls = {k: v for k, v in all_calls.items() if v["status"] != "Closed"}

    print(f"\n📊 Total convocatorias únicas: {len(all_calls)}")
    print(f"📊 Abiertas/Próximas/Sin estado: {len(open_calls)}")
    return open_calls


# ──────────────────────────────────────────────
# INFORME HTML
# ──────────────────────────────────────────────

def generate_html(all_calls, new_calls):
    calls_sorted = sorted(all_calls.values(), key=lambda x: (
        0 if x["status"] == "Open" else 1 if x["status"] == "Forthcoming" else 2,
        x.get("deadline", "9999")
    ))

    rows = ""
    for call in calls_sorted:
        is_new = call["id"] in new_calls
        new_badge = ' <span style="color:#DC2626;font-weight:700;font-size:10px;background:#FEF2F2;padding:1px 6px;border-radius:3px">🆕 NUEVA</span>' if is_new else ""

        s = call["status"]
        if s == "Open":
            badge = '<span style="color:#065F46;background:#ECFDF5;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">Abierta</span>'
        elif s == "Forthcoming":
            badge = '<span style="color:#1E40AF;background:#EFF6FF;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">Próximamente</span>'
        else:
            badge = '<span style="color:#6B7280;background:#F3F4F6;padding:2px 8px;border-radius:4px;font-size:11px">Info</span>'

        prog = call.get("programme", "")
        prog_badge = f'<span style="color:#7C3AED;background:#F5F3FF;padding:2px 6px;border-radius:3px;font-size:10px;font-weight:600;margin-left:4px">{prog}</span>' if prog else ""

        desc = call["description"][:200]
        if len(call["description"]) > 200:
            desc += "..."

        rows += f"""
        <tr style="border-bottom:1px solid #F1F5F9">
            <td style="padding:12px;vertical-align:top">
                <div style="font-weight:600;color:#1E293B;font-size:13px;margin-bottom:4px">
                    {call['title'][:120]}{new_badge}{prog_badge}
                </div>
                <div style="font-size:11px;color:#64748B;font-family:monospace">{call['id'][:60]}</div>
                {f'<div style="font-size:12px;color:#475569;margin-top:6px;line-height:1.5">{desc}</div>' if desc else ''}
            </td>
            <td style="padding:12px;vertical-align:top;white-space:nowrap">{badge}</td>
            <td style="padding:12px;vertical-align:top;font-size:12px;color:#334155;white-space:nowrap">
                {call.get('deadline','—') or '—'}
            </td>
            <td style="padding:12px;vertical-align:top;text-align:right">
                <a href="{call['url']}" target="_blank" style="color:#0057B7;text-decoration:none;font-size:12px;font-weight:500">Ver →</a>
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
                <div style="font-size:12px;color:#64748B">Bilbao · Misión Climática · Neutralidad 2030 · {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
            </div>
        </div>

        <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
            <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:16px">
                <div style="font-size:11px;color:#64748B;text-transform:uppercase;font-weight:600">Total detectadas</div>
                <div style="font-size:28px;font-weight:700">{len(all_calls)}</div>
            </div>
            <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:16px">
                <div style="font-size:11px;color:#DC2626;text-transform:uppercase;font-weight:600">🆕 Nuevas</div>
                <div style="font-size:28px;font-weight:700;color:#DC2626">{len(new_calls)}</div>
            </div>
            <div style="background:white;border:1px solid #E2E8F0;border-radius:10px;padding:16px">
                <div style="font-size:11px;color:#059669;text-transform:uppercase;font-weight:600">Abiertas</div>
                <div style="font-size:28px;font-weight:700;color:#059669">{sum(1 for c in all_calls.values() if c['status']=='Open')}</div>
            </div>
        </div>

        {'<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:10px;padding:16px;margin-bottom:20px"><strong style="color:#DC2626">🆕 ' + str(len(new_calls)) + ' convocatorias nuevas detectadas desde la última ejecución</strong></div>' if new_calls else '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:10px;padding:16px;margin-bottom:20px;color:#166534"><strong>✓ Sin novedades desde la última ejecución</strong></div>'}

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
            <strong style="color:#1E40AF">🔗 Buscar manualmente:</strong>
            <div style="margin-top:8px;font-size:13px;line-height:2">
                <a href="https://ec.europa.eu/info/funding-tenders/opportunities/portal/screen/opportunities/calls-for-proposals" target="_blank" style="color:#0057B7">Portal EU Funding & Tenders</a> ·
                <a href="https://netzerocities.eu" target="_blank" style="color:#0057B7">NetZeroCities (Bilbao Mission)</a> ·
                <a href="https://urbact.eu/calls-for-proposals" target="_blank" style="color:#0057B7">URBACT</a> ·
                <a href="https://interreg-sudoe.eu" target="_blank" style="color:#0057B7">INTERREG SUDOE</a> ·
                <a href="https://www.atlanticarea.eu" target="_blank" style="color:#0057B7">INTERREG Atlantic</a> ·
                <a href="https://cinea.ec.europa.eu/programmes/life_en" target="_blank" style="color:#0057B7">LIFE Programme</a>
            </div>
        </div>

        <div style="text-align:center;margin-top:20px;font-size:11px;color:#94A3B8">
            EU Funding Radar · Ayuntamiento de Bilbao · Fuente: API SEDIA (Comisión Europea) · Generado automáticamente
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
        print("\n📧 Email no configurado. Ver README para instrucciones.")
        return

    if not new_calls:
        print("\n📧 Sin novedades — no se envía email.")
        return

    subject = f"🇪🇺 EU Funding Radar: {len(new_calls)} nuevas — {datetime.now().strftime('%d/%m/%Y')}"

    items = ""
    for c in sorted(new_calls.values(), key=lambda x: x.get("deadline", "9999")):
        items += f'<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:12px;margin-bottom:8px"><strong style="font-size:14px">{c["title"][:100]}</strong><br><span style="font-size:11px;color:#64748B;font-family:monospace">{c["id"]}</span><br><span style="font-size:12px;color:#475569">{c["description"][:150]}</span><br><a href="{c["url"]}" style="color:#0057B7;font-size:12px">Ver en portal →</a></div>'

    body = f'<div style="font-family:sans-serif;max-width:600px;margin:0 auto"><div style="background:#0C1220;color:white;padding:20px;border-radius:12px 12px 0 0"><h1 style="font-size:18px;margin:0">🇪🇺 EU Funding Radar</h1><p style="font-size:12px;color:#94A3B8;margin:4px 0 0">Bilbao · {datetime.now().strftime("%d/%m/%Y")}</p></div><div style="padding:20px;background:white;border:1px solid #E2E8F0;border-radius:0 0 12px 12px"><p style="margin-bottom:16px"><strong style="color:#DC2626">{len(new_calls)} convocatorias nuevas</strong></p>{items}</div></div>'

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
        print("\n❌ No se encontraron convocatorias. Comprueba tu conexión.")
        return 1

    seen = load_seen()
    new_calls = {k: v for k, v in all_calls.items() if k not in seen}
    print(f"🆕 Nuevas desde última ejecución: {len(new_calls)}")

    # Guardar JSON
    with open(CONFIG["output_file"], "w", encoding="utf-8") as f:
        json.dump(list(all_calls.values()), f, ensure_ascii=False, indent=2)

    # Generar HTML
    generate_html(all_calls, new_calls)

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
    print(f"   📄 Abre resultados_convocatorias.html en tu navegador")
    print(f"{'='*50}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
