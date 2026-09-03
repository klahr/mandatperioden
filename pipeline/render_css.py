"""Stylesheet for the report.

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

CSS = r"""
:root{
  --paper:#e8eae4; --sheet:#f8f9f6; --sunk:#dfe2da;
  --ink:#191b16; --ink-2:#575a4f; --ink-3:#7e8177;
  --rule:#cfd2c7; --rule-soft:#dcdfd5;
  /* the terms = an ordered scale in one hue, oldest lightest */
/*PERIODCOLORS-LIGHT*/
  --good:#0ca30c; --bad:#d03b3b; --flat:#7e8177; --warn:#b8860b;
  --shadow:0 1px 0 rgba(25,27,22,.05), 0 8px 24px -18px rgba(25,27,22,.5);
  --display:"Familjen Grotesk","Helvetica Neue",Arial,sans-serif;
  --body:"Source Serif 4",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
}
@media (prefers-color-scheme:dark){
  :root:not([data-theme="light"]){
    --paper:#141611; --sheet:#1c1e18; --sunk:#101208;
    --ink:#eef0e6; --ink-2:#a6a99b; --ink-3:#83877a;
    --rule:#2e3128; --rule-soft:#252821;
/*PERIODCOLORS-DARK-A*/
    --good:#0ca30c; --bad:#e05a5a; --flat:#83877a; --warn:#fab219;
    --shadow:0 1px 0 rgba(0,0,0,.3), 0 10px 28px -20px #000;
  }
}
:root[data-theme="dark"]{
  --paper:#141611; --sheet:#1c1e18; --sunk:#101208;
  --ink:#eef0e6; --ink-2:#a6a99b; --ink-3:#83877a;
  --rule:#2e3128; --rule-soft:#252821;
/*PERIODCOLORS-DARK-B*/
  --good:#0ca30c; --bad:#e05a5a; --flat:#83877a; --warn:#fab219;
  --shadow:0 1px 0 rgba(0,0,0,.3), 0 10px 28px -20px #000;
}

*{box-sizing:border-box}
.visually-hidden{position:absolute!important; width:1px; height:1px; margin:-1px;
  padding:0; overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; border:0}
.skiplink{position:absolute; left:-9999px; top:0; z-index:100; background:var(--sheet);
  color:var(--ink); padding:10px 16px; border:1px solid var(--ink);
  font-family:var(--display); font-size:.9rem}
.skiplink:focus{left:8px; top:8px}
body{background:var(--paper); color:var(--ink); font-family:var(--body);
     font-size:17px; line-height:1.62; -webkit-font-smoothing:antialiased}
.wrap{max-width:1220px; margin:0 auto; padding:0 28px 96px}
h1,h2,h3,h4{font-family:var(--display); font-weight:600; text-wrap:balance; line-height:1.12}
p{margin:0 0 .9em}
a{color:inherit; text-decoration:underline; text-decoration-color:var(--rule); text-underline-offset:2px}
a:hover{text-decoration-color:var(--p3)}
:focus-visible{outline:2px solid var(--p3); outline-offset:2px; border-radius:2px}
.eyebrow{font-family:var(--display); font-size:.66rem; font-weight:600;
         letter-spacing:.16em; text-transform:uppercase; color:var(--ink-3)}
.mono{font-family:var(--mono); font-size:.78em}
.dot{display:inline-block; width:8px; height:8px; border-radius:50%; flex:none}
.swatch{width:10px; height:10px; border-radius:2px; flex:none; display:inline-block}

.causes{margin-top:14px; border:1px solid var(--rule); border-radius:4px; background:var(--sunk)}
.causes>summary{padding:9px 12px; cursor:pointer; font-family:var(--display);
                font-size:.76rem; font-weight:600; display:flex; align-items:center; gap:10px}
.causes>summary::marker{color:var(--ink-3)}
.causes .cn{font-family:var(--mono); font-size:.62rem; color:var(--ink-2);
            font-weight:400; margin-left:auto}
