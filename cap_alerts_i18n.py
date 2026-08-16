from __future__ import annotations

import json
import locale
import os
from pathlib import Path

DEFAULT_LOCALE = "en-US"
LOCALES_DIR = Path(__file__).resolve().parent / "locales"

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "en-US": {
        "service.show_alert_chip.title": "Show alert chip on bar",
        "service.show_alert_chip.description": "Displays a warning chip on the bar when active alerts affect your saved location.",
        "service.demo_alert_chip.title": "Demo alert chip",
        "service.demo_alert_chip.description": "Use sample alert data to test the chip and popup behavior.",
        "service.status": "Uses your saved shared location for live alerts. If you use a VPN, save your real region here so alerts stay accurate.",
        "service.name": "CAP Alerts",
        "service.description": "Official active local alerts surfaced as a warning chip on the bar.",
        "alert.expiry.now": "Ending now",
        "alert.expiry.minutes": "Ends in {count} min",
        "alert.expiry.hours": "Ends in {count}h",
        "alert.expiry.days": "Ends in {count}d",
        "alert.severity.extreme": "Extreme",
        "alert.severity.severe": "Severe",
        "alert.severity.moderate": "Moderate",
        "alert.severity.minor": "Minor",
        "alert.severity.unknown": "Unknown",
        "alert.urgency.immediate": "Immediate",
        "alert.urgency.expected": "Expected",
        "alert.urgency.future": "Future",
        "alert.urgency.past": "Past",
        "alert.urgency.unknown": "Unknown",
        "alert.fallback.thunder": "Move indoors, stay away from windows, and monitor official local instructions.",
        "alert.fallback.flood": "Move to higher ground immediately and never drive through flood waters.",
        "alert.fallback.wind": "Shelter away from windows, secure loose objects, and follow official evacuation guidance.",
        "alert.fallback.snow": "Avoid unnecessary travel, keep charged devices nearby, and prepare for outages.",
        "alert.fallback.heat": "Hydrate, limit exertion, and check on vulnerable people nearby.",
        "alert.fallback.fire": "Be ready to leave quickly, follow evacuation orders, and watch official fire updates.",
        "alert.fallback.default": "Follow official alert instructions and call emergency services if you are in immediate danger.",
        "popup.eyebrow": "CAP ALERTS",
        "popup.title": "Official local alerts",
        "popup.subtitle": "Helpful info, contacts, and official alert guidance.",
        "popup.loading": "Loading official alerts…",
        "popup.no_alerts_title": "No active official alerts",
        "popup.no_alerts_hero": "No current alert bulletin",
        "popup.no_alerts_demo": "Demo mode is enabled but no sample alerts were generated.",
        "popup.no_alerts_live": "No active official alerts for {label}.",
        "popup.active_alerts": "{count} active alert(s)",
        "popup.demo_feed": "Demo feed",
        "popup.live_feed": "Live feed",
        "popup.demo_status": "Demo mode is enabled. These are sample alerts from random countries for UI testing.",
        "popup.live_status": "Official alerts affecting {label}.",
        "popup.no_location": "Choose a shared location in Region settings first.",
        "popup.open_official": "Open official alert",
        "popup.refresh": "Refresh alerts",
        "popup.close": "Close",
        "popup.contact_source": "Source: {source}",
        "popup.contact_emergency": "Emergency: {contact}",
        "popup.contact_official": "Official bulletin: {url}",
        "overlay.official_alert": "OFFICIAL ALERT",
        "overlay.affected_area": "Affected Area",
        "overlay.what_to_do": "What To Do Right Now",
        "overlay.emergency_contact": "Emergency Contact",
        "overlay.official_bulletin": "Official Bulletin",
        "overlay.details_hint": "Open the detailed alert popup for the official source link.",
        "overlay.dismiss": "Dismiss",
        "overlay.open_details": "Open Details",
        "overlay.region_settings": "Region Settings",
        "overlay.title_default": "Weather Alert",
        "overlay.headline_default": "Official alert received.",
        "overlay.tip_default": "Follow official safety guidance.",
        "overlay.contact_default": "Official local emergency services",
        "overlay.details_window": "Hanauta CAP Alert",
    },
    "pt-BR": {
        "service.show_alert_chip.title": "Mostrar chip de alerta na barra",
        "service.show_alert_chip.description": "Exibe um chip de aviso na barra quando alertas ativos afetarem sua localidade salva.",
        "service.demo_alert_chip.title": "Chip de alerta de demonstração",
        "service.demo_alert_chip.description": "Use dados de exemplo para testar o chip e o popup.",
        "service.status": "Usa sua localidade compartilhada salva para alertas ao vivo. Se você usa VPN, salve sua região real aqui para manter os alertas corretos.",
        "service.name": "Alertas CAP",
        "service.description": "Alertas oficiais locais ativos exibidos como um chip de aviso na barra.",
        "alert.expiry.now": "Encerrando agora",
        "alert.expiry.minutes": "Termina em {count} min",
        "alert.expiry.hours": "Termina em {count}h",
        "alert.expiry.days": "Termina em {count}d",
        "alert.severity.extreme": "Extremo",
        "alert.severity.severe": "Severo",
        "alert.severity.moderate": "Moderado",
        "alert.severity.minor": "Menor",
        "alert.severity.unknown": "Desconhecido",
        "alert.urgency.immediate": "Imediato",
        "alert.urgency.expected": "Esperado",
        "alert.urgency.future": "Futuro",
        "alert.urgency.past": "Passado",
        "alert.urgency.unknown": "Desconhecido",
        "alert.fallback.thunder": "Vá para um local coberto, afaste-se de janelas e acompanhe as instruções oficiais locais.",
        "alert.fallback.flood": "Procure terreno mais alto imediatamente e nunca dirija em áreas alagadas.",
        "alert.fallback.wind": "Proteja-se longe das janelas, prenda objetos soltos e siga a orientação oficial de evacuação.",
        "alert.fallback.snow": "Evite deslocamentos desnecessários, mantenha dispositivos carregados e prepare-se para quedas de energia.",
        "alert.fallback.heat": "Hidrate-se, limite esforço físico e verifique pessoas vulneráveis por perto.",
        "alert.fallback.fire": "Esteja pronto para sair rapidamente, siga ordens de evacuação e acompanhe atualizações oficiais sobre incêndios.",
        "alert.fallback.default": "Siga as instruções oficiais do alerta e ligue para os serviços de emergência se estiver em perigo imediato.",
        "popup.eyebrow": "ALERTAS CAP",
        "popup.title": "Alertas oficiais locais",
        "popup.subtitle": "Informações úteis, contatos e orientações oficiais do alerta.",
        "popup.loading": "Carregando alertas oficiais…",
        "popup.no_alerts_title": "Nenhum alerta oficial ativo",
        "popup.no_alerts_hero": "Nenhum boletim de alerta no momento",
        "popup.no_alerts_demo": "O modo de demonstração está ativado, mas nenhum alerta de exemplo foi gerado.",
        "popup.no_alerts_live": "Nenhum alerta oficial ativo para {label}.",
        "popup.active_alerts": "{count} alerta(s) ativo(s)",
        "popup.demo_feed": "Feed de demonstração",
        "popup.live_feed": "Feed ao vivo",
        "popup.demo_status": "O modo de demonstração está ativado. Estes são alertas de exemplo de países aleatórios para testes da interface.",
        "popup.live_status": "Alertas oficiais que afetam {label}.",
        "popup.no_location": "Escolha primeiro uma localidade compartilhada em Configurações da Região.",
        "popup.open_official": "Abrir alerta oficial",
        "popup.refresh": "Atualizar alertas",
        "popup.close": "Fechar",
        "popup.contact_source": "Fonte: {source}",
        "popup.contact_emergency": "Emergência: {contact}",
        "popup.contact_official": "Boletim oficial: {url}",
        "overlay.official_alert": "ALERTA OFICIAL",
        "overlay.affected_area": "Área Afetada",
        "overlay.what_to_do": "O que fazer agora",
        "overlay.emergency_contact": "Contato de emergência",
        "overlay.official_bulletin": "Boletim oficial",
        "overlay.details_hint": "Abra o popup detalhado do alerta para ver o link oficial.",
        "overlay.dismiss": "Fechar",
        "overlay.open_details": "Abrir detalhes",
        "overlay.region_settings": "Configurações da região",
        "overlay.title_default": "Alerta meteorológico",
        "overlay.headline_default": "Alerta oficial recebido.",
        "overlay.tip_default": "Siga as orientações oficiais de segurança.",
        "overlay.contact_default": "Serviços locais oficiais de emergência",
        "overlay.details_window": "Hanauta CAP Alert",
    },
    "ru-RU": {
        "service.show_alert_chip.title": "Показывать чип тревоги на панели",
        "service.show_alert_chip.description": "Показывает предупреждающий чип на панели, когда активные оповещения затрагивают сохранённую локацию.",
        "service.demo_alert_chip.title": "Демо-чип тревоги",
        "service.demo_alert_chip.description": "Используйте тестовые данные оповещений для проверки чипа и всплывающего окна.",
        "service.status": "Использует сохранённую общую локацию для живых оповещений. Если вы используете VPN, сохраните здесь реальный регион, чтобы оповещения были точными.",
        "service.name": "Оповещения CAP",
        "service.description": "Активные официальные локальные оповещения показываются на панели как предупреждающий чип.",
        "alert.expiry.now": "Завершается сейчас",
        "alert.expiry.minutes": "Закончится через {count} мин",
        "alert.expiry.hours": "Закончится через {count} ч",
        "alert.expiry.days": "Закончится через {count} дн.",
        "alert.severity.extreme": "Экстремальная",
        "alert.severity.severe": "Серьёзная",
        "alert.severity.moderate": "Умеренная",
        "alert.severity.minor": "Незначительная",
        "alert.severity.unknown": "Неизвестно",
        "alert.urgency.immediate": "Немедленно",
        "alert.urgency.expected": "Ожидается",
        "alert.urgency.future": "В будущем",
        "alert.urgency.past": "Прошло",
        "alert.urgency.unknown": "Неизвестно",
        "alert.fallback.thunder": "Перейдите в помещение, держитесь подальше от окон и следите за официальными местными инструкциями.",
        "alert.fallback.flood": "Немедленно перейдите на возвышенность и никогда не проезжайте через паводковую воду.",
        "alert.fallback.wind": "Укройтесь вдали от окон, закрепите незакреплённые предметы и следуйте официальным указаниям по эвакуации.",
        "alert.fallback.snow": "Избегайте необязательных поездок, держите устройства заряженными и подготовьтесь к перебоям с электричеством.",
        "alert.fallback.heat": "Пейте воду, ограничьте нагрузку и проверьте уязвимых людей рядом.",
        "alert.fallback.fire": "Будьте готовы быстро уйти, выполняйте приказы об эвакуации и следите за официальными пожарными сводками.",
        "alert.fallback.default": "Следуйте официальным инструкциям тревоги и звоните в экстренные службы, если вам угрожает непосредственная опасность.",
        "popup.eyebrow": "CAP ALERTS",
        "popup.title": "Официальные локальные оповещения",
        "popup.subtitle": "Полезная информация, контакты и официальные рекомендации по тревоге.",
        "popup.loading": "Загрузка официальных оповещений…",
        "popup.no_alerts_title": "Нет активных официальных оповещений",
        "popup.no_alerts_hero": "Сейчас нет бюллетеня тревоги",
        "popup.no_alerts_demo": "Режим демо включён, но тестовые оповещения не были сгенерированы.",
        "popup.no_alerts_live": "Для {label} нет активных официальных оповещений.",
        "popup.active_alerts": "{count} активных оповещений",
        "popup.demo_feed": "Демо-канал",
        "popup.live_feed": "Живой канал",
        "popup.demo_status": "Включён демо-режим. Это тестовые оповещения из случайных стран для проверки интерфейса.",
        "popup.live_status": "Официальные оповещения для {label}.",
        "popup.no_location": "Сначала выберите общую локацию в настройках региона.",
        "popup.open_official": "Открыть официальное оповещение",
        "popup.refresh": "Обновить оповещения",
        "popup.close": "Закрыть",
        "popup.contact_source": "Источник: {source}",
        "popup.contact_emergency": "Экстренно: {contact}",
        "popup.contact_official": "Официальный бюллетень: {url}",
        "overlay.official_alert": "ОФИЦИАЛЬНОЕ ОПОВЕЩЕНИЕ",
        "overlay.affected_area": "Затронутая область",
        "overlay.what_to_do": "Что делать сейчас",
        "overlay.emergency_contact": "Экстренный контакт",
        "overlay.official_bulletin": "Официальный бюллетень",
        "overlay.details_hint": "Откройте подробное всплывающее окно тревоги, чтобы увидеть официальную ссылку.",
        "overlay.dismiss": "Закрыть",
        "overlay.open_details": "Открыть детали",
        "overlay.region_settings": "Настройки региона",
        "overlay.title_default": "Погодное оповещение",
        "overlay.headline_default": "Получено официальное оповещение.",
        "overlay.tip_default": "Следуйте официальным рекомендациям по безопасности.",
        "overlay.contact_default": "Местные официальные службы экстренной помощи",
        "overlay.details_window": "Hanauta CAP Alert",
    },
    "es-AR": {
        "service.show_alert_chip.title": "Mostrar chip de alerta en la barra",
        "service.show_alert_chip.description": "Muestra un chip de advertencia en la barra cuando las alertas activas afectan tu ubicación guardada.",
        "service.demo_alert_chip.title": "Chip de alerta de prueba",
        "service.demo_alert_chip.description": "Usa datos de alerta de ejemplo para probar el chip y el popup.",
        "service.status": "Usa tu ubicación compartida guardada para alertas en vivo. Si usas VPN, guarda tu región real aquí para que las alertas sean precisas.",
        "service.name": "Alertas CAP",
        "service.description": "Alertas oficiales locales activas mostradas como un chip de advertencia en la barra.",
        "alert.expiry.now": "Terminando ahora",
        "alert.expiry.minutes": "Termina en {count} min",
        "alert.expiry.hours": "Termina en {count} h",
        "alert.expiry.days": "Termina en {count} d",
        "alert.severity.extreme": "Extrema",
        "alert.severity.severe": "Severa",
        "alert.severity.moderate": "Moderada",
        "alert.severity.minor": "Menor",
        "alert.severity.unknown": "Desconocida",
        "alert.urgency.immediate": "Inmediata",
        "alert.urgency.expected": "Esperada",
        "alert.urgency.future": "Futura",
        "alert.urgency.past": "Pasada",
        "alert.urgency.unknown": "Desconocida",
        "alert.fallback.thunder": "Entrá bajo techo, alejate de las ventanas y seguí las instrucciones oficiales locales.",
        "alert.fallback.flood": "Buscá terreno alto de inmediato y nunca manejes por zonas inundadas.",
        "alert.fallback.wind": "Refugiate lejos de las ventanas, asegurá objetos sueltos y seguí la guía oficial de evacuación.",
        "alert.fallback.snow": "Evitá viajes innecesarios, mantené los dispositivos cargados y preparate para cortes de energía.",
        "alert.fallback.heat": "Hidratate, limitá el esfuerzo físico y verificá a personas vulnerables cercanas.",
        "alert.fallback.fire": "Preparáte para salir rápido, seguí órdenes de evacuación y mirá actualizaciones oficiales sobre incendios.",
        "alert.fallback.default": "Seguí las instrucciones oficiales de la alerta y llamá a emergencias si estás en peligro inmediato.",
        "popup.eyebrow": "ALERTAS CAP",
        "popup.title": "Alertas oficiales locales",
        "popup.subtitle": "Información útil, contactos y guía oficial de alertas.",
        "popup.loading": "Cargando alertas oficiales…",
        "popup.no_alerts_title": "No hay alertas oficiales activas",
        "popup.no_alerts_hero": "No hay boletín de alerta ahora",
        "popup.no_alerts_demo": "El modo de prueba está activado, pero no se generaron alertas de ejemplo.",
        "popup.no_alerts_live": "No hay alertas oficiales activas para {label}.",
        "popup.active_alerts": "{count} alerta(s) activa(s)",
        "popup.demo_feed": "Canal de prueba",
        "popup.live_feed": "Canal en vivo",
        "popup.demo_status": "El modo de prueba está activado. Estas son alertas de ejemplo de países aleatorios para probar la UI.",
        "popup.live_status": "Alertas oficiales que afectan a {label}.",
        "popup.no_location": "Primero elegí una ubicación compartida en Configuración de Región.",
        "popup.open_official": "Abrir alerta oficial",
        "popup.refresh": "Actualizar alertas",
        "popup.close": "Cerrar",
        "popup.contact_source": "Fuente: {source}",
        "popup.contact_emergency": "Emergencia: {contact}",
        "popup.contact_official": "Boletín oficial: {url}",
        "overlay.official_alert": "ALERTA OFICIAL",
        "overlay.affected_area": "Área afectada",
        "overlay.what_to_do": "Qué hacer ahora",
        "overlay.emergency_contact": "Contacto de emergencia",
        "overlay.official_bulletin": "Boletín oficial",
        "overlay.details_hint": "Abrí el popup detallado de la alerta para ver el enlace oficial.",
        "overlay.dismiss": "Cerrar",
        "overlay.open_details": "Abrir detalles",
        "overlay.region_settings": "Configuración de región",
        "overlay.title_default": "Alerta meteorológica",
        "overlay.headline_default": "Se recibió una alerta oficial.",
        "overlay.tip_default": "Seguí las indicaciones oficiales de seguridad.",
        "overlay.contact_default": "Servicios locales oficiales de emergencia",
        "overlay.details_window": "Hanauta CAP Alert",
    },
}


