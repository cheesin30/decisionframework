const { chromium } = (function(){try{return require('playwright');}catch(e){return require('/opt/node22/lib/node_modules/playwright');}})();

(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || '/opt/pw-browsers/chromium' });
  const ctx = await browser.newContext();
  const page = await ctx.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message));
  const dialogs = [];
  page.on('dialog', async d => { dialogs.push(d.message()); await d.dismiss(); });

  await page.goto('file://'+require('path').resolve(__dirname,'..','LTI_Engagement_Calendar_QR_v1.html'));
  await page.waitForTimeout(300);
  await page.fill('#clientName', 'DBS'); await page.fill('#startDate', '2026-06-23');

  // --- Upload a small file + a >3MB file on Resources (step 2) ---
  await page.click('#stepper li:nth-child(2)'); await page.waitForTimeout(150);
  const [fc] = await Promise.all([ page.waitForEvent('filechooser'), page.click('button[onclick="uploadFileAssets()"]') ]);
  await fc.setFiles([
    { name: 'One-Pager.pdf', mimeType: 'application/pdf', buffer: Buffer.from('%PDF-1.4 small') },
    { name: 'Big-Deck.pdf', mimeType: 'application/pdf', buffer: Buffer.concat([Buffer.from('%PDF-1.4 '), Buffer.alloc(3400000, 65)]) },
  ]);
  await page.waitForTimeout(400);
  const bigChip = await page.$$eval('.asset-card .chip', cs => cs.map(c => c.textContent).find(t => /too big to attach/.test(t)) || null);

  // --- Attach both to touchpoint 1 (step 3), check plural summary ---
  await page.click('#stepper li:nth-child(3)'); await page.waitForTimeout(150);
  await page.click('.reminder-card .reminder-main .actions .btn.ghost.small'); await page.waitForTimeout(150);
  const boxes = await page.$$('.reminder-card.open input[type=checkbox][data-rem-asset]');
  for (const b of boxes) await b.check();
  await page.waitForTimeout(150);
  const summary = await page.textContent('.reminder-card .desc');

  // --- Size guard: flow-json export should warn about the big file ---
  await page.click('#stepper li:nth-child(4)'); await page.waitForTimeout(150);
  await page.evaluate(() => { window.__dl = []; window.downloadBlob = (b, n) => { window.__dl.push(n); }; });
  await page.$$eval('#mainPanel details.opts', ds => ds.forEach(d => d.open = true));
  await page.click('button[onclick="downloadFlowJson()"]'); await page.waitForTimeout(600);
  const dlAfterDismiss = await page.evaluate(() => window.__dl);

  // --- Refresh: files should restore from IndexedDB, no reselect ---
  await page.reload(); await page.waitForTimeout(600);   // restoreFiles is async post-init
  // wizard reopens on Details: refill firm/date first, then inspect Resources
  await page.fill('#clientName', 'DBS'); await page.fill('#startDate', '2026-06-23');
  await page.click('#stepper li:nth-child(2)'); await page.waitForTimeout(250);
  const chipsAfterReload = await page.$$eval('.asset-card', cards => cards.map(c => ({
    name: c.querySelector('h3').textContent,
    ready: !!Array.from(c.querySelectorAll('.chip')).find(x => x.textContent === 'Ready'),
  })));

  // Export the .ics after reload WITHOUT reselecting — must not hit the reselect alert
  let ics = null; await page.exposeFunction('capIcs', t => { ics = t; });
  await page.click('#stepper li:nth-child(4)'); await page.waitForTimeout(150);
  await page.evaluate(() => { window.downloadBlob = async (b, n) => { if (n.endsWith('.ics')) window.capIcs(await b.text()); }; });
  const dialogsBefore = dialogs.length;
  await page.$$eval('#mainPanel details.opts', ds => ds.forEach(d => d.open = true));
  await page.click('button[onclick="downloadICS()"]'); await page.waitForTimeout(800);
  const icsOk = !!ics && /ATTACH;ENCODING=BASE64/.test(ics);
  const noReselectAlert = !dialogs.slice(dialogsBefore).some(m => /Reselect/.test(m));

  // --- Stepper keyboard: Tab to a step, press Enter ---
  await page.focus('#stepper li:nth-child(3)');
  await page.keyboard.press('Enter'); await page.waitForTimeout(150);
  const kbdStep = await page.$eval('#stepper li[aria-current="step"]', el => el.textContent);

  // --- Print handout: capture the popup document ---
  await page.click('#stepper li:nth-child(4)'); await page.waitForTimeout(300);
  const printed = await page.evaluate(() => {
    let html = '';
    window.open = () => ({ document: { write: h => { html = h; }, close: () => {} }, print: () => {} });
    printQR();
    return html;
  });

  await browser.close();

  console.log('big-file chip:', JSON.stringify(bigChip));
  console.log('touchpoint summary (expect "1 day ... 2 resources"):', JSON.stringify(summary.trim()));
  console.log('size-guard confirm shown:', dialogs.some(m => /over 3\.0 MB[\s\S]*Big Deck/.test(m)), '| export blocked on dismiss:', dlAfterDismiss.length === 0);
  console.log('after reload, assets ready from IndexedDB:', JSON.stringify(chipsAfterReload));
  console.log('.ics exported after reload w/o reselect:', icsOk, '| no reselect alert:', noReselectAlert);
  console.log('keyboard Enter switched to step:', JSON.stringify((kbdStep || '').trim()));
  console.log('print handout has adviser steps:', /Scan the code with your phone camera/.test(printed) && /already filled in for your firm/.test(printed) && /accept<\/strong>/.test(printed));
  console.log('dialogs seen:', JSON.stringify(dialogs.map(d=>d.slice(0,80))));
console.log('errors:', errors.length ? errors : 'NONE');
})();