.cbody{padding:2px 14px 14px; border-top:1px solid var(--rule)}
.cbody>p{font-size:.82rem; line-height:1.55; color:var(--ink-2); margin:11px 0}
.cbody>p b{color:var(--ink)}
.csect{margin-top:16px}
.csect h5{font-family:var(--display); font-size:.68rem; letter-spacing:.07em;
          text-transform:uppercase; color:var(--ink-3); margin:0 0 4px}
.chint{font-size:.72rem; line-height:1.5; color:var(--ink-2); margin:0 0 8px; max-width:52em}
.dlist,.omlist{list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:7px}
.dlist.tight{margin-top:7px; gap:5px}
.dlist>li{font-size:.79rem; line-height:1.45; padding-left:0}
.dlist>li a{color:var(--ink); text-decoration:none; border-bottom:1px solid var(--rule)}
.dlist>li a:hover{border-bottom-color:var(--ink)}
.dref{font-family:var(--mono); font-size:.62rem; color:var(--ink-2); white-space:nowrap}
.dperiod{display:inline-flex; align-items:center; gap:4px; font-family:var(--mono);
         font-size:.6rem; color:var(--ink-2); margin-right:7px}
.dcit{margin:6px 0 2px; padding:8px 11px; border-left:2px solid var(--rule);
      background:var(--paper); font-size:.76rem; line-height:1.5; color:var(--ink-2)}
.dcit cite{display:block; margin-top:5px; font-family:var(--mono); font-size:.6rem;
           font-style:normal; color:var(--ink-2)}
.omlist>li{font-size:.79rem; line-height:1.45}
.omtext{display:block; margin-top:3px; color:var(--ink-2)}
@media print{.causes{break-inside:avoid} .causes>summary{list-style:none}}

.mast{padding:56px 0 0; border-bottom:1px solid var(--ink)}
.mast .kicker{display:flex; flex-wrap:wrap; gap:10px 20px; align-items:baseline; margin-bottom:26px}
.mast h1{font-size:clamp(2.5rem,6.4vw,4.6rem); letter-spacing:-.028em; margin:0 0 18px}
.standfirst{font-size:clamp(1.05rem,1.7vw,1.3rem); line-height:1.5; max-width:36em;
            color:var(--ink-2); margin:0 0 30px}
.periodbar{display:grid; grid-template-columns:repeat(var(--np,4),1fr); border-top:1px solid var(--rule);
           border-left:1px solid var(--rule); margin-bottom:34px}
.periodbar>div{padding:14px 15px 16px; border-right:1px solid var(--rule)}
/*PERIODBAR-NTH*/
.periodbar .lbl{display:flex; align-items:center; gap:8px; margin-bottom:5px}
.periodbar .dates{font-family:var(--display); font-size:.98rem; font-weight:600;
                  font-variant-numeric:tabular-nums}
.periodbar .sub{font-size:.8rem; color:var(--ink-2); line-height:1.4; margin-top:4px}
.periodbar .gov{font-family:var(--mono); font-size:.68rem; color:var(--ink-3); margin-top:6px; display:block}

.tblock{margin-bottom:20px}
.tbhead{display:flex; align-items:baseline; gap:12px; flex-wrap:wrap; margin-bottom:8px}
.tbhead .eyebrow{font-size:.78rem; letter-spacing:.14em; color:var(--ink)}
.tbsub{font-size:.85rem; color:var(--ink-3); font-family:var(--display)}
.tally{display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
       border:1px solid var(--rule); background:var(--sheet); box-shadow:var(--shadow)}
.tally .cell{padding:16px 16px 18px; border-right:1px solid var(--rule-soft)}
.tally .cell:last-child{border-right:0}
.tally .n{font-family:var(--display); font-size:2.3rem; font-weight:600; line-height:1;
          font-variant-numeric:tabular-nums; display:block}
