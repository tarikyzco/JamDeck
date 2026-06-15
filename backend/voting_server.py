import os
import re
import json
import glob
import html
import time
import shutil
import socket
import secrets
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn
try:
    from backend.voter_page import VOTER_PAGE, CODES_PAGE
except ImportError:
    from voter_page import VOTER_PAGE, CODES_PAGE

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))   # paket içi (salt-okunur) kaynaklar


def data_dir():
    """Yazılabilir veri yolu (%LOCALAPPDATA%\\JamDeck\\data) — frozen build'de
    _internal'a YAZILMAZ (eski MODULE_DIR yolu .exe'de yazma hatası → hang verirdi)."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "JamDeck", "data")
    try:
        os.makedirs(d, exist_ok=True)
    except OSError:
        pass
    return d


DATA_DIR = data_dir()
VOTES_FILE = os.path.join(DATA_DIR, "votes.json")
ACCESS_FILE = os.path.join(DATA_DIR, "access.json")

# eski sürüm dosyalarını (backend yanı) yeni veri dizinine bir kez taşı
for _old, _new in ((os.path.join(MODULE_DIR, "votes.json"), VOTES_FILE),
                   (os.path.join(MODULE_DIR, "access.json"), ACCESS_FILE)):
    try:
        if os.path.exists(_old) and not os.path.exists(_new) \
                and os.path.abspath(_old) != os.path.abspath(_new):
            shutil.copy2(_old, _new)
    except OSError:
        pass

import sys as _sys
_I18N_CACHE = None


def _load_i18n():
    """Tek kaynak frontend/i18n.js (lang -> {app, voter, countdown}); JSON gövdesi ayıklanır."""
    global _I18N_CACHE
    if _I18N_CACHE is None:
        base = getattr(_sys, "_MEIPASS", os.path.dirname(MODULE_DIR))
        try:
            with open(os.path.join(base, "frontend", "i18n.js"), encoding="utf-8") as f:
                txt = f.read()
            _I18N_CACHE = json.loads(txt[txt.index("{"):txt.rindex("}") + 1])
        except Exception:
            _I18N_CACHE = {}
    return _I18N_CACHE


_LANG_NAMES = {"tr": "Türkçe", "en": "English", "fr": "Français",
               "de": "Deutsch", "es": "Español", "pt": "Português", "ja": "日本語"}


def voter_i18n_block(lang):
    """Voter/Codes sayfasına gömülecek JS: TÜM diller + varsayılan kategori/grup
    etiketleri + dil listesi. Telefondaki oy veren kendi dilini seçebilir (organizatörün
    dili varsayılan); seçim cihazda (localStorage) hatırlanır. Sunucuya gidiş yok."""
    data = _load_i18n()
    langs = list(data.keys()) or ["tr"]
    if lang not in data:
        lang = "tr" if "tr" in data else langs[0]
    voter = {l: (data[l] or {}).get("voter", {}) for l in langs}
    vd = {l: (data[l] or {}).get("vote_defaults", {"cat": {}, "grp": {}}) for l in langs}
    meta = [{"code": l, "name": _LANG_NAMES.get(l, l)} for l in langs]

    def js(o):
        return json.dumps(o, ensure_ascii=False).replace("</", "<\\/")

    return ("const LANG_DEFAULT=%s; const I18N=%s; const VD=%s; const LANGS=%s; "
            "let LANG=(function(){try{var s=localStorage.getItem('jamdeck_voter_lang');"
            "return (s&&I18N[s])?s:LANG_DEFAULT;}catch(e){return LANG_DEFAULT;}})(); "
            "let S=I18N[LANG]||I18N[LANG_DEFAULT]; "
            "const VD_SETS=(function(){var c={},g={};for(var l in VD){var v=VD[l]||{},"
            "cc=v.cat||{},gg=v.grp||{};for(var i in cc){(c[i]=c[i]||[]).push(cc[i]);}"
            "for(var i in gg){(g[i]=g[i]||[]).push(gg[i]);}}return{cat:c,grp:g};})(); "
            "function localCatLabel(id,lbl){var s=VD_SETS.cat[id];if(s&&s.indexOf(lbl)>=0){"
            "var cur=(VD[LANG]||{}).cat||{};return cur[id]||lbl;}return lbl;} "
            "function localGrpLabel(id,lbl){var s=VD_SETS.grp[id];if(s&&s.indexOf(lbl)>=0){"
            "var cur=(VD[LANG]||{}).grp||{};return cur[id]||lbl;}return lbl;}"
            % (js(lang), js(voter), js(vd), js(meta)))

# Human-friendly code alphabet — no easily-confused chars (no O/0/I/1/L).
CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
CODE_LEN = 4


def _is_private_lan(ip):
    """True for typical home/office Wi-Fi ranges (NOT Tailscale 100.x / VPN)."""
    if ip.startswith("192.168.") or ip.startswith("10."):
        return True
    if ip.startswith("172."):
        try:
            return 16 <= int(ip.split(".")[1]) <= 31
        except (IndexError, ValueError):
            return False
    return False


def get_all_ipv4():
    """All non-loopback IPv4 addresses of this machine (Wi-Fi, Ethernet, Tailscale...)."""
    ips = []
    # 1) source IP of the default route (most likely the active interface)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    # 2) everything bound to the hostname
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = info[4][0]
            if ip not in ips:
                ips.append(ip)
    except Exception:
        pass
    return [ip for ip in ips if not ip.startswith("127.")]


def get_lan_ip() -> str:
    """Best single LAN IP: prefer real private Wi-Fi/LAN over Tailscale/VPN."""
    ips = get_all_ipv4()
    lan = [ip for ip in ips if _is_private_lan(ip)]
    if lan:
        return lan[0]
    return ips[0] if ips else "127.0.0.1"

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


# ---------------------------------------------------------------- voter theme
# Voter page shares the desktop app's CSS variable palette; the organizer's
# theme is injected into the /*__THEME__*/ slot inside :root (overrides the
# Frostbite defaults baked into the template).

_THEME_VAR_MAP = {
    "bg": "--bg", "bg2": "--bg-2", "surface": "--surface", "surface2": "--surface-2",
    "border": "--border", "accent": "--accent", "accent2": "--accent-2",
    "accentInk": "--accent-ink", "text": "--text", "textMuted": "--text-muted",
    "success": "--success", "warning": "--warning", "error": "--error",
}
_HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}$")


def _hex_is_light(hex_color):
    c = hex_color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    try:
        r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    except ValueError:
        return False
    return (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 > 0.5


def theme_css(brand):
    """CSS variable overrides for the voter page from {colors, radius, glow}."""
    brand = brand or {}
    colors = brand.get("colors") or {}
    lines = []
    for key, var in _THEME_VAR_MAP.items():
        v = colors.get(key)
        if isinstance(v, str) and _HEX_RE.match(v.strip()):
            lines.append(f"{var}:{v.strip()};")
    # accent üstü metin rengi verilmemişse accent parlaklığından türet
    if "accentInk" not in colors and isinstance(colors.get("accent"), str) \
            and _HEX_RE.match(colors["accent"].strip()):
        ink = "#10131c" if _hex_is_light(colors["accent"]) else "#ffffff"
        lines.append(f"--accent-ink:{ink};")
    radius = brand.get("radius")
    if isinstance(radius, (int, float)):
        r = max(0, min(40, int(radius)))
        lines.append(f"--radius:{r}px;--radius-sm:{max(2, round(r * 0.55))}px;")
    glow = brand.get("glow")
    if isinstance(glow, (int, float)):
        lines.append(f"--glow-a:{max(0, min(60, round(float(glow) * 30)))}%;")
    return "".join(lines)

class VotingServer:
    def __init__(self):
        self.current_game = None
        self.launched_order = []   # game ids in launch order
        self.launched_games = {}   # id -> name (votes stay open for all of these)
        self.config = {}
        self.votes = []
        self._vote_index = {}      # (group,game_id,voter) -> votes listesi indeksi (O(1) upsert)
        self._dirty = False        # kaydedilmemiş oy var mı (biriktirilmiş yazma)
        self._flush_thread = None
        self._state_ver = 0        # /api/current ETag'i: yalnız oyun/config değişince artar (oylar artırmaz)
        self._seen = {}            # voter_id -> son görülme ts (dinamik poll için aktif kişi sayısı)
        self.tokens = {}
        self.admin_token = ""
        self.httpd = None
        self._thread = None
        self.running = False
        self._lock = threading.Lock()
        # access control (Faz 2): per-group one-time codes + authorized voters
        self.access = {"codes": {}, "authorized": {}}  # codes: grp->[{code,voter,ts}]; authorized: grp->[voterId]
        self._rate = {}  # ip -> [timestamps] for per-IP rate limiting
        self.brand = {}  # {jamName, colors, radius, glow} — voter sayfası teması

    def start(self, port=8770, config=None, brand=None):
        if config is None:
            config = {
                "scale": 10,
                "categories": [
                    {"id": "overall", "label": "Genel", "weight": 30, "enabled": True},
                    {"id": "fun", "label": "Eğlence", "weight": 25, "enabled": True},
                    {"id": "theme", "label": "Tema Uyumu", "weight": 15, "enabled": True},
                    {"id": "originality", "label": "Özgünlük", "weight": 12, "enabled": True},
                    {"id": "art", "label": "Görsel/Sanat", "weight": 10, "enabled": True},
                    {"id": "audio", "label": "Ses/Müzik", "weight": 8, "enabled": True},
                ],
                "groups": {
                    "jury": {"enabled": True, "weight": 60, "label": "Jüri"},
                    "audience": {"enabled": True, "weight": 25, "label": "Seyirci"},
                    "team": {"enabled": True, "weight": 15, "label": "Ekip"}
                }
            }
        self.config = config
        self.brand = brand or {}
        self.current_game = None
        self.launched_order = []
        self.launched_games = {}
        self.tokens = {}
        self.admin_token = secrets.token_urlsafe(8)

        groups = config.get("groups", {})
        for group_name in groups:
            self.tokens[secrets.token_urlsafe(8)] = group_name

        self._load_votes()
        self._load_access()
        self._sync_codes()

        # 127.0.0.1'e bind: online oylama Tailscale Funnel ile localhost'tan servis edilir.
        # 0.0.0.0 (tüm arayüzler) Windows güvenlik duvarı pop-up'ını tetikler; bu pop-up
        # PyWebView penceresinin ARKASINDA kalıp socket bind'i bloklayarak "Başlat"ı asardı.
        for attempt in range(10):
            try:
                self.httpd = ThreadingHTTPServer(("127.0.0.1", port), self._create_handler())
                break
            except OSError:
                port += 1
        else:
            return {"ok": False, "error": "No available port found"}

        self.running = True
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

        lan_ip = get_lan_ip()
        self.port = port
        urls = {}
        for token, group_name in self.tokens.items():
            urls[group_name] = f"http://{lan_ip}:{port}/v/{token}"

        # all candidate IPs + the raw group->token map so the UI can rebuild
        # links against a different IP (Tailscale/VPN/multi-adapter setups)
        all_ips = get_all_ipv4() or [lan_ip]
        if lan_ip in all_ips:
            all_ips = [lan_ip] + [ip for ip in all_ips if ip != lan_ip]
        group_tokens = {g: tok for tok, g in self.tokens.items()}

        return {
            "ok": True,
            "ip": lan_ip,
            "ips": all_ips,
            "port": port,
            "urls": urls,
            "group_tokens": group_tokens,
            "admin_token": self.admin_token
        }

    def stop(self):
        if self.httpd and self.running:
            self.running = False
            # bekleyen oyları kaybetmeden son kez diske yaz
            with self._lock:
                if self._dirty:
                    self._dirty = False
                    self._save_votes()
            self.httpd.shutdown()
            if self._thread:
                self._thread.join()
            self.httpd = None
        return {"ok": True}

    def _bump(self):
        """/api/current durum sürümünü artır → açık pollar bir sonraki seferde 200 (taze) alır."""
        self._state_ver += 1

    def set_current(self, game):
        self.current_game = game
        if game and game.get("id"):
            gid = game["id"]
            with self._lock:
                if gid not in self.launched_games:
                    self.launched_order.append(gid)
                self.launched_games[gid] = game.get("name", gid)
        self._bump()

    def set_config(self, config):
        self.config = config
        self._sync_codes()
        self._bump()

    def get_results(self):
        with self._lock:
            scale = self.config.get("scale", 10)
            groups_config = self.config.get("groups", {})
            categories = [c for c in self.config.get("categories", []) if c.get("enabled", True)]
            cat_ids = [c["id"] for c in categories]
            cat_weight = {c["id"]: c.get("weight", 0) for c in categories}

            # games[gid] = {id, name, by_group:{grp:{voters:set, cats:{cid:[scores]}}}}
            games = {}
            for v in self.votes:
                gid = v["game_id"]
                g = games.setdefault(gid, {"id": gid, "name": v.get("game_name", gid), "by_group": {}})
                bg = g["by_group"].setdefault(v["group"], {"voters": set(), "cats": {}})
                if v.get("voter") is not None:
                    bg["voters"].add(v["voter"])
                for cid, sc in (v.get("scores") or {}).items():
                    bg["cats"].setdefault(cid, []).append(sc)

            result_games = []
            for gid, g in games.items():
                groups_result = {}
                total_votes = 0
                for grp_name in groups_config:
                    bg = g["by_group"].get(grp_name)
                    if not bg:
                        groups_result[grp_name] = {"score": None, "count": 0, "categories": {}}
                        continue
                    count = len(bg["voters"])
                    total_votes += count
                    cat_res = {}
                    for cid in cat_ids:
                        lst = bg["cats"].get(cid, [])
                        cat_res[cid] = ({"avg": round(sum(lst) / len(lst), 2), "count": len(lst)}
                                        if lst else {"avg": None, "count": 0})
                    # group score = weight-normalized avg over enabled categories that got votes
                    tw = sum(cat_weight[cid] for cid in cat_ids if cat_res[cid]["avg"] is not None)
                    gscore = (sum(cat_res[cid]["avg"] * (cat_weight[cid] / tw)
                                  for cid in cat_ids if cat_res[cid]["avg"] is not None)
                              if tw > 0 else None)
                    groups_result[grp_name] = {
                        "score": round(gscore, 2) if gscore is not None else None,
                        "count": count, "categories": cat_res,
                    }

                # weighted total over enabled groups that have a score
                enabled = [(n, c) for n, c in groups_config.items()
                           if c.get("enabled", True) and groups_result[n]["score"] is not None]
                gw = sum(c["weight"] for _, c in enabled)
                weighted = (sum(groups_result[n]["score"] * (c["weight"] / gw) for n, c in enabled)
                            if gw > 0 else 0)

                # group-weighted per-category overall (for Excel / ranking image later)
                cat_overall = {}
                for cid in cat_ids:
                    parts = [(c["weight"], groups_result[n]["categories"][cid]["avg"])
                             for n, c in groups_config.items()
                             if c.get("enabled", True)
                             and groups_result[n]["categories"].get(cid, {}).get("avg") is not None]
                    ww = sum(w for w, _ in parts)
                    cat_overall[cid] = round(sum(a * (w / ww) for w, a in parts), 2) if ww > 0 else None

                result_games.append({
                    "id": gid, "name": g["name"],
                    "weighted": round(weighted, 2),
                    "groups": groups_result,
                    "category_overall": cat_overall,
                    "total_votes": total_votes,
                })

            result_games.sort(key=lambda x: x["weighted"], reverse=True)

            # KATILIM = oturum geneli TEKİL oy veren sayısı (kişi), oyların toplamı DEĞİL.
            # Tek cihaz 3 ayrı oyuna oy verse bile o grup için 1 kişi sayılır.
            session_voters = {}
            for v in self.votes:
                vid = v.get("voter")
                if vid is not None:
                    session_voters.setdefault(v.get("group"), set()).add(vid)
            participants = {g: len(s) for g, s in session_voters.items()}
            all_voter_ids = set()
            for s in session_voters.values():
                all_voter_ids |= s

            return {
                "scale": scale,
                "groups": {n: {"enabled": c.get("enabled", True), "weight": c["weight"], "label": c["label"]}
                           for n, c in groups_config.items()},
                "categories": [{"id": c["id"], "label": c["label"], "weight": c.get("weight", 0),
                                "enabled": c.get("enabled", True)}
                               for c in self.config.get("categories", [])],
                "games": result_games,
                "participants": participants,            # grup -> tekil kişi sayısı
                "participants_total": len(all_voter_ids),  # toplam tekil kişi
                "current": self.current_game["id"] if self.current_game else None,
            }

    # ------------------------------------------------------------- xlsx export

    def export_xlsx(self, path):
        """Write the detailed, formatted technical results workbook (openpyxl).

        4 sheets: Özet (ranked, with a per-group average column so the
        jury/audience/team difference is visible), Kategori Kırılımı
        (game x category overall), Grup Kırılımı (per group: game x category +
        vote count), Ham Oylar (every raw vote, for audit). Sorted by weighted
        score. Raises on failure; caller wraps."""
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
        from openpyxl.utils import get_column_letter

        res = self.get_results()
        scale = res.get("scale", 10)
        groups_meta = res.get("groups", {})           # name -> {enabled,weight,label}
        group_names = [n for n, c in groups_meta.items() if c.get("enabled", True)]
        cats = [c for c in res.get("categories", []) if c.get("enabled", True)]
        games = res.get("games", [])                  # already sorted by weighted desc

        HEAD_FILL = PatternFill("solid", fgColor="1E293B")
        HEAD_FONT = Font(bold=True, color="FFFFFF")
        LEAD_FILL = PatternFill("solid", fgColor="14532D")
        thin = Side(style="thin", color="D0D0D0")
        BORDER = Border(left=thin, right=thin, top=thin, bottom=thin)
        CENTER = Alignment(horizontal="center", vertical="center")

        def glabel(n):
            return groups_meta.get(n, {}).get("label", n)

        def style_header(ws, row=1):
            for cell in ws[row]:
                cell.fill = HEAD_FILL
                cell.font = HEAD_FONT
                cell.alignment = CENTER
                cell.border = BORDER

        def autosize(ws, widths):
            for i, w in enumerate(widths, 1):
                ws.column_dimensions[get_column_letter(i)].width = w

        wb = Workbook()

        # ---- Sheet 1: Özet ------------------------------------------------
        ws = wb.active
        ws.title = "Özet"
        header = ["#", "Oyun", f"Ağırlıklı Toplam (/{scale})", "Toplam Oy"]
        header += [f"{glabel(n)} Ort." for n in group_names]
        ws.append(header)
        for i, g in enumerate(games, 1):
            row = [i, g.get("name", g.get("id")), g.get("weighted"), g.get("total_votes", 0)]
            for n in group_names:
                row.append((g.get("groups", {}).get(n) or {}).get("score"))
            ws.append(row)
            if i == 1:
                for cell in ws[ws.max_row]:
                    cell.fill = LEAD_FILL
                    cell.font = Font(bold=True)
        style_header(ws)
        ws.freeze_panes = "A2"
        autosize(ws, [5, 32, 18, 10] + [13] * len(group_names))

        # ---- Sheet 2: Kategori Kırılımı (game x category overall) ---------
        ws = wb.create_sheet("Kategori Kırılımı")
        header = ["Oyun"] + [f"{c['label']} (×{(c.get('weight',0)/100):.2f})" for c in cats]
        ws.append(header)
        for g in games:
            co = g.get("category_overall", {}) or {}
            ws.append([g.get("name", g.get("id"))] + [co.get(c["id"]) for c in cats])
        style_header(ws)
        ws.freeze_panes = "B2"
        autosize(ws, [32] + [16] * len(cats))

        # ---- Sheet 3: Grup Kırılımı (per group: game x category + count) --
        ws = wb.create_sheet("Grup Kırılımı")
        header = ["Grup", "Oyun", "Grup Skoru", "Oy Sayısı"] + [c["label"] for c in cats]
        ws.append(header)
        for n in group_names:
            for g in games:
                bg = g.get("groups", {}).get(n) or {}
                gcats = bg.get("categories", {}) or {}
                row = [glabel(n), g.get("name", g.get("id")), bg.get("score"), bg.get("count", 0)]
                for c in cats:
                    row.append((gcats.get(c["id"]) or {}).get("avg"))
                ws.append(row)
        style_header(ws)
        ws.freeze_panes = "A2"
        autosize(ws, [12, 32, 12, 10] + [14] * len(cats))

        # ---- Sheet 4: Ham Oylar (audit) -----------------------------------
        ws = wb.create_sheet("Ham Oylar")
        cat_ids = [c["id"] for c in cats]
        header = ["Grup", "Oyun", "Voter", "Zaman"] + [c["label"] for c in cats]
        ws.append(header)
        with self._lock:
            raw = list(self.votes)
        raw.sort(key=lambda v: (v.get("group", ""), v.get("game_name", ""), v.get("ts", 0)))
        for v in raw:
            ts = v.get("ts")
            when = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else ""
            scores = v.get("scores", {}) or {}
            row = [glabel(v.get("group", "")), v.get("game_name", v.get("game_id", "")),
                   v.get("voter", ""), when]
            row += [scores.get(cid) for cid in cat_ids]
            ws.append(row)
        style_header(ws)
        ws.freeze_panes = "A2"
        autosize(ws, [12, 32, 26, 19] + [12] * len(cats))

        wb.save(path)
        return {"ok": True, "path": path, "games": len(games), "votes": len(raw)}

    @property
    def is_running(self) -> bool:
        return self.running

    def _load_votes(self):
        # ana dosya bozuksa .bak'tan kurtar (canlı etkinlikte veri kaybına karşı)
        for path in (VOTES_FILE, VOTES_FILE + ".bak"):
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.votes = json.load(f)
                    self._rebuild_index()
                    return
                except (json.JSONDecodeError, IOError):
                    continue
        self.votes = []
        self._rebuild_index()

    def _rebuild_index(self):
        self._vote_index = {(v.get("group"), v.get("game_id"), v.get("voter")): i
                            for i, v in enumerate(self.votes)}

    def _poll_ms(self):
        """Telefonların durum sorma aralığı (ms) — DİNAMİK: aktif kişi sayısına göre
        otomatik ayarlanır. Az kişi → hızlı (responsive); çok kişi → yavaş (yük düşük).
        Böylece toplam istek/sn ~sabit kalır (funnel sınırının altında) → kapasite artar.
        config.pollSeconds verilirse SABİT olur (override). Aralık: 2.5–25 sn."""
        cfg = (self.config or {})
        if cfg.get("pollSeconds"):
            try:
                return int(max(1.5, float(cfg["pollSeconds"])) * 1000)
            except (TypeError, ValueError):
                pass
        # CANLI STRES TESTİ DATASI (Tailscale Funnel): ≤50 req/s → %99.3-100;
        # ~70 req/s → %99.6 (nadir 502); ~90 req/s → çöküş (%54). Hedefi güvenli
        # bölgenin içine (45 req/s) koyuyoruz → ~%100, bol marj.
        n = len(self._seen)              # aktif voter (flush thread 30 sn'de bir budar)
        target_rps = 45.0
        ms = int(n / target_rps * 1000)
        # alt 2.5 sn (az kişide responsive), üst 25 sn (çok kişide yük düşük; ~1250 kişiye
        # kadar req/s 45 altında kalır, sonra hafif tırmanır ama 70'e (güvenli) ~1750'de ulaşır)
        return max(2500, min(25000, ms))

    def _flush_loop(self):
        """Biriktirilmiş kayıt: oylar her POST'ta değil, en fazla ~1.5 sn'de bir
        diske yazılır → yazma yolundaki O(n²)/disk darboğazı kalkar. Kilit kısa
        süre (tek dosya yazımı) tutulur; bu sıklıkta önemsiz."""
        while self.running:
            time.sleep(1.5)
            if self._dirty:
                with self._lock:
                    self._dirty = False
                    self._save_votes()
            # aktif-voter sayacını buda: 30 sn'dir sormayan ayrılmış sayılır (dinamik poll)
            if self._seen:
                cutoff = time.time() - 30
                for v in [v for v, ts in list(self._seen.items()) if ts < cutoff]:
                    self._seen.pop(v, None)

    def _save_votes(self):
        """Oyları çökmeye/bozulmaya dayanıklı kaydet: önce .tmp'ye yaz + fsync,
        eski sağlam dosyayı .bak'a kopyala (tek-adım geri — yanlış sıfırlamayı bile
        kurtarır), sonra atomik os.replace. Ayrıca zaman damgalı anlık görüntü."""
        try:
            tmp = VOTES_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self.votes, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            if os.path.exists(VOTES_FILE):
                try:
                    shutil.copy2(VOTES_FILE, VOTES_FILE + ".bak")
                except OSError:
                    pass
            os.replace(tmp, VOTES_FILE)   # atomik: yarım yazılmış dosya asla kalmaz
            self._snapshot_votes()
        except IOError:
            pass

    def _snapshot_votes(self):
        """Dolu oy durumunun zaman damgalı yedeği (vote_backups/), en fazla 60 sn'de
        bir, son 30 kopya tutulur. Boş durum yedeklenmez (yanlış sıfırlama iyi
        anlık görüntüleri itip atmasın; geri alma için .bak zaten var)."""
        if not self.votes:
            return
        now = time.time()
        if now - getattr(self, "_last_snapshot", 0) < 60:
            return
        self._last_snapshot = now
        try:
            d = os.path.join(DATA_DIR, "vote_backups")
            os.makedirs(d, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            with open(os.path.join(d, "votes-%s.json" % ts), "w", encoding="utf-8") as f:
                json.dump(self.votes, f, ensure_ascii=False, indent=2)
            snaps = sorted(glob.glob(os.path.join(d, "votes-*.json")))
            for old in snaps[:-30]:
                try:
                    os.remove(old)
                except OSError:
                    pass
        except OSError:
            pass

    def reset_votes(self):
        """Wipe all collected votes (memory + votes.json) so the live counter /
        results start fresh. The launched-game list and current game are kept (a
        mid-session reset shouldn't blank out voters' active game). Credential
        seats (pin authorizations + code claims) are left intact (use 'Regenerate'
        for those), but open-access auto-admit seats ARE freed so a fresh event
        starts with an empty audience (open seats are participation, not a key)."""
        with self._lock:
            self.votes = []
            self._vote_index = {}
            self._dirty = False
            for gname, gcfg in self.config.get("groups", {}).items():
                if gcfg.get("access", "open") == "open":
                    self.access["authorized"].pop(gname, None)
            self._state_ver += 1
            self._save_votes()
            self._save_access()
        return {"ok": True}

    # ----------------------------------------------------------- access control

    def _load_access(self):
        self.access = {"codes": {}, "authorized": {}}
        if os.path.exists(ACCESS_FILE):
            try:
                with open(ACCESS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self.access["codes"] = data.get("codes", {}) or {}
                    self.access["authorized"] = data.get("authorized", {}) or {}
            except (json.JSONDecodeError, IOError):
                pass

    def _save_access(self):
        try:
            with open(ACCESS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.access, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def _gen_code(self, existing):
        for _ in range(200):
            code = "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN))
            if code not in existing:
                return code
        # extremely unlikely fallback: lengthen
        return "".join(secrets.choice(CODE_ALPHABET) for _ in range(CODE_LEN + 2))

    def _sync_codes(self):
        """Ensure each 'codes'-mode group has exactly codeCount codes, preserving
        already-claimed ones. Groups not in codes mode keep their codes parked (so
        toggling back doesn't wipe claims) but they're unused."""
        groups = self.config.get("groups", {})
        with self._lock:
            for gname, gcfg in groups.items():
                if gcfg.get("access") != "codes":
                    continue
                want = max(0, int(gcfg.get("codeCount", 0) or 0))
                lst = self.access["codes"].setdefault(gname, [])
                existing = {c["code"] for c in lst}
                if len(lst) < want:
                    for _ in range(want - len(lst)):
                        code = self._gen_code(existing)
                        existing.add(code)
                        lst.append({"code": code, "voter": None, "ts": None})
                elif len(lst) > want:
                    # drop unclaimed codes first; never remove a claimed seat
                    unclaimed = [i for i, c in enumerate(lst) if not c.get("voter")]
                    to_remove = len(lst) - want
                    for i in reversed(unclaimed[-to_remove:] if to_remove <= len(unclaimed) else unclaimed):
                        lst.pop(i)
            self._save_access()

    def regenerate_codes(self, group):
        """Wipe a group's codes + authorizations and mint fresh ones (old codes
        and their device bindings become invalid)."""
        groups = self.config.get("groups", {})
        gcfg = groups.get(group)
        if not gcfg:
            return {"ok": False, "error": "unknown_group"}
        want = max(0, int(gcfg.get("codeCount", 0) or 0))
        with self._lock:
            existing = set()
            lst = []
            for _ in range(want):
                code = self._gen_code(existing)
                existing.add(code)
                lst.append({"code": code, "voter": None, "ts": None})
            self.access["codes"][group] = lst
            # clear authorizations gained via the old codes
            self.access["authorized"][group] = []
            self._save_access()
        return {"ok": True, "count": want}

    def get_access_codes(self):
        """Admin view: per-group access mode + codes (claimed flag, no voter ids)
        + seat usage counters."""
        groups = self.config.get("groups", {})
        out = {}
        with self._lock:
            for gname, gcfg in groups.items():
                access = gcfg.get("access", "open")
                codes = [{"code": c["code"], "claimed": bool(c.get("voter"))}
                         for c in self.access["codes"].get(gname, [])]
                authorized = list(self.access["authorized"].get(gname, []))
                voter_count = len({v["voter"] for v in self.votes
                                   if v["group"] == gname and v.get("voter")})
                if access == "codes":
                    seats = len(codes)
                    used = sum(1 for c in codes if c["claimed"])
                elif access == "pin":
                    seats = int(gcfg.get("limit", 0) or 0)
                    used = len(authorized)
                else:  # open
                    limit = int(gcfg.get("limit", 0) or 0)
                    seats = limit
                    # limitli open: koltuk = rezerve edilmiş giriş; limitsiz: katılım
                    used = len(authorized) if limit > 0 else voter_count
                out[gname] = {"access": access, "codes": codes,
                              "seats": seats, "used": used,
                              "limit": int(gcfg.get("limit", 0) or 0)}
        return out

    def _group_voter_count(self, group):
        return len({v["voter"] for v in self.votes if v["group"] == group and v.get("voter")})

    def _is_authed(self, group, voter):
        """Has this voter passed the gate for the group? Unlimited open groups
        need no gate; open groups WITH a capacity limit require a reserved seat
        (auto-admitted on first contact via _admit_open)."""
        gcfg = self.config.get("groups", {}).get(group, {})
        access = gcfg.get("access", "open")
        if access == "open" and int(gcfg.get("limit", 0) or 0) <= 0:
            return True
        return voter in self.access["authorized"].get(group, [])

    def _admit_open(self, group, voter):
        """Open-access seat reservation. For an open group WITH a capacity limit,
        reserve a seat for this voter on first contact (auto-admit, no PIN/code).
        Returns True if the voter holds/gets a seat, False if capacity is full.
        No-op (always True) for unlimited-open and for pin/codes groups."""
        gcfg = self.config.get("groups", {}).get(group, {})
        if gcfg.get("access", "open") != "open":
            return True  # pin/codes have their own gate
        limit = int(gcfg.get("limit", 0) or 0)
        if limit <= 0:
            return True  # unlimited
        if not voter:
            return False
        with self._lock:
            authd = self.access["authorized"].setdefault(group, [])
            if voter in authd:
                return True
            if len(authd) >= limit:
                return False
            authd.append(voter)
            self._state_ver += 1   # seat count changed → voter ETags refresh
            self._save_access()
            return True

    def _seat_full(self, group, voter):
        """True if a NOT-yet-admitted voter cannot get a seat (capacity reached).
        Already-admitted voters are never 'full'. For open+limit and pin, a seat
        is a reserved admission; codes handle capacity at claim time."""
        gcfg = self.config.get("groups", {}).get(group, {})
        access = gcfg.get("access", "open")
        if access == "codes":
            return False  # codes themselves are the seats; handled at claim time
        limit = int(gcfg.get("limit", 0) or 0)
        if limit <= 0:
            return False
        # pin and open(with limit): seat == reserved admission
        authd = self.access["authorized"].get(group, [])
        return (voter not in authd) and (len(authd) >= limit)

    def _rate_ok(self, key):
        """Per-key request throttle (key = voterId, IP'ye düşülebilir). voterId
        kullanmak funnel arkasında şarttır: orada tüm seyirci tek IP görünür, IP
        anahtarı 460 kişiyi tek kotaya sıkıştırırdı. voterId her cihaza kendi
        kotasını verir. Tek-oy garantisi bu değil, oy upsert'idir."""
        rl = self.config.get("rateLimit", {})
        if not rl or not rl.get("enabled", True):
            return True
        if not key:
            return True
        window = float(rl.get("windowSec", 10))
        max_hits = int(rl.get("max", 8))
        now = time.time()
        with self._lock:
            hits = [t for t in self._rate.get(key, []) if now - t < window]
            if len(hits) >= max_hits:
                self._rate[key] = hits
                return False
            hits.append(now)
            self._rate[key] = hits
        return True

    def claim_access(self, group, voter, code=None, pin=None):
        """Gate entry for pin/codes groups. Returns {ok} or {ok:False, error}."""
        gcfg = self.config.get("groups", {}).get(group, {})
        access = gcfg.get("access", "open")
        if access == "open":
            return {"ok": True}
        if not voter:
            return {"ok": False, "error": "missing_voter"}
        with self._lock:
            authd = self.access["authorized"].setdefault(group, [])
            if voter in authd:
                return {"ok": True}  # idempotent
            if access == "pin":
                want = str(gcfg.get("pin", "") or "")
                got = str(pin or "")
                if not want or not secrets.compare_digest(got, want):
                    return {"ok": False, "error": "bad_pin"}
                limit = int(gcfg.get("limit", 0) or 0)
                if limit > 0 and len(authd) >= limit:
                    return {"ok": False, "error": "full"}
                authd.append(voter)
                self._save_access()
                return {"ok": True}
            if access == "codes":
                got = str(code or "").strip().upper()
                if not got:
                    return {"ok": False, "error": "bad_code"}
                lst = self.access["codes"].setdefault(group, [])
                match = next((c for c in lst if c["code"] == got), None)
                if match is None:
                    return {"ok": False, "error": "bad_code"}
                if match.get("voter") and match["voter"] != voter:
                    return {"ok": False, "error": "code_used"}
                match["voter"] = voter
                match["ts"] = time.time()
                if voter not in authd:
                    authd.append(voter)
                self._save_access()
                return {"ok": True}
        return {"ok": False, "error": "bad_request"}

    def _create_handler(self):
        server = self
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass

            def _send_json(self, data, status=200, etag=None, poll_ms=None):
                body = json.dumps(data, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Expose-Headers", "ETag, X-Poll-Ms")
                if etag:
                    self.send_header("ETag", etag)
                if poll_ms:
                    self.send_header("X-Poll-Ms", str(poll_ms))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_304(self, etag, poll_ms=None):
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Expose-Headers", "ETag, X-Poll-Ms")
                if poll_ms:
                    self.send_header("X-Poll-Ms", str(poll_ms))
                self.send_header("Content-Length", "0")
                self.end_headers()

            def _send_html(self, html_content, status=200):
                body = html_content.encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _send_404(self, msg="404 Not Found"):
                self.send_response(404)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(msg.encode("utf-8"))

            def do_OPTIONS(self):
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
                self.end_headers()

            def do_GET(self):
                parsed = urllib.parse.urlparse(self.path)
                path = parsed.path.rstrip("/")
                query = urllib.parse.parse_qs(parsed.query)

                if path == "" or path == "/":
                    self._send_html("""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Voting Server</title><style>body{background:#111;color:#eee;font-family:sans-serif;padding:2rem;max-width:600px;margin:auto}a{color:#00f2ff}li{margin:1rem 0}</style></head><body><h1>🎮 Oylama Sunucusu</h1><p>Bu sunucuya oy vermek için aşağıdaki bağlantıları kullanın:</p><ul><li><strong>Jüri:</strong> jüri bağlantısı</li><li><strong>Seyirci:</strong> seyirci bağlantısı</li><li><strong>Ekip:</strong> ekip bağlantısı</li></ul><p>Bağlantıları yöneticiden alın.</p></body></html>""")
                    return

                if path.startswith("/v/"):
                    token = path[3:]
                    with server._lock:
                        group = server.tokens.get(token)
                    if group is None:
                        self._send_404("Geçersiz bağlantı")
                        return
                    groups_config = server.config.get("groups", {})
                    grp_cfg = groups_config.get(group, {})
                    label = grp_cfg.get("label", group)
                    scale = server.config.get("scale", 10)
                    brand = server.brand or {}
                    jam_name = str(brand.get("jamName") or "JAMDECK")
                    html_page = (VOTER_PAGE
                                 .replace("__LABEL__", html.escape(label))
                                 .replace("__SCALE__", str(scale))
                                 .replace("__JAM__", html.escape(jam_name.upper()))
                                 .replace("/*__THEME__*/", theme_css(brand))
                                 .replace("__POLL_MS__", str(server._poll_ms()))
                                 .replace("/*__I18N__*/", voter_i18n_block(brand.get("language", "tr"))))
                    self._send_html(html_page)
                    return

                # Kod panosu: gruba paylaşılan tek link; kullanılan kodlar canlı düşer
                if path.startswith("/k/"):
                    token = path[3:]
                    with server._lock:
                        group = server.tokens.get(token)
                    if group is None:
                        self._send_404("Geçersiz bağlantı")
                        return
                    grp_cfg = server.config.get("groups", {}).get(group, {})
                    label = grp_cfg.get("label", group)
                    brand = server.brand or {}
                    jam_name = str(brand.get("jamName") or "JAMDECK")
                    html_page = (CODES_PAGE
                                 .replace("__LABEL__", html.escape(label))
                                 .replace("__JAM__", html.escape(jam_name.upper()))
                                 .replace("/*__THEME__*/", theme_css(brand))
                                 .replace("__POLL_MS__", str(server._poll_ms()))
                                 .replace("/*__I18N__*/", voter_i18n_block(brand.get("language", "tr"))))
                    self._send_html(html_page)
                    return

                if path == "/api/codes":
                    tokens = query.get("t", [])
                    if not tokens:
                        self._send_json({"ok": False}, 403)
                        return
                    with server._lock:
                        group = server.tokens.get(tokens[0])
                    if group is None:
                        self._send_json({"ok": False}, 403)
                        return
                    grp_cfg = server.config.get("groups", {}).get(group, {})
                    access = grp_cfg.get("access", "open")
                    with server._lock:
                        codes = [{"code": c["code"], "claimed": bool(c.get("voter"))}
                                 for c in server.access["codes"].get(group, [])]
                    self._send_json({
                        "ok": True,
                        "label": grp_cfg.get("label", group),
                        "access": access,
                        "codes": codes if access == "codes" else [],
                    })
                    return

                if path == "/api/current":
                    tokens = query.get("t", [])
                    if not tokens:
                        self._send_json({"ok": False}, 403)
                        return
                    token = tokens[0]
                    with server._lock:
                        group = server.tokens.get(token)
                    if group is None:
                        self._send_json({"ok": False}, 403)
                        return
                    groups_config = server.config.get("groups", {})
                    grp_cfg = groups_config.get(group, {})
                    enabled = grp_cfg.get("enabled", True)
                    label = grp_cfg.get("label", group)
                    scale = server.config.get("scale", 10)
                    access = grp_cfg.get("access", "open")
                    voter = (query.get("voter") or [None])[0]
                    if voter:
                        server._seen[voter] = time.time()   # dinamik poll: aktif kişi sayacı
                        server._admit_open(group, voter)    # open+limit: ilk temasta koltuk rezerve et
                    pms = server._poll_ms()                  # bu yanıttaki önerilen poll aralığı
                    authed = server._is_authed(group, voter) if voter else (access == "open")
                    full = server._seat_full(group, voter) if voter else False
                    # ETag: durum değişmediyse (oylama sürerken) 304 → sunucu neredeyse sıfır iş yapar
                    etag = '"%d-%s-%d-%d"' % (server._state_ver, group, 1 if authed else 0, 1 if full else 0)
                    if self.headers.get("If-None-Match") == etag:
                        self._send_304(etag, poll_ms=pms)
                        return
                    game_data = None
                    with server._lock:
                        cg = server.current_game
                    if cg:
                        game_data = {"id": cg["id"], "name": cg["name"]}
                        if cg.get("cover"):
                            game_data["cover"] = cg["cover"]
                    cats = [{"id": c["id"], "label": c["label"]}
                            for c in server.config.get("categories", [])
                            if c.get("enabled", True)]
                    with server._lock:
                        games_list = [{"id": gid, "name": server.launched_games[gid]}
                                      for gid in server.launched_order]
                    self._send_json({
                        "ok": True,
                        "group": group,
                        "label": label,
                        "scale": scale,
                        "categories": cats,
                        "game": game_data,
                        "games": games_list,
                        "current": cg["id"] if cg else None,
                        "enabled": enabled,
                        "access": access,
                        "authed": authed,
                        "full": full,
                    }, etag=etag, poll_ms=pms)
                    return

                if path == "/api/results":
                    tokens = query.get("t", [])
                    if not tokens or tokens[0] != server.admin_token:
                        self._send_json({"ok": False}, 403)
                        return
                    results = server.get_results()
                    self._send_json(results)
                    return

                self._send_404()

            def _read_json(self):
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8")
                return json.loads(body)

            def _client_ip(self):
                return self.client_address[0] if self.client_address else "?"

            def do_POST(self):
                parsed = urllib.parse.urlparse(self.path)
                path = parsed.path.rstrip("/")

                if path == "/api/access":
                    try:
                        data = self._read_json()
                    except json.JSONDecodeError:
                        self._send_json({"ok": False, "error": "invalid json"}, 400)
                        return
                    # rate limit: voterId başına (funnel arkasında herkes tek IP
                    # görünür → IP işe yaramaz; voterId her modda gerçek kimlik).
                    # voterId yoksa IP'ye düş (savunma amaçlı yedek).
                    if not server._rate_ok(data.get("voter") or self._client_ip()):
                        self._send_json({"ok": False, "error": "rate"}, 429)
                        return
                    token = data.get("t")
                    with server._lock:
                        group = server.tokens.get(token) if token else None
                    if group is None:
                        self._send_json({"ok": False, "error": "invalid token"}, 403)
                        return
                    grp_cfg = server.config.get("groups", {}).get(group, {})
                    if not grp_cfg.get("enabled", True):
                        self._send_json({"ok": False, "error": "group disabled"}, 403)
                        return
                    res = server.claim_access(group, data.get("voter"),
                                              code=data.get("code"), pin=data.get("pin"))
                    # 200 even for ok:false — a mistyped code/PIN is normal voter
                    # flow, not an HTTP error (the body carries ok/error). Avoids
                    # console-error noise on the phone.
                    self._send_json(res)
                    return

                if path == "/api/vote":
                    try:
                        data = self._read_json()
                    except json.JSONDecodeError:
                        self._send_json({"ok": False, "error": "invalid json"}, 400)
                        return
                    # rate limit: voterId başına (funnel = tek IP; voterId gerçek
                    # kimlik). Tek-oy garantisi ZATEN upsert'te (grup,oyun,voter);
                    # bu yalnız tek cihazın istek selini/botu yavaşlatır.
                    if not server._rate_ok(data.get("voter") or self._client_ip()):
                        self._send_json({"ok": False, "error": "rate"}, 429)
                        return
                    token = data.get("t")
                    if not token:
                        self._send_json({"ok": False, "error": "missing token"}, 400)
                        return
                    with server._lock:
                        group = server.tokens.get(token)
                    if group is None:
                        self._send_json({"ok": False, "error": "invalid token"}, 403)
                        return
                    groups_config = server.config.get("groups", {})
                    grp_cfg = groups_config.get(group, {})
                    if not grp_cfg.get("enabled", True):
                        self._send_json({"ok": False, "error": "group disabled"}, 403)
                        return
                    game_id = data.get("game_id")
                    scores = data.get("scores")
                    voter = data.get("voter")
                    if not game_id or not voter or not isinstance(scores, dict) or not scores:
                        self._send_json({"ok": False, "error": "missing fields"}, 400)
                        return
                    # open-access capacity: auto-reserve a seat on first contact
                    # (a direct POST without a prior /api/current still gets gated)
                    if not server._admit_open(group, voter):
                        self._send_json({"ok": False, "error": "full"}, 403)
                        return
                    # Faz 2 gate: pin/codes groups require prior /api/access authorization
                    if not server._is_authed(group, voter):
                        self._send_json({"ok": False, "error": "need_access"}, 403)
                        return
                    # capacity (pin): reject a brand-new voter once seats are full
                    if server._seat_full(group, voter):
                        self._send_json({"ok": False, "error": "full"}, 403)
                        return
                    scale = server.config.get("scale", 10)
                    valid_cats = {c["id"] for c in server.config.get("categories", [])
                                  if c.get("enabled", True)}
                    clean = {}
                    for cid, sc in scores.items():
                        if cid not in valid_cats:
                            continue
                        try:
                            sc = int(sc)
                        except (TypeError, ValueError):
                            self._send_json({"ok": False, "error": "invalid score"}, 400)
                            return
                        if not (1 <= sc <= scale):
                            self._send_json({"ok": False, "error": "invalid score"}, 400)
                            return
                        clean[cid] = sc
                    if not clean:
                        self._send_json({"ok": False, "error": "no valid scores"}, 400)
                        return
                    with server._lock:
                        launched = dict(server.launched_games)
                    if game_id not in launched:
                        self._send_json({"ok": False, "error": "unknown_game"}, 409)
                        return
                    game_name = launched[game_id]
                    with server._lock:
                        # upsert by (group, game_id, voter) — O(1) index ile
                        key = (group, game_id, voter)
                        found = server._vote_index.get(key)
                        if found is not None and found < len(server.votes) \
                                and server.votes[found].get("voter") == voter:
                            server.votes[found]["scores"] = clean
                            server.votes[found]["ts"] = time.time()
                        else:
                            server._vote_index[key] = len(server.votes)
                            server.votes.append({
                                "group": group,
                                "game_id": game_id,
                                "game_name": game_name,
                                "scores": clean,
                                "voter": voter,
                                "ts": time.time()
                            })
                        server._dirty = True   # diske yazma flusher thread'e bırakılır
                    self._send_json({"ok": True})
                    return

                self._send_404()

        return Handler
