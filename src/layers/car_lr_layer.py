from PySide6 import QtWidgets, QtGui, QtCore
import time
from layers.base_layer import BaseLayer


class CarLRLayer(BaseLayer):
    def __init__(self, app, layer_id="car_lr", title="Car Left/Right", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        # Estado interno
        self.near_cars = []
        self.alpha = 200
        self.color = QtGui.QColor("#FFD800")
        self.editing_overlay = False

        # Alturas animadas
        self.current_heights = {"left": 0, "right": 0}
        self.target_heights = {"left": 0, "right": 0}

        # Controle de tempo para animação
        self._last_time = time.time()

        # Timer mais lento (10 FPS) só para checar animação
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(100)

        self.show()

    # ---------------- Atualização do iRacing ----------------
    def update_from_iracing(self, packet):
        if self.editing_overlay:
            return

        car_lr = packet.get("car_lr", {})
        new_near_cars = car_lr.get("cars", [])

        if new_near_cars != self.near_cars:
            self.near_cars = new_near_cars
            self._update_targets()
            self.update()  # redesenha só se mudou

    # ---------------- Ajuste de targets ----------------
    def _update_targets(self):
        rect = self.rect()
        self.target_heights = {"left": 0, "right": 0}

        for car in self.near_cars:
            side = car.get("side", "clear")
            gap_m = abs(car.get("gap_m", 50))
            intensity = max(0.1, 1.0 - (gap_m / 50.0))
            bar_height = int(rect.height() * intensity)

            if side in ("left", "both"):
                self.target_heights["left"] = max(self.target_heights["left"], bar_height)
            if side in ("right", "both"):
                self.target_heights["right"] = max(self.target_heights["right"], bar_height)

    # ---------------- Animação suave (delta-time) ----------------
    def update_animation(self):
        now = time.time()
        dt = now - self._last_time
        self._last_time = now

        changed = False
        speed = 6.0  # maior = mais rápido

        for side in ("left", "right"):
            current = self.current_heights[side]
            target = self.target_heights[side]
            new_value = current + (target - current) * min(1, dt * speed)

            if abs(new_value - current) > 0.5:  # mudança perceptível
                self.current_heights[side] = new_value
                changed = True

        if changed or self.editing_overlay:
            self.update()  # só redesenha se necessário

    # ---------------- Desenho ----------------
    def paintEvent(self, event):
        if not self.near_cars and not self.editing_overlay:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        rect = self.rect()
        bar_width = 8

        # Barras reais
        if not self.editing_overlay:
            color = QtGui.QColor(self.color)
            color.setAlpha(self.alpha)
            painter.setBrush(color)
            painter.setPen(QtCore.Qt.NoPen)

            if self.current_heights["left"] > 1:
                left_rect = QtCore.QRect(
                    0, rect.height() - int(self.current_heights["left"]),
                    bar_width, int(self.current_heights["left"])
                )
                painter.drawRect(left_rect)

            if self.current_heights["right"] > 1:
                right_rect = QtCore.QRect(
                    rect.width() - bar_width, rect.height() - int(self.current_heights["right"]),
                    bar_width, int(self.current_heights["right"])
                )
                painter.drawRect(right_rect)

        # Caixa e barras de exemplo no modo edição
        if self.editing_overlay:
            overlay_color = QtGui.QColor(255, 255, 255, 40)
            painter.setBrush(overlay_color)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 2, QtCore.Qt.DashLine))
            painter.drawRect(rect)

            painter.setBrush(QtGui.QColor(self.color.red(), self.color.green(), self.color.blue(), self.alpha))
            left_rect = QtCore.QRect(0, rect.height() - 80, bar_width, 80)
            right_rect = QtCore.QRect(rect.width() - bar_width, rect.height() - 140, bar_width, 140)
            painter.drawRect(left_rect)
            painter.drawRect(right_rect)

        painter.end()

    # ---------------- Modo edição ----------------
    def set_edit_mode(self, editing: bool):
        super().set_edit_mode(editing)
        self.editing_overlay = editing
        self.update()
