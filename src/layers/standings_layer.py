from layers.base_layer import BaseLayer
from core.config_store import ConfigStore
from PySide6 import QtCore, QtWidgets, QtGui
from ui.standings_config_dialog import StandingsConfigDialog
import copy

COUNTRY_FLAGS = {
    "Brazil": "🇧🇷",
    "United States": "🇺🇸",
    "Germany": "🇩🇪",
    "France": "🇫🇷",
    "Italy": "🇮🇹",
    "Spain": "🇪🇸",
    "Portugal": "🇵🇹",
    "Argentina": "🇦🇷",
    "Canada": "🇨🇦",
    "United Kingdom": "🇬🇧",
    # pode expandir conforme os países que aparecem
}


class StandingsLayer(BaseLayer):
    standings_updated = QtCore.Signal(dict)

    def __init__(self, app, layer_id="standings", title="Standings", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        layout = QtWidgets.QVBoxLayout(self)

        # Gerenciador de configs
        self.cfg_store = ConfigStore()
        saved_cfg = self.cfg_store.load_layer_config(layer_id)

        # Transparência configurável
        self.alpha = saved_cfg.get("alpha", 220)

        # Tabela de standings
        headers = ["Pos", "Δ", "#", "Logo", "Flag", "Driver", "Lic", "iRating", "Últ. Volta", "Gap"]
        self.table = QtWidgets.QTableWidget(self)
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        self.table.verticalHeader().setVisible(False)

        # Configuração do header
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)
        self.table.setIconSize(QtCore.QSize(24, 12))

        # guarda posição inicial quando não há qualy
        self._starting_positions = {}

        # Estilos
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: transparent;
                color: white;
                font-size: 12px;
                border: none;
                gridline-color: #555;
            }
            QHeaderView::section {
                background-color: rgba(20,20,20,200);
                color: white;
                font-weight: bold;
                border: none;
                padding: 3px;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                border: none;
                background: transparent;
                width: 0px;
                height: 0px;
            }
        """)
        self.table.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.table.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        # Larguras padrão
        default_widths = {
            "Pos": 20,
            "Δ": 20,
            "#": 20,
            "Logo": 20,
            "Flag": 20,
            "Driver": 150,
            "Lic": 30,
            "iRating": 30,
            "Últ. Volta": 40,
            "Gap": 20,
        }

        saved_widths = saved_cfg.get("columns_width", {})
        for col in range(self.table.columnCount()):
            header_text = self.table.horizontalHeaderItem(col).text()
            width = saved_widths.get(header_text, default_widths.get(header_text, 80))
            self.table.setColumnWidth(col, width)

        # Restaurar estado completo do header
        saved_header = saved_cfg.get("header_state")
        if saved_header:
            self.table.horizontalHeader().restoreState(QtCore.QByteArray.fromHex(saved_header.encode()))

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
        standings = packet.get("standings")
        session = packet.get("session")
        if not standings and not session:
            return
        safe_data = copy.deepcopy(packet)
        QtCore.QTimer.singleShot(0, lambda: self.standings_updated.emit(safe_data))

    def _update_ui(self, packet):
        standings = packet.get("standings", [])
        session = packet.get("session", {})

        # filtro "eu + X players"
        saved_cfg = self.cfg_store.load_layer_config(self.layer_id)
        max_players = saved_cfg.get("max_players", 11)
        my_driver_id = session.get("my_driver_id")

        if max_players and my_driver_id is not None:
            my_driver = next((d for d in standings if d.get("id") == my_driver_id), None)
            if my_driver:
                idx = standings.index(my_driver)
                half = max_players // 2
                start = max(0, idx - half)
                end = min(len(standings), start + max_players)
                if end - start < max_players:
                    start = max(0, end - max_players)
                standings = standings[start:end]

        self.table.setRowCount(len(standings))
        for i, d in enumerate(standings):
            pos = QtWidgets.QTableWidgetItem(str(d.get("pos", "--")))

            # --- Delta estilizado ---
            delta_val = d.get("pos_gain", 0)
            if delta_val > 0:
                delta = QtWidgets.QTableWidgetItem(f"+{delta_val}")
                delta.setForeground(QtGui.QBrush(QtGui.QColor("lime")))
            elif delta_val < 0:
                delta = QtWidgets.QTableWidgetItem(str(delta_val))
                delta.setForeground(QtGui.QBrush(QtGui.QColor("red")))
            else:
                delta = QtWidgets.QTableWidgetItem("0")
                delta.setForeground(QtGui.QBrush(QtGui.QColor("lightgray")))

            car_num = QtWidgets.QTableWidgetItem(str(d.get("car_number", "--")))
            logo_item = QtWidgets.QTableWidgetItem()
            if d.get("car_logo"):
                logo_item.setIcon(QtGui.QIcon(d["car_logo"]))
            drv = QtWidgets.QTableWidgetItem(d.get("driver", "--"))

            # Flag por país
            country = (d.get("country") or "").title()
            flag_item = QtWidgets.QTableWidgetItem(COUNTRY_FLAGS.get(country, "🏳️"))
            flag_item.setTextAlignment(QtCore.Qt.AlignCenter)

            lic = QtWidgets.QTableWidgetItem(d.get("license", "--"))
            lic_color = d.get("license_color", "#333")
            lic.setBackground(QtGui.QBrush(QtGui.QColor(lic_color)))

            ir = QtWidgets.QTableWidgetItem(f"{d.get('irating', '--')} {d.get('ir_delta', '')}")
            lap = QtWidgets.QTableWidgetItem(d.get("last_lap", "--"))
            gap = QtWidgets.QTableWidgetItem(d.get("gap", "--"))

            # aplica cor de fundo
            if d.get("id") == my_driver_id:
                bg_color = QtGui.QColor(70, 130, 180, 200)  # azul destaque
            else:
                bg_color = QtGui.QColor(0, 0, 0, self.alpha) if i % 2 == 0 else QtGui.QColor(30, 30, 30, self.alpha)

            for col, item in enumerate([pos, delta, car_num, logo_item, flag_item, drv, lic, ir, lap, gap]):
                if item:
                    if col == 5:  # coluna "Driver"
                        item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
                    else:
                        item.setTextAlignment(QtCore.Qt.AlignCenter)
                    item.setBackground(QtGui.QBrush(bg_color))
                    self.table.setItem(i, col, item)

            # líder continua dourado
            if d.get("pos") == 1:
                for item in [pos, drv, ir, lap, gap]:
                    item.setForeground(QtGui.QBrush(QtGui.QColor("#FFD700")))
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)

        # Atualiza infos da sessão
        sof = session.get("sof", "--")
        length = session.get("session_length", "--")
        remain = session.get("time_remain", None)
        track_temp = session.get("track_temp", "--")

        txt = f"SOF Geral: {sof} | Sessão: {length}"
        if remain:  # só aparece em sessão por tempo
            txt += f" | Restante: {remain}"
        txt += f" | Temp. pista: {track_temp}"

        self.session_label.setText(txt)

    def open_config_dialog(self):
        saved_cfg = self.cfg_store.load_layer_config(self.layer_id)
        current_max = saved_cfg.get("max_players", 0)

        dlg = StandingsConfigDialog(self, current_max)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            new_max = dlg.get_value()
            saved_cfg["max_players"] = new_max
            self.cfg_store.save_layer_config(self.layer_id, saved_cfg)
            print(f">>> Standings atualizado: max_players = {new_max}")

    def closeEvent(self, event):
        widths = {}
        for col in range(self.table.columnCount()):
            header = self.table.horizontalHeaderItem(col).text()
            widths[header] = self.table.columnWidth(col)

        state = self.table.horizontalHeader().saveState().toHex().data().decode()

        self.cfg_store.save_layer_config(self.layer_id, {
            "columns_width": widths,
            "alpha": self.alpha,
            "header_state": state
        })
        super().closeEvent(event)
        event.accept()
