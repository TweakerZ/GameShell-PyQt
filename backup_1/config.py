import sys, os, pathlib

if getattr(sys, 'frozen', False):
    BASE_DIR = pathlib.Path(sys.executable).parent
    RESOURCE_BASE = BASE_DIR

    try:
        import PyQt6
        pyqt6_dir = pathlib.Path(PyQt6.__file__).parent
        possible = [
            pyqt6_dir / 'Qt6' / 'plugins',
            pyqt6_dir.parent / 'Qt6' / 'plugins',
            BASE_DIR / 'PyQt6' / 'Qt6' / 'plugins',
            BASE_DIR / 'qt6_plugins',
            BASE_DIR / 'plugins',
        ]
        for p in possible:
            if p.exists():
                os.environ['QT_PLUGIN_PATH'] = str(p)
                platform_dir = p / 'platforms'
                if platform_dir.exists():
                    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = str(platform_dir)
                break
    except Exception as e:
        print(f"[gameshell] Could not determine Qt plugin path: {e}")
else:
    BASE_DIR = pathlib.Path(__file__).parent.parent
    RESOURCE_BASE = BASE_DIR

GAMESHELL_DIR = pathlib.Path.home() / ".gameshell"
LIBRARY_FILE  = GAMESHELL_DIR / "library.json"
SETTINGS_FILE = GAMESHELL_DIR / "settings.json"

GAMESHELL_DIR.mkdir(parents=True, exist_ok=True)

def get_absolute_path(path_str):
    if path_str is None:
        return None
    path = pathlib.Path(path_str)
    if path.is_absolute():
        return str(path)
    return str((RESOURCE_BASE / path).resolve())
