"""Compare the parliamentary terms defined in config/periods.json.

Reads data/data.json and data/alt.json and writes data/analysis.json. Needs no
network, so it is free to re-run. The number of terms is governed entirely by
the configuration.

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

import json, os, re
import statistics as _st
import periods as PP

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
def load(n): return json.load(open(os.path.join(DATA, n), encoding="utf-8"))

D, A = load("data.json"), load("alt.json")
SHARED = (load("requests_scb.json").get("shared", [])
          if os.path.exists(os.path.join(DATA, "requests_scb.json")) else [])
META = json.load(open(os.path.join(HERE, "config", "content.json"), encoding="utf-8"))
SER = {i["key"]: i for i in D["indicators"]}
SER.update({i["key"]: i for i in A["indicators"]})

def in_period(freq, k, i): return PP.index_of(freq, k) == i
infer_freq, xval = PP.infer_freq, PP.xval

def ols(pts):
    n = len(pts)
    if n < 2: return None
    mx = sum(x for x, _ in pts)/n; my = sum(y for _, y in pts)/n
    den = sum((x-mx)**2 for x, _ in pts)
    return None if den == 0 else sum((x-mx)*(y-my) for x, y in pts)/den

def analyse(key):
    ind = SER[key]; mt = META[key]
    segs = ind.get("segments")
    def same_seg(k1, k2):
        if not segs or k1 is None or k2 is None: return True
        return any(k1 in s and k2 in s for s in segs)

    ser = {k: v for k, v in ind["series"].items() if isinstance(v, (int, float))}
    if not ser: return None
    keys = sorted(ser)
    freq = PP.infer_freq(keys)
    # Percentage points where one point is a sensible quantity: measures that
    # already are points, measures that can cross zero, and shares between 15
    # and 85 per cent. Relative change elsewhere - 0.3 points on a level of
    # seven per cent is a four per cent change, not a negligible one.
    _u = mt["unit"]
    _vals = [v for v in ind["series"].values() if isinstance(v, (int, float))]
    _med = _st.median(_vals) if _vals else 0
    _share = bool(re.search(r"procent|andel", _u, re.I))
    if re.search(r"procentenhet", _u, re.I):
        is_pp = True
    elif _vals and (min(_vals) <= 0 or max(_vals) * min(_vals) <= 0):
        is_pp = True
    else:
        is_pp = _share and 15 <= _med <= 85
    better = mt["better"]; dir_ = 1 if better == "up" else (-1 if better == "down" else 0)
    thr = PP.THR["niva_procentenheter"] if is_pp else PP.THR["niva_procent"]
    thr_t = PP.THR["takt_procentenheter"] if is_pp else PP.THR["takt_procent"]

    out = []
    for i in range(PP.N):
        obs = {k: v for k, v in ser.items() if PP.index_of(freq, k) == i}
        base = PP.base_key(freq, i, keys)
        ekey = max(obs) if obs else None
        skey = base if (base in ser and same_seg(base, ekey)) else None
        if skey is None and obs:
            cand = [k for k in sorted(obs) if same_seg(k, ekey)]
            skey = cand[0] if cand else None
        partial = skey != base
        broken = bool(segs) and base in ser and not same_seg(base, ekey)
        s, e = ser.get(skey), ser.get(ekey)
        raw = None
        if s is not None and e is not None and skey != ekey:
            raw = (e - s) if is_pp else ((e - s)/s*100 if s else None)
        pts = [(PP.xval(k, freq), v) for k, v in sorted(obs.items()) if same_seg(k, ekey)]
        sl = ols(pts); gain = None
        if sl is not None and dir_:
            lvl = sum(v for _, v in pts)/len(pts)
            gain = round(sl*dir_, 2) if is_pp else (round(sl/abs(lvl)*100*dir_, 2) if lvl else None)
        if raw is None: verd = "na"
        elif better == "neutral": verd = "neutral"
        elif abs(raw) < thr: verd = "flat"
        else: verd = "better" if ((raw > 0) == (better == "up")) else "worse"
        out.append({"label": PP.LABEL[i], "short": PP.SHORT[i], "from": skey, "to": ekey,
                    "start": s, "end": e, "raw": None if raw is None else round(raw, 2),
                    "avg": round(sum(obs.values())/len(obs), 4) if obs else None,
                    "n": len(obs), "partial": partial, "broken": broken,
                    "verdict": verd, "gain": gain, "slope_n": len(pts)})

    g_prev, g_last = (out[-2]["gain"], out[-1]["gain"]) if PP.N >= 2 else (None, None)
    shift = None if (g_prev is None or g_last is None) else round(g_last - g_prev, 2)
    if dir_ == 0 or shift is None: tkind = "neutral"
    elif abs(shift) < thr_t: tkind = "flat"
    else:
        eps = thr_t/2
        if g_prev <= -eps and g_last >= eps: tkind = "rev_up"
        elif g_prev >= eps and g_last <= -eps: tkind = "rev_down"
        elif g_prev > 0 and g_last > 0: tkind = "faster_better" if shift > 0 else "slower_better"
        elif g_prev < 0 and g_last < 0: tkind = "slower_worse" if shift > 0 else "faster_worse"
        else: tkind = "rev_up" if shift > 0 else "rev_down"
    return {"freq": freq, "is_pp": is_pp, "periods": out,
            "trend_shift": shift, "trend_kind": tkind,
            "latest": max(ser), "first": min(ser)}

OUT = []
for key in META:
    c = analyse(key)
    if c is None: continue
    OUT.append({**META[key], "key": key, "series": SER[key]["series"],
                "extra": SER[key].get("extra", {}), "kpi": SER[key].get("kpi"),
                "reqs": SER[key].get("reqs", []), "calc": c})

# All five summaries have known weaknesses, so all five are reported: if they
# agree, the conclusion holds.
import statistics as _st

BY = {i["key"]: i for i in OUT}

def _scale(ind):
    c = ind["calc"]
    ser = {k: v for k, v in ind["series"].items() if isinstance(v, (int, float))}
    ks = sorted(ser); ch = []
    for x, y in zip(ks, ks[1:]):
        dt = PP.xval(y, c["freq"]) - PP.xval(x, c["freq"])
        if dt <= 0: continue
        d = (ser[y] - ser[x]) if c["is_pp"] else \
            ((ser[y] - ser[x]) / ser[x] * 100 if ser[x] else None)
        if d is not None: ch.append(d / dt)
    if len(ch) < 3: return None
    med = _st.median(ch)
    mad = _st.median([abs(v - med) for v in ch]) * 1.4826
    return mad if mad > 1e-9 else (_st.pstdev(ch) or None)

for i in OUT:
    i["calc"]["vol"] = _scale(i)

VALUED = [k for k in BY if BY[k]["better"] != "neutral"]
def _balanced(span):
    return [k for k in VALUED
            if all(BY[k]["calc"]["periods"][i]["raw"] is not None for i in span)]
BALANCED = _balanced(range(PP.N))
BALANCED3 = _balanced(range(1, PP.N))

def _panel(keys):
    res = {"n_matpunkter": len(keys), "andel": [], "netto": [], "tecken": [],
           "z": [], "z_median": [], "rang": [], "n": [], "upp": [], "ned": []}
    for i in range(PP.N):
        av = [(k, BY[k]["calc"]["periods"][i]) for k in keys
              if BY[k]["calc"]["periods"][i]["raw"] is not None]
        up = sum(1 for _, p in av if p["verdict"] == "better")
        dn = sum(1 for _, p in av if p["verdict"] == "worse")
        sg = sum(1 for k, p in av
                 if p["raw"] * (1 if BY[k]["better"] == "up" else -1) > 0)
        zs = []
        for k in keys:
            p = BY[k]["calc"]["periods"][i]; s = BY[k]["calc"]["vol"]
            if p["gain"] is None or not s: continue
            zs.append(max(-3.0, min(3.0, p["gain"] / s)))
        n = len(av)
        res["n"].append(n); res["upp"].append(up); res["ned"].append(dn)
        res["andel"].append(round(up / n * 100, 1) if n else None)
        res["netto"].append(round((up - dn) / n * 100, 1) if n else None)
        res["tecken"].append(round(sg / n * 100, 1) if n else None)
        res["z"].append(round(_st.fmean(zs), 3) if zs else None)
        res["z_median"].append(round(_st.median(zs), 3) if zs else None)
    rk = {i: [] for i in range(PP.N)}
    for k in keys:
        av = [(i, p["gain"]) for i, p in enumerate(BY[k]["calc"]["periods"])
              if p["gain"] is not None]
        if len(av) < 3: continue
        for pos, (i, _) in enumerate(sorted(av, key=lambda x: x[1])):
            rk[i].append(pos / (len(av) - 1))
    res["rang"] = [round(_st.fmean(rk[i]), 3) if rk[i] else None for i in range(PP.N)]
    return res

AGG = {"alla": _panel(VALUED),
       "balanserad": _panel(BALANCED), "balanserad3": _panel(BALANCED3),
       "valued": len(VALUED),
       "balanced_keys": sorted(BALANCED), "balanced3_keys": sorted(BALANCED3),
       "balanced_names": sorted(BY[k]["name"] for k in BALANCED),
       "balanced3_names": sorted(BY[k]["name"] for k in BALANCED3),
       "span3_from": 1,
       "excluded_names": sorted(BY[k]["name"] for k in BY if BY[k]["better"] == "neutral")}

json.dump({"base_year": D["base_year"], "shared_reqs": SHARED, "aggregate": AGG,
           "indicators": OUT, "tables": D["tables"],
           "alt_sources": A["sources"], "periods": PP.LABEL, "periods_short": PP.SHORT,
           "period_meta": PP.PERIODS, "smoothing": PP.SMOOTH},
          open(os.path.join(DATA, "analysis.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

V = {"better": "bättre", "worse": "sämre", "flat": "oför.", "neutral": "–", "na": "saknas"}
print(f'{"mätpunkt":26s} ' + " ".join(f'{p:>16s}' for p in PP.SHORT) + "  takt")
print("-" * (28 + 17*PP.N + 8))
for i in sorted(OUT, key=lambda x: x["name"]):
    c = i["calc"]; cells = []
    for p in c["periods"]:
        if p["raw"] is None: cells.append(f'{"–":>16s}')
        else:
            u = "p.e." if c["is_pp"] else "%"
            cells.append(f'{p["raw"]:+7.1f} {u:4s} {V[p["verdict"]][:4]:>4s}')
    print(f'{i["name"][:26]:26s} ' + " ".join(cells) + f'  {c["trend_kind"]}')
