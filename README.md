<h1 align="center">⚙️ BootlogoChanger</h1>

<p align="center">
  <img src="https://github.com/OwnerPlugins/BootlogoChanger/blob/main/usr/lib/enigma2/python/Plugins/Extensions/BootlogoChanger/plugin.png?raw=true" height="120">
</p>

<p align="center">
  <img src="https://komarev.com/ghpvc/?username=Belfagor2005" />
  <img src="https://img.shields.io/badge/version-1.06--r11-blue" />
<img src="https://img.shields.io/badge/Python-3.x-orange" />
  <a href="https://github.com/OwnerPlugins/BootlogoChanger/actions/workflows/pylint.yml">
    <img src="https://github.com/OwnerPlugins/BootlogoChanger/actions/workflows/pylint.yml/badge.svg" />
  </a>
</p>


Easily switch between different bootlogos on your Enigma2 receiver.  
This plugin allows you to preview, select, and randomly change bootlogos (bootlogo.mvi, bootlogo_wait.mvi, reboot.mvi, shutdown.mvi, etc.) from a user-defined directory.

---

## Features

- Browse folders containing complete bootlogo sets (`.mvi` files)
- Preview bootlogos before applying (requires `ffmpeg` for thumbnail generation)
- Apply a new bootlogo immediately
- Enable/disable random bootlogo selection at system startup
- Include or exclude specific bootlogos from random selection
- Delete old bootlogo files before copying (optional)
- Hide empty folders (no `.mvi` files)

---

## Installation

1. open telnet and put command::
   ```
   wget -q --no-check-certificate https://raw.githubusercontent.com/OwnerPlugins/BootlogoChanger/main/installer.sh -O - | /bin/sh
   ```
2. Restart Enigma2 GUI.
3. The plugin will appear in **Extensions** or **Plugins** menu.

---

## Usage

1. **Main Screen**  
   - List of available bootlogos (including the currently active one)  
   - Preview of the selected bootlogo (if `ffmpeg` is installed)  
   - Overview of which `.mvi` files are present in the selected folder

2. **Apply a bootlogo**  
   - Navigate to a bootlogo folder and press **OK** (full preview) or **GREEN** to save and exit.

3. **Random mode**  
   - Press **YELLOW** to enable/disable random selection at startup.  
   - When enabled, use **BLUE** to include/exclude a bootlogo from the random pool.

4. **Settings** (press **MENU**)  
   - Install/remove `ffmpeg` (required for preview thumbnails)  
   - Choose which logo to use for preview (`bootlogo.mvi`, `reboot.mvi`, etc.)  
   - Set the directory containing bootlogo folders (default: `/usr/share/`)  
   - Delete old `.mvi` files before copying new ones  
   - Hide empty folders (no `.mvi` files)  
   - Adjust status message display duration (1‑60 seconds)  
   - Enable debug output to console

---

## Best Practices

- Keep a backup of the original bootlogo folder (`/usr/share/`)
- Use folders with complete sets of `.mvi` files (at least `bootlogo.mvi`)
- Before changing bootlogos, ensure you have `ffmpeg` installed for previews
- For random mode, include only stable bootlogos (avoid experimental ones)
- Regularly clean up unused bootlogo folders to save space

---

## Technical Notes

- **Bootlogo directories**: each subfolder under the configured path must contain `.mvi` files  
- **Preview generation**: uses `ffmpeg` to extract the first frame of the selected `.mvi` file  
- **Randomization status** is stored in `Extensions/BootlogoChanger/BootlogoChanger.xml`  
- **Ignored bootlogos** are stored in `Extensions/BootlogoChanger/IgnoreBootlogos.xml`  
- **Target installation**: bootlogos are copied to `/usr/share/` (or your image‑specific path)

---

## Troubleshooting

- **No preview pictures**: Install `ffmpeg` via the plugin settings or manually:  
  `opkg install ffmpeg`
- **Bootlogo not changing**: Ensure the selected folder contains valid `.mvi` files and you have write permissions to `/usr/share/`
- **Random mode not working**: Check that at least one bootlogo is marked as *included* (green checkmark)  
- **Plugin not appearing**: Restart Enigma2 or check that the folder structure is correct (`Extensions/BootlogoChanger/plugin.py`)
- **Copy failed**: Verify that the destination directory is writable and has enough free space

---

## Credits

- **Original author**: thirsty73  
- **Python 3 porting & fixes**: Lululla  
- **Last update**: 17.04.2026

---

## License

This plugin is free software; you may modify it under the terms of the original license.  
Distribution without source code is not permitted.

