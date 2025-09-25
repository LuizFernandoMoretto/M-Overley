from layers.base_layer import BaseLayer
from PySide6 import QtCore, QtWidgets, QtGui
import copy


class FuelLayer(BaseLayer):
    fuel_updated = QtCore.Signal(dict)  # sinal dedicado para fuel

    def __init__(self, app, layer_id="fuel", title="Fuel Calc", initial_rect=None):
        super().__init__(layer_id, title, app, initial_rect)

        # tabela
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(2)
        self.table.setRowCount(4)
        self.table.setHorizontalHeaderLabels(["Item", "Valor"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(20, 20, 20, 200);
                color: white;
                font-size: 14px;
                border: 2px solid #444;
                gridline-color: #555;
            }
            QHeaderView::section {
                background-color: #222;
                color: #00ff88;
                font-weight: bold;
                border: none;
                padding: 4px;
            }
        """)

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

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "table"):
            self.table.setGeometry(self.rect().adjusted(5, 25, -5, -5))

    def update_from_iracing(self, packet):
        """Recebe pacote do iracing_client (executa fora da thread Qt)"""
        if not isinstance(packet, dict):
            return

        fuel = packet.get("fuel")
        if not fuel:
            return

        safe_data = copy.deepcopy(fuel)
        # agenda o update na thread principal
        QtCore.QTimer.singleShot(0, lambda: self.fuel_updated.emit(safe_data))

    def _update_table(self, fuel):
        """Executa no thread principal Qt"""
        values = [
            f"{fuel.get('level', 0):.1f} L" if fuel.get("level") else "--",
            f"{fuel.get('capacity', 0):.1f} L" if fuel.get("capacity") else "--",
            f"{fuel.get('use_per_lap', 0):.2f} L" if fuel.get("use_per_lap") else "--",
            str(fuel.get("laps", '--'))
        ]

        for i, val in enumerate(values):
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(val))

        self.table.viewport().update()
        self.table.repaint()
