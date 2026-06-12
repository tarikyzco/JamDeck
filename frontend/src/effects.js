/* ============================================================
   JamDeck — BACKGROUND EFFECTS  (14 effects)
   Each effect: { init(ctx,w,h,o), frame(ctx,w,h,t,o) }
   Controller reads theme colors live, handles resize/rAF/intensity/on-off,
   pauses when hidden, respects prefers-reduced-motion.
   ============================================================ */

/* read current theme colors from CSS vars -> {accent, accent2, text, bg, ...} as hex */
function themeColors(){
  const cs = getComputedStyle(document.documentElement);
  const g = v => cs.getPropertyValue(v).trim() || "#ffffff";
  return { accent:g("--accent"), accent2:g("--accent-2"), text:g("--text"),
           bg:g("--bg"), bg2:g("--bg-2"), surface:g("--surface") };
}
function hexToRgb(hex){
  hex = (hex||"#000").replace("#","");
  if(hex.length===3) hex = hex.split("").map(c=>c+c).join("");
  const n = parseInt(hex.slice(0,6),16);
  return { r:(n>>16)&255, g:(n>>8)&255, b:n&255 };
}
function rgba(hex,a){ const c=hexToRgb(hex); return `rgba(${c.r},${c.g},${c.b},${a})`; }
function lerpColor(h1,h2,t){ const a=hexToRgb(h1),b=hexToRgb(h2);
  return `rgb(${Math.round(a.r+(b.r-a.r)*t)},${Math.round(a.g+(b.g-a.g)*t)},${Math.round(a.b+(b.b-a.b)*t)})`; }
const rnd=(a,b)=>a+Math.random()*(b-a);