.tally .cap{font-size:.82rem; color:var(--ink-2); line-height:1.35; display:block; margin-top:7px}
.tally .cell.g .n{color:var(--good)} .tally .cell.b .n{color:var(--bad)}
.tally .cell.f .n{color:var(--flat)} .tally .cell.m .n{color:var(--ink-3)}
.tally .cell.w .n{color:var(--warn)}
.caution{border:1px solid var(--warn); border-left-width:3px; background:var(--sheet);
         padding:16px 18px 4px; margin:22px 0 0}
.caution .eyebrow{color:var(--warn); display:block; margin-bottom:7px}
.caution p{font-size:.9rem; color:var(--ink-2); line-height:1.58; max-width:58em}
.mastnote{font-size:.9rem; color:var(--ink-2); line-height:1.55; max-width:56em;
          margin:20px 0 0; padding-left:13px; border-left:2px solid var(--rule)}

section{margin-top:72px}
.sechead{border-top:1px solid var(--ink); padding-top:14px; margin-bottom:26px}
.sechead h2{font-size:clamp(1.5rem,2.6vw,2.1rem); letter-spacing:-.02em; margin:.15em 0 0}
.sechead .lede{max-width:40em; color:var(--ink-2); font-size:.97rem; margin:.6em 0 0}

.ledger-scroll{overflow-x:auto; border:1px solid var(--rule); background:var(--sheet); box-shadow:var(--shadow)}
table.ledger{width:100%; border-collapse:collapse; min-width:1080px}
table.ledger th{font-family:var(--display); font-size:.65rem; font-weight:600; letter-spacing:.11em;
  text-transform:uppercase; color:var(--ink-3); text-align:left; padding:11px 11px;
  border-bottom:1px solid var(--ink); white-space:nowrap}
table.ledger th.r,table.ledger td.r{text-align:right}
table.ledger th.pcol{text-align:right}
table.ledger th.pcol span{display:block; font-size:.6rem; letter-spacing:.06em; color:var(--ink-3); font-weight:400}
table.ledger td{padding:10px 11px; border-bottom:1px solid var(--rule-soft); vertical-align:middle}
table.ledger tbody tr:last-child td{border-bottom:0}
table.ledger tbody tr:hover{background:var(--sunk)}
table.ledger td.p4col{background:var(--p4w)}
.idx{font-family:var(--mono); font-size:.72rem; color:var(--ink-3)}
.lname{font-family:var(--display); font-weight:600; font-size:.95rem}
.lname a{text-decoration:none; border-bottom:1px solid transparent}
.lname a:hover{border-bottom-color:var(--p3)}
.lunit{font-size:.74rem; color:var(--ink-3); font-family:var(--display); line-height:1.3;
       display:block; margin-top:1px; max-width:24em}
.delta{font-family:var(--display); font-variant-numeric:tabular-nums; font-weight:600;
       font-size:.92rem; white-space:nowrap}
.delta.up{color:var(--good)} .delta.down{color:var(--bad)}
.delta.nil{color:var(--flat)} .delta.na{color:var(--ink-3); font-weight:400}
.pflag{font-family:var(--mono); font-size:.6rem; color:var(--ink-2); display:block; line-height:1.2}
.chip{display:inline-flex; align-items:center; gap:5px; font-family:var(--display);
  font-size:.68rem; font-weight:600; letter-spacing:.06em; text-transform:uppercase;
  padding:3px 7px; border-radius:2px; white-space:nowrap; border:1px solid currentColor}
.chip.g{color:var(--good)} .chip.b{color:var(--bad)} .chip.f{color:var(--flat)}
.chip.n{color:var(--ink-3)} .chip.w{color:var(--warn)}
.chip.m{color:var(--ink-3); border-style:dashed}
.chip svg{width:9px; height:9px; flex:none}
.prod{display:inline-block; font-family:var(--display); font-size:.64rem; font-weight:600;
  letter-spacing:.08em; text-transform:uppercase; padding:2px 6px; border-radius:2px;
  white-space:nowrap; border:1px solid var(--rule); color:var(--ink-2); background:var(--sunk)}
