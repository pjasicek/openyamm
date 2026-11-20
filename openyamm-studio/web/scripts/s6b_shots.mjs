// S6, the second run: screenshots of what it added to the browser, in output/studio_s6b/shots/ (build the web app
// first: npm run build). The project list's world map over the briefs (mm6, mm7, mm8; light and dark), the Mods view
// with a project packed into a mod with its map numbers, the New project form proposing a number from that mod's range,
// and the Overlay tab's tools on a copy of the Goblinwatch overlay (a light placed on the plan, a base spawn taken out,
// the project's light recoloured); with --bake also a lighting bake run as a job from the Jobs tab and its pictures.
//   node scripts/s6b_shots.mjs [--bake]
import { cpSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';
import { repo, sleep, stampFolder, startRun, studio } from './exit_common.mjs';

const out = join(repo, 'output', 'studio_s6b', 'shots');
const runFolder = stampFolder('s6b', 'studio_s6b');
// Copies the run may change: the overlay (edited by the Overlay tab) and the loft (packed into a mod).
cpSync(join(studio, 'examples', 's6_overlay_goblinwatch'), join(runFolder, 'projects', 'overlay_goblinwatch'), { recursive: true,
    filter: (source) => !/\/(\.oymap|build)(\/|$)/.test(source) });
cpSync(join(studio, 'examples', 's6_loft'), join(runFolder, 'projects', 'loft'), { recursive: true,
    filter: (source) => !/\/(\.oymap|build)(\/|$)/.test(source) });
const mods = join(runFolder, 'mods');
mkdirSync(mods, { recursive: true });
// (The host takes its roots as one list, comma-separated.)
const run = await startRun({ out, prefix: 's6b', roots: [[join(repo, 'devdocs', 'map_studio', 'briefs'), join(repo, 'devdocs', 'xeen', 'briefs'),
    join(runFolder, 'projects')].join(',')], hostArgs: ['--mods', mods] });
const { page, check } = run;

// --- the world map -------------------------------------------------------------------------------------------------
try
{
    await page.goto(`${run.base}/#token=${run.token}`);
}
catch (error)
{
    console.log(`the host did not answer: ${run.hostLog().slice(-2000)}`);
    throw error;
}
await page.waitForSelector('[data-testid="list-view-world"]', { timeout: 20000 });
await page.click('[data-testid="list-view-world"]');
await page.waitForSelector('[data-testid="world-view"] svg', { timeout: 20000 });
await sleep(500);
for (const world of ['mm6', 'mm7', 'mm8'])
{
    await page.getByRole('tab', { name: new RegExp(`^${world} `) }).click();
    await page.waitForSelector(`[data-testid="world-map-${world}"]`, { timeout: 10000 });
    await sleep(300);
    const maps = await page.locator(`[data-testid="world-map-${world}"] [data-map]`).count();
    const edges = await page.locator(`[data-testid="world-map-${world}"] [data-edge]`).count();
    check(`world map ${world}: maps and links drawn`, maps >= 5 && edges >= 4, `${maps} maps, ${edges} lines`);
    await run.shot(`world_${world}`, `the project list's world map of ${world}: projects, the shipped maps their exits reach, the links`);
}
// Hovering a project's map lights its lines; clicking it opens the project.
const xeen = page.locator('[data-testid="world-map-mm7"] [data-map="xeen_x1.odm"]');
await page.getByRole('tab', { name: /^mm7 / }).click();
await xeen.hover();
await sleep(200);
check('world map: hovering Vertigo Meadows lights its lines', await page.locator('[data-testid="world-map-mm7"] [data-edge]').evaluateAll((lines) =>
    lines.filter((line) => /edgeLit/.test(line.getAttribute('class') ?? '')).length >= 5), '');
await run.shot('world_mm7_hover', 'mm7 with Vertigo Meadows under the pointer: its links lit');
await page.emulateMedia({ colorScheme: 'dark' });
await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'dark'));
await sleep(300);
await run.shot('world_mm7_dark', 'the mm7 world map, dark');
await page.evaluate(() => document.documentElement.removeAttribute('data-theme'));
await page.emulateMedia({ colorScheme: 'light' });

// --- the mods: pack the loft into a mod with its numbers ---------------------------------------------------------
await page.click('[data-testid="list-view-mods"]');
await page.waitForSelector('[data-testid="mod-pack-form"]', { timeout: 10000 });
await page.fill('[data-testid="mod-id"]', 'leaning_lofts');
await page.fill('[data-testid="mod-name"]', 'The leaning lofts');
await page.fill('[data-testid="mod-range"]', '9400-9409');
await page.locator('[data-testid="mod-projects"] label', { hasText: 'The Leaning Ladder' }).locator('input').check();
await page.click('[data-testid="mod-pack"]');
await page.waitForSelector('[data-testid="mod-packed"]', { timeout: 60000 });
await page.waitForSelector('[data-testid="mods-table"]', { timeout: 10000 });
await sleep(300);
const packed = await page.locator('[data-testid="mod-packed"]').textContent();
check('mods: the loft packed with its map number', /studio07\.blv \(new, 9400\)/.test(packed ?? ''), packed);
const row = await page.locator('[data-testid="mods-table"] tbody tr').first().textContent();
check('mods: the folder lists it with its range', /9400 to 9409/.test(row ?? ''), row);
await run.shot('mods', 'the Mods view: the loft packed into a mod declaring the map numbers 9400 to 9409');

