"""Standalone countdown page over HTTP — for browsers and OBS Browser Source.

Serves a self-contained page that mirrors the in-app countdown stage
(same phase machine: pre -> main -> done) and polls /config.json every 5 s,
so changes made in the launcher (logos, style, start time, theme) appear
live in any open tab/OBS source. `?transparent=1` clears the background
for stream overlays.
"""
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from socketserver import ThreadingMixIn

DEFAULT_PORT = 8771


class _ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


PAGE = r"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>JamDeck — Countdown</title>
<style>
:root{
  --bg:#050a14; --bg-2:#080e1c; --surface:#0f1629; --surface-2:#141d33; --border:#1e293b;
  --accent:#00f2ff; --accent-2:#0062ff; --text:#ffffff; --text-muted:#94a3b8; --error:#ff1744;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{background:var(--bg); color:var(--text); overflow:hidden;
  font-family:"Segoe UI",system-ui,sans-serif}
body.transparent{background:transparent}
/* launcher'daki gibi arka plan efekti canvas'ı (en altta) */
#fx{position:fixed; inset:0; width:100%; height:100%; z-index:0; pointer-events:none}
.cd-stage{position:relative; z-index:1; height:100vh; display:flex; flex-direction:column;
  align-items:center; justify-content:space-between; padding:4vh 4vw; overflow:hidden}
.cd-logos{width:100%; display:grid; grid-template-columns:1fr auto 1fr; align-items:start; gap:24px}
.cd-logos .cd-side{max-height:12vh; max-width:20vw; object-fit:contain}
.cd-logos .cd-side.r{justify-self:end}
.cd-logos .cd-center{max-height:30vh; max-width:46vw; object-fit:contain; justify-self:center}
.cd-center-ph{justify-self:center; align-self:center; border:2px dashed var(--border);
  border-radius:18px; padding:4vh 6vw; color:var(--text-muted);
  font-weight:800; letter-spacing:.2em; text-align:center}
body.transparent .cd-center-ph{display:none}
.cd-bottom{display:flex; flex-direction:column; align-items:center; gap:1.4vh; padding-bottom:2.5vh}
.cd-phase{font-weight:700; letter-spacing:.35em; font-size:clamp(14px,1.6vw,26px); color:var(--text-muted)}
.cd-digit-wrap{position:relative}
.cd-digits{position:relative; z-index:1; font-weight:800;
  font-size:clamp(64px,13vw,250px); line-height:1; letter-spacing:.04em;
  font-variant-numeric:tabular-nums; display:flex; color:var(--text)}
.cd-d,.cd-sep{display:inline-block; text-align:center}
.cd-d{width:.64em}
.cd-sep{width:.38em}
.cd-ghost{display:none; position:absolute; inset:0; z-index:0; opacity:.1; pointer-events:none;
  font-size:clamp(64px,13vw,250px); font-weight:800; line-height:1; letter-spacing:.04em;
  font-variant-numeric:tabular-nums}
.cd-done-msg{font-weight:800; font-size:clamp(28px,4.5vw,80px); color:var(--error);
  text-align:center; letter-spacing:.04em; text-shadow:0 0 40px rgba(255,23,68,.5);
  animation:cdFlash 1s steps(2,start) infinite}
@keyframes cdFlash{50%{opacity:.12}}
.cd-stage.done .cd-digits{color:var(--error)}
.cd-style-neon .cd-digits{color:var(--accent);
  text-shadow:0 0 14px var(--accent), 0 0 60px var(--accent)}
