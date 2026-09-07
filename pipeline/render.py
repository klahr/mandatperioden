"""Render the report as a standalone HTML page.

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

import json, html, re, os, datetime
from render_css import CSS
from render_js import JS

D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "analysis.json"), encoding="utf-8"))
IND = {i["key"]: i for i in D["indicators"]}
TABLES, ALTSRC = D["tables"], D["alt_sources"]
PLABEL = D["periods"]
PSHORT = D["periods_short"]
PMETA = D["period_meta"]
NP = len(PLABEL)
BASE = D["base_year"]
E = html.escape
HERE = os.path.dirname(os.path.abspath(__file__))

# Single hue, monotonic in lightness. Light mode never lighter than step 250,
# dark mode never darker than step 600.
RAMP = ["#86b6ef", "#6da7ec", "#5598e7", "#3987e5", "#2a78d6", "#256abf", "#1c5cab", "#184f95"]
def ramp(n, dark=False):
    if n == 1: idx = [len(RAMP) - 1]
    else: idx = [round(i * (len(RAMP) - 1) / (n - 1)) for i in range(n)]
    steps = [RAMP[i] for i in idx]
    return list(reversed(steps)) if dark else steps
def period_css():
    lo, dk = ramp(NP), ramp(NP, dark=True)
    def toks(steps, rgb, base):
        out = []
        for i, hexv in enumerate(steps):
            a = base + i * ((0.17 - base) / max(1, NP - 1))
            out.append(f"  --p{i+1}:{hexv}; --p{i+1}w:rgba({rgb},{a:.3f});")
        return "\n".join(out)
    nth = lambda sel: "\n".join(
        f"{sel}:nth-child({i+1}){{background:var(--p{i+1}w)}}" for i in range(NP))
    return {
        "/*PERIODCOLORS-LIGHT*/": f"  --np:{NP};\n" + toks(lo, "42,120,214", 0.05),
        "/*PERIODCOLORS-DARK-A*/": toks(dk, "57,135,229", 0.07),
        "/*PERIODCOLORS-DARK-B*/": toks(dk, "57,135,229", 0.07),
        "/*PERIODBAR-NTH*/": nth(".periodbar>div"),
        "/*FIGS-NTH*/": nth(".figs .f"),
        "/*DT-NTH*/": "\n".join(
            f"table.dt td.w{i+1}{{background:var(--p{i+1}w)}}" for i in range(NP)),
    }

DATESTR = datetime.date.today().isoformat()

def _load(n):
    fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", n)
    return json.load(open(fp, encoding="utf-8"))["requests"] if os.path.exists(fp) else []
REQ_SCB, REQ_ALT = _load("requests_scb.json"), _load("requests_alt.json")
SHARED_REQS = D.get("shared_reqs", [])
AGG = D.get("aggregate", {})

def sh(s):
    return "'" + str(s).replace("'", "'\\''") + "'"

def curl_block(ind):
    tabs = [t for t in (ind.get("tables") or []) if t in TABLES]
    reqs = list(ind.get("reqs") or [])
    # A measure sharing its fetch with the preceding one has no log entries of
    # its own; its source tables' calls are shown instead.
    if not reqs and ind.get("source", "SCB") == "SCB":
        reqs = [x for x in REQ_SCB if x["table"] in tabs]
    pc = "per 100 000 invånare" in ind["unit"] or "per invånare" in ind["unit"]
    for x in SHARED_REQS:
        pop = x["table"] in ("TAB5890", "TAB6667")
        if x["table"] in tabs or (pc and pop):
            reqs.append(x)
    seen, uniq = set(), []
    for x in reqs:
        sig = (x["method"], x["url"], json.dumps(x.get("body"), sort_keys=True))
        if sig in seen: continue
        seen.add(sig); uniq.append(x)
    reqs = uniq
    if not reqs: return ""

    def label(x):
        if x.get("table"):
            lab = TABLES.get(x["table"], {}).get("label", "")
            return f'{x["table"]} · {lab}'
        return x.get("note") or ""

    out = []
    for x in reqs:
        if x["method"] == "POST":
            body = json.dumps(x["body"], ensure_ascii=False, separators=(",", ":"))
            cmd = ("curl -s -X POST " + sh(x["url"]) + " \\\n"
                   "  -H 'Content-Type: application/json' \\\n"
                   "  -d " + sh(body))
        else:
            k = str(x.get("key") or "")
            cmd = "curl -sL " + sh(x["url"]) + (" -o " + k if k.endswith(".xlsx") else "")
        out.append(f'<div class="creq"><span class="cnote">{E(label(x))}</span>'
                   f'<pre class="curl"><code>{E(cmd)}</code></pre></div>')
    n = len(out)
    return ('<details class="repro"><summary>Hämta datan själv '
            f'({n} {"förfrågan" if n == 1 else "förfrågningar"})</summary>'
            '<p class="cintro">Klipp och kör – det här är samma anrop som rapporten gjorde. '
            'SCB svarar med JSON-stat 2.0, Kolada och Socialstyrelsen med vanlig JSON och Brå '
            'med en kalkylfil. En stjärna i <span class="mono">valueCodes</span> betyder samtliga '
            'värden i variabeln, vilket är precis vad som begärdes där den står. Hur siffrorna '
            'sedan räknas fram ur svaret står i ”Så är måttet framtaget” ovan.</p>'
            + "".join(out) + '</details>')

PROD = {"SCB": ("SCB", "Statistiska centralbyrån"),
        "BRÅ": ("Brå", "Brottsförebyggande rådet"),
        "SKR": ("SKR", "Sveriges Kommuner och Regioner, via Kolada"),
        "SOS": ("Socialstyrelsen", "Socialstyrelsens dödsorsaksregister och statistik om socialtjänstinsatser"),
        "SKOLVERKET": ("Skolverket", "Skolverkets betygsstatistik"),
        "KRONOFOGDEN": ("Kronofogden", "Kronofogdens statistik över skuldsatta"),
        "TRAFA": ("Trafikanalys", "Trafikanalys statistik över punktlighet på järnväg"),
        "TVA": ("Tillväxtanalys", "Tillväxtanalys statistik över företagskonkurser")}
PCLS = {"SCB": "scb", "BRÅ": "bra", "SKR": "skr", "SOS": "sos",
        "SKOLVERKET": "skv", "KRONOFOGDEN": "kfm",
        "TRAFA": "trf", "TVA": "tva"}

MIXED = {"vardkoer", "vantetider", "hatbrott"}

SV = "abcdefghijklmnopqrstuvwxyzåäö"
SVM = {"é": "e", "è": "e", "ü": "u", "á": "a", "ø": "ö", "æ": "ä"}
def svkey(s):
    out = []
    for ch in s.lower():
        ch = SVM.get(ch, ch); i = SV.find(ch)
        out.append(i + 1 if i >= 0 else 0)
    return out
ORDER = sorted(IND, key=lambda k: svkey(IND[k]["name"]))

def nf(v, dec=1):
    if v is None: return "–"
    if abs(v) >= 10000: return f"{round(v):,}".replace(",", " ")
    return f"{v:,.{dec}f}".replace(",", " ").replace(".", ",")
def pct(v):
    return "–" if v is None else ("+" if v >= 0 else "−") + f"{abs(v):.1f}".replace(".", ",") + " %"
def ppf(v):
    return "–" if v is None else ("+" if v >= 0 else "−") + f"{abs(v):.1f}".replace(".", ",") + " p.e."
def chg(ind, p):
    return ("–" if p["raw"] is None else (ppf(p["raw"]) if ind["calc"]["is_pp"] else pct(p["raw"])))

VERD = {"better": ("g", "Bättre"), "worse": ("b", "Sämre"), "flat": ("f", "Oförändrat"),
        "neutral": ("n", "Utan värdering"), "mixed": ("w", "Blandat"), "na": ("m", "Saknas")}
TKIND = {"rev_up": ("g", "Vänt från försämring till förbättring"),
         "faster_better": ("g", "Förbättringen har tagit fart"),
         "slower_worse": ("g", "Försämringen har bromsat in"),
         "rev_down": ("b", "Vänt från förbättring till försämring"),
         "slower_better": ("b", "Förbättringen har bromsat in"),
         "faster_worse": ("b", "Försämringen har tagit fart"),
         "flat": ("f", "Oförändrad takt"), "neutral": ("n", "Utan värdering")}
TSHORT = {"rev_up": ("g", "Vänt till bättre"), "faster_better": ("g", "Bättre takt"),
          "slower_worse": ("g", "Bättre takt"), "rev_down": ("b", "Vänt till sämre"),
          "slower_better": ("b", "Sämre takt"), "faster_worse": ("b", "Sämre takt"),
          "flat": ("f", "Oförändrad takt"), "neutral": ("n", "–")}
ARROW = {"g": '<svg viewBox="0 0 10 10" fill="currentColor"><path d="M5 0l5 6H0z"/></svg>',
         "b": '<svg viewBox="0 0 10 10" fill="currentColor"><path d="M5 10L0 4h10z"/></svg>',
         "f": '<svg viewBox="0 0 10 10" fill="currentColor"><rect x="0" y="4" width="10" height="2"/></svg>',
         "n": '<svg viewBox="0 0 10 10" fill="currentColor"><circle cx="5" cy="5" r="2"/></svg>',
         "w": '<svg viewBox="0 0 10 10" fill="currentColor"><path d="M0 5h10v2H0z"/><path d="M5 0l4 4H1z"/></svg>',
         "m": '<svg viewBox="0 0 10 10" fill="none" stroke="currentColor" stroke-width="1.6"><path d="M1 9L9 1"/></svg>'}
def chip(cls, label):
    return f'<span class="chip {cls}">{ARROW[cls]}{E(label)}</span>'
def dclass(ind, p):
    v = p["verdict"]
    return {"better": "up", "worse": "down", "flat": "nil", "neutral": "nil", "na": "na"}[v]
def verdict_of(ind):
    if ind["key"] in MIXED: return "mixed"
    return ind["calc"]["periods"][-1]["verdict"]

def moving_avg(vals, win, seasonal=False):
    """Centred moving average. Sub-annual series use the 2xN filter, which is
    centred correctly on an even window and removes exactly one annual cycle;
    an odd five-quarter window overweights one quarter and leaves part of the
    seasonal pattern behind. Weights are renormalised at the edges."""
    n = len(vals)
    half = win // 2
    if seasonal:
        offs = list(range(-half, half + 1))
        w = [1.0] * (win + 1); w[0] = w[-1] = 0.5
    else:
        offs = list(range(-half, half + 1))
        w = [1.0] * win
    out = []
    for i in range(n):
        num = den = 0.0
        for o, ww in zip(offs, w):
            j = i + o
            if 0 <= j < n and vals[j] is not None:
                num += ww * vals[j]; den += ww
        out.append(round(num / den, 4) if den >= 2 else None)
    return out

CHARTS = {}
def payload(key):
    ind = IND[key]; c = ind["calc"]
    keys = sorted(ind["series"], key=lambda k: (len(k), k))
    keys = sorted(ind["series"])
    vals = [ind["series"][k] if isinstance(ind["series"][k], (int, float)) else None for k in keys]
    def segof(k):
        for i in range(NP):
            p = c["periods"][i]
            if p["from"] and p["to"] and p["from"] <= k <= p["to"]:
                pass
        return 0
    import importlib
    an = importlib.import_module("analyze")
    seg = []
    for k in keys:
        s = 0
        for i in range(NP):
            if an.in_period(c["freq"], k, i): s = i + 1
        seg.append(s)
    marks = [p["to"] for p in c["periods"] if p["to"]]
    ma, mawin, malab = None, None, None
    n_fin = sum(1 for v in vals if v is not None)
    sm = D["smoothing"].get(c["freq"])
    if sm and n_fin >= 8:
        mawin, malab = sm["fonster"], sm["label"]
        ma = moving_avg(vals, mawin, seasonal=sm["seasonal"])
    pmeans = []
    for i, p in enumerate(c["periods"]):
        if p["avg"] is None: continue
        idx = [n for n, k in enumerate(keys) if seg[n] == i + 1]
        if len(idx) < 2: continue
        pmeans.append({"i": i, "a": min(idx), "b": max(idx), "v": p["avg"]})
    CHARTS[key] = {"pmeans": pmeans,
                   "name": ind["name"], "unit": ind["unit"], "short": ind.get("short", ""),
                   "dec": ind.get("dec", 1), "keys": keys, "vals": vals, "seg": seg,
                   "marks": sorted(set(marks)), "pshort": PSHORT,
                   "ma": ma, "mawin": mawin, "malab": malab,
                   "rawlab": {"Q": "kvartalsvärden", "M": "månadsvärden", "A": "årsvärden",
                              "LA": "läsårsvärden", "ULF": "mätpunkter"}[c["freq"]]}

def figs_block(ind):
    c = ind["calc"]; dec = ind.get("dec", 1)
    out = ['<div class="figs">']
    for i, p in enumerate(c["periods"]):
        head = (f'<div class="plabel"><span class="swatch" style="background:var(--p{i+1})"></span>'
                f'<span>{E(PLABEL[i])}</span></div>')
        if p["raw"] is None and p["end"] is None:
            out.append(f'<div class="f">{head}<div class="miss">Ingen statistik</div></div>')
            continue
        if p["raw"] is None:
            note = ("Bara en mätpunkt" if p["n"] <= 1 else "Brott i serien")
            out.append(f'<div class="f">{head}<div class="pts">{nf(p["end"], dec)}</div>'
                       f'<span class="when">{E(str(p["to"]))}</span>'
                       f'<div class="miss" style="margin-top:6px">{note}</div></div>')
            continue
        flag = '<span class="pflag">delvis</span>' if p["partial"] else ""
        out.append(f'<div class="f">{head}'
                   f'<div class="pts">{nf(p["start"], dec)}<span class="arrow">→</span>'
                   f'{nf(p["end"], dec)}</div>'
                   f'<span class="when">{E(str(p["from"]))} → {E(str(p["to"]))}</span>'
                   f'<div class="chg"><span class="delta {dclass(ind,p)}">{chg(ind,p)}</span>{flag}</div>'
                   f'<div class="avg">Snitt {nf(p["avg"], dec)}</div></div>')
    out.append("</div>")
    return "".join(out)

def slopef(v, is_pp):
    if v is None: return "–"
    u = " p.e./år" if is_pp else " %/år"
    sign = "" if abs(v) < 0.005 else ("+" if v > 0 else "−")
    return sign + f"{abs(v):.2f}".replace(".", ",") + u

def trend_block(ind):
    c = ind["calc"]; is_pp = c["is_pp"]
    cls, lbl = TKIND[c["trend_kind"]]
    sh = c["trend_shift"]
    shtxt = ("–" if sh is None else ("+" if sh >= 0 else "−") +
             f"{abs(sh):.2f}".replace(".", ",") + (" p.e./år" if is_pp else " %/år"))
    parts = []
    for i, p in enumerate(c["periods"]):
        parts.append(f'<span><span class="swatch" style="background:var(--p{i+1})"></span>'
                     f'{E(slopef(p["gain"], is_pp))}</span>')
        if i < 3: parts.append('<span class="tarrow">→</span>')
    b = ind.get("better")
    gloss = ("Positiva tal betyder förbättring. För det här måttet är en <b>minskning</b> en "
             "förbättring, så ett positivt tal betyder att måttet sjönk."
             if b == "down" else
             "Positiva tal betyder förbättring. För det här måttet är en <b>ökning</b> en "
             "förbättring, så ett positivt tal betyder att måttet steg."
             if b == "up" else
             "Måttet saknar självklar riktning, så takten redovisas utan omdöme.")
    ns = ", ".join(str(p["slope_n"]) for p in c["periods"])
    return (f'<div class="trend"><div class="thead">'
            f'<span class="eyebrow">Förbättringstakt per år</span>{chip(cls, lbl)}</div>'
            f'<div class="tslopes">{"".join(parts)}'
            f'<span class="tshift">skifte mot förra perioden {E(shtxt)}</span></div>'
            f'<p class="tgloss">{gloss}</p>'
            f'<span class="tn">Lutningarna bygger på {E(ns)} mätpunkter per period.</span></div>')

def src_line(ind):
    ids = ind.get("tables") or []
    if ind.get("source", "SCB") == "SCB":
        parts = [f'<a href="{E(TABLES[t]["url"])}" target="_blank" rel="noopener">{E(t)}</a>'
                 for t in ids if t in TABLES]
        return f'<div class="srcline">Tabeller i SCB:s statistikdatabas: {" · ".join(parts)}</div>' if parts else ""
    parts = []
    for t in ids:
        m = ALTSRC.get(t)
        if m: parts.append(f'<a href="{E(m["url"])}" target="_blank" rel="noopener">{E(m["namn"])}</a> '
                           f'<span style="opacity:.75">({E(m["producent"])})</span>')
    kpi = ind.get("kpi") or []
    extra = f'<br>Kolada-nyckeltal: {E(", ".join(kpi))}' if kpi else ""
    return f'<div class="srcline">Källa: {" · ".join(parts)}{extra}</div>'

def notes_block(ind):
    ns = ind.get("notes") or []
    return f'<div class="notes"><ul>{"".join(f"<li>{E(n)}</li>" for n in ns)}</ul></div>' if ns else ""

def values_table(ind):
    import importlib
    an = importlib.import_module("analyze")
    c = ind["calc"]; dec = ind.get("dec", 1)
    keys = sorted(ind["series"])
    def w(k):
        for i in range(NP):
            if an.in_period(c["freq"], k, i): return f"w{i+1}"
        return ""
    th = "".join(f'<th>{E(k)}</th>' for k in keys)
    td = "".join(f'<td class="{w(k)}">'
                 f'{nf(ind["series"][k], dec) if isinstance(ind["series"][k], (int, float)) else "·"}</td>'
                 for k in keys)
    return ('<details><summary>Visa alla värden</summary><div class="dt-scroll">'
            f'<table class="dt"><thead><tr><th>Period</th>{th}</tr></thead>'
            f'<tbody><tr><th scope="row">{E(ind.get("short") or ind["unit"])}</th>{td}</tr></tbody>'
            '</table></div></details>')

def infer_freq(keys):
    k = keys[0]
    if "K" in k: return "Q"
    if "M" in k: return "M"
    if "/" in k: return "LA"
    if "-" in k: return "ULF"
    return "A"

def extras_table(ind):
    import importlib
    an = importlib.import_module("analyze")
    ex = ind.get("extra") or {}
    rows = []
    for name, ser in ex.items():
        ser = {k: v for k, v in ser.items() if isinstance(v, (int, float))}
        if not ser: continue
        f = infer_freq(sorted(ser))
        mx = max(abs(v) for v in ser.values())
        dec = 0 if mx >= 1000 else (1 if mx >= 10 else 2)
        cells = []
        for i in range(NP):
            obs = {k: v for k, v in ser.items() if an.in_period(f, k, i)}
            if not obs: cells.append('<td>–</td>'); continue
            cells.append(f'<td class="w{i+1}">{nf(ser[max(obs)], dec)}</td>')
        rows.append(f'<tr><th scope="row">{E(name)}</th>{"".join(cells)}</tr>')
    if not rows: return ""
    th = "".join(f'<th>{E(p)}</th>' for p in PSHORT)
    return ('<details><summary>Kompletterande serier</summary><div class="dt-scroll">'
            f'<table class="dt"><thead><tr><th>Serie, värde vid periodens slut</th>{th}</tr>'
            f'</thead><tbody>{"".join(rows)}</tbody></table></div></details>')

def ledger():
    rows = []
    for n, key in enumerate(ORDER, 1):
        ind = IND[key]; c = ind["calc"]
        prod = ind.get("source", "SCB")
        cells = ""
        for i, p in enumerate(c["periods"]):
            klass = "r p4col" if i == 3 else "r"
            flag = '<span class="pflag">delvis</span>' if (p["partial"] and p["raw"] is not None) else ""
            cells += f'<td class="{klass}"><span class="delta {dclass(ind,p)}">{chg(ind,p)}</span>{flag}</td>'
        cls, lbl = VERD[verdict_of(ind)]
        rows.append(
            f'<tr><td class="idx">{n:02d}</td>'
            f'<td><span class="lname"><a href="#i-{key}">{E(ind["name"])}</a></span>'
            f'<span class="lunit">{E(ind["unit"])}</span></td>'
            f'<td><span class="prod p-{PCLS[prod]}">{E(PROD[prod][0])}</span></td>'
            f'{cells}'
            f'<td><span data-spark="{key}"></span></td>'
            f'<td>{chip(cls, lbl)}</td>'
            f'<td>{chip(*TSHORT[c["trend_kind"]])}</td></tr>')
    ph = "".join(f'<th class="pcol" scope="col">{E(PSHORT[i])}'
                 f'<span>{E(PLABEL[i].split("–")[0])}–</span></th>' for i in range(NP))
    return ('<div class="ledger-scroll"><table class="ledger">'
            f'<caption class="visually-hidden">Samtliga {len(ORDER)} mätpunkter med förändring '
            f'per mandatperiod, nivå och takt</caption>'
            f'<thead><tr><th scope="col">#</th><th scope="col">Mätpunkt</th>'
            f'<th scope="col">Källa</th>{ph}'
            '<th>Förlopp</th><th>Nivå nu</th><th>Takt</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>')


CAUSES = json.load(open(os.path.join(HERE, "data", "causes.json"),
                        encoding="utf-8")) if os.path.exists(
    os.path.join(HERE, "data", "causes.json")) else {"matpunkter": {}, "omvarld": {}}

N_BESLUT = sum(len(v.get("beslut", [])) for v in CAUSES["matpunkter"].values())
N_BET = sum(1 for v in CAUSES["matpunkter"].values()
            for d in v.get("beslut", []) if d.get("bet_url"))

DOKNAMN = {"prop": "Proposition", "bet": "Betänkande", "rir": "Riksrevisionen",
           "sou": "Utredning", "rfr": "Riksdagsrapport"}


def _doklista(rader, med_period=True):
    ut = []
    for d in rader:
        pd = ""
        if med_period and d.get("period") is not None:
            i = d["period"]
            pd = (f'<span class="dperiod"><i class="swatch" style="background:'
                  f'var(--p{i+1})"></i>{E(PSHORT[i])}</span>')
        cit = ""
        if d.get("sammanfattning"):
            cit = (f'<blockquote class="dcit">{E(d["sammanfattning"])}'
                   f'<cite>{E(d["ref"])}, egen sammanfattning</cite></blockquote>')
        bet = ""
        if d.get("bet_url"):
            bet = (f'<a class="votelink" href="{E(d["bet_url"])}" rel="noopener noreferrer" '
                   f'target="_blank" title="Utskottets betänkande {E(d["bet_ref"])}. Där står '
                   f'förslagspunkterna och, om någon punkt gick till omröstning, hur varje '
                   f'parti röstade.">votering och beslut →</a>')
        ut.append(f'<li>{pd}<a href="{E(d["url"])}" rel="noopener noreferrer" '
                  f'target="_blank">{E(d["titel"])}</a> '
                  f'<span class="dref">{E(d["ref"])} · {E(d["datum"])}</span>{bet}'
                  f'{vote_block(d)}{cit}</li>')
    return "".join(ut)


PARTIES = D.get("parties", {})


def _lum(hexv):
    r, g, b = (int(hexv[i:i + 2], 16) / 255 for i in (1, 3, 5))
    f = lambda v: v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def _kontrast(a, b):
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def party_ink(farg):
    """Svart eller vit text på partifärgen, den som ger högst kontrast. Färgerna
    är partiernas egna och ändras inte, så texten får anpassa sig."""
    svart, vit = _kontrast(farg, "#111111"), _kontrast(farg, "#ffffff")
    ink = "#111111" if svart >= vit else "#ffffff"
    if max(svart, vit) < 4.5:                 # 4.5:1 krävs för text i den här storleken
        raise SystemExit(f"partifärg {farg} klarar inte 4.5:1 mot varken svart eller vitt")
    return ink


def party_chip(kod, stod=False):
    m = PARTIES.get(kod, {})
    farg = m.get("farg", "#888888")
    titel = m.get("namn", kod) + (" – samarbets- eller stödparti utanför regeringen" if stod else "")
    kls = "pchip stod" if stod else "pchip"
    return (f'<span class="{kls}" style="--pc:{farg};--pi:{party_ink(farg)}" '
            f'title="{E(titel)}">{E(kod)}</span>')


def party_row(i, med_etikett=True):
    """Regeringsunderlaget för en mandatperiod. Regeringspartier fyllda,
    stödpartier utanför regeringen streckade."""
    m = PMETA[i]
    reg, stod = m.get("regeringspartier") or [], m.get("stodpartier") or []
    if not reg:
        return ""
    chips = "".join(party_chip(k) for k in reg) + "".join(party_chip(k, True) for k in stod)
    lbl = f'<span class="pchip-lbl">{E(m.get("regering", ""))}</span>' if med_etikett else ""
    return f'<span class="pchips">{lbl}{chips}</span>' 

VOTES = json.load(open(os.path.join(HERE, "data", "votes.json"),
                       encoding="utf-8"))["betankanden"] if os.path.exists(
    os.path.join(HERE, "data", "votes.json")) else {}

ROSTORD = [("Ja", "ja"), ("Nej", "nej"), ("Avstår", "avst"), ("Frånvarande", "franv")]


def vote_block(d):
    """How the parties voted on the committee report that handled this bill.
    Reported point by point, because that is the unit a division applies to -
    the party lines differ between the points of one report."""
    b = VOTES.get(d.get("bet_id") or "")
    if not b:
        return ""
    röstade = [p for p in b["punkter"] if p.get("partier")]
    if not röstade:
        return ""
    ack = sum(1 for p in b["punkter"] if p.get("beslutstyp") == "acklamation")
    rader = ""
    for p in röstade:
        grupper = ""
        for rost, kls in ROSTORD:
            med = [k for k, v in p["partier"].items()
                   if v["linje"] == rost and k not in ("-", "")]
            if not med:
                continue
            chips = "".join(party_chip(k) for k in med)
            grupper += (f'<span class="vgrp v-{kls}">'
                        f'<span class="vlbl">{E(rost)}</span>{chips}</span>')
        split = [f'{k}: {v["avvikande"]} av {v["narvarande"]} närvarande röstade annat'
                 for k, v in p["partier"].items() if v.get("avvikande")]
        splittext = (f'<span class="vsplit">{E(" · ".join(split))}</span>'
                     if split else "")
        rader += (f'<div class="vrow"><div class="vpt">Punkt {E(str(p["punkt"]))}'
                  f' · {E(p["rubrik"] or "utan rubrik")}</div>'
                  f'<div class="vgrps">{grupper}</div>{splittext}</div>')
    ackrad = (f'<div class="vack">{ack} av {len(b["punkter"])} punkter avgjordes '
              f'med acklamation – ingen ledamot begärde omröstning.</div>'
              if ack else "")
    return (f'<div class="votes"><div class="vhead">Hur partierna röstade'
            f'<span class="vn">{len(röstade)} omröstning'
            f'{"ar" if len(röstade) != 1 else ""}</span></div>'
            f'<div class="vbody">{rader}{ackrad}</div></div>')


def causes_block(key):
    c = CAUSES["matpunkter"].get(key)
    if not c:
        return ""
    d = []
    if c.get("mekanism"):
        d.append(f'<p><b>Vad som styr måttet.</b> {E(c["mekanism"])}</p>')
    if c.get("tolkning"):
        d.append(f'<p><b>Vad materialet räcker till.</b> {E(c["tolkning"])}</p>')

    om = [CAUSES["omvarld"][k] for k in c.get("omvarld", []) if k in CAUSES["omvarld"]]
    if om:
        rader = "".join(
            f'<li><b>{E(o["namn"])}</b> <span class="dref">{E(o.get("nar",""))}</span>'
            f'<span class="omtext">{E(o["vad"])}</span>'
            + (f'<ul class="dlist tight">{_doklista(o["dokument"])}</ul>'
               if o.get("dokument") else "") + '</li>' for o in om)
        d.append('<div class="csect"><h5>Omvärlden</h5>'
                 '<p class="chint">Händelser utanför politiken som rör måttet. '
                 'De förklarar ofta mer av rörelsen än besluten gör.</p>'
                 f'<ul class="omlist">{rader}</ul></div>')

    if c.get("granskning"):
        d.append('<div class="csect"><h5>Vad granskarna kommit fram till</h5>'
                 '<p class="chint">Riksrevisionen och statliga utredningar som '
                 'faktiskt utvärderat området. Det är här det finns evidens om '
                 'effekter – citaten är sammanfattningar hämtade ur rapporternas '
                 'egna sammanfattningskapitel. Urvalet är granskarnas eget: '
                 'Riksrevisionen väljer var den letar, och letar där problem '
                 'misstänks.</p>'
                 f'<ul class="dlist">{_doklista(c["granskning"], False)}</ul></div>')

    if c.get("beslut"):
        d.append('<div class="csect"><h5>Beslut i området</h5>'
                 '<p class="chint">Propositioner som riksdagen behandlat, tre per '
                 'mandatperiod, valda på titelinnehåll. Att ett beslut ligger i '
                 'samma period som en förändring är <b>inget belägg</b> för att det '
                 'orsakade den – listan visar vad som gjordes, inte vad det gav.</p>'
                 f'<ul class="dlist">{_doklista(c["beslut"])}</ul></div>')

    nröst = sum(1 for b in c.get("beslut", []) if VOTES.get(b.get("bet_id") or "")
                and any(p.get("partier") for p in VOTES[b["bet_id"]]["punkter"]))
    röst = f' · {nröst} med partiröster' if nröst else ""
    return ('<details class="causes"><summary>Orsaker och sammanhang'
            '<span class="cn">' + str(len(c.get("beslut", [])) +
                                      len(c.get("granskning", []))) +
            f' källor{röst}</span></summary><div class="cbody">' + "".join(d) +
            '</div></details>')


def entry(n, key):
    ind = IND[key]; c = ind["calc"]
    payload(key)
    cls, lbl = VERD[verdict_of(ind)]
    prod = ind.get("source", "SCB")
    prose = "".join(f"<p>{E(p.strip())}</p>" for p in ind["comment"].split("\n\n") if p.strip())
    return (f'<article class="entry" id="i-{key}">'
            f'<div class="ehead"><span class="idx">{n:02d}</span>'
            f'<h3>{E(ind["name"])}</h3>{chip(cls, lbl)}'
            f'<span class="prod p-{PCLS[prod]}" title="{E(PROD[prod][1])}">{E(PROD[prod][0])}</span>'
            f'<span class="eyebrow" style="margin-left:auto">{E(ind["grupp"])}</span></div>'
            f'<p class="eunit">{E(ind["unit"])}</p>'
            f'<div class="ebody">'
            f'<div class="prose">{figs_block(ind)}{trend_block(ind)}{prose}'
            f'<div class="method"><b>Så är måttet framtaget</b>{E(ind["method"])}</div>'
            f'{notes_block(ind)}{src_line(ind)}</div>'
            f'<div><div class="chartbox">'
            f'<div class="ctitle">{E(ind["name"])} · {E(ind.get("short") or "")}</div>'
            f'<div data-chart="{key}"></div></div>'
            f'{values_table(ind)}{extras_table(ind)}{causes_block(key)}{curl_block(ind)}</div>'
            f'</div></article>')

ENTRIES = "".join(entry(n, k) for n, k in enumerate(ORDER, 1))

def tally():
    lvl = {"better": 0, "worse": 0, "flat": 0, "neutral": 0, "mixed": 0, "na": 0}
    trd = {"g": 0, "b": 0, "f": 0, "n": 0}
    rev_up = rev_down = 0
    for key in ORDER:
        ind = IND[key]
        lvl[verdict_of(ind)] += 1
        k = ind["calc"]["trend_kind"]
        trd[TSHORT[k][0]] += 1
        rev_up += k == "rev_up"; rev_down += k == "rev_down"
    a = [("g", lvl["better"], "mätpunkter står på en bättre nivå än vid maktskiftet 2022"),
         ("b", lvl["worse"], "står på en sämre nivå"),
         ("f", lvl["flat"], "har rört sig för lite för att kallas en förändring"),
         ("w", lvl["mixed"], "är blandade: huvudserien och de kompletterande serierna pekar olika"),
         ("m", lvl["neutral"] + lvl["na"], "saknar självklar riktning eller går inte att mäta")]
    b = [("g", trd["g"], f"mätpunkter förbättras snabbare än under perioden 2018–2022 – "
                         f"{rev_up} av dem har vänt från försämring till förbättring"),
         ("b", trd["b"], f"förbättras långsammare eller har försämrats – "
                         f"{rev_down} har vänt från förbättring till försämring"),
         ("f", trd["f"], "håller i stort sett samma takt som under förra perioden"),
         ("m", trd["n"], "saknar självklar riktning och lämnas utan omdöme")]
    def block(lbl, sub, cells):
        return (f'<div class="tblock"><div class="tbhead"><span class="eyebrow">{E(lbl)}</span>'
                f'<span class="tbsub">{E(sub)}</span></div><div class="tally">' + "".join(
                f'<div class="cell {c}"><span class="n">{v}</span><span class="cap">{E(t)}</span></div>'
                for c, v, t in cells) + '</div></div>')
    return (block("Nivå", "var måttet ligger nu jämfört med oktober 2022", a) +
            block("Takt", "hur snabbt måttet förbättras jämfört med 2018–2022", b))

OV_PP, OV_REL = [], []
for key in ORDER:
    ind = IND[key]; c = ind["calc"]
    better = ind.get("better")
    if better == "neutral": continue
    d = 1 if better == "up" else -1
    ps = [p["raw"] for p in c["periods"]]
    rank = None if ps[-1] is None else round(ps[-1] * d, 4)
    verd = "flat" if rank is None or abs(rank) < 0.5 else ("good" if rank > 0 else "bad")
    row = {"name": ind["name"], "p": ps, "rank": rank, "verdict": verd}
    (OV_PP if c["is_pp"] else OV_REL).append(row)
def ov_sort(rows):
    return sorted(rows, key=lambda x: (x["rank"] is None, -(x["rank"] or 0)))
OV_PP, OV_REL = ov_sort(OV_PP), ov_sort(OV_REL)

def gov_block():
    """Regeringsunderlaget per mandatperiod. Rena fakta om vem som styrde -
    rapporten kopplar inga utfall till partier, och säger det uttryckligen."""
    rader = ""
    for i in range(NP):
        rader += (f'<div class="govrow">'
                  f'<div class="govhead"><span class="swatch" style="background:var(--p{i+1})">'
                  f'</span><b>{E(PLABEL[i])}</b>{party_row(i)}</div>'
                  f'<p>{E(GOVNOT[i])}</p></div>')
    return (f'<div class="govbox"><span class="eyebrow">Vem som styrde</span>'
            f'{rader}<p class="govfoot">Fyllda märken är regeringspartier, streckade är '
            f'partier som gav stöd utan att ingå i regeringen. Uppgifterna är sammanställda '
            f'för hand och är den enda delen av rapporten som inte kommer ur ett API – '
            f'regeringsbildningar finns inte som statistik. <b>Rapporten kopplar inga utfall '
            f'till partier.</b> Att en förändring inträffade under en viss regering säger '
            f'ingenting om vad regeringen orsakade; se metodavsnittet.</p></div>')

def agg_table(panel_key, from_i=0):
    rows = [
      ("Andel som förbättrades", "andel", "%", 0,
       "Andel av de mätpunkter som går att mäta i perioden som blev bättre. "
       "Lätt att tolka, men beroende av var tröskeln för ”en förändring” sätts."),
      ("Netto: bättre minus sämre", "netto", "%", 0,
       "Skillnaden mellan andelen som blev bättre och andelen som blev sämre. "
       "Straffar försämringar, till skillnad från raden ovan."),
      ("Andel med rätt tecken", "tecken", "%", 0,
       "Som första raden, men utan tröskel: varje förändring räknas, hur liten den än är. "
       "Visar om slutsatsen hänger på tröskelvärdet."),
      ("Standardiserad takt (medel)", "z", "", 2,
       "Varje mätpunkts förbättringstakt delad med dess egen normala variation, sedan "
       "genomsnittad. Väger in hur stor förändringen var, men låter inte kronor och "
       "procentenheter dominera över varandra. Kapad vid ±3."),
      ("Standardiserad takt (median)", "z_median", "", 2,
       "Samma sak men median i stället för medelvärde, så att några få stora utfall "
       "inte kan bära resultatet."),
      ("Normaliserad rang", "rang", "", 3,
       "För varje mätpunkt rangordnas perioderna: 0 = måttets sämsta period, 1 = dess "
       "bästa. Helt fri från enheter och utstickare, men säger bara vilken period som "
       "var bäst, inte hur mycket."),
    ]
    ths = "".join(f'<th class="pcol" scope="col">{E(PLABEL[i])}'
                  f'{party_row(i, med_etikett=False)}</th>' for i in range(NP))
    body = ""
    for name, key, unit, dec, expl in rows:
        vals = AGG[panel_key][key]
        vv = [v for i, v in enumerate(vals) if i >= from_i and v is not None]
        best = max(vv, default=None)
        cells = ""
        for i, v in enumerate(vals):
            if i < from_i: cells += '<td class="r" style="color:var(--ink-3)">·</td>'; continue
            txt = "–" if v is None else nf(v, dec) + (" " + unit if unit else "")
            strong = ' style="font-weight:700;color:var(--good)"' if v == best else ""
            cells += f'<td class="r"{strong}>{txt}</td>'
        body += (f'<tr><th scope="row">{E(name)}<span class="aexpl">{E(expl)}</span></th>'
                 f'{cells}</tr>')
    nb = AGG[panel_key]["n_matpunkter"]
    span = (f'{PLABEL[from_i].split("–")[0]}–{PLABEL[-1].split("–")[1]}' if from_i
            else "hela spannet")
    return ('<div class="srcs-scroll"><table class="srcs aggt">'
            f'<caption class="visually-hidden">Sex helhetsmått per mandatperiod, '
            f'{nb} mätpunkter</caption>'
            f'<thead><tr><th scope="col">Mått · {nb} mätpunkter, {span}</th>'
            f'{ths}</tr></thead><tbody>{body}</tbody></table></div>')

def matrix_counts():
    turned = stalled = 0
    for key in ORDER:
        c = IND[key]["calc"]
        lv = c["periods"][-1]["verdict"]; tv = c["trend_kind"]
        if lv in ("neutral", "na") or tv == "neutral": continue
        if TSHORT[tv][0] == "g" and lv in ("worse", "flat"): turned += 1
        if TSHORT[tv][0] == "b" and lv == "better": stalled += 1
    return turned, stalled
N_TURNED, N_STALLED = matrix_counts()

AGG_MEAS = [("andel", "andel som förbättrades"), ("netto", "netto"),
            ("tecken", "andel med rätt tecken"), ("z", "standardiserad takt, medel"),
            ("z_median", "standardiserad takt, median"), ("rang", "normaliserad rang")]

def agg_leaders(panel_key, from_i=0):
    p = AGG[panel_key]; out = []
    for mk, mn in AGG_MEAS:
        vals = [(i, p[mk][i]) for i in range(NP) if i >= from_i and p[mk][i] is not None]
        if not vals: continue
        top = max(v for _, v in vals)
        out.append((mn, [i for i, v in vals if abs(v - top) < 1e-9]))
    return out

def _pe(v):
    """Procentenheter med svenskt decimaltecken och explicit tecken."""
    return ("+" if v >= 0 else "−") + f"{abs(v):.1f}".replace(".", ",") + " p.e."

def panel_extra_names():
    """Mätpunkterna som bara finns i den bredare panelen."""
    smal = set(AGG.get("balanced_keys") or [])
    bred = set(AGG.get("balanced3_keys") or [])
    return sorted((IND[k]["name"] for k in bred - smal if k in IND), key=str.lower)

def panel_top(panel_key, from_i=1):
    """Perioderna som leder på flest av de sex måtten i en panel."""
    wins = {}
    for _, ids in agg_leaders(panel_key, from_i):
        for i in ids: wins[i] = wins.get(i, 0) + 1
    if not wins: return ()
    best = max(wins.values())
    return tuple(sorted(k for k, v in wins.items() if v == best))

def panel_shift():
    """Vad panelvalet gör med talen, räknat ur AGG i stället för bedömt för hand."""
    namn = panel_extra_names()
    if not namn:
        return "Panelerna innehåller samma mätpunkter, så valet mellan dem flyttar inga tal."
    inled = (f"De {len(namn)} mätpunkter som bara finns i den bredare panelen – "
             f"{E(', '.join(namn))} – når inte tillbaka till "
             f"{E(PLABEL[0].split('–')[0])}, och det är därför den bredare panelen finns.")
    smal, bred = AGG["balanserad"], AGG["balanserad3"]
    d = [bred["andel"][i] - smal["andel"][i] for i in range(1, NP)
         if bred["andel"][i] is not None and smal["andel"][i] is not None]
    if not d:
        return inled + " Panelerna har inga tal som går att ställa mot varandra."
    lo, hi = min(d), max(d)
    rorelse = _pe(lo) if abs(hi - lo) < 0.05 else f"mellan {_pe(lo)} och {_pe(hi)}"
    ordning = ("utan att ändra vilken period som ligger högst"
               if panel_top("balanserad") == panel_top("balanserad3")
               else "och ändrar vilken period som ligger högst")
    return (inled + f" Att ta med dem flyttar andelen som förbättrades {rorelse} från "
            f"{E(PLABEL[1])} och framåt, {ordning}.")

def agg_verdict(panel_key, from_i=0):
    lead = agg_leaders(panel_key, from_i)
    if not lead: return "Panelen ger inga tal att jämföra."
    wins = {}
    for _, ids in lead:
        for i in ids: wins[i] = wins.get(i, 0) + 1
    n = len(lead)
    best = max(wins.values())
    who = sorted(k for k, v in wins.items() if v == best)
    if best == n and len(who) == 1:
        return (f"På den här panelen ligger {PLABEL[who[0]]} högst på <b>alla {n} måtten</b>.")
    if len(who) == 1:
        return (f"På den här panelen ligger {PLABEL[who[0]]} högst på {best} av {n} mått.")
    return ("På den här panelen delar " + " och ".join(PLABEL[i] for i in who) +
            f" förstaplatsen, med {best} mått var av {n}.")

def matrix():
    LVL = [("better", "Bättre nivå"), ("flat", "Oförändrad nivå"), ("worse", "Sämre nivå")]
    TRD = [("g", "Takten har förbättrats"), ("f", "Oförändrad takt"), ("b", "Takten har försämrats")]
    cell = {(t, l): [] for t, _ in TRD for l, _ in LVL}
    ut = []
    for key in ORDER:
        ind = IND[key]; c = ind["calc"]
        lv = c["periods"][-1]["verdict"]; tv = TSHORT[c["trend_kind"]][0]
        if lv in ("neutral", "na") or c["trend_kind"] == "neutral":
            ut.append(ind); continue
        cell[(tv, lv)].append(ind)
    def tag(ind):
        v = verdict_of(ind)
        cc = "g" if v == "better" else ("b" if v == "worse" else "f")
        return f'<a class="mtag t-{cc}" href="#i-{ind["key"]}">{E(ind["name"])}</a>'
    head = "".join(f'<div class="mh">{E(l)}</div>' for _, l in LVL)
    rows = ""
    for tk, tl in TRD:
        cells = ""
        for lk, _ in LVL:
            items = cell[(tk, lk)]
            klass = "mc" + (" mc-good" if tk == "g" and lk == "better" else
                            " mc-bad" if tk == "b" and lk == "worse" else "")
            cells += (f'<div class="{klass}">' +
                      ("".join(tag(i) for i in items) if items else '<span class="mempty">–</span>')
                      + "</div>")
        rows += f'<div class="mrow"><div class="mrh">{E(tl)}</div>{cells}</div>'
    return (f'<div class="matrix"><div class="mrow mhead"><div class="mrh"></div>{head}</div>{rows}</div>'
            f'<p class="ovcap">Matrisen jämför bara de två senaste perioderna – 2022–2026 mot '
            f'2018–2022 – eftersom det är rapportens fråga. Rader: om utvecklingstakten är bättre '
            f'eller sämre än under förra perioden, räknat som förbättring per år. Kolumner: om nivån '
            f'vid periodens slut är bättre, sämre eller oförändrad. I den övre mittenrutan och den övre '
            f'högerrutan har takten förbättrats medan nivån ännu inte hunnit '
            f'tillbaka; i den nedre vänstra gäller det omvända, nivån är bättre men takten '
            f'har försämrats. Vilka rutor som betyder mest beror på vad man frågar efter. Utanför matrisen: {E(" · ".join(i["name"] for i in ut))}.</p>')

def sources():
    us, ua = {}, {}
    for key in ORDER:
        ind = IND[key]
        b = us if ind.get("source", "SCB") == "SCB" else ua
        for t in ind.get("tables") or []:
            b.setdefault(t, []).append(ind["name"])
    rows = []
    for t in sorted(us):
        m = TABLES.get(t)
        if not m: continue
        rows.append(f'<tr><td class="id"><a href="{E(m["url"])}" target="_blank" rel="noopener">{E(t)}</a></td>'
                    f'<td>{E(m["label"])}</td><td>{E(m["source"])}</td>'
                    f'<td class="upd">{E(m["updated"][:10])}</td>'
                    f'<td>{E(", ".join(dict.fromkeys(us[t])))}</td></tr>')
    a = ('<div class="srcs-scroll"><table class="srcs">'
         '<caption class="visually-hidden">Tabeller ur SCB:s statistikdatabas</caption>'
         '<thead><tr><th scope="col">Tabell</th>'
         '<th scope="col">Tabellens namn i statistikdatabasen</th>'
         '<th scope="col">Statistikansvarig</th>'
         f'<th scope="col">Uppdaterad</th><th scope="col">Används för</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    rows = []
    for t in sorted(ua, key=lambda x: ALTSRC[x]["producent"]):
        m = ALTSRC[t]
        rows.append(f'<tr><td>{E(m["producent"])}</td>'
                    f'<td><a href="{E(m["url"])}" target="_blank" rel="noopener">{E(m["namn"])}</a></td>'
                    f'<td>{E(m["kanal"])}</td><td>{E(", ".join(dict.fromkeys(ua[t])))}</td></tr>')
    nd = sum(len(v.get("beslut", [])) + len(v.get("granskning", []))
             for v in CAUSES["matpunkter"].values())
    rows.append(
        '<tr><td>Sveriges riksdag</td>'
        '<td><a href="https://data.riksdagen.se/" target="_blank" rel="noopener">'
        'Riksdagens öppna data – dokumentlista</a></td>'
        '<td>Hämtat maskinellt ur data.riksdagen.se: propositioner, utskottsbetänkanden, '
        'Riksrevisionens granskningsrapporter, statens offentliga utredningar och rapporter '
        'från riksdagen, 2009–2026. Fulltext hämtas bara för de granskningar som citeras.</td>'
        f'<td>Orsaker och sammanhang ({nd} källhänvisningar)</td></tr>')
    b = ('<div class="srcs-scroll"><table class="srcs">'
         '<caption class="visually-hidden">Övriga statistikansvariga myndigheter</caption>'
         '<thead><tr><th scope="col">Statistikansvarig</th>'
         '<th scope="col">Källa</th><th scope="col">Så är den hämtad</th>'
         '<th scope="col">Används för</th></tr></thead>'
         f'<tbody>{"".join(rows)}</tbody></table></div>')
    return a, b
SRC_SCB, SRC_ALT = sources()

N_SCB = sum(1 for k in ORDER if IND[k].get("source", "SCB") == "SCB")
N_ALT = len(ORDER) - N_SCB
N_BRA = sum(1 for k in ORDER if IND[k].get("source") == "BRÅ")
N_SKR = sum(1 for k in ORDER if IND[k].get("source") == "SKR")
N_SOS = sum(1 for k in ORDER if IND[k].get("source") == "SOS")
def cover(i):
    return sum(1 for k in ORDER if IND[k]["calc"]["periods"][i]["raw"] is not None)
COV = [cover(i) for i in range(NP)]
N_STALE = sum(1 for k in ORDER
              if (IND[k]["calc"]["periods"][-1]["to"] or "")[:4].isdigit()
              and int((IND[k]["calc"]["periods"][-1]["to"] or "0")[:4]) <= 2024)

GOV = [p.get("regering", "") for p in PMETA]
SUB = [p.get("not", "") for p in PMETA]
GOVNOT = [p.get("regeringsnot", "") for p in PMETA]

CSSOUT = CSS
for k, v in period_css().items():
    CSSOUT = CSSOUT.replace(k, v)
def _pan(key, name, span_from=0):
    p = AGG[key]
    return {"name": name,
            "vals": [v if i >= span_from else None for i, v in enumerate(p["andel"])],
            "n": p["n"], "upp": p["upp"]}
AGGP = {"labels": PLABEL, "panels": [
    _pan("balanserad3", f'{AGG["balanserad3"]["n_matpunkter"]} mätpunkter, '
                        f'{PLABEL[1].split("–")[0]}–{PLABEL[-1].split("–")[1]}', 1),
    _pan("balanserad", f'{AGG["balanserad"]["n_matpunkter"]} mätpunkter, hela spannet'),
]} if AGG else None
PAYLOAD = json.dumps({"agg": AGGP, "charts": CHARTS, "ovPP": OV_PP, "ovREL": OV_REL, "periods": PLABEL, "np": NP},
                     ensure_ascii=False, separators=(",", ":"))

def pbar():
    out = ['<div class="periodbar">']
    for i in range(NP):
        out.append(f'<div><div class="lbl"><span class="swatch" style="background:var(--p{i+1})"></span>'
                   f'<span class="eyebrow">{E(PSHORT[i])}</span></div>'
                   f'<div class="dates">{E(PLABEL[i])}</div>'
                   f'<div class="sub">{E(SUB[i])}</div>'
                   f'{party_row(i, med_etikett=False)}'
                   f'<span class="gov">{E(GOV[i])} · {COV[i]} av {len(ORDER)} mätpunkter</span></div>')
    return "".join(out) + "</div>"

TITLE = "Fyra mandatperioder i officiell statistik"
DESC = (f"{len(ORDER)} mätpunkter ur SCB:s, Brås, SKR:s och Socialstyrelsens egna databaser, "
        f"jämförda över {NP} mandatperioder {PLABEL[0].split('–')[0]}–{PLABEL[-1].split('–')[1]}.")
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
         'family=Familjen+Grotesk:wght@400;500;600;700&amp;'
         'family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&amp;'
         'family=IBM+Plex+Mono:wght@400;500&amp;display=swap">')

BODY = f"""<a class="skiplink" href="#innehall">Hoppa till innehållet</a>
<div class="wrap">
<header class="mast">
  <div class="kicker">
    <span class="eyebrow">{len(ORDER)} mätpunkter · {NP} mandatperioder</span>
    <span class="eyebrow" style="color:var(--ink-2)">SCB · Brå · SKR · Socialstyrelsen</span>
  </div>
  <h1>{E(TITLE)}</h1>
  <p class="standfirst">{len(ORDER)} mätpunkter, hämtade maskinellt ur myndigheternas egna databaser
  och ställda mot varandra över sexton år: fyra mandatperioder, från 2010 till i dag. Ingen siffra är
  skriven för hand.</p>
  {pbar()}
  {tally()}
  <div class="caution">
    <span class="eyebrow">Läs inte det här som ett resultat</span>
    <p>De {len(ORDER)} mätpunkterna är inte lika viktiga, och de är inte viktade. Bostadsbyggandets fall
    på 42 procent och de anmälda brottens minskning på 1,6 procent räknas båda som ett steg i sin
    kolumn. Att räkna mätpunkter är inte att väga dem, och vilka av de {len(ORDER)} som betyder mest är
    en politisk fråga och inte en statistisk.</p>
    <p>Historiken är dessutom ojämn. Bara {COV[0]} av {len(ORDER)} mätpunkter kan mätas över perioden
    {E(PLABEL[0])} och {COV[1]} över {E(PLABEL[1])}, mot {COV[-1]} för den pågående perioden – svensk officiell
    statistik i sin nuvarande form är för många mått yngre än sexton år. Luckorna redovisas öppet i
    stället för att fyllas. {N_STALE} av serierna slutar 2024 eller tidigare och säger därför lite om
    den pågående periodens andra hälft. Och perioderna är inte jämförbara i art: en innehåller en
    finanskris, en ett stort flyktingmottagande, en en pandemi och en en inflationschock.</p>
  </div>
  <p class="mastnote">{N_SCB} av de {len(ORDER)} mätpunkterna kommer ur SCB:s statistikdatabas. De
  övriga {N_ALT} finns inte där och är hämtade från den myndighet som ansvarar för statistiken:
  Brottsförebyggande rådet ({N_BRA} mätpunkter), Sveriges Kommuner och Regioner via Kolada ({N_SKR})
  och Socialstyrelsen ({N_SOS}). Varje mätpunkt är märkt med sin källa.</p>
