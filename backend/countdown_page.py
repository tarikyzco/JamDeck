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
  --bg:#050a14; --surface:#0f1629; --border:#1e293b;
  --accent:#00f2ff; --text:#ffffff; --text-muted:#94a3b8; --error:#ff1744;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%}
body{background:var(--bg); color:var(--text); overflow:hidden;
  font-family:"Segoe UI",system-ui,sans-serif}
body.transparent{background:transparent}
.cd-stage{position:relative; height:100vh; display:flex; flex-direction:column;
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

const L={
  tr:{pre:"BAŞLAMASINA", main:"KALAN SÜRE", done:"SÜRE DOLDU — TESLİM ZAMANI!",
      empty:"Başlangıç zamanı ayarlanmadı — JamDeck'in Sayaç sekmesinden kurun."},
  en:{pre:"STARTS IN", main:"TIME REMAINING", done:"TIME'S UP — SUBMIT NOW!",
      empty:"No start time set — configure it in JamDeck's Countdown tab."}
};
const VAR_MAP={bg:"--bg",surface:"--surface",border:"--border",accent:"--accent",
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

function lang(){ return (CFG&&CFG.jam&&CFG.jam.language)==="en"?"en":"tr"; }

function apply(){
  if(!CFG) return;
  const sig=JSON.stringify([CFG.theme&&CFG.theme.colors, CFG.countdown&&[CFG.countdown.style,
    CFG.countdown.logoLeft,CFG.countdown.logoCenter,CFG.countdown.logoRight], CFG.jam&&CFG.jam.logo]);
  if(sig===lastApplied) return;
  lastApplied=sig;
  const colors=(CFG.theme&&CFG.theme.colors)||{};
  for(const k in VAR_MAP) if(colors[k]) document.documentElement.style.setProperty(VAR_MAP[k],colors[k]);
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
  dg.style.fontSize=""; gh.style.fontSize="";
  const avail=stage.clientWidth*0.92;
  const w=dg.scrollWidth;
  if(w>avail){
    const px=Math.max(24, Math.floor(parseFloat(getComputedStyle(dg).fontSize)*avail/w));
    dg.style.fontSize=px+"px"; gh.style.fontSize=px+"px";
  }
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
  const st=computeState(), S=L[lang()];
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
