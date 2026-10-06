// Renders the 1200x630 link-preview cards in og/ from on-brand HTML, in headless
// Chrome over the DevTools protocol (no npm dependencies; Pillow is not available
// to every Python on this machine). Run after changing a card or the price book:
//
//   node make_og.mjs            # writes og/og-packages.jpg, og-team.jpg, og-contact.jpg, og-a1.jpg
//
// Same look as the site since the 2026-10-06 redesign: flat ink, white Archivo
// with the orange highlight bar, real material only (headshots, real numbers).
// Prices come from data/packages.json, never typed here. Each JPEG must stay under
// 150KB; the script fails if one does not.
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync, mkdtempSync, statSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const ROOT = dirname(fileURLToPath(import.meta.url));
const f = p => pathToFileURL(join(ROOT, p)).href;
const PKG = JSON.parse(readFileSync(join(ROOT, 'data/packages.json'), 'utf8'));
const money = n => '$' + n.toLocaleString('en-US');
const minPrice = Math.min(...PKG.tiers.map(t => t.price));
const words = ['zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'];
const programs = words[PKG.tiers.length] || String(PKG.tiers.length);

const css = `
@font-face{font-family:Archivo;font-weight:700;src:url(${f('fonts/archivo-700.woff2')});font-display:block}
@font-face{font-family:Archivo;font-weight:900;src:url(${f('fonts/archivo-900.woff2')});font-display:block}
@font-face{font-family:Onest;font-weight:400;src:url(${f('fonts/onest-400.woff2')});font-display:block}
@font-face{font-family:Onest;font-weight:600;src:url(${f('fonts/onest-600.woff2')});font-display:block}
*{box-sizing:border-box;margin:0}
html,body{width:1200px;height:630px;overflow:hidden}
body{background:#14171A;color:#fff;font-family:Onest,sans-serif;position:relative}
.top{position:absolute;left:72px;top:56px;display:flex;align-items:center;gap:14px;font-weight:600;font-size:24px}
.top img{height:36px;width:auto;border-radius:2px}
.lines{position:absolute;left:0;right:0;bottom:0;height:260px;opacity:.9}
.body{position:absolute;left:72px;right:72px;bottom:64px}
.eyebrow{font-family:Archivo;font-weight:700;font-variant-caps:all-small-caps;letter-spacing:.06em;font-size:30px;color:#A8A29A;margin-bottom:14px}
h1{font-family:Archivo;font-weight:900;font-size:84px;line-height:1.14;letter-spacing:-.025em;max-width:16ch}
.hl{background:#F04820;color:#14171A;padding:0 .14em;box-decoration-break:clone;-webkit-box-decoration-break:clone}
.sub{margin-top:22px;font-size:28px;line-height:1.4;color:#D8D3C9;max-width:40ch}
h1.wide{max-width:22ch;font-size:76px}
.faces{position:absolute;right:72px;top:56px;display:flex;gap:10px}
.faces img{width:96px;height:96px;object-fit:cover;border-radius:3px}
.bars{position:absolute;right:72px;top:150px;width:430px;height:220px;display:flex;align-items:flex-end;gap:12px;border-bottom:2px solid #33383D}
.bars span{flex:1;background:rgba(0,176,200,.6);border-radius:3px 3px 0 0}
.bars span.lead{background:#F04820}
.bars.pair{width:260px;right:120px;gap:28px}
`;
const lines = `<svg class="lines" viewBox="0 0 1200 260" preserveAspectRatio="none" aria-hidden="true">
<path d="M-60,150 C90,118 210,118 300,150 C390,182 510,182 600,150 C690,118 810,118 900,150 C990,182 1110,182 1260,150" stroke="rgba(240,72,32,.35)" stroke-width="2" fill="none"/>
<path d="M-60,200 C120,186 280,186 400,200 C520,214 680,214 800,200 C920,186 1080,186 1260,200" stroke="rgba(0,176,200,.28)" stroke-width="1.5" fill="none"/></svg>`;
const top = `<div class="top"><img src="${f('logos_hss/nav_mark_hss.webp')}" alt="">Home Service Studios</div>`;

