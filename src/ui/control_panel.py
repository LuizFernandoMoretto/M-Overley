import os
import json
from PySide6 import QtWidgets, QtGui, QtCore
from ui.standings_config_dialog import StandingsConfigDialog
from layers.twitch_chat_layer import save_config, load_config


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, layers_meta, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("M-Overlay Control Panel")
        self.setGeometry(100, 100, 380, 520)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
                font-family: Segoe UI, Arial;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3a3a3a;
                border: 1px solid #555;
                border-radius: 6px;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QGroupBox {
                border: 1px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                font-weight: bold;
            }
        """)

        main_layout = QtWidgets.QVBoxLayout(self)

        # ---------- LOGO ----------
        logo = QtWidgets.QLabel()
        if os.path.exists("logo.png"):
            pixmap = QtGui.QPixmap("logo.png").scaled(
                200, 90,
                QtCore.Qt.KeepAspectRatio,
                QtCore.Qt.SmoothTransformation
            )
            logo.setPixmap(pixmap)
        else:
            logo.setText("M-Overlay")
            logo.setStyleSheet("font-size: 20px; font-weight: bold; color: #00d9ff;")
        logo.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(logo)

        # ---------- CAMADAS ----------
        layers_group = QtWidgets.QGroupBox("Camadas")
        layers_layout = QtWidgets.QVBoxLayout(layers_group)

        # Botão para salvar layout
        btn_save = QtWidgets.QPushButton("Salvar Layout")
        btn_save.setIcon(QtGui.QIcon.fromTheme("document-save"))
        btn_save.clicked.connect(self.app.save_layouts)
        btn_save.setFixedHeight(32)
        layers_layout.addWidget(btn_save)

        # Checkbox para modo edição
        self.edit_checkbox = QtWidgets.QCheckBox("Modo Edição")
        self.edit_checkbox.toggled.connect(self.toggle_edit_mode)
        layers_layout.addWidget(self.edit_checkbox)

        # Checkbox para travar layout
        self.lock_checkbox = QtWidgets.QCheckBox("Travar Layout")
        self.lock_checkbox.toggled.connect(self.toggle_lock)
        layers_layout.addWidget(self.lock_checkbox)

        # Camadas ativas
        layers_layout.addWidget(QtWidgets.QLabel("Camadas Ativas:"))

        self.checkboxes = {}
        for meta in layers_meta:
            row = QtWidgets.QHBoxLayout()

            cb = QtWidgets.QCheckBox(meta["title"])
            cb.setChecked(meta.get("visible", True))
            cb.toggled.connect(lambda checked, lid=meta["id"]: self.toggle_layer(lid, checked))
            self.checkboxes[meta["id"]] = cb
            row.addWidget(cb)

            # Botão engrenagem
            btn = QtWidgets.QPushButton("⚙️")
            btn.setFixedWidth(30)
            btn.clicked.connect(lambda checked=False, lid=meta["id"]: self.open_layer_config(lid))
            row.addWidget(btn)

            layers_layout.addLayout(row)

        layers_group.setLayout(layers_layout)
        main_layout.addWidget(layers_group)

        main_layout.addStretch()

        # ---------- FOOTER ----------
        footer_layout = QtWidgets.QHBoxLayout()
        by_label = QtWidgets.QLabel("By: Moretto")
        by_label.setStyleSheet("color: #aaa; font-size: 11px;")
        footer_layout.addWidget(by_label, alignment=QtCore.Qt.AlignLeft)

        donate_btn = QtWidgets.QPushButton()
        if os.path.exists("donate.png"):
            donate_btn.setIcon(QtGui.QIcon("donate.png"))
        else:
            donate_btn.setText("☕")
        donate_btn.setToolTip("Apoie o projeto com uma doação")
        donate_btn.setFixedSize(32, 32)
        donate_btn.setStyleSheet("border: none; background: transparent;")
        footer_layout.addWidget(donate_btn, alignment=QtCore.Qt.AlignRight)

        main_layout.addLayout(footer_layout)

        # Centraliza painel
        self.center_on_screen()
        self.load_layer_states()

    # -------- Funções de controle --------
    def toggle_layer(self, layer_id, checked):
        self.app.toggle_layer_visibility(layer_id, checked)
        self.save_layer_states()

    def toggle_lock(self, checked):
        for layer in self.app.layers.values():
            layer.set_locked(checked)
        self.app.locked = checked

    def toggle_edit_mode(self, checked):
        for layer in self.app.layers.values():
            if hasattr(layer, "set_edit_mode"):
                layer.set_edit_mode(checked)
        if not checked:
            for lid, cb in self.checkboxes.items():
                self.app.toggle_layer_visibility(lid, cb.isChecked())

    # -------- Configs por layer --------
    def open_layer_config(self, layer_id):
        cfg = load_config().get("layer_configs", {}).get(layer_id, {})

        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle(f"Configurações - {layer_id}")
        dialog.setModal(True)
        layout = QtWidgets.QVBoxLayout(dialog)

        if layer_id == "twitchchat":
            inp = QtWidgets.QLineEdit(cfg.get("channel", ""))
            layout.addWidget(QtWidgets.QLabel("Canal da Twitch"))
            layout.addWidget(inp)

            btn_save = QtWidgets.QPushButton("Salvar")
            btn_save.clicked.connect(lambda: self._save_and_close(dialog, layer_id, {"channel": inp.text().strip()}))
            layout.addWidget(btn_save)

        elif layer_id == "car_lr":
            spin = QtWidgets.QSpinBox()
            spin.setRange(10, 100)
            spin.setValue(int(cfg.get("width_ratio", 0.33) * 100))
            layout.addWidget(QtWidgets.QLabel("Largura (%)"))
            layout.addWidget(spin)

            slider_alpha = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider_alpha.setRange(50, 255)
            slider_alpha.setValue(cfg.get("alpha", 220))
            layout.addWidget(QtWidgets.QLabel("Transparência"))
            layout.addWidget(slider_alpha)

            btn_color = QtWidgets.QPushButton("Escolher Cor")
            current_color = QtGui.QColor(cfg.get("color", "#FFD800"))
            self._update_button_color(btn_color, current_color)
            btn_color.clicked.connect(lambda: self.pick_color(btn_color))
            layout.addWidget(btn_color)

            btn_save = QtWidgets.QPushButton("Salvar")
            btn_save.clicked.connect(lambda: self._save_and_close(dialog, layer_id, {
                "width_ratio": spin.value() / 100,
                "alpha": slider_alpha.value(),
                "color": btn_color.property("chosen_color").name()
            }))
            layout.addWidget(btn_save)

        elif layer_id == "standings":
            slider_alpha = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider_alpha.setRange(50, 255)
            slider_alpha.setValue(cfg.get("alpha", 220))
            layout.addWidget(QtWidgets.QLabel("Transparência"))
            layout.addWidget(slider_alpha)

            spin_players = QtWidgets.QSpinBox()
            spin_players.setRange(0, 60)
            spin_players.setValue(cfg.get("max_players", 0))
            spin_players.setSuffix(" jogadores (0 = todos)")
            layout.addWidget(QtWidgets.QLabel("Mostrar você + X jogadores"))
            layout.addWidget(spin_players)

            btn_save = QtWidgets.QPushButton("Salvar")
            btn_save.clicked.connect(lambda: self._save_and_close(dialog, layer_id, {
                "alpha": slider_alpha.value(),
                "max_players": spin_players.value()
            }))
            layout.addWidget(btn_save)

        elif layer_id == "fuel":
            slider_alpha = QtWidgets.QSlider(QtCore.Qt.Horizontal)
            slider_alpha.setRange(50, 255)
            slider_alpha.setValue(cfg.get("alpha", 220))
            layout.addWidget(QtWidgets.QLabel("Transparência"))
            layout.addWidget(slider_alpha)

            zebra_cb = QtWidgets.QCheckBox("Ativar zebra striping (linhas alternadas)")
            zebra_cb.setChecked(cfg.get("zebra", True))
            layout.addWidget(zebra_cb)

            btn_save = QtWidgets.QPushButton("Salvar")
            btn_save.clicked.connect(lambda: self._save_and_close(dialog, layer_id, {
                "alpha": slider_alpha.value(),
                "zebra": zebra_cb.isChecked()
            }))
            layout.addWidget(btn_save)

        else:
            layout.addWidget(QtWidgets.QLabel("Sem opções específicas para este layer ainda."))

        dialog.setLayout(layout)
        dialog.exec()

    def _save_and_close(self, dialog, layer_id, cfg):
        self.save_layer_config(layer_id, cfg)
        dialog.accept()

    def save_layer_config(self, layer_id, cfg):
        data = load_config()
        if "layer_configs" not in data:
            data["layer_configs"] = {}
        if layer_id not in data["layer_configs"]:
            data["layer_configs"][layer_id] = {}
        data["layer_configs"][layer_id].update(cfg)
        save_config(data)

    # -------- Auxiliares de cor --------
    def pick_color(self, button):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self._update_button_color(button, color)
            button.setProperty("chosen_color", color)

    def _update_button_color(self, button, color):
        button.setProperty("chosen_color", color)
        button.setStyleSheet(f"background-color: {color.name()};")

    # -------- Estados gerais --------
    def save_layer_states(self):
        data = load_config()
        if "layers" not in data:
            data["layers"] = {}
        for lid, cb in self.checkboxes.items():
            data["layers"][lid] = cb.isChecked()
        save_config(data)

    def load_layer_states(self):
        data = load_config()
        if "layers" in data:
            for lid, visible in data["layers"].items():
                if lid in self.checkboxes:
                    self.checkboxes[lid].setChecked(visible)

    def center_on_screen(self):
        screen = self.screen().availableGeometry()
        size = self.geometry()
        x = (screen.width() - size.width()) // 2
        y = (screen.height() - size.height()) // 2
        self.move(x, y)