</header>

<main id="innehall">
<section aria-labelledby="h-sammanstallning">
  <div class="sechead">
    <span class="eyebrow">Sammanställning</span>
    <h2>Alla {len(ORDER)} mätpunkter, fyra perioder</h2>
    <p class="lede">Förändringen mäts inom varje mandatperiod, från den sista mätpunkten före
    regeringsskiftet till periodens sista. Andelsmått som ligger mellan 15 och 85 procent redovisas
    i procentenheter (p.e.), övriga mått i procentuell förändring. Ett plustecken betyder att värdet steg – inte att utvecklingen var bra;
    färgen visar omdömet. Ett streck betyder att statistiken inte når så långt bak. Märkningen
    <span class="pflag" style="display:inline">delvis</span> betyder att perioden bara delvis täcks.</p>
  </div>
  {ledger()}

  <div class="overview">
    <div class="legend">
      {"".join(f'<span><span class="swatch" style="background:var(--p{i+1})"></span>{E(PLABEL[i])}</span>' for i in range(NP))}
      <span style="margin-left:auto"><span class="dot" style="background:var(--good)"></span>bättre
        <span class="dot" style="background:var(--bad);margin-left:10px"></span>sämre
        <span class="dot" style="background:var(--flat);margin-left:10px"></span>oförändrat</span>
    </div>
    <div class="ctitle">Andelsmått · förändring i procentenheter per period</div>
    <div id="ovPP"></div>
    <div class="ctitle" style="margin-top:26px">Nivåmått · procentuell förändring per period</div>
    <div id="ovREL"></div>
    <p class="ovcap"><b>Staplarna visar hur värdet rörde sig, med samma tecken som i tabellen ovan.</b>
    En stapel åt höger betyder att måttet steg, åt vänster att det sjönk – inte att det blev bättre eller
    sämre. Omdömet ligger i <b>punkten vid radnamnet</b>, som gäller den pågående perioden, och
    <b>radordningen</b> är sorterad från bäst till sämst efter just den perioden. De fyra staplarna i
    varje rad är de fyra mandatperioderna i tidsordning, äldst först.</p>
    <p class="ovcap" style="border-top:0; padding-top:0; margin-top:8px">Det övre diagrammet visar mått
    som redan är andelar och mäts i procentenheter, det nedre nivåmått i kronor, dagar, antal och kiloton
    mätta i procent; skalorna är olika och staplarnas längd ska inte jämföras mellan diagrammen. Enstaka
    extremvärden går utanför skalan och är kapade med en sågtandad kant; den exakta siffran står alltid i
    stapeln. Medelålder, skatteintäkter, skattetryck, inkomstklyfta och bostadspriser saknar självklar
    riktning och ingår inte här.</p>
  </div>
