import json
import os
from PySide6 import QtWidgets

LAYOUT_FILE = "overlay_layout.json"


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro lendo {path}: {e}")
    return {}


def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Erro ao salvar {path}: {e}")
        return False


class LayoutStore:
    def __init__(self, widget=None):
        # Usa a resolução da tela do widget (se existir), senão pega a tela primária
        if widget and widget.screen():
            size = widget.screen().size()
        else:
            screen = QtWidgets.QApplication.primaryScreen()
            size = screen.size()

        self.key = f"{size.width()}x{size.height()}"
        self.data = load_json(LAYOUT_FILE)

    def load_layer(self, layer_id: str):
        """Carrega a geometria salva de um layer, se existir"""
        return self.data.get(self.key, {}).get(layer_id)

    def _normalize(self, rect):
        """Normaliza a geometria para proporções relativas"""
        screen = QtWidgets.QApplication.primaryScreen()
        size = screen.size()
        return {
            "x": rect.x() / size.width(),
            "y": rect.y() / size.height(),
            "w": rect.width() / size.width(),
            "h": rect.height() / size.height(),
        }

    def save_layer(self, layer_id: str, rect: dict):
        """Salva a geometria normalizada de um layer no JSON"""
        if self.key not in self.data:
            self.data[self.key] = {}

        self.data[self.key][layer_id] = rect
        if save_json(LAYOUT_FILE, self.data):
            print(f">>> Gravado {layer_id} em {LAYOUT_FILE}")

    # --------- Novos métodos ---------
    def save_layer_states(self, states: dict):
        """
        Salva estado (visível / não visível) das camadas.
        states = { "standings": True, "fuel": False, ... }
        """
        if "layers_state" not in self.data:
            self.data["layers_state"] = {}
        self.data["layers_state"].update(states)
        if save_json(LAYOUT_FILE, self.data):
            print(">>> Estados das camadas salvos")

    def load_layer_states(self):
        """Carrega estados de camadas salvos anteriormente"""
        return self.data.get("layers_state", {})

    def save_control_panel_geometry(self, rect):
        """Salva geometria do painel de controle (opcional)"""
        self.data["control_panel"] = {
            "x": rect.x(),
            "y": rect.y(),
            "w": rect.width(),
            "h": rect.height(),
        }
        if save_json(LAYOUT_FILE, self.data):
            print(">>> Geometria do painel salva")

    def load_control_panel_geometry(self):
        """Carrega geometria do painel de controle, se existir"""
        return self.data.get("control_panel")
