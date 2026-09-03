# mandatperioden

Har Sverige blivit bättre? En jämförelse av **52 mätpunkter** över **fyra
mandatperioder** – 2010–2014, 2014–2018, 2018–2022 och 2022–2026 – byggd enbart
på officiell statistik, med varje siffra spårbar tillbaka till myndighetens eget
API.

**Läs rapporten: <https://klahr.github.io/mandatperioden/>**

Den renderade sidan ligger i repot som [`docs/index.html`](docs/index.html) och
serveras därifrån av GitHub Pages. Den är fristående – all CSS och JavaScript är
inbäddad – så den går också att öppna direkt från disk.

```
./pipeline/run.sh          # räkna om + rendera ur sparad data (inget nätverk)
./pipeline/run.sh fetch    # hämta om från myndigheternas API:er först
./pipeline/run.sh sources  # ladda ner Brås och Trafikanalys kalkylfiler igen
```

Resultatet skrivs till `docs/index.html`.

## Vad rapporten kommer fram till

Sex olika aggregeringsmetoder ger samma rangordning, men skillnaderna är små och
alla siffror bör läsas med de förbehåll som står i rapportens metodavsnitt.

| Panel | Mätpunkter | 2010–14 | 2014–18 | 2018–22 | 2022–26 |
|---|---|---|---|---|---|
| Alla mätbara | 47 | 53,3 % | 53,5 % | 48,9 % | **55,3 %** |
| Balanserad (mätbar i alla fyra perioder) | 30 | 53,3 % | 53,3 % | 56,7 % | **60,0 %** |

Andelen mätpunkter som förbättrats. Den balanserade panelen är den rättvisaste
jämförelsen: bara 35 av 52 mätpunkter går att mäta över 2010–2014, mot 52 över
de två senaste, och en panel med olika innehåll per period jämför olika saker.

Två invändningar mot att läsa tabellen som ett betyg på regeringar:

- **Periodgränsen gör en stor del av jobbet.** Inflations- och energiprischocken
  2022–2023 slog ner i slutet av en period och återhämtningen i början av nästa.
  Den period som råkar innehålla återhämtningen får kredit för den. Detsamma
  gäller medellivslängden, som föll under pandemin och steg efteråt.
- **Rapporten belägger inte orsakssamband.** Den mäter nivåer och förändringar
  och kan visa att något sammanfaller i tid med ett riksdagsbeslut. Steget
  därifrån till orsak kräver en kontrafaktisk jämförelse som statistiken inte
  innehåller.

## Källor

All statistik hämtas maskinellt. Ingen siffra är inskriven för hand.

| Myndighet | Mätpunkter | Hur |
|---|---|---|
| SCB | 34 | PxWeb 2.0-API, `api.scb.se` |
| Brå | 7 | egna kalkylfiler + Kolada |
| SKR / RKA | 3 | Kolada v3, `api.kolada.se` |
| Socialstyrelsen | 3 | SDB-API + Kolada |
| Kronofogden | 2 | Kolada |
| Skolverket | 1 | Kolada |
| Trafikanalys | 1 | egen kalkylfil |
| Tillväxtanalys | 1 | Kolada |

Varje mätpunkt i rapporten har en utfällbar ruta **Hämta datan själv** med de
faktiska `curl`-anropen bakom just den serien – 50 mätpunkter har sådana, och
anropen loggas när hämtningen körs, så de kan inte hamna i otakt med koden.

## Orsakslagret

Varje mätpunkt har också ett avsnitt **Orsaker och sammanhang** som bygger på
Riksdagens öppna data: 13 519 dokument 2009–2026 (4 258 propositioner, 6 570
betänkanden, 460 av Riksrevisionens granskningsrapporter, 1 919 utredningar och
312 riksdagsrapporter), varav 586 används som källhänvisningar och 141 citeras
ordagrant.

Tre slags påstående hålls medvetet åtskilda, eftersom de har helt olika
bevisvärde:

| Lager | Vad det är | Bevisvärde |
|---|---|---|
| Beslut i området | propositioner riksdagen behandlat, tre per mandatperiod | fakta om vad som gjordes, inget om effekt |
| Vad granskarna kommit fram till | Riksrevisionens granskningar, citerade ur deras egna sammanfattningar | här finns evidensen om effekter |
| Omvärlden | daterade händelser utanför politiken | förklarar ofta mer än besluten gör |

## Struktur

```
LICENSE                  GPL version 3
README.md                den här filen
docs/
  index.html             den renderade rapporten, serverad av GitHub Pages
pipeline/
  run.sh                 enda ingången
  fetch_scb.py           hämtar SCB
  fetch_agencies.py      hämtar Brå, Kolada, Socialstyrelsen, Trafikanalys
  fetch_riksdag.py       hämtar riksdagens dokumentmetadata
  fetch_sources.sh       laddar ner kalkylfiler som saknar API
  scb_api.py             PxWeb 2.0-klient med filcache och anropslogg
  jsonstat.py            JSON-stat 2.0-avkodning
  periods.py             mandatperiodernas datum -> statistikens periodnycklar
  analyze.py             periodjämförelser, trendskiften, aggregat
  causes.py              kopplar mätpunkter till beslut och granskningar
  render.py              HTML
  render_css.py          stilmall
  render_js.py           diagram
  config/                all konfiguration och redaktionell text
out/                     publiceringsfragment (skapas vid körning, ej i repot)
```

## Att lägga till en mandatperiod

Lägg till ett objekt i `periods` i `pipeline/config/periods.json` och kör
`./pipeline/run.sh`. Ingen kodändring behövs – nollpunkter, periodfönster,
tabellkolumner, färgskala, periodsnitt, täckningssiffror och metodtext räknas
fram ur datumen.

## Krav

Python 3.9 eller senare och `openpyxl` (för myndigheternas kalkylfiler). Inga
andra beroenden – hämtningen använder standardbibliotekets `urllib`.

```
pip install openpyxl
```

Cache, nedladdade myndighetsfiler och härledd data ligger inte i repot –
tillsammans är de omkring 400 MB och allt går att återskapa. Den renderade
rapporten är undantaget: den är versionshanterad, så att den går att läsa utan
att byggas. En första
`./pipeline/run.sh fetch` tar ungefär en timme, mest därför att riksdagens
fulltexter hämtas en gång. Sedan är cachen varm och omkörningar är gratis.

## Licens

GNU General Public License version 3 eller senare – se [LICENSE](LICENSE).

Statistiken tillhör de myndigheter som producerar den och omfattas av deras egna
villkor, inte av den här licensen. Rapportens texter, urval och beräkningar är
mina.
