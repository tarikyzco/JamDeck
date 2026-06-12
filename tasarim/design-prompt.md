# JamDeck — Komple Arayüz Tasarım Brief'i (web Claude için)

> Bu metni claude.ai'ye yapıştır. Claude'dan **tek dosyalık, çalışan bir `index.html`** (HTML iskelet +
> gömülü CSS, gerekiyorsa minik vanilla JS sadece görsel demo için) istiyoruz. Üretilen tasarımı geliştirici
> mevcut uygulamanın mantığına entegre edecek; bu yüzden **yapı, sınıf/ID isimleri ve tema değişkenleri**
> çok önemli.

---

## ROLÜN
Sen üst düzey bir ürün/arayüz tasarımcısısın. Aşağıdaki masaüstü uygulaması için **modern, şık, "premium"
ama performanslı** bir arayüz tasarlayacaksın. Çıktı: **tek `index.html`** (HTML + `<style>` içinde tüm CSS).
Harici kütüphane, font CDN'i, framework, build adımı **YOK**. Saf HTML/CSS (+ gerekiyorsa çok az vanilla JS
sadece sekme geçişi/demo için). Çevrimdışı çalışmalı (pywebview masaüstü uygulaması).

## ÜRÜN: JamDeck nedir?
Game-jam (oyun yapma yarışması) **düzenleyen kişi** için masaüstü "yönetim merkezi". Akış:
1. **İndir+Hazırla:** itch.io jam linkinden tüm oyunları indirir, otomatik açar/düzenler (zip/rar/7z).
2. **Sunum/Oyna:** jüri önünde oyunları tek tek tam ekran başlatır (her birine süreli "sunum").
3. **Oylama:** Jüri/Seyirci/Ekip telefonlarından LAN üzerinden ağırlıklı oy verir.
4. **Sonuçlar:** kazananları şık, sahneye yansıtılabilir bir görselle açıklar.
5. **Kılavuz:** jam'e katılanlara teslim kurallarını anlatan paylaşılabilir bir sayfa.
6. **Kurulum:** tema/renk/efekt/logo ayarları.

Hedef his: oyun-jam'e yakışan, enerjik ama profesyonel; sahnede projeksiyonda iyi durmalı; bol "neon/glow"
yerine **dengeli, okunaklı, ferah ama kompakt** (boşluğu israf etme).

## MUTLAKA KORUNACAK GÜÇLÜ YANLAR (mevcut uygulamadan)
Bu özellikler uygulamanın **en sevilen** yanları; yeniden tasarım bunları **korumalı ve daha da iyi
sunmalı**, asla tek-temalı/katı bir tasarıma indirgememeli:
- **Tema çeşitliliği:** 8 hazır tema preseti — hem koyu hem **açık** temalar: `Frostbite, Ember, Synthwave,
  Forest, Royal, Mono, Daylight, Paper`. Tasarım hepsinde güzel durmalı (yani açık temada da kontrast/okunaklılık
  korunmalı). Kurulumda bunlar bir **kart galerisi** olarak, her kart kendi renk önizlemesiyle gösterilmeli.
- **Tam özelleştirilebilirlik:** organizatör accent/accent2/bg vb. renkleri **kendi seçebilir** (custom tema),
  köşe yuvarlaklığı (`--radius`) ve parıltı (`--glow`) ayarlanabilir. Bu yüzden her şey CSS değişkeni olmalı.
- **14 arka plan efekti** (canlı canvas): `snow, rain, starfield, plexus, orbs, matrix, aurora, confetti,
  fireflies, gradient, lowpoly, bubbles, waves` (+ `none`). Kurulumda her efekt için küçük **önizleme kartı**
  + yoğunluk slider'ı + aç/kapat. (Efektin kendisini sen kodlamayacaksın; sadece seçim galerisini + önizleme
  kutularını tasarla — arka plan katmanı uygulamada `<canvas>` ile çiziliyor.)
- **Canlı tema değişimi:** organizatör tema/renk değiştirince tüm arayüz anında güncellenmeli (CSS değişkenleri).
- **Çift dil (TR/EN)** anında geçiş.
Kısacası: görseli baştan, daha şık yap — ama **çeşitlilik + özelleştirme + efektler** olduğu gibi yaşamalı.

