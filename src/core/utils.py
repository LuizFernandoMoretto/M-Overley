from __future__ import annotations
from PySide6 import QtCore, QtWidgets

def screen_size(widget: QtWidgets.QWidget) -> tuple[int,int]:
    scr = widget.screen() or QtWidgets.QApplication.primaryScreen()
    s = scr.size()
    return s.width(), s.height()

def normalize_geom(widget: QtWidgets.QWidget, rect) -> dict:
    sw, sh = screen_size(widget)
    return {
        "x": rect.x()/sw,
        "y": rect.y()/sh,
        "w": rect.width()/sw,
        "h": rect.height()/sh
    }

def denormalize_geom(widget: QtWidgets.QWidget, data: dict) -> QtCore.QRect:
    sw, sh = screen_size(widget)
    return QtCore.QRect(
        int(data["x"]*sw), int(data["y"]*sh),
        max(50, int(data["w"]*sw)), max(30, int(data["h"]*sh))
    )
