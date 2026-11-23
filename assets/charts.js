/* Diagramme ohne Bibliothek: <figure class="viz" data-viz="name" ...>. Siehe assets/charts.css. */
(function(){
"use strict";
const NS="http://www.w3.org/2000/svg";
const eur=v=>Math.round(v).toLocaleString("de-DE")+" €";
const eurS=v=>{const a=Math.abs(v);
  if(a>=1e6)return (v/1e6).toLocaleString("de-DE",{maximumFractionDigits:a>=1e7?0:1})+" Mio. €";
  if(a>=1e3)return Math.round(v/1e3).toLocaleString("de-DE")+" Tsd. €";
  return Math.round(v)+" €";};
const el=(tag,attrs,parent)=>{const n=document.createElementNS(NS,tag);for(const k in attrs)n.setAttribute(k,attrs[k]);if(parent)parent.appendChild(n);return n;};
const h=(tag,cls,html)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(html!=null)n.innerHTML=html;return n;};
function niceStep(raw){const p=Math.pow(10,Math.floor(Math.log10(raw||1)));const f=raw/p;return (f<=1?1:f<=2?2:f<=2.5?2.5:f<=5?5:10)*p;}

/* Grundgerüst: Titel, Legende, Plotfläche, Tooltip, Tabelle */
function frame(fig){
  if(fig._f) return fig._f;
  const cap=h("figcaption","",`<b>${fig.dataset.title||""}</b>${fig.dataset.sub?`<span>${fig.dataset.sub}</span>`:""}`);
  const legend=h("ul","vlegend"); const plot=h("div","vplot"); const tip=h("div","vtip");
  const note=h("p","vnote"); const det=h("details","","<summary>Werte als Tabelle</summary>");
  plot.appendChild(tip); fig.replaceChildren(cap,legend,plot,note,det);
  fig._f={legend,plot,tip,note,det}; return fig._f;
}
function setLegend(f,series){
  f.legend.replaceChildren(...series.map(s=>{const li=h("li","",`<i class="${s.dash?"dash":""}" style="color:${s.color}"></i>${s.name}`);return li;}));
  f.legend.hidden=series.length<2;
}
function setTable(f,head,rows){
  const t=h("table");t.innerHTML="<thead><tr>"+head.map(x=>`<th>${x}</th>`).join("")+"</tr></thead><tbody>"+
    rows.map(r=>"<tr>"+r.map(x=>`<td>${x}</td>`).join("")+"</tr>").join("")+"</tbody>";
  const old=f.det.querySelector("table"); old?old.replaceWith(t):f.det.appendChild(t);
}

/* Liniendiagramm: cfg = {x:[], xFmt, xTip, series:[{name,color,values,dash,area}], ref:{value,label}, step} */
function line(fig,cfg){
  const f=frame(fig); setLegend(f,cfg.series);
  const W=Math.max(280,f.plot.clientWidth), H=W<480?220:270, m={l:W<480?52:64,r:12,t:16,b:26};
  const iw=W-m.l-m.r, ih=H-m.t-m.b, n=cfg.x.length;
  let max=cfg.ref?cfg.ref.value:0; cfg.series.forEach(s=>s.values.forEach(v=>{if(v>max)max=v;}));
  const st=niceStep(max/4), yMax=Math.ceil(max*1.04/st)*st||1;
  const X=i=>m.l+(n<2?0:i*iw/(n-1)), Y=v=>m.t+ih-(Math.max(0,v)/yMax)*ih;
  f.plot.querySelector("svg")?.remove();
  const svg=el("svg",{viewBox:`0 0 ${W} ${H}`,height:H,role:"img","aria-label":fig.dataset.title||"Diagramm"});
  f.plot.insertBefore(svg,f.tip);
  for(let v=0;v<=yMax+1e-9;v+=st){const y=Y(v);
    el("line",{x1:m.l,x2:W-m.r,y1:y,y2:y,stroke:"var(--vgrid)","stroke-width":1},svg);
    const t=el("text",{x:m.l-8,y:y+4,"text-anchor":"end"},svg);t.textContent=eurS(v);}
  const xt=Math.max(1,Math.ceil((n-1)/(W<480?4:7)));
  for(let i=0;i<n;i+=xt){const t=el("text",{x:X(i),y:H-6,"text-anchor":i===0?"start":"middle"},svg);t.textContent=cfg.xFmt(cfg.x[i],i);}
  if(cfg.ref){const y=Y(cfg.ref.value);
    el("line",{x1:m.l,x2:W-m.r,y1:y,y2:y,stroke:"var(--vref)","stroke-width":1.5,"stroke-dasharray":"5 4"},svg);
    const t=el("text",{x:m.l+6,y:y-6,class:"lbl"},svg);t.textContent=cfg.ref.label;}
  cfg.series.forEach(s=>{
    const pts=s.values.map((v,i)=>v==null?null:[X(i),Y(v)]);
    let d="",pen=false; pts.forEach(p=>{if(!p){pen=false;return;}d+=(pen?"L":"M")+p[0].toFixed(1)+","+p[1].toFixed(1);pen=true;});
    if(s.area){const ok=pts.filter(Boolean);el("path",{d:d+`L${ok[ok.length-1][0]},${Y(0)}L${ok[0][0]},${Y(0)}Z`,fill:s.color,opacity:.13},svg);}
    el("path",{d,fill:"none",stroke:s.color,"stroke-width":2,"stroke-linejoin":"round","stroke-linecap":"round","stroke-dasharray":s.dash?"6 5":"none"},svg);
  });
  // Direktbeschriftung am Linienende (Kollisionen auseinanderschieben)
  const ends=cfg.series.filter(s=>!s.noLabel).map(s=>({s,y:Y(s.values[n-1]||0)-8})).sort((a,b)=>a.y-b.y);
  for(let i=1;i<ends.length;i++) if(ends[i].y-ends[i-1].y<15) ends[i].y=ends[i-1].y+15;
  ends.forEach(e=>{const t=el("text",{x:W-m.r-2,y:Math.max(m.t+10,e.y),"text-anchor":"end",class:"lbl"},svg);t.textContent=e.s.short||e.s.name;});
  // Hover: Fadenkreuz + Tooltip
  const g=el("g",{opacity:0},svg); const cross=el("line",{y1:m.t,y2:m.t+ih,stroke:"var(--vref)","stroke-width":1},g);
  const dots=cfg.series.map(s=>el("circle",{r:4.5,fill:s.color,stroke:"var(--vsurf)","stroke-width":2},g));
  const hit=el("rect",{x:m.l,y:0,width:iw,height:H,fill:"transparent"},svg);
  const move=ev=>{const r=svg.getBoundingClientRect();const px=(ev.clientX-r.left)*(W/r.width);
    const i=Math.max(0,Math.min(n-1,Math.round((px-m.l)/(iw/(Math.max(1,n-1))))));const x=X(i);
    g.setAttribute("opacity",1);cross.setAttribute("x1",x);cross.setAttribute("x2",x);
    cfg.series.forEach((s,k)=>{const v=s.values[i];dots[k].setAttribute("cx",x);dots[k].setAttribute("cy",Y(v||0));dots[k].style.display=v==null?"none":"";});
    f.tip.innerHTML=`<b>${cfg.xTip(cfg.x[i],i)}</b>`+cfg.series.filter(s=>s.values[i]!=null).map(s=>`<div><i style="background:${s.color}"></i>${s.name}<em>${eur(s.values[i])}</em></div>`).join("");
    f.tip.classList.add("on");const tw=f.tip.offsetWidth,sx=x*(r.width/W);
    f.tip.style.left=(sx+14+tw>r.width?sx-14-tw:sx+14)+"px";f.tip.style.top=Math.max(0,(ev.clientY-r.top)-40)+"px";};
  const leave=()=>{g.setAttribute("opacity",0);f.tip.classList.remove("on");};
  hit.addEventListener("pointermove",move);hit.addEventListener("pointerdown",move);hit.addEventListener("pointerleave",leave);
  const step=cfg.step||Math.max(1,Math.ceil((n-1)/10)),rows=[];
  for(let i=0;i<n;i+=step) rows.push(i);
  if(rows[rows.length-1]!==n-1) rows.push(n-1);
  setTable(f,[cfg.xHead||"Jahr",...cfg.series.map(s=>s.name)],rows.map(i=>[cfg.xTip(cfg.x[i],i),...cfg.series.map(s=>s.values[i]==null?"–":eur(s.values[i]))]));
}

/* Balken (horizontal): cfg = {items:[{name,value,color,label}], fmt} */
function bars(fig,cfg){
  const f=frame(fig); f.legend.hidden=true;
  const W=Math.max(280,f.plot.clientWidth), bh=26, gap=34, m={l:0,r:W<480?80:110,t:4};
  const H=m.t+cfg.items.length*(bh+gap);
  const max=Math.max(...cfg.items.map(i=>i.value));
  f.plot.querySelector("svg")?.remove();
  const svg=el("svg",{viewBox:`0 0 ${W} ${H}`,height:H,role:"img","aria-label":fig.dataset.title||"Diagramm"});
  f.plot.insertBefore(svg,f.tip);
  cfg.items.forEach((it,k)=>{const y=m.t+k*(bh+gap)+18, w=(W-m.l-m.r)*it.value/max;
    const t=el("text",{x:0,y:y-6},svg);t.textContent=it.name;
    el("path",{d:`M0,${y}h${w-4}a4,4 0 0 1 4,4v${bh-8}a4,4 0 0 1 -4,4h${-(w-4)}z`,fill:it.color},svg);
    const v=el("text",{x:w+8,y:y+bh/2+4,class:"lbl"},svg);v.textContent=it.label||eurS(it.value);
    const r=el("rect",{x:0,y:y-20,width:W,height:bh+24,fill:"transparent"},svg);
    r.addEventListener("pointermove",ev=>{const b=svg.getBoundingClientRect();f.tip.innerHTML=`<b>${it.name}</b><div><i style="background:${it.color}"></i>${it.tip||""}<em>${eur(it.value)}</em></div>`;
      f.tip.classList.add("on");f.tip.style.left=Math.min(b.width-f.tip.offsetWidth,ev.clientX-b.left+12)+"px";f.tip.style.top=(y-40)*(b.width/W)+"px";});
    r.addEventListener("pointerleave",()=>f.tip.classList.remove("on"));
  });
  setTable(f,["",cfg.valHead||"Wert"],cfg.items.map(i=>[i.name,eur(i.value)]));
}

/* ---------- Die einzelnen Diagramme ---------- */
const num=id=>{const n=document.getElementById(id);return n?(+n.value||0):0;};
const R={
  // Depotentwicklung zum Rechner. data-inputs="ziel,sparrate,depot,rendite,entnahme" (IDs der Eingabefelder)
  sparplan(fig){
    const [a,b,c,d,e]=fig.dataset.inputs.split(","); const t=num(a),rate=num(b),s0=num(c),y=num(d)/100,wd=(e?num(e):3.5)/100||0.035;
    const need=t*12/wd; let v=s0,mo=0; while(v<need&&mo<600){v=v*(1+y/12)+rate;mo++;}
    const years=Math.min(50,Math.max(10,Math.ceil(mo/12)+3));
    const xs=[],dep=[],paid=[]; v=s0;
    for(let yr=0;yr<=years;yr++){xs.push(yr);dep.push(v);paid.push(s0+rate*12*yr);for(let k=0;k<12;k++)v=v*(1+y/12)+rate;}
    line(fig,{x:xs,xFmt:x=>x===0?"heute":x+" J.",xTip:x=>x===0?"Heute":"Nach "+x+(x===1?" Jahr":" Jahren"),
      series:[{name:"Depotwert",short:"Depot",color:"var(--v1)",values:dep,area:true},{name:"Selbst eingezahlt",short:"Eingezahlt",color:"var(--vref)",values:paid,dash:true}],
      ref:{value:need,label:"Ziel: "+eurS(need)}});
    const gain=dep[dep.length-1]-paid[paid.length-1];
    frame(fig).note.textContent=(mo>=600?"Ziel wird in 50 Jahren nicht erreicht. ":`Ziel nach rund ${Math.floor(mo/12)} Jahren und ${mo%12} Monaten. `)+
      `Nach ${years} Jahren stammen ${eurS(Math.max(0,gain))} aus Zinseszins. Annahme: ${(y*100).toLocaleString("de-DE")} % Rendite pro Jahr, ohne Steuern und Inflation, keine Prognose.`;
  },
  // Gleiche Sparrate, unterschiedlicher Start
  fruehstart(fig){
    const rate=+fig.dataset.rate||300, y=(+fig.dataset.ret||6)/100, end=67, starts=[25,35,45], cols=["var(--v1)","var(--v2)","var(--v3)"];
    const xs=[];for(let a=25;a<=end;a++)xs.push(a);
    const series=starts.map((st,k)=>{let v=0;const vals=xs.map(a=>{if(a<st)return null;const out=v;for(let i=0;i<12;i++)v=v*(1+y/12)+rate;return out;});
      return {name:"Start mit "+st,short:"ab "+st,color:cols[k],values:vals};});
    line(fig,{x:xs,xFmt:a=>a+"",xTip:a=>"Mit "+a+" Jahren",xHead:"Alter",series,step:5});
    frame(fig).note.textContent=series.map((s,k)=>`Start mit ${starts[k]}: ${eurS(rate*12*(end-starts[k]))} eingezahlt, ${eurS(s.values[s.values.length-1])} mit 67`).join(" · ")+
      `. Annahme: ${rate} € im Monat, ${(y*100).toLocaleString("de-DE")} % Rendite pro Jahr, ohne Steuern und Inflation.`;
  },
  // Sequenzrisiko: gleiche Renditen, andere Reihenfolge. data-inputs="depot,entnahme"
  sequenz(fig){
    const [a,b]=fig.dataset.inputs.split(","); const d0=num(a)||300000, w=num(b)/100||0.04, infl=0.02, N=30;
    const early=[-0.20,-0.10,...Array(N-2).fill(0.08)], late=[...early].reverse();
    const geo=Math.pow(early.reduce((p,r)=>p*(1+r),1),1/N)-1, even=Array(N).fill(geo);
    const run=rs=>{let v=d0,wd=d0*w;const out=[v];rs.forEach(r=>{v=Math.max(0,(v-wd)*(1+r));wd*=1+infl;out.push(v);});return out;};
    const xs=[...Array(N+1).keys()];
    line(fig,{x:xs,xFmt:x=>x===0?"Start":x+" J.",xTip:x=>x===0?"Ruhestand beginnt":"Nach "+x+(x===1?" Jahr":" Jahren"),
      series:[{name:"Crash in Jahr 1 und 2",short:"Crash früh",color:"var(--v3)",values:run(early)},
              {name:"Jedes Jahr gleich",short:"gleichmäßig",color:"var(--v2)",values:run(even)},
              {name:"Crash in Jahr 29 und 30",short:"Crash spät",color:"var(--v1)",values:run(late)}],step:5});
    frame(fig).note.textContent=`Alle drei Wege haben dieselbe Durchschnittsrendite von ${(geo*100).toLocaleString("de-DE",{maximumFractionDigits:1})} % pro Jahr (−20 %, −10 % und 28 × +8 %, nur in anderer Reihenfolge). Entnahme ${(w*100).toLocaleString("de-DE")} % im ersten Jahr, danach jedes Jahr +2 % Inflation. Rechenbeispiel, keine Prognose.`;
  },
  // Dividenden-ETF vs. Welt-ETF, 100.000 € seit Mitte 2019 (Zahlen aus dem Finanztip-Vergleich)
  dividende(fig){
    bars(fig,{valHead:"Wert heute",items:[
      {name:"FTSE All-World (≈ +134 %)",value:234000,color:"var(--v1)",tip:"Wert heute"},
      {name:"All-World High Dividend (≈ +106 %)",value:206000,color:"var(--v2)",tip:"Wert heute"}]});
    frame(fig).note.textContent="Aus 100.000 € Mitte 2019 wurden rund 234.000 € bzw. 206.000 €, beide thesaurierend gerechnet. Vergangenheit, keine Prognose; in anderen Marktphasen kann es umgekehrt laufen.";
  }
};

function render(fig){const fn=R[fig.dataset.viz];if(fn){try{fn(fig);}catch(e){console.error("viz",e);}}}
function init(){
  document.querySelectorAll("figure.viz[data-viz]").forEach(fig=>{
    render(fig);
    (fig.dataset.inputs||"").split(",").filter(Boolean).forEach(id=>document.getElementById(id)?.addEventListener("input",()=>render(fig)));
    let w=fig.clientWidth; new ResizeObserver(()=>{if(Math.abs(fig.clientWidth-w)>8){w=fig.clientWidth;render(fig);}}).observe(fig);
  });
}
document.readyState==="loading"?document.addEventListener("DOMContentLoaded",init):init();
})();