</section>

<section aria-labelledby="h-helhet">
  <div class="sechead">
    <span class="eyebrow">Perioderna mot varandra</span>
    <h2 id="h-helhet">Perioderna sammanvägda på sex sätt</h2>
    <p class="lede">Att slå ihop {AGG.get("valued", 0)} olika mått till ett tal per period är inte
    oproblematiskt, och det finns inget enda rätt sätt. Nedan görs det på sex sätt och på två paneler.
    Poängen är inte något av talen i sig, utan var de är överens och var de inte är det.</p>
  </div>

  <div class="overview">
    <div class="ctitle">Andel av mätpunkterna som förbättrades</div>
    <div id="aggChart"></div>
    <p class="ovcap"><b>Vilka mätpunkter som räknas påverkar resultatet.</b>
    Statistiken täcker {COV[0]} mätpunkter under {E(PLABEL[0])} men {COV[-1]} under {E(PLABEL[-1])},
    och en period med fler mått är inte jämförbar med en som har färre. Därför används
    <b>balanserade paneler</b>: samma mätpunkter i alla perioder som ingår. Den smalare panelen
    ({AGG["balanserad"]["n_matpunkter"]} mätpunkter) sträcker sig över hela spannet men utesluter
    allt som inte når tillbaka till {E(PLABEL[0].split("–")[0])}. Den bredare
    ({AGG["balanserad3"]["n_matpunkter"]} mätpunkter) släpper den äldsta perioden och får i stället
    med nästan allt. De {len(AGG.get("excluded_names", []))} mätpunkter som saknar självklar riktning
    ingår i ingen av dem: {E(", ".join(AGG.get("excluded_names", [])))}.</p>
  </div>

  {gov_block()}

  <h3 style="margin:34px 0 8px;font-size:1.15rem">Sex mått, två paneler</h3>
  <p class="lede" style="margin-bottom:14px">Grönt är bästa värdet för respektive mått inom panelen.
  Den bredare panelen har {AGG["balanserad3"]["n_matpunkter"] - AGG["balanserad"]["n_matpunkter"]}
  mätpunkter till men saknar den äldsta perioden. {agg_verdict("balanserad3", 1)}</p>
  {agg_table("balanserad3", 1)}
  <p class="lede" style="margin:18px 0 14px">{agg_verdict("balanserad")}</p>
  {agg_table("balanserad")}

  <div class="caution" style="margin-top:26px">
    <span class="eyebrow">Vad talen inte klarar</span>
    <p><b>Panelvalet flyttar resultatet.</b> {panel_shift()} Ett sammanvägt tal
    beror alltid på vad man råkar mäta, och den här rapporten mäter inte vård- och omsorgskapacitet,
    kunskapsresultat, äldreomsorg, ungas psykiska hälsa eller rättskedjans genomströmning i närheten
    av så väl som den mäter ekonomi och brott.</p>
    <p><b>Antal och storlek svarar på olika frågor.</b> De tre första måtten räknar hur många
    mätpunkter som rör sig rätt, de tre sista väger in hur mycket. En period kan ha få men stora
    förbättringar, eller många men små. Här pekar båda sorterna åt samma håll, men det är ingen
    naturlag – när de går isär är det en upplysning och inte ett fel.</p>
    <p><b>Ingen viktning.</b> Alla mätpunkter räknas lika. Att bostadsbyggandet halveras väger lika
    mycket som att anmälda brott minskar en procent. Vilka mått som borde väga tyngst är en politisk
    fråga.</p>
    <p><b>Den pågående perioden är kortare.</b> {E(PLABEL[-1])} mäts till som längst andra kvartalet
    2026 och för {N_STALE} av serierna bara till 2024. Kortare tid betyder mindre hunnen förändring,
    vilket drar ned andelen som passerar tröskeln – antalsmåtten underskattar alltså snarast den
    pågående perioden. De standardiserade måtten räknar per år och påverkas inte.</p>
    <p><b>Och framför allt:</b> det här mäter vad som hände, inte vad någon regering orsakade.
    Finanskrisen, flyktingmottagandet 2015, pandemin, inflationsvågen och räntecykeln påverkar de
    flesta serierna mer än enskilda riksdagsbeslut.</p>
  </div>
