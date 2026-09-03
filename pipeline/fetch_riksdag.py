#!/usr/bin/env python3
"""Fetch document metadata from the Swedish Parliament's open data.

Five document types are used:
  prop  government bills                 - what the government proposed
  bet   committee reports                - carry the decision (beslutsdag)
  rir   National Audit Office audits     - independent evaluation
  sou   public inquiries                 - background and evaluation
  rfr   parliamentary reports            - the committees' own follow-ups

Only metadata is fetched (title, date, reference, link). No full text and no
interpretation - the per-measure selection happens in causes.py, driven by
config/causes.json.

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

import json, os, sys, time, datetime as dt, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "cache_rd")
os.makedirs(CACHE, exist_ok=True)
API = "https://data.riksdagen.se/dokumentlista/"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126 Safari/537.36")
DOKTYP = ["prop", "bet", "rir", "sou", "rfr"]
FROM, TOM = "2009-01-01", "2026-12-31"
LOG = []

# notis and notisrubrik are excluded: an OCR reading of the front page, 8 of
# 13 MB, never read by anything.
KEEP = ["dok_id", "doktyp", "subtyp", "beteckning", "nummer", "rm", "titel",
        "undertitel", "datum", "beslutsdag", "organ", "dokument_url_html"]


def _url(doktyp, frm, tom, sz=500):
    q = urllib.parse.urlencode({"doktyp": doktyp, "from": frm, "tom": tom,
                                "sz": sz, "utformat": "json",
                                "sort": "datum", "sortorder": "asc"})
    return API + "?" + q


def _get(url):
    key = str(abs(hash(url)) % (10 ** 16)) + ".json"
    path = os.path.join(CACHE, key)
    if os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for försök in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(r.read().decode("utf-8"))
            break
        except Exception as e:
            if försök == 3:
                raise
            time.sleep(2 * (försök + 1))
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(0.35)
    return d


def _split(frm, tom):
    a, b = dt.date.fromisoformat(frm), dt.date.fromisoformat(tom)
    mid = a + (b - a) // 2
    return (frm, mid.isoformat()), ((mid + dt.timedelta(days=1)).isoformat(), tom)


def hämta(doktyp, frm=FROM, tom=TOM, djup=0):
    """Split the window in half when hits exceed one page - the API does not
    paginate reliably at sz=500."""
    url = _url(doktyp, frm, tom)
    d = _get(url)["dokumentlista"]
    n = int(d.get("@traffar") or 0)
    docs = d.get("dokument") or []
    if isinstance(docs, dict):
        docs = [docs]
    if n > len(docs) and djup < 12:
        (a1, b1), (a2, b2) = _split(frm, tom)
        return hämta(doktyp, a1, b1, djup + 1) + hämta(doktyp, a2, b2, djup + 1)
    LOG.append({"url": url, "doktyp": doktyp, "fran": frm, "till": tom, "n": len(docs)})
    return docs


def main():
    ut = {}
    for t in DOKTYP:
        docs = hämta(t)
        rader = {}
        for x in docs:
            rader[x["dok_id"]] = {k: x.get(k) for k in KEEP if x.get(k)}
        ut[t] = sorted(rader.values(), key=lambda r: (r.get("datum") or "", r["dok_id"]))
        span = (ut[t][0]["datum"][:10], ut[t][-1]["datum"][:10]) if ut[t] else ("-", "-")
        print(f"  {t:5s} n={len(ut[t]):5d}  {span[0]} .. {span[1]}")
    json.dump({"dokument": ut, "requests": LOG, "hamtad": dt.date.today().isoformat()},
              open(os.path.join(HERE, "data", "riksdag.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"  {sum(len(v) for v in ut.values())} dokument, {len(LOG)} anrop"
          f" -> data/riksdag.json")


if __name__ == "__main__":
    main()
