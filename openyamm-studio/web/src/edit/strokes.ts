// The brushes' pure work (S5_BROWSER_EDITOR.md 3.18 "Land by hand", D15 extended): a sculpt stroke gathered node by
// node while the pointer moves, turned on pointer-up into one block of `heights.strokes` (differences in steps of
// 32, `~` outside the brush) or a keyed patch of the rows of a block that already holds it; a smooth or flatten
// stroke's outline (the nodes it covered, traced); the ground brush's painted cells per kind of land traced back
// into zone outlines. Nothing here draws or sends.
import type { JsonValue, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import { NODES, insideOrOn } from './cells.ts';
import { keysOf, segment } from './keys.ts';

export const STROKE_UNIT = 32;

// The nodes a person may sculpt: inside a patch (each node with its half cell round it), or every node when the
// land is marked made by hand.
export function sculptMask(patches: readonly (readonly Point[])[], handMade: boolean, size = NODES): Uint8Array
{
    const mask = new Uint8Array(size * size);
    if (handMade)
    {
        mask.fill(1);
        return mask;
    }
    for (const patch of patches)
    {
        if (patch.length < 3)
        {
            continue;
        }
        const xs = patch.map((p) => p[0]);
        const ys = patch.map((p) => p[1]);
        for (let y = Math.max(0, Math.floor(Math.min(...ys))); y <= Math.min(size - 1, Math.ceil(Math.max(...ys))); ++y)
        {
            for (let x = Math.max(0, Math.floor(Math.min(...xs))); x <= Math.min(size - 1, Math.ceil(Math.max(...xs))); ++x)
            {
                // The node's whole half cell: so a smooth outline round it stays inside the patch too.
                if ([[-0.5, -0.5], [0.5, -0.5], [0.5, 0.5], [-0.5, 0.5]].every(([dx, dy]) => insideOrOn([x + dx, y + dy], patch, 1e-6)))
                {
                    mask[y * size + x] = 1;
                }
            }
        }
    }
    return mask;
}

export type BrushMode = 'raise' | 'lower' | 'smooth' | 'flatten';

// One stroke while it is drawn: the dabs along the pointer's path, what they covered and (raise and lower) by how
// much, in map units, node by node.
export class Stroke
{
    readonly size: number;
    readonly mode: BrushMode;
    readonly radius: number;
    readonly strength: number;
    readonly allowed: Uint8Array;
    // Map units per node (raise, lower).
    readonly delta: Float32Array;
    // The nodes the brush passed over (inside the allowed nodes).
    readonly covered: Uint8Array;
    private last: Point | null = null;

    constructor(mode: BrushMode, radius: number, strength: number, allowed: Uint8Array, size = NODES)
    {
        this.size = size;
        this.mode = mode;
        this.radius = Math.max(0.5, radius);
        this.strength = strength;
        this.allowed = allowed;
        this.delta = new Float32Array(size * size);
        this.covered = new Uint8Array(size * size);
    }

    // The pointer at a node point (fractions allowed): dabs every third of the radius since the last.
    to(at: Point): void
    {
        if (!this.last)
        {
            this.dab(at);
            this.last = at;
            return;
        }
        const spacing = Math.max(0.5, this.radius / 3);
        const length = Math.hypot(at[0] - this.last[0], at[1] - this.last[1]);
        const steps = Math.floor(length / spacing);
        for (let i = 1; i <= steps; ++i)
        {
            const t = (i * spacing) / length;
            this.dab([this.last[0] + (at[0] - this.last[0]) * t, this.last[1] + (at[1] - this.last[1]) * t]);
        }
        if (steps > 0)
        {
            const t = (steps * spacing) / length;
            this.last = [this.last[0] + (at[0] - this.last[0]) * t, this.last[1] + (at[1] - this.last[1]) * t];
        }
    }

    private dab(at: Point): void
    {
        const r = this.radius;
        const sign = this.mode === 'lower' ? -1 : 1;
        for (let y = Math.max(0, Math.floor(at[1] - r)); y <= Math.min(this.size - 1, Math.ceil(at[1] + r)); ++y)
        {
            for (let x = Math.max(0, Math.floor(at[0] - r)); x <= Math.min(this.size - 1, Math.ceil(at[0] + r)); ++x)
            {
                const index = y * this.size + x;
                const d = Math.hypot(x - at[0], y - at[1]) / r;
                if (d > 1 || !this.allowed[index])
                {
                    continue;
                }
                this.covered[index] = 1;
                if (this.mode === 'raise' || this.mode === 'lower')
                {
                    const fall = (1 - d * d) * (1 - d * d);
                    this.delta[index] += sign * this.strength * fall;
                }
            }
        }
    }

    empty(): boolean
    {
        return !this.covered.some((value) => value !== 0);
    }
}

// What a raise or lower stroke writes: the block of nodes it changed (by at least half a step), in steps of `unit`,
// null where it changed nothing.
export interface StrokeBlock
{
    at: Point;
    rows: (number | null)[][];
}

export function strokeBlock(delta: Float32Array, size = NODES, unit = STROKE_UNIT): StrokeBlock | null
{
    let x0 = size;
    let y0 = size;
    let x1 = -1;
    let y1 = -1;
    const steps = new Int32Array(size * size);
    for (let index = 0; index < size * size; ++index)
    {
        const value = Math.round(delta[index] / unit);
        if (value !== 0)
        {
            steps[index] = value;
            const x = index % size;
            const y = Math.floor(index / size);
            x0 = Math.min(x0, x);
            x1 = Math.max(x1, x);
            y0 = Math.min(y0, y);
            y1 = Math.max(y1, y);
        }
    }
    if (x1 < 0)
    {
        return null;
    }
    const rows: (number | null)[][] = [];
    for (let y = y0; y <= y1; ++y)
    {
        const row: (number | null)[] = [];
        for (let x = x0; x <= x1; ++x)
        {
            const value = steps[y * size + x];
            row.push(value === 0 ? null : value);
        }
        rows.push(row);
    }
    return { at: [x0, y0], rows };
}

// A stroke block of the sketch as written ({key, at, unit, rows}).
export interface WrittenBlock
{
    key?: string;
    at: number[];
    unit?: number;
    rows: (number | null)[][];
}

// The operations' patch steps that write a new stroke block into sketch.yml: rows added to the existing block that
// covers it whole (a keyed patch of its rows, each with a test of the row it replaces), else a new block appended
// (the core gives its key). `blocks` is heights.strokes as written (absent: none yet).
export function strokePatch(block: StrokeBlock, blocks: readonly WrittenBlock[] | undefined, unit = STROKE_UNIT): PatchStep[]
{
    const width = block.rows[0]?.length ?? 0;
    const keys = blocks ? keysOf(blocks as unknown as JsonValue[], 'strokes', { field: 'key', prefix: 'stroke' }) : [];
    const index = (blocks ?? []).findIndex((written) => (written.unit ?? STROKE_UNIT) === unit && written.rows.length > 0
        && written.at[0] <= block.at[0] && written.at[1] <= block.at[1]
        && written.at[0] + Math.max(...written.rows.map((row) => row.length)) >= block.at[0] + width
        && written.at[1] + written.rows.length >= block.at[1] + block.rows.length);
    if (index >= 0)
    {
        const written = blocks![index];
        const base = `/heights/strokes/${segment(keys[index])}/rows`;
        const steps: PatchStep[] = [];
        block.rows.forEach((row, r) =>
        {
            const y = block.at[1] - written.at[1] + r;
            const old = written.rows[y];
            const merged = [...old];
            row.forEach((value, c) =>
            {
                const x = block.at[0] - written.at[0] + c;
                while (merged.length <= x)
                {
                    merged.push(null);
                }
                if (value !== null)
                {
                    const sum = (merged[x] ?? 0) + value;
                    merged[x] = sum === 0 && merged[x] === null ? null : sum;
                }
            });
            if (JSON.stringify(merged) !== JSON.stringify(old))
            {
                steps.push({ op: 'test', path: `${base}/${y}`, value: old }, { op: 'replace', path: `${base}/${y}`, value: merged });
            }
        });
        return steps;
    }
    const value = { at: block.at, rows: block.rows, ...(unit !== STROKE_UNIT ? { unit } : {}) };
    return blocks ? [{ op: 'add', path: '/heights/strokes/-', value }] : [{ op: 'add', path: '/heights/strokes', value: [value] }];
}

// --- smoothing as the build does it (for the preview) ----------------------------------------------------------

// The land after a smooth stroke over `mask`: `passes` times, each masked node moved by `strength` toward the mean
// of the eight around it. Heights in map units, size x size row by row from the north.
export function smoothed(heights: Float32Array, mask: Uint8Array, strength: number, passes: number, size = NODES): Float32Array
{
    let current = Float32Array.from(heights);
    for (let pass = 0; pass < passes; ++pass)
    {
        const next = Float32Array.from(current);
        for (let y = 0; y < size; ++y)
        {
            for (let x = 0; x < size; ++x)
            {
                const index = y * size + x;
                if (!mask[index])
                {
                    continue;
                }
                let sum = 0;
                let count = 0;
                for (let dy = -1; dy <= 1; ++dy)
                {
                    for (let dx = -1; dx <= 1; ++dx)
                    {
                        const nx = x + dx;
                        const ny = y + dy;
                        if ((dx || dy) && nx >= 0 && ny >= 0 && nx < size && ny < size)
                        {
                            sum += current[ny * size + nx];
                            ++count;
                        }
                    }
                }
                next[index] = current[index] + strength * (sum / count - current[index]);
            }
        }
        current = next;
    }
    return current;
}

// --- masks traced into outlines -----------------------------------------------------------------------------

// The outlines of a mask of unit squares (square i, j spans [i + offset, i + offset + 1] across and down): one
// polygon per piece, its corners where its boundary turns, holes filled (a zone or an area has one outline).
// Pieces that touch only at a corner are traced apart.
export function traceMask(mask: Uint8Array, width: number, height: number, offset = 0): Point[][]
{
    const filled = (x: number, y: number) => x >= 0 && y >= 0 && x < width && y < height && mask[y * width + x] !== 0;
    // Directed boundary edges between the corners of the squares, the filled side on the right (x east, y south: a
    // clockwise walk on the screen), by their start corner.
    const edges = new Map<number, number[]>();
    const corner = (x: number, y: number) => y * (width + 1) + x;
    const add = (ax: number, ay: number, bx: number, by: number) =>
    {
        const from = corner(ax, ay);
        const list = edges.get(from);
        if (list)
        {
            list.push(corner(bx, by));
        }
        else
        {
            edges.set(from, [corner(bx, by)]);
        }
    };
    for (let y = 0; y < height; ++y)
    {
        for (let x = 0; x < width; ++x)
        {
            if (!filled(x, y))
            {
                continue;
            }
            if (!filled(x, y - 1))
            {
                add(x, y, x + 1, y);
            }
            if (!filled(x + 1, y))
            {
                add(x + 1, y, x + 1, y + 1);
            }
            if (!filled(x, y + 1))
            {
                add(x + 1, y + 1, x, y + 1);
            }
            if (!filled(x - 1, y))
            {
                add(x, y + 1, x, y);
            }
        }
    }
    const xy = (c: number): Point => [c % (width + 1), Math.floor(c / (width + 1))];
    const loops: Point[][] = [];
    while (edges.size > 0)
    {
        const [start, targets] = edges.entries().next().value as [number, number[]];
        let from = start;
        let to = targets[0];
        const loop: Point[] = [xy(start)];
        const take = (a: number, b: number) =>
        {
            const list = edges.get(a)!;
            list.splice(list.indexOf(b), 1);
            if (list.length === 0)
            {
                edges.delete(a);
            }
        };
        take(from, to);
        for (let guard = 0; guard < 4 * (width + 1) * (height + 1) && to !== start; ++guard)
        {
            loop.push(xy(to));
            const next = edges.get(to);
            if (!next || next.length === 0)
            {
                break;
            }
            let chosen = next[0];
            if (next.length > 1)
            {
                // Two pieces meet at this corner only: turn right (toward the filled side) so each is traced apart.
                const [fx, fy] = xy(from);
                const [tx, ty] = xy(to);
                const dir: Point = [tx - fx, ty - fy];
                chosen = next.find((candidate) =>
                {
                    const [cx, cy] = xy(candidate);
                    return dir[0] * (cy - ty) - dir[1] * (cx - tx) > 0;
                }) ?? next[0];
            }
            take(to, chosen);
            from = to;
            to = chosen;
        }
        loops.push(simplify(loop));
    }
    // Outer outlines run clockwise on the screen (positive area in x east, y south); holes the other way.
    return loops.filter((loop) => area(loop) > 0).map((loop) => loop.map((p) => [p[0] + offset, p[1] + offset] as Point));
}

function area(loop: readonly Point[]): number
{
    let sum = 0;
    for (let i = 0; i < loop.length; ++i)
    {
        const a = loop[i];
        const b = loop[(i + 1) % loop.length];
        sum += a[0] * b[1] - b[0] * a[1];
    }
    return sum / 2;
}

// Corners where the outline does not turn are left out.
function simplify(loop: readonly Point[]): Point[]
{
    const out: Point[] = [];
    for (let i = 0; i < loop.length; ++i)
    {
        const a = loop[(i + loop.length - 1) % loop.length];
        const b = loop[i];
        const c = loop[(i + 1) % loop.length];
        if ((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]) !== 0)
        {
            out.push(b);
        }
    }
    return out;
}

