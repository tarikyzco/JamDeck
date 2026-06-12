/* ============================================================
   JamDeck — SETUP / CUSTOMIZE  (split: controls | live preview)
   Exposes window.renderSetup / wireSetup / mountSetup / refreshSetupText
   ============================================================ */
(function(){
  const PRESET_ORDER = ["frostbite","ember","synthwave","forest","royal","mono","daylight","paper"];

  function swatchCard(key){
    const p = THEME_PRESETS[key];
    const c = p.colors;
    return `<button class="preset-card ${CONFIG.theme.preset===key?"sel":""}" data-preset="${key}">
      <span class="pc-prev" style="background:linear-gradient(135deg,${c.bg},${c.bg2})">
        <span class="pc-dot" style="background:${c.accent}"></span>
        <span class="pc-dot" style="background:${c.accent2}"></span>
        <span class="pc-bar" style="background:${c.surface};border:1px solid ${c.border}"></span>
      </span>
      <span class="pc-label">${p.label}</span>
      ${p.mode==="light"?'<span class="pc-mode">LIGHT</span>':''}
    </button>`;
  }

  function effectCard(key){
    const lbl = EFFECT_LABELS[key] ? EFFECT_LABELS[key][LANG]||EFFECT_LABELS[key].en : key;
    return `<button class="fx-card ${CONFIG.effect.name===key?"sel":""}" data-fx="${key}">
      <canvas class="fx-thumb" data-fxname="${key}" width="120" height="68"></canvas>
      <span class="fx-label">${lbl}</span>
    </button>`;
  }

  function colorRow(field,labelKey,val){
    return `<div class="color-field" data-color-row>
      <label class="color-swatch"><input type="color" value="${val}" data-col="${field}"><span style="position:absolute;inset:0;background:${val}" data-col-fill="${field}"></span></label>
      <div style="display:flex;flex-direction:column;gap:1px">
        <span class="color-name" data-t="${labelKey}">${t(labelKey)}</span>
        <span class="color-hex" data-col-hex="${field}">${val}</span>
      </div>
    </div>`;
  }

  window.renderSetup = function(){
    const cfg=CONFIG, c=cfg.theme.colors;
    return `<section class="screen" id="screen-setup" data-screen-label="Setup">
      <div class="setup-grid">
        <div class="setup-controls">
          <div class="page-head">
            <h1 class="page-title" data-t="setup_title">${t("setup_title")}</h1>
            <p class="page-sub" data-t="setup_sub">${t("setup_sub")}</p>
          </div>

          <!-- Identity -->
          <div class="acc-sec open">
            <button class="acc-head">${icon("id")}<span data-t="sec_identity">${t("sec_identity")}</span>${icon("chevron")}</button>
            <div class="acc-body">
              <div class="field"><label class="field-label" data-t="jam_name">${t("jam_name")}</label>
                <input class="input" id="suName" value="${cfg.jam.name}"></div>
              <div class="field"><label class="field-label" data-t="jam_tagline">${t("jam_tagline")}</label>
                <input class="input" id="suTag" value="${cfg.jam.tagline}"></div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
                <div><label class="field-label" style="display:block;margin-bottom:7px" data-t="logo_upload">${t("logo_upload")}</label>
                  <div class="dropzone" id="dzLogo">${cfg.jam.logo?`<img class="dz-thumb" src="${cfg.jam.logo}">`:icon("upload")}
                    <span class="dz-title" data-t="choose_file">${t("choose_file")}</span>
                    <span class="dz-sub" data-t="logo_hint">${t("logo_hint")}</span></div></div>
                <div><label class="field-label" style="display:block;margin-bottom:7px" data-t="bg_upload">${t("bg_upload")}</label>
                  <div class="dropzone" id="dzBg">${cfg.jam.background?`<img class="dz-thumb" src="${cfg.jam.background}">`:icon("upload")}
                    <span class="dz-title" data-t="choose_file">${t("choose_file")}</span>
                    <span class="dz-sub" data-t="bg_hint">${t("bg_hint")}</span></div></div>
              </div>
            </div>
          </div>

          <!-- Theme -->
          <div class="acc-sec open">
            <button class="acc-head">${icon("palette")}<span data-t="sec_theme">${t("sec_theme")}</span>${icon("chevron")}</button>
            <div class="acc-body">
              <label class="field-label" style="display:block;margin-bottom:10px" data-t="theme_presets">${t("theme_presets")}</label>
              <div class="preset-grid" id="presetGrid">${PRESET_ORDER.map(swatchCard).join("")}</div>
              <label class="field-label" style="display:block;margin:18px 0 10px" data-t="customize">${t("customize")}</label>
              <div class="color-grid" id="colorGrid">
                ${colorRow("accent","col_accent",c.accent)}
                ${colorRow("accent2","col_accent2",c.accent2)}
                ${colorRow("bg","col_bg",c.bg)}
                ${colorRow("surface","col_surface",c.surface)}
                ${colorRow("text","col_text",c.text)}
              </div>
              <div style="margin-top:16px">
                <label class="field-label" style="display:flex;justify-content:space-between"><span data-t="radius">${t("radius")}</span></label>
                <div class="slider-row"><input type="range" class="range" id="suRadius" min="0" max="28" value="${cfg.theme.radius}">
                  <span class="slider-val" id="suRadiusVal">${cfg.theme.radius}px</span></div>
              </div>
              <div style="margin-top:10px">
                <label class="field-label" data-t="glow">${t("glow")}</label>
                <div class="slider-row"><input type="range" class="range" id="suGlow" min="0" max="2" step="0.1" value="${cfg.theme.glow}">
                  <span class="slider-val" id="suGlowVal">${cfg.theme.glow.toFixed(1)}×</span></div>
              </div>
            </div>
          </div>

          <!-- Effect -->
          <div class="acc-sec open">
            <button class="acc-head">${icon("sparkles")}<span data-t="sec_effect">${t("sec_effect")}</span>${icon("chevron")}</button>
            <div class="acc-body">
              <div class="toggle-row"><div class="tr-text"><span class="tr-title" data-t="effect_enabled">${t("effect_enabled")}</span></div>
                <div class="toggle ${cfg.effect.enabled?"on":""}" id="suFxOn"></div></div>
              <div class="fx-grid" id="fxGrid">${EFFECT_KEYS.map(effectCard).join("")}</div>
              <div style="margin-top:14px"><label class="field-label" data-t="effect_intensity">${t("effect_intensity")}</label>
                <div class="slider-row"><input type="range" class="range" id="suFxInt" min="20" max="400" value="${cfg.effect.intensity}">
                  <span class="slider-val" id="suFxIntVal">${cfg.effect.intensity}</span></div></div>
            </div>
          </div>

          <!-- Language -->
          <div class="acc-sec">
            <button class="acc-head">${icon("globe")}<span data-t="sec_language">${t("sec_language")}</span>${icon("chevron")}</button>
            <div class="acc-body">
              <div class="segmented" id="suLang">
                <button data-lang="tr" class="${LANG==="tr"?"on":""}">Türkçe</button>
                <button data-lang="en" class="${LANG==="en"?"on":""}">English</button>
              </div>
            </div>
          </div>

          <!-- Behavior -->
          <div class="acc-sec">
            <button class="acc-head">${icon("clock")}<span data-t="sec_behavior">${t("sec_behavior")}</span>${icon("chevron")}</button>
            <div class="acc-body">
              <div class="field"><label class="field-label" data-t="default_minutes">${t("default_minutes")}</label>
                <input class="input" id="suMin" type="number" min="1" max="60" value="${cfg.launcher.defaultMinutes}"></div>
              <div class="field"><label class="field-label" data-t="on_timeup">${t("on_timeup")}</label>
                <div class="segmented" id="suTimeup">
                  <button data-tu="kill" class="${cfg.launcher.onTimeUp==="kill"?"on":""}" data-t="timeup_kill">${t("timeup_kill")}</button>
                  <button data-tu="warn" class="${cfg.launcher.onTimeUp==="warn"?"on":""}" data-t="timeup_warn">${t("timeup_warn")}</button>
                  <button data-tu="return" class="${cfg.launcher.onTimeUp==="return"?"on":""}" data-t="timeup_return">${t("timeup_return")}</button>
                </div></div>
              <div class="field"><label class="field-label" data-t="kill_delay">${t("kill_delay")}</label>
                <input class="input" id="suKill" type="number" min="0" max="30" value="${cfg.launcher.killDelay}"></div>
              <div class="toggle-row"><div class="tr-text"><span class="tr-title" data-t="kiosk_lock">${t("kiosk_lock")}</span><span class="tr-sub" data-t="kiosk_lock_sub">${t("kiosk_lock_sub")}</span></div>
                <div class="toggle ${cfg.launcher.kioskLock?"on":""}" id="suKiosk"></div></div>
              <div class="toggle-row"><div class="tr-text"><span class="tr-title" data-t="show_timer">${t("show_timer")}</span></div>
                <div class="toggle ${cfg.launcher.timerOverlay?"on":""}" id="suTimer"></div></div>
            </div>
          </div>

          <!-- Folders -->
          <div class="acc-sec">
            <button class="acc-head">${icon("folder")}<span data-t="sec_folders">${t("sec_folders")}</span>${icon("chevron")}</button>
            <div class="acc-body">
              <label class="field-label" style="display:block;margin-bottom:7px" data-t="games_dir">${t("games_dir")}</label>
              <div style="display:flex;gap:10px;flex-wrap:wrap">
                <div class="input-readonly"><span id="suDir">${cfg.paths.gamesDir}</span></div>
                <button class="btn btn-secondary btn-sm" id="suChangeDir">${icon("folder")}<span data-t="change">${t("change")}</span></button>
                <button class="btn btn-ghost btn-sm" id="suOpenDir"><span data-t="open_folder">${t("open_folder")}</span></button>
              </div>
            </div>
          </div>

          <div class="setup-bar">
            <button class="btn btn-primary" id="suSave">${icon("save")}<span data-t="save">${t("save")}</span></button>
            <button class="btn btn-ghost" id="suReset">${icon("rotate")}<span data-t="reset_defaults">${t("reset_defaults")}</span></button>
            <div style="flex:1"></div>
            <button class="btn btn-ghost btn-sm" id="suExport">${icon("export")}<span data-t="export_config">${t("export_config")}</span></button>
            <button class="btn btn-ghost btn-sm" id="suImport">${icon("import")}<span data-t="import_config">${t("import_config")}</span></button>
          </div>
        </div>

        <!-- LIVE PREVIEW -->
        <div class="setup-preview">
          <div class="prev-label">${icon("expand")}<span data-t="live_preview">${t("live_preview")}</span></div>
          <div class="prev-frame" id="prevFrame">
            <canvas class="prev-canvas" id="prevCanvas"></canvas>
            <div class="prev-ui">
              <div class="prev-side">
                <div class="prev-brand"><span class="prev-logo" id="prevLogo">A</span><span class="prev-bname" id="prevName">${cfg.jam.name}</span></div>
                <div class="prev-nav"><span class="on"></span><span></span><span></span></div>
              </div>
              <div class="prev-main">
                <div class="prev-hero">
                  <div class="prev-art"></div>
                  <div class="prev-htext">
                    <span class="prev-team">Pixel Studio</span>
                    <span class="prev-gname" id="prevGame">Neon Ascent</span>
                    <span class="prev-play">${icon("play")} ${t("play")}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>`;
  };

  let prevCtl=null;
  let thumbCtls=[];

  window.mountSetup=function(){
    // preview effect
    const pc=$("#prevCanvas");
    if(pc && !prevCtl){ prevCtl=makeEffectController(pc); }
    if(prevCtl){ prevCtl.setEffect(CONFIG.effect.name, Math.round(CONFIG.effect.intensity*0.4),1); prevCtl.setEnabled(CONFIG.effect.enabled); }
    startThumbs();
    syncPreview();
  };

  function startThumbs(){
    thumbCtls.forEach(c=>c.stop&&c.stop());
    thumbCtls=[];
    $$(".fx-thumb").forEach(cv=>{
      const ctl=makeEffectController(cv);
      ctl.setEffect(cv.dataset.fxname, 26, 1.4);
      ctl.setEnabled(true);
      thumbCtls.push(ctl);
    });
  }

  function syncPreview(){
    const c=CONFIG.theme.colors, j=CONFIG.jam;
    $("#prevName").textContent=j.name;
    $("#prevLogo").textContent=(j.name||"J")[0].toUpperCase();
    if(j.logo){ const l=$("#prevLogo"); l.style.backgroundImage=`url('${j.logo}')`; l.style.backgroundSize="cover"; l.textContent=""; }
  }

  // ---- live update helpers ----
  function liveTheme(){
    applyTheme({colors:CONFIG.theme.colors, radius:CONFIG.theme.radius, glow:CONFIG.theme.glow,
      mode: modeForBg(CONFIG.theme.colors.bg)});
  }

  window.wireSetup=function(){
    const root=$("#screen-setup"); if(!root) return;

    // accordions
    $$(".acc-head",root).forEach(h=>h.onclick=()=>h.parentElement.classList.toggle("open"));

    // identity
    $("#suName",root).oninput=e=>{ CONFIG.jam.name=e.target.value; $("#prevName").textContent=e.target.value;
      $$("[data-t-text='jamname']").forEach(n=>n.textContent=e.target.value); $("#prevLogo").textContent=(e.target.value||"J")[0].toUpperCase(); };
    $("#suTag",root).oninput=e=>{ CONFIG.jam.tagline=e.target.value; };
    $("#dzLogo",root).onclick=()=>Bridge.pickImage("logo").then(r=>{ CONFIG.jam.logo=r.dataUrl;
      $("#dzLogo").innerHTML=`<img class="dz-thumb" src="${r.dataUrl}"><span class="dz-title">${t("choose_file")}</span>`; syncPreview();
      $(".brand-logo").innerHTML=`<img src="${r.dataUrl}" alt="">`; });
    $("#dzBg",root).onclick=()=>Bridge.pickImage("background").then(r=>{ CONFIG.jam.background=r.dataUrl;
      $("#dzBg").innerHTML=`<img class="dz-thumb" src="${r.dataUrl}"><span class="dz-title">${t("choose_file")}</span>`; });

    // presets
    $$("[data-preset]",root).forEach(b=>b.onclick=()=>{
      const key=b.dataset.preset; CONFIG.theme=themeFromPreset(key,CONFIG.theme);
      $$("[data-preset]",root).forEach(x=>x.classList.toggle("sel",x===b));
      liveTheme(); refreshColorInputs();
    });

    // color pickers
    $$("[data-col]",root).forEach(inp=>inp.oninput=e=>{
      const f=e.target.dataset.col; CONFIG.theme.colors[f]=e.target.value; CONFIG.theme.preset="custom";
      // surface2/border derive lightly from surface; bg2 from bg
      if(f==="surface") CONFIG.theme.colors.surface2=e.target.value;
      $(`[data-col-fill="${f}"]`).style.background=e.target.value;
      $(`[data-col-hex="${f}"]`).textContent=e.target.value;
      $$("[data-preset]",root).forEach(x=>x.classList.remove("sel"));
      liveTheme();
    });

    // radius / glow
    const rad=$("#suRadius",root); rad.oninput=e=>{ CONFIG.theme.radius=+e.target.value; $("#suRadiusVal").textContent=e.target.value+"px";
      setRangeFill(rad); liveTheme(); };
    const glow=$("#suGlow",root); glow.oninput=e=>{ CONFIG.theme.glow=+e.target.value; $("#suGlowVal").textContent=(+e.target.value).toFixed(1)+"×";
      setRangeFill(glow); liveTheme(); };

    // effect
    $("#suFxOn",root).onclick=e=>{ const on=!e.currentTarget.classList.contains("on"); e.currentTarget.classList.toggle("on",on);
      CONFIG.effect.enabled=on; if(prevCtl)prevCtl.setEnabled(on); if(effectCtl)effectCtl.setEnabled(on); };
    $$("[data-fx]",root).forEach(b=>b.onclick=()=>{ const k=b.dataset.fx; CONFIG.effect.name=k;
      $$("[data-fx]",root).forEach(x=>x.classList.toggle("sel",x===b));
      if(prevCtl)prevCtl.setEffect(k,Math.round(CONFIG.effect.intensity*0.4),1);
      if(effectCtl)effectCtl.setEffect(k,CONFIG.effect.intensity,1); });
    const fxi=$("#suFxInt",root); fxi.oninput=e=>{ CONFIG.effect.intensity=+e.target.value; $("#suFxIntVal").textContent=e.target.value;
      setRangeFill(fxi); if(prevCtl)prevCtl.setIntensity(Math.round(+e.target.value*0.4)); if(effectCtl)effectCtl.setIntensity(+e.target.value); };

    // language
    $$("#suLang button",root).forEach(b=>b.onclick=()=>{ setLanguage(b.dataset.lang); CONFIG.jam.language=LANG;
      $$("#suLang button",root).forEach(x=>x.classList.toggle("on",x===b)); });

    // behavior
    $("#suMin",root).oninput=e=>CONFIG.launcher.defaultMinutes=+e.target.value;
    $$("#suTimeup button",root).forEach(b=>b.onclick=()=>{ CONFIG.launcher.onTimeUp=b.dataset.tu;
      $$("#suTimeup button",root).forEach(x=>x.classList.toggle("on",x===b)); });
    $("#suKill",root).oninput=e=>CONFIG.launcher.killDelay=+e.target.value;
    $("#suKiosk",root).onclick=e=>{ const on=!e.currentTarget.classList.contains("on"); e.currentTarget.classList.toggle("on",on); CONFIG.launcher.kioskLock=on; };
    $("#suTimer",root).onclick=e=>{ const on=!e.currentTarget.classList.contains("on"); e.currentTarget.classList.toggle("on",on); CONFIG.launcher.timerOverlay=on; };

    // folders
    $("#suChangeDir",root).onclick=()=>Bridge.selectGamesFolder().then(r=>{ CONFIG.paths.gamesDir=r.path; $("#suDir").textContent=r.path; });
    $("#suOpenDir",root).onclick=()=>Bridge.openGamesFolder();

    // save bar
    $("#suSave",root).onclick=()=>Bridge.saveConfig(CONFIG).then(()=>toast(t("saved_ok"),"success"));
    $("#suReset",root).onclick=()=>modal({title:t("reset_q"),body:t("reset_sub"),danger:true,onConfirm:()=>
      Bridge.resetConfig().then(c=>{ CONFIG=c; LANG=c.jam.language; applyConfig(CONFIG); applyEffectFromConfig();
        rebuildSetup(); toast(t("reset_ok"),"info"); })});
    $("#suExport",root).onclick=()=>Bridge.exportConfig().then(()=>toast(t("exported_ok"),"info"));
    $("#suImport",root).onclick=()=>Bridge.importConfig().then(()=>toast(t("saved_ok"),"info"));

    // init range fills
    [rad,glow,fxi].forEach(setRangeFill);
  };

  function rebuildSetup(){
    const main=$("#main");
    const old=$("#screen-setup"); if(old) old.remove();
    main.insertAdjacentHTML("beforeend", window.renderSetup());
    window.wireSetup(); window.__rerenderText();
    navigate("setup");
  }

  function refreshColorInputs(){
    const c=CONFIG.theme.colors;
    [["accent",c.accent],["accent2",c.accent2],["bg",c.bg],["surface",c.surface],["text",c.text]].forEach(([f,v])=>{
      const inp=$(`[data-col="${f}"]`); if(inp)inp.value=v;
      const fill=$(`[data-col-fill="${f}"]`); if(fill)fill.style.background=v;
      const hex=$(`[data-col-hex="${f}"]`); if(hex)hex.textContent=v;
    });
    const rad=$("#suRadius"); if(rad){rad.value=CONFIG.theme.radius; $("#suRadiusVal").textContent=CONFIG.theme.radius+"px"; setRangeFill(rad);}
    const glow=$("#suGlow"); if(glow){glow.value=CONFIG.theme.glow; $("#suGlowVal").textContent=CONFIG.theme.glow.toFixed(1)+"×"; setRangeFill(glow);}
  }

  function setRangeFill(r){ if(!r)return; const min=+r.min,max=+r.max,v=+r.value; r.style.setProperty("--fill",((v-min)/(max-min)*100)+"%"); }

  window.refreshSetupText=function(){
    // re-label effect cards + restart thumbs on lang change
    $$(".fx-card").forEach(card=>{ const k=card.dataset.fx; const lbl=card.querySelector(".fx-label");
      if(lbl&&EFFECT_LABELS[k]) lbl.textContent=EFFECT_LABELS[k][LANG]||EFFECT_LABELS[k].en; });
  };
})();
