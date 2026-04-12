#!/usr/bin/env python3
from __future__ import annotations

import math
import types

from PyQt6.QtGui import QColor

SERVICE_KEY = "cap_alerts"


def _rgba(color: str, alpha: float) -> str:
    q = QColor(color)
    q.setAlphaF(max(0.0, min(1.0, float(alpha))))
    return q.name(QColor.NameFormat.HexArgb)


def _chip_radius(window) -> int:
    bar = getattr(window, "bar_settings", {}) or {}
    return max(8, int(bar.get("chip_radius", 0) or 0))


def _patch_cap_alert_visuals(window) -> None:
    if getattr(window, "_cap_alert_plugin_patch_applied", False):
        return

    if not hasattr(window, "_apply_cap_alert_chip_style") or not hasattr(
        window, "_tick_cap_alert_pulse"
    ):
        return

    window._cap_alert_plugin_patch_applied = True

    def _apply_cap_alert_chip_style(self, accent: str) -> None:
        text_color = "#101114" if QColor(accent).lightnessF() > 0.62 else "#FFF9E8"
        warning_color = accent if QColor(accent).lightnessF() <= 0.82 else "#C99200"
        radius = _chip_radius(self)
        self.cap_alert_chip.setStyleSheet(
            f"""
            QFrame#capAlertChip {{
                background: {_rgba(accent, 0.30)};
                border: 1px solid {_rgba(accent, 0.58)};
                border-radius: {radius}px;
            }}
            QFrame#capAlertChip:hover {{
                background: {_rgba(accent, 0.38)};
                border: 1px solid {_rgba(accent, 0.76)};
                border-radius: {radius}px;
            }}
            """
        )
        self.cap_alert_warning.setStyleSheet(
            f'color: {warning_color}; font-family: "{self.material_font}"; font-size: 17px;'
        )
        self.cap_alert_text.setStyleSheet(
            f"color: {text_color}; font-size: 11px; font-weight: 700;"
        )

    def _tick_cap_alert_pulse(self) -> None:
        if not self.cap_alert_chip.isVisible():
            self.cap_alert_glow_frame.hide()
            self.cap_alert_warning_opacity.setOpacity(1.0)
            return
        self._cap_alert_pulse_tick = (self._cap_alert_pulse_tick + 1) % 360
        phase = self._cap_alert_pulse_tick / 18.0
        alpha = 0.20 + (0.30 * ((math.sin(phase) + 1.0) / 2.0))
        width = 2 if math.sin(phase * 1.2) < 0.35 else 3
        icon_phase = self._cap_alert_pulse_tick / 6.0
        icon_alpha = 0.20 + (0.80 * ((math.sin(icon_phase) + 1.0) / 2.0))
        self.cap_alert_warning_opacity.setOpacity(icon_alpha)
        radius = _chip_radius(self)
        self.cap_alert_glow_frame.setStyleSheet(
            f"background: transparent; border: {width}px solid {_rgba(self._cap_alert_accent, alpha)}; border-radius: {radius}px;"
        )
        self.cap_alert_glow_frame.setGeometry(self.cap_alert_chip.rect())
        self.cap_alert_glow_frame.show()

    window._apply_cap_alert_chip_style = types.MethodType(
        _apply_cap_alert_chip_style, window
    )
    window._tick_cap_alert_pulse = types.MethodType(_tick_cap_alert_pulse, window)


def register_hanauta_bar_plugin(window, api: dict[str, object]) -> None:
    _patch_cap_alert_visuals(window)
    register_hook = api.get("register_hook")
    if callable(register_hook):
        register_hook("settings_reloaded", lambda: _patch_cap_alert_visuals(window))
