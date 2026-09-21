# HuntezPatch — Dokumentation (Deutsch)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**HuntezPatch v1.02** ist ein Mod-Generator für **World of Tanks Blitz** (Wargaming) und **Tanks Blitz** (Lesta Games).
Er erstellt drei Mods: **HiddenTanks** (zeigt versteckte Panzer im Forschungsbaum), **AutoRanksOFF**
(entfernt die Rang-Sperren der Hangar-Oberfläche) und **RandomTankSelector** (Würfel-Button für Zufallspanzer im Hangar).

> **Dokumentation in anderen Sprachen:**
> [🇬🇧 English](README.en.md) · [🇷🇺 Русский](README.ru.md) · [🇺🇦 Українська](README.uk.md) ·
> [🇹🇷 Türkçe](README.tr.md) · [🇵🇱 Polski](README.pl.md)

---

## Inhaltsverzeichnis

- [Mods](#mods)
- [Funktionen](#funktionen)
- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Schnellstart](#schnellstart)
- [Vorgangsmodi](#vorgangsmodi)
- [DVPL-Modi](#dvpl-modi)
- [DLC (Mikro-Updates)](#dlc-mikro-updates)
- [Export-Layout](#export-layout)
- [Backup und Wiederherstellung](#backup-und-wiederherstellung)
- [Oberfläche](#oberfläche)
- [Fehlerbehebung](#fehlerbehebung)
- [Projektstruktur](#projektstruktur)
- [Sprachen](#sprachen)
- [Autor](#autor)

---

## Mods

| Mod | Funktion | Dateien (relativ zu `Data/`) |
|-----|----------|------------------------------|
| **HiddenTanks** | Zeigt ALLE versteckten Panzer im Forschungsbaum (Premium, Sammler, Test, entfernte). Der Kauf hängt weiterhin von den Angeboten ab — der Mod zeigt die Fahrzeuge nur an. Sortierung pro Stufe: **normal → Sammler → Premium**, innerhalb der Gruppe nach Klasse (**LT → MT → HT → TD**). | `Configs/TechTree/*_tree.yaml` (9 Nationen), `XML/item_defs/vehicles/*/list.xml` (9 Nationen) |
| **AutoRanksOFF** | Entfernt die Rang-Sperren: Kampf-Button immer sichtbar, Rang-Hinweise versteckt, Aufstiegs-Events entfernt, die Feier „Dein Panzer hat einen Rang“ erscheint nie. | `UI/Screens3/Lobby/Hangar/Hangar.yaml`, `UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml`, `UI/Screens3/Lobby/Inventory/Inventory.yaml`, `UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml` |
| **RandomTankSelector** | Fügt der Panzerleiste einen Button mit zwei Würfeln hinzu — per Klick wird ein zufälliger Panzer gewählt. Das Würfelsymbol wird bei jeder Generierung erzeugt. | `UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.yaml`, `UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.actions`, `Gfx/Lobby/icons/randomtankselector_button_icon.packed.webp` (+ @2x, neue Dateien) |

Dieselben Infos stehen in der App hinter dem **?**-Button der Mod-Karte.

## Funktionen

- Drei Mods in einem Tool, unabhängig wählbar (Karten mit Checkbox).
- Vorgänge **Generieren** (Staging: temp → Backup → Ersetzen) und **Exportieren** (`Mod`- + `Backup`-Paket zum Teilen).
- Dateimodi **DVPL / NON-DVPL**; DLC-Dateien immer DVPL.
- **DLC-Unterstützung (Mikro-Updates)** mit Auto-Hinweis und Ein-Klick-Öffnen des `packs`-Ordners.
- Eingebauter **Dateibrowser** (Tabs `Spieldateien` / `DLC-Dateien`): fauler Baum, Highlighting der Mod-Dateien, Statusspalte `MODIFIZIERT`, Ansicht „Nur Mod-Dateien“.
- Kopierfreundliches Protokoll (`Strg+C` / `Strg+A`, Rechtsklick-Menü, beide Tastaturlayouts).
- Fortschrittsbalken mit Dateizähler, Hintergrund-Operationen (UI friert nie ein).
- 6 Sprachen, Hell/Dunkel-Designs, portable Einstellungen.

## Voraussetzungen

- **Windows** mit **Python 3.8+** (`python --version`).
- Abhängigkeiten aus `requirements.txt`: `lz4`, `PyYAML`, `Pillow` (`tkinter` ist eingebaut).

## Installation

```bat
autoinstall_modules.bat
start_program.bat
```

Oder manuell:

```bat
pip install -r requirements.txt
python main.py
```

Keine Installation nötig — das Programm ist portabel. Einstellungen liegen in `config.json` neben `main.py`.

## Schnellstart

1. **Spielordner** wählen (der mit `Data/` darin).
2. **Projekt** (`Wargaming` / `Lesta Games`) und **DVPL-Modus** wählen (siehe unten).
3. Mods anhaken.
4. **▶ Ausführen** → **Generieren (Ersetzen)** (oder **Generieren (Export)** für ein teilbares Paket).
5. Spiel starten und prüfen. Rollback jederzeit mit **↩ Originale wiederherstellen**.

## Vorgangsmodi

| Modus | Verhalten |
|-------|-----------|
| **Generieren (Ersetzen)** | Dateien werden zuerst in einem Temp-Ordner transformiert (nie direkt im Spiel), Originale gesichert, dann die fertigen Dateien kopiert. DLC-Dateien erhalten Read-only, wie der Client es erwartet. |
| **Generieren (Export)** | Der Spielordner wird nicht angerührt. Paket unter `result/<Name>_<Version>/`: `Mod/` (gepatchte Dateien) und `Backup/` (Originale). |

## DVPL-Modi

| Modus | Verhalten |
|-------|-----------|
| **DVPL** | `.dvpl`-Container werden dekodiert → bearbeitet → neu kodiert. Wählen, wenn der Spielordner `.dvpl` enthält (z. B. Steam-Client). |
| **NON-DVPL** | Nur bereits entpackte (plain) Dateien werden verarbeitet; `.dvpl` wird mit Hinweis übersprungen. |

> **DLC-Dateien sind IMMER DVPL**, unabhängig vom Modus — Mikro-Updates werden nie entpackt geliefert.

## DLC (Mikro-Updates)

Bringt das Spiel ein Mikro-Update, überlagern dessen Dateien die Basisdateien — sie müssen mitgepatcht werden:

| Projekt | `packs`-Ordner |
|---------|----------------|
| Wargaming | `%userprofile%/AppData/Local/wotblitz/packs` |
| Lesta Games | `%userprofile%/Documents/TanksBlitz/packs` |

- **DLC-Dateien ändern** anhaken, um sie einzubeziehen.
- Existieren DLC-Dateien, ist die Checkbox aber aus, warnt die App.
- Der Button **DLC-Ordner** öffnet ein Zwei-Auswahl-Popup (`Wargaming` / `Lesta Games`) mit dem passenden `packs`-Ordner im Explorer.

## Export-Layout

```
result/BlitzMods_<Mods>_<Version>/
├── Mod/
│   ├── Data/    <- gepatchte Spieledateien (plain oder .dvpl, wie gefunden)
│   └── packs/   <- gepatchte DLC-Dateien (immer .dvpl, in packs des Spiels kopieren)
└── Backup/
    ├── Data/    <- originale Spieledateien
    └── packs/   <- originale DLC-Dateien
```

## Backup und Wiederherstellung

- Generieren sichert pro Mod unter `<Spiel>/BlitzMods_Backup/<Mod>/{Game,DLC}/...`.
- **↩ Originale wiederherstellen** kopiert sie zurück (DLC wieder read-only) und löscht danach den Backup-Ordner des Mods — die gesicherten Originale haben ihren Zweck erfüllt, ein neues Generieren legt das Backup neu an.
- Der Browser markiert jede Datei mit Generatorsignatur (`HuntezPatch - Generated`) als **MODIFIZIERT** — inklusive aller Ordner darüber. Nach Wiederherstellung erlöschen die Markierungen von selbst.

## Oberfläche

- **Kopfzeile**: Titel, Sprachbutton (`RU/EN/…`, Popup), Designbutton (`☀/☾`).
- **Spielpfad**: Zeile über die volle Breite mit Gültigkeitspunkt und Durchsuchen-Button rechts.
- **Linke Spalte** (scrollbar): Mod-Karten (Klick = an/aus, `?` = Doku), Segment-Schalter Projekt und DVPL, DLC-Block, Aktionsbuttons.
- **Rechts**: große Tabs — **Protokoll**, **Spieldateien**, **DLC-Dateien**. Datei-Tabs haben Aktualisieren / Im Explorer und die Ansicht **Nur Mod-Dateien** (Hierarchie pro Mod mit Größe und Spiel/DLC-Status).
- **Statusleiste**: Statuspunkt + Text, Live-Fortschrittsbalken (`Fortschritt: 42% · 5/12`, idle `© Huntez`), Version.

Alle Einstellungen werden automatisch gespeichert und beim Start wiederhergestellt. Beim allerersten Start kommen Sprache und Design aus dem System.

## Fehlerbehebung

| Symptom | Lösung |
|---------|--------|
| `Ungültiger Spielpfad (kein Data-Ordner)` | Ordner wählen, der `Data/` enthält. |
| `Datei fehlt … übersprungen` in NON-DVPL | Das Spiel hält hier `.dvpl` — **DVPL**-Modus wählen. |
| `! NON-DVPL überspringt DVPL-Datei` | Nur ein Hinweis, kein Fehler — siehe oben. |
| `Kein Backup für <Mod>` | Mod mindestens einmal generieren. |
| Rang-Feier erscheint trotzdem | AutoRanksOFF neu generieren (Hauptschalter `ranksAvailable` nötig), vorher Original zurückholen. |
| Lila Schachbrett statt Würfel | RandomTankSelector neu generieren, vorher Original zurückholen (Symboldatei fehlt). |
| Spiel aktualisiert | Generieren erneut laufen lassen, `MODIFIZIERT`-Markierungen prüfen. |

## Projektstruktur

```
HuntezPatch/
├── main.py                  # Einstiegspunkt
├── requirements.txt
├── start_program.bat / autoinstall_modules.bat
├── config.json              # generiert: deine Einstellungen (nicht in git)
├── core/                    # DVPL-Codec, Datei-Ops, Mod-Engines (Mods/hidden_tanks, Mods/autoranks, Mods/random_tank)
├── gui/                     # Oberfläche (Karten, Browser, Popups, Protokoll)
├── locales/                 # UI-Strings ru/en/uk/de/tr/pl
├── Documentation/           # dieses Handbuch in 6 Sprachen
└── result/                  # generiert: Export-Pakete (nicht in git)
```

Zur Laufzeit entstehen nur `config.json` und `result/` — der Rest ist Quellcode.
Vollständige Liste in [.gitignore](../.gitignore).

## Sprachen

UI und Doku: **RU · EN · UK · DE · TR · PL**. Fehlende Strings fallen auf Englisch zurück.

## Autor

© Huntez — Bugs und Ideen gern auf GitHub.