const Effects = {
  none:{
    init(){}, frame(ctx,w,h){ /* veil handles gradient; just clear */ ctx.clearRect(0,0,w,h); }
  },

  /* 2. SNOW */
  snow:{
    init(ctx,w,h,o){ const n=o.count; this.p=Array.from({length:n},()=>({
      x:Math.random()*w,y:Math.random()*h,r:rnd(1,3.4),sp:rnd(.3,1.1),dr:rnd(-.4,.4),ph:rnd(0,6.28)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      for(const f of this.p){ f.y+=f.sp*o.speed; f.x+=Math.sin(t*0.001+f.ph)*0.3+f.dr;
        if(f.y>h+5){f.y=-5;f.x=Math.random()*w} if(f.x>w+5)f.x=-5; if(f.x<-5)f.x=w+5;
        ctx.beginPath();ctx.arc(f.x,f.y,f.r,0,6.283);ctx.fillStyle=rgba(c.text,0.55*(f.r/3.4));ctx.fill(); } }
  },

  /* 3. RAIN */
  rain:{
    init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>({
      x:Math.random()*w,y:Math.random()*h,len:rnd(10,26),sp:rnd(7,15)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); ctx.lineWidth=1.1;
      for(const d of this.p){ d.y+=d.sp*o.speed; d.x+=d.sp*0.32*o.speed;
        if(d.y>h){d.y=-d.len;d.x=Math.random()*w}
        ctx.strokeStyle=rgba(c.accent,0.22); ctx.beginPath();
        ctx.moveTo(d.x,d.y); ctx.lineTo(d.x-d.len*0.32,d.y-d.len); ctx.stroke(); } }
  },

  /* 4. STARFIELD / WARP */
  starfield:{
    init(ctx,w,h,o){ this.cx=w/2;this.cy=h/2; this.s=Array.from({length:o.count},()=>({
      x:rnd(-w,w),y:rnd(-h,h),z:rnd(1,w)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); const cx=w/2,cy=h/2;
      for(const s of this.s){ s.z-=2.2*o.speed; if(s.z<1){s.x=rnd(-w,w);s.y=rnd(-h,h);s.z=w}
        const k=128/s.z, x=cx+s.x*k, y=cy+s.y*k, px=cx+s.x*(128/(s.z+2.2*o.speed)), py=cy+s.y*(128/(s.z+2.2*o.speed));
        const a=Math.min(1,(w-s.z)/w); ctx.strokeStyle=rgba(c.accent,a*0.8); ctx.lineWidth=Math.max(.5,(1-s.z/w)*2.4);
        ctx.beginPath();ctx.moveTo(px,py);ctx.lineTo(x,y);ctx.stroke(); } }
  },

  /* 5. PARTICLE NETWORK (PLEXUS) */
  plexus:{
    init(ctx,w,h,o){ const n=Math.min(o.count,140); this.p=Array.from({length:n},()=>({
      x:Math.random()*w,y:Math.random()*h,vx:rnd(-.4,.4),vy:rnd(-.4,.4)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); const d2=150*150;
      for(const p of this.p){ p.x+=p.vx*o.speed;p.y+=p.vy*o.speed;
        if(p.x<0||p.x>w)p.vx*=-1; if(p.y<0||p.y>h)p.vy*=-1; }
      for(let i=0;i<this.p.length;i++){ const a=this.p[i];
        for(let j=i+1;j<this.p.length;j++){ const b=this.p[j]; const dx=a.x-b.x,dy=a.y-b.y,dd=dx*dx+dy*dy;
          if(dd<d2){ ctx.strokeStyle=rgba(c.accent,(1-dd/d2)*0.3); ctx.lineWidth=.7;
            ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke(); } }
        ctx.beginPath();ctx.arc(a.x,a.y,2,0,6.283);ctx.fillStyle=rgba(c.accent,0.8);ctx.fill(); } }
  },

  /* 6. FLOATING ORBS / BOKEH */
  orbs:{
    init(ctx,w,h,o){ const n=Math.max(6,Math.round(o.count/14)); this.o=Array.from({length:n},()=>({
      x:Math.random()*w,y:Math.random()*h,r:rnd(40,150),vx:rnd(-.3,.3),vy:rnd(-.3,.3),a:rnd(.05,.18),c:Math.random()<.5})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      for(const b of this.o){ b.x+=b.vx*o.speed;b.y+=b.vy*o.speed;
        if(b.x<-b.r)b.x=w+b.r; if(b.x>w+b.r)b.x=-b.r; if(b.y<-b.r)b.y=h+b.r; if(b.y>h+b.r)b.y=-b.r;
        const col=b.c?c.accent:c.accent2; const g=ctx.createRadialGradient(b.x,b.y,0,b.x,b.y,b.r);
        g.addColorStop(0,rgba(col,b.a)); g.addColorStop(1,rgba(col,0));
        ctx.fillStyle=g;ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,6.283);ctx.fill(); } }
  },

  /* 7. MATRIX RAIN */
  matrix:{
    init(ctx,w,h,o){ this.fs=16; this.cols=Math.floor(w/this.fs);
      this.y=Array.from({length:this.cols},()=>rnd(-50,0)); this.glyph="ｦｱｳｴｵｶｷｸｹｺ01<>[]{}#$%&"; },
    frame(ctx,w,h,t,o){ const c=themeColors(); ctx.fillStyle=rgba(c.bg,0.12); ctx.fillRect(0,0,w,h);
      ctx.font=this.fs+"px var(--font-mono),monospace";
      for(let i=0;i<this.cols;i++){ const ch=this.glyph[Math.floor(Math.random()*this.glyph.length)];
        const x=i*this.fs,y=this.y[i]*this.fs;
        ctx.fillStyle=rgba(c.text,0.9); ctx.fillText(ch,x,y);
        ctx.fillStyle=rgba(c.accent,0.85); ctx.fillText(ch,x,y-this.fs);
        if(y>h&&Math.random()>0.975)this.y[i]=0; this.y[i]+=0.45*o.speed; } }
  },

  /* 8. AURORA */
  aurora:{
    init(ctx,w,h,o){ this.blobs=Array.from({length:4},(_,i)=>({ph:rnd(0,6.28),sp:rnd(.0002,.0006),r:rnd(.4,.7),i})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      const cols=[c.accent,c.accent2,c.accent,c.accent2];
      for(const b of this.blobs){ const x=w*(0.5+0.4*Math.sin(t*b.sp*o.speed+b.ph));
        const y=h*(0.4+0.35*Math.cos(t*b.sp*1.4*o.speed+b.ph)); const rr=Math.min(w,h)*b.r;
        const g=ctx.createRadialGradient(x,y,0,x,y,rr); g.addColorStop(0,rgba(cols[b.i],0.22)); g.addColorStop(1,rgba(cols[b.i],0));
        ctx.fillStyle=g; ctx.beginPath();ctx.arc(x,y,rr,0,6.283);ctx.fill(); } }
  },

  /* 9. CONFETTI */
  confetti:{
    init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>this.spawn(w,h,true)); },
    spawn(w,h,init){ return {x:Math.random()*w,y:init?Math.random()*h:-10,
      vx:rnd(-1,1),vy:rnd(2,5),s:rnd(5,11),rot:rnd(0,6.28),vr:rnd(-.2,.2),k:Math.random()}; },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); const pal=[c.accent,c.accent2,c.text];
      for(let i=0;i<this.p.length;i++){ const q=this.p[i]; q.x+=q.vx*o.speed;q.y+=q.vy*o.speed;q.rot+=q.vr*o.speed;
        if(q.y>h+12)this.p[i]=this.spawn(w,h,false);
        ctx.save();ctx.translate(q.x,q.y);ctx.rotate(q.rot);
        ctx.fillStyle=pal[Math.floor(q.k*pal.length)]; ctx.globalAlpha=.85;
        ctx.fillRect(-q.s/2,-q.s/2,q.s,q.s*0.6); ctx.restore();ctx.globalAlpha=1; } }
  },

  /* 10. FIREFLIES / EMBERS */
  fireflies:{
    init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>({
      x:Math.random()*w,y:Math.random()*h,vx:rnd(-.3,.3),vy:rnd(-.6,-.1),ph:rnd(0,6.28),r:rnd(1,2.6)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      for(const f of this.p){ f.x+=f.vx*o.speed+Math.sin(t*0.001+f.ph)*0.2; f.y+=f.vy*o.speed;
        if(f.y<-5){f.y=h+5;f.x=Math.random()*w}
        const a=0.4+0.5*Math.sin(t*0.003+f.ph); const g=ctx.createRadialGradient(f.x,f.y,0,f.x,f.y,f.r*4);
        g.addColorStop(0,rgba(c.accent,a)); g.addColorStop(1,rgba(c.accent,0));
        ctx.fillStyle=g;ctx.beginPath();ctx.arc(f.x,f.y,f.r*4,0,6.283);ctx.fill();
        ctx.fillStyle=rgba(c.text,a);ctx.beginPath();ctx.arc(f.x,f.y,f.r,0,6.283);ctx.fill(); } }
  },

  /* 11. ANIMATED GRADIENT */
  gradient:{
    init(){}, frame(ctx,w,h,t,o){ const c=themeColors(); const a=(Math.sin(t*0.0003*o.speed)+1)/2;
      const x1=w*a,y1=h*(1-a),x2=w*(1-a),y2=h*a;
      const g=ctx.createLinearGradient(x1,y1,x2,y2);
      g.addColorStop(0,rgba(c.accent,0.5)); g.addColorStop(.5,rgba(c.bg,0.2)); g.addColorStop(1,rgba(c.accent2,0.5));
      ctx.clearRect(0,0,w,h); ctx.fillStyle=g; ctx.fillRect(0,0,w,h); }
  },

  /* 12. LOW-POLY / GEOMETRIC */
  lowpoly:{
    init(ctx,w,h,o){ const n=Math.max(6,Math.round(o.count/12)); this.tr=Array.from({length:n},()=>({
      x:Math.random()*w,y:Math.random()*h,r:rnd(30,90),rot:rnd(0,6.28),vr:rnd(-.005,.005),
      vx:rnd(-.25,.25),vy:rnd(-.25,.25),sides:Math.random()<.5?3:4})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); ctx.lineWidth=1.2;
      for(const p of this.tr){ p.x+=p.vx*o.speed;p.y+=p.vy*o.speed;p.rot+=p.vr*o.speed;
        if(p.x<-p.r)p.x=w+p.r; if(p.x>w+p.r)p.x=-p.r; if(p.y<-p.r)p.y=h+p.r; if(p.y>h+p.r)p.y=-p.r;
        ctx.strokeStyle=rgba(c.accent,0.28); ctx.beginPath();
        for(let i=0;i<=p.sides;i++){ const a=p.rot+i/p.sides*6.283; const x=p.x+Math.cos(a)*p.r,y=p.y+Math.sin(a)*p.r;
          i?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke(); } }
  },

  /* 13. BUBBLES */
  bubbles:{
    init(ctx,w,h,o){ this.p=Array.from({length:o.count},()=>({
      x:Math.random()*w,y:Math.random()*h,r:rnd(4,16),sp:rnd(.5,1.6),ph:rnd(0,6.28),wob:rnd(.4,1.1)})); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors(); ctx.lineWidth=1.2;
      for(const b of this.p){ b.y-=b.sp*o.speed; b.x+=Math.sin(t*0.001+b.ph)*b.wob*0.5;
        if(b.y<-b.r){b.y=h+b.r;b.x=Math.random()*w}
        ctx.strokeStyle=rgba(c.accent,0.4); ctx.fillStyle=rgba(c.accent,0.06);
        ctx.beginPath();ctx.arc(b.x,b.y,b.r,0,6.283);ctx.fill();ctx.stroke();
        ctx.fillStyle=rgba(c.text,0.4); ctx.beginPath();ctx.arc(b.x-b.r*0.3,b.y-b.r*0.3,b.r*0.2,0,6.283);ctx.fill(); } }
  },

  /* 14. WAVES / EQUALIZER */
  waves:{
    init(ctx,w,h,o){ this.bars=64; this.ph=Array.from({length:this.bars},(_,i)=>i*0.4); },
    frame(ctx,w,h,t,o){ ctx.clearRect(0,0,w,h); const c=themeColors();
      // sine waves
      for(let l=0;l<3;l++){ ctx.beginPath(); ctx.strokeStyle=rgba(l%2?c.accent2:c.accent,0.3-l*0.08); ctx.lineWidth=2;
        for(let x=0;x<=w;x+=8){ const y=h*0.78+Math.sin(x*0.012+t*0.002*o.speed+l*1.3)*(28+l*14);
          x?ctx.lineTo(x,y):ctx.moveTo(x,y); } ctx.stroke(); }
      // equalizer bars along bottom
      const bw=w/this.bars;
      for(let i=0;i<this.bars;i++){ const v=(Math.sin(t*0.004*o.speed+this.ph[i])+1)/2;
        const bh=20+v*120; const x=i*bw;
        const g=ctx.createLinearGradient(0,h,0,h-bh); g.addColorStop(0,rgba(c.accent,0.55)); g.addColorStop(1,rgba(c.accent2,0.05));
        ctx.fillStyle=g; ctx.fillRect(x+bw*0.18,h-bh,bw*0.64,bh); } }
  }
};

const EFFECT_KEYS = ["none","snow","rain","starfield","plexus","orbs","matrix","aurora","confetti","fireflies","gradient","lowpoly","bubbles","waves"];
const EFFECT_LABELS = {
  none:{tr:"Yok",en:"None"}, snow:{tr:"Kar",en:"Snow"}, rain:{tr:"Yağmur",en:"Rain"},
  starfield:{tr:"Yıldız Alanı",en:"Starfield"}, plexus:{tr:"Parçacık Ağı",en:"Plexus"},
  orbs:{tr:"Küreler",en:"Orbs"}, matrix:{tr:"Matrix",en:"Matrix"}, aurora:{tr:"Aurora",en:"Aurora"},
  confetti:{tr:"Konfeti",en:"Confetti"}, fireflies:{tr:"Ateş Böcekleri",en:"Fireflies"},
  gradient:{tr:"Gradyan",en:"Gradient"}, lowpoly:{tr:"Geometrik",en:"Low-Poly"},
  bubbles:{tr:"Baloncuklar",en:"Bubbles"}, waves:{tr:"Dalgalar",en:"Waves"}
};

/* ---------- CONTROLLER ----------
   Each controller owns a PRIVATE effect instance via Object.create, so every
   canvas (background + live preview + 14 gallery thumbnails) keeps its OWN
   particle state. Without this, all controllers would share Effects[name].p
   and the last/smallest init would shrink everyone's particle field. */
function makeEffectController(canvas){
  const ctx = canvas.getContext("2d");
  let cur="snow", inst=Object.create(Effects.snow), opts={count:150,speed:1}, raf=null, running=false, w=0,h=0, dpr=1;

  function resize(){
    dpr = Math.min(window.devicePixelRatio||1, 2);
    w = canvas.clientWidth; h = canvas.clientHeight;
    if(w<1||h<1) return;            // skip until laid out — avoids clustered init
    canvas.width = Math.round(w*dpr); canvas.height = Math.round(h*dpr);
    ctx.setTransform(dpr,0,0,dpr,0,0);
    if(inst.init) inst.init(ctx,w,h,opts);
  }
  function loop(ts){ if(!running) return;
    if(w>0&&h>0) inst.frame(ctx,w,h,ts||0,opts);
    else resize();
    raf = requestAnimationFrame(loop);
  }
  function start(){ if(running) return; running=true; raf=requestAnimationFrame(loop); }
  function stop(){ running=false; if(raf)cancelAnimationFrame(raf); if(w>0&&h>0)ctx.clearRect(0,0,w,h); }

  function setEffect(name, intensity, speed){
    cur = Effects[name]?name:"none";
    inst = Object.create(Effects[cur]);   // fresh private instance for this controller
    if(intensity!=null) opts.count = Math.max(0, Math.round(intensity));
    if(speed!=null) opts.speed = speed;
    resize();
  }
  function setIntensity(v){ opts.count=Math.max(0,Math.round(v)); if(inst.init)resize(); }
  function setSpeed(v){ opts.speed=v; }
  function setEnabled(on){ on?start():stop(); }

  window.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", ()=>{ document.hidden?stop():start(); });

  resize();
  return { setEffect, setIntensity, setSpeed, setEnabled, start, stop, resize,
    get current(){return cur} };
}
