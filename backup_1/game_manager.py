import subprocess, threading, signal, os, time

class GameManager:
    def __init__(self):
        self.process     = None
        self.game_info   = None
        self.start_time  = None
        self._monitor    = None
        self.on_exit     = None

    def launch(self, cmd, name):
        if self.process and self.process.poll() is None:
            self.kill()
        self.process = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid)
        self.game_info = {"name": name, "exec": cmd,
                          "started": int(time.time()), "pid": self.process.pid}
        self.start_time = time.time()
        self._monitor = threading.Thread(target=self._watch, daemon=True)
        self._monitor.start()
        print(f"[gameshell] Launched: {name} (pid {self.process.pid})")

    def _watch(self):
        if self.process:
            self.process.wait()
            self.process   = None
            self.game_info = None
            if self.on_exit:
                self.on_exit()

    def kill(self):
        if self.process:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            except Exception:
                try: self.process.terminate()
                except: pass
            self.process   = None
            self.game_info = None
            self.start_time= None

    @property
    def running(self):
        return self.process is not None and self.process.poll() is None

    def elapsed(self):
        if not self.start_time:
            return "00:00"
        secs = int(time.time() - self.start_time)
        return f"{secs//60:02d}:{secs%60:02d}"

game_mgr = GameManager()