## KRİTİK TEKNİK KISITLAR
- **Tek dosya `index.html`**, tüm stiller `<style>` içinde. Harici kaynak yok.
- **Tema tamamen CSS değişkenleriyle.** ASLA sabit renk (hex) yazma; her renk `var(--…)` olacak. Uygulama
  çalışırken organizatör temayı değiştirince tüm arayüz anında değişmeli. Değişken paleti (`:root`):
  ```
  --bg  --bg-2  --surface  --surface-2  --border
  --accent  --accent-2  --text  --text-muted
  --success  --warning  --error
  --radius (örn 18px)  --radius-sm  --glow (gölge/parıltı)
  --font-display (başlıklar)  --font-mono (sayı/konsol)
  ```
  `:root`'a örnek bir **koyu** tema ("Frostbite") koy ama tüm bileşenler değişkenleri kullansın:
  `--bg:#050a14; --bg-2:#080e1c; --surface:#0f1629; --surface-2:#141d33; --border:#1e293b;
   --accent:#00f2ff; --accent-2:#0062ff; --text:#ffffff; --text-muted:#94a3b8;
   --success:#00e676; --warning:#ffab00; --error:#ff1744;`
  Ayrıca alternatif bir tema göstermek için ikinci bir `:root.theme-ember` örneği ekleyebilirsin (turuncu).
- **Çift dil (TR/EN):** metinler örnek olarak Türkçe yazılabilir; ama gerçek metinler JS'ten gelecek. Metin
  taşan yerlerde kırpma/elips düşün.
- **Ölçek:** 1366×768'den 1920×1080'e iyi çalışsın. Sol sabit **sidebar (~240px)** + sağda içerik.
- **Animasyon:** ince, hızlı (150–300ms), abartısız. Performans önemli (arka planda canvas efekti döner).

## GENEL DÜZEN
- Solda **sidebar**: üstte marka (logo + jam adı), ortada navigasyon, altta dil + ayar düğmesi + sürüm.
  - **Varsayılan logo (özel logo yokken):** kalın, iki satır, alt alta **"GAME JAM" / "LOGO"** yazsın
    (placeholder hissi). Özel logo yüklenirse onun yerini alır.
  - **Nav öğeleri (bu sıra):** `Ana` (indir+hazırla) · `Sunum` · `Oylama` · `Sonuçlar` · `Kılavuz` · (alt) `Kurulum`.
- Arka planda hafif hareketli bir efekt katmanı olduğunu varsay (kar/parçacık) — içerik kartları onun
  üstünde okunaklı durmalı (hafif blur/şeffaf yüzeyler güzel durur).
- Her ekran üstte küçük bir başlık + alt açıklama ("page-head") ile başlasın.

## EKRANLAR (her birini ayrı bir `<section class="screen">` olarak tasarla; biri aktif görünsün)

### 1) ANA — İndir + Hazırla (TEK, OTOMATİK akış)
Amaç: organizatör jam linkini + API anahtarını girer, "Başlat" der; indirme biter bitmez **otomatik** açma/
düzenleme başlar. İki adım **tek ekranda canlı** akar.
- Üstte: hedef klasör bilgisi.
- Bir kart: **Jam URL** input (boş, placeholder `https://itch.io/jam/...`), **itch.io API anahtarı** input
  (boş, password + göz ikonu). Altında **"İndir ve Hazırla"** ana butonu + ikincil **"Bütünlük Kontrolü"**.
  (Not: alanlar boş başlar; kullanıcı değeri girince hatırlanır — sadece boş halini tasarla.)
- Bir **durum/ilerleme** paneli: büyük sayaç `indirilen / toplam`, hız, ilerleme çubuğu, "şu an: <oyun>".
- İlerleme çubuğunun altında **aşama rozetleri**: `İndiriliyor → Açılıyor → Düzenleniyor → Hazır` (aktif aşama
  vurgulu). Bitince özet çipleri: `N açıldı`, `N düzeltildi`, `N sorunlu`.
