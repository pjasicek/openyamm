// Lighting bakes as jobs (S6: src/lighting.mjs, the lighting_bake job of src/jobs.mjs): a sidecar's pages read back
// in both families (the indoor OYILIT1 and outdoor OYMLIT1 headers, the bakes' RLE spans of BGRM texels), a page drawn
// as a PNG (the light as RGB * M * 4, bottom-up rows turned over, uncharted texels dark), the job's params and
// profiles, and its refusals (no Blender, an overlay project). With LIGHTING_BAKE=<project folder> it also runs a real
// bake of a copy of that project through the job (Blender, the game; about a minute), LIGHTING_BAKE_OUT=<folder> keeping
// its pictures.
//   node test/lighting.test.mjs
import assert from 'node:assert/strict';
import { cpSync, existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { inflateSync } from 'node:zlib';
import { fileURLToPath } from 'node:url';
import { Jobs, jobParamsProblem, resultLine } from '../src/jobs.mjs';
import { decodeSpans, encodePng, encodeSpans, indoorProfile, outdoorProfile, overviewPose, pagePicture, readLightingPages, shotConsole } from '../src/lighting.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const studio = path.resolve(here, '../..');
const repo = path.resolve(studio, '..');

// --- spans ----------------------------------------------------------------------------------------------------------
// A 4 x 2 page: a run of three equal texels, then five different ones (B, G, R, M).
const texels = Buffer.from([
  10, 20, 30, 64, 10, 20, 30, 64, 10, 20, 30, 64, 0, 0, 0, 0,
  255, 255, 255, 255, 1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 9]);
const spans = encodeSpans(texels);
// One repeat span (tag 0x82: three texels) and one literal span of five.
assert.equal(spans[0], 0x82);
assert.equal(spans[5], 4);
assert.equal(spans.length, 1 + 4 + 1 + 5 * 4);
assert.deepEqual(decodeSpans(spans, 8), texels);
assert.throws(() => decodeSpans(spans, 7), /runs past the page/);
assert.throws(() => decodeSpans(spans, 9), /8 texels of 9/);

// --- sidecars of both families ------------------------------------------------------------------------------------
function sidecar(magic, recordOffsetAt, pages) {
  const header = Buffer.alloc(magic === 'OYILIT1\0' ? 64 : 96);
  header.write(magic, 0, 'latin1');
  header.writeUInt32LE(magic === 'OYILIT1\0' ? 1 : 5, 8);
  header.writeUInt32LE(header.length, 12);
  header.writeUInt32LE(pages.length, 32);
  header.writeUInt32LE(header.length, recordOffsetAt);
  const records = Buffer.alloc(16 * pages.length);
  const payloads = pages.map((page) => encodeSpans(page.texels));
  let cursor = header.length + records.length;
  pages.forEach((page, index) => {
    records.writeUInt32LE(page.width, index * 16);
    records.writeUInt32LE(page.height, index * 16 + 4);
    records.writeUInt32LE(cursor, index * 16 + 8);
    records.writeUInt32LE(payloads[index].length, index * 16 + 12);
    cursor += payloads[index].length;
  });
  return Buffer.concat([header, records, ...payloads]);
}

const indoor = readLightingPages(sidecar('OYILIT1\0', 40, [{ width: 4, height: 2, texels }]));
assert.equal(indoor.family, 'indoor');
assert.equal(indoor.version, 1);
assert.equal(indoor.pages.length, 1);
assert.deepEqual(indoor.pages[0].texels, texels);
const outdoor = readLightingPages(sidecar('OYMLIT1\0', 48, [{ width: 4, height: 2, texels }, { width: 4, height: 2, texels }]));
assert.equal(outdoor.family, 'outdoor');
assert.equal(outdoor.pages.length, 2);
assert.throws(() => readLightingPages(Buffer.alloc(80)), /neither OYILIT1 nor OYMLIT1/);
assert.throws(() => readLightingPages(Buffer.alloc(8)), /shorter than its header/);

// --- a page as a picture ----------------------------------------------------------------------------------------
const drawn = pagePicture(indoor.pages[0]);
assert.deepEqual([...drawn.png.subarray(0, 8)], [0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
assert.equal(drawn.png.readUInt32BE(16), 4);
assert.equal(drawn.png.readUInt32BE(20), 2);
// Seven charted texels (M > 0); the mean light of the first: (30, 20, 10) * 64 * 4 / 255 / 255 averaged.
assert.equal(drawn.covered, 7);
// The rows turned over: the picture's first row is the page's second (bottom-up), whose first texel is white light 4.
const idat = drawn.png.indexOf('IDAT');
const rows = inflateSync(drawn.png.subarray(idat + 4, idat + 4 + drawn.png.readUInt32BE(idat - 4)));
assert.equal(rows[0], 0);
assert.deepEqual([...rows.subarray(1, 4)], [255, 255, 255]);
// The second row's last texel is uncharted (M = 0): dark grey.
assert.deepEqual([...rows.subarray(13 + 1 + 9, 13 + 1 + 12)], [40, 40, 40]);
assert.equal(encodePng(1, 1, Buffer.from([1, 2, 3])).length > 50, true);

// --- the job's params, profiles and line ----------------------------------------------------------------------
assert.equal(jobParamsProblem({ samples: 16, units_per_texel: 24 }), null);
assert.match(jobParamsProblem({ samples: 0 }), /samples is not of its form/);
assert.match(jobParamsProblem({ units_per_texel: 2.5 }), /units_per_texel is not of its form/);
assert.deepEqual(indoorProfile({ world: 'mm6', map: 'studio06.blv', samples: 16 }),
  { world: 'mm6', map: 'studio06.blv', samples: 16, units_per_texel: 16, page_size: 1024 });
const shipped = JSON.parse(readFileSync(path.join(repo, 'tools/lighting/baked_outdoors/profiles/mm6_oute3.yml'), 'utf8'));
const draft = outdoorProfile(shipped, { world: 'mm6', map: 'calib_newsorpigal.odm', samples: 16 });
assert.equal(draft.map, 'calib_newsorpigal.odm');
assert.equal(draft.sun_energy, shipped.sun_energy);
assert.equal(draft.terrain_size, 512);
assert.equal(resultLine('lighting_bake', { pages: [{}, {}], report: { faces_lightmapped: 210, bake_seconds: 31.5 } }),
  '2 lightmap page(s), 210 faces lit in 31.5 s of Cycles');

// --- the pictures' pose ----------------------------------------------------------------------------------------
// A hall 1024 x 512 with the start near its south-west corner: from the start toward the far corner.
const pose = overviewPose({ start: { at: [100, 80, 0], facing: 90 }, rooms: [
  { id: 'room:other', outline: [[2000, 0], [3000, 0], [3000, 500], [2000, 500]], floor: 64 },
  { id: 'room:hall', outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]], floor: 0 }] });
assert.deepEqual(pose.position, [100, 80, 0]);
assert.ok(Math.abs(pose.yaw - Math.atan2(512 - 80, 1024 - 100)) < 1e-9);
assert.equal(pose.pitch, -6);
// Outdoors (no room): the start as it faces.
assert.deepEqual(overviewPose({ start: { at: [5, 6, 7], facing: 180 } }), { position: [5, 6, 7], yaw: Math.PI, pitch: -8 });
assert.equal(overviewPose({}), null);
assert.equal(shotConsole({ position: [1, 2, 3], yaw: 1.5, pitch: -12 }), 'render hud off\ncinematic skip\ntp 1.000 2.000 3.000 1.5000 -12.000\n');
assert.equal(shotConsole(null), 'render hud off\ncinematic skip\n');

// --- refusals: no Blender; an overlay project ------------------------------------------------------------------
const scratch = mkdtempSync(path.join(tmpdir(), 'oymap-lighting-'));
const fakeCore = { call: async (method) => (method === 'project.status' ? { result: { revision: 'r'.repeat(32) } } : { error: { message: 'no' } }), kill: () => undefined };
const context = (overrides) => ({ coreJ: fakeCore, coreI: fakeCore, repo, assets: path.join(repo, 'assets_dev'), game: process.execPath,
  oymap: process.execPath, folderOf: () => scratch, infoOf: () => ({ kind: 'indoor', world: 'mm6', reference: '', base: '' }),
  mountOf: () => path.join(scratch, 'mount'), ...overrides });
const without = new Jobs(context({ blender: path.join(scratch, 'no-blender') }));
assert.match((await without.start('p', 'lighting_bake', {})).error, /no .*no-blender .*local mode only/);
// A stand-in Blender that answers --version: the job starts, and an overlay is refused when it runs.
const standIn = path.join(scratch, 'blender.sh');
writeFileSync(standIn, '#!/bin/sh\necho Blender 0.0\n', { mode: 0o755 });
const overlayJobs = new Jobs(context({ blender: standIn, infoOf: () => ({ kind: 'indoor', world: 'mm6', reference: '', base: '6d01.blv' }) }));
const queued = await overlayJobs.start('p', 'lighting_bake', { samples: 8 });
assert.ok(queued.job, queued.error);
while (overlayJobs.jobs.has(queued.job.id)) await new Promise((resolve) => setTimeout(resolve, 20));
const refused = overlayJobs.status('p', queued.job.id);
assert.equal(refused.state, 'failed');
assert.match(refused.error, /overlay project .* keeps its base's bake/);
rmSync(scratch, { recursive: true, force: true });

// --- a real bake (opt-in) ---------------------------------------------------------------------------------------
if (process.env.LIGHTING_BAKE) {
  const { Core } = await import('../src/core.mjs');
  const { readCard, readOriginal } = await import('../src/projects.mjs');
  const work = mkdtempSync(path.join(tmpdir(), 'oymap-bake-'));
  const folder = path.join(work, 'project');
  cpSync(path.resolve(process.env.LIGHTING_BAKE), folder, { recursive: true, filter: (source) => !/\/(\.oymap|build)(\/|$)/.test(source) });
  const assets = path.join(repo, 'assets_dev');
  const oymap = process.env.OYMAP ?? path.join(studio, 'build-s4/oymap');
  const coreI = new Core(oymap, { assets });
  const coreJ = new Core(oymap, { assets });
  const jobs = new Jobs({ coreI, coreJ, repo, assets, game: path.join(repo, 'build/game/openyamm'), oymap,
    folderOf: () => folder, infoOf: () => ({ ...readCard(path.join(folder, 'project.yml')), ...readOriginal(path.join(folder, 'project.yml')) }),
    // The scratch copy goes where the host puts it (output/studio_host/bake_roots): hard links need the asset root's disk.
    mountOf: () => path.join(work, 'mount'), runGame: path.join(repo, 'tools/run_game.sh') });
  const started = await jobs.start('p', 'lighting_bake', { samples: 16 });
  assert.ok(started.job, started.error);
  while (jobs.jobs.has(started.job.id)) await new Promise((resolve) => setTimeout(resolve, 500));
  const done = jobs.status('p', started.job.id);
  assert.equal(done.state, 'done', done.error ?? '');
  assert.ok(done.result.pages.length >= 1);
  assert.ok(done.result.pages.every((page) => existsSync(path.join(folder, '.oymap/jobs', done.revision, done.id, page.picture))));
  // The scratch copy is gone.
  assert.equal(existsSync(path.join(repo, 'output/studio_host/bake_roots', done.id)), false);
  const pictures = path.join(folder, '.oymap/jobs', done.revision, done.id, 'pictures');
  // LIGHTING_BAKE_OUT=<folder> keeps the pictures (the work folder goes).
  if (process.env.LIGHTING_BAKE_OUT) cpSync(pictures, path.resolve(process.env.LIGHTING_BAKE_OUT), { recursive: true });
  console.log(`lighting: a real bake: ${resultLine('lighting_bake', done.result)}; pictures ${done.pictures.join(', ')}`);
  coreI.kill();
  coreJ.kill();
  rmSync(work, { recursive: true, force: true });
}

console.log('lighting: all checks passed');
