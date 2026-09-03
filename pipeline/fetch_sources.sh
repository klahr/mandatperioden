#!/usr/bin/env bash
#
# Part of mandatperioden - https://github.com/klahr/mandatperioden
# Copyright (C) 2026 Joachim Klahr
#
# Free software under the GNU General Public License version 3 or later.
# There is NO WARRANTY, to the extent permitted by law. See the file LICENSE.
#
# Brå and Trafikanalys publish no API. Every link below carries a version id and
# changes on republication; the current one is on the page named in
# config/content.json under that measure.
set -euo pipefail
cd "$(dirname "$0")/sources/bra"
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36"
dl(){ curl -fsS -m 90 -A "$UA" -L "https://bra.se$1" -o "$2"; echo "  $2 $(stat -c%s "$2") B"; }
dl "/download/18.4450dd8019ed44e114546eae/1783421446755/10La_uppklbr_10_ar.xlsx" uppklarade.xlsx
dl "/download/18.5b3bbb9a19d24bdce4b157ff/1774872877489/Tabell%2020_2002-2025.xlsx" dodligt_vald.xlsx
dl "/download/18.5b3bbb9a19d24bdce4b15801/1774872877607/Tabell%2022_2016-2025.xlsx" dv_skjut.xlsx
dl "/download/18.125e930a19b6e6f26ff4e23e/1783940787861/Tabellsamling%20Polisanm%C3%A4lda%20hatbrott%202020-2024.xlsx" hatbrott.xlsx

# Built by Brå's selection tool (JavaScript), so these have no stable URL.
mkdir -p ../xlsx && cd ../xlsx
curl -fsS -m 90 -A "$UA" -L "https://bra.se/download/18.5d0a8fbf19ddcaf2a6c2173f/1778480930401/p811La-2014-2023.xlsx" -o aterfall_1ar_2014_2023.xlsx
curl -fsS -m 90 -A "$UA" -L "https://bra.se/download/18.388a7da196d6c2b1c49b21/1747660630514/p811La-2013-2022.xlsx" -o aterfall_1ar_2013_2022.xlsx
curl -fsS -m 90 -A "$UA" -L "https://bra.se/download/18.1bcc29ae199371e6e753026e/1758634024334/S811La-2009-2018.xlsx" -o aterfall_3ar_2009_2018.xlsx
for f in aterfall_1ar_2014_2023 aterfall_1ar_2013_2022 aterfall_3ar_2009_2018; do
  echo "  $f.xlsx $(stat -c%s $f.xlsx) B"
done

mkdir -p ../xlsx && cd ../xlsx
curl -fsS -m 90 -A "$UA" -L "https://www.trafa.se/globalassets/statistik/bantrafik/punktlighet-pa-jarnvag/2026/punktlighet-pa-jarnvag-2025.xlsx" -o punktlighet.xlsx
echo "  punktlighet.xlsx $(stat -c%s punktlighet.xlsx) B"