.prod.p-bra{border-color:var(--warn); color:var(--warn); background:transparent}
.prod.p-skr{border-color:var(--p3); color:var(--p3); background:var(--p3w)}
.prod.p-sos{border-color:var(--good); color:var(--good); background:transparent}
.prod.p-skv{border-color:var(--ink-2); color:var(--ink-2); background:transparent}
.prod.p-kfm{border-color:var(--bad); color:var(--bad); background:transparent}
.prod.p-trf{border-color:var(--p2); color:var(--p2); background:transparent}
.prod.p-tva{border-color:var(--warn); color:var(--warn); background:var(--sunk)}
.spark{display:block}

.overview{border:1px solid var(--rule); background:var(--sheet); box-shadow:var(--shadow);
          padding:22px 22px 18px; margin-top:26px}
.overview .ctitle{font-family:var(--display); font-size:.72rem; font-weight:600; letter-spacing:.11em;
  text-transform:uppercase; color:var(--ink-3); margin-bottom:6px; padding-bottom:5px;
  border-bottom:1px solid var(--rule-soft)}
.legend{display:flex; flex-wrap:wrap; gap:8px 20px; margin-bottom:18px; align-items:center}
.legend span{display:inline-flex; align-items:center; gap:7px; font-family:var(--display);
             font-size:.79rem; color:var(--ink-2)}
.ovcap{font-size:.85rem; color:var(--ink-2); margin:14px 0 0; padding-top:12px;
       border-top:1px dotted var(--rule); max-width:60em}

.entry{border-top:1px solid var(--rule); padding:30px 0 6px; scroll-margin-top:20px}
.entry:first-of-type{border-top:1px solid var(--ink)}
.ehead{display:flex; flex-wrap:wrap; align-items:baseline; gap:8px 12px; margin-bottom:4px}
.ehead h3{font-size:1.42rem; letter-spacing:-.018em; margin:0}
.eunit{font-family:var(--display); font-size:.82rem; color:var(--ink-3); margin:0 0 20px; max-width:46em}
.ebody{display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.08fr); gap:34px; align-items:start}
.prose{font-size:.98rem; line-height:1.66}
.prose p{margin:0 0 .8em}
.figs{display:grid; grid-template-columns:repeat(var(--np,4),1fr); border:1px solid var(--rule);
      border-left:0; margin-bottom:18px; background:var(--sheet)}
.figs .f{padding:11px 11px 13px; border-left:1px solid var(--rule-soft)}
/*FIGS-NTH*/
.figs .plabel{display:flex; align-items:center; gap:6px; margin-bottom:7px}
.figs .plabel span{font-family:var(--display); font-size:.66rem; font-weight:600;
                   letter-spacing:.06em; color:var(--ink-2); white-space:nowrap}
.figs .pts{font-family:var(--display); font-variant-numeric:tabular-nums; font-size:.88rem;
           font-weight:600; letter-spacing:-.01em; line-height:1.3}
.figs .pts .arrow{color:var(--ink-3); font-weight:400; padding:0 2px}
.figs .when{font-family:var(--mono); font-size:.62rem; color:var(--ink-3); margin-top:3px; display:block}
.figs .chg{margin-top:7px}
.figs .avg{font-size:.72rem; color:var(--ink-2); margin-top:5px; font-family:var(--display)}
.figs .miss{font-family:var(--display); font-size:.78rem; color:var(--ink-3)}
.chartbox{border:1px solid var(--rule); background:var(--sheet); box-shadow:var(--shadow); padding:14px 14px 8px}
.chartbox .ctitle{font-family:var(--display); font-size:.72rem; font-weight:600; letter-spacing:.09em;
  text-transform:uppercase; color:var(--ink-3); margin-bottom:8px}
