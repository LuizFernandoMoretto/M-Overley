from PySide6 import QtWidgets, QtGui, QtCore
from layers.base_layer import BaseLayer


class CarLRLayer(BaseLayer):
    def __init__(self, app, layer_id="car_lr", title="Car Left/Right", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.near_cars = []
        self.alpha = 200
        self.color = QtGui.QColor("#FFD800")

        # Atualização periódica (20fps)
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.hide()

    def update_from_iracing(self, packet):
        """Atualiza dados recebidos do iRacing"""
        car_lr = packet.get("car_lr", {})
        self.near_cars = car_lr.get("cars", [])

        if not self.near_cars:
            self.hide()
        else:
            self.show()
            self.update()

    def paintEvent(self, event):
        if not self.near_cars:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()

        bar_width = 8

        for car in self.near_cars:
            side = car.get("side", "clear")
            gap_m = abs(car.get("gap_m", 50))

            # Quanto mais perto, maior a barra (0m = altura total, 50m = 10%)
            intensity = max(0.1, 1.0 - (gap_m / 50.0))
            bar_height = int(rect.height() * intensity)

            color = QtGui.QColor(self.color)
            color.setAlpha(self.alpha)
            painter.setBrush(color)
            painter.setPen(QtCore.Qt.NoPen)

            if side in ("left", "both"):
                left_rect = QtCore.QRect(0, rect.height() - bar_height, bar_width, bar_height)
                painter.drawRect(left_rect)

            if side in ("right", "both"):
                right_rect = QtCore.QRect(rect.width() - bar_width, rect.height() - bar_height, bar_width, bar_height)
                painter.drawRect(right_rect)

        painter.end()

    def set_edit_mode(self, editing: bool):
        super().set_edit_mode(editing)

        if editing:
            # 🔹 Sempre mostra exemplo para editar
            self.near_cars = [
                {"side": "left", "gap_m": 10},
                {"side": "right", "gap_m": 25}
            ]
            self.show()
            self.update()
        else:
            # 🔹 Volta para o estado real (depende do iRacing)
            self.near_cars = []
            self.update()
