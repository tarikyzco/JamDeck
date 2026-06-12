/* ============================================================
   JamDeck — BRIDGE (mock)
   Event emitter + Promise API. Real pywebview impl replaces 1:1:
   each method -> window.pywebview.api.<method>(...) ; Python pushes
   via window.JamDeck.emit(event, payload).
   ============================================================ */

const DEFAULT_CONFIG = {
  jam:    { name:"AyazJam 2025", tagline:"Game Jam", logo:null, background:null, language:"tr" },
  theme:  { preset:"frostbite", colors:{...THEME_PRESETS.frostbite.colors}, radius:18, glow:1.0 },
  effect: { name:"snow", intensity:150, enabled:true },
  launcher:{ defaultMinutes:5, onTimeUp:"kill", killDelay:3, timerOverlay:true, kioskLock:true },
  paths:  { gamesDir:"C:\\JamGames" }
};

/* ---------- mock game list (24 entries) ---------- */
const ENGINES = ["unity","unreal","godot","gamemaker","other"];
const TEAM_WORDS = ["Pixel","Frost","Neon","Crimson","Echo","Lunar","Void","Hyper","Quantum","Ember","Static","Glitch","Cobalt","Solar","Drift","Iron","Nova","Pulse","Onyx","Vapor","Cosmic","Rogue","Astral","Zenith"];
const GAME_WORDS = ["Ascent","Dash","Protocol","Drift","Loop","Hollow","Signal","Reverie","Cascade","Verge","Halt","Bloom","Fracture","Rift","Tide","Forge","Specter","Orbit","Relay","Mire","Beacon","Surge","Husk","Veil"];