- Altta geniş bir **konsol** (mono font, satır satır log; renk: info/success/warning/error → `--text-muted/--success/--warning/--error`).

### 2) SUNUM (oyunları sahnede başlatma)
- Solda aranabilir **oyun listesi** (her satır: küçük kapak + takım adı (üst, küçük) + oyun adı). Seçili satır vurgulu.
- Sağda büyük **"hero" kart**: 
  - **Kapak** kutusu **4:3**, görsel **kırpılmadan** (`contain`) ortada, arkada görselin **bulanık** hali dolgu.
  - Oyun adı (büyük, display font), takım adı (üstte, uppercase, soluk).
  - Çipler: motor (Unity/Godot/…) veya **🌐 Web Oyunu**; gerekiyorsa "Bozuk/Eksik".
  - Aksiyonlar: büyük **"Sunumu Başlat"** (play ikonu), gerekiyorsa **"EXE Değiştir (1/3)"**, küçük **"✏️ Düzenle"** (ad/takım düzelt).
  - Süre (dakika) girişi bir köşede.
- Oyun yoksa boş-durum (ikon + "Henüz oyun yok").

### 3) OYLAMA — **KOMPAKT** olmalı (şu an çok boşluk var)
Üç-dört kartı **sıkı** yerleştir; gereksiz dikey boşluğu azalt. İçerik:
- **Kategoriler** kartı: satır satır kategori (aç/kapat onay kutusu + ad inputu + ağırlık slider'ı + "×0.80" katsayı + sil). Altta "+ Kategori ekle".
- **Gruplar & Erişim** kartı: Jüri/Seyirci/Ekip — her biri: aç/kapat, ağırlık slider'ı (×katsayı), erişim modu (Açık/PIN/Kodlar) ve moda göre ek alan (PIN/limit/kod adedi + "Kodları Göster").
- **Sunucu** kartı: port + **Başlat/Durdur** + durum rozeti; altında telefon **oy linkleri** (kopyalanır) + IP seçici.
- **Katılım** kutusu (skor GİZLİ): büyük "Toplam N oy" + grup başına oy çipleri + "Sonuçlar gizli — bitince Sonuçlandır" ipucu.
- En altta: **"🏁 Sonuçları Sonuçlandır"** butonu + **"Oylamayı Sıfırla"** (tehlikeli, kırmızı).
- Tasarımı 2 sütun grid yapabilirsin ama **dengeli ve kompakt**; sağ sütun kısa kalıp boşluk yaratmasın.

### 4) SONUÇLAR (YENİ, sahneye yansıtmalık)
- Üstte **varyant seçici** sekme/segment: **İlk 3** · **İlk 5** · **Tümü** (genelde ilk 3 ödül alır).
- Ortada büyük, **temalı liderlik görseli**: sıralı oyunlar; her oyun için ad + genel puan rozeti (örn 8.4/10)
  ve **grup başına ortalama çubukları** (Jüri 9.0 / Seyirci 8.0 / Ekip 8.5 — her grup kendi renginde, farklar
  görünür). 1.'ye podyum/kupa vurgusu. Jam logosu + adı başlıkta. (Bu görsel PNG olarak da kaydedilecek; bu
  yüzden net, yüksek-kontrast, projeksiyon-dostu olsun.)
- Aksiyonlar: **"🖼️ Görseli Kaydet (PNG)"** + **"📊 Teknik Dosya (.xlsx)"**.
- İlk 3 varyantı için özel, daha gösterişli bir "podyum" düzeni tasarla (1-2-3 basamak); ilk 5 / tümü için
  sıralı liste/çubuk düzeni.

