import json
import os
from PySide6 import QtWidgets
from layers.twitch_chat_layer import save_config, load_config


class ControlPanel(QtWidgets.QWidget):
    def __init__(self, layers_meta, app):
        super().__init__()
        self.app = app
        self.setWindowTitle("Overlay Control Panel")
        self.setGeometry(100, 100, 350, 500)

        tabs = QtWidgets.QTabWidget()
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(tabs)

        # ---------------- CAMADAS ----------------
        layers_tab = QtWidgets.QWidget()
        layers_layout = QtWidgets.QVBoxLayout(layers_tab)

        # Botão para salvar layout
        btn_save = QtWidgets.QPushButton("Salvar Layout")
        btn_save.clicked.connect(self.app.save_layouts)
        layers_layout.addWidget(btn_save)

        # Checkbox para modo edição
        self.edit_checkbox = QtWidgets.QCheckBox("Modo Edição")
        self.edit_checkbox.toggled.connect(self.toggle_edit_mode)
        layers_layout.addWidget(self.edit_checkbox)

        # Checkbox para travar layout
        self.lock_checkbox = QtWidgets.QCheckBox("Travar Layout")
        self.lock_checkbox.toggled.connect(self.toggle_lock)
        layers_layout.addWidget(self.lock_checkbox)

        layers_layout.addWidget(QtWidgets.QLabel("Camadas:"))

        self.checkboxes = {}
        for meta in layers_meta:
            cb = QtWidgets.QCheckBox(meta["title"])
            cb.setChecked(meta.get("visible", True))
            cb.toggled.connect(lambda checked, lid=meta["id"]: self.toggle_layer(lid, checked))
            layers_layout.addWidget(cb)
            self.checkboxes[meta["id"]] = cb

        layers_layout.addStretch()
        tabs.addTab(layers_tab, "Camadas")

        # ---------------- CONFIG ----------------
        config_tab = QtWidgets.QWidget()
        config_layout = QtWidgets.QVBoxLayout(config_tab)

        cfg = load_config()
        self.twitch_input = QtWidgets.QLineEdit()
        self.twitch_input.setPlaceholderText("Canal da Twitch")
        self.twitch_input.setText(cfg.get("twitch_channel", ""))
        config_layout.addWidget(QtWidgets.QLabel("Twitch Channel"))
        config_layout.addWidget(self.twitch_input)

        btn_save_cfg = QtWidgets.QPushButton("Salvar Config")
        btn_save_cfg.clicked.connect(self.save_config)
        config_layout.addWidget(btn_save_cfg)

        config_layout.addStretch()
        tabs.addTab(config_tab, "Config")

    # -------- Funções de controle --------
    def toggle_layer(self, layer_id, checked):
        print(f"[ControlPanel] {layer_id} → {checked}")
        self.app.toggle_layer_visibility(layer_id, checked)

    def toggle_lock(self, checked):
        for layer in self.app.layers.values():
            layer.set_locked(checked)
        self.app.locked = checked
        print(f"[ControlPanel] Layout travado: {checked}")

    def toggle_edit_mode(self, checked):
        for layer in self.app.layers.values():
            layer.set_edit_mode(checked)
        print(f"[ControlPanel] Modo edição: {checked}")

    def save_config(self):
        data = load_config()
        data["twitch_channel"] = self.twitch_input.text().strip()
        save_config(data)
        print("[Config] Canal salvo:", data["twitch_channel"])
