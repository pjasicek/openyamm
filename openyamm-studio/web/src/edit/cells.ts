// Cells and map units (S5_BROWSER_EDITOR.md 3.18, the Outdoor table): a sketch's points, lines and polygons are in
// cells, [x, y] with x east and y south from the map's north-west corner, 512 map units a cell; the plan and the 3D
// view work in map units with the origin in the middle of the map and y north (as the built map and view.layout
// have them). Nodes are the land's height points at the cells' corners, 0 to 127 each way on a classic map.
//
// The map's side is the project's (project.yml terrain.side: 128 a classic ODM, 160 an ODM v2 map; core/OutdoorGrid).
// MAP_CELLS, HALF and NODES are live bindings: setMapSide changes them for every module that imports them when a
// project opens.
import type { Point } from './ops.ts';

export const CELL = 512;
export const CLASSIC_SIDE = 128;
export let MAP_CELLS = CLASSIC_SIDE;
export let HALF = (MAP_CELLS / 2) * CELL;
// The land's nodes along a side (view.layout's land.size).
export let NODES = CLASSIC_SIDE;

// A project's side: project.yml terrain.side when it is an even number from 32 to 256, else the classic 128.
export function projectSide(card: unknown): number
{
    const terrain = (card as { terrain?: { side?: unknown } } | undefined)?.terrain;
    const side = Number(terrain?.side);
    return Number.isInteger(side) && side >= 32 && side <= 256 && side % 2 === 0 ? side : CLASSIC_SIDE;
}

// Sets the side of the map being edited.
export function setMapSide(side: number): void
{
    MAP_CELLS = side;
    HALF = (side / 2) * CELL;
    NODES = side;
}

// A sketch point (cells) to map units.
export function cellToMap(cell: readonly number[]): Point
{
    return [cell[0] * CELL - HALF, HALF - cell[1] * CELL];
}

// Map units to a sketch point in cells (fractions kept).
export function mapToCell(map: readonly number[]): Point
{
    return [(map[0] + HALF) / CELL, (HALF - map[1]) / CELL];
}

// A cell coordinate rounded to a step (1 whole cells, 0.5 half cells), inside the map.
export function snapCell(cell: readonly number[], step: number): Point
{
    const round = (value: number) => Math.min(MAP_CELLS, Math.max(0, Math.round(value / step) * step));
    return [round(cell[0]), round(cell[1])];
}

// The middle of the cell a point lies in ([12.5, 40.5]): where roads run.
export function cellCentre(cell: readonly number[]): Point
{
    const clamp = (value: number) => Math.min(MAP_CELLS - 0.5, Math.max(0.5, Math.floor(value) + 0.5));
    return [clamp(cell[0]), clamp(cell[1])];
}

// The node nearest a cell point.
export function nearestNode(cell: readonly number[]): Point
{
    const clamp = (value: number) => Math.min(NODES - 1, Math.max(0, Math.round(value)));
    return [clamp(cell[0]), clamp(cell[1])];
}

// A building part's local point (map units east and south of the plot's north-west corner) to cells, and back.
export function localToCell(at: readonly number[], local: readonly number[]): Point
{
    return [at[0] + local[0] / CELL, at[1] + local[1] / CELL];
}

export function cellToLocal(at: readonly number[], cell: readonly number[]): Point
{
    return [Math.round((cell[0] - at[0]) * CELL), Math.round((cell[1] - at[1]) * CELL)];
}

// The next point of a road from the last: the segment turned to the nearest of the eight directions the world's
// road tiles lay (square or at 45 degrees), its length kept along that direction, on cell centres.
export function roadStep(from: readonly number[], to: readonly number[]): Point
{
    const dx = to[0] - from[0];
    const dy = to[1] - from[1];
    if (dx === 0 && dy === 0)
    {
        return [from[0], from[1]];
    }
    const angle = Math.round(Math.atan2(dy, dx) / (Math.PI / 4)) * (Math.PI / 4);
    const ux = Math.round(Math.cos(angle));
    const uy = Math.round(Math.sin(angle));
    const length = ux !== 0 && uy !== 0 ? Math.round((Math.abs(dx) + Math.abs(dy)) / 2) : Math.round(Math.abs(ux !== 0 ? dx : dy));
    const clamp = (value: number) => Math.min(MAP_CELLS - 0.5, Math.max(0.5, value));
    return [clamp(from[0] + ux * length), clamp(from[1] + uy * length)];
}

// Whether a point lies inside a polygon or on its edge (within `epsilon`).
export function insideOrOn(p: readonly number[], polygon: readonly (readonly number[])[], epsilon = 1e-6): boolean
{
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++)
    {
        const a = polygon[i];
        const b = polygon[j];
        const ex = b[0] - a[0];
        const ey = b[1] - a[1];
        const length = ex * ex + ey * ey;
        const t = length > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / length)) : 0;
        if (Math.hypot(a[0] + ex * t - p[0], a[1] + ey * t - p[1]) <= epsilon)
        {
            return true;
        }
        if ((a[1] > p[1]) !== (b[1] > p[1]) && p[0] < ((b[0] - a[0]) * (p[1] - a[1])) / (b[1] - a[1]) + a[0])
        {
            inside = !inside;
        }
    }
    return inside;
}

// The cells' bounding box of a polygon: [width, depth].
export function extentOf(polygon: readonly (readonly number[])[]): [number, number]
{
    const xs = polygon.map((p) => p[0]);
    const ys = polygon.map((p) => p[1]);
    return [Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
}