### 5) KILAVUZ (YENİ — çok öz, öğretici, paylaşılabilir)
Hedef: jam'e katılan geliştiriciye teslim kurallarını **çok net** anlatan tek sayfa. Ana mesaj büyük ve net:
**"Oyununuzun hem WINDOWS (.exe) hem WEB (HTML5) build'ini yükleyin."** Yanında 2-3 minik destek maddesi
(itch.io'da oyun adı + kapak görseli girin; tek temiz arşiv; motor dosyalarını silmeyin). Sade ikonografik
kartlar. Sağda/altta: bunun **paylaşılabilir poster** (1080×1920 dikey) önizlemesi + "Görsel olarak indir".
Eski karmaşık "name.txt / zip ağacı" anlatımını **kullanma** — sade tut.

### 6) KURULUM  (çeşitlilik + özelleştirme vitrini — bu ekran güçlü olmalı)
- **Tema presetleri** (kart grid, 8 adet): `Frostbite, Ember, Synthwave, Forest, Royal, Mono, Daylight, Paper`
  — her kart o temanın renklerini (accent/bg/surface) küçük örnekle göstersin; seçili olan vurgulu. Koyu+açık
  temalar var; galeri ikisini de güzel sunmalı.
- **Renkler:** accent/accent-2/bg/surface vb. için renk seçiciler (custom tema) + `--radius` ve `--glow` slider'ları.
- **Arka plan efekti:** 14 efekt (`snow, rain, starfield, plexus, orbs, matrix, aurora, confetti, fireflies,
  gradient, lowpoly, bubbles, waves`) + `none` — her biri küçük **canvas önizleme kartı** (kare/yatay), seçili
  vurgulu; + yoğunluk slider'ı + aç/kapat anahtarı.
- **Marka:** jam adı, slogan, **logo** yükle, **arka plan görseli** yükle.
- **Yollar:** oyunlar klasörü seç/aç.
- **Sunum/Launcher:** varsayılan süre, süre bitince davranış, zamanlayıcı katmanı aç/kapat, kiosk kilidi.
- Köşede dil değiştirme + "varsayılana dön".

## BİLEŞEN KİTAPLIĞI (tutarlı tasarla, hepsi tema değişkenli)
- **Butonlar:** `primary` (accent dolgu + glow), `secondary` (yüzey + kenarlık), `danger` (error), `lg` boyut,
  ikon+metin, yükleniyor (spinner) durumu, disabled.
- **Kart:** `surface` zemin, `border`, `radius`, hafif gölge; başlık satırı (ikon + başlık). `featured` varyant (accent vurgulu).
- **Çip/rozet:** küçük, yuvarlak; durum renkleri (ok/uyarı/hata/accent).
- **Input/select/slider/switch/onay kutusu:** accent vurgulu, odak halkası.
- **Konsol:** koyu, mono, kaydırılır, satır renkleri.
- **İlerleme çubuğu**, **toast bildirimi** (sağ alt, başarı/bilgi/hata), **modal** (onay diyaloğu).
- **Sekme/segment** kontrolü (Sonuçlar varyantı için).

## ÇIKTI FORMATI (önemli)
- **Tek `index.html`** ver: `<head>`'de `<style>` (tüm CSS, `:root` değişkenleri dahil), `<body>`'de sidebar +
  tüm ekranlar (`section.screen`, biri `.active`). Ekranlar arası geçişi göstermek için en fazla **küçük bir
  vanilla JS** (nav tıklayınca aktif `.screen` değiştir) yeterli — başka mantık ekleme.
- Dinamik listelerde (oyun listesi, kategoriler, oy linkleri, sonuç satırları) **2-3 örnek statik kart** koy ki
  düzen görünsün.
- Anlamlı **class isimleri** kullan (örn `.sidebar .nav-item .card .btn .btn-primary .chip .hero-art .vote-grid`),
  geliştirici bunları JS'e bağlayacak. ID'leri çok şart koşma; düzen ve sınıflar yeterli.
- Kısa bir **tasarım notu** ekle (renk/tipografi/spacing mantığın) ki tutarlı genişletebilelim.

## YAPMA
- Harici font/CDN/framework/JS kütüphanesi yok. Sabit hex renk (değişken dışında) yok. Aşırı animasyon/parlama
  yok. Devasa boşluk yok (özellikle oylama ekranı kompakt). Erişilebilir kontrast koru.

Teşekkürler — şık, tutarlı ve **tema-değişkeni odaklı** tek bir `index.html` bekliyorum.
