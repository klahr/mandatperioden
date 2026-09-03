"""Fetch every Statistics Sweden measure from the statistical database
(PxWeb API 2.0). The time window covers four parliamentary terms: 2010-14,
2014-18, 2018-22 and 2022-26.

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

import json, os
import scb_api as px
import jsonstat as js
from collections import defaultdict

IND, TBL = [], {}
# All fetching in this file happens inside the arguments to add(), so requests
# made since the previous call belong to the measure being added now.
_seen = 0
def add(**kw):
    global _seen
    kw["reqs"] = px.LOG[_seen:]
    _seen = len(px.LOG)
    IND.append(kw)

def tbl(tid):
    if tid not in TBL:
        mm = px.m(tid)
        TBL[tid] = {"id": tid, "label": mm.get("label"), "source": mm.get("source"),
                    "updated": mm.get("updated"),
                    "url": f"https://www.statistikdatabasen.scb.se/pxweb/sv/ssd/START__{tid}/"}
    return tid

def clean(tid, vc):
    out = {}
    for k, v in vc.items():
        out[k] = px.allcodes(tid, k) if v is None else px.valid(tid, k, v)
    return out

def s(tid, vc, tv="Tid"):
    tbl(tid)
    return js.series(px.data(tid, clean(tid, vc)), tv)

def summ(tid, vc, tv="Tid"):
    tbl(tid)
    out, seen = defaultdict(float), set()
    for code, lab, v in js.flat(px.data(tid, clean(tid, vc))):
        if v is None: continue
        out[code[tv]] += v; seen.add(code[tv])
    return {k: round(v, 4) for k, v in out.items() if k in seen}

YEARS = [str(y) for y in range(2008, 2027)]
Y = ",".join(YEARS)
Q = ",".join(f"{y}K{q}" for y in range(2008, 2027) for q in range(1, 5))
M = ",".join(f"{y}M{m:02d}" for y in range(2008, 2027) for m in range(1, 13))
LAS = ",".join(f"{y}/{str(y+1)[2:]}" for y in range(2008, 2026))

POP_Y = summ("TAB5890", {"Alder": "tot", "Kon": "1,2", "ContentsCode": "0000053A", "Tid": Y})
POP_Y.update(summ("TAB6667", {"Alder": "TotSA", "Kon": "TotSa", "ContentsCode": "0000088D", "Tid": "2025"}))
POP_Y = {k: int(v) for k, v in POP_Y.items()}
def per100k(ser, nd=1):
    return {k: round(v / POP_Y[k[:4]] * 1e5, nd) for k, v in ser.items()
            if v is not None and k[:4] in POP_Y}

KPI = s("TAB4352", {"ContentsCode": "000000KL", "Tid": Y})
BASE = "2025"
def real(nom, nd=1):
    return {y: round(v * KPI[BASE] / KPI[y], nd) for y, v in nom.items() if y in KPI and v is not None}

mean_nom = {**s("TAB4272", {"Sektor": "0", "Yrkesgrupp12": "0000", "Kon": "1+2",
                            "ContentsCode": "000000D5", "Tid": Y}),
            **s("TAB5709", {"Sektor": "0", "Yrkesgrupp12": "0000", "Kon": "1+2",
                            "ContentsCode": "000007AW", "Tid": Y})}
med_nom = {**s("TAB4272", {"Sektor": "0", "Yrkesgrupp12": "0000", "Kon": "1+2",
                           "ContentsCode": "000000D6", "Tid": Y}),
           **s("TAB5709", {"Sektor": "0", "Yrkesgrupp12": "0000", "Kon": "1+2",
                           "ContentsCode": "000007AX", "Tid": Y})}
add(key="realmedellon", series=real(mean_nom),
    extra={"Nominell månadslön, kr": mean_nom, "KPI, årsmedeltal (1980=100)": KPI})
add(key="realmedianlon", series=real(med_nom), extra={"Nominell medianlön, kr": med_nom})

AKU = {"TypData": "SR_DATA", "Kon": "1+2", "ContentsCode": "000007V3"}
add(key="syssgrad",
    series=s("TAB6516", {**AKU, "Arbetskraftstillh": "SYSP", "Alder": "tot20-64", "Tid": Q}),
    extra={"Arbetslöshetstal 15–74 år, procent (säsongrensat)":
               s("TAB6516", {**AKU, "Arbetskraftstillh": "ALÖSP", "Alder": "tot15-74", "Tid": Q}),
           "Arbetskraftstal 20–64 år, procent (säsongrensat)":
               s("TAB6516", {**AKU, "Arbetskraftstillh": "IAKRP", "Alder": "tot20-64", "Tid": Q})})
add(key="arbetsloshet",
    series=s("TAB6516", {**AKU, "Arbetskraftstillh": "ALÖSP", "Alder": "tot15-74", "Tid": Q}),
    extra={"Arbetslöshet 15–24 år, procent":
               s("TAB6516", {**AKU, "Arbetskraftstillh": "ALÖSP", "Alder": "15-24", "Tid": Q}),
           "Arbetskraftstal 20–64 år, procent":
               s("TAB6516", {**AKU, "Arbetskraftstillh": "IAKRP", "Alder": "tot20-64", "Tid": Q})})
sys_inr = s("TAB6528", {"Arbetskraftstillh": "SYSP", "InrikesUtrikes": "13", "TypData": "SR_DATA",
                        "Kon": "1+2", "Alder": "tot20-64", "ContentsCode": "000007VF", "Tid": Q})
sys_utr = s("TAB6528", {"Arbetskraftstillh": "SYSP", "InrikesUtrikes": "23", "TypData": "SR_DATA",
                        "Kon": "1+2", "Alder": "tot20-64", "ContentsCode": "000007VF", "Tid": Q})
add(key="sysselsattningsgap",
    series={q: round(sys_inr[q] - sys_utr[q], 1) for q in sys_inr
            if q in sys_utr and sys_inr[q] is not None and sys_utr[q] is not None},
    extra={"Sysselsättningsgrad, inrikes födda, procent": sys_inr,
           "Sysselsättningsgrad, utrikes födda, procent": sys_utr,
           "Arbetslöshet, utrikes födda 15–74 år, procent":
               s("TAB6528", {"Arbetskraftstillh": "ALÖSP", "InrikesUtrikes": "23",
                             "TypData": "SR_DATA", "Kon": "1+2", "Alder": "tot15-74",
                             "ContentsCode": "000007VF", "Tid": Q})})

sjk = s("TAB5236", {"Alder": "S", "Kon": "2", "ContentsCode": "0000034F", "Tid": Y})
sjm = s("TAB5236", {"Alder": "S", "Kon": "1", "ContentsCode": "0000034F", "Tid": Y})
ages1664 = ",".join(str(a) for a in range(16, 65))
popk = summ("TAB5890", {"Alder": ages1664, "Kon": "2", "ContentsCode": "0000053A", "Tid": Y})
popm = summ("TAB5890", {"Alder": ages1664, "Kon": "1", "ContentsCode": "0000053A", "Tid": Y})
popk.update(summ("TAB6667", {"Alder": ages1664, "Kon": "2", "ContentsCode": "0000088D", "Tid": "2025"}))
popm.update(summ("TAB6667", {"Alder": ages1664, "Kon": "1", "ContentsCode": "0000088D", "Tid": "2025"}))
add(key="sjukfranvaro",
    series={y: round((sjk[y]*popk[y] + sjm[y]*popm[y]) / (popk[y]+popm[y]), 2)
            for y in sjk if y in popk and y in popm and sjk[y] is not None and sjm[y] is not None},
    extra={"Sjukpenningtal, kvinnor": sjk, "Sjukpenningtal, män": sjm,
           "Andel sjukfrånvarande, procent (KS, kvartal, nedlagd efter 2023K4)":
               s("TAB4295", {"Kon": "1+2", "Sektor": "010", "ContentsCode": "000000G7", "Tid": Q}),
           "Andel sjukfrånvaro, procent (Anställningar, månad, från 2024)":
               s("TAB6652", {"NyckeltalSCB": "Anst03", "ContentsCode": "00000875", "Tid": M})})

def beh(kon, cc, prog="yrk"):
    return s("TAB5274", {"Program": prog, "SvUtlBakgrund": "SA", "Kon": kon,
                         "ContentsCode": cc, "Tid": LAS})
a_f, a_p = beh("2", "0000036E"), beh("1", "0000036E")
p_f, p_p = beh("2", "0000036F"), beh("1", "0000036F")
gymn = {}
for t in a_f:
    if p_f.get(t) and p_p.get(t) and a_f.get(t) is not None and a_p.get(t) is not None:
        lev = a_f[t]/p_f[t]*100 + a_p[t]/p_p[t]*100
        gymn[t] = round((a_f[t]+a_p[t])/lev*100, 1)
add(key="gymnasiebehorighet", series=gymn,
    extra={"Andel flickor, procent": p_f, "Andel pojkar, procent": p_p,
           "Behöriga till naturvetenskaps-/teknikprogram, flickor, procent": beh("2", "0000036F", "nt"),
           "Behöriga till naturvetenskaps-/teknikprogram, pojkar, procent": beh("1", "0000036F", "nt")})

def larare(tid, cc_tot, cc_ex):
    a = summ(tid, {"Lararkategori": "01", "Kon": "1,2", "ContentsCode": cc_tot, "Tid": Y})
    b = summ(tid, {"Lararkategori": "01", "Kon": "1,2", "ContentsCode": cc_ex, "Tid": Y})
    return {t: round(b[t]/a[t]*100, 1) for t in a if a.get(t) and b.get(t)}, a, b
gr, gr_a, gr_b = larare("TAB5351", "000003E6", "000003EC")
mg = px.m("TAB5352")["dimension"]["ContentsCode"]["category"]["label"]
cc_t = [k for k, v in mg.items() if v == "Antal årsarbetare"][0]
cc_e = [k for k, v in mg.items() if "pedagogisk högskoleexamen" in v and "Därav" in v][0]
gy, _, _ = larare("TAB5352", cc_t, cc_e)
add(key="behoriga_larare", series=gr,
    extra={"Gymnasieskolan, procent": gy, "Årsarbetare, lärare i grundskolan": gr_a,
           "Därav med pedagogisk högskoleexamen": gr_b})

SNI = px.allcodes("TAB4349", "SNI2007")
add(key="vaxthusgaser",
    series=summ("TAB4349", {"SNI2007": SNI, "AmneMiljo": "GHG", "ContentsCode": "000000KH", "Tid": Q}),
    extra={"Fossil koldioxid, kiloton":
               summ("TAB4349", {"SNI2007": SNI, "AmneMiljo": "CO2", "ContentsCode": "000000KH", "Tid": Q})})

YM = "2021,2022,2023,2024,2025,2026"
add(key="fortroende",
    series=s("TAB5874", {"Region": "00", "MedbVariabel15": "1200", "MedBakgrund": "000",
                         "ContentsCode": "000005D0", "Tid": YM}),
    extra={"Förtroende för politiker i riksdagen, procent":
               s("TAB5873", {"Region": "00", "MedbVariabel14": "1190", "MedBakgrund": "000",
                             "ContentsCode": "000005CN", "Tid": YM}),
           "Förtroende för kommunens politiker, procent":
               s("TAB5873", {"Region": "00", "MedbVariabel14": "1180", "MedBakgrund": "000",
                             "ContentsCode": "000005CN", "Tid": YM}),
           "Upplever att kommunens politiker är ansvarstagande, procent":
               s("TAB5871", {"Region": "00", "MedbVariabel12": "1120", "MedBakgrund": "000",
                             "ContentsCode": "000005BX", "Tid": YM})})

AGE = {"15-29": (15, 29), "30-44": (30, 44), "45-59": (45, 59), "60-74": (60, 74), "75+": (75, 110)}
tbl("TAB5243")
rates = {}
for c, l, v in js.flat(px.data("TAB5243", clean("TAB5243", {"Dodsorsak": "sjalv",
        "Alder": ",".join(AGE), "Kon": "1,2", "ContentsCode": "0000034O", "Tid": Y}))):
    rates[(c["Tid"], c["Alder"], c["Kon"])] = v
POP = {}
for a, (lo, hi) in AGE.items():
    ags = [str(x) for x in range(lo, min(hi, 109) + 1)] + (["110+"] if hi >= 110 else [])
    for kon in ("1", "2"):
        POP[(a, kon)] = summ("TAB5890", {"Alder": ",".join(ags), "Kon": kon,
                                         "ContentsCode": "0000053A", "Tid": Y})
suic = {}
for y in sorted({k[0] for k in rates}):
    num = den = 0.0; ok = True
    for a in AGE:
        for kon in ("1", "2"):
            r, p = rates.get((y, a, kon)), POP[(a, kon)].get(y)
            if r is None or p is None: ok = False; break
            num += r * p / 1e5; den += p
    if ok and den: suic[y] = round(num / den * 1e5, 1)
add(key="sjalvmord", series=suic,
    extra={"Dödstal, män 15–29 år": {y: rates.get((y, "15-29", "1")) for y in suic},
           "Dödstal, män 45–59 år": {y: rates.get((y, "45-59", "1")) for y in suic},
           "Dödstal, kvinnor 45–59 år": {y: rates.get((y, "45-59", "2")) for y in suic}})

add(key="medelalder", series=s("TAB4375", {"Kon": "1+2", "ContentsCode": "000000MD", "Tid": Y}),
    extra={"Medianålder, år": s("TAB4375", {"Kon": "1+2", "ContentsCode": "000000ME", "Tid": Y})})

def yrke(codes):
    bas = summ("TAB4355", {"Yrke2012": codes, "Fodelseregion": None, "Kon": "1,2",
                           "ContentsCode": "000006XO", "Tid": Y})
    rams = summ("TAB3103", {"Yrke2012": codes, "Fodelseregion": None, "Kon": "1,2",
                            "ContentsCode": "000001TV", "Tid": Y})
    old = summ("TAB4456", {"Yrke2012": codes, "Fodelseregion": None, "Kon": "1,2",
                           "ContentsCode": "000000RI", "Tid": Y})
    ser = {k: int(round(v)) for k, v in {**old, **rams, **bas}.items()}
    return ser, {k: int(round(v)) for k, v in bas.items()}, \
           {k: int(round(v)) for k, v in rams.items()}, {k: int(round(v)) for k, v in old.items()}
for key, codes in [("lakare", "221"), ("sjukskoterskor", "222,223"), ("larare", "231,232,233,234")]:
    ser, bas, rams, old = yrke(codes)
    raw = dict(ser)
    ser = per100k(ser)
    bas, rams, old = per100k(bas), per100k(rams), per100k(old)
    # The occupational register changed production system twice; a change may
    # only be computed within one segment.
    add(key=key, series=ser,
        segments=[sorted(old), sorted(k for k in rams if k not in bas), sorted(bas)],
        extra={"Antal anställda (utan befolkningsjustering)": raw,
               "BAS-baserad tabell, per 100 000 inv (2020–2024)": bas,
               "RAMS-baserad tabell, 16–64 år, per 100 000 inv (2019–2021)": rams,
               "Äldre tabell, 16–64 år, per 100 000 inv (2014–2018)": old})

add(key="trygghet",
    series=s("TAB6089", {"Indikator": "T374", "Redovisningsgrupp": "16+", "Kon": "00",
                         "ContentsCode": "000005YU", "Tid": None}),
    extra={"Utsatt för hot eller våld, procent":
               s("TAB6089", {"Indikator": "T366", "Redovisningsgrupp": "16+", "Kon": "00",
                             "ContentsCode": "000005YU", "Tid": None}),
           "Avstått från att gå ut, lång serie från 1988, procent":
               s("TAB6453", {"Indikator": "T374", "Alder": "16+", "Kon": "00",
                             "ContentsCode": "000007QF", "Tid": None})})
add(key="psykisk_halsa",
    series=s("TAB6676", {"Indikator": "H700", "Redovisningsgrupp": "16+", "Kon": "00",
                         "ContentsCode": "00000897", "Tid": None}),
    extra={"Pågående sjukfall pga depressiv episod, antal (kvartal)":
               summ("TAB5238", {"Kon": "1,2", "ContentsCode": "0000034C", "Tid": Q}),
           "Pågående sjukfall pga stressreaktioner, antal (månad)":
               summ("TAB679", {"Kon": "1,2", "ContentsCode": "0000028O", "Tid": M})})

bnp = s("TAB4553", {"Anvandningstyp": "BNPM", "ContentsCode": "NR0103CE", "Tid": Q})
bnp_lop = s("TAB4553", {"Anvandningstyp": "BNPM", "ContentsCode": "NR0103CG", "Tid": Q})
qmid = {f"{y}K{q}": f"{y}M{(q-1)*3+2:02d}" for y in range(2008, 2027) for q in range(1, 5)}
ages_all = ",".join([str(a) for a in range(0, 100)] + ["100+"])
need = ",".join(sorted(set(qmid.values())))
pm = summ("TAB5444", {"Region": "00", "Alder": ages_all, "Kon": "1,2",
                      "ContentsCode": "000003O5", "Tid": need})
pm.update(s("TAB6471", {"Region": "00", "Alder": "TotSA", "Kon": "TotSa",
                        "ContentsCode": "000007SF", "Tid": need}))
bnp_pc = {q: round(bnp[q] * 1e6 / pm[qmid[q]]) for q in bnp
          if qmid.get(q) in pm and bnp[q] is not None}
bnp_lop_pc = {q: round(bnp_lop[q] * 1e6 / pm[qmid[q]]) for q in bnp_lop
              if qmid.get(q) in pm and bnp_lop[q] is not None}
add(key="bnp", series=bnp_pc,
    extra={"BNP totalt, mnkr (fasta priser, utan befolkningsjustering)": bnp,
           "Folkmängd mitt i kvartalet": {q: pm[qmid[q]] for q in bnp if qmid.get(q) in pm},
           "BNP till marknadspris, löpande priser (mnkr)": bnp_lop})
add(key="bnp_nominell", series=bnp_lop_pc,
    extra={"BNP totalt, mnkr (löpande priser, utan befolkningsjustering)": bnp_lop,
           "BNP i fasta priser (referensår 2025), mnkr": bnp,
           "Implicit prisnivå, index 2022K3=100":
               {q: round(bnp_lop[q]/bnp[q] / (bnp_lop["2022K3"]/bnp["2022K3"]) * 100, 1)
                for q in bnp if q in bnp_lop and bnp.get(q)}})
timmar = s("TAB3122", {"SNI2007": "0005", "ContentsCode": "NR0103CJ", "Tid": Q})
add(key="produktivitet",
    series={q: round(bnp[q] * 1e6 / (timmar[q] * 1e4), 1)
            for q in timmar if q in bnp and timmar.get(q) and bnp.get(q)},
    extra={"Arbetade timmar totalt, 10 000-tal (säsongrensat)": timmar,
           "Arbetade timmar i näringslivet, 10 000-tal":
               s("TAB3122", {"SNI2007": "A01-T98", "ContentsCode": "NR0103CJ", "Tid": Q})})

skatt_nom = s("TAB1892", {"Skattetyp": "190", "ContentsCode": "000000TE", "Tid": Y})
add(key="skatteintakter", series=real(skatt_nom, 0),
    extra={"Totala skatteintäkter per invånare, kr (2025 års priser)":
               {y: round(v * 1e6 / POP_Y[y]) for y, v in real(skatt_nom, 0).items() if y in POP_Y},
           "Totala skatteintäkter, löpande priser (mnkr)": skatt_nom,
           "Offentliga sektorns skatteintäkter, löpande priser (mnkr)":
               s("TAB1892", {"Skattetyp": "192", "ContentsCode": "000000TE", "Tid": Y})})
bnp_ar = s("TAB121", {"Skattetyp": "101", "ContentsCode": "000000T8", "Tid": Y})
add(key="skattetryck", series=s("TAB121", {"Skattetyp": "102", "ContentsCode": "000000SP", "Tid": Y}),
    extra={"Totala skatter, mnkr (löpande priser)":
               s("TAB121", {"Skattetyp": "102", "ContentsCode": "000000T8", "Tid": Y}),
           "BNP till marknadspris, mnkr (löpande priser)": bnp_ar,
           "Skatter på produktion och import, mnkr":
               s("TAB121", {"Skattetyp": "201", "ContentsCode": "000000T8", "Tid": Y}),
           "Löpande inkomst- och förmögenhetsskatter, mnkr":
               s("TAB121", {"Skattetyp": "203", "ContentsCode": "000000T8", "Tid": Y}),
           "Obligatoriska sociala avgifter, mnkr":
               s("TAB121", {"Skattetyp": "204", "ContentsCode": "000000T8", "Tid": Y})})

statsskuld = s("TAB6378", {"Marknad": "SSTot", "ContentsCode": "000007J7", "Tid": M})
maastricht = s("TAB5045", {"Sektor": "S13", "Kontopost": "FL01N", "ContentsCode": "000002KJ", "Tid": Q})
ss_kvot = {}
for y in YEARS:
    mm = [k for k in statsskuld if k.startswith(y + "M") and statsskuld[k] is not None]
    if mm and bnp_ar.get(y):
        ss_kvot[y] = round(statsskuld[f"{y}M12" if f"{y}M12" in mm else max(mm)] / bnp_ar[y] * 100, 1)
bnp_r4, qs = {}, sorted(bnp_lop)
for i in range(3, len(qs)):
    w = [bnp_lop[qs[j]] for j in range(i-3, i+1)]
    if all(v is not None for v in w): bnp_r4[qs[i]] = sum(w)
lastq = max(bnp_r4)
if lastq.startswith("2026"):
    mm = [k for k in statsskuld if k.startswith("2026M") and statsskuld[k] is not None]
    if mm: ss_kvot["2026"] = round(statsskuld[max(mm)] / bnp_r4[lastq] * 100, 1)
add(key="statsskuld", series=ss_kvot,
    extra={"Statsskulden, mnkr (månad)": statsskuld,
           "Statsskulden i 2025 års priser, mnkr":
               {k: round(v * KPI[BASE] / KPI[k[:4]]) for k, v in statsskuld.items()
                if v is not None and k[:4] in KPI},
           "Maastrichtskulden, procent av BNP (rullande fyra kvartal)":
               {q: round(maastricht[q] / bnp_r4[q] * 100, 1) for q in maastricht
                if q in bnp_r4 and maastricht[q] is not None},
           "Maastrichtskulden, mnkr (kvartal)": maastricht})

AGES = px.valid("TAB2542", "Alder", [str(a) for a in range(0, 110)] + ["110+"])
tbl("TAB2542")
def lt(cc):
    out = {}
    for c, l, v in js.flat(px.data("TAB2542", clean("TAB2542",
            {"Kon": "1,2", "Alder": AGES, "ContentsCode": cc, "Tid": Y}))):
        out[(c["Tid"], c["Alder"], c["Kon"])] = v
    return out
DEAD, EXPO = lt("BE0101A§"), lt("BE0101AW")
ALIST = AGES.split(",")
def e0(year):
    mx = []
    for a in ALIST:
        d = sum(DEAD.get((year, a, k)) or 0 for k in ("1", "2"))
        e = sum(EXPO.get((year, a, k)) or 0 for k in ("1", "2"))
        if e <= 0: return None
        mx.append(d / e)
    l, T = 100000.0, 0.0
    for i, mv in enumerate(mx):
        if i == len(mx) - 1:
            T += l / mv if mv > 0 else 0; break
        dd = l * (mv / (1 + 0.5 * mv)); T += l - 0.5 * dd; l -= dd
        if l <= 0: break
    return round(T / 100000.0, 2)
mll = {y: e0(y) for y in YEARS}
add(key="medellivslangd", series={k: v for k, v in mll.items() if v is not None},
    extra={"Medellivslängd, kvinnor": s("TAB2542", {"Kon": "2", "Alder": "0", "ContentsCode": "BE0101A$", "Tid": Y}),
           "Medellivslängd, män": s("TAB2542", {"Kon": "1", "Alder": "0", "ContentsCode": "BE0101A$", "Tid": Y}),
           "Återstående medellivslängd vid 65 år, kvinnor": s("TAB2542", {"Kon": "2", "Alder": "65", "ContentsCode": "BE0101A$", "Tid": Y}),
           "Återstående medellivslängd vid 65 år, män": s("TAB2542", {"Kon": "1", "Alder": "65", "ContentsCode": "BE0101A$", "Tid": Y})})

kpif = s("TAB6590", {"ContentsCode": "000007ZM", "Tid": M})
add(key="inflation",
    series={k: round(abs(v - 2.0), 2) for k, v in kpif.items() if v is not None},
    extra={"KPIF, förändring på tolv månader, procent": kpif,
           "KPIF, index 2020=100": s("TAB6590", {"ContentsCode": "000007ZN", "Tid": M}),
           "KPI, fastställda årsmedeltal (1980=100)": KPI})

def ink(cc, typ="DispInkExkl"):
    return s("TAB1121", {"Region": "00", "InkomstTyp": typ, "ContentsCode": cc, "Tid": Y})
add(key="disp_inkomst", series=ink("000006R7"),
    extra={"Medelvärde, tkr": ink("000006Q1"), "P90/P10": ink("000006RD"),
           "Disponibel inkomst inkl. kapitalvinst, median tkr": ink("000006R7", "DispInkInkl")})
add(key="inkomstklyfta", series=ink("000006PO"),
    extra={"P90/P10": ink("000006RD"), "P80/P20": ink("000006RB"),
           "Hög ekonomisk standard, procent": ink("000006PS"),
           "Gini inkl. kapitalvinst": ink("000006PO", "DispInkInkl")})
bb = summ("TAB6249", {"Kon": "5+6", "Alder": "0-17", "BakgrundSvUt": "TotalC",
                      "UtbNivaForalder": "30", "ContentsCode": "000006G0", "Tid": Y})
bt = summ("TAB6249", {"Kon": "5+6", "Alder": "0-17", "BakgrundSvUt": "TotalC",
                      "UtbNivaForalder": "30", "ContentsCode": "000006G1", "Tid": Y})
add(key="lag_ekonomisk_standard", series=ink("000006PT"),
    extra={"Fattigdomsgapet, procent": ink("000006PN"),
           "Barn 0–17 år i familjer med ekonomiskt bistånd, procent":
               {k: round(bb[k]/bt[k]*100, 1) for k in bb if bt.get(k)},
           "Hushåll 18–64 år med ekonomiskt bistånd, andel av alla":
               s("TAB5123", {"Hushallstyp": "tot", "ContentsCode": "000002UW", "Tid": Y})})

_bo = {k: int(v) for k, v in summ("TAB2538", {"Region": "00", "Hustyp": "FLERBO,SMÅHUS",
                                              "ContentsCode": "BO0101A5", "Tid": Y}).items()}
add(key="bostadsbyggande", series=per100k(_bo),
    extra={"Färdigställda lägenheter, antal (utan befolkningsjustering)": _bo,
           "Flerbostadshus": s("TAB2538", {"Region": "00", "Hustyp": "FLERBO", "ContentsCode": "BO0101A5", "Tid": Y}),
           "Småhus": s("TAB2538", {"Region": "00", "Hustyp": "SMÅHUS", "ContentsCode": "BO0101A5", "Tid": Y})})
fpi = s("TAB1150", {"Region": "00", "ContentsCode": "BO0501K2", "Tid": Q})
add(key="bostadspriser",
    series={q: round(v * KPI[BASE] / KPI[q[:4]], 1) for q, v in fpi.items()
            if v is not None and q[:4] in KPI},
    extra={"Fastighetsprisindex, löpande priser (1981=100)": fpi,
           "Fastighetsprisindex, Stor-Stockholm, löpande priser":
               s("TAB1150", {"Region": "0010", "ContentsCode": "BO0501K2", "Tid": Q}),
           "Fastighetsprisindex, Stor-Göteborg, löpande priser":
               s("TAB1150", {"Region": "0020", "ContentsCode": "BO0501K2", "Tid": Q})})
bol = s("TAB5783", {"Referenssektor": "1", "Motpartssektor": "2c", "Avtal": "0200",
                    "Rantebindningstid": "1", "ContentsCode": "000004ZW", "Tid": M})
add(key="bolanerantor", series={k: round(v, 2) for k, v in bol.items() if v is not None},
    extra={"Ränta på nya och omförhandlade avtal, procent":
               s("TAB5783", {"Referenssektor": "1", "Motpartssektor": "2c", "Avtal": "0100",
                             "Rantebindningstid": "1", "ContentsCode": "000004ZW", "Tid": M}),
           "Ränta på nya avtal med rörlig ränta (t.o.m. 3 mån), procent":
               s("TAB5783", {"Referenssektor": "1", "Motpartssektor": "2c", "Avtal": "0100",
                             "Rantebindningstid": "1.1.1", "ContentsCode": "000004ZW", "Tid": M})})

spar = s("TAB6735", {"Delsektor": "S13", "ContentsCode": "000008E3", "Tid": Y})
add(key="offentligt_sparande",
    series={y: round(v / bnp_ar[y] * 100, 2) for y, v in spar.items()
            if v is not None and bnp_ar.get(y)},
    extra={"Finansiellt sparande, mnkr": spar,
           "Offentliga sektorns totala inkomster, mnkr":
               s("TAB6735", {"Delsektor": "S13", "ContentsCode": "000008E5", "Tid": Y}),
           "Offentliga sektorns totala utgifter, mnkr":
               s("TAB6735", {"Delsektor": "S13", "ContentsCode": "000008E7", "Tid": Y})})

fk = s("TAB5615", {"Myndighet": "OFM", "AndamalCOFOG": "02", "ContentsCode": "00000417", "Tid": Y})
fi = s("TAB5619", {"Myndighet": "OFM", "AndamalCOFOG": "02", "ContentsCode": "000004BV", "Tid": Y})
ft = {y: (fk.get(y) or 0) + (fi.get(y) or 0) for y in fk if fk.get(y) is not None}
add(key="forsvar", series={y: round(v / bnp_ar[y] * 100, 2) for y, v in ft.items() if bnp_ar.get(y)},
    extra={"Konsumtionsutgifter för försvar, mnkr": fk,
           "Fasta bruttoinvesteringar i försvar, mnkr": fi,
           "Försvarsutgifter totalt, mnkr": ft,
           "Militärt försvar, konsumtionsutgifter, mnkr":
               s("TAB5615", {"Myndighet": "OFM", "AndamalCOFOG": "021", "ContentsCode": "00000417", "Tid": Y})})

EL = ["SE1", "SE2", "SE3", "SE4"]
el_area = {o: s("TAB3819", {"Avtalstyp": "rorligt", "Elomrade": o, "Kundkategori": "3",
                            "ContentsCode": "000003GO", "Tid": M}) for o in EL}
el_mean = {}
for t in el_area["SE3"]:
    vals = [el_area[o].get(t) for o in EL]
    if all(v is not None for v in vals): el_mean[t] = round(sum(vals)/4, 1)
add(key="elpriser", series=el_mean,
    extra={**{f"Elområde {o}, öre/kWh": el_area[o] for o in EL},
           "Elnätspriser, öre/kWh exkl. skatter (1 januari)":
               s("TAB3950", {"Kundkategori": "3", "Viktat": "viktat",
                             "ContentsCode": "000006QI", "Tid": Y})})

# Fetched once, attached separately to each measure that uses them.
SHARED = [r for r in px.LOG
          if r["table"] == "TAB4352"
          or (r["table"] in ("TAB5890", "TAB6667")
              and r["body"]["selection"][0]["valueCodes"] in (["tot"], ["TotSA"]))]
json.dump({"requests": px.LOG, "shared": SHARED},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data",
                            "requests_scb.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
json.dump({"base_year": BASE, "kpi": KPI, "pop": POP_Y, "indicators": IND, "tables": TBL},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("SCB-mätpunkter:", len(IND), "| tabeller:", len(TBL))
for i in IND:
    ser = {k: v for k, v in sorted(i["series"].items()) if v is not None}
    ks = list(ser)
    print(f'  {i["key"]:24s} n={len(ser):4d}  {ks[0] if ks else "-":9s} .. {ks[-1] if ks else "-"}')
