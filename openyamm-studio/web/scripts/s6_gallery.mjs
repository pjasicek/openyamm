// The panel gallery's S6 section (the Cinematics and Overlay panels), light and dark, as pictures in
// output/studio_s6/shots_gallery/. Build the web app first (npm run build).
//   node scripts/s6_gallery.mjs
import { join } from 'node:path';
import { repo, sleep, stampFolder, startRun } from './exit_common.mjs';

const out = join(repo, 'output', 'studio_s6', 'shots_gallery');
const run = await startRun({ out, prefix: 'gallery', roots: [stampFolder('gallery', 'studio_s6')] });
const { page, check } = run;
for (const theme of ['light', 'dark'])
{
    await page.goto(`${run.base}/gallery.html?theme=${theme}#token=${run.token}`);
    await page.waitForSelector('[data-section="s6"] figure[data-card]', { timeout: 20000 });
    await sleep(1500);
    const cards = await page.locator('[data-section="s6"] figure[data-card]').count();
    check(`gallery (${theme}): the S6 section's cards render`, cards === 4, `${cards} cards`);
    const camera = await page.locator('[data-section="s6"] [data-testid="cinematic-camera"]').first().textContent();
    check(`gallery (${theme}): the cinematic's camera readout`, /shot 1, camera \[120, 120, 420\]/.test(camera ?? ''), camera);
    await run.shotOf('[data-section="s6"]', `s6_${theme}`, `the panel gallery's S6 section, ${theme}`);
}
const failed = await run.finish('s6_gallery');
process.exit(failed > 0 ? 1 : 0);
