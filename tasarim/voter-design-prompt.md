# JamDeck — Telefon Oy Verme Sayfası (Voter Page) Tasarım Brief'i (web Claude için)

> Bu metni claude.ai'ye yapıştır. Daha önce tasarladığın **JamDeck masaüstü arayüzünün** (Frostbite teması,
> CSS-değişkenli tasarım dili) devamı niteliğinde, **telefon oy verme sayfası** istiyoruz. Çıktı yine
> **tek dosyalık, çalışan `index.html`** (HTML + `<style>` içinde tüm CSS + sadece demo için minik vanilla JS).
> Geliştirici bunu mevcut sunucu şablonuna entegre edecek; **yapı, sınıf isimleri ve tema değişkenleri** kritik.

---

## ROLÜN
Üst düzey ürün/arayüz tasarımcısısın. JamDeck (game-jam yönetim uygulaması) için **oy verenlerin telefonundan
açtığı** sayfayı tasarlayacaksın. Harici kütüphane, font CDN'i, framework **YOK** — saf HTML/CSS (+ durumlar
arası geçişi göstermek için çok az vanilla JS). Sayfa LAN üzerinden telefon tarayıcısında açılır.

## BAĞLAM: Bu sayfa nedir?
Jam sırasında organizatör oylama sunucusunu açar; **Jüri / Seyirci / Ekip** üyeleri telefonlarından kendilerine
verilen linki açıp her oyuna **kategori başına 1–10 puan** verir. Sayfa 2 saniyede bir sunucudan güncel durumu
çeker: organizatör sahnede yeni oyun başlattığında sayfada otomatik belirir.

**ÇOK ÖNEMLİ — KOMPAKTLIK:** Bu sayfa hem **telefonda (360–430px)** hem **PC tarayıcısında** güzel ve **kompakt**
görünmeli. Telefonda bir kategori bloğu + gönder butonu kaydırmadan görünebilmeli; 3-4 kategori varsa
makul bir kaydırmayla bitmeli. Dev başlıklar, israf edilmiş dikey boşluk YOK. PC'de içerik ortalanmış dar bir
sütunda kalmalı (örn `max-width:480px`), kenarlar boş ama dengeli dursun.

## KRİTİK TEKNİK KISITLAR
- **Tek dosya `index.html`**, tüm stiller `<style>` içinde. Harici kaynak yok, çevrimdışı çalışır.
- **Tema tamamen CSS değişkenleriyle** — masaüstü uygulamayla AYNI palet. Sabit hex yazma; her renk `var(--…)`:
  ```
  --bg --bg-2 --surface --surface-2 --border
  --accent --accent-2 --accent-ink --text --text-muted
  --success --warning --error
  --radius --radius-sm --glow-a --glow
  --font-display --font-body --font-mono
  ```
  `:root`'a Frostbite koyu temasını koy (entegrasyonda bu blok, organizatörün seçtiği tema renkleriyle
  sunucu tarafından değiştirilecek — o yüzden TÜM bileşenler değişken kullanmalı, açık temalarda da okunaklı olmalı):
  `--bg:#050a14; --bg-2:#080e1c; --surface:#0f1629; --surface-2:#141d33; --border:#1e293b;
   --accent:#00f2ff; --accent-2:#0062ff; --accent-ink:#03121c; --text:#ffffff; --text-muted:#94a3b8;
   --success:#00e676; --warning:#ffab00; --error:#ff1744; --radius:18px; --radius-sm:10px; --glow-a:30%;`
- Metinler Türkçe örnek olabilir; gerçek metinler sunucudan gelir (başlıkta grup adı: "Jüri Oylaması" gibi).
- Dokunma hedefleri ≥ 40px; `user-scalable=no` viewport; performans hafif (eski telefonlar).
- Masaüstü uygulamadaki bileşen diliyle tutarlı: aynı kart/çip/buton hissi (yarı saydam yüzey + blur,
  `--radius`, accent dolgulu primary buton + `--accent-ink` metin, `--glow` parıltı).

## SAYFANIN DURUMLARI (hepsini tasarla; demo JS ile aralarında geçilebilsin)
Sayfa tek "akış" değil, sunucu durumuna göre şu hallerden birindedir. Her halin markup'ı sayfada bulunmalı
(gizli/görünür yönetilir). Demo için sayfanın köşesine küçük bir durum-seçici koyabilirsin (entegrasyonda silinir).

