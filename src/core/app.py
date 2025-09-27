import sys
from PySide6 import QtWidgets, QtCore
from core.layout_store import LayoutStore
from ui.control_panel import ControlPanel
from layers.standings_layer import StandingsLayer
from layers.fuel_layer import FuelLayer
from layers.car_lr_layer import CarLRLayer
from core.iracing_client import IRacingClient
from layers.twitch_chat_layer import TwitchChatLayer


LAYER_CLASSES = {
    "standings": StandingsLayer,
    "fuel": FuelLayer,
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
                {"id": "twitchchat", "title": "Twitch Chat", "visible": True},
            ]
        }

        self.layers = {}
        self.locked = False

        # Gerenciador de layouts
        self.store = LayoutStore(QtWidgets.QWidget())

        # Carregar estados de camadas previamente salvos
        saved_states = self.store.load_layer_states()

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
                # Se já temos estado salvo, respeita ele
                visible = saved_states.get(meta["id"], meta.get("visible", True))
                layer.setVisible(visible)

        # Painel de controle
        self.panel = ControlPanel(self.cfg["initial_layers"], self)

        # Restaurar geometria do painel (se existir)
        saved_panel_geo = self.store.load_control_panel_geometry()
        if saved_panel_geo:
            self.panel.setGeometry(
                saved_panel_geo["x"],
                saved_panel_geo["y"],
                saved_panel_geo["w"],
                saved_panel_geo["h"],
            )

        self.panel.show()

        # Cliente iRacing (thread + sinal Qt)
        self.iracing_client = IRacingClient()
        self.iracing_client.data_ready.connect(self._dispatch_iracing_data)
        self.iracing_client.start()

        # 🎨 Aplica tema moderno
        dark_stylesheet = """
        QWidget {
            background-color: #000000;
            color: #f5f5f5;
            font-family: 'Segoe UI';
            font-size: 11pt;
        }

        QPushButton {
            background-color: #3a3a4f;
            border: 1px solid #5a5a7f;
            border-radius: 6px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #50506a;
        }
        QPushButton:pressed {
            background-color: #2d2d3d;
        }

        QCheckBox {
            spacing: 8px;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border-radius: 3px;
            border: 1px solid #aaa;
            background: #2d2d3d;
        }
        QCheckBox::indicator:checked {
            background-color: #4CAF50;
            border: 1px solid #4CAF50;
        }

        QLabel {
            font-weight: bold;
            margin-top: 6px;
            margin-bottom: 2px;
            color: #cfcfe0;
        }

        QGroupBox {
            border: 1px solid #5a5a7f;
            border-radius: 8px;
            margin-top: 10px;
            padding: 6px;
            color: #f5f5f5;
            font-weight: bold;
        }

        QTabWidget::pane {
            border: 1px solid #5a5a7f;
            background: #2d2d3d;
            border-radius: 6px;
        }
        QTabBar::tab {
            background: #2d2d3d;
            color: #f5f5f5;
            padding: 6px 12px;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
        }
        QTabBar::tab:selected {
            background: #3a3a4f;
            font-weight: bold;
        }
        """
        self.setStyleSheet(dark_stylesheet)

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
            #print(f"Saving layout for {layer_id}")
            rect = layer.save_layout()
            self.store.save_layer(layer_id, rect)

        # Salvar também estados dos checkboxes
        states = {lid: cb.isChecked() for lid, cb in self.panel.checkboxes.items()}
        self.store.save_layer_states(states)

        # Salvar geometria do painel
        self.store.save_control_panel_geometry(self.panel.geometry())

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
        #print("Encerrando OverlayApp...")
        # Salva antes de sair
        self.save_layouts()

        if hasattr(self, "iracing_client"):
            self.iracing_client.stop()
            self.iracing_client.wait()  # garante encerrar a thread sem crash

        super().closeAllWindows()
        event.accept()
