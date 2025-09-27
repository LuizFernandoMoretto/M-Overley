from PySide6 import QtWidgets, QtCore


class StandingsConfigDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, current_max=0):
        super().__init__(parent)
        self.setWindowTitle("Configurações do Standings")

        layout = QtWidgets.QVBoxLayout(self)

        # Campo para número de jogadores
        self.spin_players = QtWidgets.QSpinBox(self)
        self.spin_players.setMinimum(0)
        self.spin_players.setMaximum(60)  # limite razoável de grid
        self.spin_players.setValue(current_max or 0)
        self.spin_players.setSuffix(" players (0 = todos)")
        layout.addWidget(QtWidgets.QLabel("Mostrar você + X players"))
        layout.addWidget(self.spin_players)

        # Botões OK/Cancelar
        btn_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal,
            self
        )
        btn_box.accepted.connect(self.accept)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def get_value(self):
        """Retorna o valor configurado"""
        return self.spin_players.value()
