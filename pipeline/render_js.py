"""Chart code for the report.

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

JS = r"""
(function(){
const D = window.__DATA__;
const css = k => getComputedStyle(document.documentElement).getPropertyValue(k).trim();
const NB = ' ';
const PCOL = Array.from({length: D.np}, (_,i)=>'--p'+(i+1));
const PNAME = D.periods;

function fmt(v, dec){
  if (v === null || v === undefined) return '–';
  const s = Math.abs(v) >= 10000
    ? v.toLocaleString('sv-SE', {maximumFractionDigits:0})
    : v.toLocaleString('sv-SE', {minimumFractionDigits:dec, maximumFractionDigits:dec});
  return s.replace(/ /g, NB);
}
const NS = 'http://www.w3.org/2000/svg';
const el = (n,a)=>{const e=document.createElementNS(NS,n); for(const k in a) e.setAttribute(k,a[k]); return e;};

const TT = document.createElement('div');
TT.className = 'tt'; document.body.appendChild(TT);

/* ---------------- tidsserie med fyra mandatperioder ---------------- */
function seriesChart(host, ind){
  const {keys, vals, seg} = ind;
  const W = host.clientWidth || 540, H = 228;
  const P = {t:38, r:12, b:28, l:48};
  const iw = W-P.l-P.r, ih = H-P.t-P.b;
  const fin = vals.map((v,i)=>[i,v]).filter(d=>d[1]!==null);
  if (!fin.length) return;
  let lo = Math.min(...fin.map(d=>d[1])), hi = Math.max(...fin.map(d=>d[1]));
  if (lo===hi){lo-=1;hi+=1;}
  const pad=(hi-lo)*.14; lo-=pad; hi+=pad;
  const x = i => P.l + (keys.length===1 ? iw/2 : iw*i/(keys.length-1));
  const y = v => P.t + ih - ih*(v-lo)/(hi-lo);
  const svg = el('svg',{viewBox:`0 0 ${W} ${H}`, width:'100%', height:H, role:'img',
    'aria-label':`${ind.name}, ${ind.unit}, ${keys[0]} till ${keys[keys.length-1]}`});

  for (let s=1; s<=D.np; s++){
    const idx = seg.map((v,i)=>v===s?i:-1).filter(i=>i>=0);
    if (!idx.length) continue;
    const half = keys.length>1 ? iw/(keys.length-1)/2 : 0;
    const a = Math.max(P.l, x(Math.min(...idx))-half);
    const b = Math.min(W-P.r, x(Math.max(...idx))+half);
    svg.appendChild(el('rect',{x:a, y:P.t, width:Math.max(2,b-a), height:ih, fill:css('--p'+s+'w')}));
    if (b-a > 30){
      const t = el('text',{x:a+4, y:P.t-7, fill:css('--ink-3'), 'font-size':9,
                           'font-family':css('--mono')});
      t.textContent = ind.pshort[s-1]; svg.appendChild(t);
    }
  }
  [lo+(hi-lo)*.12, (lo+hi)/2, hi-(hi-lo)*.12].forEach(v=>{
    svg.appendChild(el('line',{x1:P.l,x2:W-P.r,y1:y(v),y2:y(v),stroke:css('--rule'),
                               'stroke-width':1,'stroke-dasharray':'2 3'}));
    const t = el('text',{x:P.l-7,y:y(v)+3.5,fill:css('--ink-3'),'font-size':10,
                         'text-anchor':'end','font-family':css('--display')});
    t.textContent = fmt(Math.round(v*100)/100, ind.dec); svg.appendChild(t);
  });
  svg.appendChild(el('line',{x1:P.l,x2:W-P.r,y1:P.t+ih,y2:P.t+ih,stroke:css('--rule'),'stroke-width':1}));

  const col = s => s>=1 ? css(PCOL[s-1]) : css('--ink-3');
  const ma = ind.ma;
  for (let i=1;i<keys.length;i++){
    if (vals[i]===null || vals[i-1]===null) continue;
    svg.appendChild(el('line',{x1:x(i-1),y1:y(vals[i-1]),x2:x(i),y2:y(vals[i]),
      stroke:col(Math.max(seg[i],seg[i-1])),
      'stroke-width': ma?1.2:2, opacity: ma?.42:1, 'stroke-linecap':'round'}));
  }
  (ind.pmeans||[]).forEach(pm=>{
    const half = keys.length>1 ? iw/(keys.length-1)/2 : 0;
    const a = Math.max(P.l, x(pm.a)-half), b = Math.min(W-P.r, x(pm.b)+half);
    svg.appendChild(el('line',{x1:a, x2:b, y1:y(pm.v), y2:y(pm.v),
      stroke:css(PCOL[pm.i]), 'stroke-width':1.6, 'stroke-dasharray':'5 3', opacity:.9}));
  });
  if (ma){
    for (let i=1;i<keys.length;i++){
      if (ma[i]===null || ma[i-1]===null) continue;
      svg.appendChild(el('line',{x1:x(i-1),y1:y(ma[i-1]),x2:x(i),y2:y(ma[i]),
        stroke:col(Math.max(seg[i],seg[i-1])),'stroke-width':2.4,'stroke-linecap':'round'}));
    }
    const gy = 11;
    const items = [
      {t: ind.rawlab, w: 1.2, o: .42, d: null},
      {t: ind.malab,  w: 2.4, o: 1,   d: null},
      {t: 'periodsnitt', w: 1.6, o: .9, d: '5 3'}];
    let gx = W - P.r;
    for (let k = items.length - 1; k >= 0; k--){
      const it = items[k];
      const tw = it.t.length*4.5 + 18;
      gx -= tw;
      const at = {x1:gx, x2:gx+13, y1:gy-3, y2:gy-3, stroke:css('--ink-3'),
                  'stroke-width':it.w, opacity:it.o};
      if (it.d) at['stroke-dasharray'] = it.d;
      svg.appendChild(el('line', at));
      const tx = el('text',{x:gx+17, y:gy, fill:css('--ink-3'), 'font-size':8.5,
                            'font-family':css('--display')});
      tx.textContent = it.t; svg.appendChild(tx);
      gx -= 12;
    }
  }
  ind.marks.forEach(mk=>{
    const i = keys.indexOf(mk);
    if (i<0 || vals[i]===null) return;
    svg.appendChild(el('circle',{cx:x(i),cy:y(vals[i]),r:4,fill:css('--sheet'),
                                 stroke:col(seg[i]),'stroke-width':2}));
  });
  [keys[0], ...ind.marks].filter((v,i,a)=>a.indexOf(v)===i).forEach(k=>{
    const i = keys.indexOf(k); if (i<0) return;
    const anchor = i===0?'start':(i===keys.length-1?'end':'middle');
    const t = el('text',{x:x(i),y:H-9,fill:css('--ink-3'),'font-size':9,
                         'text-anchor':anchor,'font-family':css('--mono')});
    t.textContent = k; svg.appendChild(t);
  });

  const cross = el('line',{y1:P.t,y2:P.t+ih,stroke:css('--ink-3'),'stroke-width':1,opacity:0});
  const dot = el('circle',{r:5,fill:css('--p4'),stroke:css('--sheet'),'stroke-width':2,opacity:0});
  svg.appendChild(cross); svg.appendChild(dot);
  const hit = el('rect',{x:P.l,y:P.t,width:iw,height:ih,fill:'transparent'});
  svg.appendChild(hit);
  hit.addEventListener('pointermove', ev=>{
    const r = svg.getBoundingClientRect();
    const px = (ev.clientX-r.left)*W/r.width;
    let best=-1, bd=1e9;
    keys.forEach((k,i)=>{ if(vals[i]===null) return; const d=Math.abs(x(i)-px); if(d<bd){bd=d;best=i;} });
    if (best<0) return;
    cross.setAttribute('x1',x(best)); cross.setAttribute('x2',x(best)); cross.setAttribute('opacity',.45);
    dot.setAttribute('cx',x(best)); dot.setAttribute('cy',y(vals[best]));
    dot.setAttribute('fill',col(seg[best])); dot.setAttribute('opacity',1);
    const pn = seg[best]>=1 ? PNAME[seg[best]-1] : 'Före perioderna';
    const mv = ind.ma && ind.ma[best]!==null && ind.ma[best]!==undefined
      ? `<br><span style="color:var(--ink-3)">glidande medel ${fmt(ind.ma[best], ind.dec)}</span>` : '';
    TT.innerHTML = `<span class="ttp">${pn} · ${keys[best]}</span>`+
      `<span class="ttv">${fmt(vals[best], ind.dec)}</span> <span style="color:var(--ink-3)">${ind.short}</span>`+mv;
    TT.style.opacity = 1;
    TT.style.left = Math.min(innerWidth-TT.offsetWidth-10, ev.clientX+14)+'px';
    TT.style.top = Math.max(8, ev.clientY-TT.offsetHeight-12)+'px';
  });
  hit.addEventListener('pointerleave', ()=>{
    TT.style.opacity=0; cross.setAttribute('opacity',0); dot.setAttribute('opacity',0);
  });
  host.textContent=''; host.appendChild(svg);
}

/* ---------------- överblick: fyra staplar per rad ---------------- */
function overview(host, rows, suffix){
  const W = host.clientWidth || 900;
  const bh = 7, gap = 2, rowH = 4*bh+3*gap, rgap = 14;
  const P = {t:6, r:62, b:26, l:Math.min(230, Math.max(150, W*.24))};
  const H = P.t + rows.length*(rowH+rgap) + P.b;
  const iw = W-P.l-P.r;
  const absv = rows.flatMap(r=>r.p).filter(v=>v!==null&&v!==undefined).map(Math.abs).sort((a,b)=>a-b);
  const q = absv[Math.min(absv.length-1, Math.floor(absv.length*.85))] || 1;
  const m = Math.max(q*1.15, .0001);
  const zero = P.l + iw*.5, half = iw*.5;
  const xs = v => zero + half*(v/m);
  const svg = el('svg',{viewBox:`0 0 ${W} ${H}`, width:'100%', height:H, role:'img',
    'aria-label':'Förändring per mandatperiod och mätpunkt'});

  rows.forEach((r,i)=>{
    const yTop = P.t + i*(rowH+rgap);
    const lab = el('text',{x:P.l-18, y:yTop+rowH/2+4, 'text-anchor':'end', fill:css('--ink'),
      'font-size':12, 'font-family':css('--display'), 'font-weight':600});
    lab.textContent = r.name; svg.appendChild(lab);
    const vc = r.verdict==='good'?'--good':r.verdict==='bad'?'--bad':'--flat';
    svg.appendChild(el('circle',{cx:P.l-8, cy:yTop+rowH/2, r:3.5, fill:css(vc)}));
    r.p.forEach((v,j)=>{
      const yb = yTop + j*(bh+gap);
      if (v===null || v===undefined){
        const t = el('text',{x:zero+5, y:yb+bh-.5, fill:css('--ink-3'), 'font-size':8.5,
                             'font-family':css('--mono')});
        t.textContent = '–'; svg.appendChild(t); return;
      }
      const clipped = Math.abs(v) > m;
      const vv = clipped ? (v>0?m:-m) : v;
      const w = Math.max(2, Math.abs(xs(vv)-zero));
      const x0 = v>=0 ? zero : zero-w;
      svg.appendChild(el('rect',{x:x0, y:yb, width:w, height:bh, fill:css(PCOL[j]), rx:1.5}));
      if (clipped){
        const tip = v>=0 ? x0+w : x0, dir = v>=0?1:-1;
        svg.appendChild(el('path',{d:`M${tip-dir*6},${yb} l${dir*3},${bh/3} l${-dir*3},${bh/3} l${dir*3},${bh/3}`,
          fill:'none', stroke:css('--sheet'), 'stroke-width':1.4}));
      }
      const t = el('text',{x: clipped ? (v>=0?x0+w-8:x0+8) : (v>=0?x0+w+5:x0-5),
        y: yb+bh-.5, 'text-anchor': clipped ? (v>=0?'end':'start') : (v>=0?'start':'end'),
        fill: clipped ? css('--sheet') : css('--ink-2'),
        'font-size':8.8, 'font-family':css('--display'), 'font-weight': clipped?600:400});
      t.textContent = (v>=0?'+':'−')+Math.abs(v).toFixed(1).replace('.',',')+suffix;
      svg.appendChild(t);
    });
  });
  svg.appendChild(el('line',{x1:zero,x2:zero,y1:P.t-2,y2:H-P.b+4,stroke:css('--ink'),'stroke-width':1}));
  const z = el('text',{x:zero,y:H-9,'text-anchor':'middle',fill:css('--ink-3'),
                       'font-size':10,'font-family':css('--mono')});
  z.textContent = '0'+suffix; svg.appendChild(z);
  host.textContent=''; host.appendChild(svg);
}

/* ---------------- sparkline ---------------- */
function spark(host, ind){
  const {keys, vals, seg} = ind;
  const W=104, H=26;
  const fin = vals.map((v,i)=>[i,v]).filter(d=>d[1]!==null);
  if (fin.length<2) return;
  let lo=Math.min(...fin.map(d=>d[1])), hi=Math.max(...fin.map(d=>d[1]));
  if(lo===hi){lo-=1;hi+=1;}
  const x=i=>1+(W-2)*i/(keys.length-1), y=v=>H-3-(H-6)*(v-lo)/(hi-lo);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`,width:W,height:H,class:'spark','aria-hidden':'true'});
  const col=s=>s>=1?css(PCOL[s-1]):css('--ink-3');
  for(let i=1;i<keys.length;i++){
    if(vals[i]===null||vals[i-1]===null) continue;
    svg.appendChild(el('line',{x1:x(i-1),y1:y(vals[i-1]),x2:x(i),y2:y(vals[i]),
      stroke:col(Math.max(seg[i],seg[i-1])),'stroke-width':1.4,'stroke-linecap':'round'}));
  }
  const li=fin[fin.length-1][0];
  svg.appendChild(el('circle',{cx:x(li),cy:y(vals[li]),r:2.2,fill:col(seg[li])}));
  host.textContent=''; host.appendChild(svg);
}

/* ---------------- helhetsmått per mandatperiod ---------------- */
function aggChart(host){
  const A = D.agg;                     // {labels, panels:[{name,vals,n,upp}]}
  const np = A.panels.length;
  const W = host.clientWidth || 760, bh = 14, gap = 3;
  const rowH = np*(bh+gap) + 20;
  const P = {t:30, r:16, b:34, l:Math.min(150, Math.max(96, W*.15))};
  const H = P.t + A.labels.length*rowH + P.b;
  const iw = W-P.l-P.r, hi = 100;
  const x = v => P.l + iw*v/hi;
  const svg = el('svg',{viewBox:`0 0 ${W} ${H}`, width:'100%', height:H, role:'img',
    'aria-label':'Andel av mätpunkterna som förbättrades under varje mandatperiod, två paneler'});
  [25,50,75,100].forEach(v=>{
    svg.appendChild(el('line',{x1:x(v),x2:x(v),y1:P.t-8,y2:H-P.b+2,
      stroke:css(v===50?'--ink-3':'--rule'),'stroke-width':1,
      'stroke-dasharray':v===50?'':'2 3'}));
    const t=el('text',{x:x(v),y:H-P.b+16,'text-anchor':'middle',fill:css('--ink-3'),
                       'font-size':9.5,'font-family':css('--mono')});
    t.textContent = v+' %'; svg.appendChild(t);
  });
  A.labels.forEach((lab,i)=>{
    const y0 = P.t + i*rowH;
    const t = el('text',{x:P.l-12,y:y0+bh+2,'text-anchor':'end',fill:css('--ink'),
      'font-size':12,'font-family':css('--display'),'font-weight':600});
    t.textContent = lab; svg.appendChild(t);
    A.panels.forEach((pan,k)=>{
      const yb = y0 + k*(bh+gap);
      const v = pan.vals[i];
      if (v === null || v === undefined){
        const m = el('text',{x:P.l+4,y:yb+bh-3,fill:css('--ink-3'),'font-size':9,
                             'font-family':css('--mono')});
        m.textContent = 'utanför panelen'; svg.appendChild(m); return;
      }
      const w = Math.max(2, x(v)-P.l);
      svg.appendChild(el('rect',{x:P.l,y:yb,width:w,height:bh,
        fill:css(PCOL[i]), opacity: k===0?1:.45, rx:2}));
      const lv = el('text',{x:P.l+w+7,y:yb+bh-3,fill:css('--ink-2'),'font-size':10.5,
        'font-family':css('--display'),'font-weight':600});
      lv.textContent = v.toFixed(0).replace('.',',')+' %  ('+pan.upp[i]+' av '+pan.n[i]+')';
      svg.appendChild(lv);
    });
  });
  A.panels.forEach((pan,k)=>{
    const gx = P.l + k*Math.min(260, iw/np);
    svg.appendChild(el('rect',{x:gx,y:6,width:12,height:9,fill:css('--ink-3'),
                               opacity:k===0?1:.45,rx:2}));
    const t = el('text',{x:gx+17,y:14,fill:css('--ink-3'),'font-size':9,
                         'font-family':css('--display')});
    t.textContent = pan.name; svg.appendChild(t);
  });
  host.textContent=''; host.appendChild(svg);
}

function draw(){
  document.querySelectorAll('[data-chart]').forEach(h=>{
    const i=D.charts[h.dataset.chart]; if(i) seriesChart(h,i);
  });
  document.querySelectorAll('[data-spark]').forEach(h=>{
    const i=D.charts[h.dataset.spark]; if(i) spark(h,i);
  });
  const ag=document.getElementById('aggChart'); if(ag) aggChart(ag);
  const a=document.getElementById('ovPP'); if(a) overview(a, D.ovPP, NB+'p.e.');
  const b=document.getElementById('ovREL'); if(b) overview(b, D.ovREL, NB+'%');
}
draw();
let rt; addEventListener('resize',()=>{clearTimeout(rt); rt=setTimeout(draw,180);});
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', draw);
new MutationObserver(draw).observe(document.documentElement,{attributes:true,attributeFilter:['data-theme']});
})();
"""