</section>

<section aria-labelledby="h-riktning">
  <div class="sechead">
    <span class="eyebrow">Nivå eller riktning</span>
    <h2 id="h-riktning">Takt mot nivå: har kurvan vänt?</h2>
    <p class="lede">En jämförelse av nivåer missar en sak: en nedåtgående utveckling som ärvts från
    föregående period tar tid att vända, och en mätpunkt kan ha vänt till det bättre utan att ha hunnit
    tillbaka till utgångsnivån. Därför mäts också <b>takten</b> – hur många enheter per år måttet
    förbättrades inom varje period. Takten räknas alltid som förbättring per år: för sjukfrånvaro,
    utsläpp, väntetider och dödligt våld är en minskning en förbättring och ger därför ett positivt tal.
    {N_TURNED} mätpunkter har fått bättre takt trots att nivån fortfarande är sämre eller oförändrad, och
    {N_STALLED} har bättre nivå men har tappat fart.</p>
  </div>
  {matrix()}
</section>

<section aria-labelledby="h-matpunkter">
  <div class="sechead">
    <span class="eyebrow">Mätpunkt för mätpunkt</span>
    <h2 id="h-matpunkter">Vad varje serie visar</h2>
    <p class="lede">Mätpunkterna står i bokstavsordning. Varje post visar utgångsläge och slutläge för
    alla fyra perioderna, periodsnittet, takten, hur måttet är framtaget och vilka förbehåll som gäller.
    Texten beskriver framför allt de två senaste perioderna, som är rapportens fråga; diagrammet och
    tabellen bär hela historiken. Under varje diagram går alla värden och de kompletterande serierna att
    fälla ut.</p>
  </div>
  {ENTRIES}
