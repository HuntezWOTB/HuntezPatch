# HuntezPatch — Belgeler (Türkçe)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**HuntezPatch v1.00**, **World of Tanks Blitz** (Wargaming) ve **Tanks Blitz** (Lesta Games) için mod üreticisidir.
İki mod kurar: **HiddenTanks** (araştırma ağacındaki gizli tankları gösterir) ve **AutoRanksOFF**
(hangar arayüzündeki rütbe kilitlerini kaldırır).

> **Diğer dillerde belgeler:**
> [🇬🇧 English](README.en.md) · [🇷🇺 Русский](README.ru.md) · [🇺🇦 Українська](README.uk.md) ·
> [🇩🇪 Deutsch](README.de.md) · [🇵🇱 Polski](README.pl.md)

---

## İçindekiler

- [Modlar](#modlar)
- [Özellikler](#özellikler)
- [Gereksinimler](#gereksinimler)
- [Kurulum](#kurulum)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [İşlem Kipleri](#i̇şlem-kipleri)
- [DVPL Kipleri](#dvpl-kipleri)
- [DLC (Mikro Güncellemeler)](#dlc-mikro-güncellemeler)
- [Dışa Aktarma Yapısı](#dışa-aktarma-yapısı)
- [Yedek ve Geri Yükleme](#yedek-ve-geri-yükleme)
- [Arayüz](#arayüz)
- [Sorun Giderme](#sorun-giderme)
- [Proje Yapısı](#proje-yapısı)
- [Diller](#diller)
- [Yazar](#yazar)

---

## Modlar

| Mod | Ne yapar | Dosyalar (`Data/` göreli) |
|-----|----------|------------------------------|
| **HiddenTanks** | Araştırma ağacındaki TÜM gizli tankları gösterir (premium, koleksiyonluk, test, kaldırılmış). Satın alma yine geliştirici tekliflerine bağlıdır — mod yalnızca gösterir. Seviye içi sıralama: **sıradan → koleksiyonluk → premium**, grup içinde sınıfa göre (**HT → MT → AT → TD**). | `Configs/TechTree/*_tree.yaml` (9 ulus), `XML/item_defs/vehicles/*/list.xml` (9 ulus) |
| **AutoRanksOFF** | Rütbe kilitlerini kaldırır: Savaş düğmesi hep görünür, rütbe ipuçları gizlenir, rütbe olayları silinir, “tankın rütbe kazandı” kutlaması hiç çıkmaz. | `UI/Screens3/Lobby/Hangar/Hangar.yaml`, `UI/Screens3/Lobby/Hangar/Squad/SquadView.yaml`, `UI/Screens3/Lobby/Inventory/Inventory.yaml`, `UI/Screens3/Lobby/Inventory/TankProgress/AchievementsTab.yaml` |

Aynı bilgi uygulamada mod kartındaki **?** düğmesindedir.

## Özellikler

- Tek araçta iki mod, bağımsız seçilir (kart onay kutuları).
- **Üret** (aşamalı: temp → yedek → değiştir) ve **Dışa aktar** (paylaşıma hazır `Mod` + `Backup` paketi) işlemleri.
- **DVPL / NON-DVPL** dosya kipleri; DLC dosyaları her zaman DVPL.
- Otomatik uyarılı **DLC (mikro güncelleme) desteği**, `packs` klasörünü tek tıkla açma.
- Yerleşik **dosya gezgini** (`Oyun dosyaları` / `DLC dosyaları` sekmeleri): tembel ağaç, mod dosyası vurgulama, `DEĞİŞTİRİLDİ` durum sütunu, yalnızca-mod listesi.
- Kopyalaması kolay günlük (`Ctrl+C` / `Ctrl+A`, sağ tık menüsü, iki klavye düzeni).
- Dosya sayaçlı ilerleme çubuğu, arka plan işlemleri (arayüz donmaz).
- 6 arayüz dili, açık/koyu tema, taşınabilir ayarlar.

## Gereksinimler

- **Windows** ve **Python 3.8+** (`python --version`).
- `requirements.txt` bağımlılıkları: `lz4`, `PyYAML` (`tkinter` gömülü).

## Kurulum

```bat
autoinstall_modules.bat
start_program.bat
```

Veya elle:

```bat
pip install -r requirements.txt
python main.py
```

Kurulum gerekmez — program taşınabilirdir. Ayarlar `main.py` yanındaki `config.json` dosyasındadır.

## Hızlı Başlangıç

1. **Oyun klasörünü** seçin (içinde `Data/` olan).
2. **Proje** (`Wargaming` / `Lesta Games`) ve **DVPL kipi** seçin (aşağıya bakın).
3. İstediğiniz modları işaretleyin.
4. **▶ Çalıştır** → **Üret (Değiştir)** (paylaşılacak paket için **Üret (Dışa aktar)**).
5. Oyunu açıp kontrol edin. Geri alma her zaman: **↩ Orijinali geri yükle**.

## İşlem Kipleri

| Kip | Davranış |
|-----|----------|
| **Üret (Değiştir)** | Dosyalar önce temp klasörde dönüştürülür (asla oyun içinde değil), orijinaller yedeklenir, sonra bitmiş dosyalar kopyalanır. DLC dosyalarına istemcinin beklediği gibi salt-okunur özniteliği verilir. |
| **Üret (Dışa aktar)** | Oyun klasörüne dokunulmaz. Paket `result/<ad>_<sürüm>/` altına yazılır: `Mod/` (yamalı dosyalar) ve `Backup/` (orijinaller). |

## DVPL Kipleri

| Kip | Davranış |
|-----|----------|
| **DVPL** | `.dvpl` kapları çözülür → düzenlenir → yeniden paketlenir. Oyun klasöründe `.dvpl` varsa bunu seçin (örn. Steam istemcisi). |
| **NON-DVPL** | Yalnızca açılmamış (düz) oyun dosyaları işlenir; `.dvpl` dosyaları günlük uyarısıyla atlanır. |

> **DLC dosyaları HER ZAMAN DVPL'dir** — mikro güncellemeler açılmış gelmez.

## DLC (Mikro Güncellemeler)

Oyun mikro güncelleme getirdiyse dosyaları temelleri ezer — onlar da yamalanmalı:

| Proje | `packs` klasörü |
|-------|-----------------|
| Wargaming | `%userprofile%/AppData/Local/wotblitz/packs` |
| Lesta Games | `%userprofile%/Documents/TanksBlitz/packs` |

- Dahil etmek için **DLC dosyalarını değiştir** seçeneğini açın.
- Modlara ait DLC dosyaları varken seçenek kapalıysa uygulama uyarır.
- **DLC klasörü** düğmesi iki seçenekli açılır (`Wargaming` / `Lesta Games`) ve doğru `packs` klasörünü Gezgin'de açar.

## Dışa Aktarma Yapısı

```
result/BlitzMods_<modlar>_<sürüm>/
├── Mod/
│   ├── Data/    <- yamalı oyun dosyaları (bulunduğu gibi düz ya da .dvpl)
│   └── packs/   <- yamalı DLC dosyaları (hep .dvpl, oyunun packs klasörüne kopyalanır)
└── Backup/
    ├── Data/    <- orijinal oyun dosyaları
    └── packs/   <- orijinal DLC dosyaları
```

## Yedek ve Geri Yükleme

- Üretim, mod başına yedekleri `<oyun>/BlitzMods_Backup/<mod>/{Game,DLC}/...` altında tutar.
- **↩ Orijinali geri yükle** bunları yerine kopyalar (DLC yine salt-okunur).
- Gezgin, üretici imzalı her dosyayı (`# AutoRankOFF`, `# HiddenTanks-Generator`) **DEĞİŞTİRİLDİ** olarak işaretler — üst klasörler dahil. Geri yüklemede işaretler kendiliğinden söner.

## Arayüz

- **Başlık**: ad, dil düğmesi (`RU/EN/…` açılır), tema düğmesi (`☀/☾`).
- **Oyun yolu**: boydan boya satır, geçerlilik noktası ve sağda Gözat düğmesi.
- **Sol sütun** (kaydırmalı): mod kartları (tıkla aç/kapat, `?` bilgi), Proje ve DVPL anahtarları, DLC bloğu, işlem düğmeleri.
- **Sağ**: büyük sekmeler — **Günlük**, **Oyun dosyaları**, **DLC dosyaları**. Dosya sekmelerinde Yenile / Gezginde aç ve **Yalnızca mod dosyaları** listesi (moda göre hiyerarşi, boyut ve Oyun/DLC durumu).
- **Durum çubuğu**: durum noktası + yazı, canlı ilerleme (`İlerleme: %42 · 5/12`, boşta `© Huntez`), sürüm.

Tüm ayarlar otomatik kaydedilir ve açılışta geri gelir. İlk açılışta dil ve tema işletim sisteminden alınır.

## Sorun Giderme

| Belirti | Çözüm |
|---------|-------|
| `Geçersiz oyun yolu (Data klasörü yok)` | İçinde `Data/` olan klasörü gösterin. |
| NON-DVPL'de `Dosya yok … atlanıyor` | Oyun burada `.dvpl` tutuyor — **DVPL** kipine geçin. |
| `! NON-DVPL, DVPL dosyasını atlıyor` | Bilgi uyarısıdır, hata değil — yukarıya bakın. |
| Geri yüklemede `{mod} için yedek yok` | Önce modu en az bir kez üretin. |
| Rütbe kutlaması yine çıkıyor | AutoRanksOFF'u yeniden üretin (`ranksAvailable` ana şalteri gerekir), önce orijinali döndürün. |
| Oyun güncellendi | Üretimi yeniden çalıştırın, DEĞİŞTİRİLDİ işaretlerini kontrol edin. |

## Proje Yapısı

```
HuntezPatch/
├── main.py                  # giriş noktası
├── requirements.txt
├── start_program.bat / autoinstall_modules.bat
├── config.json              # üretilir: ayarlarınız (git'te yok)
├── core/                    # DVPL codec, dosya işlemleri, mod motorları
├── gui/                     # arayüz (kartlar, gezgin, açılırlar, günlük)
├── locales/                 # arayüz metinleri ru/en/uk/de/tr/pl
├── Documentation/           # bu kılavuz, 6 dilde
└── result/                  # üretilir: dışa aktarma paketleri (git'te yok)
```

Çalışırken yalnızca `config.json` ve `result/` oluşur — gerisi kaynak kodudur.
Tam liste: [.gitignore](../.gitignore).

## Diller

Arayüz ve belgeler: **RU · EN · UK · DE · TR · PL**. Eksik metinler İngilizceye döner.

## Yazar

© Huntez — hata ve fikirler için GitHub'a bekleriz.
