// Texture loading for the 3D view (S5_BROWSER_EDITOR.md 2.11): lowest mips first. Every texture's small levels are
// fetched and uploaded before any larger one, the view is drawn textured, then the full chains replace them. Bytes
// come through the RPC client's own fetch (with the token).
import { parseTexture } from './oytex.ts';
import type { ParsedTexture } from './oytex.ts';

export interface TextureSink
{
    setTexture(name: string, parsed: ParsedTexture): void;
}

export interface TextureFetcher
{
    fetchBytes(path: string): Promise<{ bytes: ArrayBuffer; headers: Headers }>;
}

export interface TextureLoadReport
{
    names: number;
    low: { ok: number; failed: string[]; ms: number; bytes: number };
    full: { ok: number; failed: string[]; ms: number; bytes: number };
}

// The level the low pass asks for: textures_x4 pictures are 4 x their logical size, so level 4 is a 32-texel mip
// of a 128-texel picture (the host answers the header and the levels from that one down).
export const LOW_LEVEL = 4;

async function pool<T>(items: T[], width: number, work: (item: T) => Promise<void>): Promise<void>
{
    let next = 0;
    await Promise.all(Array.from({ length: Math.min(width, items.length) }, async () =>
    {
        while (next < items.length)
        {
            await work(items[next++]);
        }
    }));
}

export function textureUrl(world: string, name: string, from?: number): string
{
    return `/tex/${encodeURIComponent(world)}/${encodeURIComponent(name)}${from !== undefined ? `?from=${from}` : ''}`;
}

export async function fetchTexture(fetcher: TextureFetcher, world: string, name: string, from?: number): Promise<{ parsed: ParsedTexture; bytes: number }>
{
    const { bytes, headers } = await fetcher.fetchBytes(textureUrl(world, name, from));
    const scale = Number(headers.get('X-Texture-Scale') ?? '1') || 1;
    const first = Number(headers.get('X-Texture-From') ?? String(from ?? 0)) || 0;
    return { parsed: parseTexture(bytes, first, scale), bytes: bytes.byteLength };
}

// Loads every texture: the low pass, `onLow` (the caller draws), then the full pass. `isCurrent` stops the work
// when another mesh replaced this one.
export async function loadTextures(
    fetcher: TextureFetcher,
    sink: TextureSink,
    world: string,
    names: string[],
    onLow: () => void,
    isCurrent: () => boolean = () => true,
): Promise<TextureLoadReport>
{
    const report: TextureLoadReport = {
        names: names.length,
        low: { ok: 0, failed: [], ms: 0, bytes: 0 },
        full: { ok: 0, failed: [], ms: 0, bytes: 0 },
    };
    let start = performance.now();
    const missing = new Set<string>();
    await pool(names, 8, async (name) =>
    {
        try
        {
            let answer;
            try
            {
                answer = await fetchTexture(fetcher, world, name, LOW_LEVEL);
            }
            catch
            {
                // A texture with fewer levels than LOW_LEVEL: its whole chain is small anyway.
                answer = await fetchTexture(fetcher, world, name);
            }
            if (isCurrent())
            {
                sink.setTexture(name, answer.parsed);
            }
            report.low.ok += 1;
            report.low.bytes += answer.bytes;
        }
        catch
        {
            missing.add(name);
            report.low.failed.push(name);
        }
    });
    report.low.ms = performance.now() - start;
    if (!isCurrent())
    {
        return report;
    }
    onLow();
    start = performance.now();
    await pool(names.filter((name) => !missing.has(name)), 6, async (name) =>
    {
        try
        {
            const answer = await fetchTexture(fetcher, world, name);
            if (isCurrent())
            {
                sink.setTexture(name, answer.parsed);
            }
            report.full.ok += 1;
            report.full.bytes += answer.bytes;
        }
        catch
        {
            report.full.failed.push(name);
        }
    });
    report.full.ms = performance.now() - start;
    return report;
}
