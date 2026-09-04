#!/usr/bin/env python3
"""Build the cause layer: link each measure to parliamentary documents.

Three kinds of claim are kept apart, because their evidential weight differs
entirely:

  DECISIONS   what parliament actually decided in the policy area, with date
              and reference. A verifiable fact - but a decision falling in the
              same term as a change is no evidence that it caused the change.
  AUDITS      what the National Audit Office, an inquiry or a committee found
              when they actually evaluated. This is where the evidence lives.
  CONTEXT     dated events outside politics that bear on the measure.

The selection is driven by config/causes.json. Nothing is fetched that is not
already in data/riksdag.json, and every entry carries its link to the source.

Part of mandatperioden - https://github.com/klahr/mandatperioden
Copyright (C) 2026 Joachim Klahr

This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your option)
any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
Public License for more details. You should have received a copy of the
License along with this program; see the file LICENSE or
<https://www.gnu.org/licenses/>.
"""

import html as H, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache_rd", "text")
os.makedirs(CACHE, exist_ok=True)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")

RD = json.load(open(os.path.join(HERE, "data", "riksdag.json"), encoding="utf-8"))
DOK = RD["dokument"]
CFG = json.load(open(os.path.join(HERE, "config", "causes.json"), encoding="utf-8"))
SHOCK = json.load(open(os.path.join(HERE, "config", "shocks.json"), encoding="utf-8"))
PERIODS = json.load(open(os.path.join(HERE, "config", "periods.json"), encoding="utf-8"))["periods"]

ALLA = [d for t in DOK for d in DOK[t]]
BY_ID = {d["dok_id"]: d for d in ALLA}
FEL = []


# data.riksdagen.se serves the raw document body with no navigation at all, so a
# reader who lands there cannot get to the committee report or the votes. The
# public page carries "Ärendets gång" and links onward.
SLUG = {"prop": "proposition", "bet": "betankande", "rir": "granskningsrapport",
        "sou": "statens-offentliga-utredningar", "rfr": "rapport-fran-riksdagen"}


def länk(d):
    slug = SLUG.get(d["doktyp"])
    if slug:
        return ("https://www.riksdagen.se/sv/dokument-och-lagar/dokument/"
                f"{slug}/_{d['dok_id']}/")
    return f"https://data.riksdagen.se/dokument/{d['dok_id']}"


_BET_BY_TITLE = {}
for _b in DOK.get("bet", []):
    _BET_BY_TITLE.setdefault(_b["titel"].strip().lower(), []).append(_b)


def betankande(d):
    """The committee report that handled a bill, matched on identical title
    within a year. The votes live on that page; the bill's own page does not
    have them. Ambiguous matches are dropped - a wrong citation is worse than
    none, so 217 of 305 bills get a link and the rest do not."""
    if d["doktyp"] != "prop":
        return None
    år = int(d["datum"][:4])
    kand = [b for b in _BET_BY_TITLE.get(d["titel"].strip().lower(), [])
            if abs(int(b["datum"][:4]) - år) <= 1]
    return kand[0] if len(kand) == 1 else None


def beteckning(d):
    t, rm, nr = d["doktyp"], d.get("rm") or "", d.get("beteckning") or ""
    if t == "prop":
        return f"prop. {rm}:{nr}"
    if t == "bet":
        return f"bet. {rm}:{d.get('beteckning') or nr}"
    if t == "rir":
        return f"RiR {rm}:{nr}"
    if t == "sou":
        return f"SOU {rm}:{nr}"
    if t == "rfr":
        return f"RFR {rm}:{nr}"
    return f"{t} {rm}:{nr}"


def period_index(datum):
    for i, p in enumerate(PERIODS):
        if p["start"] <= datum[:10] <= p["slut"]:
            return i
    return None


def träffar(spec, redan=()):
    pat = re.compile(spec["re"], re.I)
    neg = re.compile(spec["inte"], re.I) if spec.get("inte") else None
    typer = spec.get("doktyp") or ["prop"]
    ut = []
    for t in typer:
        for d in DOK.get(t, []):
            txt = d["titel"] + " " + (d.get("undertitel") or "")
            if not pat.search(txt) or (neg and neg.search(txt)):
                continue
            if d["dok_id"] in redan:
                continue
            if spec.get("fran") and d["datum"][:10] < spec["fran"]:
                continue
            ut.append(d)
    prio = re.compile(spec["prioritera"], re.I) if spec.get("prioritera") else None
    ut.sort(key=lambda d: (bool(prio and prio.search(d["titel"])), d["datum"]),
            reverse=True)
    if spec.get("per_period") is None:
        return ut[: spec.get("max", 8)]
    per_period = spec["per_period"]
    tak = per_period * len(PERIODS)
    # Without this nearly everything lands in the most recent term, since the
    # sort is newest first.
    hinkar, kvar = {}, []
    for d in ut:
        i = period_index(d["datum"])
        if i is None:
            continue
        if len(hinkar.setdefault(i, [])) < per_period:
            hinkar[i].append(d)
        else:
            kvar.append(d)
    valda = [d for i in sorted(hinkar) for d in hinkar[i]]
    valda.sort(key=lambda d: d["datum"], reverse=True)
    return valda[:tak]


