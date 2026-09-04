#!/usr/bin/env bash
#
# Part of mandatperioden - https://github.com/klahr/mandatperioden
# Copyright (C) 2026 Joachim Klahr
#
# Free software under the GNU General Public License version 3 or later.
# There is NO WARRANTY, to the extent permitted by law. See the file LICENSE.
#
# No argument: recompute and render from stored data, no network.
# "fetch": re-fetch from the agencies' APIs first. "sources": re-download files.
set -euo pipefail
cd "$(dirname "$0")"

# Not in version control, so they may be missing in a fresh clone.
mkdir -p data ../out ../docs

if [[ "${1:-}" == "fetch" ]]; then
  echo "== hämtar SCB (cache i cache/, bara nya frågor går på nätet)"
  python3 fetch_scb.py
  echo "== hämtar Brå, Kolada och Socialstyrelsen"
  python3 fetch_agencies.py
  echo "== hämtar riksdagens dokumentmetadata (orsakslagret)"
  python3 fetch_riksdag.py
elif [[ "${1:-}" == "sources" ]]; then
  echo "== laddar ner Brås kalkylfiler igen"
  ./fetch_sources.sh
fi

echo "== räknar om perioderna ur config/periods.json"
python3 analyze.py
echo "== kopplar orsakslagret ur config/causes.json"
python3 causes.py
echo "== hämtar partiernas röster för de betänkanden som citeras"
python3 fetch_votes.py
echo "== renderar"
python3 render.py
echo "== klar: ../docs/index.html"
