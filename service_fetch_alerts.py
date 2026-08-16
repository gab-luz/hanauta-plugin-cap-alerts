#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from urllib import parse, request

SETTINGS_FILE = Path.home() / ".local" / "state" / "hanauta" / "notification-center" / "settings.json"
SERVICE_DIR = Path.home() / ".local" / "state" / "hanauta" / "service"
OUTPUT_FILE = SERVICE_DIR / "cap_alerts.json"

INMET_API = "https://apiprevmet3.inmet.gov.br/avisos/ativos"
NWS_API = "https://api.weather.gov/alerts/active"

INMET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Hanauta/1.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://avisos.inmet.gov.br",
    "Referer": "https://avisos.inmet.gov.br/",
}
NWS_HEADERS = {
    "User-Agent": "Hanauta CAP Alerts Service/1.0",
    "Accept": "application/geo+json, application/json",
}


def _normalized(text: str) -> str:
    base = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(re.sub(r"[^0-9a-zA-Z]+", " ", base.lower()).split())


def _write_payload(payload: dict) -> None:
    SERVICE_DIR.mkdir(parents=True, exist_ok=True)
    tmp_file = OUTPUT_FILE.with_suffix(f"{OUTPUT_FILE.suffix}.tmp")
    data = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    tmp_file.write_text(data, encoding="utf-8")
    tmp_file.replace(OUTPUT_FILE)


def _request_json(url: str, headers: dict[str, str], timeout: float = 10.0) -> dict:
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace").strip()
    return json.loads(body) if body else {}


def _load_settings() -> dict:
    try:
        payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _service_enabled(settings: dict) -> bool:
    services = settings.get("services", {})
    if not isinstance(services, dict):
        return True
    cap = services.get("cap_alerts", {})
    if not isinstance(cap, dict):
        return True
    return bool(cap.get("enabled", True))


def _location(settings: dict) -> dict | None:
    weather = settings.get("weather", {})
    if not isinstance(weather, dict):
        return None
    try:
        return {
            "name": str(weather.get("name", "")).strip(),
            "admin1": str(weather.get("admin1", "")).strip(),
            "country": str(weather.get("country", "")).strip(),
            "latitude": float(weather.get("latitude")),
            "longitude": float(weather.get("longitude")),
            "timezone": str(weather.get("timezone", "auto")).strip() or "auto",
        }
    except Exception:
        return None


def _icon_for_event(event: str) -> str:
    lowered = (event or "").strip().lower()
    if any(token in lowered for token in ("thunder", "storm", "tornado", "tempestade", "trovoada", "granizo", "hail")):
        return "thunderstorms"
    if any(token in lowered for token in ("flood", "rain", "flash flood", "chuva", "alag")):
        return "overcast-rain"
    if any(token in lowered for token in ("snow", "blizzard", "ice", "sleet", "neve", "geada")):
        return "overcast-snow"
    if any(token in lowered for token in ("wind", "hurricane", "tropical", "vento", "vendaval", "ciclone")):
        return "air-quality"
    if any(token in lowered for token in ("fog", "nevoeiro")):
        return "fog"
    if any(token in lowered for token in ("heat", "fire", "red flag", "calor", "incendio", "incêndio")):
        return "clear-day"
    return "not-available"


def _severity_inmet(text: str) -> str:
    lowered = (text or "").strip().lower()
    if "grande perigo" in lowered:
        return "Extreme"
    if "perigo" in lowered and "potencial" not in lowered:
        return "Severe"
    if "potencial" in lowered:
        return "Moderate"
    return "Unknown"


def _normalize_alert_color(value: str) -> str:
    text = (value or "").strip()
    if not text or not text.startswith("#"):
        return ""
    hex_part = text[1:]
    if len(hex_part) == 3 and all(ch in "0123456789abcdefABCDEF" for ch in hex_part):
        return f"#{hex_part.upper()}"
    if len(hex_part) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in hex_part):
        return f"#{hex_part.upper()}"
    return ""


def _to_iso(value: str) -> str:
    raw = (value or "").strip()
    return raw.replace(" ", "T") if raw else ""


