// Face textures for the browser (S5_BROWSER_EDITOR.md 2.11): the cooked `.oytex` files of the asset root (and of a
// mount in front of it), un-framed by the host so that the browser uploads block-compressed mips as they are and
// local mode does not depend on the WebAssembly core.
//
// A .oytex file (engine/render/CookedTexture.h, version 3) is a 120-byte header of fifteen little-endian u64 fields
// (0 magic, 1 version, 2 codec, 3 semantic, 4 alpha cutoff, 5 width, 6 height, 7 levels, 8 source hash, 9 block
// bytes, 10 unused, 11 zstd bytes, 12 alpha use, 13 statistics, 14 content width | content height << 16) and one zstd
// frame holding every level's blocks, largest level first. The answer of /tex is that header unchanged followed by
// the blocks of the levels asked for (`from` to the last), so the browser can take the smallest mips first.
//
// Un-framing uses the asynchronous zlib.zstdDecompress (the synchronous form blocked the host up to 32 ms a file in
// spike 1). Bodies are kept in an LRU bounded by bytes; concurrent requests for one file share one decompression.
//
// The one frame holds the largest level first, so the low pass (the smallest levels, asked first) cannot be had
// without un-framing the whole file. So the store keeps the small levels of every texture it un-framed in a cache
// folder of its own (`cacheDir`: one small file per texture, named by a hash of the texture's path, size and time):
// the low pass of every later opening reads them without un-framing anything, and the full pass un-frames as before.
// A cache file is: "OYLC", the first level it holds (u32 LE), the texture's 120-byte header, the blocks from that
// level to the last.
import { createHash } from 'node:crypto';
import { mkdir, open, readFile, rename, stat, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { promisify } from 'node:util';
import zlib from 'node:zlib';

const zstdDecompress = promisify(zlib.zstdDecompress);
const HEADER_BYTES = 120;
const MAGIC = 0x313030584554594fn;

// Bytes of one 4x4 block by codec id (engine/render/TextureBlockCodec.h): BC4, EAC R, BC1 and ETC2 RGB take 8.
const BLOCK_BYTES = { 1: 16, 2: 8, 3: 16, 4: 16, 5: 8, 6: 16, 7: 8, 8: 8, 9: 16 };
const WORLDS = ['mm6', 'mm7', 'mm8', 'mm9'];
// The level from which the low cache keeps a texture's chain (the web app's low pass asks for level 4).
export const LOW_CACHE_LEVEL = 4;
const LOW_MAGIC = 0x434c594f; // "OYLC" little-endian

export function readTextureHeader(buffer) {
  if (buffer.length < HEADER_BYTES) throw new Error('not a cooked texture (too short)');
  const field = (index) => buffer.readBigUInt64LE(index * 8);
  if (field(0) !== MAGIC) throw new Error('not a cooked texture (no OYTEX001 signature)');
  const packed = field(14);
  return {
    version: Number(field(1)), codec: Number(field(2)), width: Number(field(5)), height: Number(field(6)),
    levels: Number(field(7)), blockBytes: Number(field(9)), zstdBytes: Number(field(11)),
    contentWidth: Number(packed & 0xffffn), contentHeight: Number((packed >> 16n) & 0xffffn),
  };
}

// Byte size of each mip level, largest first.
export function levelSizes(header) {
  const block = BLOCK_BYTES[header.codec];
  if (!block) throw new Error(`unknown texture codec ${header.codec}`);
  const sizes = [];
  for (let level = 0; level < header.levels; ++level) {
    const width = Math.max(1, header.width >> level);
    const height = Math.max(1, header.height >> level);
    sizes.push(Math.ceil(width / 4) * Math.ceil(height / 4) * block);
  }
  return sizes;
}

export class TextureStore {
  // `roots`: folders that hold worlds/ and engine/, searched in order (a mount, then the asset root).
  constructor(roots, { budgetBytes = 256 * 1024 * 1024, cacheDir = null } = {}) {
    this.roots = roots.filter(Boolean);
    this.cacheDir = cacheDir;
    this.budget = budgetBytes;
    this.used = 0;
    this.bodies = new Map(); // key -> {header, blocks, sizes}; Map order is the LRU order (oldest first)
    this.pending = new Map();
    this.found = new Map(); // world/name -> {file, scale} | null
    this.stats = { unframed: 0, hits: 0, zstdMs: 0, lowHits: 0, lowWritten: 0 };
  }

  // The folders a name is looked for in, in order: the world's own, then the other worlds', then the engine's.
  folders(world) {
    const list = [];
    for (const root of this.roots) {
      const worlds = [world, ...WORLDS.filter((other) => other !== world)];
      for (const each of worlds) {
        list.push({ dir: path.join(root, 'worlds', each, 'textures_x4'), scale: 4 });
        list.push({ dir: path.join(root, 'worlds', each, 'textures'), scale: 1 });
      }
      list.push({ dir: path.join(root, 'engine', 'textures_x4'), scale: 4 });
      list.push({ dir: path.join(root, 'engine', 'textures'), scale: 1 });
    }
    return list;
  }

  async find(world, name) {
    const key = `${world}/${name}`;
    if (this.found.has(key)) return this.found.get(key);
    let hit = null;
    for (const folder of this.folders(world)) {
      const file = path.join(folder.dir, `${name}.oytex`);
      try {
        const info = await stat(file);
        if (info.isFile()) {
          hit = { file, scale: folder.scale };
          break;
        }
      } catch {
        // not in this folder
      }
    }
    // Only hits are kept: a texture added to the mount later is found on its next request.
    if (hit) this.found.set(key, hit);
    return hit;
  }

  // Whether the store holds a texture's un-framed blocks now (by its path, any version).
  inMemory(file) {
    for (const key of this.bodies.keys()) {
      if (key.startsWith(`${file}|`)) return true;
    }
    return false;
  }

  async unframe(file) {
    const info = await stat(file);
    const key = `${file}|${info.mtimeMs}|${info.size}`;
    const kept = this.bodies.get(key);
    if (kept) {
      this.bodies.delete(key);
      this.bodies.set(key, kept);
      this.stats.hits += 1;
      return kept;
    }
    if (this.pending.has(key)) return this.pending.get(key);
    const work = (async () => {
      const handle = await open(file, 'r');
      let bytes;
      try {
        bytes = await handle.readFile();
      } finally {
        await handle.close();
      }
      const header = readTextureHeader(bytes);
      if (header.version !== 3) throw new Error(`cooked texture version ${header.version}, not 3`);
      const started = performance.now();
      const blocks = await zstdDecompress(bytes.subarray(HEADER_BYTES));
      this.stats.zstdMs += performance.now() - started;
      this.stats.unframed += 1;
      const sizes = levelSizes(header);
      const total = sizes.reduce((sum, size) => sum + size, 0);
      if (blocks.length !== header.blockBytes || total !== header.blockBytes) {
        throw new Error(`${path.basename(file)}: blocks ${blocks.length}, header ${header.blockBytes}, levels ${total}`);
      }
      const body = { headerBytes: bytes.subarray(0, HEADER_BYTES), header, blocks, sizes };
      void this.writeLow(file, info, body);
      this.bodies.set(key, body);
      this.used += blocks.length + HEADER_BYTES;
      for (const [oldKey, old] of this.bodies) {
        if (this.used <= this.budget || oldKey === key) break;
        this.bodies.delete(oldKey);
        this.used -= old.blocks.length + HEADER_BYTES;
      }
      return body;
    })();
    this.pending.set(key, work);
    try {
      return await work;
    } finally {
      this.pending.delete(key);
    }
  }

  lowCacheFile(file, info) {
    const key = createHash('sha256').update(`${file}|${info.size}|${info.mtimeMs}`).digest('hex').slice(0, 32);
    return path.join(this.cacheDir, key.slice(0, 2), `${key}.lowmip`);
  }

  // The kept small levels of a texture, when the cache holds them from `from` or a larger level: {headerBytes,
  // header, first, blocks (from `first`), sizes}; null otherwise.
  async readLow(file, from) {
    if (!this.cacheDir) return null;
    let bytes;
    try {
      bytes = await readFile(this.lowCacheFile(file, await stat(file)));
    } catch {
      return null;
    }
    if (bytes.length < 8 + HEADER_BYTES || bytes.readUInt32LE(0) !== LOW_MAGIC) return null;
    const first = bytes.readUInt32LE(4);
    if (first > from) return null;
    const headerBytes = bytes.subarray(8, 8 + HEADER_BYTES);
    const header = readTextureHeader(headerBytes);
    const sizes = levelSizes(header);
    const blocks = bytes.subarray(8 + HEADER_BYTES);
    if (blocks.length !== sizes.slice(first).reduce((sum, size) => sum + size, 0)) return null;
    return { headerBytes, header, first, blocks, sizes };
  }

  // Writes the small levels of an un-framed texture into the cache (once; errors are ignored: it is a cache).
  async writeLow(file, info, body) {
    if (!this.cacheDir) return;
    const first = Math.min(LOW_CACHE_LEVEL, body.header.levels - 1);
    const target = this.lowCacheFile(file, info);
    try {
      await stat(target);
      return;
    } catch {
      // not kept yet
    }
    const skip = body.sizes.slice(0, first).reduce((sum, size) => sum + size, 0);
    const head = Buffer.alloc(8);
    head.writeUInt32LE(LOW_MAGIC, 0);
    head.writeUInt32LE(first, 4);
    try {
      await mkdir(path.dirname(target), { recursive: true });
      const temporary = `${target}.${process.pid}.tmp`;
      await writeFile(temporary, Buffer.concat([head, body.headerBytes, body.blocks.subarray(skip)]));
      await rename(temporary, target);
      this.stats.lowWritten += 1;
    } catch {
      // a cache that cannot be written is only slower
    }
  }

  // {status, headers, body} for /tex/<world>/<name>?from=<level>.
  async answer(world, name, from) {
    if (!/^mm[0-9]$/.test(world) || !/^[a-z0-9_\-.]+$/.test(name) || name.includes('..')) {
      return { status: 404, body: 'no texture of that name' };
    }
    const hit = await this.find(world, name);
    if (!hit) return { status: 404, body: 'no texture of that name' };
    const headers = (scale, level, levels) => ({
      'Content-Type': 'application/octet-stream',
      'Cache-Control': 'private, max-age=3600',
      'X-Texture-Scale': String(scale),
      'X-Texture-From': String(level),
      'X-Texture-Levels': String(levels),
    });
    // The low pass: from the cache, without un-framing, unless the texture is in memory already.
    const asked = Number.isInteger(from) ? from : 0;
    if (asked > 0 && !this.inMemory(hit.file)) {
      const low = await this.readLow(hit.file, asked);
      if (low) {
        const level = Math.max(low.first, Math.min(asked, low.header.levels - 1));
        const skip = low.sizes.slice(low.first, level).reduce((sum, size) => sum + size, 0);
        this.stats.lowHits += 1;
        return { status: 200, headers: headers(hit.scale, level, low.header.levels),
          body: Buffer.concat([low.headerBytes, low.blocks.subarray(skip)]) };
      }
    }
    const body = await this.unframe(hit.file);
    const level = Math.max(0, Math.min(asked, body.header.levels - 1));
    const skip = body.sizes.slice(0, level).reduce((sum, size) => sum + size, 0);
    return {
      status: 200,
      headers: {
        'Content-Type': 'application/octet-stream',
        'Cache-Control': 'private, max-age=3600',
        'X-Texture-Scale': String(hit.scale),
        'X-Texture-From': String(level),
        'X-Texture-Levels': String(body.header.levels),
      },
      body: Buffer.concat([body.headerBytes, body.blocks.subarray(skip)]),
    };
  }
}