</section>

<section aria-labelledby="h-metod">
  <div class="sechead">
    <span class="eyebrow">Metod</span>
    <h2 id="h-metod">Så är jämförelsen gjord</h2>
  </div>
  <div class="ebody">
    <div class="prose">
      <p><b>Orsaker – och gränsen för vad rapporten kan säga.</b> Under varje mätpunkt går ett avsnitt
      "Orsaker och sammanhang" att fälla ut. Det innehåller tre slags påstående som medvetet hålls
      åtskilda, eftersom de har helt olika bevisvärde. <b>Beslut i området</b> är propositioner som
      riksdagen behandlat, hämtade maskinellt ur Riksdagens öppna data och fördelade tre per
      mandatperiod. De är verifierbara fakta om vad som gjordes – men att ett beslut ligger i samma
      period som en förändring är inget som helst belägg för att det orsakade den. <b>Vad granskarna
      kommit fram till</b> är Riksrevisionens granskningsrapporter, med citat ur rapporternas egna
      sammanfattningar. Det är här det finns faktisk evidens om effekter, och den evidensen lutar
      negativt: i de granskningar rapporten citerar finner Riksrevisionen oftast att effekterna av
      statliga satsningar är svagt belagda. Ett förbehåll hör till den slutsatsen. Riksrevisionen
      väljer själv vad som granskas, och väljer där problem misstänks; rapporten citerar i sin tur
      ett urval ur de granskningarna. Att granskade satsningar oftast visar svagt belagda effekter
      säger därför lite om statliga satsningar i allmänhet, och ingenting om hur stor andel av dem
      som fungerar. <b>Omvärlden</b> är daterade händelser utanför politiken. För flera av de största
      rörelserna i rapporten – inflationschocken, pandemin, energipriserna, räntan – väger omvärlden
      tungt, och den mandatperiod som råkar innehålla återhämtningen får kredit för en rörelse
      rapporten inte kan tillskriva den.</p>
      <p><b>Partierna.</b> Varje mandatperiod visar vilka partier som satt i regeringen och vilka
      som gav stöd utanför den. Det är den enda uppgiften i rapporten som är sammanställd för hand:
      regeringsbildningar publiceras inte som statistik, och riksdagens öppna data beskriver dokument,
      inte regeringar. Uppgifterna går att kontrollera mot riksdagens och regeringens egna
      publiceringar, men inte att verifiera maskinellt som resten av materialet, och de står
      därför i ett eget block, inte i tabellerna.</p>
      <p><b>Partiernas röster redovisas per förslagspunkt.</b> Under varje listat beslut går det att
      fälla ut hur partierna röstade i det utskottsbetänkande som behandlade förslaget. Punkten är den
      enhet en omröstning faktiskt gäller, och det är därför varje punkt redovisas för sig i stället
      för ett tal för beslutet: Justitieutskottets betänkande 2022/23:JuU12 har fyra punkter och
      partilinjerna skiljer sig på varje – Socialdemokraterna röstade nej på en, ja på en annan och
      avstod på en tredje. Rapporten pekar därför aldrig ut vilken punkt som ”är” regeringens förslag.
      Det fält i datan som skulle säga det är nästan aldrig ifyllt, och att gissa vore att uppfinna
      ett svar.</p>
      <p>Underlaget är 215 betänkanden med 1012 förslagspunkter, varav 374 avgjordes med
      omröstning och 609 med acklamation. Acklamation betyder att ingen ledamot begärde
      omröstning. Det kan betyda att förslaget inte möttes av tillräckligt motstånd för att någon
      skulle kräva votering, men också att utgången var känd i förväg eller uppgjord i förhandling;
      vilket av dem det är säger materialet inte. Partilinjen är den röst flertalet av partiets närvarande ledamöter
      lade. En avvikelse redovisas bara när den är verklig – minst tre ledamöter och minst en tiondel
      av de närvarande – eftersom en enda avvikande ledamot i ett parti på hundra inte är en delad
      partilinje. Talmannen och ledamöter utan partibeteckning utgör inget parti och ingår inte.
      Två omröstningar från 2011/12 saknas helt: källan svarar med ett tomt dokument.</p>
      <p><b>Att listan inte är en lista över orsaker.</b> Besluten är valda på titelinnehåll, tre per
      mandatperiod, och rapporten har inte visat att något av dem påverkade måttet. Att se hur
      partierna röstade om ett beslut i samma sakområde som en förändring är inte att se vem som
      orsakade förändringen. Den slutsatsen bär materialet inte, och partirösterna gör den inte
      starkare – de gör bara besluten mer genomskinliga.</p>
      <p><b>Men vägen dit finns.</b> Varje beslut som listas länkar till propositionen på
      riksdagen.se, och de flesta har dessutom länken <span class="votelink"
      style="margin:0">votering och beslut →</span> direkt till utskottets betänkande. Där står
      förslagspunkterna, vilka som avgjordes med omröstning och hur varje parti röstade på var och
      en. Kopplingen mellan proposition och betänkande görs på identisk titel inom ett år, och bara
      när träffen är entydig – {N_BET} av {N_BESLUT} beslutsrader får en länk, resten ingen, eftersom
      en felaktig källhänvisning är sämre än ingen.</p>
      <p><b>Rapporten belägger inte orsakssamband.</b> Den mäter nivåer och förändringar, och kan visa
      att en förändring sammanfaller i tid med ett beslut. Att gå därifrån till att beslutet orsakade
      förändringen kräver en kontrafaktisk jämförelse som statistiken här inte innehåller. På två
      ställen ställs ändå ett svagare anspråk, och då mot tre villkor som alla tre måste hålla:
      <b>tidsordning</b> – beslutet ligger före förändringen, med marginal för att hinna få verkan;
      <b>känd mekanism</b> – vägen från beslutet till måttet är beskriven någon annanstans än i den
      här rapporten och pekar i en bestämd riktning; och <b>oberoende granskning</b> – Riksrevisionen
      eller en statlig utredning har prövat sambandet utan att avvisa det. De två mätpunkter som
      passerar är utsläppen av växthusgaser och reduktionsplikten, samt sjukfrånvaron och regelverket
      i sjukförsäkringen. Villkoren är satta här och är inte hämtade ur någon standard; de utesluter
      inte att politiken påverkat andra mått, utan säger bara var underlaget räcker för att påstå
      det. Överallt annars ska avsnittet läsas som sammanhang, inte som förklaring.</p>
      <p><b>Fyra mandatperioder.</b> Riksmötet inleds i mitten av oktober valåret, och perioderna räknas
      därför 15 oktober till 14 oktober: 2010–2014, 2014–2018, 2018–2022 och 2022–2026. De faktiska
      riksmötesöppningarna har varierat med några veckor mellan valen; ett gemensamt datum gör perioderna
      lika långa och jämförbara.</p>
      <p><b>Nollpunkt och slutläge.</b> Eftersom ingen statistikserie är dagsaktuell används den sista
      publicerade mätpunkten före skiftet som utgångsläge och periodens sista som slutläge. För
      kvartalsserier betyder det tredje kvartalet valåret, för årsserier valåret självt, för läsår det
      läsår som avslutas på våren. Periodsnittet räknas i stället på alla mätpunkter som helt ligger
      inne i perioden.</p>
      <p><b>Ojämn historik.</b> Bara {COV[0]} mätpunkter kan mätas över 2010–2014 och {COV[1]} över
      2014–2018. Där statistiken börjar inne i en period används den tidigaste mätpunkten som nollpunkt
      och rutan märks <span class="pflag" style="display:inline">delvis</span>. Där det bara finns en
      enda mätpunkt i perioden redovisas ingen förändring alls – en punkt är ingen utveckling.</p>
      <p><b>Brott i serierna.</b> Yrkesregistret har bytt produktionssystem två gånger, och de tre
      personalmätpunkterna bygger därför på tre tabeller med olika avgränsning. Serien visas hel i
      diagrammet, men en förändring beräknas aldrig över ett brott: nollpunkten flyttas i stället till
      den tidigaste mätpunkten inom samma tabell. Samma princip gäller lönestrukturstatistiken och de
      nedlagda sjukfrånvaroserierna.</p>
      <p><b>Två skalor för förändring.</b> En andel som ligger kring 80 procent mäts naturligt i
      procentenheter – en procentenhet är en rimlig storhet. En andel som ligger kring 5 procent gör
      det inte: tre tiondelars procentenhet är där en förändring på sex procent, inte en försumbar.
      Regeln är därför att <b>andelar mellan 15 och 85 procent mäts i procentenheter</b> och allt
      annat i procentuell förändring. Två undantag går före: ett mått som redan <i>är</i>
      procentenheter – en differens som sysselsättningsgapet eller ett avstånd som inflationen till
      målet – mäts alltid i procentenheter, och så gör ett mått som kan passera noll, som det
      offentliga sparandet, eftersom en relativ förändring blir meningslös kring nollpunkten.
      Gränsen för att kalla något en förändring är en halv procentenhet respektive en halv procent.</p>
      <p><b>Takt och vändning.</b> För varje period beräknas en lutning med minsta kvadratmetoden över
      periodens mätpunkter, uttryckt som förbättring per år. Skillnaden mellan den pågående periodens
      takt och den föregående avgör om utvecklingen vänt, tagit fart eller bromsat in. En äkta vändning
      kräver att takten bytt tecken, inte bara ändrat storlek.</p>
      <p><b>Tre linjer i varje diagram.</b> De faktiska mätpunkterna ligger som en tunn ljus linje.
      Ovanpå den ligger ett centrerat glidande medelvärde över ett år – för kvartals- och månadsserier
      det klassiska 2×4- respektive 2×12-filtret, som med halva vikten på ändpunkterna kan centreras
      korrekt och tar bort en årscykel exakt; för årsserier tre år. Den streckade vågräta linjen är
      <b>periodens genomsnitt</b>, en nivå per mandatperiod.</p>
      <p><b>Varför inte ett längre glidande medelvärde?</b> Ett fönster på tre eller fyra år skulle
      jämna ut konjunkturen, men det skulle också sudda ut precis det rapporten mäter: vändningarna
      vid regeringsskiftena. Ett fyraårsfönster smetar en vändning i oktober 2022 över både perioden
      före och efter, och gör den svårare att se snarare än tydligare. Den långa horisonten hämtas
      därför i stället från de streckade periodgenomsnitten, som byter nivå exakt vid maktskiftena
      i stället för att glida över dem. Vid seriens kanter normaliseras vikterna om över de mätpunkter
      som finns, så linjen når hela vägen ut men vilar på färre värden längst ut.</p>
      <p>Undersökningarna av levnadsförhållanden får ingen utjämning alls, eftersom deras mätpunkter
      är ojämnt utspridda i tiden. Alla siffror i tabeller, omdömen och takter bygger på de faktiska
      värdena, aldrig på det utjämnade.</p>
      <p><b>Fasta priser.</b> Löner, skatteintäkter, statsskuld och bostadspriser är deflaterade med
      konsumentprisindexets fastställda årsmedeltal till {BASE} års prisnivå. BNP redovisas i
      nationalräkenskapernas egna fasta priser med referensår {BASE}.</p>
      <p><b>Egna beräkningar är märkta.</b> Källtabellerna saknar i flera fall färdiga totalvärden.
      Där en summa, en andel, ett viktat medelvärde eller en kvot har räknats fram står det i rutan
      ”Så är måttet framtaget” under respektive mätpunkt. Inga värden är uppskattade eller interpolerade.</p>
      <p><b>Vad detta inte är.</b> Sambandet mellan en regerings politik och en statistikserie är inte
      utrett här. Finanskrisen, flyktingmottagandet 2015, pandemin, inflationsvågen och Riksbankens
      räntecykel påverkar flera av serierna mer än något riksdagsbeslut. Sammanställningen visar vad som
      hände, inte varför.</p>
    </div>
    <div>
      <div class="method" style="margin-top:0">
        <b>Uttaget</b>
        SCB: PxWeb API 2.0 (api.scb.se/OV0104/v2beta/api/v2) i formatet JSON-stat 2.0,
        {len(TABLES)} tabeller. Socialstyrelsen: dödsorsaksdatabasens öppna API
        (sdb.socialstyrelsen.se/api/v1/sv/dodsorsaker). SKR:s väntetidsdatabas: Kolada
        (api.kolada.se/v3), riket. Brå: tabellfiler i xlsx nedladdade från bra.se och lästa
        programmatiskt. Ingen siffra i rapporten är skriven för hand.
      </div>
      <div class="method">
        <b>Täckning per period</b>
        {"<br>".join(f"{E(PLABEL[i])}: {COV[i]} av {len(ORDER)} mätpunkter" for i in range(NP))}
      </div>
      <div class="method">
        <b>Riktning</b>
        För varje mätpunkt är det angivet vilket håll som räknas som en förbättring. Sjunkande
        sjukfrånvaro, utsläpp, självmord, dödligt våld, hatbrott, otrygghet, väntetider, arbetslöshet,
        elpriser, räntor och statsskuld räknas som bättre; stigande löner, sysselsättning, behörighet,
        personal, uppklarande, BNP, produktivitet, medellivslängd och tillit räknas som bättre.
        Medelålder, skatteintäkter, skattetryck, inkomstklyfta och bostadspriser har ingen självklar
        riktning och lämnas utan omdöme.
      </div>
    </div>
  </div>
