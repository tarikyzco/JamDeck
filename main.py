import os
import sys
import ctypes
from pathlib import Path


def resource_path(relative: str) -> Path:
    try:
        base = Path(sys._MEIPASS)
    except AttributeError:
        base = Path(os.path.abspath(__file__)).parent
    return base / relative


def main():
    # GÖMÜLÜ itch-dl: frozen exe kendini bu argümanla yeniden çağırır → harici
    # "itch-dl" CLI'ına (pip kurulumu) gerek kalmaz, her sistemde çalışır.
    if len(sys.argv) > 1 and sys.argv[1] == "__itch-dl__":
        from itch_dl.cli import run as _itch_run
        sys.argv = ["itch-dl"] + sys.argv[2:]
        sys.exit(_itch_run())

    if len(sys.argv) > 1 and sys.argv[1] == "--overlay":
        from backend.overlay import run_overlay
        mins = sys.argv[2] if len(sys.argv) > 2 else "5"
        accent = sys.argv[3] if len(sys.argv) > 3 else "#00f2ff"
        run_overlay(mins, accent)
        return

    # High-DPI awareness (Windows)
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

    import webview
    from backend.api import JamDeckAPI

    api = JamDeckAPI()
    html_path = resource_path("frontend/index.html")

    window = webview.create_window(
        title="JamDeck — Game Jam Launcher",
        url=html_path.as_uri(),
        js_api=api,
        width=1400,
        height=900,
        min_size=(1100, 680),
        resizable=True,
        maximized=True,
        text_select=False,
    )
    api.set_window(window)
    # gui="edgechromium" ZORUNLU: WebView2 yoksa pywebview sessizce eski IE/MSHTML
    # motoruna düşüp modern JS'i çalıştıramaz (siyah ekran / kilitlenme). edgechromium
    # zorlanınca WebView2 eksikse net hata verir (kurulum WebView2'yi zaten yükler).
    try:
        webview.start(gui="edgechromium", debug="--debug" in sys.argv)
    except Exception:
        webview.start(debug="--debug" in sys.argv)   # son çare: varsayılan motor


if __name__ == "__main__":
    main()
