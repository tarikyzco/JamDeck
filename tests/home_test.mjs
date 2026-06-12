// Faz 5: Ana ekran — indir + organize TEK otomatik akış, kalıcı boş alanlar, Sunum ekranı
import { chromium } from 'playwright';
import { pathToFileURL, fileURLToPath } from 'url';
import path from 'path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const url = pathToFileURL(path.resolve(__dirname, '../frontend/index.html')).href;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1400, height: 900 } });
const errors = [];
page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
page.on('pageerror', e => errors.push('PAGEERROR: ' + e.message));

await page.goto(url);
await page.waitForTimeout(1500);

const log = [];
const step = (n, ok, x='') => log.push(`${ok ? 'PASS' : 'FAIL'}  ${n}${x ? ' — ' + x : ''}`);

// 1. açılış ekranı = Kurulum (kullanıcı kararı), organize nav YOK
step('initial screen is Kurulum', await page.$eval('#screen-setup', el => el.classList.contains('active')).catch(()=>false));
step('no separate Organize nav', !(await page.$('.nav-item[data-nav="organize"]')));
step('Results nav exists', !!(await page.$('.nav-item[data-nav="results"]')));
await page.evaluate(() => navigate('download'));
await page.waitForTimeout(300);

// 2. alanlar boş başlar (hardcoded demo değer yok)
const urlVal = await page.$eval('#dlUrl', e => e.value);
const keyVal = await page.$eval('#dlKey', e => e.value);
step('itch fields start empty', urlVal === '' && keyVal === '', `url="${urlVal}" key="${keyVal}"`);

// 3. değer gir + başlat -> config'e kalıcı yazılır
await page.fill('#dlUrl', 'https://itch.io/jam/test-jam');
await page.fill('#dlKey', 'itch_test_key');
await page.click('#dlStart');
await page.waitForTimeout(400);
const itchCfg = await page.evaluate(() => CONFIG.itch);
step('start persists itch config', itchCfg.jamUrl === 'https://itch.io/jam/test-jam' && itchCfg.apiKey === 'itch_test_key', JSON.stringify(itchCfg));

// 4. aşama rozetleri: indirme aktif
const dlStageActive = await page.$eval('.stage[data-stage="download"]', el => el.classList.contains('active'));
step('download stage active while running', dlStageActive);

// 5. indirme + organize otomatik zincir (mock ~13sn) — tek konsolda iki kanal
await page.waitForTimeout(11000); // mock download bitsin
const extractStarted = await page.evaluate(() =>
  document.querySelector('.stage[data-stage="extract"]').classList.contains('active') ||
  document.querySelector('.stage[data-stage="extract"]').classList.contains('done') ||
  document.querySelector('.stage[data-stage="organize"]').classList.contains('active') ||
  document.querySelector('.stage[data-stage="ready"]').classList.contains('active'));
step('extract/organize chains automatically after download', extractStarted);
await page.waitForTimeout(6500); // organize bitsin
const readyDone = await page.$eval('.stage[data-stage="ready"]', el => el.classList.contains('done') || el.classList.contains('active'));
step('ready stage reached', readyDone);
const chips = (await page.$$('#homeChips .chip')).length;
step('summary chips rendered', chips === 3, `chips=${chips}`);
const consoleHasOrganize = await page.evaluate(() => document.querySelector('#homeConsole').textContent.includes('Done ✓'));
step('single console carries organize logs too', consoleHasOrganize);
const statusDone = !!(await page.$('#dlStatusChip.chip-ok'));
step('status chip = done', statusDone);

await page.screenshot({ path: path.resolve(__dirname, '../scratch/home_screenshot.png') });

// 6. SUNUM ekranı: oyun listesi + hero + "Sunumu Başlat"
await page.evaluate(() => navigate('launcher'));
await page.waitForTimeout(900);
step('present screen activates', await page.$eval('#screen-launcher', el => el.classList.contains('active')).catch(()=>false));
const rows = (await page.$$('.game-row')).length;
step('game rows rendered', rows > 0, `rows=${rows}`);
const playLabel = await page.$eval('#heroPlay', el => el.textContent.trim()).catch(()=>'');
step('play button = Sunumu Başlat', /Sunumu Başlat/.test(playLabel), `"${playLabel}"`);
step('hero 4:3 cover present', !!(await page.$('.hero-art .art-img')));
step('duration box present', !!(await page.$('#llMinutes')));

// 7. arama filtreler
const firstName = await page.$eval('.game-row .name', el => el.textContent);
await page.fill('#llSearch', firstName.slice(0, 4));
await page.waitForTimeout(250);
const filtered = (await page.$$('.game-row')).length;
step('search filters list', filtered > 0 && filtered <= rows, `filtered=${filtered}`);
await page.fill('#llSearch', '');

await page.screenshot({ path: path.resolve(__dirname, '../scratch/present_screenshot.png') });

console.log('\n=== HOME + PRESENT TEST RESULTS ===');
console.log(log.join('\n'));
console.log('\n=== CONSOLE ERRORS (' + errors.length + ') ===');
console.log(errors.length ? errors.join('\n') : '(none)');

await browser.close();
process.exit(log.filter(l => l.startsWith('FAIL')).length + errors.length > 0 ? 1 : 0);