function mockCover(seed){
  // deterministic gradient SVG data url -> graceful, no network
  const hues=[(seed*47)%360,(seed*47+60)%360];
  const svg=`<svg xmlns='http://www.w3.org/2000/svg' width='600' height='800'>
    <defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>
      <stop offset='0' stop-color='hsl(${hues[0]},70%,22%)'/>
      <stop offset='1' stop-color='hsl(${hues[1]},75%,12%)'/></linearGradient></defs>
    <rect width='600' height='800' fill='url(#g)'/>
    <circle cx='${120+seed*37%360}' cy='${180+seed*53%420}' r='${90+seed*13%120}' fill='hsla(${hues[0]},80%,60%,.18)'/>
    <circle cx='${380+seed*29%180}' cy='${520+seed*41%200}' r='${60+seed*17%90}' fill='hsla(${hues[1]},80%,60%,.16)'/>
  </svg>`;
  return "data:image/svg+xml;utf8,"+encodeURIComponent(svg).replace(/'/g,"%27");
}

function buildMockGames(){
  const games=[];
  for(let i=0;i<24;i++){
    const team=TEAM_WORDS[i%TEAM_WORDS.length]+" "+["Studio","Collective","Labs","Works","Team","Crew"][i%6];
    const game=GAME_WORDS[i%GAME_WORDS.length]+(i%5===0?" "+["II","Zero","X","Prime"][i%4]:"");
    const engine=ENGINES[i%ENGINES.length];
    const multi = i%4===0; // some have multiple exes
    const exes = multi?["Game.exe","Launcher.exe","x64/Game.exe"]:[`${game.replace(/\s/g,"")}.exe`];
    const hasCover = i%7!==3; // some missing cover -> placeholder
    games.push({ id:"g"+i, team, game, cover:hasCover?mockCover(i+1):null,
      exes, currentExe:0, engine });
  }
  return games;
}

/* ---------- event emitter ---------- */
function makeEmitter(){
  const map={};
  return {
    on(ev,cb){ (map[ev]||(map[ev]=[])).push(cb); return ()=>{ map[ev]=map[ev].filter(f=>f!==cb); }; },
    emit(ev,payload){ (map[ev]||[]).forEach(cb=>{ try{cb(payload)}catch(e){console.error(e)} }); }
  };
}

/* ---------- mock helpers ---------- */
const wait = ms => new Promise(r=>setTimeout(r,ms));
function nowTime(){ const d=new Date(); return d.toTimeString().slice(0,8); }

function makeBridge(){
  const em = makeEmitter();
  let config = JSON.parse(JSON.stringify(DEFAULT_CONFIG));
  let cancelDl=false;
  let timerHandle=null;

  // expose JamDeck.emit so a real Python layer can push events identically
  window.JamDeck = window.JamDeck || {};
  window.JamDeck.emit = (ev,payload)=>em.emit(ev,payload);

  const Bridge = {
    on:(ev,cb)=>em.on(ev,cb),
    _emit:(ev,p)=>em.emit(ev,p),

    getConfig(){ return Promise.resolve(JSON.parse(JSON.stringify(config))); },
    saveConfig(c){ config=JSON.parse(JSON.stringify(c)); return wait(220).then(()=>({ok:true})); },
    resetConfig(){ config=JSON.parse(JSON.stringify(DEFAULT_CONFIG)); return wait(150).then(()=>JSON.parse(JSON.stringify(config))); },
    exportConfig(){ const blob=JSON.stringify(config,null,2); return Promise.resolve({ok:true,data:blob}); },
    importConfig(file){ return Promise.resolve(JSON.parse(JSON.stringify(config))); },

    pickImage(target){
      // mock: return a generated gradient dataURL so preview updates
      const seed = target==="logo"?7:21;
      return wait(300).then(()=>({ path:`C:\\Picked\\${target}.png`, dataUrl:mockCover(seed) }));
    },
    selectGamesFolder(){ return wait(250).then(()=>({path:"C:\\JamGames"})); },
    openGamesFolder(){ return Promise.resolve({ok:true}); },

    startDownload(url,apiKey){
      cancelDl=false;
      const total = 24;
      em.emit("log",{channel:"download",level:"info",line:`Connecting to ${url||"itch.io"}…`});
      (async()=>{
        await wait(400);
        em.emit("log",{channel:"download",level:"success",line:`Authenticated · ${total} entries found`});
        for(let i=1;i<=total;i++){
          if(cancelDl){ em.emit("log",{channel:"download",level:"warning",line:"Download cancelled by user"}); return; }
          const g=`${GAME_WORDS[i%GAME_WORDS.length]} by ${TEAM_WORDS[i%TEAM_WORDS.length]}`;
          const speed=(2.5+Math.random()*5).toFixed(1)+" MB/s";
          em.emit("download:progress",{current:i,total,name:g,speed});
          em.emit("log",{channel:"download",level:"info",line:`↓ [${i}/${total}] ${g}`});
          await wait(260+Math.random()*240);
          if(Math.random()<0.08) em.emit("log",{channel:"download",level:"warning",line:`  retried chunk for ${g}`});
        }
        em.emit("log",{channel:"download",level:"success",line:"All downloads complete ✓"});
        em.emit("download:done",{ok:true});
      })();
      return Promise.resolve({ok:true});
    },
    cancelDownload(){ cancelDl=true; return Promise.resolve({ok:true}); },

    verifyArchives(){
      (async()=>{
        const total=24; let bad=0;
        em.emit("log",{channel:"verify",level:"info",line:"Verifying archive integrity…"});
        for(let i=1;i<=total;i++){
          await wait(120);
          const ok=Math.random()>0.1;
          if(ok) em.emit("log",{channel:"verify",level:"success",line:`OK  [${i}/${total}] entry_${i}.zip`});
          else { bad++; em.emit("log",{channel:"verify",level:"error",line:`BAD [${i}/${total}] entry_${i}.zip — CRC mismatch`}); }
        }
        em.emit("log",{channel:"verify",level:bad?"warning":"success",line:`Done · ${total-bad} OK, ${bad} corrupt`});
      })();
      return wait(120*24+200).then(()=>({ok:true,corrupt:0}));
    },

    organizeFiles(){
      let extracted=0,fixed=0,removed=0;
      (async()=>{
        const total=24;
        em.emit("log",{channel:"organize",level:"info",line:"Scanning JamGames directory…"});
        for(let i=1;i<=total;i++){
          await wait(150);
          const r=Math.random();
          if(r<0.6){ extracted++; em.emit("log",{channel:"organize",level:"success",line:`[UNZIP] entry_${i}.zip → ${i} files`}); }
          else if(r<0.78){ extracted++; em.emit("log",{channel:"organize",level:"success",line:`[WINRAR] entry_${i}.rar extracted`}); }
          else if(r<0.92){ fixed++; em.emit("log",{channel:"organize",level:"info",line:`[FIX] flattened nested folder for entry_${i}`}); }
          else { removed++; em.emit("log",{channel:"organize",level:"warning",line:`[CLEAN] removed junk folder entry_${i} (no .exe)`}); }
        }
        em.emit("log",{channel:"organize",level:"success",line:`Done ✓ ${extracted} extracted, ${fixed} fixed, ${removed} removed`});
      })();
      return wait(150*24+250).then(()=>({extracted:18,fixed:4,removed:2}));
    },

    scanGames(){ return wait(500).then(()=>buildMockGames()); },

    launchGame(gameId,exeIndex,minutes){
      // start a countdown timer that emits ticks + timesup
      if(timerHandle) clearInterval(timerHandle);
      let remaining = Math.round((minutes||config.launcher.defaultMinutes)*60);
      em.emit("timer:tick",{remaining});
      timerHandle=setInterval(()=>{
        remaining--;
        em.emit("timer:tick",{remaining});
        if(remaining<=0){ clearInterval(timerHandle); timerHandle=null; em.emit("timer:timesup",{}); }
      },1000);
      return Promise.resolve({ok:true});
    },
    stopGame(){ if(timerHandle){clearInterval(timerHandle);timerHandle=null;} em.emit("game:closed",{}); return Promise.resolve({ok:true}); },

    // demo helper to launch a short timer quickly (not part of real API)
    _demoTimer(seconds){
      if(timerHandle) clearInterval(timerHandle);
      let remaining=seconds;
      em.emit("timer:tick",{remaining});
      timerHandle=setInterval(()=>{ remaining--; em.emit("timer:tick",{remaining});
        if(remaining<=0){clearInterval(timerHandle);timerHandle=null;em.emit("timer:timesup",{});} },1000);
    }
  };
  return Bridge;
}
