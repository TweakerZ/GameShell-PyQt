from PyQt6.QtCore import QThread, pyqtSignal
import time

class SDL2ControllerThread(QThread):
    nav_signal = pyqtSignal(str)
    button_signal = pyqtSignal(str)
    state_signal = pyqtSignal(object)

    DEADZONE = 0.20
    REPEAT_DELAY = 0.40
    REPEAT_RATE = 0.12

    def __init__(self):
        super().__init__()
        self._active = True
        self._nav_lock = False
        self._controller = None
        self._buttons = {}
        self._axes = {}

    def stop(self):
        self._active = False

    def run(self):
        try:
            import sdl2
            import sdl2.ext
        except ImportError:
            print("[gameshell] sdl2 not installed — controller disabled")
            return

        if sdl2.SDL_Init(sdl2.SDL_INIT_GAMECONTROLLER) != 0:
            print(f"[gameshell] SDL_Init failed: {sdl2.SDL_GetError()}")
            return

        try:
            for i in range(sdl2.SDL_NumJoysticks()):
                if sdl2.SDL_IsGameController(i):
                    self._controller = sdl2.SDL_GameControllerOpen(i)
                    if self._controller:
                        name = sdl2.SDL_GameControllerName(self._controller)
                        print(f"[gameshell] Controller: {name.decode() if name else 'Unknown'}")
                        break

            if not self._controller:
                print("[gameshell] No game controller found")
                return

            nav_held = {}
            last_emit = {}
            event = sdl2.SDL_Event()

            while self._active:
                while sdl2.SDL_PollEvent(event):
                    if event.type == sdl2.SDL_CONTROLLERBUTTONDOWN:
                        btn = self._map_sdl_button(event.cbutton.button)
                        if btn:
                            self._buttons[btn] = True
                            self.button_signal.emit(btn)
                    elif event.type == sdl2.SDL_CONTROLLERBUTTONUP:
                        btn = self._map_sdl_button(event.cbutton.button)
                        if btn:
                            self._buttons[btn] = False
                    elif event.type == sdl2.SDL_CONTROLLERAXISMOTION:
                        axis = self._map_sdl_axis(event.caxis.axis)
                        if axis:
                            val = event.caxis.value / 32767.0 if event.caxis.value >= 0 else event.caxis.value / 32768.0
                            self._axes[axis] = val

                now = time.time()
                dx = self._axes.get('lx', 0)
                dy = self._axes.get('ly', 0)
                dpad_up = self._buttons.get('dup', False)
                dpad_down = self._buttons.get('ddown', False)
                dpad_left = self._buttons.get('dleft', False)
                dpad_right = self._buttons.get('dright', False)

                dirs = {
                    'up': dy < -self.DEADZONE or dpad_up,
                    'down': dy > self.DEADZONE or dpad_down,
                    'left': dx < -self.DEADZONE or dpad_left,
                    'right': dx > self.DEADZONE or dpad_right,
                }

                for d, active in dirs.items():
                    if active:
                        first = nav_held.get(d, 0)
                        if first == 0:
                            nav_held[d] = now
                            self.nav_signal.emit(d)
                            last_emit[d] = now
                        elif now - first > self.REPEAT_DELAY:
                            if now - last_emit.get(d, 0) > self.REPEAT_RATE:
                                self.nav_signal.emit(d)
                                last_emit[d] = now
                    else:
                        nav_held[d] = 0

                self.state_signal.emit({
                    'axes': dict(self._axes),
                    'buttons': dict(self._buttons),
                })

                sdl2.SDL_Delay(16)

        finally:
            if self._controller:
                sdl2.SDL_GameControllerClose(self._controller)
            sdl2.SDL_Quit()

    def _map_sdl_button(self, sdl_button):
        import sdl2
        mapping = {
            sdl2.SDL_CONTROLLER_BUTTON_A: 'a',
            sdl2.SDL_CONTROLLER_BUTTON_B: 'b',
            sdl2.SDL_CONTROLLER_BUTTON_X: 'x',
            sdl2.SDL_CONTROLLER_BUTTON_Y: 'y',
            sdl2.SDL_CONTROLLER_BUTTON_BACK: 'select',
            sdl2.SDL_CONTROLLER_BUTTON_GUIDE: 'guide',
            sdl2.SDL_CONTROLLER_BUTTON_START: 'start',
            sdl2.SDL_CONTROLLER_BUTTON_LEFTSTICK: 'ls',
            sdl2.SDL_CONTROLLER_BUTTON_RIGHTSTICK: 'rs',
            sdl2.SDL_CONTROLLER_BUTTON_LEFTSHOULDER: 'lb',
            sdl2.SDL_CONTROLLER_BUTTON_RIGHTSHOULDER: 'rb',
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_UP: 'dup',
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_DOWN: 'ddown',
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_LEFT: 'dleft',
            sdl2.SDL_CONTROLLER_BUTTON_DPAD_RIGHT: 'dright',
        }
        return mapping.get(sdl_button)

    def _map_sdl_axis(self, sdl_axis):
        import sdl2
        mapping = {
            sdl2.SDL_CONTROLLER_AXIS_LEFTX: 'lx',
            sdl2.SDL_CONTROLLER_AXIS_LEFTY: 'ly',
            sdl2.SDL_CONTROLLER_AXIS_RIGHTX: 'rx',
            sdl2.SDL_CONTROLLER_AXIS_RIGHTY: 'ry',
            sdl2.SDL_CONTROLLER_AXIS_TRIGGERLEFT: 'lt',
            sdl2.SDL_CONTROLLER_AXIS_TRIGGERRIGHT: 'rt',
        }
        return mapping.get(sdl_axis)
