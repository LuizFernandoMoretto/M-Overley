from PySide6 import QtWidgets, QtGui, QtCore
from layers.base_layer import BaseLayer


class CarLRLayer(BaseLayer):
    def __init__(self, app, layer_id="car_lr", title="Car Left/Right", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        self.side = "clear"  # valores: clear, left, right, both

        # Efeito de opacidade para animação
        self.effect = QtWidgets.QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        self.anim = QtCore.QPropertyAnimation(self.effect, b"opacity")
        self.anim.setDuration(150)  # rápido e fluido
        self.anim.setEasingCurve(QtCore.QEasingCurve.InOutQuad)

        self.hide()

    def update_from_iracing(self, packet):
        """Atualiza com base no campo CarLeftRight do iRacing"""
        if "CarLeftRight" not in packet:
            return

        val = packet["CarLeftRight"]
        new_side = "clear"
        if val == 1:
            new_side = "left"
        elif val == 2:
            new_side = "right"
        elif val == 3:
            new_side = "both"

        if new_side != self.side:
            self.side = new_side
            if self.side == "clear":
                self.fade_out()
            else:
                self.fade_in()
            self.update()

    def fade_in(self):
        self.show()
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(1.0)
        self.anim.start()

    def fade_out(self):
        self.anim.stop()
        self.anim.setStartValue(self.effect.opacity())
        self.anim.setEndValue(0.0)
        self.anim.start()
        self.anim.finished.connect(self.hide)

    def paintEvent(self, event):
        if self.side == "clear":
            return

        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        # cor: amarelo suave (pode virar configurável depois)
        color = QtGui.QColor(255, 220, 0, 220)  # RGBA
        painter.setBrush(color)
        painter.setPen(QtCore.Qt.NoPen)

        rect = self.rect()
        bar_width = int(rect.width() * 0.33)  # largura = 1/3 (padrão, depois configurável)

        if self.side == "left":
            bar = QtCore.QRect(0, 0, bar_width, rect.height())
            painter.drawRect(bar)
        elif self.side == "right":
            bar = QtCore.QRect(rect.width() - bar_width, 0, bar_width, rect.height())
            painter.drawRect(bar)
        elif self.side == "both":
            left = QtCore.QRect(0, 0, bar_width, rect.height())
            right = QtCore.QRect(rect.width() - bar_width, 0, bar_width, rect.height())
            painter.drawRect(left)
            painter.drawRect(right)

        painter.end()
