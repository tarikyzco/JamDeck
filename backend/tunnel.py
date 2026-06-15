"""İnternet üzerinden oylama — Cloudflare quick tunnel yönetimi.

Organizatörün makinesindeki yerel oylama sunucusunu (localhost:<port>) public bir
`https://*.trycloudflare.com` adresine açar. Böylece seyirci, aynı Wi-Fi'da olmadan
(mobil veriyle) QR okutup oy verebilir — voter tarafında HİÇBİR ekstra adım yok.

- `cloudflared` binary'si ilk kullanımda indirilip saklanır (kuruluma gömülü değil).
- Quick tunnel: hesap GEREKMEZ, anonim, HTTPS, ara uyarı sayfası YOK.
- Adres her oturumda değişir (geçici) — voter QR okuttuğu için bunu görmez.
"""
import os
import re
import sys
import json
import time
import threading
import subprocess
import urllib.request

# Resmi stabil doğrudan indirme bağlantısı (~18 MB)
CF_DOWNLOAD_URL = ("https://github.com/cloudflare/cloudflared/releases/latest/"
                   "download/cloudflared-windows-amd64.exe")

_URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def parse_tunnel_url(text):
    """cloudflared çıktısından trycloudflare adresini ayıkla (yoksa None)."""
    m = _URL_RE.search(text or "")
    return m.group(0) if m else None


def tools_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "JamDeck", "tools")
    os.makedirs(d, exist_ok=True)
    return d


def cloudflared_path():
    return os.path.join(tools_dir(), "cloudflared.exe")


def is_installed():
    p = cloudflared_path()
    # küçük/yarım indirilmiş dosyayı "kurulu" sayma
    return os.path.exists(p) and os.path.getsize(p) > 1_000_000


