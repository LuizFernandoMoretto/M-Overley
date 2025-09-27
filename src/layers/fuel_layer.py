from layers.base_layer import BaseLayer
from core.config_store import ConfigStore
from PySide6 import QtCore, QtWidgets, QtGui


class FuelLayer(BaseLayer):
    fuel_updated = QtCore.Signal(dict)

    def __init__(self, app, layer_id="fuel", title="Fuel Calc", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        layout = QtWidgets.QVBoxLayout(self)

        # Configuração persistente
        self.cfg_store = ConfigStore()
        saved_cfg = self.cfg_store.load_layer_config(layer_id)

        # Transparência configurável
        self.alpha = saved_cfg.get("alpha", 220)

        # Tabela 2 colunas (Item | Valor)
        labels = ["Fuel atual", "Capacidade", "Consumo/volta", "Voltas restantes"]

        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setRowCount(len(labels))
        self.table.setHorizontalHeaderLabels(["Item", "Valor"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        # Remove barras de rolagem
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Estilo preto/cinza translúcido
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                color: white;
                font-size: 12px;
                border: 2px solid #444;
                gridline-color: #555;
            }}
            QHeaderView::section {{
                background-color: rgba(20,20,20,{self.alpha});
                color: white;
                font-weight: bold;
                border: none;
                padding: 3px;
            }}
        """)

        # Preenche coluna de itens
        for i, lbl in enumerate(labels):
            item = QtWidgets.QTableWidgetItem(lbl)
            item.setForeground(QtGui.QBrush(QtGui.QColor("white")))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem("--"))

        layout.addWidget(self.table)
        self.setLayout(layout)

        # conecta sinal
        self.fuel_updated.connect(self._update_ui)

        # registra listener
        if hasattr(self.app, "iracing_client"):
            self.app.iracing_client.add_listener(self.update_from_iracing)

        self.show()

    def set_edit_mode(self, editing: bool):
        header = self.table.horizontalHeader()
        if editing:
            header.setSectionResizeMode(QtWidgets.QHeaderView.Interactive)
        else:
            header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        super().set_edit_mode(editing)

    def update_from_iracing(self, packet):
        if not isinstance(packet, dict):
            return
        fuel = packet.get("fuel")
        if not fuel:
            return
        QtCore.QTimer.singleShot(0, lambda: self.fuel_updated.emit(fuel))

    def _update_ui(self, fuel):
        values = [
            f"{fuel.get('level', 0):.1f} L",
            f"{fuel.get('capacity', 0):.1f} L",
            f"{fuel.get('use_per_lap', 0):.2f} L",
            str(fuel.get('laps', 0))
        ]
        for i, val in enumerate(values):
            item = QtWidgets.QTableWidgetItem(val)
            item.setTextAlignment(QtCore.Qt.AlignCenter)

            # zebra striping translúcido
            bg_color = QtGui.QColor(0, 0, 0, self.alpha) if i % 2 == 0 else QtGui.QColor(30, 30, 30, self.alpha)
            item.setBackground(QtGui.QBrush(bg_color))
            item.setForeground(QtGui.QBrush(QtGui.QColor("white")))

            self.table.setItem(i, 1, item)

    def closeEvent(self, event):
        widths = {}
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            widths[header] = self.table.columnWidth(col)

        self.cfg_store.save_layer_config(self.layer_id, {
            "columns_width": widths,
            "alpha": self.alpha
        })
        super().closeEvent(event)
        event.accept()
