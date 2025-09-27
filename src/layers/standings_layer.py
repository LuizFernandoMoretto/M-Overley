from layers.base_layer import BaseLayer
from core.config_store import ConfigStore
from PySide6 import QtCore, QtWidgets, QtGui
import copy


class StandingsLayer(BaseLayer):
    standings_updated = QtCore.Signal(dict)

    def __init__(self, app, layer_id="standings", title="Standings", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        layout = QtWidgets.QVBoxLayout(self)

        # Gerenciador de configs
        self.cfg_store = ConfigStore()
        saved_cfg = self.cfg_store.load_layer_config(layer_id)

        # Tabela de standings
        headers = ["Pos", "Δ", "#", "Logo", "Driver", "Lic", "iRating", "Últ. Volta", "Gap", "Inc."]
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setIconSize(QtCore.QSize(24, 12))

        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #000000;
                color: white;
                font-size: 12px;
                border: 2px solid #444;
                gridline-color: #555;
            }
            QHeaderView::section {
                background-color: #111;
                color: white;
                font-weight: bold;
                border: none;
                padding: 3px;
            }
        """)

        # Restaurar larguras salvas
        saved_widths = saved_cfg.get("columns_width", {})
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            if header in saved_widths:
                self.table.setColumnWidth(col, saved_widths[header])

        # Label inferior com infos da sessão
        self.session_label = QtWidgets.QLabel("Sessão: --", self)
        self.session_label.setStyleSheet("""
            QLabel {
                background-color: rgba(30,30,30,200);
                color: white;
                font-size: 12px;
                padding: 2px;
            }
        """)

        layout.addWidget(self.table)
        layout.addWidget(self.session_label)
        self.setLayout(layout)

        # conecta sinal
        self.standings_updated.connect(self._update_ui)

        # registra listener
        if hasattr(self.app, "iracing_client"):
            print(">>> DEBUG Registrando standings no iracing_client")
            self.app.iracing_client.add_listener(self.update_from_iracing)

        self.show()

    def update_from_iracing(self, packet):
        if not isinstance(packet, dict):
            return
        standings = packet.get("standings")
        session = packet.get("session")
        if not standings and not session:
            return
        safe_data = copy.deepcopy(packet)
        QtCore.QTimer.singleShot(0, lambda: self.standings_updated.emit(safe_data))

    def _update_ui(self, packet):
        standings = packet.get("standings", [])
        session = packet.get("session", {})

        self.table.setRowCount(len(standings))
        for i, d in enumerate(standings):
            # Campos
            pos = QtWidgets.QTableWidgetItem(str(d.get("pos", "--")))

            delta_val = d.get("pos_gain", 0)
            delta = QtWidgets.QTableWidgetItem(
                f"{'+' if delta_val > 0 else ''}{delta_val}" if delta_val else ""
            )
            if delta_val > 0:
                delta.setForeground(QtGui.QBrush(QtGui.QColor("lime")))
            elif delta_val < 0:
                delta.setForeground(QtGui.QBrush(QtGui.QColor("red")))

            car_num = QtWidgets.QTableWidgetItem(str(d.get("car_number", "--")))

            logo_item = QtWidgets.QTableWidgetItem()
            logo_path = d.get("car_logo")
            if logo_path:
                logo_item.setIcon(QtGui.QIcon(logo_path))

            drv = QtWidgets.QTableWidgetItem(d.get("driver", "--"))

            lic = QtWidgets.QTableWidgetItem(d.get("license", "--"))
            lic_color = d.get("license_color", "#333")
            lic.setBackground(QtGui.QBrush(QtGui.QColor(lic_color)))

            ir_val = d.get("irating", "--")
            ir_delta = d.get("ir_delta", "")
            ir = QtWidgets.QTableWidgetItem(f"{ir_val} {ir_delta}")

            lap = QtWidgets.QTableWidgetItem(d.get("last_lap", "--"))
            gap = QtWidgets.QTableWidgetItem(d.get("gap", "--"))
            inc = QtWidgets.QTableWidgetItem(str(d.get("incidents", "--")))

            # Destaque do líder
            if d.get("pos") == 1:
                for item in [pos, drv, ir, lap, gap, inc]:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("#FFD700")))  # dourado discreto
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

            # Insere colunas
            self.table.setItem(i, 0, pos)
            self.table.setItem(i, 1, delta)
            self.table.setItem(i, 2, car_num)
            self.table.setItem(i, 3, logo_item)
            self.table.setItem(i, 4, drv)
            self.table.setItem(i, 5, lic)
            self.table.setItem(i, 6, ir)
            self.table.setItem(i, 7, lap)
            self.table.setItem(i, 8, gap)
            self.table.setItem(i, 9, inc)

            # Multiclass tem prioridade
            class_color = d.get("class_color")
            if class_color:
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        brush = QtGui.QBrush(QtGui.QColor(class_color))
                        brush.setStyle(QtCore.Qt.Dense4Pattern)
                        item.setBackground(brush)
            else:
                # 🎨 Zebra striping
                bg_color = "#000000" if i % 2 == 0 else "#1a1a1a"
                for col in range(self.table.columnCount()):
                    item = self.table.item(i, col)
                    if item:
                        item.setBackground(QtGui.QBrush(QtGui.QColor(bg_color)))

        # Atualiza infos da sessão
        sof = session.get("sof", "--")
        race_time = session.get("time", "--")
        laps = session.get("laps", "--")
        track_temp = session.get("track_temp", "--")

        txt = f"SOF Geral: {sof} | Tempo: {race_time} | Voltas: {laps} | Temp. pista: {track_temp}"

        class_sof = session.get("class_sof", {})
        if class_sof:
            parts = []
            for cid, sof_val in class_sof.items():
                parts.append(f"Classe {cid}: {sof_val}")
            txt += " | " + " | ".join(parts)

        self.session_label.setText(txt)

    def closeEvent(self, event):
        widths = {}
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            widths[header] = self.table.columnWidth(col)

        self.cfg_store.save_layer_config(self.layer_id, {"columns_width": widths})
        super().closeEvent(event)
        event.accept()
