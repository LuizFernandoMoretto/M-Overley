import json
import os
from PySide6 import QtWidgets, QtWebEngineWidgets
from layers.base_layer import BaseLayer

CONFIG_FILE = "config.json"


def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("[Config] Erro ao ler config.json:", e)
    return {}


def save_config(data):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("[Config] Erro ao salvar config.json:", e)


class TwitchChatLayer(BaseLayer):
    def __init__(self, app, layer_id="twitchchat", title="Twitch Chat", initial_rect=None):
        super().__init__(app, layer_id, title, initial_rect)

        self.view = QtWebEngineWidgets.QWebEngineView(self)

        cfg = load_config()
        channel = cfg.get("twitch_channel", "twitch")  # valor padrão
        url = f"https://www.twitch.tv/embed/{channel}/chat?parent=localhost&darkpopout"

        self.view.setUrl(url)
        self.show()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.view.setGeometry(self.rect().adjusted(5, 25, -5, -5))
