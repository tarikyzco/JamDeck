# 🎮 JamDeck

**Game jam'ler için hepsi-bir-arada masaüstü yönetim uygulaması** — oyunları
itch.io'dan indirir, sahnede sunar, LAN üzerinden oylatır, sonuçları açıklar ve
48 saatlik geri sayımı mekan ekranına yansıtır. Tamamen çevrimdışı çalışır
(yalnız indirme ve güncelleme internet ister), her jam'e göre özelleştirilir.

> All-in-one desktop toolkit for running game jams: download builds from
> itch.io, present on stage, run weighted LAN voting from phones, reveal
> results, and put a themed 48-hour countdown on the venue screen. Turkish/English UI.

---

## ✨ Özellikler

| | |
|---|---|
| 📥 **İndir & Hazırla** | itch.io jam arşivini tek tıkla indirir (itch-dl), zip/rar/7z/tar ve iç içe arşivleri açar, oyun adı + kapağı otomatik alır, bozuk teslimleri işaretler |
| 🎬 **Sunum** | Tam ekran sahne: oyun listesi + dev kapak + tek tık başlatma; süre dolunca otomatik kapatma, web (HTML5/WebGL) oyunlar dahil |
| 🗳️ **LAN Oylaması** | Jüri / Seyirci / Ekip telefondan oy verir (ağırlıklı kategoriler); tek kullanımlık erişim kodları, **canlı kod panosu** (kullanılan kod herkeste anında düşer), QR ekranı |
| 🏆 **Sonuçlar** | İlk 3 podyumu, grup kırılımları, paylaşılık PNG sonuç afişi + teknik .xlsx raporu |
| ⏱️ **Sayaç** | 48 saatlik jam sayacı: 8 stil (Neon, LED, Pixel, Glitch, HP-Bar…), 3 logo alanı, başlamaya 10 dk kala **her ekrandan otomatik tam ekran**, OBS Browser-Source desteği |
| 🎨 **Tema** | 16 hazır palet + tam renk/font/efekt özelleştirme; tema telefonlardaki oy sayfasına da yansır |
| 📋 **Teslim Kılavuzu** | Katılımcılara paylaşılan kurallar ekranı + 1080×1920 poster çıktısı; metinler uygulama içinden düzenlenebilir |
| 🔄 **Otomatik Güncelleme** | Uygulama yeni sürümü GitHub Releases'tan kendisi bulur, indirir, kurar — ayarlar ve oylar korunur |

## 📸 Ekran Görüntüleri

| Sunum sahnesi | Kurulum & temalar |
|---|---|
| ![Sunum](docs/sunum.png) | ![Temalar](docs/kurulum-temalar.png) |

| Oylama yönetimi | Telefonda oy verme | Canlı kod panosu |
|---|---|---|
| ![Oylama](docs/oylama.png) | ![Telefon](docs/telefon-oylama.png) | ![Kod panosu](docs/kod-panosu.png) |

| Sayaç (Pixel stili) | Sayaç kurulumu | Sonuçlar |
|---|---|---|
| ![Sayaç](docs/sayac-pixel.png) | ![Sayaç kurulum](docs/sayac-kurulum.png) | ![Sonuçlar](docs/sonuclar.png) |

## 🚀 Kurulum

1. [Releases](../../releases/latest) sayfasından son `JamDeck-vX.Y.Z-win64.zip` dosyasını indirin.
2. Zip'i bir klasöre açın → `Ayazjam Manager.exe` çalıştırın.
   - Windows SmartScreen uyarısında: **Daha fazla bilgi → Yine de çalıştır** (uygulama imzasız).
3. Sonraki sürümler için hiçbir şey yapmanıza gerek yok: uygulama açılışta
   yeni sürümü bildirir, **İndir & Kur** dersiniz, kendini günceller.

**Gereksinimler:** Windows 10/11 (WebView2 — Windows 11'de hazır gelir).

## 🛠️ Kaynaktan Çalıştırma

```powershell
pip install -r requirements.txt
python main.py
```

Frontend tek dosyadır: `frontend/index.html` (vanilla JS, derleme yok).
Backend: `backend/` (pywebview + stdlib HTTP sunucuları). Testler:
`tests/*.mjs` (Playwright) ve `tests/*.py`.

Sürüm çıkarma akışı için: [`RELEASE.md`](RELEASE.md)

## 🧩 Mimari (özet)

```
main.py                 → pywebview penceresi
frontend/index.html     → tüm arayüz (tek dosya)
backend/api.py          → JS köprüsü: indirme, organize, sunum, ayarlar
backend/voting_server.py→ LAN oylama sunucusu (+ /k/ kod panosu)
backend/voter_page.py   → telefon oy sayfası + kod panosu şablonları
backend/countdown_page.py→ tarayıcı/OBS sayaç sayfası
backend/updater.py      → kendi kendini güncelleme (GitHub Releases)
```

## 📄 Lisans

MIT — dilediğiniz jam'de kullanın, uyarlayın, paylaşın. 🎉
