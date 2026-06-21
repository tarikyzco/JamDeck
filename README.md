<div align="right">

🇹🇷 **Türkçe** · [🇬🇧 English](README.en.md)

</div>

<p align="center"><img src="JamDeck.png" width="400" alt="JamDeck — Game Jam Manager"></p>

<p align="center"><b>Game Jam Manager</b> — itch.io teslim indirme · online oylama · 48 saat sayaç · sunum · sonuç töreni</p>

# JamDeck — Game Jam Manager

**Game jam'ler için hepsi-bir-arada masaüstü yönetim uygulaması** — oyunları
itch.io'dan indirir, sahnede sunar, telefonlardan **online** oylatır (sabit link/QR,
~500 kişiye kadar stabil), sonuçları sinematik bir törenle açıklar ve 48 saatlik geri
sayımı mekan ekranına yansıtır. Her jam'e göre tamamen özelleştirilir.
**7 dilde** kullanılabilir — Türkçe · English · Français · Deutsch · Español ·
Português · 日本語.

![JamDeck arayüzü 7 dilde](docs/jamdeck-langs.gif)

## ⬇️ İndir

**[Son sürümü indirin →](../../releases/latest)**

| Dosya | Ne için |
|---|---|
| `JamDeck-Setup-vX.Y.Z.exe` | **Önerilen** — klasik kurulum: Başlat menüsü + masaüstü kısayolu, kaldırıcı. Yönetici izni istemez. |
| `JamDeck-vX.Y.Z-win64.zip` | Taşınabilir (portable): bir klasöre açın, `JamDeck.exe` çalıştırın. USB'den bile çalışır. |

- Windows SmartScreen uyarısında: **Daha fazla bilgi → Yine de çalıştır** (uygulama imzasız).
- Setup, kurulumda tek seferlik yönetici onayıyla güvenlik duvarı iznini
  ayarlar — jam günü oylama/sayaç başlatırken izin penceresi çıkmaz.
- Sonrası otomatik: uygulama açılışta yeni sürümü bildirir, **İndir & Kur**
  dersiniz, kendini günceller — ayarlarınız ve oylar korunur (iki dağıtımda da).

**Gereksinimler:** Windows 10/11 (WebView2 — Windows 11'de hazır gelir).

## ✨ Özellikler

| | |
|---|---|
| 📥 **İndir & Hazırla** | itch.io jam arşivini tek tıkla indirir, zip/rar/7z/tar ve iç içe arşivleri açar, oyun adı + kapağı otomatik alır, bozuk teslimleri işaretler |
| 🎬 **Sunum** | Tam ekran sahne: oyun listesi + dev kapak + tek tık başlatma; süre dolunca otomatik kapatma, web (HTML5/WebGL) oyunlar dahil |
| 🗳️ **Online Oylama** | Jüri / Seyirci / Ekip telefondan **online** oy verir (sabit link/QR, ~500 kişiye kadar stabil, aynı Wi-Fi gerekmez); ağırlıklı kategoriler, tek kullanımlık erişim kodları, **canlı kod panosu** (kullanılan kod herkeste anında düşer), QR ekranı |
| 🏆 **Sonuçlar** | İlk 3 podyumu, grup kırılımları, paylaşılık PNG sonuç afişi + teknik .xlsx raporu |
| ⏱️ **Sayaç** | 48 saatlik jam sayacı: 8 stil (Neon, LED, Pixel, Glitch, HP-Bar…), 3 logo alanı, başlamaya 10 dk kala **her ekrandan otomatik tam ekran**, OBS Browser-Source desteği |
| 🎨 **Tema** | 16 hazır palet + tam renk/font/efekt özelleştirme; tema telefonlardaki oy sayfasına da yansır |
| 📋 **Teslim Kılavuzu** | Katılımcılara paylaşılan kurallar ekranı + 1080×1920 poster çıktısı; metinler uygulama içinden düzenlenebilir |
| 🔄 **Otomatik Güncelleme** | Uygulama yeni sürümü kendisi bulur, indirir, kurar |
| 🌍 **7 Dil** | Arayüzün tamamı Türkçe, English, Français, Deutsch, Español, Português ve 日本語 — telefon oy sayfası, kod panosu ve OBS sayaç dahil; varsayılan oy kategorileri de çevrilir, açılır menüden anında değişir |

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

## 📖 Kullanım Rehberi

### ➡️ **[JamDeck Guide'ı aç (tek tık)](https://tarikyzco.github.io/JamDeck/JamDeck-Guide.html)**

Adım adım interaktif rehber — tüm ekranlar, SSS ve ipuçları içinde. Tarayıcıda doğrudan açılır;
indirip çevrimdışı da kullanabilirsiniz.

## ❓ Sık Sorulanlar

**JamDeck nedir?**
Game jam'lerin tüm operasyonel tarafını yürüten ücretsiz Windows uygulaması (bir
"game jam manager"): itch.io'dan teslimleri indirir, sahnede sunar, telefonlardan
online oy toplar, sonuçları törenle açıklar ve OBS/mekan ekranına 48 saatlik geri
sayım koyar.

**Kimler için?**
Game jam ve hackathon düzenleyenler, üniversite oyun toplulukları, etkinlik
sunucuları — sayaç, oylama ve sunumu ayrı ayrı kurmak yerine tek araç isteyenler.

**İnternet gerekir mi?**
Sunum ve sayaç çevrimdışı çalışır. Oylama internet üzerinden sabit bir public
link/QR ile yürür; teslim indirme ve güncellemeler de internet ister.

**Oylama nasıl çalışır? Hesap gerekir mi?**
Seyirci sadece QR okutup telefonundan oy verir, hiçbir şey kurmaz. Organizatör ilk
kullanımda bir kez ücretsiz Tailscale girişi yapar ki uygulama sabit oylama
bağlantısını yayınlasın. Ağırlıklı kategoriler, tek kullanımlık kodlar, canlı kod
panosu; ~500 kişiye kadar stabil.

**Ücretsiz mi? Açık kaynak mı?**
Tamamen ücretsiz ve **açık kaynaklı** — [GPL-3.0](LICENSE) lisansıyla.

**Hangi platformlar?**
Windows 10/11 (WebView2). Telefon oy sayfaları tarayıcısı olan her cihazda çalışır.

## 🔎 Anahtar Kelimeler

Game jam manager · game jam yazılımı · game jam oylama uygulaması · jam sayaç ·
48 saat geri sayım sayacı · jam sunum aracı · itch.io teslim indirici · telefondan
online oylama · QR kod oylama · hackathon yönetim yazılımı · OBS geri sayım browser
source · game jam sonuç/puanlama · Windows game jam düzenleyici aracı.

## ℹ️

JamDeck **ücretsiz** ve **açık kaynaklı** ([GPL-3.0](LICENSE)) bir game jam
yönetim uygulamasıdır. Sorun bildirimi ve öneriler için [Issues](../../issues)
sayfasını kullanabilirsiniz.

© 2026 tarikyzco
