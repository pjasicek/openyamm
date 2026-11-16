// The hosted page's own pieces (S5c): the read-only file system over packages (zip directories, ZIP64-free stored
// and deflated entries, read by range), the install's layout (a player's index of packs, the single packages, a
// development tree), and the pairing address.
import { describe, expect, it } from 'vitest';
import { zipSync } from 'three/examples/jsm/libs/fflate.module.js';
import { EntryReader, addZip, findEntry, isDir, newDir, readZipDirectory } from './packfs.ts';
import type { ByteSource, FileEntry } from './packfs.ts';
import { openInstall } from './install.ts';
import { parsePairing } from './pairing.ts';

function source(bytes: Uint8Array): ByteSource & { reads: number }
{
    const counted = {
        size: bytes.length, mtime: 0, reads: 0,
        read(offset: number, length: number)
        {
            counted.reads += 1;
            return bytes.slice(offset, offset + length);
        },
    };
    return counted;
}

const text = (value: string) => new TextEncoder().encode(value);

describe('packfs', () =>
{
    const big = new Uint8Array(300000).map((_, index) => (index * 7) & 0xff);
    const zip = zipSync({
        'data_tables/decoration_data.txt': [text('row one\nrow two\n'.repeat(500)), { level: 9 }],
        'textures_x4/wall.oytex': [big, { level: 0 }],
        'empty/': new Uint8Array(0),
    });

    it('reads a zip\'s central directory without the folders', () =>
    {
        const records = readZipDirectory(source(zip));
        expect(records.map((record) => record.name).sort()).toEqual(['data_tables/decoration_data.txt', 'textures_x4/wall.oytex']);
        expect(records.find((record) => record.name.endsWith('.oytex'))!.method).toBe(0);
        expect(records.find((record) => record.name.endsWith('.txt'))!.method).toBe(8);
    });

    it('puts entries under their mount and reads stored ones by range, deflated ones whole once', () =>
    {
        const tree = newDir();
        const bytes = source(zip);
        expect(addZip(tree, bytes, '/engine')).toBe(2);
        const table = findEntry(tree, 'engine/data_tables/decoration_data.txt') as FileEntry;
        const texture = findEntry(tree, 'engine/textures_x4/wall.oytex') as FileEntry;
        expect(isDir(findEntry(tree, 'engine/data_tables')!)).toBe(true);
        const reader = new EntryReader(1 << 20);
        expect(new TextDecoder().decode(reader.read(table, 0, 16))).toBe('row one\nrow two\n');
        const before = bytes.reads;
        reader.read(table, 16, 16);
        expect(bytes.reads).toBe(before);
        expect(reader.stats.inflated).toBe(1);
        // A stored entry: the bytes at a position, read ahead within the entry.
        expect(Array.from(reader.read(texture, 299990, 20))).toEqual(Array.from(big.subarray(299990)));
        expect(Array.from(reader.read(texture, 1000, 8))).toEqual(Array.from(big.subarray(1000, 1008)));
        expect(reader.readAll(texture).length).toBe(big.length);
    });
});

describe('install', () =>
{
    const pack = (files: Record<string, string>) => zipSync(Object.fromEntries(Object.entries(files).map(([name, value]) => [name, text(value)])));

    it('opens a player\'s install by its current release\'s index, leaving language packs out', () =>
    {
        const engine = pack({ 'data_tables/map_stats.txt': 'stats' });
        const world = pack({ '6d01.blv': 'map' });
        const index = JSON.stringify({ release: '2.0', store: '../../assets/packs', packs: [
            { id: 'engine.core', package: 'engine', mount: '/engine', file: 'engine.core-1.zip', size: engine.length },
            { id: 'mm6.maps', package: 'mm6', mount: '/worlds/mm6/maps', file: 'mm6.maps-1.zip', size: world.length },
            { id: 'lang-de.engine', package: 'engine', mount: '/engine', file: 'lang-de-1.zip', size: 5, language: 'de' },
        ] });
        const opened = openInstall([
            { path: 'app/current', source: source(text('2.0\n')) },
            { path: 'app/2.0/index.json', source: source(text(index)) },
            { path: 'assets/packs/engine.core-1.zip', source: source(engine) },
            { path: 'assets/packs/mm6.maps-1.zip', source: source(world) },
        ]);
        expect(opened.kind).toBe('install');
        expect(opened.release).toBe('2.0');
        expect(opened.packages).toBe(2);
        expect(opened.worlds).toEqual(['mm6']);
        expect(findEntry(opened.tree, 'worlds/mm6/maps/6d01.blv')).toBeDefined();
        expect(findEntry(opened.tree, 'engine/data_tables/map_stats.txt')).toBeDefined();
    });

    it('refuses an install with a pack missing or of the wrong size, as the game does', () =>
    {
        const engine = pack({ 'a.txt': 'a' });
        const index = (size: number) => JSON.stringify({ store: 'packs', packs: [{ id: 'e', package: 'engine', mount: '/engine', file: 'e.zip', size }] });
        expect(() => openInstall([{ path: 'index.json', source: source(text(index(engine.length))) }])).toThrow(/missing the content pack/);
        expect(() => openInstall([{ path: 'index.json', source: source(text(index(engine.length + 1))) }, { path: 'packs/e.zip', source: source(engine) }]))
            .toThrow(/wrong size/);
    });

    it('opens the single packages and a development tree picked one folder up', () =>
    {
        const packages = openInstall([
            { path: 'assets/engine.zip', source: source(pack({ 'data_tables/x.txt': 'x' })) },
            { path: 'assets/worlds/mm7.zip', source: source(pack({ 'maps/7d06.blv': 'm' })) },
        ]);
        expect(packages.kind).toBe('packages');
        expect(findEntry(packages.tree, 'worlds/mm7/maps/7d06.blv')).toBeDefined();
        const tree = openInstall([
            { path: 'assets_dev/engine/data_tables/x.txt', source: source(text('x')) },
            { path: 'assets_dev/worlds/mm6/maps/6d01.blv', source: source(text('m')) },
        ]);
        expect(tree.kind).toBe('tree');
        expect(findEntry(tree.tree, 'engine/data_tables/x.txt')).toBeDefined();
        expect(() => openInstall([{ path: 'notes.txt', source: source(text('x')) }])).toThrow(/not the game's files/);
    });
});

describe('pairing', () =>
{
    it('takes the address the studio prints, or a port and a token', () =>
    {
        expect(parsePairing('http://127.0.0.1:8765/#token=Ab_c-1')).toEqual({ port: 8765, token: 'Ab_c-1' });
        expect(parsePairing(' 9001 abc ')).toEqual({ port: 9001, token: 'abc' });
        expect(parsePairing('https://example.com:8765/#token=x')).toBeNull();
        expect(parsePairing('http://127.0.0.1:8765/?token=x')).toBeNull();
    });
});
