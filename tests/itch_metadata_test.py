"""Faz 4 test: itch.io otomatik metadata (oyun adÄ± + takÄ±m + kapak).

(1) scanGames metadata.json'dan title/author okur; metadata'sÄ±z klasÃ¶r sezgisele dÃ¼ÅŸer.
(2) organizeFiles itch klasÃ¶rÃ¼nÃ¼ (<slug>/files/<zip> + metadata.json) YERÄ°NDE Ã§Ä±karÄ±r;
    metadata.json korunur, files/ silinir, ayrÄ± bir klasÃ¶r oluÅŸmaz.
Run: python tests/itch_metadata_test.py
"""
import base64
import json
import os
import sys
import time
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.api import JamDeckAPI  # noqa: E402

log = []
def check(name, ok, extra=""):
    log.append(("PASS" if ok else "FAIL") + f"  {name}" + (f" â€” {extra}" if extra else ""))

# tiny valid 1x1 PNG
PNG_1x1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

def write(path, data="x"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    mode = "wb" if isinstance(data, (bytes, bytearray)) else "w"
    with open(path, mode) as f:
        f.write(data)


# ------------------------------------------------------------ (1) scanGames
tmp1 = tempfile.mkdtemp(prefix="jamdeck_scan_")
# itch folder: metadata.json + cover.png + exe in place
dev1 = os.path.join(tmp1, "222ss99")
write(os.path.join(dev1, "metadata.json"),
      json.dumps({"title": "Vargus", "author": "Eren Soylu"}))
write(os.path.join(dev1, "cover.png"), PNG_1x1)
write(os.path.join(dev1, "Vargus.exe"), b"MZ")
# plain folder (no metadata) -> heuristic fallback
dev_plain = os.path.join(tmp1, "PlainTeam")
write(os.path.join(dev_plain, "MyCoolGame.exe"), b"MZ")

api = JamDeckAPI()
api._load_config = lambda: {"paths": {"gamesDir": tmp1}}
games = api.scanGames()
by_id = {g["id"]: g for g in games}

check("scanGames found both folders", len(games) == 2, f"count={len(games)}")
g1 = by_id.get("222ss99", {})
check("itch: game name from metadata.title", g1.get("game") == "Vargus", str(g1.get("game")))
check("itch: team from metadata.author", g1.get("team") == "Eren Soylu", str(g1.get("team")))
check("itch: cover loaded (data url)", str(g1.get("cover") or "").startswith("data:image"), str(g1.get("cover"))[:24])
gp = by_id.get("PlainTeam", {})
check("plain: game name falls back to exe", gp.get("game") == "MyCoolGame", str(gp.get("game")))
check("plain: no metadata -> heuristic team", gp.get("team") == "PlainTeam", str(gp.get("team")))


# --------------------------------------------------- (2) organize in place
tmp2 = tempfile.mkdtemp(prefix="jamdeck_org_")
dev2 = os.path.join(tmp2, "devslug")
write(os.path.join(dev2, "metadata.json"),
      json.dumps({"title": "Tutsak", "author": "AKP"}))
write(os.path.join(dev2, "cover.jpg"), PNG_1x1)
zip_path = os.path.join(dev2, "files", "DemoJam2025.zip")
os.makedirs(os.path.dirname(zip_path), exist_ok=True)
with zipfile.ZipFile(zip_path, "w") as z:
    z.writestr("Tutsak.exe", "MZ")

api2 = JamDeckAPI()
api2._window = None                       # _emit becomes a no-op
api2._load_config = lambda: {"paths": {"gamesDir": tmp2}}
api2.organizeFiles()

# wait for the background thread to finish (files/ removed + exe extracted)
deadline = time.time() + 15
while time.time() < deadline:
    if os.path.exists(os.path.join(dev2, "Tutsak.exe")) and not os.path.exists(os.path.join(dev2, "files")):
        break
    time.sleep(0.2)

check("itch extracted in place (exe in slug dir)", os.path.exists(os.path.join(dev2, "Tutsak.exe")))
check("metadata.json preserved", os.path.exists(os.path.join(dev2, "metadata.json")))
check("cover preserved", os.path.exists(os.path.join(dev2, "cover.jpg")))
check("files/ cleaned up", not os.path.exists(os.path.join(dev2, "files")))
check("no separate folder created", not os.path.exists(os.path.join(tmp2, "DemoJam2025")))

# and scanGames now reads it end-to-end
games2 = api2.scanGames()
g2 = next((g for g in games2 if g["id"] == "devslug"), {})
check("post-organize scan: name+team from metadata", g2.get("game") == "Tutsak" and g2.get("team") == "AKP",
      f"game={g2.get('game')} team={g2.get('team')}")

print("\n=== ITCH METADATA TEST ===")
print("\n".join(log))
fails = sum(1 for l in log if l.startswith("FAIL"))
print(f"\n{len(log)-fails}/{len(log)} passed")
sys.exit(1 if fails else 0)

