"""Translate parliamentary terms (dates in config/periods.json) into the period
keys the statistics themselves use. Adding a term requires no code change.

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

import json, os, datetime as dt

HERE = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(HERE, "config", "periods.json"), encoding="utf-8"))
PERIODS = CFG["periods"]
FREQ = CFG["frekvenser"]
SMOOTH = CFG["utjamning"]
THR = CFG["trosklar"]
N = len(PERIODS)
LABEL = [p["label"] for p in PERIODS]
SHORT = [p["kort"] for p in PERIODS]

def _d(s): return dt.date.fromisoformat(s)

def _q_add(y, q, k):
    t = (y * 4 + (q - 1)) + k
    return t // 4, t % 4 + 1
def _m_add(y, m, k):
    t = (y * 12 + (m - 1)) + k
    return t // 12, t % 12 + 1

def first_key(freq, start):
    d = _d(start); off = FREQ[freq].get("offset", 0)
    if freq == "Q":
        y, q = _q_add(d.year, (d.month - 1)//3 + 1, off); return f"{y}K{q}"
    if freq == "M":
        y, m = _m_add(d.year, d.month, off); return f"{y}M{m:02d}"
    if freq == "A":
        return str(d.year + off)
    if freq == "LA":
        y = d.year + off; return f"{y}/{str(y+1)[2:]}"
    raise ValueError(freq)

def prev_key(freq, key):
    if freq == "Q":
        y, q = key.split("K"); y, q = _q_add(int(y), int(q), -1); return f"{y}K{q}"
    if freq == "M":
        y, m = key.split("M"); y, m = _m_add(int(y), int(m), -1); return f"{y}M{m:02d}"
    if freq == "A":
        return str(int(key) - 1)
    if freq == "LA":
        y = int(key.split("/")[0]) - 1; return f"{y}/{str(y+1)[2:]}"
    raise ValueError(freq)

def _ulf_mid(key):
    """Midpoint of a ULF interval: "2010-2011" spans 2010-01 through 2011-12,
    so the midpoint is 2011-01, not 2010-07."""
    a, b = (key.split("-") + [key])[:2]
    lo, hi = int(a) * 12, (int(b) + 1) * 12
    mid = (lo + hi) // 2
    return dt.date(mid // 12, mid % 12 + 1, 1)

def index_of(freq, key):
    if freq == "ULF":
        mid = _ulf_mid(key)
        for i, p in enumerate(PERIODS):
            if _d(p["start"]) <= mid <= _d(p["slut"]): return i
        return None
    for i, p in enumerate(PERIODS):
        lo = first_key(freq, p["start"])
        hi = prev_key(freq, first_key(freq, PERIODS[i+1]["start"])) if i + 1 < N else None
        if key >= lo and (hi is None or key <= hi):
            return i
    return None

def base_key(freq, i, keys_present):
    if freq == "ULF":
        inside = [k for k in keys_present if index_of(freq, k) == i]
        if not inside: return None
        earlier = [k for k in keys_present if _ulf_mid(k) < _ulf_mid(min(inside))]
        return max(earlier) if earlier else None
    k = first_key(freq, PERIODS[i]["start"])
    for _ in range(FREQ[freq].get("nollpunkt_offset", 1)):
        k = prev_key(freq, k)
    return k

def window(freq, keys_present, i):
    return [k for k in keys_present if index_of(freq, k) == i]

def infer_freq(keys):
    k = keys[0]
    if "K" in k: return "Q"
    if "M" in k: return "M"
    if "/" in k: return "LA"
    if "-" in k: return "ULF"
    return "A"

def xval(k, freq):
    if freq == "Q": y, q = k.split("K"); return int(y) + (int(q)*3 - 1.5)/12
    if freq == "M": y, m = k.split("M"); return int(y) + (int(m) - 0.5)/12
    if freq == "LA": return int(k.split("/")[0]) + 0.75
    if freq == "ULF": a, b = (k.split("-") + [k])[:2]; return (int(a) + int(b))/2 + 0.5
    return int(k) + 0.5

if __name__ == "__main__":
    for f in ("Q", "M", "A", "LA"):
        print(f, "nollpunkt/första:",
              [(base_key(f, i, []), first_key(f, PERIODS[i]["start"])) for i in range(N)])
