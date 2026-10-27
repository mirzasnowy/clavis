"""Search an Android app by its NAME, not its package.

Usage: user says "buka Netflix" / "buka WhatsApp" — no package needed.
Search order:
1. Known alias map (most common apps, phone + TV variants).
2. Exact package / exact suffix match.
3. Suffix contains query.
4. Fuzzy (difflib) on the package suffix.
Returns ranked candidates with a score + reason, so the caller can
confirm before launching when the match is ambiguous (score < 90
or top-2 scores are close).

Package labels: Android does not give a human label from `pm list`
alone. The label is resolved by: known map first, then suffix
prettified (com.netflix.ninja -> "Netflix Ninja"). On a real device
with aapt2, `aapt2 dump badging <apk>` gives the real label — that
is documented in docs, not required here.
"""
import difflib
import re

KNOWN_APPS = {
    # query -> [packages, ...] (first = preferred)
    "netflix": ["com.netflix.ninja", "com.netflix.mediaclient"],
    "youtube": ["com.google.android.youtube.tv", "com.google.android.youtube"],
    "whatsapp": ["com.whatsapp"],
    "spotify": ["com.spotify.music", "com.spotify.tv.android"],
    "chrome": ["com.android.chrome"],
    "gmail": ["com.google.android.gm"],
    "maps": ["com.google.android.apps.maps"],
    "instagram": ["com.instagram.android"],
    "tiktok": ["com.zhiliaoapp.musically", "com.ss.android.ugc.trill"],
    "telegram": ["org.telegram.messenger"],
    "disney": ["com.disney.disneyplus"],
    "prime video": ["com.amazon.avod.thirdpartyclient"],
    "drive": ["com.google.android.apps.docs"],
    "photos": ["com.google.android.apps.photos"],
    "facebook": ["com.facebook.katana"],
    "x": ["com.twitter.android"],
    "twitter": ["com.twitter.android"],
    "shopee": ["com.shopee.id"],
    "tokopedia": ["com.tokopedia.tkpd"],
    "gojek": ["com.gojek.app"],
    "grab": ["com.grabtaxi.passenger"],
    "dana": ["id.dana"],
    "ovo": ["ovo.id"],
    "gopay": ["com.gojek.gopay"],
    "bca mobile": ["com.bca"],
    "mobile legends": ["com.mobile.legends"],
    "pubg": ["com.tencent.ig"],
}


def _norm(s):
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def _suffix(pkg):
    return pkg.rsplit(".", 1)[-1]


def prettify(pkg):
    return _suffix(pkg).replace("_", " ").title()


def search(query, packages):
    """packages = list of package names from `pm list packages`."""
    q = query.strip().lower()
    nq = _norm(q)
    results = []
    # 1. known alias
    for pkg in KNOWN_APPS.get(q, []):
        if pkg in packages:
            results.append({"package": pkg, "score": 100, "reason": "known alias"})
    # 2-4. scan all packages
    for pkg in packages:
        if any(r["package"] == pkg for r in results):
            continue
        suf = _suffix(pkg)
        nsuf = _norm(suf)
        if pkg.lower() == q or nsuf == nq:
            results.append({"package": pkg, "score": 95, "reason": "exact suffix"})
        elif nq in nsuf or nsuf in nq:
            results.append({"package": pkg, "score": 85, "reason": "suffix contains query"})
        else:
            ratio = difflib.SequenceMatcher(None, nq, nsuf).ratio()
            if ratio >= 0.6:
                results.append({"package": pkg, "score": round(ratio * 80, 1),
                                "reason": f"fuzzy {ratio:.2f}"})
    results.sort(key=lambda r: -r["score"])
    for r in results:
        r["label_guess"] = prettify(r["package"])
    # Ambiguity flag: top score < 90, or top-2 within 5 points
    ambiguous = False
    if not results:
        ambiguous = True
    elif results[0]["score"] < 90:
        ambiguous = True
    elif len(results) > 1 and results[0]["score"] - results[1]["score"] < 5:
        ambiguous = True
    return {"query": query, "candidates": results[:5], "ambiguous": ambiguous,
            "best": results[0] if results else None}
