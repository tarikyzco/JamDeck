"""Seyirci (open) kapasite limiti = GİRİŞTE koltuk rezervasyonu.
Gerçek VotingServer'ı HTTP üzerinden sürer; iki voter ile limit=1 senaryosu.
Çalıştır: python tests/vote_capacity_test.py  (repo kökünden)"""
import sys, os, json, tempfile, urllib.request, urllib.error

sys.path.insert(0, "backend")
import voting_server
voting_server.ACCESS_FILE = os.path.join(tempfile.gettempdir(), "_cap_test_access.json")
if os.path.exists(voting_server.ACCESS_FILE):
    os.remove(voting_server.ACCESS_FILE)
from voting_server import VotingServer

P = F = 0
def chk(name, ok, extra=""):
    global P, F
    if ok: P += 1; print(f"PASS  {name}" + (f" — {extra}" if extra else ""))
    else:  F += 1; print(f"FAIL  {name}" + (f" — {extra}" if extra else ""))

vs = VotingServer()
config = {
    "scale": 10,
    "categories": [{"id": "overall", "label": "Genel", "weight": 30, "enabled": True}],
    "groups": {
        "audience": {"enabled": True, "weight": 25, "label": "Seyirci",
                     "access": "open", "pin": "", "limit": 1, "codeCount": 0},
    },
    "rateLimit": {"enabled": False},
}
r = vs.start(port=8806, config=config)
base = f"http://127.0.0.1:{r['port']}"
atok = [t for t, g in vs.tokens.items() if g == "audience"][0]
vs.set_current({"id": "g1", "name": "Oyun A"})

def get_current(voter):
    url = f"{base}/api/current?t={atok}&voter={voter}"
    with urllib.request.urlopen(url) as resp:
        return json.loads(resp.read().decode())

def post_vote(voter):
    body = json.dumps({"t": atok, "game_id": "g1", "scores": {"overall": 7}, "voter": voter}).encode()
    req = urllib.request.Request(f"{base}/api/vote", data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())

try:
    # A girişe gelir → koltuk rezerve, authed/full doğru
    a = get_current("A")
    chk("A girişte authed", a.get("authed") is True, f"authed={a.get('authed')}")
    chk("A girişte dolu değil", a.get("full") is False, f"full={a.get('full')}")

    # B girişe gelir → koltuk dolu (limit=1), form yerine 'full'
    b = get_current("B")
    chk("B girişte authed DEĞİL", b.get("authed") is False, f"authed={b.get('authed')}")
    chk("B girişte FULL", b.get("full") is True, f"full={b.get('full')}")

    # A oy verir → başarılı
    sa, da = post_vote("A")
    chk("A oyu kabul", sa == 200 and da.get("ok") is True, f"{sa} {da}")

    # B oy vermeyi dener → reddedilir (full)
    sb, db = post_vote("B")
    chk("B oyu RED (full)", sb == 403 and db.get("error") == "full", f"{sb} {db}")

    # A tekrar girer → hâlâ koltukta (idempotent)
    a2 = get_current("A")
    chk("A idempotent koltuk", a2.get("authed") is True and a2.get("full") is False)

    # admin göstergesi: 1/1 dolu
    ac = vs.get_access_codes()
    used = ac["audience"]["used"]; seats = ac["audience"]["seats"]
    chk("admin used/seats = 1/1", used == 1 and seats == 1, f"{used}/{seats}")

    # Sıfırla → open koltukları serbest → B artık girebilir
    vs.reset_votes()
    b2 = get_current("B")
    chk("reset sonrası B girer", b2.get("authed") is True and b2.get("full") is False)
finally:
    vs.stop()
    if os.path.exists(voting_server.ACCESS_FILE):
        os.remove(voting_server.ACCESS_FILE)

print(f"\n{P}/{P+F} passed")
sys.exit(1 if F else 0)