const cards = {
  'og-packages': `${top}${lines}<div class="body"><p class="eyebrow">Monthly packages</p>
    <h1 class="wide">Known and trusted<br><span class="hl">before they need you.</span></h1>
    <p class="sub">${programs[0].toUpperCase() + programs.slice(1)} monthly programs, from ${money(minPrice)} a month.</p></div>`,
  'og-team': `${top}<div class="faces">${['craig-balog', 'seth-yeager', 'paloma-barro', 'yoni-paz', 'sergy-olkowski']
      .map(n => `<img src="${f('post/' + n + '.jpg')}" alt="">`).join('')}</div>${lines}
    <div class="body"><p class="eyebrow">Meet the team</p><h1>Meet <span class="hl">the team.</span></h1>
    <p class="sub">The people who write, shoot, edit and post the work.</p></div>`,
  'og-contact': `${top}${lines}<div class="body"><p class="eyebrow">Contact</p>
    <h1>Talk <span class="hl">to us.</span></h1>
    <p class="sub">Tell us your city and your trade. A person answers within one business day.</p></div>`,
  'og-a1': `${top}<div class="bars">${[623, 428, 410, 312, 195, 162, 134]
      .map((v, i) => `<span class="${i ? '' : 'lead'}" style="height:${(v / 623 * 100).toFixed(1)}%"></span>`).join('')}</div>${lines}
    <div class="body"><p class="eyebrow">Case study &middot; A1 Air Conditioning</p>
    <h1><span class="hl">2.26M views.</span></h1>
    <p class="sub">Seven reels past 100,000 views for a Tucson HVAC company with 9,200 followers.</p></div>`,
  'og-bee-right-there': `${top}<div class="bars pair">${[27851, 106439]
      .map((v, i) => `<span class="${i ? 'lead' : ''}" style="height:${(v / 106439 * 100).toFixed(1)}%"></span>`).join('')}</div>${lines}
    <div class="body"><p class="eyebrow">Case study &middot; Bee Right There Heating &amp; Air</p>
    <h1><span class="hl">3.8x the views.</span></h1>
    <p class="sub">46 posts were seen 27,851 times. The next 57, in three weeks, 106,439 times.</p></div>`,
  'og-icomfort': `${top}<div class="bars pair">${[290, 1970]
      .map((v, i) => `<span class="${i ? 'lead' : ''}" style="height:${(v / 1970 * 100).toFixed(1)}%"></span>`).join('')}</div>${lines}
    <div class="body"><p class="eyebrow">Case study &middot; iComfort Heating and Air Conditioning</p>
    <h1><span class="hl">290 to 1,970 followers.</span></h1>
    <p class="sub">A family-owned HVAC company in the San Fernando Valley, in under a year, all organic.</p></div>`,
};

const work = mkdtempSync(join(tmpdir(), 'hss-og-'));
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const port = 9400 + Math.floor(Math.random() * 90);
const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${port}`, '--no-first-run',
  '--hide-scrollbars', '--allow-file-access-from-files', `--user-data-dir=${join(work, 'profile')}`, 'about:blank'],
  { stdio: 'ignore' });
const sleep = ms => new Promise(r => setTimeout(r, ms));
let wsUrl;
for (let i = 0; i < 60 && !wsUrl; i++) {
  await sleep(200);
  try { const t = await (await fetch(`http://127.0.0.1:${port}/json`)).json(); wsUrl = t.find(x => x.type === 'page')?.webSocketDebuggerUrl; } catch {}
}
const ws = new WebSocket(wsUrl);
await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map(); const waiters = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method) waiters.slice().forEach(w => w(m));
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const once = method => new Promise(r => { const g = m => { if (m.method === method) { waiters.splice(waiters.indexOf(g), 1); r(m); } }; waiters.push(g); });

await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1200, height: 630, deviceScaleFactor: 1, mobile: false });
let failed = false;
for (const [name, body] of Object.entries(cards)) {
  const file = join(work, name + '.html');
  writeFileSync(file, `<!doctype html><html><head><meta charset="utf-8"><style>${css}</style></head><body>${body}</body></html>`);
  const loaded = once('Page.loadEventFired');
  await send('Page.navigate', { url: pathToFileURL(file).href });
  await loaded;
  await send('Runtime.evaluate', { expression: 'document.fonts.ready.then(() => Promise.all([...document.images].map(i => i.decode())))', awaitPromise: true });
  await sleep(150);
  const r = await send('Page.captureScreenshot', { format: 'jpeg', quality: 82, clip: { x: 0, y: 0, width: 1200, height: 630, scale: 1 } });
  const out = join(ROOT, 'og', name + '.jpg');
  writeFileSync(out, Buffer.from(r.result.data, 'base64'));
  const kb = statSync(out).size / 1024;
  console.log(`${name}.jpg  ${kb.toFixed(1)} KB`);
  if (kb >= 150) { console.error(`  ${name}.jpg is over the 150KB limit`); failed = true; }
}
ws.close(); chrome.kill();
process.exit(failed ? 1 : 0);
