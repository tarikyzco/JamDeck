<div align="right">

[🇹🇷 Türkçe](README.md) · 🇬🇧 **English**

</div>

# 🎮 JamDeck

**All-in-one desktop toolkit for running game jams** — downloads builds from
itch.io, presents them on stage, runs weighted **online** voting from phones
(fixed link/QR, stable up to ~500 people), reveals results with a cinematic
ceremony, and puts a themed 48-hour countdown on the venue screen. Customizable for any jam.
Available in **7 languages** — Türkçe · English · Français · Deutsch · Español ·
Português · 日本語.

![JamDeck interface in 7 languages](docs/jamdeck-langs.gif)

> ℹ️ **Note:** The permanent logo hasn't been chosen yet — the current icon is
> a temporary placeholder.

## ⬇️ Download

**[Get the latest release →](../../releases/latest)**

| File | What for |
|---|---|
| `JamDeck-Setup-vX.Y.Z.exe` | **Recommended** — classic installer: Start Menu + desktop shortcut, uninstaller. No admin rights needed. |
| `JamDeck-vX.Y.Z-win64.zip` | Portable: extract to a folder and run `JamDeck.exe`. Even works from a USB stick. |

- On the Windows SmartScreen warning: **More info → Run anyway** (the app is unsigned).
- The installer configures the Windows Firewall permission with a single
  admin confirmation — no firewall popup when you start voting/countdown at the jam.
- Everything after that is automatic: on startup the app announces new
  versions; click **Download & Install** and it updates itself — your settings
  and votes are preserved (in both distributions).

**Requirements:** Windows 10/11 (WebView2 — preinstalled on Windows 11).

## ✨ Features

| | |
|---|---|
| 📥 **Download & Prepare** | One-click itch.io jam archive download, extracts zip/rar/7z/tar and nested archives, pulls game name + cover automatically, flags broken submissions |
| 🎬 **Presentation** | Fullscreen stage: game list + giant cover + one-click launch; auto-close on time-up, web (HTML5/WebGL) games included |
| 🗳️ **LAN Voting** | Jury / Audience / Team vote from phones (weighted categories); single-use access codes, **live code board** (used codes flip instantly for everyone), QR screen |
| 🏆 **Results** | Top-3 podium, per-group breakdowns, shareable PNG results poster + technical .xlsx report |
| ⏱️ **Countdown** | 48-hour jam timer: 8 styles (Neon, LED, Pixel, Glitch, HP-Bar…), 3 logo slots, **auto-fullscreen from any screen** 10 minutes before start, OBS Browser-Source support |
| 🎨 **Themes** | 16 presets + full color/font/effect customization; the theme carries over to the phone voting page |
| 📋 **Submission Guide** | Rules screen to share with participants + 1080×1920 poster export; texts editable in-app |
| 🔄 **Auto-Update** | The app finds, downloads and installs new versions by itself |
| 🌍 **7 Languages** | Whole UI in Turkish, English, French, German, Spanish, Portuguese and Japanese — including the phone voting page, code board and OBS countdown; default vote categories localize too, switch live from a dropdown |

## 📸 Screenshots

| Presentation stage | Setup & themes |
|---|---|
| ![Presentation](docs/sunum.png) | ![Themes](docs/kurulum-temalar.png) |

| Voting admin | Voting on a phone | Live code board |
|---|---|---|
| ![Voting](docs/oylama.png) | ![Phone](docs/telefon-oylama.png) | ![Code board](docs/kod-panosu.png) |

| Countdown (Pixel style) | Countdown setup | Results |
|---|---|---|
| ![Countdown](docs/sayac-pixel.png) | ![Countdown setup](docs/sayac-kurulum.png) | ![Results](docs/sonuclar.png) |

## 📖 User Guide

### ➡️ **[Open JamDeck Guide (one click)](https://tarikyzco.github.io/JamDeck/JamDeck-Guide.html)**

Step-by-step interactive guide — all screens, FAQ and tips. Opens directly in your browser
(currently in Turkish); you can also download it for offline use.

## ℹ️

JamDeck is a closed-source, **free** application. Use the
[Issues](../../issues) page for bug reports and suggestions.

© 2026 tarikyzco
