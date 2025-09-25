from layers.base_layer import BaseLayer
from PySide6 import QtCore, QtWidgets, QtGui
import copy


class StandingsLayer(BaseLayer):
    standings_updated = QtCore.Signal(dict)  # pacote completo: standings + sessão

    def __init__(self, app, layer_id="standings", title="Standings", initial_rect=None):
        super().__init__(layer_id, title, app, initial_rect)

        layout = QtWidgets.QVBoxLayout(self)

        # Tabela de standings
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(
            ["Pos", "Driver", "iRating", "Últ. Volta", "Gap", "Inc."]
        )
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(20, 20, 20, 220);
                color: white;
                font-size: 13px;
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

        # Label inferior com infos da sessão
        self.session_label = QtWidgets.QLabel("Sessão: --", self)
        self.session_label.setStyleSheet("""
            QLabel {
                background-color: rgba(30,30,30,200);
                color: #00ff88;
                font-size: 12px;
                padding: 2px;
            }
        """)

        layout.addWidget(self.table)
        layout.addWidget(self.session_label)
        self.setLayout(layout)

        # conecta o sinal ao método de update
        self.standings_updated.connect(self._update_ui)

        # registra listener
        if hasattr(self.app, "iracing_client"):
            print(">>> DEBUG Registrando standings no iracing_client")
            self.app.iracing_client.add_listener(self.update_from_iracing)

        self.show()

    def update_from_iracing(self, packet):
        """Recebe pacote do iracing_client (executa fora da thread Qt)"""
        if not isinstance(packet, dict):
            return

        standings = packet.get("standings")
        session = packet.get("session")
        if not standings and not session:
            return

        safe_data = copy.deepcopy(packet)
        # agenda o update na thread principal
        QtCore.QTimer.singleShot(0, lambda: self.standings_updated.emit(safe_data))

    def _update_ui(self, packet):
        """Executa no thread principal Qt"""
        standings = packet.get("standings", [])
        session = packet.get("session", {})

        # Atualiza tabela de standings
        self.table.setRowCount(len(standings))
        for i, d in enumerate(standings):
            pos = QtWidgets.QTableWidgetItem(str(d.get("pos", "--")))
            drv = QtWidgets.QTableWidgetItem(d.get("driver", "--"))
            ir = QtWidgets.QTableWidgetItem(f"{d.get('irating','--')} {d.get('ir_delta','')}")
            lap = QtWidgets.QTableWidgetItem(d.get("last_lap", "--"))
            gap = QtWidgets.QTableWidgetItem(d.get("gap", "--"))
            inc = QtWidgets.QTableWidgetItem(str(d.get("incidents", "--")))

            if d.get("pos") == 1:
                for item in [pos, drv, ir, lap, gap, inc]:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("#00ff88")))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

            self.table.setItem(i, 0, pos)
            self.table.setItem(i, 1, drv)
            self.table.setItem(i, 2, ir)
            self.table.setItem(i, 3, lap)
            self.table.setItem(i, 4, gap)
            self.table.setItem(i, 5, inc)

        # Atualiza infos da sessão
        sof = session.get("sof", "--")
        race_time = session.get("time", "--")
        laps = session.get("laps", "--")
        track_temp = session.get("track_temp", "--")

        self.session_label.setText(
            f"SOF: {sof} | Tempo: {race_time} | Voltas: {laps} | Temp. pista: {track_temp}"
        )
