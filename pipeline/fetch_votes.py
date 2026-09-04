#!/usr/bin/env python3
"""Fetch how the parties voted on the committee reports the cause layer cites.

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

A committee report is decided point by point, and the party lines differ
between points - so every point that went to a division is recorded, with its
own heading, rather than one figure for the report. Points settled by
acclamation are recorded as such: no member called for a division.
"""
import html as H, json, os, re, sys, time, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache_rd", "votes")
os.makedirs(CACHE, exist_ok=True)
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
ROSTER = ["Ja", "Nej", "Avstår", "Frånvarande"]
LOG, FEL = [], []


def _get(url, suffix):
    key = re.sub(r"[^A-Za-z0-9_-]", "_", url)[-120:] + suffix
    path = os.path.join(CACHE, key)
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for försök in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                txt = r.read().decode("utf-8", "replace")
            break
        except Exception as e:
            if försök == 3:
                FEL.append(f"{url}: {e}")
                return ""
            time.sleep(2 * (försök + 1))
    open(path, "w", encoding="utf-8").write(txt)
    time.sleep(0.25)
    return txt


def punkter(dok_id):
    """The report's proposal points: heading, how it was decided, and the id of
    the division if there was one."""
    url = f"https://data.riksdagen.se/dokumentstatus/{urllib.parse.quote(dok_id)}.json"
    raw = _get(url, ".json")
    if not raw:
        return []
    try:
        d = json.loads(raw)["dokumentstatus"]
    except Exception as e:
        FEL.append(f"punkter {dok_id}: {e}")
        return []
    uf = (d.get("dokutskottsforslag") or {}).get("utskottsforslag")
    if not uf:
        return []
    uf = [uf] if isinstance(uf, dict) else uf
    LOG.append({"url": url, "dok_id": dok_id, "punkter": len(uf)})
    ut = []
    for x in uf:
        ut.append({"punkt": x.get("punkt"),
                   "rubrik": re.sub(r"\s+", " ", x.get("rubrik") or "").strip(),
                   "beslutstyp": x.get("beslutstyp"),
                   "votering_id": x.get("votering_id") or None,
                   "motforslag_partier": [p for p in re.findall(
                       r"[A-ZÅÄÖ]{1,2}", x.get("motforslag_partier") or "")]})
    return ut


def rostrakning(votering_id):
    """Per-party tallies, summed from the per-member list. The API's own
    gruppering=parti returns a single bogus row, so it is not used."""
    url = f"https://data.riksdagen.se/votering/{urllib.parse.quote(votering_id)}/html"
    raw = _get(url, ".html")
    if not raw:
        # Two divisions from 2011/12 answer 200 with an empty body. That is a gap
        # in the source, not a fetch error, but it must not pass unrecorded.
        FEL.append(f"votering {votering_id}: tomt svar från källan")
        return None
    celler = [H.unescape(re.sub(r"<[^>]+>", "", c)).strip()
              for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", raw, re.S)]
    celler = [c for c in celler if c]
    if len(celler) < 6 or celler[:3] != ["Namn", "Parti", "Röst"]:
        FEL.append(f"votering {votering_id}: oväntad tabell")
        return None
    per = {}
    for i in range(3, len(celler) - 2, 3):
        parti, rost = celler[i + 1], celler[i + 2]
        if rost not in ROSTER:
            continue
        per.setdefault(parti, dict.fromkeys(ROSTER, 0))[rost] += 1
    LOG.append({"url": url, "votering_id": votering_id, "partier": len(per)})
    return per or None


def linje(per_parti):
    """One party, one verdict: the vote the majority of its present members
    cast. Absentees are reported but never decide the line.

    A split is only recorded when it is a real one. A single member abstaining
    in a party of a hundred is not a divided party line, and flagging it would
    have marked 109 of 195 cases; the threshold is therefore at least three
    members and at least a tenth of those present. The speaker and members
    without a party sit under "-" and are not a party, so they are excluded.
    """
    ut = {}
    for parti, r in per_parti.items():
        if parti in ("-", ""):
            continue
        närvarande = {k: v for k, v in r.items() if k != "Frånvarande" and v}
        if not närvarande:
            ut[parti] = {"linje": "Frånvarande", "roster": r}
            continue
        linje = max(närvarande, key=närvarande.get)
        n = sum(närvarande.values())
        avvikande = n - närvarande[linje]
        post = {"linje": linje, "roster": r}
        if avvikande >= 3 and avvikande / n >= 0.10:
            post["avvikande"] = avvikande
            post["narvarande"] = n
        ut[parti] = post
    return ut


def main():
    C = json.load(open(os.path.join(HERE, "data", "causes.json"), encoding="utf-8"))
    bets = {}
    for m in C["matpunkter"].values():
        for d in m.get("beslut", []):
            if d.get("bet_id"):
                bets[d["bet_id"]] = d["bet_ref"]

    ut = {}
    for n, (dok_id, ref) in enumerate(sorted(bets.items()), 1):
        pts = punkter(dok_id)
        rader = []
        for p in pts:
            r = {"punkt": p["punkt"], "rubrik": p["rubrik"],
                 "beslutstyp": p["beslutstyp"], "motforslag": p["motforslag_partier"]}
            if p["beslutstyp"] == "röstning" and p["votering_id"]:
                per = rostrakning(p["votering_id"])
                if per:
                    r["partier"] = linje(per)
            rader.append(r)
        ut[dok_id] = {"ref": ref, "punkter": rader}
        röstade = sum(1 for r in rader if r.get("partier"))
        print(f"  [{n:3d}/{len(bets)}] {ref:22s} {len(rader):2d} punkter, "
              f"{röstade} med omröstning")

    json.dump({"betankanden": ut, "requests": LOG, "fel": FEL},
              open(os.path.join(HERE, "data", "votes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    npunkt = sum(len(v["punkter"]) for v in ut.values())
    nrost = sum(1 for v in ut.values() for r in v["punkter"] if r.get("partier"))
    print(f"  {len(ut)} betänkanden, {npunkt} punkter, {nrost} omröstningar, "
          f"{len(FEL)} fel -> data/votes.json")
    for e in FEL[:8]:
        print("   ! " + e)


if __name__ == "__main__":
    main()