// --- a new project of the mod: its number proposed ---------------------------------------------------------------
await page.click('[data-testid="new-project"]');
await page.waitForSelector('[data-testid="new-stats-note"]', { timeout: 10000 });
await run.waitFor(() => /first free number/.test(document.querySelector('[data-testid="new-stats-note"]')?.textContent ?? ''), 10000);
const studioNote = await page.locator('[data-testid="new-stats-note"]').textContent();
check('new project: a number from the studio\'s band', /the studio's band \(9400 to 9999/.test(studioNote ?? ''), studioNote);
await page.selectOption('[data-testid="new-mod"]', 'leaning_lofts');
await run.waitFor(() => /mod leaning_lofts/.test(document.querySelector('[data-testid="new-stats-note"]')?.textContent ?? ''), 10000);
const modNote = await page.locator('[data-testid="new-stats-note"]').textContent();
const proposed = await page.inputValue('[data-testid="new-stats"]');
check('new project: the mod\'s next free number', proposed === '9401' && /9400 to 9409, 1 taken/.test(modNote ?? ''), `${proposed}: ${modNote}`);
await run.shotOf('[data-testid="new-project-form"]', 'new_project_mod', 'the New project form: the map number proposed from the mod\'s range');
await page.getByRole('button', { name: 'Cancel' }).click();

// --- the Overlay tab's tools ---------------------------------------------------------------------------------------
await page.click('[data-testid="list-view-list"]');
await page.locator('tr', { hasText: 's6_lamps' }).first().click().catch(async () => page.locator('tr', { hasText: 'overlay_goblinwatch' }).first().click());
await run.waitFor(() => window.__studio?.app?.store.getState().project.state === 'ready', 30000);
await run.settled();
await page.click('[data-testid="mode-author"]');
await page.click('[data-testid="tab-overlay"]');
await page.waitForSelector('[data-testid="overlay-tools"]', { timeout: 20000 });
await sleep(500);
await run.shotOf('[data-testid="overlay-panel"]', 'overlay_before', 'the Overlay tab in Author mode, before');
// A light placed on the plan.
await page.click('[data-testid="overlay-tool-light"]');
await sleep(300);
const plan = await page.locator('[data-testid="overlay-plan"]').boundingBox();
await page.mouse.click(plan.x + plan.width * 0.3, plan.y + plan.height * 0.4);

await run.waitFor(() => window.__studio.app.store.getState().project.value.files['objects.yml'].tree.scene.lights.some((light) => light.id === 'light:new_1'), 20000);
await run.settled();
await sleep(800);
// A base spawn point taken out.
await page.click('[data-testid="overlay-tool-select"]');
await page.locator('[data-testid="overlay-plan"] [data-thing="spawn:s2"]').dispatchEvent('click');
await page.waitForSelector('[data-testid="overlay-remove"]', { timeout: 10000 });
await page.click('[data-testid="overlay-remove"]');
await run.waitFor(() => (window.__studio.app.store.getState().project.value.files['objects.yml'].tree.scene.removals ?? []).includes('spawn:s2'), 20000);
await run.settled();
await sleep(800);
// The project's own light recoloured by its form.
await page.click('[data-testid="overlay-thing-light:vault_glow"]');
await page.waitForSelector('[data-testid="overlay-field-color"]', { timeout: 10000 });
await page.fill('[data-testid="overlay-field-color"]', '255, 120, 60');
await page.click('[data-testid="overlay-apply"]');
await run.waitFor(() => JSON.stringify(window.__studio.app.store.getState().project.value.files['objects.yml'].tree.scene.lights
    .find((light) => light.id === 'light:vault_glow').color) === '[255,120,60]', 20000);
await run.settled();
await sleep(1200);
// What the three gestures wrote, read from the project's file.
const written = readFileSync(join(runFolder, 'projects', 'overlay_goblinwatch', 'objects.yml'), 'utf8');
check('overlay tools: the light placed on the plan, spawn:s2 taken out and the glow recoloured, in objects.yml',
    /id: light:new_1, position: \[/.test(written) && /removals: \[spawn:s1, spawn:s2\]/.test(written) && /color: \[255, 120, 60\]/.test(written),
    written.slice(0, 600));
await run.shotOf('[data-testid="overlay-panel"]', 'overlay_after', 'the Overlay tab after: a light added on the plan, spawn:s2 taken out, the vault glow recoloured (its form open)');

// --- a lighting bake as a job, its pictures in the Pictures tab (--bake: Blender and the game, about a minute) ------
if (process.argv.includes('--bake'))
{
    await page.getByRole('button', { name: 'Map Studio' }).click();
    await page.waitForSelector('[data-testid="list-view-list"]', { timeout: 20000 });
    await page.click('[data-testid="list-view-list"]');
    await page.locator('tr', { hasText: 'The Leaning Ladder' }).first().click();
    await run.waitFor(() => window.__studio?.app?.store.getState().project.state === 'ready', 30000);
    await run.settled();
    await page.click('[data-testid="tab-jobs"]');
    await page.getByRole('button', { name: 'Bake lighting' }).click();
    const baked = await run.waitFor(() => (window.__studio.app.store.getState().jobs.value ?? [])
        .some((job) => job.kind === 'lighting_bake' && (job.state === 'done' || job.state === 'failed')), 600000);
    const job = (await run.state()).jobs.value.find((entry) => entry.kind === 'lighting_bake');
    check('lighting bake: the job ran to its pictures', baked && job?.state === 'done' && job.pictures.length >= 3, `${job?.state}: ${job?.line ?? job?.error}`);
    await sleep(500);
    await run.shotOf('[data-testid="jobs"]', 'bake_job', 'the Jobs tab: the lighting bake done, its line');
    await page.click('[data-testid="tab-pictures"]');
    await page.waitForSelector('[data-testid="pictures"] img[src]', { timeout: 20000 });
    await sleep(1500);
    await run.shot('bake_pictures', 'the Pictures tab: the game before and with the bake, and the lightmap page');
}

const failed = await run.finish('s6b_shots');
process.exit(failed > 0 ? 1 : 0);
