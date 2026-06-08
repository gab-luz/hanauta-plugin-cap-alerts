from __future__ import annotations

import json
import importlib.util
import random
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib import parse, request


def _load_weather_backend():
    candidates = [
        Path.home() / "dev" / "hanauta-plugin-weather" / "weather_backend.py",
        Path("/mnt/outros/DEV/hanauta-plugin-weather/weather_backend.py"),
    ]
    for candidate in candidates:
        if not candidate.exists():
            continue
        spec = importlib.util.spec_from_file_location("hanauta_plugin_weather_backend", candidate)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module
    try:
        from pyqt.shared import weather as module

        return module
    except Exception as exc:
        raise ImportError("weather backend not found") from exc


_WEATHER = _load_weather_backend()
WeatherCity = _WEATHER.WeatherCity
configured_location = _WEATHER.configured_location
AnimatedWeatherIcon = _WEATHER.AnimatedWeatherIcon
animated_icon_path = _WEATHER.animated_icon_path


NWS_ALERTS_API = "https://api.weather.gov/alerts/active"
INMET_ALERTS_API = "https://apiprevmet3.inmet.gov.br/avisos/ativos"
SETTINGS_FILE = Path.home() / ".local" / "state" / "hanauta" / "notification-center" / "settings.json"
SERVICE_CAP_ALERTS_CACHE = Path.home() / ".local" / "state" / "hanauta" / "service" / "cap_alerts.json"
SERVICE_CACHE_MAX_AGE_SECONDS = 180

NWS_HEADERS = {
    "User-Agent": "Hanauta CAP Alerts/1.0 (weather integration)",
    "Accept": "application/geo+json, application/json",
}
INMET_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Hanauta/1.0",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://avisos.inmet.gov.br",
    "Referer": "https://avisos.inmet.gov.br/",
}

_DEMO_CACHE: list["CapAlert"] = []
_DEMO_CACHE_EXPIRES: datetime | None = None
SEVERITY_RANK = {
    "extreme": 4,
    "severe": 3,
    "moderate": 2,
    "minor": 1,
    "unknown": 0,
}
SEVERITY_COLOR = {
    "extreme": "#D32F2F",
    "severe": "#F57C00",
    "moderate": "#FBC02D",
    "minor": "#0288D1",
    "unknown": "#9E9E9E",
}


@dataclass(frozen=True)
class CapAlert:
    identifier: str
    event: str
    headline: str
    severity: str
    urgency: str
    certainty: str
    area_desc: str
    sender_name: str
    sent: str
    effective: str
    expires: str
    instruction: str
    description: str
    response: str
    web: str
    icon_name: str
    contact_number: str = ""
    color: str = ""


def normalize_alert_color(value: str) -> str:
    text = (value or "").strip()
    if not text:
        return ""
    if not text.startswith("#"):
        return ""
    hex_part = text[1:]
    if len(hex_part) == 3 and all(ch in "0123456789abcdefABCDEF" for ch in hex_part):
        return f"#{hex_part.upper()}"
    if len(hex_part) == 6 and all(ch in "0123456789abcdefABCDEF" for ch in hex_part):
        return f"#{hex_part.upper()}"
    return ""


def severity_color(severity: str) -> str:
    lowered = (severity or "").strip().lower()
    return SEVERITY_COLOR.get(lowered, SEVERITY_COLOR["unknown"])


def cap_alert_accent(severity: str, provider_color: str) -> str:
    normalized = normalize_alert_color(provider_color)
    if normalized:
        return normalized
    return severity_color(severity)


def alert_accent_color(alert: CapAlert | None) -> str:
    if alert is None:
        return SEVERITY_COLOR["moderate"]
    return cap_alert_accent(alert.severity, alert.color)


def _request_json(url: str, headers: dict[str, str], timeout: float = 10.0) -> dict[str, Any]:
    req = request.Request(url, headers=headers)
    with request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace").strip()
    if not body:
        return {}
    return json.loads(body)


def load_runtime_settings() -> dict[str, Any]:
    try:
        payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def cap_alert_settings() -> dict[str, Any]:
    settings = load_runtime_settings()
    services = settings.get("services", {})
    if not isinstance(services, dict):
        return {}
    cap = services.get("cap_alerts", {})
    return cap if isinstance(cap, dict) else {}


def test_mode_enabled() -> bool:
    return bool(cap_alert_settings().get("test_mode", False))


def configured_alert_location() -> WeatherCity | None:
    return configured_location()


def _normalized(text: str) -> str:
    base = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return " ".join(base.lower().replace("-", " ").split())


