# JamDeck — Logo Tasarım Promptu

Uygulama kimliği: **JamDeck** — evrensel game jam launcher'ı. Herhangi bir jam'e,
herhangi bir markaya hizmet eder (16 tema, TR/EN); logo bu yüzden **hiçbir jam'in
kimliğine bağlanmaz**. Kimliği üç kavramdan gelir:
- **Launch** (oyunu sahneye fırlatma — play butonu / başlatma enerjisi)
- **Deck** (güverte/deste — oyunların dizildiği platform, üst üste kartlar)
- **Jam** (sayaç, enerji, yarışma temposu)

Renk: logo **renge bağımlı olmamalı** (uygulama 16 farklı temayla çalışıyor).
Ana üretimde nötr/teknolojik bir palet kullan (örn. beyaz/grafit + tek vurgu rengi);
vurgu rengi varyantlarda değiştirilebilir olmalı.

---

## Ana Prompt (EN — Midjourney / DALL-E / Ideogram / SD hepsinde çalışır)

> Minimal flat vector logo for "JamDeck", a universal game jam launcher app.
> A rounded-square app icon: three stacked rounded cards fanned like a deck,
> the top card carrying a bold play-button triangle. Clean geometric shapes,
> sharp modern angles, energetic launch feel. Monochrome white-and-graphite
> base with a single vibrant accent color on the play triangle. Flat design,
> no text, no 3D render, no photorealism, centered composition with generous
> margin — must stay readable at 16×16 favicon size.

**Negatif / kaçınılacaklar:** `text, letters, watermark, 3D, bevel, photorealistic,
busy background, clutter, thin hairlines, seasonal or weather motifs (snow, ice,
fire), any specific jam branding`

---

## Varyantlar

### V1 — Gamepad + play
> App icon: a minimalist gamepad silhouette merged with a play-button triangle
> at its center, single-weight geometric line style, one accent color on a dark
> neutral rounded square, flat vector, no text.

### V2 — Fırlatma rampası (launch)
> App icon: an upward play triangle doubling as a launching rocket with two
> speed lines beneath it, suggesting "launching games on stage". Geometric,
> flat vector, neutral dark background, single accent color, no text.

### V3 — Sayaç/jam enerjisi
> App icon: a play-button triangle inscribed in a circular countdown dial with
> a tick mark at 12 o'clock, evoking a 48-hour game jam timer. Flat geometric
> vector, two-tone neutral palette plus one accent color, no text.

### V4 — Yatay kelime işareti (başlık/splash için)
> Horizontal logotype "JAMDECK" in a bold geometric display font with sharp
> diagonal cuts, the letter "A" replaced by a play-button triangle. Neutral
> single color (works in pure white or pure black), flat vector.

---

## Kullanım Notları

- **Tema bağımsızlığı:** Uygulamada 16 tema var (koyu+açık). Logoyu tek vurgu
  renkli iste; vurgu rengini sonradan değiştirmek kolay olur. Salt beyaz ve
  salt siyah tek-renk versiyonları mutlaka üretilmeli.
- **Boyut testi:** 16, 32, 48, 256 px'te okunabilirlik (ICO çoklu boyut içermeli).
- **Zemin testi:** koyu (#0a0a14 gibi) ve açık (#f6f7fb gibi) zeminlerde dene.
- Üreticiden **SVG veya 1024×1024 PNG** iste; ICO'ya çevirip `main.py`
  `create_window`'a ve PyInstaller spec'ine bağlamak sonraki adım.
- Sidebar'daki yer tutucu (`index.html` `#__bundler_thumbnail` şablonu)
  play-button-in-rounded-square fikrini kullanıyor — V2/ana prompt bununla
  uyumlu, seçilen logo onun yerine geçebilir.