### A) KAPI EKRANI (erişim korumalı gruplar)
Jüri/Ekip girişi PIN veya tek-kullanımlık kodla korunabilir. Ortalanmış tek kart:
- Kilit ikonu + başlık: "PIN gerekli" veya "Erişim kodu gerekli" + 1 satır açıklama.
- Büyük, ortalı, harf-aralıklı **kod/PIN inputu** (mono font, uppercase; PIN'de numerik) + **"Onayla"** butonu.
- Hata satırı (`--error`): "Kod geçersiz." / "Bu kod başka bir cihazda kullanılmış." / "PIN yanlış." vb.
- İki varyantı da göster (PIN ve KOD — demo seçiciyle).

### B) AKTİF OYLAMA (ana durum)
- **Üst başlık:** kompakt; grup adı ("Jüri Oylaması") + küçük jam kimliği. Dev h1 yok.
- **Gezinme çubuğu:** "← Önceki oyun" / "Sıradaki oyun →" butonları (yalnızca ilgili yön varsa görünür).
  Sıradaki butonu yeni oyun geldiğinde dikkat çekmeli (hafif `--warning` nabız animasyonu var — koru).
- **Oyun kartı:** oyun adı (display font) + grup etiketi (soluk). Oyun şu an sahnede sunuluyorsa
  **"🔴 Şu an sunulan oyun"** canlı rozeti (nabız animasyonlu, `--error` tonu).
- **Puanlama:** kategori başına bir blok: kategori adı + **1–10 butonları 5×2 ızgara** (yuvarlak, eşit,
  dokunması rahat; seçili olan accent dolgu + `--accent-ink` rakam). 2-4 kategori örneği koy. Bloklar
  arası boşluk SIKI olsun.
- **Gönder butonu:** geniş "Oyu Gönder" (primary). Tüm kategoriler seçilmeden disabled. Gönderildikten sonra
  **"✓ Oy Verildi"** durumuna döner (`--success` dolgu, disabled ama canlı görünüm).
- Altta küçük durum satırı (✓ Oyunuz kaydedildi / ✗ Bağlantı hatası) + en altta minik mono **debug satırı**
  (soluk, ör. "durum: grup=jury · gösterilen=Derin Uyku · oyun=3") — koru ama göze batmasın.

### C) BEKLEME — aktif oyun yok
Oyun kartının yerinde sakin boş-durum: ikon + "Henüz aktif oyun yok — düzenleyici bir oyun başlattığında
burada görünecek." Puanlama gizli.

### D) KAPALI / DOLU
- Grup kapalı: ortalanmış mesaj kartı "Bu oy grubu kapalı." (`--error` tonlu ama agresif değil).
- Kontenjan dolu: "Bu grup için kontenjan dolu. Düzenleyiciye danışın."

### E) TOAST
Üstten kayan bildirim (mevcut davranış korunacak): normal (accent) + uyarı (`--warning`) varyantı.
Örnek metinler: "✓ Oyunuz kaydedildi · Yeni oyun: Cosmic Drift", "🎮 Sıradaki oyun başladı! Bu oyunu
bitirip 'Sıradaki oyun →' butonuna bas."
Ayrıca oyun kartının yeni oyuna geçişte kısa parlaması (flash animasyonu) için bir keyframe öner.

## KORUNACAK İSİM/YAPILAR (geliştirici mevcut JS'i bunlara bağlayacak)
Mevcut mantık şu element ID'lerini kullanıyor; bunları AYNEN kullan:
`#toast #nav #prevBtn #nextBtn #gameContainer #gate #gateTitle #gateSub #gateInput #gateBtn #gateErr
#disabledMsg #ratingArea #cats #submitBtn #status #dbg`
Sınıflar: `.game-card .live-badge .cat-block .cat-label .rating .submit-btn(.voted) .gate-* .nav-btn(.highlight)
.toast(.show .warn) .waiting .disabled-msg` — yeni sınıf ekleyebilirsin ama bu çekirdek isimler kalsın.
Kategori blokları ve puan butonları JS ile dinamik üretiliyor: `.rating` içinde 10 adet `<button>` (5×2 grid
CSS ile), seçili durumu `button.selected`.

## ÇIKTI FORMATI
- **Tek `index.html`**: `<head>`'de `<style>`, `<body>`'de yukarıdaki tüm durum markup'ları + en fazla küçük
  bir demo JS (durum seçici + puan butonu seçimi + toast gösterimi). Başka mantık ekleme.
- Kısa bir **tasarım notu** ekle (spacing/tipografi kararları, masaüstü tasarımla tutarlılık noktaları).

## YAPMA
Harici kaynak yok. Değişken dışı sabit renk yok. Dev dikey boşluk yok. Aşırı animasyon yok (eski telefon
performansı). Erişilebilir kontrast (açık temalarda da) koru.

Teşekkürler — masaüstüyle aynı ailenin üyesi gibi hissettiren, **kompakt ve hızlı** bir oy sayfası bekliyorum.
