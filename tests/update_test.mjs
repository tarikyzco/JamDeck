// Güncelleme kartı UI testi (mock bridge): denetle -> bul -> indir (progress) -> dev hint
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

// kart + sürüm tek kaynaktan
step('update card renders', !!(await page.$('#suUpdCheck')));
const sideVer = await page.textContent('#sideVersion');
step('sidebar version from getAppInfo', sideVer.includes('v2.0.0'), sideVer);
const cardVer = await page.textContent('#suUpdVer');
step('card shows current version', cardVer.includes('2.0.0'), cardVer);

// repo uygulamaya gömülü -> kartta repo alanı YOK (kullanıcı kararı)
step('no repo field in UI (embedded)', !(await page.$('#suUpdRepo')));

// denetle -> mock 2.1.0 bulur
await page.click('#suUpdCheck');
await page.waitForTimeout(800);
const found = await page.textContent('#suUpdResult');
step('check finds v2.1.0 + notes', found.includes('v2.1.0') && found.includes('Sayaç'), found.slice(0, 60));
step('install button appears', !!(await page.$('#suUpdInstall')));

// indir -> progress -> dev modda kurulum yerine uyarı
await page.click('#suUpdInstall');
await page.waitForTimeout(700);
const barW = await page.$eval('#suUpdBar', e => e.style.width);
step('progress bar advances', parseInt(barW) >= 50, `width=${barW}`);
await page.waitForTimeout(800);
const ready = await page.textContent('#suUpdResult');
step('dev mode shows manual-copy hint after download', ready.includes('Geliştirme modunda'), ready.slice(0, 80));

// oto-denetim anahtarı
await page.click('#suUpdAuto');
await page.waitForTimeout(200);
const autoCfg = await page.evaluate(() => CONFIG.update.auto);
step('auto toggle persists', autoCfg === false, String(autoCfg));

console.log(log.join('\n'));
console.log('\nConsole errors:', errors.length ? errors.join('\n') : 'none');
await browser.close();
process.exit(log.some(l => l.startsWith('FAIL')) ? 1 : 0);
