import { chromium } from 'playwright';
import { pathToFileURL, fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const url = pathToFileURL(path.resolve(__dirname, '../frontend/index.html')).href;
const shot = (n) => path.resolve(__dirname, `_cer_${n}.png`);

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));

await page.goto(url);
await page.waitForTimeout(1200);

const log = [];
const step = (n, ok, x='') => log.push(`${ok ? 'PASS' : 'FAIL'}  ${n}${x ? ' — ' + x : ''}`);

// load mock games so results have data
await page.evaluate(() => navigate('launcher'));
await page.waitForTimeout(700);

// ── 1. Sonuç sekmesi → spoiler kapısı ──
await page.evaluate(() => navigate('results'));
await page.waitForTimeout(500);
step('gate shown on results', !!(await page.$('#resStage .res-gate')));
step('NO podium leaked behind gate', !(await page.$('#resStage .podium')));
const headHidden = await page.$eval('#resultSeg', el => el.style.display === 'none').catch(()=>null);
step('head actions hidden at gate', headHidden === true, `display=${headHidden}`);
await page.screenshot({ path: shot('1_gate') });

// ── 2. "Tümünü Göster" ──
await page.click('#rgAll');
await page.waitForTimeout(300);
step('podium appears after Show All', !!(await page.$('#resStage .podium')));
const headShown = await page.$eval('#resultSeg', el => el.style.display !== 'none').catch(()=>null);
step('head actions visible after Show All', headShown === true);

// ── 3. her girişte tekrar kapı ──
await page.evaluate(() => navigate('launcher'));
await page.waitForTimeout(200);
await page.evaluate(() => navigate('results'));
await page.waitForTimeout(400);
step('gate re-shown on every entry', !!(await page.$('#resStage .res-gate')));

// ── 4. Adım adım → derinlik seçici → Tören ──
await page.click('#rgCer');
await page.waitForTimeout(200);
step('depth selector revealed', await page.$eval('#rgDepth', el => !el.hidden).catch(()=>false));
await page.click('#rgStart');   // varsayılan Top 5
await page.waitForTimeout(400);
step('ceremony screen active', await page.$eval('#screen-ceremony', el => el.classList.contains('active')).catch(()=>false));
step('intro shown', !!(await page.$('#cerStage .cer-intro')));
step('kiosk mode on', await page.evaluate(() => document.body.classList.contains('kiosk-mode')));
await page.screenshot({ path: shot('2_intro') });

// ── 5. açılışlar (5 → 1) ──
const depth = await page.evaluate(() => CEREMONY.depth);
step('depth = 5', depth === 5, `depth=${depth}`);
for (let i = 1; i <= depth; i++) {
  await page.evaluate(() => cerNext());
  await page.waitForTimeout(550);   // > 420ms çift-tıklama kilidi
  const rank = await page.evaluate(() => CEREMONY.order[CEREMONY.pos-1]);
  const has = await page.$('#cerStage .cer-reveal');
  step(`reveal ${i} (rank ${rank}) shows card`, !!has);
  if (rank === 3) await page.screenshot({ path: shot('3_bronze') });
  // her açılışta kenar konfeti patlaması parçacık üretmeli
  const burstN = await page.evaluate(() => (cerBurst && cerBurst.parts) ? cerBurst.parts.length : 0);
  step(`reveal ${i} fires side confetti`, burstN > 0, `parts=${burstN}`);
  if (rank === 1) {
    step('1st is gold', await page.$eval('#cerStage .cer-reveal', el => el.classList.contains('r-gold')).catch(()=>false));
    await page.waitForTimeout(200);
    await page.screenshot({ path: shot('4_gold') });
  }
}
step('no persistent Next button', !(await page.$('#cerNext')));
const saVisible = await page.$eval('#cerShowAll', el => !el.hidden).catch(()=>false);
step('final → Show-All button visible', saVisible === true);
const miniCount = await page.$$eval('#cerStage .cm-row', els => els.length);
step('mini list shows 4 revealed (2..5)', miniCount === 4, `count=${miniCount}`);

// ── 6. final → Tüm Sıralamayı Göster (herhangi bir tuş) ──
await page.evaluate(() => cerNext());
await page.waitForTimeout(400);
step('show-all returns to results podium', !!(await page.$('#resStage .podium')));

// ── 7. ESC çıkış (yeni tören) ──
await page.evaluate(() => navigate('results'));
await page.waitForTimeout(300);
await page.click('#rgCer'); await page.waitForTimeout(150); await page.click('#rgStart');
await page.waitForTimeout(300);
// "herhangi bir tuş" ilerletir: rastgele bir harf
await page.keyboard.press('a');
await page.waitForTimeout(300);
step('any key advances reveal', await page.evaluate(() => CEREMONY.pos) === 1);
await page.keyboard.press('Escape');
await page.waitForTimeout(300);
step('ESC exits ceremony to results gate', !!(await page.$('#resStage .res-gate')));
const fxAfter = await page.evaluate(() => CEREMONY.fx);
step('ceremony fx cleaned up on exit', fxAfter === null);

await browser.close();
console.log('\n' + log.join('\n'));
console.log('\nConsole errors: ' + (errors.length ? '\n  ' + errors.join('\n  ') : 'none'));
const failed = log.filter(l => l.startsWith('FAIL')).length;
console.log(`\n${failed ? 'FAILED ' + failed : 'ALL PASSED'} (${log.length} checks)`);
process.exit(failed || errors.length ? 1 : 0);
