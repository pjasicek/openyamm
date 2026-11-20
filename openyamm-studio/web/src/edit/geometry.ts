// Plan geometry of the indoor tools (S5_BROWSER_EDITOR.md 3.4, 3.18): snapping to the grid, to other rooms' corners
// and walls and to 45-degree steps; the outline's winding; where an opening sits on the wall two rooms share (the
// core's own rule, IndoorLowering's wall pairs); which wall a slope climbs toward. Pure functions in map units
// (x east, y north).
import type { Point } from './ops.ts';

export type Outline = readonly (readonly number[])[];

export function signedArea(points: Outline): number
{
    let area = 0;
    for (let i = 0; i < points.length; ++i)
    {
        const [x1, y1] = points[i];
        const [x2, y2] = points[(i + 1) % points.length];
        area += x1 * y2 - x2 * y1;
    }
    return area / 2;
}

// Counter-clockwise, as rooms.yml wants outlines (the room on the left of each edge).
export function counterClockwise(points: readonly Point[]): Point[]
{
    return signedArea(points) < 0 ? [...points].reverse() : [...points];
}

export function roundTo(value: number, step: number): number
{
    return step > 0 ? Math.round(value / step) * step : Math.round(value);
}

export function distance(a: readonly number[], b: readonly number[]): number
{
    return Math.hypot(a[0] - b[0], a[1] - b[1]);
}

// The nearest point of a segment, and how far along it (0..1).
export function nearestOnSegment(p: readonly number[], a: readonly number[], b: readonly number[]): { point: Point; t: number; distance: number }
{
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const length = dx * dx + dy * dy;
    const t = length > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length)) : 0;
    const point: Point = [a[0] + dx * t, a[1] + dy * t];
    return { point, t, distance: distance(p, point) };
}

export interface SnapOptions
{
    grid: number;
    // The previous point of the drawing: without `free`, the new segment keeps to 45-degree steps from it.
    previous?: Point | null;
    // Shift: any angle (and no snapping to walls).
    free?: boolean;
    // Other rooms' outlines to snap to (their corners first, then their walls).
    outlines?: readonly Outline[];
    // How near counts, in map units (the caller turns pixels into units).
    reach: number;
}

export interface Snapped
{
    point: Point;
    to: 'corner' | 'wall' | 'angle' | 'grid' | 'free';
}

// Where a pointer at `p` puts a point.
export function snapPoint(p: readonly number[], options: SnapOptions): Snapped
{
    const outlines = options.outlines ?? [];
    if (!options.free)
    {
        let best: { point: Point; d: number } | null = null;
        for (const outline of outlines)
        {
            for (const corner of outline)
            {
                const d = distance(p, corner);
                if (d <= options.reach && (!best || d < best.d))
                {
                    best = { point: [corner[0], corner[1]], d };
                }
            }
        }
        if (best)
        {
            return { point: best.point, to: 'corner' };
        }
    }
    if (options.previous && !options.free)
    {
        // 45-degree steps from the previous point, the length on the grid.
        const [px, py] = options.previous;
        const angle = Math.atan2(p[1] - py, p[0] - px);
        const step = Math.round(angle / (Math.PI / 4)) * (Math.PI / 4);
        const ux = Math.round(Math.cos(step) * 1e6) / 1e6;
        const uy = Math.round(Math.sin(step) * 1e6) / 1e6;
        const along = (p[0] - px) * ux + (p[1] - py) * uy;
        if (ux !== 0 && uy !== 0)
        {
            const d = roundTo(along * Math.abs(ux), options.grid);
            return { point: [px + Math.sign(ux) * d, py + Math.sign(uy) * d], to: 'angle' };
        }
        const d = roundTo(along, options.grid);
        // On the grid across the step too: an axis step from an off-grid point keeps that point's line.
        return { point: [px + ux * d, py + uy * d], to: 'angle' };
    }
    if (!options.free)
    {
        let best: { point: Point; d: number } | null = null;
        for (const outline of outlines)
        {
            for (let i = 0; i < outline.length; ++i)
            {
                const a = outline[i];
                const b = outline[(i + 1) % outline.length];
                const near = nearestOnSegment(p, a, b);
                if (near.distance <= options.reach && (!best || near.distance < best.d))
                {
                    // Along an axis wall the point stays on the grid.
                    const point: Point = a[0] === b[0] ? [a[0], roundTo(p[1], options.grid)]
                        : a[1] === b[1] ? [roundTo(p[0], options.grid), a[1]] : [Math.round(near.point[0]), Math.round(near.point[1])];
                    best = { point, d: near.distance };
                }
            }
        }
        if (best)
        {
            return { point: best.point, to: 'wall' };
        }
        return { point: [roundTo(p[0], options.grid), roundTo(p[1], options.grid)], to: 'grid' };
    }
    return { point: [Math.round(p[0]), Math.round(p[1])], to: 'free' };
}

