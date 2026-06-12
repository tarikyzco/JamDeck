/* ============================================================
   JamDeck — THEMES
   8 presets + applyTheme + applyConfig + custom override.
   ============================================================ */

const THEME_PRESETS = {
  frostbite:{
    label:"Frostbite", mode:"dark",
    colors:{ bg:"#050a14", bg2:"#080e1c", surface:"#0f1629", surface2:"#141d33", border:"#1e293b",
             accent:"#00f2ff", accent2:"#0062ff", text:"#ffffff", textMuted:"#94a3b8",
             success:"#00e676", warning:"#ffab00", error:"#ff1744" }
  },
  ember:{
    label:"Ember", mode:"dark",
    colors:{ bg:"#170a06", bg2:"#1f0d07", surface:"#2a130b", surface2:"#371a0f", border:"#4a2415",
             accent:"#ff6b35", accent2:"#ff1744", text:"#fff6f0", textMuted:"#d2a48c",
             success:"#7bd88f", warning:"#ffc14d", error:"#ff3b5c" }
  },
  synthwave:{
    label:"Synthwave", mode:"dark",
    colors:{ bg:"#0d0221", bg2:"#150435", surface:"#1c0a44", surface2:"#27105c", border:"#3a1d78",
             accent:"#ff2bd6", accent2:"#00f0ff", text:"#fdf0ff", textMuted:"#b794d6",
             success:"#3dffb0", warning:"#ffd23f", error:"#ff3d7f" }
  },
  forest:{
    label:"Forest", mode:"dark",
    colors:{ bg:"#0a140d", bg2:"#0d1c13", surface:"#11271a", surface2:"#163322", border:"#1f4631",
             accent:"#00e676", accent2:"#2dd4bf", text:"#f0fff6", textMuted:"#8db9a0",
             success:"#5cffac", warning:"#e6c34d", error:"#ff5c72" }
  },
  royal:{
    label:"Royal", mode:"dark",
    colors:{ bg:"#0a0a1f", bg2:"#0f0f2e", surface:"#16163f", surface2:"#1f1f54", border:"#2e2e6e",
             accent:"#a855f7", accent2:"#fbbf24", text:"#f7f4ff", textMuted:"#a89dce",
             success:"#5ce6a8", warning:"#fbbf24", error:"#ff5c8a" }
  },
  mono:{
    label:"Mono", mode:"dark",
    colors:{ bg:"#0a0a0a", bg2:"#101010", surface:"#161616", surface2:"#1e1e1e", border:"#2c2c2c",
             accent:"#f5f5f5", accent2:"#9ca3af", text:"#ffffff", textMuted:"#8a8a8a",
             success:"#cfcfcf", warning:"#bdbdbd", error:"#ff6b6b" }
  },
  daylight:{
    label:"Daylight", mode:"light",
    colors:{ bg:"#f6f7fb", bg2:"#eef0f7", surface:"#ffffff", surface2:"#f1f3fa", border:"#dde1ee",
             accent:"#4f46e5", accent2:"#0ea5e9", text:"#10131c", textMuted:"#64708a",
             success:"#16a34a", warning:"#d97706", error:"#e11d48" }
  },
  paper:{
    label:"Paper", mode:"light",
    colors:{ bg:"#faf7f0", bg2:"#f3ede1", surface:"#fffdf8", surface2:"#f5efe3", border:"#e6dcc8",
             accent:"#e2583e", accent2:"#c9942a", text:"#2a2118", textMuted:"#8a7a63",
             success:"#3f8f5b", warning:"#c9942a", error:"#cf4436" }
  }
};

const COLOR_VAR_MAP = {
  bg:"--bg", bg2:"--bg-2", surface:"--surface", surface2:"--surface-2", border:"--border",
  accent:"--accent", accent2:"--accent-2", text:"--text", textMuted:"--text-muted",
  success:"--success", warning:"--warning", error:"--error"
};

/* Apply a theme object {colors, radius, glow, mode} to :root */
function applyTheme(theme){
  const root = document.documentElement;
  const colors = theme.colors || {};
  for(const k in COLOR_VAR_MAP){
    if(colors[k]) root.style.setProperty(COLOR_VAR_MAP[k], colors[k]);
  }
  if(theme.radius != null){
    root.style.setProperty("--radius", theme.radius + "px");
    root.style.setProperty("--radius-sm", Math.max(2, Math.round(theme.radius*0.55)) + "px");
  }
  if(theme.glow != null){
    root.style.setProperty("--glow-strength", String(theme.glow));
  }
  // mode drives shadow/glow adjustments via [data-mode]
  const mode = theme.mode || (theme.preset && THEME_PRESETS[theme.preset] && THEME_PRESETS[theme.preset].mode) || "dark";
  root.setAttribute("data-mode", mode);
}

/* Merge a preset into a theme config block (preserving radius/glow) */
function themeFromPreset(presetKey, base){
  const p = THEME_PRESETS[presetKey] || THEME_PRESETS.frostbite;
  return {
    preset:presetKey,
    colors:{...p.colors},
    radius:(base && base.radius!=null)?base.radius:18,
    glow:(base && base.glow!=null)?base.glow:1.0,
    mode:p.mode
  };
}

/* Determine if a custom set of colors is light or dark (luminance of bg) */
function modeForBg(hex){
  const c = hex.replace("#","");
  const r=parseInt(c.substr(0,2),16),g=parseInt(c.substr(2,2),16),b=parseInt(c.substr(4,2),16);
  const lum=(0.2126*r+0.7152*g+0.0722*b)/255;
  return lum>0.5?"light":"dark";
}

/* Apply full config: theme + identity text + logo + background + effect */
function applyConfig(config){
  const t = {...config.theme};
  if(t.preset && t.preset!=="custom" && THEME_PRESETS[t.preset]){
    // keep stored colors if present, else fill from preset
    t.colors = t.colors && Object.keys(t.colors).length ? t.colors : {...THEME_PRESETS[t.preset].colors};
    t.mode = THEME_PRESETS[t.preset].mode;
  } else if(t.colors && t.colors.bg){
    t.mode = modeForBg(t.colors.bg);
  }
  applyTheme(t);
  // background image (if any) handled by effects/bg layer
  return t;
}
