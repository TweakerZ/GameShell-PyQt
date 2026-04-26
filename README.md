# GameShell PyQt6

A modern game launcher built with PyQt6 for Linux.

![GameShell](screenshot.png)

## Features

- **Desktop Entry Import**: Drag and drop `.desktop` files directly into the launcher
- **AppImage Support**: Launch AppImage executables seamlessly
- **Desktop Export**: Export games to `.desktop` format compatible with:
  - Faugus Launcher
  - Lutris
  - PCSX2
  - Eden Emulator
  - Other Linux desktop launchers
- **Game Management**: Organize games with recently added, recently played and favorites categories
- **Now Playing**: See currently running games in the home page & now playing dialog

## Dependencies

### Core Requirements

- **Python 3.10+**
- **PyQt6** - Modern Qt bindings for Python
  ```bash
  pip install PyQt6
  ```
- **PySDL2** - Python bindings for SDL2
  ```bash
  pip install PySDL2
  ```

### Optional Dependencies

- **MangoHud** - Gaming performance overlay (for launch options)
  ```bash
  # Arch Linux
  sudo pacman -S mangohud
  
  # Debian/Ubuntu
  sudo apt install mangohud
  ```
- **gamescope** - Steam's gaming compositor (for launch options)
- **lsfgvk** - lossless scaling frame gen for linux by Pancake

## Installation

### From Source

```bash
git clone https://github.com/TweakerZ/GameShell-PyQt.git
cd GameShell-PyQt
pip install -r requirements.txt
python -m src
```

### Build Executable (Optional)

```bash
pip install pyinstaller
pyinstaller gameshell.spec
```

The executable will be created in `dist/gameshell`.

## Usage

### Adding Games

1. **Drag and Drop**: Drag a `.desktop` file or AppImage onto the exec/command field in the add game page
2. **Manual Add**: Click the + button and browse for executables
3. **Import**: Import existing games from libraries from other launchers (importing their `.desktop` file)

### Running Games

1. Select a game from the grid
2. Click **Play** or press Enter
3. (Optional) Configure launch options via **Edit**

### Launch Options

- **MangoHud**: Enable performance overlay
- **Wine FSR**: Enable Wine FSR upscaling
- **LSFG-VK**: For frame generation
- **Gamescope**: Run in gaming compositor

### Data Storage

Games and settings are stored in `~./gameshell/`:
- `~./gameshell/libraries.json` - Game library
- `~./gamesshell/settings.json` - Application settings

## Compatible Launchers & Emulators

GameShell can import `.desktop` files from:

- **Faugus Launcher**
- **Lutris**
- **PCSX2**
- **Eden Emulator**
- Any launcher that exports standard `.desktop` files

## Troubleshooting

### Games not launching
- Check the game executable path is correct
- Ensure the file has execute permissions: `chmod +x game_file`

### Import not working
- Ensure the `.desktop` file has a valid `Exec` line
- Check file permissions

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## License

MIT License - see [LICENSE](LICENSE) for details.
