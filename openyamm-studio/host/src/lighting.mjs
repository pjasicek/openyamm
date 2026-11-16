// Lighting bakes as jobs (devdocs/map_studio/S6_PLAN.md 2.9; S5_BROWSER_EDITOR.md 6.3, "later, not jobs in S5"): the
// bake tools of the repository (tools/lighting/bake_indoor.py, bake_outdoor.py; devdocs/INDOOR_BAKED_LIGHTING.md,
// tools/lighting/baked_outdoors/README.md) run by the host on a project's build, local only, and their result shown as
// pictures: the sidecar's lightmap pages, and the game's view of the map before and after the bake.
//
// The bakes read the map from an asset tree by name (the indoor one through the game's
// --headless-export-indoor-bake-scene, which reads no extra mount), so the job makes a scratch tree of its own: a
// hard-link copy of the asset root (`cp -al`, as the MM9 scratch builds), the build installed into it with `oymap
// install --root` (which writes by rename, so no file of the asset root changes), the sidecar copied in beside the
// map for the "after" picture. The tree is removed when the job ends. Nothing is written into the asset root.
//
// This file: the sidecar's pages read back (both families: OYILIT1 indoor, OYMLIT1 outdoor; RLE spans of BGRM texels,
// light = RGB * M * 4), a page drawn as a PNG, and the profiles a job bakes with.
import { deflateSync } from 'node:zlib';

const INDOOR_MAGIC = 'OYILIT1\0';
const OUTDOOR_MAGIC = 'OYMLIT1\0';

// The pages of a .lighting sidecar: {family: 'indoor' | 'outdoor', version, pages: [{width, height, texels}]}, the
// texels BGRM bytes, rows bottom-up as baked. Throws on a file that is not one.
export function readLightingPages(bytes) {
  const buffer = Buffer.from(bytes);
  if (buffer.length < 64) throw new Error('the sidecar is shorter than its header');
  const magic = buffer.subarray(0, 8).toString('latin1');
  const family = magic === INDOOR_MAGIC ? 'indoor' : magic === OUTDOOR_MAGIC ? 'outdoor' : null;
  if (!family) throw new Error('not a lighting sidecar (its magic is neither OYILIT1 nor OYMLIT1)');
  const version = buffer.readUInt32LE(8);
  const pageCount = buffer.readUInt32LE(32);
  // Indoor: the page records' offset at 40; outdoor: at 48 (FORMAT.md).
  const recordOffset = buffer.readUInt32LE(family === 'indoor' ? 40 : 48);
  const pages = [];
  for (let page = 0; page < pageCount; ++page) {
    const record = recordOffset + page * 16;
    if (record + 16 > buffer.length) throw new Error('the page records run past the file');
    const width = buffer.readUInt32LE(record);
    const height = buffer.readUInt32LE(record + 4);
    const offset = buffer.readUInt32LE(record + 8);
    const size = buffer.readUInt32LE(record + 12);
    if (offset + size > buffer.length) throw new Error(`page ${page} runs past the file`);
    pages.push({ width, height, texels: decodeSpans(buffer.subarray(offset, offset + size), width * height) });
  }
  return { family, version, pages };
}

// The RLE of the bakes (bake_geometry.py rle_bgra): a tag byte, its low seven bits the span's length less one; the
// high bit set repeats the next texel, clear copies that many texels.
export function decodeSpans(data, texelCount) {
  const out = Buffer.alloc(texelCount * 4);
  let at = 0;
  let written = 0;
  while (at < data.length) {
    const tag = data[at++];
    const count = (tag & 0x7f) + 1;
    if (written + count > texelCount) throw new Error('a span runs past the page');
    if (tag & 0x80) {
      for (let index = 0; index < count; ++index) data.copy(out, (written + index) * 4, at, at + 4);
      at += 4;
    } else {
      data.copy(out, written * 4, at, at + count * 4);
      at += count * 4;
    }
    written += count;
  }
  if (written !== texelCount) throw new Error(`the page has ${written} texels of ${texelCount}`);
  return out;
}

// The encoder, for tests and fixtures: BGRM texels as spans (the bakes' rule: runs of two or more repeat).
export function encodeSpans(texels) {
  const parts = [];
  const count = texels.length / 4;
  const same = (a, b) => texels.readUInt32LE(a * 4) === texels.readUInt32LE(b * 4);
  let index = 0;
  while (index < count) {
    let run = 1;
    while (run < 128 && index + run < count && same(index, index + run)) run += 1;
    if (run >= 2) {
      parts.push(Buffer.from([0x80 | (run - 1)]), texels.subarray(index * 4, index * 4 + 4));
      index += run;
      continue;
    }
    const start = index;
    index += 1;
    while (index - start < 128 && index < count && !(index + 1 < count && same(index, index + 1))) index += 1;
    parts.push(Buffer.from([index - start - 1]), texels.subarray(start * 4, index * 4));
  }
  return Buffer.concat(parts);
}

