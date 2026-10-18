# HuntezPatch

<img src="huntezpatch_icon.png" width="128" alt="HuntezPatch icon">

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Version](https://img.shields.io/badge/Version-v1.05-orange.svg)

Mod generator for **World of Tanks Blitz** (Wargaming) and **Tanks Blitz** (Lesta Games):
**HiddenTanks** (shows hidden tanks), **AutoRanksOFF** (disables rank gating),
**RandomTankSelector** (random-tank dice button) and **SelectableClusters**
(login server list with per-cluster picker).

## Download

Get `HuntezPatch-1.05.exe` from
[Releases](https://github.com/HuntezWOTB/HuntezPatch/releases) — no Python install
needed, just run it.

Portable user data lives in `%LocalAppData%/HuntezProjects/HuntezPatch/`:
`huntezpatch_cfg.json` (settings, reset when the app version changes),
`backups/` (per-install originals for restore), `result/` (exported mod packages).

## Build from source

```bat
build.bat
```

Requires Windows + Python 3.8+. Output: `dist/HuntezPatch-1.05.exe`.
Launch from source with `start_program.vbs` (no console window).

## Documentation

- [🇬🇧 English](Documentation/README.en.md)
- [🇷🇺 Русский](Documentation/README.ru.md)
- [🇺🇦 Українська](Documentation/README.uk.md)
- [🇩🇪 Deutsch](Documentation/README.de.md)
- [🇹🇷 Türkçe](Documentation/README.tr.md)
- [🇵🇱 Polski](Documentation/README.pl.md)

## Author

© Huntez
