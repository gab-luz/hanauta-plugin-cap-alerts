#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget

PLUGIN_ROOT = Path(__file__).resolve().parent
SERVICE_KEY = "cap_alerts"


def build_cap_alerts_service_section(window, api: dict[str, object]) -> QWidget:
    SettingsRow = api["SettingsRow"]
    SwitchButton = api["SwitchButton"]
    ExpandableServiceSection = api["ExpandableServiceSection"]
    material_icon = api["material_icon"]
    icon_path = str(api.get("plugin_icon_path", "")).strip()

    service = window.settings_state.setdefault("services", {}).setdefault(
        SERVICE_KEY,
        {
            "enabled": True,
            "show_in_bar": True,
            "test_mode": False,
        },
    )

    content = QWidget()
    layout = QVBoxLayout(content)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(10)

    bar_switch = SwitchButton(bool(service.get("show_in_bar", True)))
    bar_switch.toggledValue.connect(
        lambda enabled: window._set_service_bar_visibility(SERVICE_KEY, enabled)
    )
    window.service_display_switches[SERVICE_KEY] = bar_switch
    window.cap_alerts_bar_switch = bar_switch
    layout.addWidget(
        SettingsRow(
            material_icon("warning"),
            "Show alert chip on bar",
            "Displays a warning chip on the bar when active alerts affect your saved location.",
            window.icon_font,
            window.ui_font,
            bar_switch,
        )
    )

    test_mode_switch = SwitchButton(bool(service.get("test_mode", False)))
    test_mode_switch.toggledValue.connect(window._set_cap_alerts_test_mode)
    window.cap_alerts_test_mode_switch = test_mode_switch
    layout.addWidget(
        SettingsRow(
            material_icon("science"),
            "Demo alert chip",
            "Use sample alert data to test the chip and popup behavior.",
            window.icon_font,
            window.ui_font,
            test_mode_switch,
        )
    )

    window.cap_alerts_status = QLabel(
        "Uses your saved shared location for live alerts. If you use a VPN, save your real region here so alerts stay accurate."
    )
    window.cap_alerts_status.setWordWrap(True)
    window.cap_alerts_status.setStyleSheet("color: rgba(246,235,247,0.72);")
    layout.addWidget(window.cap_alerts_status)

    section = ExpandableServiceSection(
        SERVICE_KEY,
        "CAP Alerts",
        "Official active local alerts surfaced as a warning chip on the bar.",
        material_icon("warning"),
        window.icon_font,
        window.ui_font,
        content,
        window._service_enabled(SERVICE_KEY),
        lambda enabled: window._set_service_enabled(SERVICE_KEY, enabled),
        icon_path=icon_path,
    )
    window.service_sections[SERVICE_KEY] = section
    return section


def register_hanauta_plugin() -> dict[str, object]:
    return {
        "id": SERVICE_KEY,
        "name": "CAP Alerts",
        "api_min_version": 1,
        "service_sections": [
            {
                "key": SERVICE_KEY,
                "builder": build_cap_alerts_service_section,
                "supports_show_on_bar": True,
            }
        ],
    }
