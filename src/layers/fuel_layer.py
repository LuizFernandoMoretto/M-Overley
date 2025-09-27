from layers.base_layer import BaseLayer
from core.config_store import ConfigStore
from PySide6 import QtCore, QtWidgets, QtGui
import copy


class FuelLayer(BaseLayer):
    fuel_updated = QtCore.Signal(dict)

    def __init__(self, app, layer_id="fuel", title="Fuel Calc", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        # Gerenciador de configs
        self.cfg_store = ConfigStore()
        self.cfg = self.cfg_store.load_layer_config(layer_id)

        # Alpha padrão
        self.alpha = self.cfg.get("alpha", 220)
        self.zebra = self.cfg.get("zebra", True)

        # tabela
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setRowCount(4)
        self.table.setHorizontalHeaderLabels(["Item", "Valor"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self._apply_styles()

        labels = ["Fuel atual", "Capacidade", "Consumo/volta", "Voltas restantes"]
        for i, lbl in enumerate(labels):
            item = QtWidgets.QTableWidgetItem(lbl)
            item.setForeground(QtGui.QBrush(QtGui.QColor("#00ff88")))
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem("--"))

        # conecta o sinal ao método de update
        self.fuel_updated.connect(self._update_table)

        # registra listener no iRacing
        if hasattr(self.app, "iracing_client"):
            print(">>> DEBUG Registrando listener do fuel no iracing_client")
            self.app.iracing_client.add_listener(self.update_from_iracing)

        self.show()

    def _apply_styles(self):
        """Aplica transparência e zebra striping"""
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: rgba(0, 0, 0, {self.alpha});
                color: white;
                font-size: 14px;
                border: 2px solid #444;
                gridline-color: #555;
            }}
            QHeaderView::section {{
                background-color: rgba(20, 20, 20, {self.alpha});
                color: white;
                font-weight: bold;
                border: none;
                padding: 4px;
            }}
        """)

        # Aplica zebra
        if self.zebra:
            for row in range(self.table.rowCount()):
                bg = QtGui.QColor(0, 0, 0, self.alpha) if row % 2 == 0 else QtGui.QColor(30, 30, 30, self.alpha)
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        item.setBackground(QtGui.QBrush(bg))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "table"):
            self.table.setGeometry(self.rect().adjusted(5, 25, -5, -5))

    def update_from_iracing(self, packet):
        if not isinstance(packet, dict):
            return

        fuel = packet.get("fuel")
        if not fuel:
            return

        safe_data = copy.deepcopy(fuel)
        QtCore.QTimer.singleShot(0, lambda: self.fuel_updated.emit(safe_data))

    def _update_table(self, fuel):
        values = [
            f"{fuel.get('level', 0):.1f} L" if fuel.get("level") else "--",
            f"{fuel.get('capacity', 0):.1f} L" if fuel.get("capacity") else "--",
            f"{fuel.get('use_per_lap', 0):.2f} L" if fuel.get("use_per_lap") else "--",
            str(fuel.get("laps", '--'))
        ]

        for i, val in enumerate(values):
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(val))

        self._apply_styles()

    def closeEvent(self, event):
        # Salvar alpha e zebra
        self.cfg_store.save_layer_config(self.layer_id, {
            "alpha": self.alpha,
            "zebra": self.zebra
        })
        super().closeEvent(event)
        event.accept()
