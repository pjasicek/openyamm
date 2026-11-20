// The panel gallery's outdoor section (S5b2), light and dark, as two pictures in output/s5b2_shots/ (the whole gallery
// is scripts/shots.mjs --only gallery). Build the web app first (npm run build).
//   node scripts/s5b2_gallery.mjs
import { join } from 'node:path';
import { repo, sleep, stampFolder, startRun } from './exit_common.mjs';

const out = join(repo, 'output', 's5b2_shots');
const run = await startRun({ out, prefix: 'gallery', roots: [stampFolder('gallery', 's5b2_web')] });
const { page, check } = run;
for (const theme of ['light', 'dark'])
{
    await page.goto(`${run.base}/gallery.html?theme=${theme}#token=${run.token}`);
    await page.waitForSelector('[data-section="outdoor"] figure[data-card]', { timeout: 20000 });
    await sleep(2500);
    const cards = await page.locator('[data-section="outdoor"] figure[data-card]').count();
    check(`gallery (${theme}): the outdoor section's cards render`, cards >= 18, `${cards} cards`);
    await run.shotOf('[data-section="outdoor"]', `outdoor_${theme}`, `the panel gallery's outdoor section, ${theme}`);
}
const failed = await run.finish('s5b2_gallery');
process.exit(failed > 0 ? 1 : 0);