def _prosa_score(s):
    """A contents list is full of short lines and page numbers; prose is not."""
    rader = [r.strip() for r in s.split("\n") if r.strip()]
    if not rader:
        return 0
    siffror = sum(1 for r in rader if re.fullmatch(r"[\d.,\s]+", r))
    return (sum(len(r) for r in rader) / len(rader)) - 12 * (siffror / len(rader)) * 4


def fulltext(dok_id):
    p = os.path.join(CACHE, dok_id + ".txt")
    if os.path.exists(p):
        return open(p, encoding="utf-8").read()
    u = f"https://data.riksdagen.se/dokumentstatus/{dok_id}.json"
    try:
        req = urllib.request.Request(u, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.loads(r.read().decode("utf-8"))
        raw = (d["dokumentstatus"]["dokument"].get("html") or "")
    except Exception as e:
        FEL.append(f"fulltext {dok_id}: {e}")
        raw = ""
    txt = H.unescape(re.sub(r"<[^>]+>", "\n", raw))
    txt = re.sub(r"[ \t\xa0]+", " ", txt)
    txt = re.sub(r"\n\s*\n+", "\n", txt).strip()
    open(p, "w", encoding="utf-8").write(txt)
    time.sleep(0.3)
    return txt


def sammanfattning(dok_id, tecken=700):
    txt = fulltext(dok_id)
    if not txt:
        return None
    bäst, bästpoäng = None, -1e9
    rubrik = re.compile(r"(?:^|\n)\s*(?:\d[\d.]*\s*)?(?:Sammanfattning"
                        r"(?: och rekommendationer)?|Riksrevisionens slutsatser"
                        r"|Slutsatser och rekommendationer)\s*(?:\n|$)")
    for m in rubrik.finditer(txt):
        block = txt[m.end(): m.end() + 2600]
        s = _prosa_score(block)
        if s > bästpoäng:
            bäst, bästpoäng = block, s
    if bäst is None or bästpoäng < 25:
        return None
    bäst = re.sub(r"\s+", " ", bäst.replace("\n", " ")).strip()
    bäst = re.sub(r"^(?:[\d.,\s]+|[a-zåäö]\S*\s+)", "", bäst, count=1).strip()
    if not bäst[:1].isupper():
        return None
    if len(bäst) > tecken:
        klipp = bäst[:tecken]
        p = max(klipp.rfind(". "), klipp.rfind(".”"))
        bäst = (klipp[: p + 1] if p > tecken * 0.5 else klipp.rstrip() + "…")
    return bäst or None


def dok_ut(d, med_sammanfattning=False):
    r = {"id": d["dok_id"], "typ": d["doktyp"], "ref": beteckning(d),
         "titel": re.sub(r"\s+", " ", d["titel"]).strip(),
         "datum": d["datum"][:10], "url": länk(d), "period": period_index(d["datum"])}
    if d.get("beslutsdag"):
        r["beslutsdag"] = d["beslutsdag"][:10]
    b = betankande(d)
    if b:
        r["bet_id"] = b["dok_id"]
        r["bet_rm"] = b.get("rm")
        r["bet_bet"] = b.get("beteckning")
        r["bet_ref"] = beteckning(b)
        r["bet_url"] = länk(b)
    if med_sammanfattning:
        s = sammanfattning(d["dok_id"])
        if s:
            r["sammanfattning"] = s
    return r


def hitta_titel(titel):
    t = titel.lower().strip()
    for d in ALLA:
        if d["titel"].lower().strip().startswith(t):
            return d
    FEL.append(f"omvärldsankare saknas: {titel!r}")
    return None


def main():
    hämta_text = "--utan-text" not in sys.argv
    ut = {"matpunkter": {}, "omvarld": {}, "fel": []}

    for nyckel, s in SHOCK.items():
        rader = []
        for titel in s.get("ankare", []):
            d = hitta_titel(titel)
            if d:
                rader.append(dok_ut(d))
        ut["omvarld"][nyckel] = {**{k: v for k, v in s.items() if k != "ankare"},
                                 "dokument": sorted(rader, key=lambda r: r["datum"])}

    for key, c in CFG.items():
        post = {k: c[k] for k in ("mekanism", "tolkning") if c.get(k)}
        post["omvarld"] = c.get("omvarld", [])
        for f in ("beslut", "granskning"):
            if c.get(f):
                mt = f == "granskning" and hämta_text
                post[f] = [dok_ut(d, mt) for d in träffar(c[f])]
        if c.get("extra_ref"):
            post["extra_ref"] = c["extra_ref"]
        ut["matpunkter"][key] = post
        nb = len(post.get("beslut", []))
        ng = len(post.get("granskning", []))
        ns = sum(1 for g in post.get("granskning", []) if g.get("sammanfattning"))
        print(f"  {key:24s} beslut={nb:2d} granskning={ng:2d} (varav citat {ns})"
              f" omvärld={len(post['omvarld'])}")

    ut["fel"] = FEL
    json.dump(ut, open(os.path.join(HERE, "data", "causes.json"), "w",
                       encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  {len(ut['matpunkter'])} mätpunkter, {len(FEL)} fel -> data/causes.json")
    for e in FEL[:12]:
        print("   ! " + e)


if __name__ == "__main__":
    main()
