import { chromium } from 'playwright';
import { execSync } from 'child_process';
import { fileURLToPath } from 'url';
import http from 'http';
import path from 'path';
import fs from 'fs';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, '..');
const htmlPath = path.join(__dirname, '_cd.html');

// countdown_page.py içindeki PAGE'i al
execSync(`python -c "from backend.countdown_page import PAGE; open(r'${htmlPath}','w',encoding='utf-8').write(PAGE)"`, { cwd: root });
const HTML = fs.readFileSync(htmlPath, 'utf-8');
fs.unlinkSync(htmlPath);

const CFG = {
  countdown: { startAt: new Date(Date.now() + 3600e3).toISOString(), durationHours: 48, style: "neon" },
  jam: { name: "Demo", logo: null, language: "tr" },
  theme: { colors: { bg:"#050a14", bg2:"#080e1c", surface:"#0f1629", surface2:"#141d33", border:"#1e293b", accent:"#00f2ff", accent2:"#0062ff", text:"#ffffff", textMuted:"#94a3b8", error:"#ff1744" } },
  effect: { name: "confetti", intensity: 120, enabled: true },
  cdtext: { pre:"BAŞLAMASINA", main:"KALAN SÜRE", done:"SÜRE DOLDU", empty:"" }
};

// gerçek HTTP sunucusu (file:// fetch kısıtını aşar)
const server = http.createServer((req, res) => {
  const p = req.url.split('?')[0];
  if (p === '/config.json') { res.writeHead(200, {'Content-Type':'application/json'}); res.end(JSON.stringify(CFG)); }
  else { res.writeHead(200, {'Content-Type':'text/html; charset=utf-8'}); res.end(HTML); }
});
await new Promise(r => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}`;

const log = [];
const step = (n, ok, x='') => log.push(`${ok ? 'PASS' : 'FAIL'}  ${n}${x ? ' — ' + x : ''}`);
const browser = await chromium.launch();
const errors = [];

async function openPage(transparent){
  const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));
  await page.goto(base + (transparent ? '/?transparent=1' : '/'));
  await page.waitForTimeout(700);
  return page;
}

// ── normal mod ──
let page = await openPage(false);
const fx = await page.$eval('#fx', el => ({ cw: el.clientWidth, bw: el.width, disp: getComputedStyle(el).display }));
step('effect canvas sized by controller (width set)', fx.cw > 0 && fx.bw > 800 && fx.disp !== 'none', JSON.stringify(fx));
const digitsTxt = await page.$eval('#digits', el => el.textContent.replace(/\s/g,''));
step('digits show a countdown value', /\d\d:\d\d:\d\d/.test(digitsTxt), digitsTxt);
const fpx = await page.$eval('#digits', el => parseFloat(getComputedStyle(el).fontSize));
step('digits FILL width (grew past old ~182px cap on 1400w)', fpx > 230, `fontSize=${Math.round(fpx)}px`);
const digitsW = await page.$eval('#digits', el => el.scrollWidth);
step('digits span most of the screen width', digitsW > 1400 * 0.8, `w=${digitsW}`);
await page.close();

// ── şeffaf (OBS overlay) mod: efekt kapalı ──
page = await openPage(true);
const fxT = await page.$eval('#fx', el => getComputedStyle(el).display);
step('transparent mode hides effect canvas', fxT === 'none', `display=${fxT}`);
await page.close();

await browser.close();
server.close();

console.log('\n' + log.join('\n'));
console.log('\nConsole errors: ' + (errors.length ? '\n  ' + errors.join('\n  ') : 'none'));
const failed = log.filter(l => l.startsWith('FAIL')).length;
console.log(`\n${failed || errors.length ? 'FAILED ' + (failed+errors.length) : 'ALL PASSED'} (${log.length} checks)`);
process.exit(failed || errors.length ? 1 : 0);