</section>

<section aria-labelledby="h-kallor">
  <div class="sechead">
    <span class="eyebrow">Källor</span>
    <h2 id="h-kallor">Varje siffras källa</h2>
    <p class="lede">Först de {len(TABLES)} tabellerna ur SCB:s statistikdatabas – varje tabell-id länkar
    till tabellen, och uppdateringsdatumet är det SCB angav vid uttaget.</p>
  </div>
  {SRC_SCB}
  <h3 style="margin:34px 0 6px;font-size:1.15rem">Övriga statistikansvariga myndigheter</h3>
  <p class="lede" style="margin-bottom:14px">De {N_ALT} mätpunkter som inte finns hos SCB är hämtade
  direkt från den myndighet som ansvarar för statistiken.</p>
  {SRC_ALT}
</section>
</main>

<footer class="foot">
  <p>Alla siffror är hämtade maskinellt: SCB via PxWeb API 2.0, Socialstyrelsen via
  dödsorsaksdatabasens öppna API, SKR:s väntetidsdata via Kolada och Brås tabeller som nedladdade
  kalkylfiler från bra.se. Ingen siffra i rapporten är skriven för hand.</p>
  <p>Uttag gjort {DATESTR}. Rapporten byggs av skripten i <span class="mono">pipeline/</span>;
  perioderna definieras i <span class="mono">config/periods.json</span>.</p>