.trend{border:1px solid var(--rule); border-left:3px solid var(--ink); background:var(--sheet);
       padding:12px 14px 13px; margin:0 0 18px}
.trend .thead{display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:9px}
.tslopes{display:flex; align-items:center; gap:8px; flex-wrap:wrap; font-family:var(--display);
         font-variant-numeric:tabular-nums; font-size:.9rem; font-weight:600}
.tslopes>span{display:inline-flex; align-items:center; gap:5px}
.tslopes .tarrow{color:var(--ink-3); font-weight:400}
.tslopes .tshift{font-weight:400; font-size:.8rem; color:var(--ink-2);
                 border-left:1px solid var(--rule); padding-left:9px; margin-left:2px}
.trend .tgloss{font-size:.8rem; color:var(--ink-3); line-height:1.5; margin:8px 0 0}
.trend .tn{display:block; font-family:var(--mono); font-size:.66rem; color:var(--ink-3); margin-top:7px}
.notes{margin-top:14px; padding-top:12px; border-top:1px dotted var(--rule)}
.notes ul{margin:0; padding-left:1.1em}
.notes li{font-size:.85rem; color:var(--ink-2); line-height:1.5; margin-bottom:5px}
.method{font-size:.85rem; color:var(--ink-2); line-height:1.55; margin-top:12px;
        padding-left:13px; border-left:2px solid var(--rule)}
.method b{font-family:var(--display); color:var(--ink); font-size:.72rem; letter-spacing:.09em;
          text-transform:uppercase; display:block; margin-bottom:3px}
.srcline{margin-top:12px; font-family:var(--mono); font-size:.71rem; color:var(--ink-3); line-height:1.7}
.srcline a{text-decoration:none; border-bottom:1px solid var(--rule)}
details{margin-top:14px}
details summary{cursor:pointer; font-family:var(--display); font-size:.75rem; font-weight:600;
  letter-spacing:.08em; text-transform:uppercase; color:var(--ink-2); padding:4px 0}
details summary:hover{color:var(--p3)}
details.repro summary{color:var(--p3)}
.cintro{font-size:.83rem; color:var(--ink-2); line-height:1.5; margin:8px 0 12px; max-width:44em}
.creq{margin:0 0 12px}
.cnote{display:block; font-family:var(--mono); font-size:.68rem; color:var(--ink-3);
       margin-bottom:4px; word-break:break-word}
pre.curl{margin:0; padding:9px 11px; background:var(--sunk); border:1px solid var(--rule-soft);
         border-left:2px solid var(--p3);
         font-family:var(--mono); font-size:.68rem; line-height:1.6; color:var(--ink-2);
         /* soft wrap: the whole command is visible, what gets copied is unchanged */
         white-space:pre-wrap; overflow-wrap:anywhere;
         -webkit-user-select:all; user-select:all}
pre.curl code{font:inherit; color:inherit}
.dt-scroll{overflow-x:auto; margin-top:10px; border:1px solid var(--rule-soft)}
table.dt{width:100%; border-collapse:collapse; font-size:.79rem}
table.dt th,table.dt td{padding:5px 8px; text-align:right; white-space:nowrap;
                        border-bottom:1px solid var(--rule-soft)}
table.dt th:first-child,table.dt td:first-child{text-align:left; position:sticky; left:0; background:var(--sheet)}
table.dt thead th{font-family:var(--mono); font-size:.68rem; color:var(--ink-3); font-weight:400}
table.dt td{font-family:var(--display); font-variant-numeric:tabular-nums}
table.dt tbody th{font-family:var(--display); font-weight:600; font-size:.77rem; text-align:left}
/*DT-NTH*/

.matrix{border:1px solid var(--rule); background:var(--sheet); box-shadow:var(--shadow); overflow-x:auto}
.mrow{display:grid; grid-template-columns:minmax(150px,180px) repeat(3,minmax(180px,1fr));
      border-bottom:1px solid var(--rule-soft); min-width:740px}
