from PySide6 import QtWidgets, QtGui, QtCore
from layers.base_layer import BaseLayer
from core.config_store import ConfigStore


class CarLRLayer(BaseLayer):
    def __init__(self, app, layer_id="car_lr", title="Car L/R", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        # Configuração com persistência
        self.cfg_store = ConfigStore()
        saved_cfg = self.cfg_store.load_layer_config(layer_id)

        self.box_size = saved_cfg.get("box_size", 70)
        self.left_active = False
        self.right_active = False

        # Timer de redraw rápido (50ms = 20fps)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update_from_iracing(self, data: dict):
        """Recebe dados do iRacing via OverlayApp"""
        val = data.get("car_lr", {}).get("val", 0)

        self.left_active = False
        self.right_active = False

        if val in (2,):      # Car Left
            self.left_active = True
        elif val in (3,):    # Car Right
            self.right_active = True
        elif val in (4,):    # Both sides
            self.left_active = True
            self.right_active = True

        #print(f"[CarLRLayer] update_from_iracing: val={val} -> L={self.left_active} R={self.right_active}")
        self.update()

    # -------------------
    # Desenho customizado
    # -------------------
    def _draw_box(self, painter, x, y, size, active, color1, color2):
        rect = QtCore.QRectF(x, y, size, size)

        # Gradiente radial (efeito glow no centro)
        gradient = QtGui.QRadialGradient(rect.center(), size / 1.5)
        if active:
            gradient.setColorAt(0, QtGui.QColor(color1))
            gradient.setColorAt(1, QtGui.QColor(color2))
        else:
            off_col = QtGui.QColor(color1)
            off_col.setAlpha(40)
            gradient.setColorAt(0, off_col)
            gradient.setColorAt(1, QtGui.QColor(0, 0, 0, 0))

        painter.setBrush(QtGui.QBrush(gradient))

        # Glow extra na borda quando ativo
        pen = QtGui.QPen(QtGui.QColor(color1), 3 if active else 1)
        pen.setCosmetic(True)
        painter.setPen(pen)

        # Desenha com bordas arredondadas (pill/circle)
        painter.drawRoundedRect(rect, size/2, size/2)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing | QtGui.QPainter.SmoothPixmapTransform)

        w, h = self.width(), self.height()
        size = self.box_size
        margin = 12

        # Left → Amarelo
        self._draw_box(painter, margin, h//2 - size//2, size, self.left_active, "#fffb00", "#fbff00")

        # Right → Amarelo
        self._draw_box(painter, w - margin - size, h//2 - size//2, size, self.right_active, "#fffb00", "#fbff00")

    def save_config(self):
        self.cfg_store.save_layer_config(self.layer_id, {
            "box_size": self.box_size
        })
