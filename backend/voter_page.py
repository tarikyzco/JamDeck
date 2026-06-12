# Voter-facing page template (served by voting_server for /v/<token>).
# Plain string with __LABEL__ / __SCALE__ / __JAM__ / __THEME__ placeholders
# (NOT an f-string) so the embedded JS keeps normal { } braces.
# Faz 5 redesign: same CSS-variable palette as the desktop app; the organizer's
# theme is injected server-side into the /*__THEME__*/ slot inside :root.
# Visibility is driven by body[data-state]:
#   gate-pin / gate-code / vote / waiting / closed / full
# The JS is validated by tests (node --check + real-browser Playwright test).

VOTER_PAGE = """<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"><meta name="theme-color" id="metaTheme" content="#050a14"><title>__LABEL__ Oylaması</title><style>
/* ─── TEMA (organizatörün teması sunucu tarafından enjekte edilir) ─── */
:root{
  --bg:#050a14; --bg-2:#080e1c;
  --surface:#0f1629; --surface-2:#141d33; --border:#1e293b;
  --accent:#00f2ff; --accent-2:#0062ff; --accent-ink:#03121c;
  --text:#ffffff; --text-muted:#94a3b8;
  --success:#00e676; --warning:#ffab00; --error:#ff1744;
  --radius:18px; --radius-sm:10px;
  --glow-a:30%;
  --glow:0 0 18px color-mix(in srgb, var(--accent) var(--glow-a), transparent);
  --font-display:system-ui,-apple-system,'Segoe UI',sans-serif;
  --font-body:system-ui,-apple-system,'Segoe UI',sans-serif;
  --font-mono:ui-monospace,'Cascadia Mono',Consolas,Menlo,monospace;
  /*__THEME__*/
}
/* AÇIK MOD (kullanıcı seçimi — sağ üst düğme): nötr zeminler açılır,
   jam'in accent renkleri korunur */
:root.light{
  --bg:#eef1f7; --bg-2:#e6eaf2;
  --surface:#ffffff; --surface-2:#f2f5fa; --border:#d7dde8;
  --text:#10141c; --text-muted:#5a6577;
}
*{box-sizing:border-box; margin:0; padding:0}
/* TEK DÜZ ZEMİN: sayfa, iOS durum çubuğu ve alt bar hepsi aynı --bg rengi.
   Degrade/ışık yıkaması bilinçli olarak YOK — Safari çubukları theme-color ile
   düz boyadığı için zemindeki en ufak ton farkı dikiş gibi görünüyordu. */
html{-webkit-text-size-adjust:100%; background:var(--bg)}
body{
  min-height:100vh; min-height:100dvh;
  background:var(--bg);
  color:var(--text); font:14px/1.45 var(--font-body);
  -webkit-font-smoothing:antialiased;
  display:flex; flex-direction:column; align-items:center;
  /* çentik/alt bar güvenli alanlarına taş (viewport-fit=cover ile) */
  padding:calc(10px + env(safe-area-inset-top)) 12px calc(14px + env(safe-area-inset-bottom));
}
.wrap{width:100%; max-width:480px; display:flex; flex-direction:column; gap:8px; flex:1}
button{font-family:var(--font-body)}
button:focus-visible{outline:2px solid var(--accent); outline-offset:2px}
.card{
  background:color-mix(in srgb, var(--surface) 84%, transparent);
  backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
  border:1px solid var(--border); border-radius:var(--radius);
  padding:12px 14px;
}
.top{display:flex; align-items:center; justify-content:space-between; gap:8px; padding:2px 4px}
.top .group-name{
  font:800 13px var(--font-display); letter-spacing:.04em; text-transform:uppercase;
  color:var(--accent); display:flex; align-items:center; gap:7px;
}
.top .group-name .gdot{width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:var(--glow)}
.top .top-right{display:flex; align-items:center; gap:9px}
.top .jam-id{font:600 10.5px var(--font-mono); color:var(--text-muted); letter-spacing:.06em; white-space:nowrap}
.mode-btn{
  width:32px; height:32px; border-radius:50%; border:1px solid var(--border);
  background:color-mix(in srgb, var(--surface) 84%, transparent);
  color:var(--text-muted); font-size:14px; line-height:1; cursor:pointer;
  display:grid; place-items:center; transition:color .15s, border-color .15s;
}
.mode-btn:active{transform:scale(.94)}
.toast{
  position:fixed; top:calc(10px + env(safe-area-inset-top)); left:50%; z-index:50;
  /* gizliyken opacity+visibility da kapalı — yoksa gölgesi üstte
     "kesik kutu" gibi sızıyordu */
  transform:translate(-50%,-130%); opacity:0; visibility:hidden;
  transition:transform .28s cubic-bezier(.3,1.2,.4,1), opacity .25s, visibility .25s;
  width:calc(100% - 24px); max-width:456px;
  background:color-mix(in srgb, var(--surface) 94%, transparent);
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1px solid color-mix(in srgb, var(--accent) 40%, var(--border));
  border-left:3px solid var(--accent);
  border-radius:var(--radius-sm); padding:10px 14px;
  font:600 12.5px/1.4 var(--font-body);
  box-shadow:0 8px 28px color-mix(in srgb, var(--bg) 70%, transparent);
}
.toast.show{transform:translate(-50%,0); opacity:1; visibility:visible}
.toast.warn{border-color:color-mix(in srgb, var(--warning) 45%, var(--border)); border-left-color:var(--warning)}
.gate{
  flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center;
  gap:0; text-align:center; padding:22px 18px; margin:auto 0;
}
.gate-ic{font-size:30px; margin-bottom:10px; opacity:.9}
.gate-title{font:800 17px var(--font-display); letter-spacing:-.01em}
.gate-sub{font-size:12.5px; color:var(--text-muted); margin-top:4px; max-width:300px}
.gate-input{
  margin-top:14px; width:100%; max-width:240px;
  padding:11px 12px; text-align:center;
  font:700 19px var(--font-mono); letter-spacing:.35em; text-transform:uppercase;
  color:var(--text); background:color-mix(in srgb, var(--bg-2) 82%, transparent);
  border:1px solid var(--border); border-radius:var(--radius-sm);
  transition:border-color .16s, box-shadow .16s;
}
.gate-input::placeholder{color:color-mix(in srgb, var(--text-muted) 55%, transparent); letter-spacing:.2em}
.gate-input:focus{outline:none; border-color:var(--accent); box-shadow:0 0 0 3px color-mix(in srgb, var(--accent) 18%, transparent)}
.gate-btn{
  margin-top:10px; width:100%; max-width:240px; min-height:46px;
  border:none; border-radius:var(--radius-sm); cursor:pointer;
  background:linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent-2) 80%, var(--accent)));
  color:var(--accent-ink); font:700 14.5px var(--font-body);
  box-shadow:var(--glow); transition:filter .15s, transform .12s;
}
.gate-btn:active{transform:scale(.98)}
.gate-btn:disabled{opacity:.5; cursor:not-allowed}
.gate-err{margin-top:10px; font:600 12px var(--font-body); color:var(--error); min-height:17px}
.disabled-msg{
  flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center;
  gap:8px; text-align:center; padding:26px 18px; margin:auto 0;
}
.disabled-msg .ic{font-size:30px; opacity:.85}
.disabled-msg b{font:800 16px var(--font-display); color:var(--error)}
.disabled-msg p{font-size:12.5px; color:var(--text-muted); max-width:280px}
.nav{display:flex; gap:8px}
.nav-btn{
  flex:1; min-height:42px; padding:8px 12px;
  background:color-mix(in srgb, var(--surface) 84%, transparent);
  border:1px solid var(--border); border-radius:var(--radius-sm);
  color:var(--text-muted); font:600 13px var(--font-body); cursor:pointer;
  transition:color .15s, border-color .15s, transform .12s;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}
.nav-btn:active{transform:scale(.98)}
.nav-btn[hidden]{display:none}
.nav-btn.highlight{
  color:var(--warning); border-color:color-mix(in srgb, var(--warning) 50%, var(--border));
  animation:navPulse 1.4s ease infinite;
}
@keyframes navPulse{50%{box-shadow:0 0 14px color-mix(in srgb, var(--warning) 35%, transparent)}}
.game-card{position:relative; padding:13px 15px; display:flex; flex-direction:column; gap:3px}
.game-card .g-team{font:700 10px var(--font-body); letter-spacing:.14em; text-transform:uppercase; color:var(--text-muted)}
.game-card .g-name{font:800 21px/1.15 var(--font-display); letter-spacing:-.015em}
.live-badge{
  position:absolute; top:11px; right:13px;
  display:inline-flex; align-items:center; gap:6px;
  font:700 10px var(--font-body); letter-spacing:.05em; text-transform:uppercase;
  color:var(--error);
  background:color-mix(in srgb, var(--error) 12%, transparent);
  border:1px solid color-mix(in srgb, var(--error) 38%, transparent);
  border-radius:999px; padding:3px 9px;
}
.live-badge .ldot{width:6px; height:6px; border-radius:50%; background:var(--error); animation:livePulse 1.1s ease infinite}
@keyframes livePulse{50%{opacity:.3}}
.game-card.flash{animation:cardFlash .7s ease}
@keyframes cardFlash{
  0%{box-shadow:0 0 0 1px var(--accent), 0 0 26px color-mix(in srgb, var(--accent) 55%, transparent)}
  100%{box-shadow:0 0 0 0 transparent}
}
.waiting{display:flex; flex-direction:column; align-items:center; gap:8px; text-align:center; padding:30px 18px}
.waiting .ic{font-size:28px; opacity:.55}
.waiting b{font:700 14px var(--font-display); color:var(--text-muted)}
.waiting p{font-size:12px; color:color-mix(in srgb, var(--text-muted) 80%, transparent); max-width:270px}
#ratingArea{display:flex; flex-direction:column; gap:8px}
.cat-block{padding:10px 12px 12px}
.cat-label{
  font:700 12px var(--font-body); letter-spacing:.07em; text-transform:uppercase;
  color:var(--text-muted); margin-bottom:8px;
  display:flex; align-items:center; justify-content:space-between; gap:8px;
}
.cat-label .picked{font:800 12px var(--font-mono); color:var(--accent); letter-spacing:0}
.cat-label .picked:empty::before{content:"—"; color:color-mix(in srgb, var(--text-muted) 50%, transparent)}
.rating{display:grid; grid-template-columns:repeat(5,1fr); gap:6px}
.rating button{
  min-height:44px; border-radius:var(--radius-sm); cursor:pointer;
  background:color-mix(in srgb, var(--surface-2) 85%, transparent);
  border:1px solid var(--border); color:var(--text);
  font:700 15px var(--font-mono);
  transition:background .12s, border-color .12s, color .12s, transform .1s;
  touch-action:manipulation;
}
.rating button:active{transform:scale(.94)}
/* seçilen puana KADAR tüm kutular dolu görünür (bar mantığı);
   asıl tıklanan kutu (.peak) ekstra parıltıyla vurgulanır */
.rating button.selected{
  background:linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent-2) 75%, var(--accent)));
  border-color:var(--accent); color:var(--accent-ink);
}
.rating button.peak{box-shadow:var(--glow)}
.submit-btn{
  width:100%; min-height:48px; border:none; cursor:pointer;
  border-radius:var(--radius-sm);
  background:linear-gradient(135deg, var(--accent), color-mix(in srgb, var(--accent-2) 80%, var(--accent)));
  color:var(--accent-ink); font:800 15px var(--font-body); letter-spacing:.01em;
  box-shadow:var(--glow);
  transition:filter .15s, transform .12s, opacity .15s;
}
.submit-btn:active{transform:scale(.985)}
.submit-btn:disabled{opacity:.4; cursor:not-allowed; box-shadow:none}
.submit-btn.voted{
  background:color-mix(in srgb, var(--success) 16%, transparent);
  border:1px solid color-mix(in srgb, var(--success) 45%, transparent);
  color:var(--success); opacity:1; box-shadow:none; cursor:default;
}
.status{text-align:center; font:600 12px var(--font-body); min-height:17px; color:var(--text-muted)}
.status.ok{color:var(--success)}
.status.err{color:var(--error)}
.dbg{
  text-align:center; font:10px var(--font-mono);
  color:color-mix(in srgb, var(--text-muted) 45%, transparent);
  letter-spacing:.04em; padding-bottom:2px; user-select:none; word-break:break-all;
}
/* durum görünürlüğü: body[data-state] */
.top,.nav,#gameContainer,#ratingArea,.status,.dbg,#gate,#disabledMsg{display:none}
body[data-state^="gate"] #gate{display:flex}
body[data-state="vote"] .top,
body[data-state="waiting"] .top{display:flex}
body[data-state="vote"] .nav{display:flex}
body[data-state="vote"] #gameContainer,
body[data-state="waiting"] #gameContainer{display:block}
body[data-state="vote"] #ratingArea{display:flex}
body[data-state="vote"] .status,
body[data-state="vote"] .dbg,
body[data-state="waiting"] .dbg{display:block}
body[data-state="closed"] #disabledMsg,
body[data-state="full"] #disabledMsg{display:flex}
body[data-state="vote"] .waiting,
body[data-state="waiting"] .game-card{display:none}
body[data-state="waiting"] .waiting{display:flex}
</style></head><body data-state="waiting">

<div class="toast" id="toast"></div>

<div class="wrap">
  <header class="top">
    <span class="group-name"><span class="gdot"></span>__LABEL__ Oylaması</span>
    <span class="top-right">
      <span class="jam-id">__JAM__</span>
      <button class="mode-btn" id="modeBtn" title="Açık / koyu tema">☀</button>
    </span>
  </header>

  <div class="card gate" id="gate">
    <span class="gate-ic" id="gateIc">🔒</span>
    <div class="gate-title" id="gateTitle"></div>
    <div class="gate-sub" id="gateSub"></div>
    <input class="gate-input" id="gateInput" type="text" autocomplete="one-time-code" autocapitalize="characters" enterkeyhint="go">
    <button class="gate-btn" id="gateBtn">Onayla</button>
    <div class="gate-err" id="gateErr"></div>
  </div>

  <div class="card disabled-msg" id="disabledMsg">
    <span class="ic">🚫</span>
    <b id="disabledTitle"></b>
    <p id="disabledSub"></p>
  </div>

  <nav class="nav" id="nav">
    <button class="nav-btn" id="prevBtn" hidden></button>
    <button class="nav-btn highlight" id="nextBtn" hidden>Sıradaki oyun →</button>
  </nav>

  <div id="gameContainer">
    <div class="card game-card" id="gameCard"></div>
    <div class="card waiting">
      <span class="ic">🎮</span>
      <b>Henüz aktif oyun yok</b>
      <p>Düzenleyici bir oyun başlattığında burada görünecek.</p>
    </div>
  </div>

  <div id="ratingArea">
    <div id="cats"></div>
    <button class="submit-btn" id="submitBtn" disabled>Oyu Gönder</button>
  </div>

  <div class="status" id="status"></div>
  <div class="dbg" id="dbg">durum: bağlanıyor…</div>
</div>

<script>
/* Safari üst/alt çubuk rengi = aktif temanın --bg değeri (enjekte tema + açık mod dahil) */
function syncMetaTheme(){
  var m=document.getElementById('metaTheme');if(!m)return;
  var bg=getComputedStyle(document.documentElement).getPropertyValue('--bg').trim();
  if(bg)m.content=bg;
}
/* Açık/koyu mod: oy veren kendi seçer (cihazda hatırlanır); koyu = jam'in teması */
(function(){
  var btn=document.getElementById('modeBtn');
  function apply(light){
    document.documentElement.classList.toggle('light',light);
    if(btn)btn.textContent=light?'☾':'☀';
    syncMetaTheme();
  }
  apply(localStorage.getItem('jamdeck_voter_mode')==='light');
  if(btn)btn.addEventListener('click',function(){
    var light=!document.documentElement.classList.contains('light');
    localStorage.setItem('jamdeck_voter_mode',light?'light':'dark');
    apply(light);
  });
})();
const TOKEN=location.pathname.split('/').pop();
const SCALE=__SCALE__;
let voterId=localStorage.getItem('jamdeck_voter');
if(!voterId){voterId='v_'+Math.random().toString(36).substr(2,9);localStorage.setItem('jamdeck_voter',voterId);}
let games=[],idx=-1,cats=[],selected={},enabled=true,groupLabel='',submitted=false,currentId=null;
let access='open',authed=true,full=false;
let toastTimer=null;
function setState(st){document.body.dataset.state=st;}
function accessErr(code){return ({bad_code:'Kod geçersiz.',code_used:'Bu kod başka bir cihazda kullanılmış.',bad_pin:'PIN yanlış.',full:'Kontenjan dolu.',rate:'Çok hızlı denedin, birkaç saniye bekle.','group disabled':'Bu grup kapalı.'})[code]||'Bir hata oluştu.';}
async function submitAccess(){
  const inp=document.getElementById('gateInput'),err=document.getElementById('gateErr'),btn=document.getElementById('gateBtn');
  const val=(inp.value||'').trim();if(!val)return;
  btn.disabled=true;err.textContent='';
  try{
    const body={t:TOKEN,voter:voterId};
    if(access==='pin')body.pin=val;else body.code=val;
    const resp=await fetch('/api/access',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await resp.json();
    if(data.ok){authed=true;document.getElementById('gate').dataset.mode='';renderGame();fetchCurrent();}
    else{err.textContent=accessErr(data.error);}
  }catch(e){err.textContent='Bağlantı hatası';}
  btn.disabled=false;
}
function catsKey(list){return list.map(c=>c.id).join(',');}
function allSelected(){return cats.length>0&&cats.every(c=>selected[c.id]!=null);}
function showToast(msg,kind){
  const t=document.getElementById('toast');
  t.textContent=msg;t.className='toast'+(kind?(' '+kind):'');
  void t.offsetWidth;t.classList.add('show');
  if(toastTimer)clearTimeout(toastTimer);
  toastTimer=setTimeout(function(){t.classList.remove('show');},3200);
}
function flashCard(){const gc=document.getElementById('gameCard');gc.classList.remove('flash');void gc.offsetWidth;gc.classList.add('flash');}
function updateSubmit(){
  const b=document.getElementById('submitBtn');
  if(submitted){b.disabled=true;b.classList.add('voted');b.textContent='✓ Oy Verildi';}
  else{b.classList.remove('voted');b.textContent='Oyu Gönder';b.disabled=!allSelected();}
}
function resetSelection(){
  submitted=false;selected={};
  document.querySelectorAll('#cats .rating button').forEach(b=>b.classList.remove('selected','peak'));
  document.querySelectorAll('#cats .picked').forEach(p=>p.textContent='');
  updateSubmit();
}
function displayed(){return (idx>=0&&idx<games.length)?games[idx]:null;}
function renderCats(list){
  submitted=false;selected={};
  const host=document.getElementById('cats');host.innerHTML='';
  list.forEach(c=>{
    const block=document.createElement('div');block.className='card cat-block';
    const lbl=document.createElement('div');lbl.className='cat-label';
    const name=document.createElement('span');name.textContent=c.label;
    const picked=document.createElement('span');picked.className='picked';
    lbl.appendChild(name);lbl.appendChild(picked);
    const row=document.createElement('div');row.className='rating';
    for(let i=1;i<=SCALE;i++){
      const btn=document.createElement('button');btn.type='button';btn.textContent=i;btn.dataset.score=i;
      btn.addEventListener('click',function(){
        const v=parseInt(this.dataset.score);
        row.querySelectorAll('button').forEach(b=>{
          const bv=parseInt(b.dataset.score);
          b.classList.toggle('selected', bv<=v);
          b.classList.toggle('peak', bv===v);
        });
        selected[c.id]=v;
        picked.textContent=v+'/'+SCALE;
        if(submitted)submitted=false;updateSubmit();
      });
      row.appendChild(btn);
    }
    block.appendChild(lbl);block.appendChild(row);host.appendChild(block);
  });
  updateSubmit();
}
function updateNav(){
  const pv=document.getElementById('prevBtn'),nx=document.getElementById('nextBtn');
  if(idx>0){pv.hidden=false;pv.textContent='← '+games[idx-1].name;}else{pv.hidden=true;}
  nx.hidden=!(idx>=0&&idx<games.length-1);
}
function setDisabledMsg(title,sub){
  document.getElementById('disabledTitle').textContent=title;
  document.getElementById('disabledSub').textContent=sub;
}
function renderGame(){
  const gate=document.getElementById('gate');
  if(!enabled){setState('closed');setDisabledMsg('Bu oy grubu kapalı.','Düzenleyici bu grubu şu an oylamaya kapattı.');return;}
  if(full){setState('full');setDisabledMsg('Kontenjan dolu.','Bu grup için katılımcı limiti doldu. Düzenleyiciye danışın.');return;}
  if(access!=='open'&&!authed){
    setState(access==='pin'?'gate-pin':'gate-code');
    if(gate.dataset.mode!==access){
      gate.dataset.mode=access;
      document.getElementById('gateIc').textContent=(access==='pin')?'🔒':'🎟️';
      document.getElementById('gateTitle').textContent=(access==='pin')?'PIN gerekli':'Erişim kodu gerekli';
      document.getElementById('gateSub').textContent=(access==='pin')?'Düzenleyicinin verdiği PIN ile giriş yap.':'Sana verilen tek-kullanımlık kodu gir.';
      document.getElementById('gateErr').textContent='';
      const inp=document.getElementById('gateInput');
      inp.placeholder=(access==='pin')?'····':'········';
      inp.maxLength=(access==='pin')?8:6;
      inp.inputMode=(access==='pin')?'numeric':'text';
      inp.value='';
    }
    return;
  }
  gate.dataset.mode='';
  const g=displayed();
  if(g){
    setState('vote');
    const gc=document.getElementById('gameCard');
    const liveBadge=(g.id===currentId)?'<span class="live-badge"><span class="ldot"></span>Şu an sunulan</span>':'';
    gc.innerHTML=liveBadge+'<span class="g-team"></span><span class="g-name"></span>';
    gc.querySelector('.g-team').textContent=groupLabel;
    gc.querySelector('.g-name').textContent=g.name;
  }else{
    setState('waiting');
  }
  updateNav();
}
async function submitVote(silent){
  const g=displayed();if(!g)return false;
  const st=document.getElementById('status');
  try{
    const resp=await fetch('/api/vote',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({t:TOKEN,game_id:g.id,scores:selected,voter:voterId})});
    const data=await resp.json();
    if(data.ok){
      if(!silent){st.textContent='✓ Oyunuz kaydedildi';st.className='status ok';setTimeout(()=>{st.textContent='';st.className='status';},3000);}
      return true;
    }
    if(!silent){st.textContent='✗ Hata: '+(data.error||'');st.className='status err';}
    return false;
  }catch(e){if(!silent){st.textContent='✗ Bağlantı hatası';st.className='status err';}return false;}
}
async function fetchCurrent(){
  const dbg=document.getElementById('dbg');
  try{
    const resp=await fetch('/api/current?t='+TOKEN+'&voter='+encodeURIComponent(voterId));
    const data=await resp.json();
    if(!data.ok){
      setState('closed');
      setDisabledMsg('Bağlantı geçersiz veya eski.','Düzenleyiciden GÜNCEL oy linkini isteyin.');
      if(dbg)dbg.textContent='durum: ok=false ('+resp.status+') — token geçersiz/eski';
      return;
    }
    enabled=data.enabled;groupLabel=data.label||'';currentId=data.current!=null?data.current:null;
    access=data.access||'open';authed=(data.authed!==undefined)?data.authed:(access==='open');full=!!data.full;
    const newCats=data.categories||[];
    if(catsKey(newCats)!==catsKey(cats)){cats=newCats;renderCats(cats);}
    const prevLen=games.length;
    games=data.games||[];
    const wasLatest=(idx<0)||(idx===prevLen-1);
    const newGameArrived=games.length>prevLen;
    let flashOnRender=false;
    if(!authed){idx=games.length-1;}  // kapıda: sessizce en yeniyi izle
    else if(idx<0){idx=games.length-1;}
    else if(newGameArrived&&wasLatest){
      if(allSelected()){await submitVote(true);idx=games.length-1;resetSelection();flashOnRender=true;}
      else{showToast('🎮 Sıradaki oyun başladı! Bu oyunu bitirip "Sıradaki oyun →" butonuna bas.','warn');}
    }
    else if(newGameArrived){showToast('🎮 Yeni oyun başladı','warn');}
    if(idx>=games.length)idx=games.length-1;
    if(dbg)dbg.textContent='durum: grup='+data.group+' · gösterilen='+(displayed()?displayed().name:'(yok)')+' · oyun='+games.length;
    renderGame();
    if(flashOnRender){flashCard();showToast('✓ Oyunuz kaydedildi · Yeni oyun: '+(displayed()?displayed().name:''));}
  }catch(e){if(dbg)dbg.textContent='durum: bağlantı hatası — '+e;}
}
fetchCurrent();setInterval(fetchCurrent,2000);
document.getElementById('prevBtn').addEventListener('click',function(){if(idx>0){idx--;resetSelection();renderGame();}});
document.getElementById('nextBtn').addEventListener('click',function(){if(idx<games.length-1){idx=games.length-1;resetSelection();renderGame();flashCard();}});
document.getElementById('submitBtn').addEventListener('click',async function(){if(this.disabled)return;this.disabled=true;const ok=await submitVote(false);if(ok)submitted=true;updateSubmit();});
document.getElementById('gateBtn').addEventListener('click',submitAccess);
document.getElementById('gateInput').addEventListener('keydown',function(e){if(e.key==='Enter')submitAccess();});
document.getElementById('gameCard').addEventListener('animationend',function(){this.classList.remove('flash');});
</script></body></html>"""


