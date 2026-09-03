"""Client for Statistics Sweden's PxWeb 2.0 API, with a file cache and a
request log.

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

import json, urllib.request, urllib.parse, os, time, hashlib
BASE = "https://api.scb.se/OV0104/v2beta/api/v2"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
os.makedirs(CACHE, exist_ok=True)
def get(path, params=None):
    url = BASE + path + ("?" + urllib.parse.urlencode(params, doseq=True) if params else "")
    fn = os.path.join(CACHE, hashlib.sha256(url.encode()).hexdigest()[:24] + ".json")
    if os.path.exists(fn):
        return json.load(open(fn, encoding="utf-8"))
    for a in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mandate-stats/1.0"})
            d = json.load(urllib.request.urlopen(req, timeout=90)); break
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} {url}\n  {e.read().decode('utf-8','replace')[:200]}") from None
        except Exception:
            if a == 3: raise
            time.sleep(3*(a+1))
    json.dump(d, open(fn,"w",encoding="utf-8"), ensure_ascii=False); time.sleep(0.3)
    return d
LOG = []
def _log(method, url, table, body=None):
    # Repeats included; duplicates are removed at render time, so each measure
    # carries the requests it actually made.
    LOG.append({"method": method, "url": url, "table": table, "body": body})

_M = {}
def m(tid):
    if tid not in _M: _M[tid] = get(f"/tables/{tid}/metadata", {"lang":"sv"})
    return _M[tid]
def span(tid):
    t = list(m(tid)["dimension"]["Tid"]["category"]["label"])
    return t[0], t[-1]

def post(path, params, body):
    url = BASE + path + "?" + urllib.parse.urlencode(params, doseq=True)
    raw = json.dumps(body, ensure_ascii=False, sort_keys=True)
    fn = os.path.join(CACHE, hashlib.sha256((url+raw).encode()).hexdigest()[:24] + ".json")
    if os.path.exists(fn):
        return json.load(open(fn, encoding="utf-8"))
    for a in range(4):
        try:
            req = urllib.request.Request(url, data=raw.encode("utf-8"), method="POST",
                    headers={"Content-Type": "application/json",
                             "User-Agent": "mandate-stats/1.0"})
            d = json.load(urllib.request.urlopen(req, timeout=120)); break
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code} POST {url}\n  body={raw[:200]}\n  "
                               f"{e.read().decode('utf-8','replace')[:300]}") from None
        except Exception:
            if a == 3: raise
            time.sleep(3*(a+1))
    json.dump(d, open(fn,"w",encoding="utf-8"), ensure_ascii=False); time.sleep(0.3)
    return d

def data(tid, valuecodes, fmt="json-stat2"):
    sel = [{"variableCode": k, "valueCodes": v.split(",")}
           for k, v in valuecodes.items() if v is not None]
    body = {"selection": sel}
    # A complete selection is logged as "*": same response, short enough to
    # paste into a terminal.
    show = []
    for s in sel:
        codes = s["valueCodes"]
        allc = list(m(tid)["dimension"][s["variableCode"]]["category"]["label"])
        show.append({"variableCode": s["variableCode"],
                     "valueCodes": ["*"] if set(codes) == set(allc) else codes})
    url = BASE + f"/tables/{tid}/data?" + urllib.parse.urlencode(
        {"lang": "sv", "outputFormat": fmt}, doseq=True)
    _log("POST", url, tid, {"selection": show})
    return post(f"/tables/{tid}/data", {"lang": "sv", "outputFormat": fmt}, body)

def valid(tid, var, wanted):
    have = set(m(tid)["dimension"][var]["category"]["label"])
    if isinstance(wanted, str): wanted = wanted.split(",")
    return ",".join([w for w in wanted if w in have])

def allcodes(tid, var):
    return ",".join(m(tid)["dimension"][var]["category"]["label"])