// A page as a picture: the light (RGB * M * 4, in the renderer's units: 1 lights a texture as it is, the shader
// clamps at 2) shown with 2 as white, gamma 2.2, rows top-down; texels no chart covers (M = 0) dark grey. Also the
// page's mean light over its covered texels.
export function pagePicture(page) {
  const { width, height, texels } = page;
  const rgb = Buffer.alloc(width * height * 3);
  let sum = 0;
  let covered = 0;
  for (let y = 0; y < height; ++y) {
    // Bottom-up as baked: the picture's first row is the page's last.
    const source = (height - 1 - y) * width;
    for (let x = 0; x < width; ++x) {
      const texel = (source + x) * 4;
      const m = texels[texel + 3];
      const out = (y * width + x) * 3;
      if (m === 0) {
        rgb[out] = rgb[out + 1] = rgb[out + 2] = 40;
        continue;
      }
      const scale = (m * 4) / 255 / 255;
      // B, G, R in the file.
      const light = [texels[texel + 2] * scale, texels[texel + 1] * scale, texels[texel] * scale];
      sum += (light[0] + light[1] + light[2]) / 3;
      covered += 1;
      for (let channel = 0; channel < 3; ++channel) {
        rgb[out + channel] = Math.round(Math.min(1, light[channel] / 2) ** (1 / 2.2) * 255);
      }
    }
  }
  return { png: encodePng(width, height, rgb), mean: covered ? sum / covered : 0, covered };
}

// --- PNG (RGB, 8 bits) ------------------------------------------------------------------------------------------

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let n = 0; n < 256; ++n) {
    let c = n;
    for (let k = 0; k < 8; ++k) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    table[n] = c >>> 0;
  }
  return table;
})();

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) crc = CRC_TABLE[(crc ^ byte) & 0xff] ^ (crc >>> 8);
  return (crc ^ 0xffffffff) >>> 0;
}

function chunk(type, data) {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length);
  const body = Buffer.concat([Buffer.from(type, 'latin1'), data]);
  const crc = Buffer.alloc(4);
  crc.writeUInt32BE(crc32(body));
  return Buffer.concat([length, body, crc]);
}

export function encodePng(width, height, rgb) {
  const header = Buffer.alloc(13);
  header.writeUInt32BE(width, 0);
  header.writeUInt32BE(height, 4);
  header[8] = 8;
  header[9] = 2;
  const rows = Buffer.alloc((width * 3 + 1) * height);
  for (let y = 0; y < height; ++y) {
    rows[y * (width * 3 + 1)] = 0;
    rgb.copy(rows, y * (width * 3 + 1) + 1, y * width * 3, (y + 1) * width * 3);
  }
  return Buffer.concat([Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]), chunk('IHDR', header),
    chunk('IDAT', deflateSync(rows)), chunk('IEND', Buffer.alloc(0))]);
}

// --- profiles ---------------------------------------------------------------------------------------------------

// The indoor profile of a job: the producer's defaults (bake_indoor.py load_profile) with the map, a page size that
// suits a new dungeon and the job's samples and texel spacing.
export function indoorProfile({ world, map, samples = 32, unitsPerTexel = 16 }) {
  return { world, map, samples, units_per_texel: unitsPerTexel, page_size: 1024 };
}

// The outdoor profile of a job: the shipped New Sorpigal profile's sun and sky (an outdoor profile needs every key:
// baked_outdoors/README.md) with the map and the job's samples; terrain and building pages at a draft's size.
export function outdoorProfile(base, { world, map, samples = 32 }) {
  return { ...base, world, map, samples, terrain_size: Math.min(base.terrain_size ?? 1024, 512),
    building_page_size: Math.min(base.building_page_size ?? 1024, 1024) };
}

// --- the game's pictures ----------------------------------------------------------------------------------------

function insidePolygon([x, y], outline) {
  let inside = false;
  for (let i = 0, j = outline.length - 1; i < outline.length; j = i++) {
    const [xi, yi] = outline[i];
    const [xj, yj] = outline[j];
    if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) inside = !inside;
  }
  return inside;
}

// Where the job's before and after pictures look from (view.layout's answer): from the party's start (a place the
// map is known to hold), toward the farthest corner of the start's room so the picture spans the room, a little down;
// outdoors the start as it faces. {position: [x, y, z] (the party's feet), yaw (radians), pitch (degrees)}, or null
// without a start.
export function overviewPose(layout) {
  const start = layout?.start;
  if (!start || !Array.isArray(start.at)) return null;
  const [sx, sy, sz] = start.at;
  const room = (layout.rooms ?? []).find((entry) => Array.isArray(entry.outline) && entry.outline.length >= 3
    && insidePolygon([sx, sy], entry.outline));
  if (!room) return { position: [sx, sy, sz], yaw: (start.facing * Math.PI) / 180, pitch: -8 };
  const far = room.outline.reduce((best, point) => (Math.hypot(point[0] - sx, point[1] - sy) > Math.hypot(best[0] - sx, best[1] - sy) ? point : best));
  return { position: [sx, sy, sz], yaw: Math.atan2(far[1] - sy, far[0] - sx), pitch: -6 };
}

// The console lines of a picture: the HUD off, a cinematic on arrival skipped, the party set at the pose.
export function shotConsole(pose) {
  return ['render hud off', 'cinematic skip',
    ...(pose ? [`tp ${pose.position.map((value) => value.toFixed(3)).join(' ')} ${pose.yaw.toFixed(4)} ${pose.pitch.toFixed(3)}`] : [])]
    .join('\n') + '\n';
}
