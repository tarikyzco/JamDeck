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

// load mock games first (so results have data)
await page.evaluate(() => navigate('launcher'));
await page.waitForTimeout(800);

// 1. nav item
step('sidebar has Voting nav item', !!(await page.$('.nav-item[data-nav="voting"]')));

// 2. navigate to voting
await page.evaluate(() => navigate('voting'));
await page.waitForTimeout(300);
step('voting screen activates', await page.$eval('#screen-voting', el => el.classList.contains('active')).catch(()=>false));

// 3. groups rendered (yeni kompakt group-row)
const groups = await page.$$('.group-row');
step('3 vote groups rendered', groups.length === 3, `count=${groups.length}`);
const ranges = await page.$$('[data-grp-w]');
step('weight sliders present', ranges.length === 3, `count=${ranges.length}`);

// 4. toggle a group off updates CONFIG + class
await page.click('.group-row[data-grp="team"] input[data-grp-en="team"]');
await page.waitForTimeout(150);
const teamEnabled = await page.evaluate(() => CONFIG.voting.groups.team.enabled);
const teamOffClass = await page.$eval('.group-row[data-grp="team"]', el => el.classList.contains('off'));
step('toggle group updates config + .off', teamEnabled === false && teamOffClass, `enabled=${teamEnabled} off=${teamOffClass}`);
await page.click('.group-row[data-grp="team"] input[data-grp-en="team"]');
await page.waitForTimeout(100);

// 5. weight slider updates value + config
await page.evaluate(() => { const r=document.querySelector('[data-grp-w="jury"]'); r.value=80; r.dispatchEvent(new Event('input',{bubbles:true})); });
await page.waitForTimeout(120);
const juryW = await page.evaluate(() => CONFIG.voting.groups.jury.weight);
const juryWLabel = await page.$eval('[data-grp-win="jury"]', el => el.value);
step('weight slider updates config + label', juryW === 80 && juryWLabel === '0.80', `w=${juryW} label=${juryWLabel}`);

// 5x. katsayı KLAVYE girişi: tam sayı = ağırlık (1=×0.01, 100=×1.00), ondalık = katsayı
const typeCoef = async (sel, val) => page.evaluate(({ sel, val }) => {
  const el = document.querySelector(sel); el.value = val;
  el.dispatchEvent(new Event('change', { bubbles: true }));
}, { sel, val });
await typeCoef('[data-grp-win="jury"]', '1');
let r1 = await page.evaluate(() => ({ w: CONFIG.voting.groups.jury.weight,
  v: document.querySelector('[data-grp-win="jury"]').value,
  s: +document.querySelector('[data-grp-w="jury"]').value }));
step('typed "1" -> ×0.01 (slider synced)', r1.w === 1 && r1.v === '0.01' && r1.s === 1, JSON.stringify(r1));
await typeCoef('[data-grp-win="jury"]', '100');
r1 = await page.evaluate(() => ({ w: CONFIG.voting.groups.jury.weight,
  v: document.querySelector('[data-grp-win="jury"]').value }));
step('typed "100" -> ×1.00', r1.w === 100 && r1.v === '1.00', JSON.stringify(r1));
await typeCoef('[data-grp-win="jury"]', '0,5');
r1 = await page.evaluate(() => ({ w: CONFIG.voting.groups.jury.weight,
  v: document.querySelector('[data-grp-win="jury"]').value }));
step('typed decimal "0,5" -> ×0.50', r1.w === 50 && r1.v === '0.50', JSON.stringify(r1));
await typeCoef('[data-grp-win="jury"]', 'abc');
r1 = await page.evaluate(() => ({ w: CONFIG.voting.groups.jury.weight,
  v: document.querySelector('[data-grp-win="jury"]').value }));
step('invalid input keeps old value', r1.w === 50 && r1.v === '0.50', JSON.stringify(r1));
await typeCoef('[data-cat-win="0"]', '10');
const rc = await page.evaluate(() => ({ w: CONFIG.voting.categories[0].weight,
  v: document.querySelector('[data-cat-win="0"]').value }));
step('category typed "10" -> ×0.10', rc.w === 10 && rc.v === '0.10', JSON.stringify(rc));
// jüri ağırlığını test akışının beklediği 80'e geri al
await typeCoef('[data-grp-win="jury"]', '80');

