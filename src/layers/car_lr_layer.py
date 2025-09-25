from layers.base_layer import BaseLayer
from PySide6 import QtCore, QtWidgets
import random

class CarLRLayer(BaseLayer):
    def __init__(self, app, layer_id='car_lr', title='Car Left/Right', initial_rect=None):
        super().__init__(layer_id, title, app, initial_rect)

        layout = QtWidgets.QVBoxLayout(self)
        self.label = QtWidgets.QLabel("Clear")
        self.label.setStyleSheet("font-size: 32px; font-weight: bold; color: lime;")
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(self.label)

        self.messages = [
            ("Car Left", "yellow"),
            ("Car Right", "orange"),
            ("Clear", "lime")
        ]

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(2500)  # a cada 2.5s

    def update_data(self):
        msg, color = random.choice(self.messages)
        self.label.setText(msg)
        self.label.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {color};")
