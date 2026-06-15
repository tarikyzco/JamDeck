"""Rate limit = voterId başına (IP değil). Funnel'da tüm seyirci tek IP görünür;
IP anahtarı 460 kişiyi tek kotaya sıkıştırırdı. Bu test: çok farklı voterId
birbirini BOĞMAZ; tek voterId hızlı atınca yine sınırlanır.
Çalıştır: python tests/vote_ratelimit_test.py  (repo kökünden)"""
import sys, os, json, tempfile, urllib.request, urllib.error

sys.path.insert(0, "backend")
import voting_server
voting_server.ACCESS_FILE = os.path.join(tempfile.gettempdir(), "_rl_test_access.json")
voting_server.VOTES_FILE = os.path.join(tempfile.gettempdir(), "_rl_test_votes.json")
for f in (voting_server.ACCESS_FILE, voting_server.VOTES_FILE):
    if os.path.exists(f):
        os.remove(f)
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
    "groups": {"audience": {"enabled": True, "weight": 25, "label": "Seyirci",
                            "access": "open", "pin": "", "limit": 0, "codeCount": 0}},
    "rateLimit": {"enabled": True, "windowSec": 10, "max": 8},   # VARSAYILAN sınır
}
r = vs.start(port=8807, config=config)
base = f"http://127.0.0.1:{r['port']}"
tok = [t for t, g in vs.tokens.items() if g == "audience"][0]
vs.set_current({"id": "g1", "name": "Oyun A"})

def post_vote(voter):
    body = json.dumps({"t": tok, "game_id": "g1", "scores": {"overall": 7}, "voter": voter}).encode()
    req = urllib.request.Request(f"{base}/api/vote", data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code

try:
    # 100 FARKLI voterId hepsi tek makineden (=tek IP) → hiçbiri rate yememeli
    codes = [post_vote(f"dev{i}") for i in range(100)]
    rate_blocked = sum(1 for c in codes if c == 429)
    ok200 = sum(1 for c in codes if c == 200)
    chk("100 farklı cihaz tek IP'den: 0 rate-engeli", rate_blocked == 0, f"429={rate_blocked} 200={ok200}")

    # tek voterId 15 hızlı oy → ~8 geçer (per-voter sınır hâlâ çalışır)
    codes2 = [post_vote("spammer") for _ in range(15)]
    ok_single = sum(1 for c in codes2 if c == 200)
    blk_single = sum(1 for c in codes2 if c == 429)
    chk("tek cihaz selinde sınır çalışır (~8 geçer)", ok_single <= 8 and blk_single >= 1,
        f"200={ok_single} 429={blk_single}")

    # rate yiyen cihaz BAŞKA cihazları etkilemez
    chk("yeni cihaz spammer'dan etkilenmez", post_vote("fresh_dev") == 200)
finally:
    vs.stop()
    for f in (voting_server.ACCESS_FILE, voting_server.VOTES_FILE):
        if os.path.exists(f):
            os.remove(f)

print(f"\n{P}/{P+F} passed")
sys.exit(1 if F else 0)
