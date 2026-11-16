// The plan's section view (S5_BROWSER_EDITOR.md 3.4 "a section view (a vertical cut along a line the user draws)
// shows stacked levels, stairs and lift travel"; the design page's mock-nl-lift; S5b2): what a vertical cut along a line
// crosses, as spans along the line with their heights: rooms (floor and ceiling, a sloped floor's two ends), the floor
// parts at other heights (levels, platforms, treads: view.layout's `levels`), ceiling levels, and lifts, movers and
// plates with their travel. Pure; drawn by SectionView.ts.
import type { FileTrees, JsonObject, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import { objectBlocks } from '../edit/blocks.ts';
import { towardEdge } from '../edit/geometry.ts';
import { points } from '../edit/toolbase.ts';
import { roomsOf } from '../edit/ops.ts';
import { isObject } from '../edit/keys.ts';

export type Point = [number, number];

export interface SectionLine
{
    a: Point;
    b: Point;
}

export type SpanKind = 'room' | 'level' | 'ceiling' | 'lift' | 'mover' | 'plate';

export interface SectionSpan
{
    // What a click on it selects: the room (for its floor parts too), the lift, mover or plate.
    id: string;
    kind: SpanKind;
    // Along the line from `a`, map units.
    from: number;
    to: number;
    // Heights at `from` and at `to` (a sloped floor or ceiling differs).
    floor: number;
    floorTo: number;
    ceiling?: number;
    ceilingTo?: number;
    // A lift's rise or a mover's travel up (map units), its block's thickness, where the map starts it (0 or 1).
    travel?: number;
    thickness?: number;
    startsUp?: boolean;
}

// The stretches (as shares 0 to 1 of a to b) of the segment a-b inside a polygon.
export function insideStretches(outline: readonly (readonly number[])[], a: Point, b: Point): [number, number][]
{
    const shares: number[] = [0, 1];
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    for (let i = 0; i < outline.length; ++i)
    {
        const p = outline[i];
        const q = outline[(i + 1) % outline.length];
        const ex = q[0] - p[0];
        const ey = q[1] - p[1];
        const denominator = dx * ey - dy * ex;
        if (Math.abs(denominator) < 1e-9)
        {
            continue;
        }
        const t = ((p[0] - a[0]) * ey - (p[1] - a[1]) * ex) / denominator;
        const u = ((p[0] - a[0]) * dy - (p[1] - a[1]) * dx) / denominator;
        if (t > 0 && t < 1 && u >= 0 && u <= 1)
        {
            shares.push(t);
        }
    }
    shares.sort((x, y) => x - y);
    const out: [number, number][] = [];
    for (let i = 0; i + 1 < shares.length; ++i)
    {
        const [t0, t1] = [shares[i], shares[i + 1]];
        if (t1 - t0 < 1e-6)
        {
            continue;
        }
        const middle = (t0 + t1) / 2;
        if (inside(outline, [a[0] + dx * middle, a[1] + dy * middle]))
        {
            const last = out.at(-1);
            if (last && Math.abs(last[1] - t0) < 1e-6)
            {
                last[1] = t1;
            }
            else
            {
                out.push([t0, t1]);
            }
        }
    }
    return out;
}

function inside(outline: readonly (readonly number[])[], p: Point): boolean
{
    let result = false;
    for (let i = 0, j = outline.length - 1; i < outline.length; j = i++)
    {
        const [xi, yi] = outline[i];
        const [xj, yj] = outline[j];
        if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi)
        {
            result = !result;
        }
    }
    return result;
}

// A floor that rises toward a wall (the files' `slope.toward`): its height at a point, from `low` at the far side to
// `high` at that wall.
export function slopeHeight(outline: readonly (readonly number[])[], toward: unknown, low: number, high: number, p: Point): number
{
    const edge = towardEdge(outline, toward);
    if (edge < 0)
    {
        return low;
    }
    const a = outline[edge];
    const b = outline[(edge + 1) % outline.length];
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const distanceTo = (q: readonly number[]) => Math.abs((q[0] - a[0]) * (b[1] - a[1]) - (q[1] - a[1]) * (b[0] - a[0])) / length;
    const far = Math.max(...outline.map(distanceTo));
    const share = far > 0 ? 1 - distanceTo(p) / far : 1;
    return Math.round(low + (high - low) * Math.max(0, Math.min(1, share)));
}

