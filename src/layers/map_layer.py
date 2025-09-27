from layers.base_layer import BaseLayer
from PySide6 import QtCore, QtGui
import math

class MapLayer(BaseLayer):
    def __init__(self, app, layer_id='map', title='Track Map', initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        self.cars = [{"angle": i*36} for i in range(10)]
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_positions)
        self.timer.start(200)

    def update_positions(self):
        for c in self.cars:
            c["angle"] = (c["angle"] + 2) % 360
        self.update()

    def paintEvent(self, e: QtGui.QPaintEvent):
        super().paintEvent(e)
        p = QtGui.QPainter(self)
        p.setRenderHint(QtGui.QPainter.Antialiasing, True)

        rect = self.rect().adjusted(20, 40, -20, -20)
        center = rect.center()
        radius = min(rect.width(), rect.height()) // 2 - 10

        # pista circular
        p.setPen(QtGui.QPen(QtGui.QColor("white"), 2))
        p.drawEllipse(center, radius, radius)

        # carros
        for i, c in enumerate(self.cars):
            angle_rad = math.radians(c["angle"])
            x = center.x() + int(radius * math.cos(angle_rad))
            y = center.y() + int(radius * math.sin(angle_rad))
            color = QtGui.QColor("red") if i == 0 else QtGui.QColor("cyan")
            p.setBrush(color)
            p.setPen(QtCore.Qt.NoPen)
            p.drawEllipse(QtCore.QPoint(x, y), 6, 6)
