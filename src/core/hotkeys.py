import threading
try:
    import keyboard  # type: ignore
except Exception:
    keyboard = None

class GlobalHotkey:
    def __init__(self, combo: str, callback):
        self.combo = combo
        self.callback = callback
        self._hooked = False

    def start(self):
        if keyboard is None or self._hooked:
            return
        self._hooked = True
        threading.Thread(target=self._listen, daemon=True).start()

    def _listen(self):
        keyboard.add_hotkey(self.combo, self.callback)
        keyboard.wait()