def _severity_from_inmet(level: str) -> str:
    lowered = level.strip().lower()
    if "grande perigo" in lowered:
        return "Extreme"
    if "perigo" in lowered and "potencial" not in lowered:
        return "Severe"
    if "potencial" in lowered:
        return "Moderate"
    return "Unknown"


def icon_name_for_event(event: str) -> str:
    lowered = event.strip().lower()
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


def _alert_from_plain(obj: dict[str, Any]) -> CapAlert | None:
    try:
        event = str(obj.get("event", "")).strip()
        if not event:
            return None
        return CapAlert(
            identifier=str(obj.get("identifier", "")).strip() or event,
            event=event,
            headline=str(obj.get("headline", "")).strip() or event,
            severity=str(obj.get("severity", "Unknown")).strip() or "Unknown",
            urgency=str(obj.get("urgency", "Unknown")).strip() or "Unknown",
            certainty=str(obj.get("certainty", "Unknown")).strip() or "Unknown",
            area_desc=str(obj.get("area_desc", "")).strip(),
            sender_name=str(obj.get("sender_name", "")).strip() or "Unknown",
            sent=str(obj.get("sent", "")).strip(),
            effective=str(obj.get("effective", "")).strip(),
            expires=str(obj.get("expires", "")).strip(),
            instruction=str(obj.get("instruction", "")).strip(),
            description=str(obj.get("description", "")).strip(),
            response=str(obj.get("response", "")).strip(),
            web=str(obj.get("web", "")).strip(),
            icon_name=str(obj.get("icon_name", "")).strip() or "not-available",
            contact_number=str(obj.get("contact_number", "")).strip(),
            color=normalize_alert_color(str(obj.get("color", "")).strip()),
        )
    except Exception:
        return None


def _service_cache_fresh(updated_at_iso: str) -> bool:
    try:
        parsed = datetime.fromisoformat(updated_at_iso.replace("Z", "+00:00"))
    except Exception:
        return False
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    age = (now - parsed.astimezone(timezone.utc)).total_seconds()
    return 0 <= age <= SERVICE_CACHE_MAX_AGE_SECONDS


