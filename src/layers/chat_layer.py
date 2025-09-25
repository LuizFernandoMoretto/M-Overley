from layers.base_layer import BaseLayer
from PySide6 import QtCore, QtWidgets
import random, time

class ChatLayer(BaseLayer):
    def __init__(self, app, layer_id='chat', title='Twitch Chat', initial_rect=None):
        super().__init__(layer_id, title, app, initial_rect)

        layout = QtWidgets.QVBoxLayout(self)
        self.text = QtWidgets.QTextEdit()
        self.text.setReadOnly(True)
        self.text.setStyleSheet("background-color: rgba(0,0,0,120); color: white; font-size: 12px;")
        layout.addWidget(self.text)

        self.fake_users = ["Luiz", "Racer01", "Speedy", "ChatBot", "Fan99"]
        self.fake_msgs = [
            "Boa corrida!",
            "Força no braço 💪",
            "Vai dar P1 hoje!",
            "Box this lap?",
            "Bela ultrapassagem!",
            "Cuidado na curva 3..."
        ]

        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.add_fake_message)
        self.timer.start(4000)  # nova msg a cada 4s

    def add_fake_message(self):
        user = random.choice(self.fake_users)
        msg = random.choice(self.fake_msgs)
        timestamp = time.strftime("%H:%M:%S")
        self.text.append(f"[{timestamp}] {user}: {msg}")
        self.text.verticalScrollBar().setValue(self.text.verticalScrollBar().maximum())
