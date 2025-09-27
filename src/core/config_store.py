import json
import os

CONFIG_FILE = "overlay_config.json"


def load_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro lendo {path}: {e}")
    return {}


class ConfigStore:
    def __init__(self):
        self.data = load_json(CONFIG_FILE)

    def load_layer_config(self, layer_id: str):
        """Carrega configurações específicas de um layer"""
        return self.data.get(layer_id, {})

    def save_layer_config(self, layer_id: str, cfg: dict):
        """Atualiza e salva configurações de um layer"""
        if layer_id not in self.data:
            self.data[layer_id] = {}
        self.data[layer_id].update(cfg)
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2)
            print(f"[ConfigStore] Gravado {layer_id} em {CONFIG_FILE}")
        except Exception as e:
            print(f"Erro ao salvar config: {e}")