.mrow:last-child{border-bottom:0}
.mrow.mhead{border-bottom:1px solid var(--ink)}
.mh,.mrh{font-family:var(--display); font-size:.67rem; font-weight:600; letter-spacing:.1em;
         text-transform:uppercase; color:var(--ink-3); padding:12px 14px}
.mrh{border-right:1px solid var(--rule-soft); color:var(--ink-2); display:flex; align-items:center}
.mc{padding:12px 14px; display:flex; flex-wrap:wrap; gap:6px; align-content:flex-start;
    border-right:1px solid var(--rule-soft)}
.mc:last-child{border-right:0}
.mc-good{background:var(--p4w)}
.mc-bad{background:rgba(208,59,59,.07)}
.mtag{display:inline-block; font-family:var(--display); font-size:.79rem; font-weight:600;
  padding:3px 8px; border:1px solid var(--rule); border-radius:2px; background:var(--paper);
  text-decoration:none; color:var(--ink)}
.mtag:hover{border-color:var(--p3)}
.mtag.t-g{border-left:3px solid var(--good)} .mtag.t-b{border-left:3px solid var(--bad)}
.mtag.t-f{border-left:3px solid var(--flat)}
.mempty{color:var(--ink-3); font-family:var(--mono); font-size:.8rem}

.srcs-scroll{overflow-x:auto; border:1px solid var(--rule); background:var(--sheet)}
table.srcs{width:100%; border-collapse:collapse; min-width:720px; font-size:.85rem}
table.srcs th{font-family:var(--display); font-size:.65rem; letter-spacing:.11em; text-transform:uppercase;
  color:var(--ink-3); text-align:left; padding:12px 13px; border-bottom:1px solid var(--ink); white-space:nowrap}
table.srcs td{padding:9px 13px; border-bottom:1px solid var(--rule-soft); vertical-align:top}
table.srcs tr:last-child td{border-bottom:0}
table.srcs td.id,table.srcs td.upd{font-family:var(--mono); font-size:.74rem; white-space:nowrap}
table.srcs td.upd{color:var(--ink-3)}
footer.foot{margin-top:72px; padding-top:18px; border-top:1px solid var(--ink);
      font-size:.85rem; color:var(--ink-3); max-width:52em}
footer.foot p{margin:0 0 .6em}

.tt{position:fixed; z-index:50; pointer-events:none; opacity:0; transition:opacity .1s;
  background:var(--sheet); border:1px solid var(--rule); box-shadow:var(--shadow);
  padding:7px 10px; font-family:var(--display); font-size:.78rem; line-height:1.4;
  color:var(--ink); white-space:nowrap; border-radius:2px}
.tt .ttp{font-size:.66rem; letter-spacing:.1em; text-transform:uppercase; color:var(--ink-3); display:block}
.tt .ttv{font-variant-numeric:tabular-nums; font-weight:600}

@media (max-width:980px){
  .ebody{grid-template-columns:minmax(0,1fr); gap:22px}
  .figs{grid-template-columns:repeat(2,1fr)}
  .periodbar{grid-template-columns:repeat(2,1fr)}
  .wrap{padding:0 18px 72px}
  body{font-size:16px}
}
@media (prefers-reduced-motion:reduce){*{animation:none!important; transition:none!important}}

@media print{
  :root{--paper:#fff; --sheet:#fff; --sunk:#f4f4f2; --shadow:none}
  body{font-size:10.5pt}
  .wrap{max-width:none; padding:0}
  .skiplink,.tt{display:none}
  .entry{break-inside:avoid; page-break-inside:avoid}
  .sechead{break-after:avoid}
  details{display:none}
  .ledger-scroll,.srcs-scroll,.matrix,.dt-scroll{overflow:visible}
  table.ledger{min-width:0; font-size:8pt}
  a{text-decoration:none}
  .srcline a::after{content:" (" attr(href) ")"; font-size:7pt; word-break:break-all}
}
"""
