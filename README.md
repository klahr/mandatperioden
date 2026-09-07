# mandatperioden

**Fyra mandatperioder i officiell statistik** – en jämförelse av **52
mätpunkter** över 2010–2014, 2014–2018, 2018–2022 och 2022–2026, där varje siffra
är spårbar tillbaka till myndighetens eget API.

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

- **Periodgränsen gör en stor del av jobbet.** Flera serier rör sig kraftigt i
  två steg som hamnar på var sin sida om en periodgräns: inflationsavståndet steg
  6,8 procentenheter under en period och föll 6,4 under nästa, och
  medellivslängden föll 0,62 år 2020 och steg därefter. Den period som råkar
  innehålla återhämtningen får kredit för den.
- **Rapporten belägger inte orsakssamband.** Den mäter nivåer och förändringar
  och kan visa att något sammanfaller i tid med ett riksdagsbeslut. Steget
  därifrån till orsak kräver en kontrafaktisk jämförelse som statistiken inte
  innehåller.

## Avsikt och urval

**Texterna är genererade.** Rapportens löpande texter – kommentarerna under varje mätpunkt,
orsaksavsnitten och metodavsnittet – är skrivna av en språkmodell. Inget stycke är formulerat för
hand, och det gäller utan undantag.

Siffrorna är däremot oberoende av texten. De hämtas ur myndigheternas API:er, citaten är maskinellt
urklippta ur granskningsrapporternas egna sammanfattningskapitel, dokumentraderna kommer ur
riksdagens öppna data och curl-anropen loggas när hämtningen körs – allt det går att kontrollera mot
källan, och koden som gör det ligger i det här repot. Texterna om siffrorna har inte samma garanti.
Där en text påstår något utöver vad tabellen visar är det påståendet det svagaste i rapporten, och
fel av det slaget rättas gärna – se [Bidra](#bidra).

**Ingen politisk agenda.** Sammanställningen är inte gjord för att stödja någon slutsats, något parti
eller någon regering. Ambitionen är att allt på sidan ska vara så objektivt som materialet tillåter:
varje siffra hämtas maskinellt ur myndigheternas egna databaser, ingen är skriven för hand,
beräkningarna står beskrivna under respektive mätpunkt och koden som gör dem ligger i det här repot.
Där ett val måste göras – periodgränser, tröskelvärden, skalan en förändring mäts i, vilka mätpunkter
som vägs samman – redovisas valet och vad det gör med resultatet.

**Statistik går att räkna och visa på fler sätt än ett.** Det är känt och döljs inte. Andra
periodgränser, andra trösklar, index i stället för nivåer, en annan deflator eller en annan uppsättning
mätpunkter kan ge en annan bild av samma verklighet. Därför görs sammanvägningen på sex sätt och två
paneler i stället för på ett enda – skillnaden mellan dem visar hur mycket av resultatet som sitter i
metodvalet snarare än i statistiken. Ingen tabell ska läsas som den enda möjliga redovisningen.

**Urvalet är godtyckligt.** Det finns ingen tanke bakom vilka 52 mätpunkter som kommit med. De har
valts efterhand, ungefär i den ordning de dök upp, inte efter någon uppfattning om vad som betyder mest
och inte för att täcka något samhällsområde jämnt. Godtyckligt är däremot inte samma sak som
slumpmässigt draget: samlingen är inget statistiskt urval ur någon population av tänkbara mått och är
inte representativ för svensk officiell statistik. Att rapporten mäter vårdkapacitet, kunskapsresultat,
äldreomsorg, ungas psykiska hälsa och rättskedjans genomströmning tunnare än ekonomi och brott är
alltså inget omdöme om vad som betyder mindre, bara ett resultat av hur listan blev till.

## Bidra

Förbättringar och rättelser är välkomna – issues och pull requests tas emot, lika gärna på fel i
beräkningarna, en missad seriebrytning eller en formulering som lutar, som på **förslag på fler punkter
att mäta på**. Listan är öppen och fler mätpunkter läggs gärna till på önskemål.

Kraven på en ny mätpunkt är bara att statistiken går att hämta maskinellt från den myndighet som
ansvarar för den, att den täcker tillräckligt många år för att en mandatperiod ska gå att mäta, och att
det går att säga vilket håll som räknas som en förbättring – eller att måttet, som medelålder och
skattetryck, får stå utan omdöme.

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
villkor, inte av den här licensen. Licensen gäller repots kod och konfiguration
och den renderade rapporten. Rapportens löpande texter är genererade av en
språkmodell – se [Avsikt och urval](#avsikt-och-urval).
