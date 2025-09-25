import sys
from PySide6 import QtWidgets, QtCore
from core.layout_store import LayoutStore
from ui.control_panel import ControlPanel
from layers.standings_layer import StandingsLayer
from layers.fuel_layer import FuelLayer
from layers.map_layer import MapLayer
from layers.car_lr_layer import CarLRLayer
from core.iracing_client import IRacingClient
from layers.twitch_chat_layer import TwitchChatLayer



LAYER_CLASSES = {
    "standings": StandingsLayer,
    "fuel": FuelLayer,
    "map": MapLayer,
    "car_lr": CarLRLayer,
    "twitchchat": TwitchChatLayer,
}


class OverlayApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)

        self.cfg = {
            "initial_layers": [
                {"id": "standings", "title": "Standings", "visible": True},
                {"id": "fuel", "title": "Fuel Calc", "visible": True},
                {"id": "car_lr", "title": "Car Left/Right", "visible": True},
                {"id": "map", "title": "Track Map", "visible": True},
                {"id": "twitchchat", "title": "Twitch Chat", "visible": True},
            ]
        }

        self.layers = {}
        self.locked = False

        # Gerenciador de layouts
        self.store = LayoutStore(QtWidgets.QWidget())

        # Cria layers iniciais
        for meta in self.cfg["initial_layers"]:
            cls = LAYER_CLASSES.get(meta["id"])
            if cls:
                saved = self.store.load_layer(meta["id"])
                layer = cls(
                    app=self,
                    layer_id=meta["id"],
                    title=meta["title"],
                    initial_rect=saved,
                )
                self.layers[meta["id"]] = layer
                layer.setVisible(meta.get("visible", True))

        # Painel de controle
        self.panel = ControlPanel(self.cfg["initial_layers"], self)
        self.panel.show()

        # Cliente iRacing (thread + sinal Qt)
        self.iracing_client = IRacingClient()
        self.iracing_client.data_ready.connect(self._dispatch_iracing_data)
        self.iracing_client.start()

    def _dispatch_iracing_data(self, packet):
        """Distribui dados do iRacing para todos os layers"""
        for layer in self.layers.values():
            if hasattr(layer, "update_from_iracing"):
                try:
                    layer.update_from_iracing(packet)
                except Exception as e:
                    print(f"[OverlayApp] Erro update layer {layer.layer_id}: {e}")

    def save_layouts(self):
        for layer_id, layer in self.layers.items():
            print(f"Saving layout for {layer_id}")
            rect = layer.save_layout()
            self.store.save_layer(layer_id, rect)

    def toggle_layer_visibility(self, layer_id: str, visible: bool):
        layer = self.layers.get(layer_id)
        if not layer:
            return
        if visible:
            layer.show()
            layer.raise_()
            layer.activateWindow()
            if getattr(layer, "_locked", False):
                layer.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        else:
            layer.hide()

    def closeEvent(self, event):
        print("Encerrando OverlayApp...")
        if hasattr(self, "iracing_client"):
            self.iracing_client.stop()
        super().closeAllWindows()
        event.accept()
