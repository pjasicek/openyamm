// The game's cooked texture container (.oytex, version 3) as the host serves it (S5_BROWSER_EDITOR.md 2.11): the
// 120-byte header (15 little-endian u64) and the block-compressed mips, largest first, un-framed by the host. With
// `?from=<level>` the host sends the header and only the levels from that one down. No three.js here.

// engine/render/TextureBlockCodec.h
export const Codec = { Bc7: 1, Bc4: 2, Bc5: 3, Bc1: 7 } as const;
export type CodecNumber = (typeof Codec)[keyof typeof Codec];

const BLOCK_BYTES: Record<number, number> = { [Codec.Bc7]: 16, [Codec.Bc4]: 8, [Codec.Bc5]: 16, [Codec.Bc1]: 8 };

export interface OytexHeader
{
    codec: number;
    semantic: number;
    width: number;
    height: number;
    levels: number;
    alphaUse: number;
    contentWidth: number;
    contentHeight: number;
}

export interface MipLevel
{
    level: number;
    width: number;
    height: number;
    data: Uint8Array;
}

export interface ParsedTexture
{
    header: OytexHeader;
    // The levels in the body, from `firstLevel` down.
    firstLevel: number;
    mips: MipLevel[];
    // Map units per texel of the picture: the game's logical size is width / scale (textures_x4: scale 4).
    scale: number;
}

export const HEADER_BYTES = 120;

export function blockBytes(codec: number): number
{
    const bytes = BLOCK_BYTES[codec];
    if (bytes === undefined)
    {
        throw new Error(`unknown texture codec ${codec}`);
    }
    return bytes;
}

export function readHeader(view: DataView): OytexHeader
{
    const field = (index: number) => Number(view.getBigUint64(index * 8, true));
    const content = field(14);
    return {
        codec: field(2),
        semantic: field(3),
        width: field(5),
        height: field(6),
        levels: field(7),
        alphaUse: field(12),
        contentWidth: content & 0xffff,
        contentHeight: (content >>> 16) & 0xffff,
    };
}

// The size of each level (width, height, bytes), largest first.
export function levelSizes(header: Pick<OytexHeader, 'codec' | 'width' | 'height' | 'levels'>): { width: number; height: number; bytes: number }[]
{
    const block = blockBytes(header.codec);
    const sizes = [];
    for (let level = 0; level < header.levels; ++level)
    {
        const width = Math.max(1, header.width >> level);
        const height = Math.max(1, header.height >> level);
        sizes.push({ width, height, bytes: Math.ceil(width / 4) * Math.ceil(height / 4) * block });
    }
    return sizes;
}

// The first level whose larger side is at most `side` texels (the last level when none is): what "lowest mips
// first" fetches before the rest.
export function lowLevel(header: Pick<OytexHeader, 'width' | 'height' | 'levels'>, side = 32): number
{
    let level = 0;
    while (level + 1 < header.levels && Math.max(header.width >> level, header.height >> level) > side)
    {
        ++level;
    }
    return level;
}

export function parseTexture(bytes: ArrayBuffer, firstLevel: number, scale: number): ParsedTexture
{
    const header = readHeader(new DataView(bytes, 0, HEADER_BYTES));
    const sizes = levelSizes(header);
    const mips: MipLevel[] = [];
    let offset = HEADER_BYTES;
    for (let level = firstLevel; level < header.levels; ++level)
    {
        const size = sizes[level];
        if (offset + size.bytes > bytes.byteLength)
        {
            throw new Error(`texture body ends at level ${level} (${bytes.byteLength} bytes)`);
        }
        mips.push({ level, width: size.width, height: size.height, data: new Uint8Array(bytes, offset, size.bytes) });
        offset += size.bytes;
    }
    return { header, firstLevel, mips, scale };
}
