<div align="right">

🇹🇷 **Türkçe** · [🇬🇧 English](README.en.md)

</div>

# 🎮 JamDeck

**Game jam'ler için hepsi-bir-arada masaüstü yönetim uygulaması** — oyunları
itch.io'dan indirir, sahnede sunar, LAN üzerinden oylatır, sonuçları açıklar ve
48 saatlik geri sayımı mekan ekranına yansıtır. Tamamen çevrimdışı çalışır
(yalnız indirme ve güncelleme internet ister), her jam'e göre özelleştirilir.

> ℹ️ **Not:** Uygulamanın kalıcı logosu henüz seçilmedi — şu anki simge geçici
> bir yer tutucudur.

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
| 🗳️ **LAN Oylaması** | Jüri / Seyirci / Ekip telefondan oy verir (ağırlıklı kategoriler); tek kullanımlık erişim kodları, **canlı kod panosu** (kullanılan kod herkeste anında düşer), QR ekranı |
| 🏆 **Sonuçlar** | İlk 3 podyumu, grup kırılımları, paylaşılık PNG sonuç afişi + teknik .xlsx raporu |
| ⏱️ **Sayaç** | 48 saatlik jam sayacı: 8 stil (Neon, LED, Pixel, Glitch, HP-Bar…), 3 logo alanı, başlamaya 10 dk kala **her ekrandan otomatik tam ekran**, OBS Browser-Source desteği |
| 🎨 **Tema** | 16 hazır palet + tam renk/font/efekt özelleştirme; tema telefonlardaki oy sayfasına da yansır |
| 📋 **Teslim Kılavuzu** | Katılımcılara paylaşılan kurallar ekranı + 1080×1920 poster çıktısı; metinler uygulama içinden düzenlenebilir |
| 🔄 **Otomatik Güncelleme** | Uygulama yeni sürümü kendisi bulur, indirir, kurar |

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

Adım adım interaktif rehber: **[JamDeck Guide](JamDeck-Guide.html)**
(indirip tarayıcıda açın — tüm ekranlar, SSS ve ipuçları içinde).

## ℹ️

JamDeck kapalı kaynaklı, **ücretsiz** bir uygulamadır. Sorun bildirimi ve
öneriler için [Issues](../../issues) sayfasını kullanabilirsiniz.

© 2026 tarikyzco
