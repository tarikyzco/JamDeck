import { chromium } from 'playwright';
import { pathToFileURL, fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const htmlPath = path.resolve(__dirname, '../frontend/index.html');
const url = pathToFileURL(htmlPath).href;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });

const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));

await page.goto(url);
await page.waitForTimeout(1500); // pywebview-detection timeout + init

const log = [];
function step(name, ok, extra='') { log.push(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`); }

// 1. shell rendered
step('shell renders (sidebar present)', !!(await page.$('.sidebar')));
step('default logo placeholder', ((await page.$eval('.logo-ph', el => el.textContent).catch(()=>''))).includes('GAME JAM'));

// 2. navigate to setup
await page.evaluate(() => navigate('setup'));
await page.waitForTimeout(500);
step('setup screen activates', await page.$eval('#screen-setup', el => el.classList.contains('active')).catch(()=>false));

// 3. theme preset gallery: 16 cards with previews (8 orijinal + 8 yeni palet)
const themeCards = await page.$$('.theme-card');
step('16 theme preset cards', themeCards.length === 16, `count=${themeCards.length}`);

// 4. fx gallery: 14 canvas thumbnails, sized (live previews)
const fxThumbs = await page.$$('.fx-thumb');
step('14 effect thumbnails present', fxThumbs.length === 14, `count=${fxThumbs.length}`);
const thumbSize = fxThumbs.length ? await fxThumbs[1].evaluate(c => ({w:c.width,h:c.height})) : {w:0,h:0};
step('effect thumbnail canvas sized', thumbSize.w > 0 && thumbSize.h > 0, JSON.stringify(thumbSize));

// 5. change jam name -> sidebar brand updates live
await page.fill('#suName', 'NeonJam 2027');
await page.waitForTimeout(150);
const brandName = await page.$eval('.sidebar .jam-name', el => el.textContent).catch(()=>'');
step('jam name updates sidebar brand', brandName === 'NeonJam 2027', `brand="${brandName}"`);

// 6. pick a preset -> accent + accent-ink vars change
const accentBefore = await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--accent').trim());
await page.click('[data-preset="synthwave"]');
await page.waitForTimeout(200);
const accentAfter = await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--accent').trim());
step('preset switch changes --accent', accentBefore !== accentAfter, `${accentBefore} -> ${accentAfter}`);
const ink = await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--accent-ink').trim());
step('--accent-ink applied', ink.length > 0, ink);

// 7. custom color: change bg -> bg AND bg2 derive, preset=custom
await page.evaluate(()=>{
  const inp=document.querySelector('[data-col="bg"]'); inp.value='#220011'; inp.dispatchEvent(new Event('input',{bubbles:true}));
});
await page.waitForTimeout(150);
const cfgColors = await page.evaluate(()=>({bg:CONFIG.theme.colors.bg, bg2:CONFIG.theme.colors.bg2, preset:CONFIG.theme.preset}));
step('custom bg sets bg + bg2 + preset=custom', cfgColors.bg==='#220011' && cfgColors.bg2==='#220011' && cfgColors.preset==='custom', JSON.stringify(cfgColors));

// 8. radius + glow sliders update CSS vars
await page.evaluate(()=>{ const r=document.querySelector('#suRadius'); r.value=8; r.dispatchEvent(new Event('input',{bubbles:true})); });
await page.waitForTimeout(120);
const radiusVar = await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--radius').trim());
step('radius slider updates --radius', radiusVar === '8px', radiusVar);
await page.evaluate(()=>{ const g=document.querySelector('#suGlow'); g.value=2; g.dispatchEvent(new Event('input',{bubbles:true})); });
await page.waitForTimeout(120);
const glowVar = await page.evaluate(()=>getComputedStyle(document.documentElement).getPropertyValue('--glow-a').trim());
step('glow slider updates --glow-a', glowVar === '60%', glowVar);

// 9. language switch TR/EN
await page.click('#suLang button[data-lang="en"]').catch(()=>{});
await page.waitForTimeout(250);
const saveLabel = await page.$eval('#suSave [data-t="save"]', el=>el.textContent).catch(()=>'');
step('language switch to EN works', saveLabel==='Save', `saveLabel="${saveLabel}"`);

// 10. export triggers a download (mock path -> blob)
let downloadHappened = false;
page.on('download', () => { downloadHappened = true; });
await page.click('#suExport').catch(()=>{});
await page.waitForTimeout(400);
step('export triggers file download', downloadHappened);

// 11. reset flow -> modal confirm -> setup rebuilt, thumbs alive
await page.click('#suReset').catch(()=>{});
await page.waitForTimeout(250);
await page.click('.modal-backdrop.show [data-ok]').catch(()=>{});
await page.waitForTimeout(700);
const thumbsAfter = await page.$$('.fx-thumb');
const thumbAfterSize = thumbsAfter.length ? await thumbsAfter[1].evaluate(c=>({w:c.width,h:c.height})) : {w:0,h:0};
step('setup rebuilt after reset (14 thumbs alive)', thumbsAfter.length === 14 && thumbAfterSize.w > 0, `count=${thumbsAfter.length} ${JSON.stringify(thumbAfterSize)}`);

await page.screenshot({ path: path.resolve(__dirname, '../scratch/setup_screenshot.png'), fullPage: false });

console.log('\n=== SETUP SCREEN TEST RESULTS ===');
console.log(log.join('\n'));
console.log('\n=== CONSOLE ERRORS (' + errors.length + ') ===');
console.log(errors.length ? errors.join('\n') : '(none)');

await browser.close();
const failed = log.filter(l=>l.startsWith('FAIL')).length;
process.exit(failed + errors.length > 0 ? 1 : 0);