// 5b. categories: render + add + remove + weight (yeni cat-row)
const catRows = (await page.$$('.cat-row')).length;
step('6 category rows render', catRows === 6, `count=${catRows}`);
const catLen0 = await page.evaluate(()=>CONFIG.voting.categories.length);
await page.click('#voteAddCat'); await page.waitForTimeout(120);
const catLenAdd = await page.evaluate(()=>CONFIG.voting.categories.length);
step('add category', catLenAdd === catLen0+1 && (await page.$$('.cat-row')).length === catLen0+1, `len=${catLenAdd}`);
await page.click('.cat-row[data-ci="0"] [data-cat-del]'); await page.waitForTimeout(120);
const catLenDel = await page.evaluate(()=>CONFIG.voting.categories.length);
step('delete category', catLenDel === catLen0, `len=${catLenDel}`);
await page.evaluate(()=>{const r=document.querySelector('[data-cat-w="0"]'); r.value=50; r.dispatchEvent(new Event('input',{bubbles:true}));});
await page.waitForTimeout(120);
const catW0 = await page.evaluate(()=>CONFIG.voting.categories[0].weight);
step('category weight updates config', catW0 === 50, `w=${catW0}`);

// 5c. access controls: segment per group + mode switch + fields
const accessSegs = (await page.$$('[data-grp-access]')).length;
step('access segment per group', accessSegs === 3, `count=${accessSegs}`);
const juryAccess0 = await page.evaluate(()=>CONFIG.voting.groups.jury.access);
step('jury default access = codes', juryAccess0 === 'codes', juryAccess0);
await page.click('[data-grp-access="jury"] button[data-val="pin"]');
await page.waitForTimeout(150);
const juryAccessPin = await page.evaluate(()=>CONFIG.voting.groups.jury.access);
const pinShown = !!(await page.$('[data-grp-pin="jury"]'));
step('switch -> PIN updates config + shows pin field', juryAccessPin==='pin' && pinShown, `access=${juryAccessPin} pin=${pinShown}`);
await page.evaluate(()=>{ const p=document.querySelector('[data-grp-pin="jury"]'); p.value='1234'; p.dispatchEvent(new Event('input',{bubbles:true})); const l=document.querySelector('[data-grp-limit="jury"]'); l.value=7; l.dispatchEvent(new Event('input',{bubbles:true})); });
await page.waitForTimeout(120);
const pinCfg = await page.evaluate(()=>({pin:CONFIG.voting.groups.jury.pin, limit:CONFIG.voting.groups.jury.limit}));
step('pin + limit persisted', pinCfg.pin==='1234' && pinCfg.limit===7, JSON.stringify(pinCfg));
await page.click('[data-grp-access="jury"] button[data-val="codes"]');
await page.waitForTimeout(150);
step('switch -> Codes shows code-count field', !!(await page.$('[data-grp-count="jury"]')));

// 6. start server -> status chip ok; Online (funnel) public links appear after tunnel ready
// (LAN modu kaldırıldı; tek yol Online. Mock funnel ~450ms'de public URL verir.)
await page.click('#voteToggle');
await page.waitForTimeout(1000);
const statusOn = !!(await page.$('#voteStatus .chip-ok'));
const links = await page.$$('#voteLinks .link-row');
step('start -> status ON', statusOn);
step('vote links rendered (enabled groups)', links.length === 3, `count=${links.length}`);
const firstUrl = await page.$eval('.link-row .url', el => el.textContent).catch(()=>'');
step('link is a public vote URL', /^https?:\/\/.+\/v\/.+/.test(firstUrl), firstUrl);

// 7. live panel = participation counter only (scores HIDDEN until finalize)
await page.waitForTimeout(600);
step('live participation shown', !!(await page.$('.participation')));
step('live scores hidden (no rank rows on voting screen)', (await page.$$('#screen-voting .rank-row')).length === 0);
const totalTxt = await page.$eval('.participation .big-num', el => el.textContent).catch(()=>'0');
step('participation total > 0', parseInt(totalTxt,10) > 0, `total=${totalTxt}`);

// 7b. current-game banner shows the active game
const curName = await page.$eval('#voteCurrent.active .vc-name', el => el.textContent.trim()).catch(()=>'');
step('current-game banner shows active game', curName.length > 0, `name="${curName}"`);

// 7c. codes panel: reveal one-time codes while server running
await page.evaluate(()=>{ const c=document.querySelector('[data-grp-count="jury"]'); c.value=4; c.dispatchEvent(new Event('input',{bubbles:true})); });
await page.waitForTimeout(150);
await page.click('[data-grp-codesbtn="jury"]');
await page.waitForTimeout(400);
const codeChips = (await page.$$('.vg-codes-panel[data-grp-panel="jury"] .code-chip')).length;
step('codes panel reveals chips (server running)', codeChips === 4, `chips=${codeChips}`);
// kod panosu linki kodların ALTINDA, /k/ URL'li, QR butonu YOK (kullanıcı kararı)
const boardUrl = await page.$eval('.vg-codes-panel[data-grp-panel="jury"] [data-board-copy]',
  el => el.dataset.boardCopy).catch(() => '');