def _load_service_cached_alerts(location: WeatherCity | None) -> list[CapAlert] | None:
    if not SERVICE_CAP_ALERTS_CACHE.exists():
        return None
    try:
        payload = json.loads(SERVICE_CAP_ALERTS_CACHE.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(payload, dict):
        return None
    updated_at = str(payload.get("updated_at", "")).strip()
    if not _service_cache_fresh(updated_at):
        return None
    cached_location = payload.get("location", {})
    if isinstance(cached_location, dict) and location is not None:
        cache_name = _normalized(str(cached_location.get("name", "")))
        live_name = _normalized(location.name or "")
        if cache_name and live_name and cache_name != live_name:
            return None
    raw_alerts = payload.get("alerts", [])
    if not isinstance(raw_alerts, list):
        return None
    alerts: list[CapAlert] = []
    for item in raw_alerts:
        if not isinstance(item, dict):
            continue
        parsed = _alert_from_plain(item)
        if parsed is not None:
            alerts.append(parsed)
    alerts.sort(key=lambda item: (-SEVERITY_RANK.get(item.severity.lower(), 0), item.event.lower()))
    return alerts


def _inmet_matches_location(municipios: str, location: WeatherCity) -> bool:
    city = _normalized(location.name)
    cleaned = _normalized(municipios)
    if not city or not cleaned:
        return False
    return f"{city} " in f"{cleaned} "


def _inmet_alert_to_cap(item: dict[str, Any], location: WeatherCity) -> CapAlert | None:
    event = str(item.get("descricao", "")).strip()
    if not event:
        return None
    severidade = str(item.get("severidade", "")).strip()
    riscos = item.get("riscos")
    instrucoes = item.get("instrucoes")
    risk_text = "\n".join(str(x).strip() for x in riscos if str(x).strip()) if isinstance(riscos, list) else ""
    instruction_text = "\n".join(str(x).strip() for x in instrucoes if str(x).strip()) if isinstance(instrucoes, list) else ""
    area_desc = str(item.get("estados", "")).strip()
    municipios = str(item.get("municipios", "")).strip()
    if location.name and location.name not in area_desc and municipios:
        area_desc = f"{location.label} • {area_desc}" if area_desc else location.label
    sent = str(item.get("created_at", "")).strip()
    effective = str(item.get("inicio", "")).strip() or str(item.get("data_inicio", "")).strip()
    expires = str(item.get("fim", "")).strip() or str(item.get("data_fim", "")).strip()
    headline = f"{event} • {severidade}".strip(" •")
    identifier = str(item.get("codigo", "")).strip() or str(item.get("id", "")).strip() or event
    return CapAlert(
        identifier=identifier,
        event=event,
        headline=headline or event,
        severity=_severity_from_inmet(severidade),
        urgency="Expected",
        certainty="Likely",
        area_desc=area_desc,
        sender_name="INMET",
        sent=sent,
        effective=effective,
        expires=expires,
        instruction=instruction_text,
        description=risk_text,
        response="Monitor",
        web="https://avisos.inmet.gov.br/",
        icon_name=icon_name_for_event(event),
        contact_number="199 / 193",
        color=normalize_alert_color(str(item.get("aviso_cor", "")).strip()),
    )


def _fetch_inmet_alerts(location: WeatherCity) -> list[CapAlert]:
    try:
        payload = _request_json(INMET_ALERTS_API, INMET_HEADERS, timeout=10.0)
    except Exception:
        return []
    raw_alerts = payload.get("hoje", [])
    if not isinstance(raw_alerts, list):
        return []
    alerts: list[CapAlert] = []
    for item in raw_alerts:
        if not isinstance(item, dict):
            continue
        municipios = str(item.get("municipios", "")).strip()
        if not _inmet_matches_location(municipios, location):
            continue
        converted = _inmet_alert_to_cap(item, location)
        if converted is not None:
            alerts.append(converted)
    alerts.sort(key=lambda item: (-SEVERITY_RANK.get(item.severity.lower(), 0), item.event.lower()))
    return alerts


def _fetch_nws_alerts(location: WeatherCity) -> list[CapAlert]:
    params = parse.urlencode(
        {
            "point": f"{location.latitude:.4f},{location.longitude:.4f}",
            "status": "actual",
            "message_type": "alert",
        }
    )
    try:
        payload = _request_json(f"{NWS_ALERTS_API}?{params}", NWS_HEADERS, timeout=8.0)
    except Exception:
        return []
    features = payload.get("features", [])
    if not isinstance(features, list):
        return []
    alerts: list[CapAlert] = []
    for feature in features:
        props = feature.get("properties", {}) if isinstance(feature, dict) else {}
        if not isinstance(props, dict):
            continue
        event = str(props.get("event", "")).strip()
        if not event:
            continue
        alerts.append(
            CapAlert(
                identifier=str(props.get("id", "")).strip() or str(feature.get("id", "")).strip() or event,
                event=event,
                headline=str(props.get("headline", "")).strip() or event,
                severity=str(props.get("severity", "Unknown")).strip() or "Unknown",
                urgency=str(props.get("urgency", "Unknown")).strip() or "Unknown",
                certainty=str(props.get("certainty", "Unknown")).strip() or "Unknown",
                area_desc=str(props.get("areaDesc", "")).strip(),
                sender_name=str(props.get("senderName", "")).strip() or "National Weather Service",
                sent=str(props.get("sent", "")).strip(),
                effective=str(props.get("effective", "")).strip(),
                expires=str(props.get("expires", "")).strip(),
                instruction=str(props.get("instruction", "")).strip(),
                description=str(props.get("description", "")).strip(),
                response=str(props.get("response", "")).strip(),
                web=str(props.get("web", "")).strip(),
                icon_name=icon_name_for_event(event),
                contact_number="911",
                color="",
            )
        )
    alerts.sort(key=lambda item: (-SEVERITY_RANK.get(item.severity.lower(), 0), item.event.lower()))
    return alerts


def fetch_active_alerts(location: WeatherCity | None) -> list[CapAlert]:
    if test_mode_enabled():
        return random_test_alerts()
    if location is None:
        return []

    cached = _load_service_cached_alerts(location)
    if cached is not None:
        return cached

    country = (location.country or "").strip().lower()
    if country in {"brazil", "brasil"}:
        return _fetch_inmet_alerts(location)
    return _fetch_nws_alerts(location)


def random_test_alerts() -> list[CapAlert]:
    global _DEMO_CACHE, _DEMO_CACHE_EXPIRES
    now = datetime.now(timezone.utc)
    if _DEMO_CACHE and _DEMO_CACHE_EXPIRES is not None and now < _DEMO_CACHE_EXPIRES:
        return list(_DEMO_CACHE)
    samples = [
        CapAlert(
            identifier="test-br-sp-1",
            event="Severe Thunderstorm Warning",
            headline="Strong storms may impact Sao Paulo state through the evening.",
            severity="Severe",
            urgency="Immediate",
            certainty="Likely",
            area_desc="Sao Paulo, Brazil",
            sender_name="Brazil Civil Defense Demo Feed",
            sent=now.isoformat(),
            effective=now.isoformat(),
            expires=(now + timedelta(hours=3)).isoformat(),
            instruction="Stay indoors, avoid flooded streets, and watch official civil defense updates.",
            description="Demo alert for Hanauta test mode.",
            response="Shelter",
            web="https://www.gov.br/defesacivil",
            icon_name="thunderstorms",
            contact_number="199 / 193",
            color="",
        ),
        CapAlert(
            identifier="test-jp-1",
            event="Heavy Rain Emergency Warning",
            headline="Very heavy rainfall may trigger flash flooding and landslides.",
            severity="Extreme",
            urgency="Immediate",
            certainty="Observed",
            area_desc="Kansai region, Japan",
            sender_name="Japan Meteorological Agency Demo Feed",
            sent=now.isoformat(),
            effective=now.isoformat(),
            expires=(now + timedelta(hours=6)).isoformat(),
            instruction="Move to higher ground or a designated shelter immediately.",
            description="Demo alert for Hanauta test mode.",
            response="Evacuate",
            web="https://www.jma.go.jp/jma/indexe.html",
            icon_name="overcast-rain",
            contact_number="119 / 110",
            color="",
        ),
        CapAlert(
            identifier="test-us-1",
            event="Flash Flood Warning",
            headline="Rapid flooding is possible in low-lying roads and creeks.",
            severity="Severe",
            urgency="Immediate",
            certainty="Observed",
            area_desc="Texas, United States",
            sender_name="National Weather Service Demo Feed",
            sent=now.isoformat(),
            effective=now.isoformat(),
            expires=(now + timedelta(hours=2)).isoformat(),
            instruction="Turn around, don't drown. Move to higher ground immediately.",
            description="Demo alert for Hanauta test mode.",
            response="Avoid",
            web="https://www.weather.gov/alerts",
            icon_name="overcast-rain",
            contact_number="911",
            color="",
        ),
    ]
    count = random.randint(1, min(3, len(samples)))
    alerts = random.sample(samples, count)
    alerts.sort(key=lambda item: (-SEVERITY_RANK.get(item.severity.lower(), 0), item.event.lower()))
    _DEMO_CACHE = list(alerts)
    _DEMO_CACHE_EXPIRES = now + timedelta(minutes=10)
    return list(alerts)


def top_alert(alerts: list[CapAlert]) -> CapAlert | None:
    return alerts[0] if alerts else None


def relative_expiry(alert: CapAlert) -> str:
    raw = alert.expires or alert.effective or alert.sent
    if not raw:
        return ""
    normalized = raw.replace("Z", "+00:00").replace(" ", "T")
    try:
        moment = datetime.fromisoformat(normalized)
    except Exception:
        return ""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    now = datetime.now(moment.tzinfo)
    delta = moment - now
    minutes = int(delta.total_seconds() // 60)
    if minutes <= 0:
        return "Ending now"
    if minutes < 60:
        return f"Ends in {minutes} min"
    hours = minutes // 60
    if hours < 24:
        return f"Ends in {hours}h"
    days = hours // 24
    return f"Ends in {days}d"


def fallback_tip(alert: CapAlert) -> str:
    lowered = alert.event.lower()
    if "thunder" in lowered or "tornado" in lowered or "tempestade" in lowered or "granizo" in lowered:
        return "Move indoors, stay away from windows, and monitor official local instructions."
    if "flood" in lowered or "chuva" in lowered or "alag" in lowered:
        return "Move to higher ground immediately and never drive through flood waters."
    if "wind" in lowered or "hurricane" in lowered or "tropical" in lowered or "vento" in lowered or "vendaval" in lowered:
        return "Shelter away from windows, secure loose objects, and follow official evacuation guidance."
    if "snow" in lowered or "ice" in lowered or "blizzard" in lowered or "neve" in lowered or "geada" in lowered:
        return "Avoid unnecessary travel, keep charged devices nearby, and prepare for outages."
    if "heat" in lowered or "calor" in lowered:
        return "Hydrate, limit exertion, and check on vulnerable people nearby."
    if "fire" in lowered or "incendio" in lowered or "incêndio" in lowered:
        return "Be ready to leave quickly, follow evacuation orders, and watch official fire updates."
    return "Follow official alert instructions and call emergency services if you are in immediate danger."
