"""Decode JSON-stat 2.0 responses into plain series.

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

import itertools
def flat(ds):
    ids, dims = ds["id"], ds["dimension"]
    axes = []
    for d in ids:
        idx = dims[d]["category"]["index"]
        axes.append(sorted(idx, key=lambda k: idx[k]) if isinstance(idx, dict) else list(idx))
    vals = ds["value"]
    out = []
    for i, combo in enumerate(itertools.product(*axes)):
        code = dict(zip(ids, combo))
        lab = {d: dims[d]["category"]["label"].get(c, c) for d, c in code.items()}
        out.append((code, lab, vals[i] if i < len(vals) else None))
    return out
def series(ds, timevar="Tid"):
    return {code[timevar]: v for code, lab, v in flat(ds)}
