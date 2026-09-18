# HuntezPatch — Dokumentacja (Polski)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**HuntezPatch v1.01** to generator modów do **World of Tanks Blitz** (Wargaming) i **Tanks Blitz** (Lesta Games).
Buduje trzy mody: **HiddenTanks** (pokazuje ukryte czołgi w drzewku badań), **AutoRanksOFF**
(usuwa blokady rang z interfejsu hangaru) i **RandomTankSelector** (przycisk-kości losujące czołg w hangarze).

> **Dokumentacja w innych językach:**
> [🇬🇧 English](README.en.md) · [🇷🇺 Русский](README.ru.md) · [🇺🇦 Українська](README.uk.md) ·
> [🇩🇪 Deutsch](README.de.md) · [🇹🇷 Türkçe](README.tr.md)

---

## Spis treści

- [Mody](#mody)
- [Funkcje](#funkcje)
- [Wymagania](#wymagania)
- [Instalacja](#instalacja)
- [Szybki start](#szybki-start)
- [Tryby operacji](#tryby-operacji)
- [Tryby DVPL](#tryby-dvpl)
- [DLC (mikroaktualizacje)](#dlc-mikroaktualizacje)
- [Układ eksportu](#układ-eksportu)
- [Backup i przywracanie](#backup-i-przywracanie)
- [Przegląd interfejsu](#przegląd-interfejsu)
- [Rozwiązywanie problemów](#rozwiązywanie-problemów)
- [Struktura projektu](#struktura-projektu)
- [Języki](#języki)
- [Autor](#autor)

---

## Mody

| Mod | Co robi | Pliki (względem `Data/`) |
|-----|---------|------------------------------|
| **HiddenTanks** | Pokazuje WSZYSTKIE ukryte czołgi w drzewku badań (premium, kolekcjonerskie, testowe, usunięte). Zakup nadal zależy od ofert deweloperów — mod tylko pokazuje pojazdy. Sortowanie ukrytych na poziomie: **zwykłe → kolekcjonerskie → premium**, w grupie wg klasy (**LT → MT → HT → TD**). | `Configs/TechTree/*_tree.yaml` (9 nacji), `XML/item_defs/vehicles/*/list.xml` (9 nacji) |
| **AutoRanksOFF** | Usuwa blokady rang: przycisk „Do boju“ zawsze widoczny, podpowiedzi o randze ukryte, eventy awansu usunięte, celebracja „twój czołg zdobył rangę” nigdy nie wyskakuje. | `UI/Screens3/Lobby/Hangar/Hangar.yaml`, `UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml`, `UI/Screens3/Lobby/Inventory/Inventory.yaml`, `UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml` |
| **RandomTankSelector** | Dodaje przycisk z dwiema kośćmi do panelu czołgów — kliknięcie wybiera losowy czołg. Ikona kości jest generowana przy każdej generacji. | `UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.yaml`, `UI/Screens3/Lobby/Hangar/TanksPanel/TanksPanel.actions`, `Gfx/Lobby/icons/randomtankselector_button_icon.packed.webp` (+ @2x, nowe pliki) |

Te same informacje są w programie pod przyciskiem **?** na karcie moda.

## Funkcje

- Trzy mody w jednym narzędziu, wybierane niezależnie (karty-checkboxy).
- Operacje **Generuj** (staging: temp → backup → zamiana) i **Eksportuj** (paczka `Mod` + `Backup` do rozdawania).
- Tryby plików **DVPL / NON-DVPL**; pliki DLC zawsze DVPL.
- **Wsparcie DLC (mikroaktualizacji)** z auto-podpowiedzią i otwieraniem folderu `packs` jednym klikiem.
- Wbudowany **eksplorator** (zakładki `Pliki gry` / `Pliki DLC`): leniwe drzewo, podświetlanie plików modów, kolumna statusu `ZMODYFIKOWANY`, widok „Tylko pliki modów”.
- Wygodny dziennik (kopiowanie `Ctrl+C` / `Ctrl+A`, menu prawego przycisku, oba układy klawiatury).
- Pasek postępu z liczbą plików, operacje w tle (interfejs nie wiesza się).
- 6 języków, jasny/ciemny motyw, przenośne ustawienia.

## Wymagania

- **Windows** z **Python 3.8+** (`python --version`).
- Zależności z `requirements.txt`: `lz4`, `PyYAML`, `Pillow` (`tkinter` wbudowany).

## Instalacja

```bat
autoinstall_modules.bat
start_program.bat
```

Lub ręcznie:

```bat
pip install -r requirements.txt
python main.py
```

Instalacja nie jest potrzebna — program jest przenośny. Ustawienia w `config.json` obok `main.py`.

## Szybki start

1. Wskaż **folder gry** (ten z `Data/` w środku).
2. Wybierz **projekt** (`Wargaming` / `Lesta Games`) i **tryb DVPL** (patrz niżej).
3. Zaznacz mody.
4. Kliknij **▶ Wykonaj** → **Generuj (Zamień)** (albo **Generuj (Eksport)** na paczkę do rozdawania).
5. Uruchom grę i sprawdź. Wycofanie w każdej chwili — **↩ Przywróć oryginał**.

## Tryby operacji

| Tryb | Zachowanie |
|------|-----------|
| **Generuj (Zamień)** | Pliki najpierw modyfikowane w folderze tymczasowym (nie w grze!), oryginały backupowane, potem gotowe pliki kopiowane na miejsce. Pliki DLC dostają atrybut read-only, jak oczekuje klient. |
| **Generuj (Eksport)** | Folder gry nietknięty. Paczka ląduje w `result/<nazwa>_<wersja>/`: `Mod/` (spatchowane pliki) i `Backup/` (oryginały). |

## Tryby DVPL

| Tryb | Zachowanie |
|------|-----------|
| **DVPL** | Kontenery `.dvpl` są rozpakowywane → edytowane → pakowane z powrotem. Wybierz go, gdy w folderze gry leżą `.dvpl` (np. klient Steam). |
| **NON-DVPL** | Przetwarzane są tylko już rozpakowane (plain) pliki; `.dvpl` pomijane z podpowiedzią w dzienniku. |

> **Pliki DLC są ZAWSZE DVPL** niezależnie od trybu — mikroaktualizacje nie przychodzą rozpakowane.

## DLC (mikroaktualizacje)

Jeśli gra przywiozła mikroaktualizację, jej pliki przykrywają bazowe — trzeba je też patchować:

| Projekt | Folder `packs` |
|---------|----------------|
| Wargaming | `%userprofile%/AppData/Local/wotblitz/packs` |
| Lesta Games | `%userprofile%/Documents/TanksBlitz/packs` |

- Włącz **Modyfikuj pliki DLC**, by je objąć.
- Jeśli pliki DLC modów istnieją, a checkbox jest wyłączony — program ostrzeże.
- Przycisk **Folder DLC** otwiera wybór (`Wargaming` / `Lesta Games`) z otwarciem właściwego `packs` w eksploratorze.

## Układ eksportu

```
result/BlitzMods_<mody>_<wersja>/
├── Mod/
│   ├── Data/    <- spatchowane pliki gry (plain lub .dvpl, jak leżały)
│   └── packs/   <- spatchowane pliki DLC (zawsze .dvpl, kopiować do packs gry)
└── Backup/
    ├── Data/    <- oryginały plików gry
    └── packs/   <- oryginały plików DLC
```

## Backup i przywracanie

- Generowanie trzyma backupy w `<gra>/BlitzMods_Backup/<mod>/{Game,DLC}/...`.
- **↩ Przywróć oryginał** kopiuje je z powrotem (DLC znowu read-only).
- Eksplorator oznacza statusem **ZMODYFIKOWANY** każdy plik z sygnaturą generatora (`HuntezPatch - Generated`), łącznie z folderami wyżej. Po przywróceniu oznaczenia gasną same.

## Przegląd interfejsu

- **Nagłówek**: tytuł, przycisk języka (`RU/EN/…`, wyskakująca lista), przycisk motywu (`☀/☾`).
- **Ścieżka do gry**: wiersz na całą szerokość ze wskaźnikiem poprawności i przyciskiem Przeglądaj po prawej.
- **Lewa kolumna** (przewijana): karty modów (klik — wł/wył, `?` — pomoc), segmenty Projekt i DVPL, blok DLC, przyciski akcji.
- **Po prawej**: duże zakładki — **Dziennik**, **Pliki gry**, **Pliki DLC**. Zakładki plików mają Odśwież / W eksploratorze i tryb **Tylko pliki modów** (hierarchia wg modów z rozmiarem i stanem Gra/DLC).
- **Pasek statusu**: wskaźnik stanu, żywy pasek postępu (`Postęp: 42% · 5/12`, w spoczynku `© Huntez`), wersja.

Wszystkie ustawienia zapisują się automatycznie i wracają przy starcie. Przy pierwszym starcie język i motyw brane są z systemu.

## Rozwiązywanie problemów

| Objaw | Rozwiązanie |
|-------|-------------|
| `Nieprawidłowa ścieżka gry (brak folderu Data)` | Wskaż folder zawierający `Data/`. |
| `Brak pliku … pomijam` w NON-DVPL | Gra trzyma tu `.dvpl` — włącz tryb **DVPL**. |
| `! NON-DVPL pomija plik DVPL` | Podpowiedź informacyjna, nie błąd — patrz wyżej. |
| `Brak backupu dla <mod>` | Najpierw przynajmniej raz wygeneruj mod. |
| Popup o randze i tak wyskakuje | Przegeneruj AutoRanksOFF (potrzebny główny wyłącznik `ranksAvailable`), najpierw zwracając oryginał. |
| Fioletowa szachownica zamiast kości | Przegeneruj RandomTankSelector, najpierw zwracając oryginał (brakuje pliku ikony). |
| Gra się zaktualizowała | Przepuść generowanie od nowa i sprawdź oznaczenia ZMODYFIKOWANY. |

## Struktura projektu

```
HuntezPatch/
├── main.py                  # punkt wejścia
├── requirements.txt
├── start_program.bat / autoinstall_modules.bat
├── config.json              # generowany: twoje ustawienia (nie w git)
├── core/                    # kodek DVPL, operacje plikowe, silniki modów (Mods/hidden_tanks, Mods/autoranks, Mods/random_tank)
├── gui/                     # interfejs (karty, eksplorator, popupy, dziennik)
├── locales/                 # stringi UI ru/en/uk/de/tr/pl
├── Documentation/           # ta instrukcja w 6 językach
└── result/                  # generowane: paczki eksportu (nie w git)
```

W trakcie pracy powstają tylko `config.json` i `result/` — reszta to źródła.
Pełna lista w [.gitignore](../.gitignore).

## Języki

Interfejs i dokumentacja: **RU · EN · UK · DE · TR · PL**. Brakujące stringi cofają się do angielskiego.

## Autor

© Huntez — błędy i pomysły mile widziane na GitHubie.
