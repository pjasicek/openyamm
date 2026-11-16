// Writes the panel gallery's fixed data (src/gallery/fixtures/) from the example project gatehouse_cellars through
// the core's request list (`oymap call`). view.layout is taken from the core when it answers it, else made from the
// rooms' outlines as written. Run again when the formats change:  node scripts/make-fixtures.mjs [<oymap>]
import { execFileSync } from 'node:child_process';
import { writeFileSync } from 'node:fs';
import { join } from 'node:path';

const studio = join(import.meta.dirname, '..', '..');
const oymap = process.argv[2] ?? join(studio, 'build-s4', 'oymap');
const project = 'examples/gatehouse_cellars';
const out = join(import.meta.dirname, '..', 'src', 'gallery', 'fixtures');
// `oymap call` exits 1 on a refusal and still prints the answer.
const call = (method, params) =>
{
    try
    {
        return JSON.parse(execFileSync(oymap, ['call', method, JSON.stringify(params)], { cwd: studio, encoding: 'utf8' }));
    }
    catch (error)
    {
        return JSON.parse(error.stdout);
    }
};

const opened = call('project.open', { project });
if (!opened.result)
{
    throw new Error(JSON.stringify(opened.error));
}
const result = opened.result;
writeFileSync(join(out, 'project_open.json'), JSON.stringify(result));
const validate = call('check.validate', { project });
writeFileSync(join(out, 'validate.json'), JSON.stringify(validate.result ?? { ok: true, with_assets: false, issues: [], notes: [] }));

// With the asset root the core lowers the example (its decorations need the decoration table) and answers view.layout
// with openings and doors (the flow graph's fixture needs them).
let layout = (() =>
{
    try
    {
        return JSON.parse(execFileSync(oymap, ['call', 'view.layout', JSON.stringify({ project }), '--assets', join(studio, '..', 'assets_dev')],
            { cwd: studio, encoding: 'utf8' })).result;
    }
    catch
    {
        return call('view.layout', { project }).result;
    }
})();
if (!layout)
{
    const rooms = result.files['rooms.yml'].tree.rooms;
    const objects = result.files['objects.yml']?.tree ?? {};
    const things = [];
    for (const [list, kind] of [['lights', 'light'], ['chests', 'chest'], ['spawns', 'spawn'], ['decorations', 'decoration']])
    {
        for (const item of objects[list] ?? [])
        {
            const room = rooms.find((r) => r.id === item.room);
            if (!room)
            {
                continue;
            }
            const xs = room.outline.map((p) => p[0]);
            const ys = room.outline.map((p) => p[1]);
            const centre = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
            const offset = item.offset ?? item.at ?? [0, 0];
            things.push({ id: item.id, kind, at: [Math.round(centre[0] + (offset[0] ?? 0)), Math.round(centre[1] + (offset[1] ?? 0)), room.floor] });
        }
    }
    const xs = rooms.flatMap((r) => r.outline.map((p) => p[0]));
    const ys = rooms.flatMap((r) => r.outline.map((p) => p[1]));
    layout = {
        revision: result.revision, view_revision: result.revision, stale: false, kind: 'indoor', world: 'mm6',
        bounds: { min: [Math.min(...xs), Math.min(...ys), 0], max: [Math.max(...xs), Math.max(...ys), 512] },
        rooms: rooms.filter((r) => r.outline).map((r, i) => ({ id: r.id, sector: i + 1, outline: r.outline, floor: r.floor ?? 0, ceiling: r.ceiling ?? 384 })),
        openings: [], doors: [], lifts: [], things,
    };
    console.log('view.layout not answered: made from the outlines');
}
writeFileSync(join(out, 'layout.json'), JSON.stringify(layout));

// S5a5's scorecard, flow graph and Compare: the example's checks (audit, reach and solve) and its compare with
// Goblinwatch (its card's reference), read with the asset root; the Python checks' answers from their scripts.
const assets = join(studio, '..', 'assets_dev');
const withAssets = (method, params) =>
{
    try
    {
        return JSON.parse(execFileSync(oymap, ['call', method, JSON.stringify(params), '--assets', assets], { cwd: studio, encoding: 'utf8' }));
    }
    catch (error)
    {
        return JSON.parse(error.stdout);
    }
};
const absolute = join(studio, project);
const checks = withAssets('check.audit', { map: absolute, reach: true, solve: true });
const compare = withAssets('compare.run', { map: absolute });
if (checks.result && compare.result)
{
    // The full report is long and the panels do not read it: kept short.
    compare.result.report = { totals: compare.result.report.totals };
    writeFileSync(join(out, 'jobs_checks.json'), JSON.stringify(checks.result));
    writeFileSync(join(out, 'jobs_compare.json'), JSON.stringify(compare.result));
}
else
{
    console.log(`checks or compare not answered (no asset root?): ${JSON.stringify(checks.error ?? compare.error)}`);
}
const python = (script, args) => JSON.parse(execFileSync('python3', [join(studio, 'calibration', script), ...args],
    { cwd: studio, encoding: 'utf8', env: { ...process.env, OYMAP: oymap } }));
try
{
    writeFileSync(join(out, 'jobs_scale_bands.json'), JSON.stringify(python('scale_bands.py', [absolute, '--json', '--assets', assets])));
}
catch (error)
{
    // scale_bands exits 1 when a figure is below the 25th percentile: its answer is still on its output.
    writeFileSync(join(out, 'jobs_scale_bands.json'), JSON.stringify(JSON.parse(error.stdout)));
}
console.log(`wrote ${out}`);
