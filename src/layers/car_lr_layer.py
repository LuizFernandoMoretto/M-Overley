from PySide6 import QtWidgets, QtGui, QtCore
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

        # Atualização periódica
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(50)

        self.show()  # 🔹 garante que a camada abre sempre

    # ---------------- Atualização do iRacing ----------------
    def update_from_iracing(self, packet):
        if self.editing_overlay:
            print("[CarLRLayer] Ignorando update_from_iracing (modo edição ativo)")
            return

        car_lr = packet.get("car_lr", {})
        self.near_cars = car_lr.get("cars", [])

        print(f"[CarLRLayer] Pacote recebido do iRacing: {self.near_cars}")

        if not self.near_cars:
            print("[CarLRLayer] Nenhum carro próximo → limpando barras")
        self.update()

    # ---------------- Animação suave ----------------
    def update_animation(self):
        rect = self.rect()
        target_heights = {"left": 0, "right": 0}

        for car in self.near_cars:
            side = car.get("side", "clear")
            gap_m = abs(car.get("gap_m", 50))

            intensity = max(0.1, 1.0 - (gap_m / 50.0))
            bar_height = int(rect.height() * intensity)

            if side in ("left", "both"):
                target_heights["left"] = max(target_heights["left"], bar_height)
            if side in ("right", "both"):
                target_heights["right"] = max(target_heights["right"], bar_height)

        for side in ("left", "right"):
            self.current_heights[side] = int(
                self.current_heights[side] * 0.8 + target_heights[side] * 0.2
            )

        self.update()

    # ---------------- Desenho ----------------
    def paintEvent(self, event):
        rect = self.rect()

        # --- log apenas quando muda ---
        state = (rect.width(), rect.height(), tuple(self.near_cars), self.editing_overlay)
        if getattr(self, "_last_logged_state", None) != state:
            print(f"[CarLRLayer] paintEvent → size={rect.width()}x{rect.height()} near_cars={self.near_cars} editing={self.editing_overlay}")
            self._last_logged_state = state

        if not self.near_cars and not self.editing_overlay:
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        bar_width = 8

        # Barras reais
        if not self.editing_overlay:
            color = QtGui.QColor(self.color)
            color.setAlpha(self.alpha)
            painter.setBrush(color)
            painter.setPen(QtCore.Qt.NoPen)

            if self.current_heights["left"] > 0:
                left_rect = QtCore.QRect(
                    0, rect.height() - self.current_heights["left"], bar_width, self.current_heights["left"]
                )
                painter.drawRect(left_rect)

            if self.current_heights["right"] > 0:
                right_rect = QtCore.QRect(
                    rect.width() - bar_width, rect.height() - self.current_heights["right"], bar_width, self.current_heights["right"]
                )
                painter.drawRect(right_rect)

        # Caixa de edição com dados de teste
        if self.editing_overlay:
            overlay_color = QtGui.QColor(255, 255, 255, 40)
            painter.setBrush(overlay_color)
            painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255, 120), 2, QtCore.Qt.DashLine))
            painter.drawRect(rect)

            # desenha também barras de exemplo
            painter.setBrush(QtGui.QColor(self.color.red(), self.color.green(), self.color.blue(), self.alpha))
            left_rect = QtCore.QRect(0, rect.height() - 80, bar_width, 80)
            right_rect = QtCore.QRect(rect.width() - bar_width, rect.height() - 140, bar_width, 140)
            painter.drawRect(left_rect)
            painter.drawRect(right_rect)

        painter.end()


    # ---------------- Modo edição ----------------
    def set_edit_mode(self, editing: bool):
        super().set_edit_mode(editing)

        if editing:
            print("[CarLRLayer] Entrando em modo edição (teste ligado)")
            self.editing_overlay = True
            self.show()
            self.update()
        else:
            print("[CarLRLayer] Saindo do modo edição")
            self.editing_overlay = False
            self.update()