step('code board link under codes panel', /\/k\/.+/.test(boardUrl), boardUrl);
const boardQr = await page.$('.vg-codes-panel[data-grp-panel="jury"] [data-qr]');
step('no QR button for board link', !boardQr);

// 7d. FINALIZE: navigates to the Results screen (reveal happens there)
await page.evaluate(() => { if (Bridge) Bridge.__xlsxCalls = 0; });
await page.click('#voteFinalize');
await page.waitForTimeout(900);
step('finalize navigates to Results', await page.$eval('#screen-results', el => el.classList.contains('active')).catch(()=>false));
// spoiler kapısı (Tören Modu özelliği): tam sıralamayı görmek için "Tümünü Göster"
step('results gate shown after finalize', !!(await page.$('#resStage .res-gate')));
await page.click('#rgAll');
await page.waitForTimeout(300);
const pods = (await page.$$('.pod')).length;
step('Top-3 podium rendered', pods === 3, `pods=${pods}`);
const firstScore = await page.$eval('.pod.first .score-badge', el => el.textContent.trim()).catch(()=>'');
step('winner has score badge', firstScore.length > 0, firstScore);
const gbars = (await page.$$('.pod.first .gbar')).length;
step('per-group bars on winner', gbars > 0, `bars=${gbars}`);

// 7e. variant switch: Top 5 -> rank list
await page.click('#resultSeg button[data-variant="top5"]');
await page.waitForTimeout(300);
const rankRows = (await page.$$('#screen-results .rank-row')).length;
step('Top-5 variant lists up to 5 rows', rankRows > 0 && rankRows <= 5, `rows=${rankRows}`);
await page.click('#resultSeg button[data-variant="all"]');
await page.waitForTimeout(300);
const allRows = (await page.$$('#screen-results .rank-row')).length;
step('All variant lists >= Top-5 rows', allRows >= rankRows, `rows=${allRows}`);
await page.click('#resultSeg button[data-variant="top3"]');
await page.waitForTimeout(200);

// 7f. PNG poster builder + xlsx export from Results screen
const posterOk = await page.evaluate(() => {
  const s = buildResultsPoster(LAST_RESULTS);
  return typeof s === 'string' && s.startsWith('<svg') && s.includes('</svg>');
});
step('buildResultsPoster() returns SVG', posterOk);
await page.click('#resSaveXlsx');
await page.waitForTimeout(300);
const xlsxCalls = await page.evaluate(() => Bridge ? Bridge.__xlsxCalls : -1);
step('xlsx button triggers export', xlsxCalls >= 1, `calls=${xlsxCalls}`);

// 7g. RESET VOTING: custom modal gate — cancel keeps votes, confirm clears them
await page.evaluate(() => navigate('voting'));
await page.waitForTimeout(400);
await page.evaluate(() => { if (Bridge) Bridge.__resetCalls = 0; });
await page.click('#voteReset');
await page.waitForTimeout(300);
const modalText = await page.$eval('.modal-backdrop.show .modal p', el => el.textContent).catch(()=>'');
step('reset opens confirm modal', /silinir|deleted/i.test(modalText), `msg="${modalText}"`);
await page.click('.modal-backdrop.show [data-cancel]');
await page.waitForTimeout(300);
step('cancel -> votes NOT reset', (await page.evaluate(() => Bridge ? Bridge.__resetCalls : -1)) === 0);
await page.click('#voteReset');
await page.waitForTimeout(300);
await page.click('.modal-backdrop.show [data-ok]');
await page.waitForTimeout(500);
step('confirm -> resetVotes called', (await page.evaluate(() => Bridge ? Bridge.__resetCalls : -1)) === 1);
step('after reset live counter empties', !!(await page.$('#voteResults .vote-empty')));

// 8. stop server -> status off, links cleared
await page.click('#voteToggle');
await page.waitForTimeout(300);
const statusOff = !(await page.$('#voteStatus .chip-ok'));
const linksAfter = await page.$$('#voteLinks .link-row');
step('stop -> status OFF + links cleared', statusOff && linksAfter.length === 0, `off=${statusOff} links=${linksAfter.length}`);

// re-start for the screenshot
await page.click('#voteToggle');
await page.waitForTimeout(700);
await page.screenshot({ path: path.resolve(__dirname, '../scratch/voting_screenshot.png'), fullPage: false });

console.log('\n=== VOTING SCREEN TEST RESULTS ===');
console.log(log.join('\n'));
console.log('\n=== CONSOLE ERRORS (' + errors.length + ') ===');
console.log(errors.length ? errors.join('\n') : '(none)');

await browser.close();
process.exit(log.filter(l => l.startsWith('FAIL')).length + errors.length > 0 ? 1 : 0);
