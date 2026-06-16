"""JamDeck sürümünün TEK kaynağı.

Yeni sürüm çıkarırken yalnız APP_VERSION değişir; arayüz (sidebar + Kurulum
güncelleme kartı) ve güncelleme denetimi bu değeri getAppInfo() üzerinden okur.
"""

APP_VERSION = "2.0.5"

# Güncellemelerin denetlendiği GitHub deposu — uygulamaya gömülü (UI'da görünmez).
UPDATE_REPO = "tarikyzco/JamDeck"


def parse_version(s):
    """'v2.1.0' / '2.1' → (2, 1, 0). Bozuk parçalar 0 sayılır."""
    s = str(s or "").strip()
    if s[:1] in ("v", "V"):
        s = s[1:]
    parts = []
    for p in s.split("."):
        try:
            parts.append(int(p))
        except ValueError:
            parts.append(0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def is_newer(latest, current):
    return parse_version(latest) > parse_version(current)