// The cells (unit squares [x, x + 1] x [y, y + 1]) whose middles lie inside a polygon (in cells).
export function rasterise(polygon: readonly (readonly number[])[], mask: Uint8Array, size: number, value = 1): void
{
    if (polygon.length < 3)
    {
        return;
    }
    const ys = polygon.map((p) => p[1]);
    const xs = polygon.map((p) => p[0]);
    for (let y = Math.max(0, Math.floor(Math.min(...ys))); y < Math.min(size, Math.ceil(Math.max(...ys))); ++y)
    {
        for (let x = Math.max(0, Math.floor(Math.min(...xs))); x < Math.min(size, Math.ceil(Math.max(...xs))); ++x)
        {
            if (insideOrOn([x + 0.5, y + 0.5], polygon, 0))
            {
                mask[y * size + x] = value;
            }
        }
    }
}

// The cells a round brush covers at a cell point.
export function paintDisc(mask: Uint8Array, size: number, at: readonly number[], radius: number, value: number): void
{
    for (let y = Math.max(0, Math.floor(at[1] - radius)); y < Math.min(size, Math.ceil(at[1] + radius)); ++y)
    {
        for (let x = Math.max(0, Math.floor(at[0] - radius)); x < Math.min(size, Math.ceil(at[0] + radius)); ++x)
        {
            if (Math.hypot(x + 0.5 - at[0], y + 0.5 - at[1]) <= radius)
            {
                mask[y * size + x] = value;
            }
        }
    }
}
