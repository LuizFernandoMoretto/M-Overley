from PySide6 import QtWidgets, QtGui, QtCore
from layers.base_layer import BaseLayer
from core.config_store import ConfigStore


class CarLRLayer(BaseLayer):
    def __init__(self, app, layer_id="car_lr", title="Car L/R", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        # Configuração com persistência
        self.cfg_store = ConfigStore()
        saved_cfg = self.cfg_store.load_layer_config(layer_id)

        self.box_size = saved_cfg.get("box_size", 60)
        self.alpha_on = saved_cfg.get("alpha_on", 220)
        self.alpha_off = saved_cfg.get("alpha_off", 40)
        self.color = saved_cfg.get("color", "#ffff00")  # padrão: amarelo

        self.left_active = False
        self.right_active = False

        # Timer de redraw rápido (20fps)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

    def update_from_iracing(self, packet: dict):
        """Recebe dados do iRacing enviados pelo OverlayApp"""
        car_lr = packet.get("car_lr", {})
        val = car_lr.get("val", 0)

        # Reset
        self.left_active = False
        self.right_active = False

        # Decodificação dos valores
        if val in (2, 5):    # Carro à esquerda
            self.left_active = True
        elif val in (3, 6):  # Carro à direita
            self.right_active = True
        elif val == 4:       # Ambos os lados
            self.left_active = True
            self.right_active = True

        print(f"[CarLRLayer] update_from_iracing: val={val} -> L={self.left_active} R={self.right_active}")
        self.update()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHints(QtGui.QPainter.Antialiasing)

        w, h = self.width(), self.height()
        size = self.box_size
        margin = 10

        # Cor base
        col = QtGui.QColor(self.color)

        # Caixa esquerda
        col.setAlpha(self.alpha_on if self.left_active else self.alpha_off)
        painter.setBrush(col)
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawRect(margin, h // 2 - size // 2, size, size)

        # Caixa direita
        col.setAlpha(self.alpha_on if self.right_active else self.alpha_off)
        painter.setBrush(col)
        painter.drawRect(w - margin - size, h // 2 - size // 2, size, size)

    def save_config(self):
        self.cfg_store.save_layer_config(self.layer_id, {
            "box_size": self.box_size,
            "alpha_on": self.alpha_on,
            "alpha_off": self.alpha_off,
            "color": self.color
        })