// A cut along the long axis of a box of points, through its middle, reaching `margin` beyond it at each end.
export function longAxis(outline: readonly (readonly number[])[], margin = 512): SectionLine | null
{
    if (outline.length < 2)
    {
        return null;
    }
    const xs = outline.map((p) => p[0]);
    const ys = outline.map((p) => p[1]);
    const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
    const middle: Point = [Math.round((x0 + x1) / 2), Math.round((y0 + y1) / 2)];
    return x1 - x0 >= y1 - y0
        ? { a: [x0 - margin, middle[1]], b: [x1 + margin, middle[1]] }
        : { a: [middle[0], y0 - margin], b: [middle[0], y1 + margin] };
}

// Everything the cut crosses, rooms first (lowest floor first), then their floor parts, ceiling levels and blocks.
export function sectionSpans(layout: ViewLayoutResult | null, files: FileTrees | undefined, line: SectionLine): SectionSpan[]
{
    const { a, b } = line;
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (length < 1)
    {
        return [];
    }
    const at = (t: number): Point => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
    const fileRooms = new Map((files ? roomsOf(files) : []).map((room) => [String(room.id ?? ''), room]));
    const spans: SectionSpan[] = [];
    const floorOf = new Map<string, number>();
    for (const room of [...(layout?.rooms ?? [])].sort((x, y) => x.floor - y.floor))
    {
        floorOf.set(room.id, room.floor);
        const slope = fileRooms.get(room.id)?.slope as { toward?: unknown } | undefined;
        // An uneven roof (`ceiling_points`, a pyramid's): drawn flat at its highest point (the layout gives one height).
        const roofPoints = fileRooms.get(room.id)?.ceiling_points;
        const roof = Array.isArray(roofPoints) ? Math.max(room.ceiling, ...roofPoints.map((p) => (Array.isArray(p) && typeof p[2] === 'number' ? p[2] : room.ceiling))) : room.ceiling;
        for (const [t0, t1] of insideStretches(room.outline, a, b))
        {
            const heightAt = (t: number, low: number, high: number | undefined) => high === undefined || high === low ? low
                : slopeHeight(room.outline, slope?.toward, low, high, at(t));
            spans.push({ id: room.id, kind: 'room', from: t0 * length, to: t1 * length,
                floor: heightAt(t0, room.floor, room.floor_to), floorTo: heightAt(t1, room.floor, room.floor_to),
                ceiling: roof !== room.ceiling ? roof : heightAt(t0, room.ceiling, room.ceiling_to),
                ceilingTo: roof !== room.ceiling ? roof : heightAt(t1, room.ceiling, room.ceiling_to) });
        }
        for (const level of room.levels ?? [])
        {
            for (const [t0, t1] of insideStretches(level.outline, a, b))
            {
                spans.push({ id: room.id, kind: 'level', from: t0 * length, to: t1 * length, floor: level.height, floorTo: level.height,
                    ceiling: room.floor, ceilingTo: room.floor });
            }
        }
        const ceilings = fileRooms.get(room.id)?.ceiling_levels;
        for (const item of Array.isArray(ceilings) ? ceilings : [])
        {
            const outline = isObject(item) ? points(item.outline) : [];
            const height = isObject(item) ? Number(item.ceiling) : NaN;
            if (outline.length < 3 || !Number.isFinite(height))
            {
                continue;
            }
            for (const [t0, t1] of insideStretches(outline, a, b))
            {
                spans.push({ id: room.id, kind: 'ceiling', from: t0 * length, to: t1 * length, floor: room.ceiling, floorTo: room.ceiling,
                    ceiling: height, ceilingTo: height });
            }
        }
    }
    const items = new Map<string, JsonObject>();
    for (const list of ['lifts', 'movers', 'plates'])
    {
        const value = files?.['objects.yml']?.tree[list];
        for (const item of Array.isArray(value) ? value.filter(isObject) : [])
        {
            items.set(String(item.id ?? ''), item);
        }
    }
    for (const block of objectBlocks(files, layout))
    {
        if (block.list === 'ladders')
        {
            continue;
        }
        const item = items.get(block.id) ?? {};
        const floor = floorOf.get(block.room) ?? Number(fileRooms.get(block.room)?.floor ?? 0);
        for (const [t0, t1] of insideStretches(block.outline, a, b))
        {
            const span: SectionSpan = { id: block.id, kind: block.list === 'lifts' ? 'lift' : block.list === 'movers' ? 'mover' : 'plate',
                from: t0 * length, to: t1 * length, floor, floorTo: floor };
            if (block.list === 'lifts')
            {
                span.travel = typeof item.travel === 'number' ? item.travel : 256;
                span.thickness = typeof item.thickness === 'number' ? item.thickness : 32;
                span.startsUp = item.state === 'up';
            }
            else if (block.list === 'movers')
            {
                const bottom = floor + (typeof item.bottom === 'number' ? item.bottom : 0);
                const travel = Array.isArray(item.travel) && typeof item.travel[2] === 'number' ? item.travel[2] : 0;
                span.floor = bottom;
                span.floorTo = bottom;
                span.thickness = typeof item.height === 'number' ? item.height : 32;
                span.travel = travel;
                span.startsUp = item.state === 'end';
            }
            else
            {
                span.thickness = 8 + (typeof item.rise === 'number' ? item.rise : 0);
            }
            spans.push(span);
        }
    }
    return spans;
}