.cd-style-minimal .cd-digits{font-weight:200; letter-spacing:.02em}
.cd-style-segment .cd-digits{font-family:Consolas,"Cascadia Mono",monospace; font-weight:700;
  color:#ff7a18; text-shadow:0 0 16px rgba(255,122,24,.45)}
.cd-style-segment .cd-ghost{display:flex; font-family:Consolas,"Cascadia Mono",monospace;
  font-weight:700; color:#ff7a18}
.cd-style-flip .cd-digits{gap:.06em}
.cd-style-flip .cd-d{background:var(--surface); border:1px solid var(--border); border-radius:.1em;
  padding:.1em .06em; box-shadow:inset 0 -.45em .9em rgba(0,0,0,.3), 0 .08em .25em rgba(0,0,0,.35);
  position:relative; overflow:hidden}
.cd-style-flip .cd-d::after{content:""; position:absolute; left:0; right:0; top:50%; height:1.5px;
  background:rgba(0,0,0,.45)}
.cd-style-flip .cd-sep{padding:.1em 0}
.cd-style-terminal .cd-digits{font-family:Consolas,"Cascadia Mono",monospace; font-weight:700;
  color:#33ff66; text-shadow:0 0 12px rgba(51,255,102,.55)}
.cd-style-terminal.cd-stage::before{content:""; position:absolute; inset:0; z-index:2; pointer-events:none;
  background:repeating-linear-gradient(0deg, transparent 0 2px, rgba(0,0,0,.16) 2px 4px)}
body.transparent .cd-style-terminal.cd-stage::before{display:none}
.cd-cursor{display:none}
.cd-style-terminal .cd-cursor{display:inline-block; width:.45em; background:#33ff66; margin-left:.12em;
  animation:cdFlash 1.1s steps(2,start) infinite}
.cd-d.cd-px{width:.78em; height:1em; display:grid; grid-template-columns:repeat(5,1fr);
  grid-auto-rows:1fr; gap:7%; padding:.02em 0}
.cd-px.sep{width:.5em}
.cd-px i{border-radius:18%}
.cd-px i.on{background:currentColor; box-shadow:0 0 .03em currentColor}
.cd-style-pixel .cd-digits{color:var(--accent); gap:.12em}
.cd-style-pixel.cd-stage::before{content:""; position:absolute; inset:0; z-index:2; pointer-events:none;
  background:repeating-linear-gradient(0deg, transparent 0 3px, rgba(0,0,0,.12) 3px 6px)}
body.transparent .cd-style-pixel.cd-stage::before{display:none}
.cd-style-glitch .cd-digits{color:var(--text);
  text-shadow:.035em 0 var(--error), -.035em 0 var(--accent);
  animation:cdGlitch 2.4s steps(1) infinite}
@keyframes cdGlitch{
  0%,84%,100%{transform:none}
  86%{transform:translate(.02em,-.012em) skewX(4deg)}
  89%{transform:translate(-.018em,.008em) skewX(-3deg)}
  92%{transform:translate(.008em,0)}
  94%{transform:none}
}
.cd-bar{display:none; width:min(72vw,920px); border:2px solid var(--border); border-radius:999px;
  padding:4px; background:rgba(255,255,255,.04)}
.cd-style-hpbar .cd-bar{display:block}
.cd-bar i{display:block; height:clamp(14px,2.6vh,26px); width:100%; border-radius:999px;
  background:linear-gradient(90deg,#16a34a,#a3e635); transition:width .9s linear}
.cd-bar.low i{background:linear-gradient(90deg,#dc2626,#f97316);
  animation:cdFlash 1s steps(2,start) infinite}
.cd-style-hpbar .cd-digits{color:var(--text)}
</style>
</head>
<body>
<canvas id="fx"></canvas>
<div class="cd-stage" id="stage">
  <div class="cd-logos" id="logos"></div>
  <div class="cd-bottom">
    <div class="cd-phase" id="phase"></div>
    <div class="cd-digit-wrap">
      <div class="cd-ghost" id="ghost" aria-hidden="true"></div>
      <div class="cd-digits" id="digits"></div>
    </div>
    <div class="cd-bar" id="bar"><i></i></div>
    <div class="cd-done-msg" id="doneMsg" hidden></div>
  </div>
</div>
<script>
const qs=new URLSearchParams(location.search);
if(qs.get("transparent")) document.body.classList.add("transparent");

/* ============================================================
   ARKA PLAN EFEKTİ — launcher motorundan birebir (14 efekt)
   Tema renklerini canlı okur; rAF/resize/aç-kapa/intensity yönetir.
   ============================================================ */
function themeColors(){
  const cs=getComputedStyle(document.documentElement);
  const g=v=>cs.getPropertyValue(v).trim()||"#ffffff";
  const acc=g("--accent");
  return { accent:acc, accent2:(g("--accent-2")||acc), text:g("--text"),
           bg:g("--bg"), bg2:(g("--bg-2")||g("--bg")), surface:g("--surface") };
}
function hexToRgb(hex){ hex=(hex||"#000").replace("#",""); if(hex.length===3) hex=hex.split("").map(c=>c+c).join("");
  const n=parseInt(hex.slice(0,6),16); return {r:(n>>16)&255,g:(n>>8)&255,b:n&255}; }
function rgba(hex,a){ const c=hexToRgb(hex); return `rgba(${c.r},${c.g},${c.b},${a})`; }
function lerpColor(h1,h2,t){ const a=hexToRgb(h1),b=hexToRgb(h2);
  return `rgb(${Math.round(a.r+(b.r-a.r)*t)},${Math.round(a.g+(b.g-a.g)*t)},${Math.round(a.b+(b.b-a.b)*t)})`; }
const rnd=(a,b)=>a+Math.random()*(b-a);
const Effects={
  none:{ init(){}, frame(ctx,w,h){ ctx.clearRect(0,0,w,h); } },
  snow:{ init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>({x:Math.random()*w,y:Math.random()*h,r:rnd(1,3.4),sp:rnd(.3,1.1),dr:rnd(-.4,.4),ph:rnd(0,6.28)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      for(const f of this.p){ f.y+=f.sp*o.speed; f.x+=Math.sin(t*0.001+f.ph)*0.3+f.dr;
        if(f.y>h+5){f.y=-5;f.x=Math.random()*w} if(f.x>w+5)f.x=-5; if(f.x<-5)f.x=w+5;
        ctx.beginPath();ctx.arc(f.x,f.y,f.r,0,6.283);ctx.fillStyle=rgba(c.text,0.55*(f.r/3.4));ctx.fill(); } } },
  rain:{ init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>({x:Math.random()*w,y:Math.random()*h,len:rnd(10,26),sp:rnd(7,15)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); ctx.lineWidth=1.1;
      for(const d of this.p){ d.y+=d.sp*o.speed; d.x+=d.sp*0.32*o.speed;
        if(d.y>h){d.y=-d.len;d.x=Math.random()*w}
        ctx.strokeStyle=rgba(c.accent,0.22); ctx.beginPath(); ctx.moveTo(d.x,d.y); ctx.lineTo(d.x-d.len*0.32,d.y-d.len); ctx.stroke(); } } },
  starfield:{ init(ctx,w,h,o){ this.cx=w/2;this.cy=h/2; this.s=Array.from({length:o.count},()=>({x:rnd(-w,w),y:rnd(-h,h),z:rnd(1,w)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); const cx=w/2,cy=h/2;
      for(const s of this.s){ s.z-=2.2*o.speed; if(s.z<1){s.x=rnd(-w,w);s.y=rnd(-h,h);s.z=w}
        const k=128/s.z, x=cx+s.x*k, y=cy+s.y*k, px=cx+s.x*(128/(s.z+2.2*o.speed)), py=cy+s.y*(128/(s.z+2.2*o.speed));
        const a=Math.min(1,(w-s.z)/w); ctx.strokeStyle=rgba(c.accent,a*0.8); ctx.lineWidth=Math.max(.5,(1-s.z/w)*2.4);
        ctx.beginPath();ctx.moveTo(px,py);ctx.lineTo(x,y);ctx.stroke(); } } },
  plexus:{ init(ctx,w,h,o){ const n=Math.min(o.count,140); this.p=Array.from({length:n},()=>({x:Math.random()*w,y:Math.random()*h,vx:rnd(-.4,.4),vy:rnd(-.4,.4)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); const d2=150*150;
      for(const p of this.p){ p.x+=p.vx*o.speed;p.y+=p.vy*o.speed; if(p.x<0||p.x>w)p.vx*=-1; if(p.y<0||p.y>h)p.vy*=-1; }
      for(let i=0;i<this.p.length;i++){ const a=this.p[i];
        for(let j=i+1;j<this.p.length;j++){ const b=this.p[j]; const dx=a.x-b.x,dy=a.y-b.y,dd=dx*dx+dy*dy;
          if(dd<d2){ ctx.strokeStyle=rgba(c.accent,(1-dd/d2)*0.3); ctx.lineWidth=.7; ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke(); } }
        ctx.beginPath();ctx.arc(a.x,a.y,2,0,6.283);ctx.fillStyle=rgba(c.accent,0.8);ctx.fill(); } } },
  orbs:{ init(ctx,w,h,o){ const n=Math.max(6,Math.round(o.count/14)); this.o=Array.from({length:n},()=>({x:Math.random()*w,y:Math.random()*h,r:rnd(40,150),vx:rnd(-.3,.3),vy:rnd(-.3,.3),a:rnd(.05,.18),c:Math.random()<.5})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      for(const b of this.o){ b.x+=b.vx*o.speed;b.y+=b.vy*o.speed;
        if(b.x<-b.r)b.x=w+b.r; if(b.x>w+b.r)b.x=-b.r; if(b.y<-b.r)b.y=h+b.r; if(b.y>h+b.r)b.y=-b.r;
        const col=b.c?c.accent:c.accent2; const g=ctx.createRadialGradient(b.x,b.y,0,b.x,b.y,b.r);
        g.addColorStop(0,rgba(col,b.a)); g.addColorStop(1,rgba(col,0)); ctx.fillStyle=g;ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,6.283);ctx.fill(); } } },
  matrix:{ init(ctx,w,h,o){ this.fs=16; this.cols=Math.floor(w/this.fs); this.y=Array.from({length:this.cols},()=>rnd(-50,0)); this.glyph="0123456789<>[]{}#$%&ABCDEF"; },
    frame(ctx,w,h,t,o){ const c=themeColors(); ctx.fillStyle=rgba(c.bg,0.12); ctx.fillRect(0,0,w,h); ctx.font=this.fs+"px monospace";
      for(let i=0;i<this.cols;i++){ const ch=this.glyph[Math.floor(Math.random()*this.glyph.length)]; const x=i*this.fs,y=this.y[i]*this.fs;
        ctx.fillStyle=rgba(c.text,0.9); ctx.fillText(ch,x,y); ctx.fillStyle=rgba(c.accent,0.85); ctx.fillText(ch,x,y-this.fs);
        if(y>h&&Math.random()>0.975)this.y[i]=0; this.y[i]+=0.45*o.speed; } } },
  aurora:{ init(ctx,w,h,o){ this.blobs=Array.from({length:4},(_,i)=>({ph:rnd(0,6.28),sp:rnd(.0002,.0006),r:rnd(.4,.7),i})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); const cols=[c.accent,c.accent2,c.accent,c.accent2];
      for(const b of this.blobs){ const x=w*(0.5+0.4*Math.sin(t*b.sp*o.speed+b.ph)); const y=h*(0.4+0.35*Math.cos(t*b.sp*1.4*o.speed+b.ph)); const rr=Math.min(w,h)*b.r;
        const g=ctx.createRadialGradient(x,y,0,x,y,rr); g.addColorStop(0,rgba(cols[b.i],0.22)); g.addColorStop(1,rgba(cols[b.i],0)); ctx.fillStyle=g; ctx.beginPath();ctx.arc(x,y,rr,0,6.283);ctx.fill(); } } },
  confetti:{ init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>this.spawn(w,h,true)); },
    spawn(w,h,init){ return {x:Math.random()*w,y:init?Math.random()*h:-10,vx:rnd(-1,1),vy:rnd(2,5),s:rnd(5,11),rot:rnd(0,6.28),vr:rnd(-.2,.2),k:Math.random()}; },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); const pal=[c.accent,c.accent2,c.text];
      for(let i=0;i<this.p.length;i++){ const q=this.p[i]; q.x+=q.vx*o.speed;q.y+=q.vy*o.speed;q.rot+=q.vr*o.speed; if(q.y>h+12)this.p[i]=this.spawn(w,h,false);
        ctx.save();ctx.translate(q.x,q.y);ctx.rotate(q.rot); ctx.fillStyle=pal[Math.floor(q.k*pal.length)]; ctx.globalAlpha=.85; ctx.fillRect(-q.s/2,-q.s/2,q.s,q.s*0.6); ctx.restore();ctx.globalAlpha=1; } } },
  fireflies:{ init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>({x:Math.random()*w,y:Math.random()*h,vx:rnd(-.3,.3),vy:rnd(-.6,-.1),ph:rnd(0,6.28),r:rnd(1,2.6)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      for(const f of this.p){ f.x+=f.vx*o.speed+Math.sin(t*0.001+f.ph)*0.2; f.y+=f.vy*o.speed; if(f.y<-5){f.y=h+5;f.x=Math.random()*w}
        const a=0.4+0.5*Math.sin(t*0.003+f.ph); const g=ctx.createRadialGradient(f.x,f.y,0,f.x,f.y,f.r*4); g.addColorStop(0,rgba(c.accent,a)); g.addColorStop(1,rgba(c.accent,0));
        ctx.fillStyle=g;ctx.beginPath();ctx.arc(f.x,f.y,f.r*4,0,6.283);ctx.fill(); ctx.fillStyle=rgba(c.text,a);ctx.beginPath();ctx.arc(f.x,f.y,f.r,0,6.283);ctx.fill(); } } },
  gradient:{ init(){}, frame(ctx,w,h,t,o){ const c=themeColors(); const a=(Math.sin(t*0.0003*o.speed)+1)/2; const x1=w*a,y1=h*(1-a),x2=w*(1-a),y2=h*a;
      const g=ctx.createLinearGradient(x1,y1,x2,y2); g.addColorStop(0,rgba(c.accent,0.5)); g.addColorStop(.5,rgba(c.bg,0.2)); g.addColorStop(1,rgba(c.accent2,0.5));
      ctx.clearRect(0,0,w,h); ctx.fillStyle=g; ctx.fillRect(0,0,w,h); } },
  lowpoly:{ init(ctx,w,h,o){ const n=Math.max(6,Math.round(o.count/12)); this.tr=Array.from({length:n},()=>({x:Math.random()*w,y:Math.random()*h,r:rnd(30,90),rot:rnd(0,6.28),vr:rnd(-.005,.005),vx:rnd(-.25,.25),vy:rnd(-.25,.25),sides:Math.random()<.5?3:4})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); ctx.lineWidth=1.2;
      for(const p of this.tr){ p.x+=p.vx*o.speed;p.y+=p.vy*o.speed;p.rot+=p.vr*o.speed; if(p.x<-p.r)p.x=w+p.r; if(p.x>w+p.r)p.x=-p.r; if(p.y<-p.r)p.y=h+p.r; if(p.y>h+p.r)p.y=-p.r;
        ctx.strokeStyle=rgba(c.accent,0.28); ctx.beginPath(); for(let i=0;i<=p.sides;i++){ const a=p.rot+i/p.sides*6.283; const x=p.x+Math.cos(a)*p.r,y=p.y+Math.sin(a)*p.r; i?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke(); } } },
  bubbles:{ init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>({x:Math.random()*w,y:Math.random()*h,r:rnd(4,16),sp:rnd(.5,1.6),ph:rnd(0,6.28),wob:rnd(.4,1.1)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); ctx.lineWidth=1.2;
      for(const b of this.p){ b.y-=b.sp*o.speed; b.x+=Math.sin(t*0.001+b.ph)*b.wob*0.5; if(b.y<-b.r){b.y=h+b.r;b.x=Math.random()*w}
        ctx.strokeStyle=rgba(c.accent,0.4); ctx.fillStyle=rgba(c.accent,0.06); ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,6.283);ctx.fill();ctx.stroke();
        ctx.fillStyle=rgba(c.text,0.4); ctx.beginPath();ctx.arc(b.x-b.r*0.3,b.y-b.r*0.3,b.r*0.2,0,6.283);ctx.fill(); } } },
  waves:{ init(ctx,w,h,o){ this.bars=64; this.ph=Array.from({length:this.bars},(_,i)=>i*0.4); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      for(let l=0;l<3;l++){ ctx.beginPath(); ctx.strokeStyle=rgba(l%2?c.accent2:c.accent,0.3-l*0.08); ctx.lineWidth=2;
        for(let x=0;x<=w;x+=8){ const y=h*0.78+Math.sin(x*0.012+t*0.002*o.speed+l*1.3)*(28+l*14); x?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke(); }
      const bw=w/this.bars; for(let i=0;i<this.bars;i++){ const v=(Math.sin(t*0.004*o.speed+this.ph[i])+1)/2; const bh=20+v*120; const x=i*bw;
        const g=ctx.createLinearGradient(0,h,0,h-bh); g.addColorStop(0,rgba(c.accent,0.55)); g.addColorStop(1,rgba(c.accent2,0.05)); ctx.fillStyle=g; ctx.fillRect(x+bw*0.18,h-bh,bw*0.64,bh); } } }
};
function makeEffectController(canvas){
  const ctx=canvas.getContext("2d");
  let inst=Object.create(Effects.snow), opts={count:150,speed:1}, raf=null, running=false, w=0,h=0,dpr=1;
  function resize(){ dpr=Math.min(window.devicePixelRatio||1,2); w=canvas.clientWidth; h=canvas.clientHeight;
    if(w<1||h<1) return; canvas.width=Math.round(w*dpr); canvas.height=Math.round(h*dpr); ctx.setTransform(dpr,0,0,dpr,0,0); if(inst.init) inst.init(ctx,w,h,opts); }
  function loop(ts){ if(!running) return; if(w>0&&h>0) inst.frame(ctx,w,h,ts||0,opts); else resize(); raf=requestAnimationFrame(loop); }
  function start(){ if(running) return; running=true; raf=requestAnimationFrame(loop); }
  function stop(){ running=false; if(raf)cancelAnimationFrame(raf); if(w>0&&h>0)ctx.clearRect(0,0,w,h); }
  function setEffect(name,intensity,speed){ inst=Object.create(Effects[name]?Effects[name]:Effects.none);
    if(intensity!=null) opts.count=Math.max(0,Math.round(intensity)); if(speed!=null) opts.speed=speed; resize(); }
  function setEnabled(on){ on?start():stop(); }
  window.addEventListener("resize",resize);
  document.addEventListener("visibilitychange",()=>{ document.hidden?stop():(running||start()); });
  resize();
  return { setEffect, setEnabled };
}
let fxCtl=null;
function applyEffect(){
  const cv=document.getElementById("fx");
  if(document.body.classList.contains("transparent")){ cv.style.display="none"; if(fxCtl) fxCtl.setEnabled(false); return; }
  cv.style.display="";
  if(!fxCtl) fxCtl=makeEffectController(cv);
  const e=(CFG&&CFG.effect)||{};
  fxCtl.setEffect(e.name||"snow", (e.intensity!=null?e.intensity:150), 1);
  fxCtl.setEnabled(e.enabled!==false);
}

const L={
  tr:{pre:"BAŞLAMASINA", main:"KALAN SÜRE", done:"SÜRE DOLDU — TESLİM ZAMANI!",
      empty:"Başlangıç zamanı ayarlanmadı — JamDeck'in Sayaç sekmesinden kurun."},
  en:{pre:"STARTS IN", main:"TIME REMAINING", done:"TIME'S UP — SUBMIT NOW!",
      empty:"No start time set — configure it in JamDeck's Countdown tab."}
};
const VAR_MAP={bg:"--bg",bg2:"--bg-2",surface:"--surface",surface2:"--surface-2",
               border:"--border",accent:"--accent",accent2:"--accent-2",
               text:"--text",textMuted:"--text-muted",error:"--error"};
const STYLES=["neon","minimal","segment","flip","terminal","pixel","glitch","hpbar"];
const PIX={
  "0":"01110"+"10001"+"10011"+"10101"+"11001"+"10001"+"01110",
  "1":"00100"+"01100"+"00100"+"00100"+"00100"+"00100"+"01110",
  "2":"01110"+"10001"+"00001"+"00010"+"00100"+"01000"+"11111",
  "3":"11111"+"00010"+"00100"+"00010"+"00001"+"10001"+"01110",
  "4":"00010"+"00110"+"01010"+"10010"+"11111"+"00010"+"00010",
  "5":"11111"+"10000"+"11110"+"00001"+"00001"+"10001"+"01110",
  "6":"00110"+"01000"+"10000"+"11110"+"10001"+"10001"+"01110",
  "7":"11111"+"00001"+"00010"+"00100"+"01000"+"01000"+"01000",
  "8":"01110"+"10001"+"10001"+"01110"+"10001"+"10001"+"01110",
  "9":"01110"+"10001"+"10001"+"01111"+"00001"+"00010"+"01100",
  ":":"00000"+"00100"+"00100"+"00000"+"00100"+"00100"+"00000",
  "-":"00000"+"00000"+"00000"+"01110"+"00000"+"00000"+"00000"
};
let CFG=null, lastApplied="";

// metinler tek kaynaktan: state.cdtext (frontend/i18n.json üzerinden enjekte);
// eski sunucu / eksik alan için L (tr/en) yedeği korunur
function strings(){ return (CFG&&CFG.cdtext&&CFG.cdtext.main)?CFG.cdtext:L[lang()]; }
function lang(){ return (CFG&&CFG.jam&&CFG.jam.language)==="en"?"en":"tr"; }

function apply(){
  if(!CFG) return;
  const sig=JSON.stringify([CFG.theme&&CFG.theme.colors, CFG.countdown&&[CFG.countdown.style,
    CFG.countdown.logoLeft,CFG.countdown.logoCenter,CFG.countdown.logoRight], CFG.jam&&CFG.jam.logo,
    CFG.effect&&[CFG.effect.name,CFG.effect.intensity,CFG.effect.enabled]]);
  if(sig===lastApplied) return;
  lastApplied=sig;
  const colors=(CFG.theme&&CFG.theme.colors)||{};
  for(const k in VAR_MAP) if(colors[k]) document.documentElement.style.setProperty(VAR_MAP[k],colors[k]);
  applyEffect();   // launcher'daki arka plan efekti (renkler set edildikten SONRA)
  const cd=CFG.countdown||{};
  const stage=document.getElementById("stage");
  stage.className="cd-stage cd-style-"+(STYLES.includes(cd.style)?cd.style:"neon");
  document.getElementById("digits").dataset.v="";   // stil değişiminde rakamlar yeni stille yeniden çizilsin
  const center=cd.logoCenter||(CFG.jam&&CFG.jam.logo);
  document.getElementById("logos").innerHTML=
    (cd.logoLeft?`<img class="cd-side" src="${cd.logoLeft}" alt="">`:"<span></span>")+
    (center?`<img class="cd-center" src="${center}" alt="">`
           :`<div class="cd-center-ph">GAME JAM<br>LOGO</div>`)+
    (cd.logoRight?`<img class="cd-side r" src="${cd.logoRight}" alt="">`:"<span></span>");
}

function computeState(){
  const cd=(CFG&&CFG.countdown)||{};
  const startMs=cd.startAt?Date.parse(cd.startAt):NaN;
  if(!cd.startAt||isNaN(startMs)) return {phase:"idle",deltaMs:0};
  const endMs=startMs+(parseFloat(cd.durationHours)||48)*3600e3;
  const now=Date.now();
  if(now<startMs) return {phase:"pre", deltaMs:startMs-now};
  if(now<endMs)   return {phase:"main", deltaMs:endMs-now};
  return {phase:"done", deltaMs:0};
}
function fmt(ms,daysSplit){
  let s=Math.max(0,Math.ceil(ms/1000));
  const sec=s%60, min=Math.floor(s/60)%60;
  const parts=(daysSplit&&s>=86400)
    ? [Math.floor(s/86400),Math.floor(s/3600)%24,min,sec]
    : [Math.floor(s/3600),min,sec];
  return parts.map(v=>String(v).padStart(2,"0")).join(":");
}
function digitsHTML(str,style){
  if(style==="pixel")
    return [...str].map(ch=>{
      const bm=PIX[ch]||PIX["-"];
      return `<span class="cd-d cd-px${ch===":"?" sep":""}">${[...bm].map(b=>`<i class="${b==="1"?"on":""}"></i>`).join("")}</span>`;
    }).join("");
  return [...str].map(ch=>ch===":"?`<span class="cd-sep">:</span>`:`<span class="cd-d">${ch}</span>`).join("")
    +`<span class="cd-cursor">&nbsp;</span>`;
}
function setDigits(str){
  const dg=document.getElementById("digits");
  if(dg.dataset.v===str) return;
  const lenChanged=(dg.dataset.v||"").length!==str.length;
  dg.dataset.v=str;
  const style=(CFG&&CFG.countdown&&CFG.countdown.style)||"neon";
  dg.innerHTML=digitsHTML(str,style);
  document.getElementById("ghost").innerHTML=
    [...str].map(ch=>ch===":"?`<span class="cd-sep">:</span>`:`<span class="cd-d">8</span>`).join("");
  if(lenChanged) fitDigits();
}
function fitDigits(){
  const dg=document.getElementById("digits"), gh=document.getElementById("ghost");
  const stage=document.getElementById("stage");
  // sabit 100px tabanda ölç → genişliği DOLDURACAK boyutu oransal hesapla (büyüt VEYA küçült).
  // em-tabanlı hane genişlikleri sayesinde ölçek doğrusal; yükseklik tavanıyla sınırla.
  dg.style.fontSize="100px"; gh.style.fontSize="100px";
  const w=dg.scrollWidth||1;
  const availW=stage.clientWidth*0.94;
  let px=100*availW/w;
  px=Math.min(px, stage.clientHeight*0.46);   // logolar+faz+bar için dikey pay bırak
  px=Math.max(24, px);
  dg.style.fontSize=px+"px"; gh.style.fontSize=px+"px";
}
window.addEventListener("resize",fitDigits);
function updateBar(st){
  const bar=document.getElementById("bar");
  const cd=(CFG&&CFG.countdown)||{};
  let frac = st.phase==="main"
    ? st.deltaMs/(((parseFloat(cd.durationHours)||48))*3600e3)
    : st.phase==="pre" ? 1 : 0;
  frac=Math.max(0,Math.min(1,frac));
  bar.classList.toggle("low", st.phase!=="pre" && frac<=.25);
  bar.querySelector("i").style.width=(frac*100)+"%";
}
function tick(){
  if(!CFG) return;
  const st=computeState(), S=strings();
  const stage=document.getElementById("stage");
  const ph=document.getElementById("phase"), dm=document.getElementById("doneMsg");
  stage.classList.toggle("done", st.phase==="done");
  updateBar(st);
  if(st.phase==="idle"){ ph.textContent=""; dm.hidden=true; setDigits("--:--:--");
    document.getElementById("digits").style.opacity=".25"; return; }
  document.getElementById("digits").style.opacity="";
  if(st.phase==="done"){ ph.textContent=S.main; dm.textContent=S.done; dm.hidden=false;
    setDigits("00:00:00"); return; }
  dm.hidden=true;
  ph.textContent=st.phase==="pre"?S.pre:S.main;
  setDigits(fmt(st.deltaMs, st.phase==="pre"));
}

async function poll(){
  try{
    const r=await fetch("/config.json",{cache:"no-store"});
    CFG=await r.json(); apply();
  }catch(e){ /* launcher kapalı olabilir; eldeki config ile saymaya devam */ }
}
poll();
setInterval(poll,5000);
setInterval(tick,250);
</script>
</body>
</html>
"""


def _make_handler(get_state):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, body, ctype):
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return body

        def do_GET(self):
            try:
                path = self.path.split("?", 1)[0]
                if path == "/config.json":
                    body = json.dumps(get_state()).encode("utf-8")
                    self.wfile.write(self._send(body, "application/json; charset=utf-8"))
                elif path in ("/", "/index.html"):
                    self.wfile.write(self._send(PAGE.encode("utf-8"), "text/html; charset=utf-8"))
                else:
                    self.send_error(404)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_HEAD(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html", "/config.json"):
                self._send(b"", "text/html; charset=utf-8")
            else:
                self.send_error(404)

    return Handler


def start_countdown_server(get_state, port=DEFAULT_PORT):
    """Serve the countdown page on 0.0.0.0:<port> (free port if busy).

    `get_state` is called per /config.json request and must return the
    JSON-serializable dict {countdown, jam, theme}. Returns (httpd, port);
    stop with httpd.shutdown().
    """
    try:
        httpd = _ThreadingHTTPServer(("0.0.0.0", port), _make_handler(get_state))
    except OSError:
        httpd = _ThreadingHTTPServer(("0.0.0.0", 0), _make_handler(get_state))
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, port