// A box from two corners (the drag of a box tool), counter-clockwise, and its centre and size.
export function box(a: readonly number[], b: readonly number[]): { outline: Point[]; at: Point; size: Point } | null
{
    const x0 = Math.min(a[0], b[0]);
    const x1 = Math.max(a[0], b[0]);
    const y0 = Math.min(a[1], b[1]);
    const y1 = Math.max(a[1], b[1]);
    if (x1 - x0 < 1 || y1 - y0 < 1)
    {
        return null;
    }
    return {
        outline: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
        at: [Math.round((x0 + x1) / 2), Math.round((y0 + y1) / 2)],
        size: [x1 - x0, y1 - y0],
    };
}

export function pointInPolygon(p: readonly number[], outline: Outline): boolean
{
    let inside = false;
    for (let i = 0, j = outline.length - 1; i < outline.length; j = i++)
    {
        const [xi, yi] = outline[i];
        const [xj, yj] = outline[j];
        if ((yi > p[1]) !== (yj > p[1]) && p[0] < ((xj - xi) * (p[1] - yi)) / (yj - yi) + xi)
        {
            inside = !inside;
        }
    }
    return inside;
}

// Whether a polygon's edges cross (a figure eight), which the core refuses ("crosses itself").
export function selfCrossing(points: readonly Point[]): boolean
{
    const n = points.length;
    const cross = (o: Point, a: Point, b: Point) => (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
    for (let i = 0; i < n; ++i)
    {
        for (let j = i + 1; j < n; ++j)
        {
            if (j === i + 1 || (i === 0 && j === n - 1))
            {
                continue;
            }
            const a = points[i];
            const b = points[(i + 1) % n];
            const c = points[j];
            const d = points[(j + 1) % n];
            const d1 = cross(c, d, a);
            const d2 = cross(c, d, b);
            const d3 = cross(a, b, c);
            const d4 = cross(a, b, d);
            if (((d1 > 0 && d2 < 0) || (d1 < 0 && d2 > 0)) && ((d3 > 0 && d4 < 0) || (d3 < 0 && d4 > 0)))
            {
                return true;
            }
        }
    }
    return false;
}

// A room's corridor outline for the plan from its path (a band `width` wide round the centre line, square ends):
// enough to hit test and to draw before the core's layout answers.
export function pathBand(path: readonly (readonly number[])[], width: number): Point[][]
{
    const half = width / 2;
    const out: Point[][] = [];
    for (let i = 0; i + 1 < path.length; ++i)
    {
        const [ax, ay] = path[i];
        const [bx, by] = path[i + 1];
        const length = Math.hypot(bx - ax, by - ay) || 1;
        const nx = (-(by - ay) / length) * half;
        const ny = ((bx - ax) / length) * half;
        out.push([[ax + nx, ay + ny], [ax - nx, ay - ny], [bx - nx, by - ny], [bx + nx, by + ny]]);
    }
    return out;
}

interface WallFrame
{
    origin: Point;
    along: Point;
    outward: Point;
    length: number;
}

function wallFrame(outline: Outline, edge: number): WallFrame
{
    const a = outline[edge];
    const b = outline[(edge + 1) % outline.length];
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const along: Point = [(b[0] - a[0]) / length, (b[1] - a[1]) / length];
    return { origin: [a[0], a[1]], along, outward: [along[1], -along[0]], length };
}

const MAXIMUM_WALL_THICKNESS = 512;

export interface WallPair
{
    fromEdge: number;
    toEdge: number;
    gap: number;
    // The shared stretch, measured along the `from` room's wall from its first corner.
    low: number;
    high: number;
}

// The pairs of facing walls two rooms share (counter-clockwise outlines), as the core finds them.
export function wallPairs(from: Outline, to: Outline): WallPair[]
{
    const pairs: WallPair[] = [];
    for (let fromEdge = 0; fromEdge < from.length; ++fromEdge)
    {
        const f = wallFrame(from, fromEdge);
        for (let toEdge = 0; toEdge < to.length; ++toEdge)
        {
            const t = wallFrame(to, toEdge);
            const facing = f.along[0] * t.along[0] + f.along[1] * t.along[1];
            if (facing > -1 + 1e-9)
            {
                continue;
            }
            const ox = t.origin[0] - f.origin[0];
            const oy = t.origin[1] - f.origin[1];
            const gap = ox * f.outward[0] + oy * f.outward[1];
            if (gap < -1e-6 || gap > MAXIMUM_WALL_THICKNESS)
            {
                continue;
            }
            const toStart = ox * f.along[0] + oy * f.along[1];
            const low = Math.max(0, toStart - t.length);
            const high = Math.min(f.length, toStart);
            if (high - low > 1e-6)
            {
                pairs.push({ fromEdge, toEdge, gap: Math.max(0, gap), low, high });
            }
        }
    }
    return pairs;
}

export interface OpeningPlace
{
    from_wall?: number;
    to_wall?: number;
    along: number;
    width: number;
    // The hole on the plan (in the `from` room's wall), for the ghost.
    a: Point;
    b: Point;
    // The whole shared stretch.
    shared: [Point, Point];
}

// Where an opening dragged across the gap between two rooms sits: the pair of facing walls the drag crosses (the
// pair nearest its middle), `along` from the drag's middle, the width kept 16 inside each end of the shared
// stretch as the core requires. A reason when the two rooms share no wall there.
export function openingPlace(from: Outline, to: Outline, start: readonly number[], end: readonly number[], width: number): OpeningPlace | { reason: string }
{
    const pairs = wallPairs(from, to);
    if (pairs.length === 0)
    {
        return { reason: 'the two rooms have no facing walls within 512 of each other (an opening joins two rooms across one wall)' };
    }
    const middle: Point = [(start[0] + end[0]) / 2, (start[1] + end[1]) / 2];
    let best: { pair: WallPair; s: number; miss: number } | null = null;
    for (const pair of pairs)
    {
        const f = wallFrame(from, pair.fromEdge);
        const s = (middle[0] - f.origin[0]) * f.along[0] + (middle[1] - f.origin[1]) * f.along[1];
        const t = (middle[0] - f.origin[0]) * f.outward[0] + (middle[1] - f.origin[1]) * f.outward[1];
        const miss = Math.max(0, pair.low - s, s - pair.high) + Math.max(0, -t - 64, t - pair.gap - 64);
        if (!best || miss < best.miss)
        {
            best = { pair, s, miss };
        }
    }
    const { pair, s } = best!;
    const longest = pairs.reduce((a, b) => (b.high - b.low > a.high - a.low + 1e-6 ? b : a));
    const shared = pair.high - pair.low;
    const fitted = Math.min(width, Math.max(0, shared - 32));
    if (fitted < 32)
    {
        return { reason: `the two rooms share only ${Math.round(shared)} units of wall there: too little for a doorway` };
    }
    const centre = Math.max(pair.low + 16 + fitted / 2, Math.min(pair.high - 16 - fitted / 2, s));
    const along = Math.round(((centre - pair.low) / shared) * 1000) / 1000;
    const f = wallFrame(from, pair.fromEdge);
    const at = (d: number): Point => [Math.round(f.origin[0] + f.along[0] * d), Math.round(f.origin[1] + f.along[1] * d)];
    const place: OpeningPlace = {
        along,
        width: Math.round(fitted),
        a: at(centre - fitted / 2),
        b: at(centre + fitted / 2),
        shared: [at(pair.low), at(pair.high)],
    };
    if (pair !== longest)
    {
        place.from_wall = pair.fromEdge;
        place.to_wall = pair.toEdge;
    }
    return place;
}

const COMPASS: [string, Point][] = [['east', [1, 0]], ['north', [0, 1]], ['west', [-1, 0]], ['south', [0, -1]]];

// The wall a floor climbs toward when dragged from `start` to `end` across a room: the wall whose outside faces the
// drag's direction best, named by compass side when it faces one squarely, else by its edge number.
export function slopeToward(outline: Outline, start: readonly number[], end: readonly number[]): string | number | null
{
    const dx = end[0] - start[0];
    const dy = end[1] - start[1];
    const length = Math.hypot(dx, dy);
    if (length < 1 || outline.length < 3)
    {
        return null;
    }
    let best = 0;
    let bestFit = -2;
    for (let edge = 0; edge < outline.length; ++edge)
    {
        const f = wallFrame(outline, edge);
        const fit = (f.outward[0] * dx + f.outward[1] * dy) / length;
        if (fit > bestFit + 1e-9)
        {
            bestFit = fit;
            best = edge;
        }
    }
    const outward = wallFrame(outline, best).outward;
    const side = COMPASS.find(([, direction]) => Math.abs(direction[0] - outward[0]) < 1e-6 && Math.abs(direction[1] - outward[1]) < 1e-6);
    if (side)
    {
        // A compass side names the wall facing it best; when two walls face it, the edge number is exact.
        const facingSame = outline.map((_, edge) => wallFrame(outline, edge).outward).filter((o) => Math.abs(o[0] - outward[0]) < 1e-6 && Math.abs(o[1] - outward[1]) < 1e-6);
        return facingSame.length === 1 ? side[0] : best;
    }
    return best;
}

// The hit test of handles: the index of the corner within `reach` of p, else -1.
export function nearCorner(points: readonly (readonly number[])[], p: readonly number[], reach: number): number
{
    let best = -1;
    let bestDistance = reach;
    points.forEach((point, index) =>
    {
        const d = distance(point, p);
        if (d <= bestDistance)
        {
            best = index;
            bestDistance = d;
        }
    });
    return best;
}

// The edge (from corner i to i + 1) within `reach` of p, else -1; closed for outlines, open for paths.
export function nearEdge(points: readonly (readonly number[])[], p: readonly number[], reach: number, closed: boolean): { edge: number; point: Point } | null
{
    let best: { edge: number; point: Point; d: number } | null = null;
    const count = closed ? points.length : points.length - 1;
    for (let i = 0; i < count; ++i)
    {
        const near = nearestOnSegment(p, points[i], points[(i + 1) % points.length]);
        if (near.distance <= reach && near.t > 0.02 && near.t < 0.98 && (!best || near.distance < best.d))
        {
            best = { edge: i, point: near.point, d: near.distance };
        }
    }
    return best ? { edge: best.edge, point: best.point } : null;
}

// The outline edge a slope's `toward` names (a compass side: the wall facing it best, as the core reads it; or an
// edge number), or -1.
export function towardEdge(outline: Outline, toward: unknown): number
{
    if (typeof toward === 'number')
    {
        return Number.isInteger(toward) && toward >= 0 && toward < outline.length ? toward : -1;
    }
    const side = COMPASS.find(([name]) => name === toward);
    if (!side || outline.length < 3)
    {
        return -1;
    }
    let best = -1;
    let bestFit = -2;
    for (let edge = 0; edge < outline.length; ++edge)
    {
        const outward = wallFrame(outline, edge).outward;
        const fit = outward[0] * side[1][0] + outward[1] * side[1][1];
        if (fit > bestFit + 1e-9)
        {
            bestFit = fit;
            best = edge;
        }
    }
    return best;
}
