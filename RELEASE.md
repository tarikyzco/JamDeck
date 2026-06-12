# JamDeck — Sürüm Yayınlama Rehberi

Uygulamanın içinde güncelleme sistemi var ve depo **uygulamaya gömülü**:
`backend/version.py` → `UPDATE_REPO = "tarikyzco/JamDeck"`. Uygulama açılışta ve
"Güncellemeleri Denetle" butonuyla bu deponun son Release'ini kontrol eder,
zip'i indirir, tek tıkla kendini günceller (ayarlar/oylar/kodlar korunur).

> Depo **public** olmalı (uygulama token'sız denetler). Depo taşınırsa
> `UPDATE_REPO` güncellenip yeni sürüm çıkarılır.

## Her yeni sürümde

1. `backend\version.py` → `APP_VERSION = "2.1.0"` (tek kaynak; arayüz buradan okur).
2. ```powershell
   .\build_release.ps1
   ```
   → `release\JamDeck-v2.1.0-win64.zip` üretir.
3. ```powershell
   gh release create v2.1.0 release\JamDeck-v2.1.0-win64.zip --title "v2.1.0" --notes "Yenilikler: ..."
   ```
   `--notes` metni uygulamadaki güncelleme kartında "Sürüm notları" olarak görünür.

Hepsi bu. Eski sürümü çalıştıran herkes açılışta "Yeni sürüm var" bildirimi
alır; Kurulum'dan **İndir & Kur → Kur ve Yeniden Başlat** der, uygulama kapanır,
yeni sürüm kurulur ve kendiliğinden açılır.

## Nasıl çalışıyor (özet)

- Denetim: `api.github.com/repos/{repo}/releases/latest` (anonim, saatte 60
  istek limiti — açılışta tek istek).
- İndirme: zip `%TEMP%\jamdeck_update.zip`'e iner (ilerleme çubuğu).
- Kurulum: zip Python'da açılır → kullanıcı durumu (`jam_settings.json,
  votes.json, access.json, game_overrides.json`) yedeklenir → `%TEMP%`'e
  yazılan bir .bat uygulama kapanınca `robocopy` ile yeni sürümü üstüne
  kopyalar, JSON'ları geri yükler, uygulamayı başlatır, kendini siler.
  Günlük: `%TEMP%\jamdeck_update.log`.
- Çevrimdışı: Kurulum → **Zip'ten Güncelle** ile elden verilen release zip'i
  aynı mekanizmayla kurulur.

## Notlar / bilinen durumlar

- **SmartScreen:** exe imzasız olduğu için ilk çalıştırmada Windows uyarı
  verebilir → "Daha fazla bilgi → Yine de çalıştır".
- `robocopy /E` üstüne kopyalar, silmez: çok eski sürümden kalan artık dosyalar
  klasörde kalabilir (zararsız). Temiz kurulum isterseniz klasörü silip zip'i
  elle açın.
- Zip yapısı: kökte `Ayazjam Manager\` klasörü (build_release.ps1 böyle üretir).
  Güncelleyici, exe'yi kökte ya da tek alt klasörde de bulabilir (toleranslı).
