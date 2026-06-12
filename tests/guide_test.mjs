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
const step = (name, ok, extra='') => log.push(`${ok ? 'PASS' : 'FAIL'}  ${name}${extra ? ' — ' + extra : ''}`);

// 1. nav item present
const navGuide = await page.$('.nav-item[data-nav="guide"]');
step('sidebar has Guide nav item', !!navGuide);

// 2. navigate to guide
await page.evaluate(() => navigate('guide'));
await page.waitForTimeout(400);
const active = await page.$eval('#screen-guide', el => el.classList.contains('active')).catch(()=>false);
step('guide screen activates', active);

// 3. öz içerik: ana mesaj Windows + Web build
const mainMsg = await page.$eval('#guideMain', el => el.textContent).catch(()=>'');
step('main message = Windows VEYA Web build', /WINDOWS/.test(mainMsg) && /veya/.test(mainMsg) && /WEB/.test(mainMsg), `"${mainMsg.slice(0,60)}…"`);
step('no legacy name.txt / zip-tree content', !/name\.txt/i.test(await page.content()));
const tiles = await page.$$('.build-tile');
step('2 build tiles rendered', tiles.length === 2, `count=${tiles.length}`);
const tips = await page.$$('.guide-tips .tip');
step('3 tip cards rendered', tips.length === 3, `count=${tips.length}`);

// 4. paylaşılabilir poster önizleme
step('poster preview present', !!(await page.$('.poster')));
step('poster shows EXE veya WEB', /\.EXE veya WEB/.test(await page.$eval('.poster h3', el => el.textContent).catch(()=>'')));

// 5. poster builder returns SVG
const posterOk = await page.evaluate(() => {
  const s = buildGuidePoster();
  return typeof s === 'string' && s.startsWith('<svg') && s.includes('</svg>');
});
step('buildGuidePoster() returns SVG', posterOk);

// 6. SVG -> PNG renders in canvas (the real export path, headless Chromium)
const pngOk = await page.evaluate(async () => {
  const png = await svgToPng(buildGuidePoster(), 1080, 1920);
  return typeof png === 'string' && png.startsWith('data:image/png;base64,') && png.length > 5000;
}).catch(e => { return 'ERR:' + e.message; });
step('svgToPng() produces PNG dataURL', pngOk === true, String(pngOk));

// 7. export button triggers a download
let dl = null;
page.on('download', d => { dl = d.suggestedFilename(); });
await page.click('#guideExport');
await page.waitForTimeout(800);
step('export triggers PNG download', !!dl, `file="${dl||''}"`);

// 8. language switch re-renders main message
const trMsg = await page.$eval('#guideMain', el => el.textContent.trim());
await page.evaluate(() => setLanguage('en'));
await page.waitForTimeout(300);
const enMsg = await page.$eval('#guideMain', el => el.textContent.trim());
step('language switch re-renders guide', trMsg !== enMsg && enMsg.length > 0, `"${trMsg.slice(0,30)}" -> "${enMsg.slice(0,30)}"`);
await page.evaluate(() => setLanguage('tr'));
await page.waitForTimeout(300);

// 9. screenshot for visual confirmation
await page.screenshot({ path: path.resolve(__dirname, '../scratch/guide_screenshot.png'), fullPage: false });

console.log('\n=== GUIDE SCREEN TEST RESULTS ===');
console.log(log.join('\n'));
console.log('\n=== CONSOLE ERRORS (' + errors.length + ') ===');
console.log(errors.length ? errors.join('\n') : '(none)');

await browser.close();
const failed = log.filter(l => l.startsWith('FAIL')).length;
process.exit(failed + errors.length > 0 ? 1 : 0);
