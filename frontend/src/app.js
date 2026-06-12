/* ============================================================
   JamDeck — APP / ROUTER / SCREENS
   ============================================================ */
const Bridge = makeBridge();
let CONFIG = null;
let GAMES = [];
let selectedGameId = null;
let effectCtl = null;
let dlState = "idle";   // idle|running|done|error
let dlData = {current:0,total:24,name:"",speed:""};

/* ---------- tiny DOM helpers ---------- */
const $ = (s,r=document)=>r.querySelector(s);
const $$ = (s,r=document)=>[...r.querySelectorAll(s)];
function el(html){ const t=document.createElement("template"); t.innerHTML=html.trim(); return t.content.firstElementChild; }
function fmtTime(sec){ sec=Math.max(0,sec); const m=Math.floor(sec/60),s=sec%60; return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}`; }

/* ---------- TOASTS ---------- */
function toast(msg,type="success"){
  let wrap=$(".toast-wrap"); if(!wrap){ wrap=el(`<div class="toast-wrap"></div>`); document.body.appendChild(wrap); }
  const ic = type==="error"?"alert":type==="info"?"sparkles":"check";
  const t=el(`<div class="toast ${type}"><div class="toast-ic">${icon(ic)}</div><span>${msg}</span></div>`);
  wrap.appendChild(t);
  setTimeout(()=>{ t.classList.add("out"); setTimeout(()=>t.remove(),260); },2600);
}

/* ---------- MODAL ---------- */
function modal({title,body,confirmLabel,cancelLabel,danger,onConfirm}){
  const bd=el(`<div class="modal-backdrop"><div class="modal">
    <h3>${title}</h3><p>${body}</p>
    <div class="modal-actions">
      <button class="btn btn-ghost" data-cancel>${cancelLabel||t("cancel")}</button>
      <button class="btn ${danger?"btn-danger":"btn-primary"}" data-ok>${confirmLabel||t("confirm")}</button>
    </div></div></div>`);
  document.body.appendChild(bd);
  requestAnimationFrame(()=>bd.classList.add("show"));
  const close=()=>{ bd.classList.remove("show"); setTimeout(()=>bd.remove(),240); };
  bd.querySelector("[data-cancel]").onclick=close;
  bd.querySelector("[data-ok]").onclick=()=>{ close(); onConfirm&&onConfirm(); };
  bd.onclick=e=>{ if(e.target===bd) close(); };
}

/* ============================================================
   SIDEBAR
   ============================================================ */
const NAV = [
  {id:"download", icon:"download", key:"nav_download"},
  {id:"organize", icon:"organize", key:"nav_organize"},
  {id:"launcher", icon:"play", key:"nav_launch"}
];
function renderSidebar(){
  const logo = CONFIG.jam.logo;
  const initial = (CONFIG.jam.name||"J").trim()[0]||"J";
  return `<aside class="sidebar" id="sidebar">
    <div class="brand">
      <div class="brand-logo">${logo?`<img src="${logo}" alt="">`:initial.toUpperCase()}</div>
      <div class="brand-text">
        <span class="brand-name" data-t-text="jamname">${CONFIG.jam.name}</span>
        <span class="brand-sub" data-t="brand_sub">${t("brand_sub")}</span>
      </div>
    </div>
    <nav class="nav">
      <div class="nav-label" data-t="nav_section">${t("nav_section")}</div>
      ${NAV.map(n=>`<button class="nav-item" data-nav="${n.id}">${icon(n.icon)}<span data-t="${n.key}">${t(n.key)}</span></button>`).join("")}
    </nav>
    <div class="side-foot">
      <div class="side-row">
        <button class="lang-pill" id="langPill"><span class="flag">${LANG.toUpperCase()}</span><span class="lang-label" data-t="language">${t("language")}</span></button>
        <button class="gear-btn" data-nav="setup" title="${t("settings")}">${icon("settings")}</button>
      </div>
      <span class="side-foot-text">JamDeck · v2.0.0</span>
    </div>
  </aside>
  <button class="collapse-btn" id="collapseBtn">${icon("chevron")}</button>`;
}

/* ============================================================
   SCREEN: DOWNLOAD & VERIFY
   ============================================================ */
function screenDownload(){
  return `<section class="screen" id="screen-download" data-screen-label="Download">
    <div class="screen-inner">
      <div class="page-head">
        <h1 class="page-title" data-t="dl_title">${t("dl_title")}</h1>
        <p class="page-sub" data-t="dl_sub">${t("dl_sub")}</p>
        <span class="page-meta">${icon("folder")} <span data-t="target_folder">${t("target_folder")}</span>: <b>${CONFIG.paths.gamesDir}</b></span>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start">
        <div class="card featured">
          <div class="card-title">${icon("download")}<span data-t="jam_url">${t("jam_url")}</span></div>
          <div class="field" style="margin-top:14px">
            <label class="field-label" data-t="jam_url">${t("jam_url")}</label>
            <input class="input" id="dlUrl" placeholder="https://itch.io/jam/your-jam" value="https://itch.io/jam/ayazjam-2025">
          </div>
          <div class="field">
            <label class="field-label" data-t="api_key">${t("api_key")}</label>
            <div class="input-wrap">
              <input class="input" id="dlKey" type="password" placeholder="••••••••••••" value="itch_sk_8f2a91">
              <button class="input-icon-btn" id="dlKeyEye">${icon("eye")}</button>
            </div>
          </div>
          <div style="display:flex;gap:10px;margin-top:6px;flex-wrap:wrap">
            <button class="btn btn-primary" id="dlStart">${icon("download")}<span class="btn-spinner"></span><span class="btn-txt" data-t="start_download">${t("start_download")}</span></button>
            <button class="btn btn-secondary" id="dlVerify">${icon("shield")}<span class="btn-txt" data-t="integrity_check">${t("integrity_check")}</span></button>
          </div>
        </div>
        <div class="card" id="dlProgressCard">
          <div style="display:flex;align-items:flex-end;justify-content:space-between;gap:14px;margin-bottom:8px">
            <div class="stat-big" style="white-space:nowrap"><span id="dlCur">0</span><small> / <span id="dlTot">24</span></small></div>
            <div style="text-align:right;flex-shrink:0">
              <div style="font-size:11px;color:var(--text-muted);text-transform:uppercase;letter-spacing:.1em" data-t="speed">${t("speed")}</div>
              <div style="font-family:var(--font-mono);font-size:16px;color:var(--accent);white-space:nowrap" id="dlSpeed">—</div>
            </div>
          </div>
          <div class="progress" id="dlBar"><div class="progress-fill" id="dlFill"></div></div>
          <div style="margin-top:12px;font-size:13px;color:var(--text-muted);min-height:20px">
            <span data-t="now_downloading">${t("now_downloading")}</span>: <span id="dlName" style="color:var(--text)">—</span>
          </div>
        </div>
      </div>
      <div class="card" style="margin-top:20px;padding:16px">
        <div class="console" id="dlConsole"></div>
      </div>
    </div>
  </section>`;
}

/* ============================================================
   SCREEN: ORGANIZE & CLEAN
   ============================================================ */
function screenOrganize(){
  return `<section class="screen" id="screen-organize" data-screen-label="Organize">
    <div class="screen-inner">
      <div class="page-head">
        <h1 class="page-title" data-t="org_title">${t("org_title")}</h1>
        <p class="page-sub" data-t="org_sub">${t("org_sub")}</p>
      </div>
      <div class="card featured" style="display:flex;align-items:center;justify-content:space-between;gap:20px;flex-wrap:wrap">
        <div style="display:flex;align-items:center;gap:16px">
          <div style="width:54px;height:54px;border-radius:var(--radius-sm);display:grid;place-items:center;background:var(--accent-soft);color:var(--accent)">${icon("organize")}</div>
          <div>
            <div style="font-size:16px;font-weight:700" data-t="org_title">${t("org_title")}</div>
            <div style="font-size:13px;color:var(--text-muted)">.zip · .rar → unpack · flatten · clean</div>
          </div>
        </div>
        <button class="btn btn-primary btn-lg" id="orgRun">${icon("sparkles")}<span class="btn-spinner"></span><span class="btn-txt" data-t="auto_organize">${t("auto_organize")}</span></button>
      </div>
      <div id="orgChips" style="display:flex;gap:10px;margin-top:16px;flex-wrap:wrap"></div>
      <div class="card" style="margin-top:16px;padding:16px">
        <div class="console" id="orgConsole" style="height:360px"></div>
      </div>
    </div>
  </section>`;
}

/* ============================================================
   SCREEN: LAUNCHER (kiosk)
   ============================================================ */
function screenLauncher(){
  return `<section class="screen" id="screen-launcher" data-screen-label="Launcher">
    <div class="launcher-wrap" id="launcherWrap">
      <div class="launcher-list">
        <div class="ll-head">
          <div class="ll-title"><span data-t="games">${t("games")}</span> <span class="ll-count" id="llCount">(0)</span></div>
          <button class="gear-btn" id="llRefresh" title="${t("refresh")}">${icon("refresh")}</button>
        </div>
        <div class="ll-search">
          <span class="ll-search-ic">${icon("search")}</span>
          <input class="input" id="llSearch" placeholder="${t("search_games")}">
        </div>
        <div class="ll-rows" id="llRows"></div>
        <div class="ll-foot">
          <label class="field-label" data-t="time_limit">${t("time_limit")}</label>
          <input class="input" id="llMinutes" type="number" min="1" max="60" value="${CONFIG.launcher.defaultMinutes}" style="width:84px;text-align:center;font-family:var(--font-mono)">
        </div>
      </div>
      <div class="launcher-hero" id="launcherHero"></div>
      <button class="kiosk-exit" id="kioskExit" title="${t("exit_kiosk")}">${icon("x")}</button>
    </div>
  </section>`;
}

function renderHero(){
  const g = GAMES.find(x=>x.id===selectedGameId);
  const hero = $("#launcherHero"); if(!hero) return;
  if(!g){ hero.innerHTML=`<div class="empty-state">${icon("gamepad")}<div class="es-title">${t("no_games_title")}</div><div>${t("no_games_sub")}</div></div>`; return; }
  const cover = g.cover || placeholderCover(g);
  const multi = g.exes.length>1;
  hero.innerHTML = `
    <div class="hero-card" data-anim>
      <div class="hero-art" style="background-image:url('${cover}')">
        <div class="hero-art-glow"></div>
      </div>
      <div class="hero-info">
        <div class="hero-team">${g.team}</div>
        <h2 class="hero-name">${g.game}</h2>
        <div class="hero-meta">
          <span class="chip">${icon(ENGINE_ICON[g.engine]||"cpu")} ${g.engine}</span>
          <span class="chip">${icon("cpu")} ${g.exes[g.currentExe].split("/").pop()}</span>
          ${multi?`<span class="chip">${g.currentExe+1}/${g.exes.length}</span>`:""}
        </div>
        <div class="hero-actions">
          <button class="btn btn-primary btn-lg" id="heroPlay">${icon("play")}<span data-t="play">${t("play")}</span></button>
          ${multi?`<button class="btn btn-secondary btn-lg" id="heroSwitch">${icon("cpu")}<span data-t="switch_exe">${t("switch_exe")}</span> (${g.currentExe+1}/${g.exes.length})</button>`:""}
        </div>
      </div>
    </div>`;
  // wire
  const play=$("#heroPlay"); if(play) play.onclick=()=>startGame(g);
  const sw=$("#heroSwitch"); if(sw) sw.onclick=()=>{ g.currentExe=(g.currentExe+1)%g.exes.length; renderHero(); };
}

function placeholderCover(g){
  const svg=`<svg xmlns='http://www.w3.org/2000/svg' width='600' height='800'>
    <rect width='600' height='800' fill='%23141d33'/>
    <rect width='600' height='800' fill='none'/>
    <pattern id='p' width='28' height='28' patternUnits='userSpaceOnUse' patternTransform='rotate(45)'>
      <rect width='14' height='28' fill='rgba(255,255,255,0.03)'/></pattern>
    <rect width='600' height='800' fill='url(%23p)'/>
    <text x='300' y='400' font-family='monospace' font-size='28' fill='rgba(255,255,255,0.35)' text-anchor='middle'>no cover</text>
  </svg>`;
  return "data:image/svg+xml;utf8,"+encodeURIComponent(svg).replace(/'/g,"%27");
}

function renderGameRows(filter=""){
  const rows=$("#llRows"); if(!rows) return;
  const f=filter.toLowerCase();
  const list=GAMES.filter(g=>!f || g.game.toLowerCase().includes(f) || g.team.toLowerCase().includes(f));
  $("#llCount").textContent=`(${list.length})`;
  if(!list.length){ rows.innerHTML=`<div class="empty-state" style="padding:30px">${icon("search")}<div>—</div></div>`; return; }
  rows.innerHTML=list.map(g=>{
    const init=g.game[0]||"?";
    const thumb=g.cover?`style="background-image:url('${g.cover}')"`:"";
    return `<button class="game-row ${g.id===selectedGameId?"sel":""}" data-game="${g.id}">
      <span class="gr-thumb" ${thumb}>${g.cover?"":init}</span>
      <span class="gr-text"><span class="gr-team">${g.team}</span><span class="gr-name">${g.game}</span></span>
    </button>`;
  }).join("");
  $$(".game-row",rows).forEach(b=>b.onclick=()=>{ selectedGameId=b.dataset.game; renderGameRows(filter); renderHero(); });
}

function startGame(g){
  const mins=parseInt($("#llMinutes").value)||CONFIG.launcher.defaultMinutes;
  openTimerOverlay();
  Bridge.launchGame(g.id,g.currentExe,mins);
}

/* ============================================================
   SCREEN: SETUP  (split: controls | live preview)  -> separate file
   ============================================================ */
/* renderSetup() defined in setup.js (loaded after) */

/* ============================================================
   TIMER OVERLAY + TIME'S UP  (self-contained)
   ============================================================ */
let timerUnsub=[];
function openTimerOverlay(){
  if(!CONFIG.launcher.timerOverlay) return;
  closeTimerOverlay();
  const pill=el(`<div class="timer-pill" id="timerPill"><span class="tp-dot"></span><span id="tpTime">--:--</span></div>`);
  document.body.appendChild(pill);
}
function closeTimerOverlay(){
  $("#timerPill")?.remove(); $("#timesup")?.remove();
}
function showTimesUp(){
  const msg=t("times_up");
  const ov=el(`<div class="timesup" id="timesup">
    <div class="tu-inner">
      <div class="tu-flash"></div>
      <h1 class="tu-text">${msg}</h1>
      <div class="tu-sub"><span id="tuCountdown">${CONFIG.launcher.killDelay}</span>s · <span data-t="closing_in">${t("closing_in")}</span></div>
    </div></div>`);
  document.body.appendChild(ov);
  let n=CONFIG.launcher.killDelay;
  const iv=setInterval(()=>{ n--; const c=$("#tuCountdown"); if(c)c.textContent=Math.max(0,n);
    if(n<=0){ clearInterval(iv); Bridge.stopGame(); } },1000);
  // confetti burst behind, themed
  if(effectCtl){ /* keep current effect; flash handles drama */ }
}

function wireTimerEvents(){
  Bridge.on("timer:tick",({remaining})=>{
    const tp=$("#tpTime"); if(tp){ tp.textContent=fmtTime(remaining);
      const pill=$("#timerPill"); pill.classList.toggle("warn",remaining<60&&remaining>=15);
      pill.classList.toggle("danger",remaining<15); }
  });
  Bridge.on("timer:timesup",()=>showTimesUp());
  Bridge.on("game:closed",()=>{ closeTimerOverlay(); });
}

/* ============================================================
   ROUTER
   ============================================================ */
let currentScreen="launcher";
function navigate(id){
  currentScreen=id;
  $$(".screen").forEach(s=>s.classList.remove("active"));
  $("#screen-"+id)?.classList.add("active");
  $$(".nav-item").forEach(n=>n.classList.toggle("active",n.dataset.nav===id));
  // kiosk takes over: hide sidebar
  const kiosk = id==="launcher";
  $("#sidebar")?.classList.toggle("kiosk-hidden",kiosk);
  $("#collapseBtn")?.classList.toggle("kiosk-hidden",kiosk);
  document.body.classList.toggle("kiosk-mode",kiosk);
  if(id==="launcher"){ ensureGamesLoaded(); }
  if(id==="setup" && window.mountSetup) window.mountSetup();
}

let gamesLoaded=false;
async function ensureGamesLoaded(){
  if(gamesLoaded) return;
  GAMES = await Bridge.scanGames();
  gamesLoaded=true;
  if(GAMES.length) selectedGameId=GAMES[0].id;
  renderGameRows(); renderHero();
}

/* ============================================================
   CONSOLE LOG RENDERING
   ============================================================ */
function appendLog(container,{level,line}){
  const c=$(container); if(!c) return;
  // colorize bracket tags
  const tagged=line.replace(/(\[[A-Z]+\])/g,'<span class="log-tag">$1</span>');
  const ln=el(`<div class="log-line ${level}"><span class="log-dot"></span><span class="log-time">${nowTime()}</span><span>${tagged}</span></div>`);
  c.appendChild(ln);
  c.scrollTop=c.scrollHeight;
}

/* ============================================================
   WIRING per screen
   ============================================================ */
function wireDownload(){
  const eye=$("#dlKeyEye"), key=$("#dlKey");
  eye.onclick=()=>{ const show=key.type==="password"; key.type=show?"text":"password"; eye.innerHTML=icon(show?"eyeoff":"eye"); };
  const start=$("#dlStart"), verify=$("#dlVerify");
  start.onclick=()=>{
    if(dlState==="running") return;
    dlState="running"; setBtnLoading(start,true,t("working"));
    $("#dlConsole").innerHTML=""; $("#dlBar").classList.add("indeterminate");
    Bridge.startDownload($("#dlUrl").value,$("#dlKey").value);
  };
  verify.onclick=()=>{ $("#dlConsole").innerHTML=""; setBtnLoading(verify,true,t("working")); Bridge.verifyArchives().then(()=>setBtnLoading(verify,false)); };

  Bridge.on("download:progress",d=>{
    dlData=d; $("#dlBar").classList.remove("indeterminate");
    $("#dlCur").textContent=d.current; $("#dlTot").textContent=d.total;
    $("#dlSpeed").textContent=d.speed; $("#dlName").textContent=d.name;
    $("#dlFill").style.width=(d.current/d.total*100)+"%";
  });
  Bridge.on("download:done",()=>{ dlState="done"; setBtnLoading(start,false); toast(t("dl_done"),"success"); });
  Bridge.on("log",e=>{ if(e.channel==="download"||e.channel==="verify") appendLog("#dlConsole",e); });
}

function wireOrganize(){
  const run=$("#orgRun");
  run.onclick=()=>{ setBtnLoading(run,true,t("working")); $("#orgConsole").innerHTML=""; $("#orgChips").innerHTML="";
    Bridge.organizeFiles().then(sum=>{ setBtnLoading(run,false); toast(t("org_done"),"success");
      $("#orgChips").innerHTML=`
        <span class="chip ok">${icon("check")} ${sum.extracted} ${t("sum_extracted")}</span>
        <span class="chip">${icon("organize")} ${sum.fixed} ${t("sum_fixed")}</span>
        <span class="chip warn">${icon("alert")} ${sum.removed} ${t("sum_removed")}</span>`;
    });
  };
  Bridge.on("log",e=>{ if(e.channel==="organize") appendLog("#orgConsole",e); });
}

function wireLauncher(){
  $("#llRefresh").onclick=()=>{ const ic=$("#llRefresh"); ic.style.transition="transform .5s"; ic.style.transform="rotate(360deg)";
    setTimeout(()=>{ic.style.transform="";ic.style.transition="";},520);
    Bridge.scanGames().then(g=>{ GAMES=g; if(!GAMES.find(x=>x.id===selectedGameId))selectedGameId=GAMES[0]?.id; renderGameRows($("#llSearch").value); renderHero(); }); };
  $("#llSearch").oninput=e=>renderGameRows(e.target.value);
  $("#kioskExit").onclick=()=>{
    if(CONFIG.launcher.kioskLock){ modal({title:t("exit_kiosk_q"),body:t("exit_kiosk_sub"),confirmLabel:t("yes_exit"),danger:true,onConfirm:()=>navigate("setup")}); }
    else navigate("setup");
  };
}

function setBtnLoading(btn,on,txt){
  if(!btn) return; btn.classList.toggle("loading",on);
  const t2=btn.querySelector(".btn-txt"); if(t2&&txt&&on){ btn.dataset.orig=t2.textContent; t2.textContent=txt; }
  else if(t2&&btn.dataset.orig&&!on){ t2.textContent=btn.dataset.orig; }
}

/* ============================================================
   TEXT RE-RENDER (language switch)
   ============================================================ */
window.__rerenderText=function(){
  $$("[data-t]").forEach(n=>{ n.textContent=t(n.dataset.t); });
  $$("[data-t-text='jamname']").forEach(n=>n.textContent=CONFIG.jam.name);
  // placeholders
  const s=$("#llSearch"); if(s)s.placeholder=t("search_games");
  const lp=$("#langPill .flag"); if(lp)lp.textContent=LANG.toUpperCase();
  if(currentScreen==="launcher"){ renderHero(); }
  if(currentScreen==="setup"&&window.refreshSetupText) window.refreshSetupText();
};

/* ============================================================
   EFFECT APPLY (from config)
   ============================================================ */
function applyEffectFromConfig(){
  if(!effectCtl) return;
  const e=CONFIG.effect;
  effectCtl.setEffect(e.name, e.intensity, 1);
  effectCtl.setEnabled(e.enabled);
}

/* ============================================================
   INIT
   ============================================================ */
async function init(){
  CONFIG = await Bridge.getConfig();
  LANG = CONFIG.jam.language || "tr";
  document.documentElement.setAttribute("lang",LANG);
  applyConfig(CONFIG);

  // build shell
  const app=$("#app");
  app.insertAdjacentHTML("afterbegin", renderSidebar());
  const main=el(`<div class="main" id="main"></div>`);
  main.innerHTML = screenDownload()+screenOrganize()+screenLauncher()+ (window.renderSetup?window.renderSetup():"");
  app.appendChild(main);

  // effects
  effectCtl = makeEffectController($("#bg-canvas"));
  applyEffectFromConfig();

  // wire
  wireDownload(); wireOrganize(); wireLauncher(); wireTimerEvents();
  if(window.wireSetup) window.wireSetup();

  // nav
  $$("[data-nav]").forEach(b=>b.onclick=()=>navigate(b.dataset.nav));
  $("#collapseBtn").onclick=()=>$("#sidebar").classList.toggle("collapsed");
  $("#langPill").onclick=()=>{ setLanguage(LANG==="tr"?"en":"tr"); CONFIG.jam.language=LANG; };

  // start on launcher
  navigate("launcher");
}
document.addEventListener("DOMContentLoaded",init);
