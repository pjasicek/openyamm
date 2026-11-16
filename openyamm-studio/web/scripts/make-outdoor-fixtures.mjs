// Writes the panel gallery's outdoor fixtures (src/gallery/fixtures/outdoor_*.json) from an outdoor project (S5b2): its
// project.open and view.layout through the core's request list (the land's 128 x 128 heights included). The default
// project is the newest run of the hand-author exit test (scripts/s5b2_hand_author.mjs).
//   node scripts/make-outdoor-fixtures.mjs [<project folder>] [<oymap>]
import { execFileSync } from 'node:child_process';
import { readdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const studio = join(import.meta.dirname, '..', '..');
const repo = join(studio, '..');
const runs = join(repo, 'output', 's5b2_web', 'web', 'runs');
const newest = () => join(runs, readdirSync(runs).filter((name) => name.endsWith('-hand')).sort().at(-1), 'hollow_vale');
const project = process.argv[2] ?? newest();
const oymap = process.argv[3] ?? join(studio, 'build-s4', 'oymap');
const out = join(import.meta.dirname, '..', 'src', 'gallery', 'fixtures');
const call = (method, params) => JSON.parse(execFileSync(oymap, ['call', method, JSON.stringify(params), '--assets', join(repo, 'assets_dev')],
    { encoding: 'utf8', maxBuffer: 64 << 20 })).result;

const opened = call('project.open', { project });
writeFileSync(join(out, 'outdoor_open.json'), JSON.stringify(opened));
writeFileSync(join(out, 'outdoor_layout.json'), JSON.stringify(call('view.layout', { project })));
console.log(`outdoor fixtures from ${project}`);