def ensure_cloudflared(progress_cb=None, timeout=60):
    """cloudflared yoksa indir + sakla; yolunu döndür. progress_cb(pct, mb, total_mb)."""
    p = cloudflared_path()
    if is_installed():
        return p
    tmp = p + ".part"
    req = urllib.request.Request(CF_DOWNLOAD_URL, headers={"User-Agent": "JamDeck"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress_cb:
                    pct = int(done * 100 / total) if total else -1
                    progress_cb(pct, round(done / 1048576, 1), round(total / 1048576, 1))
    os.replace(tmp, p)
    return p


class Tunnel:
    """Tek bir cloudflared quick tunnel süreci."""

    def __init__(self):
        self.proc = None
        self.url = None

    def start(self, local_port, timeout=40, _cmd=None):
        """Tüneli başlat ve public URL'yi döndür. _cmd test için komutu ezer."""
        if _cmd is None:
            if not is_installed():
                raise RuntimeError("cloudflared not installed")
            _cmd = [cloudflared_path(), "tunnel", "--no-autoupdate",
                    "--url", "http://localhost:%d" % int(local_port)]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        self.proc = subprocess.Popen(
            _cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8", errors="replace",
            creationflags=flags, bufsize=1)
        found = threading.Event()

        def reader():
            try:
                for line in self.proc.stdout:
                    if not self.url:
                        u = parse_tunnel_url(line)
                        if u:
                            self.url = u
                            found.set()
            except Exception:
                pass
            found.set()  # süreç bitti / pipe kapandı

        threading.Thread(target=reader, daemon=True).start()
        found.wait(timeout)
        if not self.url:
            self.stop()
            raise RuntimeError("tunnel URL not received (timeout)")
        return self.url

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        if self.proc is not None:
            try:
                self.proc.terminate()
                try:
                    self.proc.wait(timeout=5)
                except Exception:
                    self.proc.kill()
            except Exception:
                pass
            self.proc = None
        self.url = None
        return {"ok": True}


# ─────────────────────────────────────────────────────────────────────────────
# TAILSCALE FUNNEL — SABİT adres (https://makine.tailnet.ts.net), ücretsiz.
# Quick tunnel'dan farkı: adres ASLA değişmez (süreç yeniden başlasa bile),
# cloudflared gibi kopmaları kendi toparlar → "QR'ı bir kez bas, hiç değişmesin".
# Voter yine HİÇBİR şey kurmaz (Funnel herkese açık HTTPS); yalnız organizatör
# bir kez Tailscale kurar + giriş yapar + Funnel'ı etkinleştirir.
# ─────────────────────────────────────────────────────────────────────────────

TS_MSI_URL = "https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.msi"


def tailscale_path():
    cand = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                        "Tailscale", "tailscale.exe")
    if os.path.exists(cand):
        return cand
    return "tailscale"  # PATH'e güven


def ensure_tailscale(progress_cb=None, timeout=300):
    """Tailscale kurulu değilse resmi MSI'yi indir + SESSİZ kur (tek UAC onayı).
    Kurulum başarısızsa/iptal edilirse RuntimeError. progress_cb(pct) indirme yüzdesi."""
    if tailscale_state()["installed"]:
        return True
    msi = os.path.join(tools_dir(), "tailscale-setup.msi")
    tmp = msi + ".part"
    req = urllib.request.Request(TS_MSI_URL, headers={"User-Agent": "JamDeck"})
    with urllib.request.urlopen(req, timeout=60) as r:
        total = int(r.headers.get("Content-Length") or 0)
        done = 0
        with open(tmp, "wb") as f:
            while True:
                chunk = r.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                done += len(chunk)
                if progress_cb:
                    progress_cb(int(done * 100 / total) if total else -1)
    os.replace(tmp, msi)
    # yükseltilmiş sessiz kurulum — TEK UAC penceresi (sürücü+servis kurar)
    import ctypes
    rc = ctypes.windll.shell32.ShellExecuteW(
        None, "runas", "msiexec", '/i "%s" /qn /norestart' % msi, None, 0)
    if rc <= 32:
        raise RuntimeError("tailscale_install_declined")
    exe = os.path.join(os.environ.get("ProgramFiles", r"C:\Program Files"),
                       "Tailscale", "tailscale.exe")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(2)
        if os.path.exists(exe):
            time.sleep(3)  # servisin ayağa kalkması için pay
            return True
    raise RuntimeError("tailscale_install_timeout")


def tailscale_up():
    """Giriş akışını tetikle (Tailscale tarayıcıda oturum açtırır). Engellemez."""
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen([tailscale_path(), "up"], creationflags=flags,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _run_ts(args, timeout=20):
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return subprocess.run([tailscale_path()] + args, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=timeout,
                          creationflags=flags)


def tailscale_state():
    """Tailscale durumu: {installed, loggedIn, url, nodeId}. url = sabit https://...ts.net."""
    out = {"installed": False, "loggedIn": False, "url": None, "nodeId": None, "msg": ""}
    try:
        r = _run_ts(["status", "--json"])
    except FileNotFoundError:
        out["msg"] = "not_installed"
        return out
    except Exception as e:
        out["msg"] = str(e)
        return out
    out["installed"] = True
    try:
        data = json.loads(r.stdout or "{}")
    except Exception:
        out["msg"] = "status_parse_error"
        return out
    state = data.get("BackendState")
    out["loggedIn"] = (state == "Running")
    self_node = data.get("Self") or {}
    dns = (self_node.get("DNSName") or "").rstrip(".")
    if dns:
        out["url"] = "https://" + dns
    out["nodeId"] = self_node.get("ID")
    if not out["loggedIn"]:
        out["msg"] = "not_logged_in"
    return out


def funnel_enable_url(node_id=None):
    """HTTPS + Funnel'ı tek akışta etkinleştiren resmi link (node id varsa node'a özel)."""
    if node_id:
        return "https://login.tailscale.com/f/funnel?node=" + str(node_id)
    return FUNNEL_ENABLE_DOCS


_LOGIN_URL_RE = re.compile(r"https://login\.tailscale\.com/\S+")
# Funnel/HTTPS etkin değil sinyalleri
_NOT_ENABLED_HINTS = ("login.tailscale.com", "is not enabled", "enable funnel",
                      "not allowed", "https is not enabled", "https must be enabled",
                      "funnel is not", "https certificates", "enablehttps", " enable ")
FUNNEL_ENABLE_DOCS = "https://tailscale.com/kb/1223/funnel"


class FunnelNotEnabled(RuntimeError):
    """Funnel/HTTPS tailnet'te etkin değil → kullanıcı bir kez konsoldan açmalı.
    enable_url: Tailscale'in verdiği gerçek etkinleştirme linki (yoksa docs)."""
    def __init__(self, enable_url="", detail=""):
        self.enable_url = enable_url or FUNNEL_ENABLE_DOCS
        self.detail = detail
        super().__init__("funnel_not_enabled")


def _tunlog(msg):
    try:
        with open(os.path.join(tools_dir(), "tunnel.log"), "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%d %H:%M:%S ") + str(msg) + "\n")
    except Exception:
        pass


def _extract_login_url(text):
    m = _LOGIN_URL_RE.search(text or "")
    return m.group(0).rstrip(".,)") if m else None


def _looks_not_enabled(text):
    low = (text or "").lower()
    return any(h in low for h in _NOT_ENABLED_HINTS)


def _funnel_active(port):
    """Funnel bu porta açık mı? Önce `serve status --json` (yapısal, güvenilir),
    olmazsa `funnel status` metin sezgisi. (Aktif bool, ham çıktı) döner."""
    # 1) yapısal: serve status --json → AllowFunnel + Proxy hedefi
    try:
        r = _run_ts(["serve", "status", "--json"], timeout=12)
        raw = (r.stdout or "").strip()
        if raw.startswith("{"):
            data = json.loads(raw)
            allow = data.get("AllowFunnel") or {}
            funnel_on = any(bool(v) for v in allow.values())
            web = data.get("Web") or {}
            proxied = any(str(port) in str((h or {}).get("Proxy", ""))
                          for cfg in web.values()
                          for h in (cfg.get("Handlers") or {}).values())
            if funnel_on and proxied:
                return (True, raw[:400])
            return (False, raw[:400])
    except Exception:
        pass
    # 2) metin sezgisi (eski sürümler)
    try:
        r = _run_ts(["funnel", "status"], timeout=12)
    except Exception:
        return (False, "")
    out = ((r.stdout or "") + "\n" + (r.stderr or "")).strip()
    low = out.lower()
    active = (".ts.net" in low and ("https" in low or "funnel" in low) and str(port) in out)
    return (active, out)


def funnel_start(local_port, timeout=75):
    """Funnel'ı yerel porta yönlendir; SABİT public URL'yi döndür.

    Strateji (asılmaz + net hata): (1) `tailscale cert` ile HTTPS sertifikasını AÇIKÇA
    sağla — HTTPS/Funnel kapalıysa burada HIZLI + anlaşılır hata gelir, funnel komutu
    sertifika beklerken sonsuza dek asılmaz; (2) sertifika hazırsa `funnel --bg` arka
    planda fırlat; (3) `funnel status`'ı yoklayarak ayağa kalkmasını doğrula. Etkin
    değilse FunnelNotEnabled(enable_url) → çağıran ekranda linke yönlendirir."""
    port = int(local_port)
    st = tailscale_state()
    if not st["installed"]:
        raise RuntimeError("tailscale_not_installed")
    if not st["loggedIn"]:
        raise RuntimeError("tailscale_not_logged_in")
    if not st["url"]:
        raise RuntimeError("tailscale_no_hostname")
    dns = st["url"][len("https://"):]
    _tunlog("funnel_start port=%d dns=%s" % (port, dns))

    # (1) Sertifikayı açıkça sağla. Funnel HTTPS sertifikası olmadan ÇALIŞAMAZ; bu yüzden
    # cert başarısızsa (HTTPS/Funnel kapalı, hesap desteklemiyor vb.) HEMEN dur ve
    # kullanıcıyı etkinleştirme sayfasına yönlendir — 75 sn boşa pollama YOK.
    crt = os.path.join(tools_dir(), "ts.crt")
    key = os.path.join(tools_dir(), "ts.key")
    try:
        cr = _run_ts(["cert", "--cert-file", crt, "--key-file", key, dns], timeout=45)
        co = ((cr.stdout or "") + "\n" + (cr.stderr or "")).strip()
        _tunlog("cert rc=%s out=%s" % (cr.returncode, co.replace("\n", " ")[:400]))
        if cr.returncode != 0:
            # sertifika alınamadı → Funnel imkansız. Gerçek linki yakala, yoksa node'dan üret.
            url = _extract_login_url(co) or funnel_enable_url(st.get("nodeId"))
            raise FunnelNotEnabled(url, co[:400])
    except subprocess.TimeoutExpired:
        _tunlog("cert TIMEOUT 45s (HTTPS muhtemelen kapalı / ACME yavaş)")
        raise FunnelNotEnabled(funnel_enable_url(st.get("nodeId")),
                               "HTTPS sertifikası alınamadı (zaman aşımı)")

    # (2) Funnel'ı arka planda fırlat (bizi bloklamaz)
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    try:
        subprocess.Popen([tailscale_path(), "funnel", "--bg", str(port)],
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         creationflags=flags)
    except Exception as e:
        raise RuntimeError("funnel_start_failed: %s" % e)

    # (3) status yokla
    deadline = time.time() + timeout
    enable_url = None
    last = ""
    while time.time() < deadline:
        time.sleep(3)
        active, out = _funnel_active(port)
        if out:
            last = out
            _tunlog("status: " + out.replace("\n", " ")[:300])
        enable_url = enable_url or _extract_login_url(out)
        if active:
            _tunlog("ACTIVE " + st["url"])
            return st["url"]
        if enable_url or _looks_not_enabled(out):
            raise FunnelNotEnabled(enable_url or funnel_enable_url(st.get("nodeId")),
                                   (out or "").strip()[:400])
    # cert geçti ama funnel ayağa kalkmadı → yine etkinleştirme/izin sorunu olabilir
    raise FunnelNotEnabled(enable_url or funnel_enable_url(st.get("nodeId")),
                           "funnel_timeout: " + (last.strip()[:200] or "aktif funnel görünmedi"))


def funnel_stop(local_port=None):
    for args in (["funnel", "--bg", "off"], ["funnel", "reset"]):
        try:
            _run_ts(args, timeout=8)
            return {"ok": True}
        except Exception:
            continue
    return {"ok": True}
