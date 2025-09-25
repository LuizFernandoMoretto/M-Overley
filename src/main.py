from core.app import OverlayApp
import sys

if __name__ == "__main__":
    app = OverlayApp(sys.argv)
    sys.exit(app.exec())