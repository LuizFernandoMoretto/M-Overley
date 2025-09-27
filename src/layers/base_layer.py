from PySide6 import QtCore, QtWidgets


class BaseLayer(QtWidgets.QWidget):
    def __init__(self, app, layer_id, title, initial_rect=None):
        super().__init__()
        self.app = app
        self.layer_id = layer_id
        self.title = title
        self._editing = False
        self._locked = False

        # Janela sem borda, sempre por cima
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowTitle(self.title)

        # Define geometria inicial
        if initial_rect:
            self.restore_geometry(initial_rect)
        else:
            self.setGeometry(100, 100, 300, 200)

        # ⚠️ Não chamamos self.show() aqui!
        # Cada subclasse deve chamar self.show() somente após montar sua UI.

    # ---------- MODO EDIÇÃO ----------
    def set_edit_mode(self, editing: bool):
        """Ativa ou desativa o modo edição (mover/redimensionar)"""
        self._editing = editing

        if editing:
            # janela normal com borda → permite arrastar/redimensionar
            self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.WindowStaysOnTopHint)
        else:
            # volta para overlay sem borda
            self.setWindowFlags(
                QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.Tool
            )

        self.show()

    # ---------- BLOQUEIO ----------
    def set_locked(self, locked: bool):
        """Trava/destrava o layer"""
        self._locked = locked
        self.setEnabled(not locked)

    # ---------- SALVAR/RESTORE ----------
    def save_layout(self):
        rect = self.geometry()
        norm = self.app.store._normalize(rect)
        return norm

    def restore_geometry(self, rect):
        screen = QtWidgets.QApplication.primaryScreen().size()
        x = int(rect["x"] * screen.width())
        y = int(rect["y"] * screen.height())
        w = int(rect["w"] * screen.width())
        h = int(rect["h"] * screen.height())
        self.setGeometry(x, y, w, h)
