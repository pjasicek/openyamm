import { describe, expect, it } from 'vitest';
import { Codec, HEADER_BYTES, levelSizes, lowLevel, parseTexture } from './oytex.ts';

function header(codec: number, width: number, height: number, levels: number): ArrayBuffer
{
    const sizes = levelSizes({ codec, width, height, levels });
    const total = HEADER_BYTES + sizes.reduce((sum, size) => sum + size.bytes, 0);
    const bytes = new ArrayBuffer(total);
    const view = new DataView(bytes);
    view.setBigUint64(2 * 8, BigInt(codec), true);
    view.setBigUint64(5 * 8, BigInt(width), true);
    view.setBigUint64(6 * 8, BigInt(height), true);
    view.setBigUint64(7 * 8, BigInt(levels), true);
    return bytes;
}

describe('.oytex levels', () =>
{
    it('sizes BC7 and BC1 levels down to one block', () =>
    {
        const sizes = levelSizes({ codec: Codec.Bc7, width: 512, height: 256, levels: 10 });
        expect(sizes[0]).toEqual({ width: 512, height: 256, bytes: 128 * 64 * 16 });
        expect(sizes[8]).toEqual({ width: 2, height: 1, bytes: 16 });
        expect(levelSizes({ codec: Codec.Bc1, width: 8, height: 8, levels: 1 })[0].bytes).toBe(4 * 8);
    });

    it('finds the 32-texel level for the low pass', () =>
    {
        expect(lowLevel({ width: 512, height: 512, levels: 10 })).toBe(4);
        expect(lowLevel({ width: 16, height: 16, levels: 5 })).toBe(0);
    });

    it('parses a body that starts at a later level', () =>
    {
        const full = header(Codec.Bc7, 64, 64, 7);
        const parsed = parseTexture(full, 0, 4);
        expect(parsed.mips.map((m) => m.width)).toEqual([64, 32, 16, 8, 4, 2, 1]);
        const sizes = levelSizes(parsed.header);
        const tail = new Uint8Array(HEADER_BYTES + sizes.slice(3).reduce((s, l) => s + l.bytes, 0));
        tail.set(new Uint8Array(full, 0, HEADER_BYTES));
        const low = parseTexture(tail.buffer, 3, 4);
        expect(low.mips.map((m) => m.level)).toEqual([3, 4, 5, 6]);
        expect(low.scale).toBe(4);
    });
});
