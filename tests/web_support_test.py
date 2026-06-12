"""Web (HTML5) game support test: local WebGL server headers, web detection in
scanGames, manual name/team override, and browser discovery.

Run: python tests/web_support_test.py
"""
import gzip
import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.web_server import serve_folder           # noqa: E402
from backend.api import JamDeckAPI, _find_browser, _find_web_index  # noqa: E402

log = []
def check(name, ok, extra=""):
    log.append(("PASS" if ok else "FAIL") + f"  {name}" + (f" — {extra}" if extra else ""))

def w(path, data="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, (bytes, bytearray)) else "w"
    with open(path, mode) as f:
        f.write(data)


# ---------------------------------------------------- web_server headers
root = tempfile.mkdtemp(prefix="jamdeck_webgl_")
w(os.path.join(root, "index.html"), "<html><body>hi</body></html>")
# .unityweb compressed with gzip (magic 1f 8b) -> server must send gzip encoding
w(os.path.join(root, "Build", "game.data.unityweb"), gzip.compress(b"unity data payload"))
w(os.path.join(root, "Build", "game.wasm"), b"\x00asm\x01\x00\x00\x00")

httpd, port = serve_folder(root)
base = f"http://127.0.0.1:{port}"
try:
    with urllib.request.urlopen(base + "/index.html") as r:
        check("index.html 200 + html type", r.status == 200 and "text/html" in r.headers.get("Content-Type", ""),
              r.headers.get("Content-Type"))
    with urllib.request.urlopen(base + "/Build/game.data.unityweb") as r:
        check("unityweb -> Content-Encoding gzip", r.headers.get("Content-Encoding") == "gzip",
              str(r.headers.get("Content-Encoding")))
        check("unityweb -> octet-stream type", r.headers.get("Content-Type") == "application/octet-stream",
              r.headers.get("Content-Type"))
    with urllib.request.urlopen(base + "/Build/game.wasm") as r:
        check("wasm -> application/wasm", r.headers.get("Content-Type") == "application/wasm",
              r.headers.get("Content-Type"))
    # path traversal blocked
    try:
        urllib.request.urlopen(base + "/../secret")
        check("path traversal blocked", False)
    except urllib.error.HTTPError as e:
        check("path traversal blocked", e.code in (403, 404), str(e.code))
finally:
    httpd.shutdown()
check("server shut down", True)


# ---------------------------------------------------- scanGames web detection
games = tempfile.mkdtemp(prefix="jamdeck_webscan_")
wg = os.path.join(games, "webgame")
w(os.path.join(wg, "index.html"), "<html></html>")
w(os.path.join(wg, "Build", "Jam.data.unityweb"), b"x")
w(os.path.join(wg, "metadata.json"), json.dumps({"title": "Webby", "author": "Dev W"}))

api = JamDeckAPI()
api._load_config = lambda: {"paths": {"gamesDir": games}}
api.OVERRIDES_FILE = Path(games) / "game_overrides.json"

games_list = api.scanGames()
g = next((x for x in games_list if x["id"] == "webgame"), {})
check("web game detected (engine=web)", g.get("engine") == "web", str(g.get("engine")))
check("web game not broken", g.get("is_broken") is False)
check("web game is_web flag", g.get("is_web") is True)
check("web name from metadata", g.get("game") == "Webby", str(g.get("game")))
check("_games has web + index_dir", api._games.get("webgame", {}).get("web") is True
      and bool(api._games.get("webgame", {}).get("index_dir")))
check("_find_web_index returns folder with index.html",
      _find_web_index(wg) and os.path.exists(os.path.join(_find_web_index(wg), "index.html")))


# ---------------------------------------------------- manual override persistence
res = api.setGameInfo("webgame", "Süper Oyun", "Takım X")
check("setGameInfo ok", res.get("ok") is True, str(res))
check("override file written", api.OVERRIDES_FILE.exists())
games_list2 = api.scanGames()
g2 = next((x for x in games_list2 if x["id"] == "webgame"), {})
check("override applied: name", g2.get("game") == "Süper Oyun", str(g2.get("game")))
check("override applied: team", g2.get("team") == "Takım X", str(g2.get("team")))


# ---------------------------------------------------- browser discovery
check("_find_browser finds Chrome/Edge", bool(_find_browser()), str(_find_browser()))

print("\n=== WEB SUPPORT TEST ===")
print("\n".join(log))
fails = sum(1 for l in log if l.startswith("FAIL"))
print(f"\n{len(log)-fails}/{len(log)} passed")
sys.exit(1 if fails else 0)
