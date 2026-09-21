# HuntezPatch — Documentation (English)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**HuntezPatch v1.02** is a mod generator for **World of Tanks Blitz** (Wargaming) and **Tanks Blitz** (Lesta Games).
It builds three mods: **HiddenTanks** (reveals hidden tanks in the research tree), **AutoRanksOFF**
(removes rank gating from the hangar UI) and **RandomTankSelector** (adds a random-tank dice button to the hangar).

> **Documentation in other languages:**
> [🇷🇺 Русский](README.ru.md) · [🇺🇦 Українська](README.uk.md) · [🇩🇪 Deutsch](README.de.md) ·
> [🇹🇷 Türkçe](README.tr.md) · [🇵🇱 Polski](README.pl.md)

---

## Table of Contents

- [Mods](#mods)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Operation Modes](#operation-modes)
- [DVPL Modes](#dvpl-modes)
- [DLC (Micro-Updates)](#dlc-micro-updates)
- [Export Layout](#export-layout)
- [Backup and Restore](#backup-and-restore)
- [Interface Overview](#interface-overview)
- [Troubleshooting](#troubleshooting)
- [Project Structure](#project-structure)
- [Languages](#languages)
- [Author](#author)

---

## Mods

| Mod | What it does | Files (relative to `Data/`) |
|-----|--------------|------------------------------|
| **HiddenTanks** | Shows ALL hidden tanks in the research tree (premium, collectible, test, deprecated). Purchase still depends on the developers' offers — the mod only reveals the vehicles. Hidden tanks are sorted per level as **ordinary → collectible → premium**, and by class inside each group (**LT → MT → HT → TD**). | `Configs/TechTree/*_tree.yaml` (9 nations), `XML/item_defs/vehicles/*/list.xml` (9 nations) |
| **AutoRanksOFF** | Removes rank gating from the UI: the Battle button is always visible, rank-unlock hints are hidden, rank-up events are removed, and the “your tank has a rank” celebration never triggers. | `UI/Screens3/Lobby/Hangar/Hangar.yaml`, `UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml`, `UI/Screens3/Lobby/Inventory/Inventory.yaml`, `UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml` |
| **RandomTankSelector** | Adds a two-dice button to the hangar tanks panel — pressing it selects a random owned tank. The dice icon is generated on every run. | `UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.yaml`, `UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.actions`, `Gfx/Lobby/icons/randomtankselector_button_icon.packed.webp` (+ @2x, new files) |

Click the **?** button on a mod card in the app for the same info in your language.

## Features

- Three mods in one utility, selectable independently (checkbox cards).
- **Generate** (staged: temp dir → backup → replace) and **Export** (ready-to-share `Mod` + `Backup` bundle) operations.
- **DVPL / NON-DVPL** file modes; DLC files are always DVPL.
- **DLC (micro-update) support** with auto-detection hint and one-click `packs` folder opening.
- Built-in **file explorer** (`Game files` / `DLC files` tabs): lazy tree, mod-file highlighting, `MODIFIED` status column, mod-only checklist view.
- Copy-friendly log (`Ctrl+C` / `Ctrl+A`, right-click menu, both keyboard layouts).
- Progress bar with file counts, background operations (the UI never freezes).
- 6 interface languages, light/dark themes, portable settings.

## Requirements

- **Windows** with **Python 3.8+** (`python --version`).
- Dependencies from `requirements.txt`: `lz4`, `PyYAML`, `Pillow` (`tkinter` is built in).

## Installation

```bat
autoinstall_modules.bat
start_program.bat
```

Or manually:

```bat
pip install -r requirements.txt
python main.py
```

No installation is needed — the program is portable. Settings live in `config.json` next to `main.py`.

## Quick Start

1. Start the app, set the **game folder** (the one containing `Data/`), e.g. `C:/Program Files/Steam/steamapps/common/World of Tanks Blitz`.
2. Pick the **project** (`Wargaming` / `Lesta Games`) and **DVPL mode** (see below).
3. Tick the mods you want.
4. Press **▶ Run** → **Generate (Replace)** (or **Generate (Export)** for a shareable bundle).
5. Launch the game and check the result. Roll back anytime with **↩ Restore originals**.

## Operation Modes

| Mode | Behaviour |
|------|-----------|
| **Generate (Replace)** | Files are transformed in a temp staging dir first (never inside the game folder directly), originals are backed up, then the finished files are copied over. DLC files get the read-only attribute, like the client expects. |
| **Generate (Export)** | Nothing in the game folder is touched. A bundle is written to `result/<name>_<version>/` with `Mod/` (patched files) and `Backup/` (originals) inside. |

## DVPL Modes

| Mode | Behaviour |
|------|-----------|
| **DVPL** | Game `.dvpl` containers are decoded → edited → re-encoded. Prefer it when the game folder contains `.dvpl` files (e.g. the Steam client). |
| **NON-DVPL** | Only already-unpacked (plain) game files are processed; `.dvpl` files are skipped with a log hint. |

> **DLC files are ALWAYS DVPL**, regardless of the selected mode — micro-update packs are never shipped unpacked.

## DLC (Micro-Updates)

If the game ships a micro-update, its files override the base ones and must be patched too:

| Project | `packs` folder |
|---------|----------------|
| Wargaming | `%userprofile%/AppData/Local/wotblitz/packs` |
| Lesta Games | `%userprofile%/Documents/TanksBlitz/packs` |

- Tick **Modify DLC files** to include them.
- If DLC files for the selected mods exist but the checkbox is off, the app warns you.
- The **DLC folder** button opens a two-option popup (`Wargaming` / `Lesta Games`) that opens the right `packs` folder in Explorer.

## Export Layout

```
result/BlitzMods_<mods>_<version>/
├── Mod/
│   ├── Data/    <- patched game files (plain or .dvpl, as found)
│   └── packs/   <- patched DLC files (always .dvpl, copy into the game's packs)
└── Backup/
    ├── Data/    <- original game files
    └── packs/   <- original DLC files
```

## Backup and Restore

- Generate keeps per-mod backups in `<game>/BlitzMods_Backup/<mod>/{Game,DLC}/...`.
- **↩ Restore originals** copies them back (DLC files back to read-only) and then deletes the mod's backup folder — the saved originals served their purpose, a fresh generate recreates the backup.
- The explorer marks every file carrying a generator signature (`HuntezPatch - Generated`) as **MODIFIED** — including deep parent folders. After restore the marks clear by themselves.

## Interface Overview

- **Header**: app title, language button (`RU/EN/…` popup), theme button (`☀/☾`).
- **Game path**: full-width row with a green/red validity dot and a right-side Browse button.
- **Left column** (scrollable): mod cards (click to toggle, `?` for docs), project and DVPL segmented switches, DLC block, action buttons.
- **Right**: big tabbed area — **Log**, **Game files**, **DLC files**. The file tabs have Refresh / In-Explorer buttons and a **Mod files only** checklist (per-mod folder hierarchy with size and Game/DLC state).
- **Status bar**: state dot + text, live progress bar (`Progress: 42% · 5/12`, `© Huntez` when idle), version.

All settings (language, theme, path, mods, project, mode, DLC flag, window geometry) are saved automatically and restored on next start. On the very first start, language and theme are taken from the OS.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Invalid game path (no Data folder)` | Point the app at the folder that contains `Data/`. |
| `Missing file … skipping` in NON-DVPL | The game ships `.dvpl` here — switch to **DVPL** mode (or unpack the files). |
| `! NON-DVPL skips DVPL file` | Same as above: informational hint, not an error. |
| `No saved originals for <mod>` on restore | Generate the mod at least once first. |
| Rank celebration still pops up | Regenerate AutoRanksOFF (the `ranksAvailable` master switch is required) after returning the original. |
| Purple checker instead of dice | Regenerate RandomTankSelector after returning the original (the icon file may be missing). |
| Game updated | Re-run Generate; then check the MODIFIED marks. |

## Project Structure

```
HuntezPatch/
├── main.py                  # entry point
├── requirements.txt
├── start_program.bat / autoinstall_modules.bat
├── config.json              # generated: your settings (not in git)
├── core/                    # dvpl codec, file ops, per-mod engines (Mods/hidden_tanks, Mods/autoranks, Mods/random_tank)
├── gui/                     # Tkinter interface (tiles, explorer, popups, log)
├── locales/                 # ru/en/uk/de/tr/pl interface strings
├── Documentation/           # this manual in 6 languages
└── result/                  # generated: export bundles (not in git)
```

Only `config.json` and `result/` are created at runtime — everything else is stock source.
See [.gitignore](../.gitignore) for the full list.

## Languages

Interface and docs: **RU · EN · UK · DE · TR · PL**. Missing strings fall back to English.

## Author

© Huntez — issues and ideas are welcome on GitHub.