def _load_locale_files() -> None:
    if not LOCALES_DIR.exists():
        return
    for path in sorted(LOCALES_DIR.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        locale_name = normalize_locale(path.stem)
        strings = {str(key): str(value) for key, value in payload.items()}
        _TRANSLATIONS.setdefault(locale_name, {}).update(strings)

_ALIASES = {
    "en": "en-US",
    "en-us": "en-US",
    "en_us": "en-US",
    "pt": "pt-BR",
    "pt-br": "pt-BR",
    "ptbr": "pt-BR",
    "pt_br": "pt-BR",
    "ru": "ru-RU",
    "ru-ru": "ru-RU",
    "ruru": "ru-RU",
    "ru_ru": "ru-RU",
    "es": "es-AR",
    "es-ar": "es-AR",
    "esar": "es-AR",
    "es_ar": "es-AR",
}


def normalize_locale(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return DEFAULT_LOCALE
    key = raw.replace("_", "-")
    alias = _ALIASES.get(key.lower())
    if alias:
        return alias
    if len(key) == 2:
        return _ALIASES.get(key.lower(), DEFAULT_LOCALE)
    return key


def current_locale() -> str:
    env = os.environ.get("HANAUTA_LOCALE") or os.environ.get("LANG") or ""
    if env:
        env = env.split(".", 1)[0]
    try:
        system_locale = locale.getdefaultlocale()[0] or ""
    except Exception:
        system_locale = ""
    return normalize_locale(env or system_locale or DEFAULT_LOCALE)


def tr(key: str, locale_name: str | None = None, **kwargs: object) -> str:
    language = normalize_locale(locale_name or current_locale())
    text = _TRANSLATIONS.get(language, {}).get(key)
    if text is None:
        text = _TRANSLATIONS[DEFAULT_LOCALE].get(key, key)
    try:
        return text.format(**kwargs)
    except Exception:
        return text


def has_translation(key: str, locale_name: str | None = None) -> bool:
    language = normalize_locale(locale_name or current_locale())
    return key in _TRANSLATIONS.get(language, {}) or key in _TRANSLATIONS[DEFAULT_LOCALE]


_load_locale_files()
