# -*- coding: utf-8 -*-
"""Oy verisi dayanıklılığı: atomik kayıt, .bak tek-adım geri, bozuk dosyadan
kurtarma, zaman damgalı anlık görüntü (vote_backups/)."""
import os
import sys
import json
import time
import glob
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import voting_server as vs

_passed = 0
_failed = 0


def step(name, ok, extra=""):
    global _passed, _failed
    if ok:
        _passed += 1
        print("PASS  " + name + ((" — " + str(extra)) if extra else ""))
    else:
        _failed += 1
        print("FAIL  " + name + ((" -> " + str(extra)) if extra else ""))


def main():
    tmp = tempfile.mkdtemp(prefix="jamdeck_votes_")
    # modül yollarını temp'e yönlendir
    vs.MODULE_DIR = tmp
    vs.VOTES_FILE = os.path.join(tmp, "votes.json")
    srv = vs.VotingServer()
    srv.votes = []

    # 1) atomik kayıt + roundtrip
    srv.votes = [{"game_id": 1, "voter": "a", "scores": {"overall": 8}}]
    srv._save_votes()
    step("votes.json yazıldı", os.path.exists(vs.VOTES_FILE))
    step("yazma sırasında .tmp kalmadı", not os.path.exists(vs.VOTES_FILE + ".tmp"))
    srv2 = vs.VotingServer()
    srv2.votes = []
    srv2._load_votes()
    step("roundtrip: yüklenen oy sayısı", len(srv2.votes) == 1, len(srv2.votes))

    # 2) ikinci kayıt önceki sağlam dosyayı .bak'a alır
    srv.votes.append({"game_id": 1, "voter": "b", "scores": {"overall": 6}})
    srv._save_votes()
    step(".bak oluştu (tek-adım geri)", os.path.exists(vs.VOTES_FILE + ".bak"))
    bak = json.load(open(vs.VOTES_FILE + ".bak", encoding="utf-8"))
    step(".bak önceki durumu tutuyor (1 oy)", len(bak) == 1, len(bak))

    # 3) yanlış sıfırlama .bak'tan kurtarılabilir
    pre_reset = list(srv.votes)
    srv.votes = []
    srv._save_votes()  # boş yazıldı; .bak artık 2 oyu tutar
    bak2 = json.load(open(vs.VOTES_FILE + ".bak", encoding="utf-8"))
    step("sıfırlama sonrası .bak sıfırlama-öncesini tutuyor", len(bak2) == len(pre_reset) == 2, len(bak2))

    # 4) bozuk ana dosya → .bak'tan otomatik kurtarma
    open(vs.VOTES_FILE, "w", encoding="utf-8").write("{ bozuk json @@@")
    srv3 = vs.VotingServer()
    srv3.votes = None
    srv3._load_votes()
    step("bozuk votes.json → .bak'tan kurtarıldı", srv3.votes is not None and len(srv3.votes) == 2,
         None if srv3.votes is None else len(srv3.votes))

    # 5) zaman damgalı anlık görüntü (dolu durum) + boş yedeklenmez
    bdir = os.path.join(tmp, "vote_backups")
    snaps0 = glob.glob(os.path.join(bdir, "votes-*.json")) if os.path.isdir(bdir) else []
    step("dolu kayıtta anlık görüntü alındı", len(snaps0) >= 1, len(snaps0))
    # boş kayıt anlık görüntü EKLEMEZ
    srv.votes = []
    srv._last_snapshot = 0  # throttle'ı sıfırla
    srv._save_votes()
    snaps1 = glob.glob(os.path.join(bdir, "votes-*.json"))
    step("boş durum anlık görüntü eklemez", len(snaps1) == len(snaps0), "%d==%d" % (len(snaps1), len(snaps0)))

    # 6) anlık görüntü 60 sn throttle
    srv.votes = [{"game_id": 2, "voter": "c", "scores": {"overall": 9}}]
    srv._last_snapshot = time.time()  # az önce alınmış gibi
    before = len(glob.glob(os.path.join(bdir, "votes-*.json")))
    srv._save_votes()
    after = len(glob.glob(os.path.join(bdir, "votes-*.json")))
    step("throttle: 60 sn içinde ikinci anlık görüntü yok", after == before, "%d==%d" % (after, before))

    print()
    print("%d/%d passed" % (_passed, _passed + _failed))
    return 0 if _failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