# ─────────────────────────────────────────────────────────────────────────────
# KOD PANOSU (/k/<token>): gruba tek link paylaşılır; herkes panodan boş bir
# kod seçer. Kullanılan kod 2.5 sn'lik poll ile HERKESTE anında "kullanıldı"ya
# düşer → "hangi kod boş?" karmaşası biter. Voter sayfasıyla aynı tema dili.
# Placeholder'lar: __LABEL__ / __JAM__ / /*__THEME__*/  (f-string DEĞİL).
# ─────────────────────────────────────────────────────────────────────────────

CODES_PAGE = """<!DOCTYPE html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover"><meta name="theme-color" id="metaTheme" content="#050a14"><title>__LABEL__ Kod Panosu</title><style>
:root{
  --bg:#050a14; --bg-2:#080e1c;
  --surface:#0f1629; --surface-2:#141d33; --border:#1e293b;
  --accent:#00f2ff; --accent-2:#0062ff; --accent-ink:#03121c;
  --text:#ffffff; --text-muted:#94a3b8;
  --success:#00e676; --warning:#ffab00; --error:#ff1744;
  --radius:18px; --radius-sm:10px;
  --glow-a:30%;
  --glow:0 0 18px color-mix(in srgb, var(--accent) var(--glow-a), transparent);
  --font-display:system-ui,-apple-system,'Segoe UI',sans-serif;
  --font-body:system-ui,-apple-system,'Segoe UI',sans-serif;
  --font-mono:ui-monospace,'Cascadia Mono',Consolas,Menlo,monospace;
  /*__THEME__*/
}
*{box-sizing:border-box; margin:0; padding:0}
html{-webkit-text-size-adjust:100%; background:var(--bg)}
body{
  min-height:100vh; min-height:100dvh; background:var(--bg);
  color:var(--text); font:14px/1.45 var(--font-body);
  -webkit-font-smoothing:antialiased;
  display:flex; flex-direction:column; align-items:center;
  padding:calc(10px + env(safe-area-inset-top)) 12px calc(14px + env(safe-area-inset-bottom));
}
.wrap{width:100%; max-width:480px; display:flex; flex-direction:column; gap:8px; flex:1}
.top{display:flex; align-items:center; justify-content:space-between; gap:8px; padding:2px 4px}
.top .group-name{
  font:800 13px var(--font-display); letter-spacing:.04em; text-transform:uppercase;
  color:var(--accent); display:flex; align-items:center; gap:7px;
}
.top .group-name .gdot{width:7px; height:7px; border-radius:50%; background:var(--accent); box-shadow:var(--glow)}
.top .jam-id{font:600 10.5px var(--font-mono); color:var(--text-muted); letter-spacing:.06em; white-space:nowrap}
.card{
  background:color-mix(in srgb, var(--surface) 84%, transparent);
  backdrop-filter:blur(10px); -webkit-backdrop-filter:blur(10px);
  border:1px solid var(--border); border-radius:var(--radius); padding:14px;
}
h1{font:800 17px var(--font-display); letter-spacing:.02em; margin-bottom:4px}
.hint{font-size:12px; color:var(--text-muted); line-height:1.5}
.meter{display:flex; align-items:center; gap:8px; margin:12px 0 10px}
.meter .chip{
  font:700 11px var(--font-mono); letter-spacing:.05em; padding:4px 10px;
  border:1px solid var(--border); border-radius:999px; color:var(--text-muted);
}
.meter .chip b{color:var(--accent)}
.grid{display:grid; grid-template-columns:1fr 1fr; gap:9px}
.code{
  position:relative; border-radius:var(--radius-sm); padding:13px 8px 11px;
  text-align:center; cursor:pointer; user-select:none;
  font:800 19px var(--font-mono); letter-spacing:.14em;
  background:color-mix(in srgb, var(--surface-2) 80%, transparent);
  border:1.5px solid color-mix(in srgb, var(--accent) 45%, var(--border));
  color:var(--text); transition:transform .12s, border-color .15s;
}
.code:active{transform:scale(.96)}
.code .st{display:block; margin-top:5px; font:700 9.5px var(--font-body);
  letter-spacing:.12em; color:var(--accent)}
.code.used{
  cursor:default; border-color:var(--border); color:var(--text-muted);
  background:color-mix(in srgb, var(--surface) 55%, transparent); opacity:.62;
}
.code.used .cv{text-decoration:line-through; text-decoration-thickness:2px}
.code.used .st{color:var(--text-muted)}
.empty{padding:18px 8px; text-align:center; color:var(--text-muted); font-size:12.5px}
.gobtn{
  display:block; width:100%; margin-top:10px; padding:13px; border:none; cursor:pointer;
  border-radius:var(--radius-sm); font:800 14px var(--font-display); letter-spacing:.03em;
  background:linear-gradient(135deg, var(--accent), var(--accent-2)); color:var(--accent-ink);
  box-shadow:var(--glow); text-align:center; text-decoration:none;
}
.toast{
  position:fixed; top:calc(10px + env(safe-area-inset-top)); left:50%; z-index:50;
  transform:translate(-50%,-130%); opacity:0; visibility:hidden;
  transition:transform .28s cubic-bezier(.3,1.2,.4,1), opacity .25s, visibility .25s;
  width:calc(100% - 24px); max-width:456px;
  background:color-mix(in srgb, var(--surface) 94%, transparent);
  backdrop-filter:blur(12px); -webkit-backdrop-filter:blur(12px);
  border:1px solid color-mix(in srgb, var(--accent) 40%, var(--border));
  border-radius:var(--radius-sm); padding:11px 14px; font:600 12.5px var(--font-body);
}
.toast.show{transform:translate(-50%,0); opacity:1; visibility:visible}
</style></head><body>
<div class="toast" id="toast"></div>
<div class="wrap">
  <div class="top">
    <span class="group-name"><span class="gdot"></span>__LABEL__ · KODLAR</span>
    <span class="jam-id">__JAM__</span>
  </div>
  <div class="card">
    <h1>Erişim Kodları</h1>
    <p class="hint">Boş bir koda dokun → kopyalanır → oylama sayfasındaki kapıda kullan.
    Kullanılan kod bu panoda <b>herkes için anında</b> kapanır; başkasının kodunu deneme.</p>
    <div class="meter">
      <span class="chip" id="meter">— / —</span>
      <span class="chip" id="freeChip"><b>—</b>&nbsp;boş</span>
    </div>
    <div class="grid" id="grid"><div class="empty">Yükleniyor…</div></div>
    <a class="gobtn" id="goVote" href="#">🗳️ Oylamaya Git</a>
  </div>
</div>
<script>
var TOKEN=location.pathname.split('/k/')[1]||'';
document.getElementById('goVote').href='/v/'+TOKEN;
var lastSig='';
function toastMsg(m){
  var el=document.getElementById('toast'); el.textContent=m; el.classList.add('show');
  clearTimeout(el._t); el._t=setTimeout(function(){el.classList.remove('show');},1800);
}
function copyCode(code){
  // LAN http bağlamında navigator.clipboard çoğu mobil tarayıcıda YOK → execCommand fallback
  function done(){ toastMsg('Kod kopyalandı: '+code); }
  if(navigator.clipboard && window.isSecureContext){
    navigator.clipboard.writeText(code).then(done).catch(function(){fallback();});
  } else fallback();
  function fallback(){
    var ta=document.createElement('textarea'); ta.value=code;
    ta.style.position='fixed'; ta.style.opacity='0';
    document.body.appendChild(ta); ta.focus(); ta.select();
    try{ document.execCommand('copy'); done(); }catch(e){ toastMsg('Kod: '+code); }
    document.body.removeChild(ta);
  }
}
function render(data){
  var grid=document.getElementById('grid');
  if(data.access!=='codes'){
    grid.innerHTML='<div class="empty">Bu grup şu an kod kullanmıyor.</div>';
    document.getElementById('meter').textContent='—';
    document.getElementById('freeChip').innerHTML='';
    return;
  }
  var codes=data.codes||[], used=0;
  var h='';
  for(var i=0;i<codes.length;i++){
    var c=codes[i];
    if(c.claimed) used++;
    h+= c.claimed
      ? '<div class="code used"><span class="cv">'+c.code+'</span><span class="st">KULLANILDI</span></div>'
      : '<div class="code" data-code="'+c.code+'"><span class="cv">'+c.code+'</span><span class="st">DOKUN = KOPYALA</span></div>';
  }
  grid.innerHTML=h||'<div class="empty">Kod yok — yöneticiden isteyin.</div>';
  document.getElementById('meter').innerHTML='<b>'+used+'</b> / '+codes.length+' kullanıldı';
  document.getElementById('freeChip').innerHTML='<b>'+(codes.length-used)+'</b>&nbsp;boş';
  var free=grid.querySelectorAll('.code[data-code]');
  for(var j=0;j<free.length;j++){
    (function(el){ el.addEventListener('click',function(){copyCode(el.getAttribute('data-code'));}); })(free[j]);
  }
}
function poll(){
  fetch('/api/codes?t='+encodeURIComponent(TOKEN),{cache:'no-store'})
    .then(function(r){return r.json();})
    .then(function(d){
      if(!d.ok) return;
      var sig=JSON.stringify([d.access,d.codes]);
      if(sig!==lastSig){ lastSig=sig; render(d); }
    }).catch(function(){});
}
poll(); setInterval(poll,2500);
</script></body></html>"""