// The heights a section shows: from the lowest floor to the highest ceiling or lift top, and the distinct floors (the
// height bands' marks on its scale).
export function sectionRange(spans: readonly SectionSpan[]): { low: number; high: number; floors: number[] }
{
    if (spans.length === 0)
    {
        return { low: 0, high: 512, floors: [] };
    }
    let low = Infinity;
    let high = -Infinity;
    const floors = new Set<number>();
    for (const span of spans)
    {
        low = Math.min(low, span.floor, span.floorTo);
        high = Math.max(high, span.ceiling ?? span.floor, span.ceilingTo ?? span.floorTo, span.floor + (span.travel ?? 0) + (span.thickness ?? 0));
        if (span.kind === 'room' || span.kind === 'level')
        {
            floors.add(span.floor);
        }
    }
    return { low, high, floors: [...floors].sort((x, y) => x - y) };
}

// The span under a point of the section (along, height): the smallest that holds it, blocks before floor parts before
// rooms; or null.
export function spanAt(spans: readonly SectionSpan[], along: number, height: number, reach: number): SectionSpan | null
{
    const rank: Record<SpanKind, number> = { lift: 0, mover: 0, plate: 1, level: 2, ceiling: 2, room: 3 };
    let best: SectionSpan | null = null;
    for (const span of spans)
    {
        if (along < span.from - reach || along > span.to + reach)
        {
            continue;
        }
        const share = span.to > span.from ? Math.max(0, Math.min(1, (along - span.from) / (span.to - span.from))) : 0;
        const floor = span.floor + (span.floorTo - span.floor) * share;
        let top = span.ceiling !== undefined ? span.ceiling + ((span.ceilingTo ?? span.ceiling) - span.ceiling) * share : floor;
        let bottom = Math.min(floor, top);
        top = Math.max(floor, top);
        if (span.kind === 'lift' || span.kind === 'mover' || span.kind === 'plate')
        {
            bottom = floor - (span.kind === 'lift' ? span.thickness ?? 32 : 0);
            top = floor + Math.max(span.travel ?? 0, 0) + (span.kind === 'lift' ? 0 : span.thickness ?? 8);
        }
        if (height >= bottom - reach && height <= top + reach && (!best || rank[span.kind] < rank[best.kind]
            || (rank[span.kind] === rank[best.kind] && span.to - span.from < best.to - best.from)))
        {
            best = span;
        }
    }
    return best;
}
