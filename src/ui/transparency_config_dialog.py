from PySide6 import QtWidgets, QtCore


class TransparencyConfigDialog(QtWidgets.QDialog):
    def __init__(self, layer, parent=None):
        super().__init__(parent)
        self.layer = layer
        self.setWindowTitle(f"Configurar Transparência - {layer.title}")
        self.setModal(True)
        self.setFixedSize(300, 150)

        layout = QtWidgets.QVBoxLayout(self)

        # Label e slider
        self.label = QtWidgets.QLabel(f"Nível de transparência: {self.layer.alpha}")
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(50)
        self.slider.setMaximum(255)
        self.slider.setValue(self.layer.alpha)
        self.slider.valueChanged.connect(self._on_slider_change)

        layout.addWidget(self.label)
        layout.addWidget(self.slider)

        # Botões
        btns = QtWidgets.QHBoxLayout()
        btn_save = QtWidgets.QPushButton("Salvar")
        btn_cancel = QtWidgets.QPushButton("Cancelar")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def _on_slider_change(self, value):
        self.label.setText(f"Nível de transparência: {value}")
        self.layer.alpha = value  # aplica em tempo real
        self.layer.update()       # força repintar