</footer>
</div>

<script>window.__DATA__={PAYLOAD};</script>
<script>{JS}</script>
"""

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
# The standalone page lives in docs/ because that is where GitHub Pages serves
# from; the fragment is a publishing intermediate and stays out of the repo.
DOCS = os.path.join(ROOT, "docs")
OUT = os.path.join(ROOT, "out")

FAVICON = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Crect width='64' height='64' rx='8' fill='%232a78d6'/%3E"
           "%3Crect x='12' y='34' width='8' height='18' fill='%23fff'/%3E"
           "%3Crect x='24' y='24' width='8' height='28' fill='%23fff'/%3E"
           "%3Crect x='36' y='16' width='8' height='36' fill='%23fff'/%3E"
           "%3Crect x='48' y='28' width='4' height='24' fill='%23fff'/%3E%3C/svg%3E")
LD = json.dumps({
    "@context": "https://schema.org", "@type": "Dataset",
    "name": TITLE, "description": DESC, "inLanguage": "sv-SE",
    "temporalCoverage": f"{PMETA[0]['start']}/{PMETA[-1]['slut']}",
    "variableMeasured": [IND[k]["name"] for k in ORDER],
    "creator": [{"@type": "GovernmentOrganization", "name": n} for n in
                ["Statistiska centralbyrån", "Brottsförebyggande rådet",
                 "Sveriges Kommuner och Regioner", "Socialstyrelsen"]],
    "isBasedOn": sorted({TABLES[t]["url"] for k in ORDER
                         for t in (IND[k].get("tables") or []) if t in TABLES}),
}, ensure_ascii=False, separators=(",", ":"))

STANDALONE = f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{E(TITLE)}</title>
<meta name="description" content="{E(DESC)}">
<meta name="generator" content="pipeline/render.py">
<meta name="theme-color" content="#e8eae4" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#141611" media="(prefers-color-scheme: dark)">
<meta property="og:type" content="article">
<meta property="og:locale" content="sv_SE">
<meta property="og:title" content="{E(TITLE)}">
<meta property="og:description" content="{E(DESC)}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="{FAVICON}">
{FONTS}
<style>{CSSOUT}</style>
<script type="application/ld+json">{LD}</script>
</head>
<body>
{BODY}</body>
</html>
"""

FRAGMENT = f"""<title>{E(TITLE)}</title>
{FONTS}
<style>{CSSOUT}</style>

{BODY}"""

open(os.path.join(DOCS, "index.html"), "w", encoding="utf-8").write(STANDALONE)
open(os.path.join(OUT, "artifact.html"), "w", encoding="utf-8").write(FRAGMENT)
print(f"skrev docs/index.html ({len(STANDALONE)} tecken, fristående sida)")
print(f"skrev out/artifact.html ({len(FRAGMENT)} tecken, fragment för publicering)")
print(len(ORDER), "mätpunkter | täckning", COV)