def _fetch_inmet(location: dict) -> list[dict]:
    payload = _request_json(INMET_API, INMET_HEADERS, timeout=10.0)
    rows = payload.get("hoje", [])
    if not isinstance(rows, list):
        return []
    city = _normalized(location.get("name", ""))
    out: list[dict] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        municipios = str(row.get("municipios", "")).strip()
        if city and f"{city} " not in f"{_normalized(municipios)} ":
            continue
        event = str(row.get("descricao", "")).strip()
        if not event:
            continue
        riscos = row.get("riscos") if isinstance(row.get("riscos"), list) else []
        instrucoes = row.get("instrucoes") if isinstance(row.get("instrucoes"), list) else []
        out.append(
            {
                "identifier": str(row.get("codigo", "")).strip() or str(row.get("id", "")).strip() or event,
                "event": event,
                "headline": f"{event} • {str(row.get('severidade', '')).strip()}".strip(" •"),
                "severity": _severity_inmet(str(row.get("severidade", ""))),
                "urgency": "Expected",
                "certainty": "Likely",
                "area_desc": str(row.get("estados", "")).strip(),
                "sender_name": "INMET",
                "sent": str(row.get("created_at", "")).strip(),
                "effective": _to_iso(str(row.get("inicio", "")).strip() or str(row.get("data_inicio", "")).strip()),
                "expires": _to_iso(str(row.get("fim", "")).strip() or str(row.get("data_fim", "")).strip()),
                "instruction": "\n".join(str(x).strip() for x in instrucoes if str(x).strip()),
                "description": "\n".join(str(x).strip() for x in riscos if str(x).strip()),
                "response": "Monitor",
                "web": "https://avisos.inmet.gov.br/",
                "icon_name": _icon_for_event(event),
                "contact_number": "199 / 193",
                "color": _normalize_alert_color(str(row.get("aviso_cor", "")).strip()),
            }
        )
    return out


def _fetch_nws(location: dict) -> list[dict]:
    params = parse.urlencode(
        {
            "point": f"{location['latitude']:.4f},{location['longitude']:.4f}",
            "status": "actual",
            "message_type": "alert",
        }
    )
    payload = _request_json(f"{NWS_API}?{params}", NWS_HEADERS, timeout=8.0)
    rows = payload.get("features", [])
    if not isinstance(rows, list):
        return []
    out: list[dict] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        props = item.get("properties", {})
        if not isinstance(props, dict):
            continue
        event = str(props.get("event", "")).strip()
        if not event:
            continue
        out.append(
            {
                "identifier": str(props.get("id", "")).strip() or str(item.get("id", "")).strip() or event,
                "event": event,
                "headline": str(props.get("headline", "")).strip() or event,
                "severity": str(props.get("severity", "Unknown")).strip() or "Unknown",
                "urgency": str(props.get("urgency", "Unknown")).strip() or "Unknown",
                "certainty": str(props.get("certainty", "Unknown")).strip() or "Unknown",
                "area_desc": str(props.get("areaDesc", "")).strip(),
                "sender_name": str(props.get("senderName", "")).strip() or "National Weather Service",
                "sent": str(props.get("sent", "")).strip(),
                "effective": str(props.get("effective", "")).strip(),
                "expires": str(props.get("expires", "")).strip(),
                "instruction": str(props.get("instruction", "")).strip(),
                "description": str(props.get("description", "")).strip(),
                "response": str(props.get("response", "")).strip(),
                "web": str(props.get("web", "")).strip(),
                "icon_name": _icon_for_event(event),
                "contact_number": "911",
                "color": "",
            }
        )
    return out


def main() -> int:
    settings = _load_settings()

    location = _location(settings)
    payload: dict = {
        "source": "hanauta-service-cap-alerts",
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "location": location or {},
        "alerts": [],
    }

    if not _service_enabled(settings) or location is None:
        _write_payload(payload)
        return 0

    try:
        country = (location.get("country") or "").strip().lower()
        if country in {"brazil", "brasil"}:
            payload["alerts"] = _fetch_inmet(location)
        else:
            payload["alerts"] = _fetch_nws(location)
    except Exception:
        payload["alerts"] = []

    payload["updated_at"] = datetime.now(timezone.utc).isoformat()
    _write_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
