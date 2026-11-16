// The placed things of objects.yml on the plan (S5_BROWSER_EDITOR.md 3.18, part 2): where each one stands as the
// files say it (a point, a place on a wall, an offset from the room's middle), which wall a click is on, and the
// operations of the placing tools and their handles (move, facing, radius). Pure plan geometry for gestures; the
// core's layout gives the exact places once it has built them.
import type { FileTrees, JsonObject, JsonValue, Op, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import { GHOST } from './ops.ts';
import { distance, nearestOnSegment, signedArea } from './geometry.ts';
import type { Outline } from './geometry.ts';

// The lists the placing tools make, with what their handles change.
export interface PlaceList
{
    list: string;
    // The tool's name for one of them.
    noun: string;
    // A thing on a wall (wall, along) rather than at a point.
    onWall: boolean;
    facing: boolean;
    // The field the radius handle sets.
    radius?: string;
}

export const PLACE_LISTS: PlaceList[] = [
    { list: 'switches', noun: 'switch', onWall: true, facing: false },
    { list: 'exits', noun: 'exit', onWall: true, facing: false },
    { list: 'chests', noun: 'chest', onWall: false, facing: true },
    { list: 'spawns', noun: 'spawn', onWall: false, facing: false, radius: 'radius' },
    { list: 'monsters', noun: 'monster', onWall: false, facing: true },
    { list: 'items', noun: 'item', onWall: false, facing: false },
    { list: 'decorations', noun: 'decoration', onWall: false, facing: true },
    { list: 'lights', noun: 'light', onWall: false, facing: false, radius: 'radius' },
    { list: 'sounds', noun: 'sound', onWall: false, facing: false, radius: 'radius' },
    { list: 'placeholders', noun: 'placeholder', onWall: false, facing: true },
];

export function placeList(list: string): PlaceList | undefined
{
    return PLACE_LISTS.find((entry) => entry.list === list);
}

// A thing on the plan.
export interface Placed
{
    // Its id (or `start` for the party start).
    address: string;
    list: string;
    room?: string;
    at: Point;
    // Degrees, counter-clockwise from east.
    facing?: number;
    radius?: number;
    // On a wall: the edge and the place along it (0..1 counter-clockwise from the wall's start corner).
    wall?: { edge: number; along: number };
    // Added on the client and not answered yet.
    ghost: boolean;
    // What it is, in a word (a decoration's name, a monster's, a switch's kind).
    label?: string;
}

const FACINGS: Record<string, number> = {
    e: 0, east: 0, ne: 45, northeast: 45, n: 90, north: 90, nw: 135, northwest: 135,
    w: 180, west: 180, sw: 225, southwest: 225, s: 270, south: 270, se: 315, southeast: 315,
};

// A `facing` (compass word or degrees) in degrees, or undefined.
export function facingDegrees(value: JsonValue | undefined): number | undefined
{
    if (typeof value === 'number')
    {
        return value;
    }
    return typeof value === 'string' ? FACINGS[value.toLowerCase()] : undefined;
}

function point(value: JsonValue | undefined): Point | null
{
    return Array.isArray(value) && typeof value[0] === 'number' && typeof value[1] === 'number' ? [value[0], value[1]] : null;
}

function outlineOf(room: JsonObject | undefined, layout: ViewLayoutResult | null): Point[]
{
    const own = Array.isArray(room?.outline) ? (room!.outline as JsonValue[]).map(point).filter((p): p is Point => !!p) : [];
    if (own.length >= 3)
    {
        return own;
    }
    const built = layout?.rooms.find((entry) => entry.id === room?.id);
    return built ? built.outline.map((p) => [p[0], p[1]] as Point) : [];
}

// The middle of a room as the plan shows it (its outline's box), for things placed by `offset` or not at all.
export function roomMiddle(outline: Outline): Point
{
    if (outline.length === 0)
    {
        return [0, 0];
    }
    const xs = outline.map((p) => p[0]);
    const ys = outline.map((p) => p[1]);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
}

// The outward direction of an outline's edge (the room on the left of a counter-clockwise outline).
function outward(outline: Outline, edge: number): Point
{
    const a = outline[edge];
    const b = outline[(edge + 1) % outline.length];
    const length = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
    const sign = signedArea(outline) >= 0 ? 1 : -1;
    return [sign * (b[1] - a[1]) / length, sign * -(b[0] - a[0]) / length];
}

const SIDES: [string, Point][] = [['east', [1, 0]], ['north', [0, 1]], ['west', [-1, 0]], ['south', [0, -1]]];
const SHORT: Record<string, string> = { e: 'east', n: 'north', w: 'west', s: 'south' };

// The edge a `wall` names: an edge number, or a compass side (the wall whose outside faces it best, as the core
// reads it); -1 when it names none.
export function wallEdge(outline: Outline, wall: JsonValue | undefined): number
{
    if (typeof wall === 'number')
    {
        return Number.isInteger(wall) && wall >= 0 && wall < outline.length ? wall : -1;
    }
    if (typeof wall !== 'string' || outline.length < 3)
    {
        return -1;
    }
    const name = SHORT[wall.toLowerCase()] ?? wall.toLowerCase();
    const side = SIDES.find(([entry]) => entry === name);
    if (!side)
    {
        return -1;
    }
    let best = -1;
    let bestFit = -2;
    for (let edge = 0; edge < outline.length; ++edge)
    {
        const o = outward(outline, edge);
        const fit = o[0] * side[1][0] + o[1] * side[1][1];
        if (fit > bestFit + 1e-9)
        {
            bestFit = fit;
            best = edge;
        }
    }
    return best;
}

// The way to write an edge as a `wall`: its compass side when it alone faces that side squarely (so it stays put when
// the outline is redrawn), else its number.
export function wallName(outline: Outline, edge: number): string | number
{
    const o = outward(outline, edge);
    const side = SIDES.find(([, direction]) => Math.abs(direction[0] - o[0]) < 1e-6 && Math.abs(direction[1] - o[1]) < 1e-6);
    if (!side)
    {
        return edge;
    }
    const same = outline.map((_, index) => outward(outline, index)).filter((other) => Math.abs(other[0] - o[0]) < 1e-6 && Math.abs(other[1] - o[1]) < 1e-6);
    return same.length === 1 && wallEdge(outline, side[0]) === edge ? side[0] : edge;
}

// The point `along` a wall (0 at the wall's start corner going counter-clockwise round the room).
export function wallPoint(outline: Outline, edge: number, along: number): Point
{
    const ccw = signedArea(outline) >= 0;
    const a = outline[edge];
    const b = outline[(edge + 1) % outline.length];
    const t = ccw ? along : 1 - along;
    return [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t];
}

// The wall of a room nearest to a point: its edge, the place along it and how far the point is from it.
export function nearestWall(outline: Outline, at: readonly number[]): { edge: number; along: number; distance: number; point: Point } | null
{
    if (outline.length < 3)
    {
        return null;
    }
    const ccw = signedArea(outline) >= 0;
    let best: { edge: number; along: number; distance: number; point: Point } | null = null;
    for (let edge = 0; edge < outline.length; ++edge)
    {
        const near = nearestOnSegment(at, outline[edge], outline[(edge + 1) % outline.length]);
        if (!best || near.distance < best.distance)
        {
            const along = Math.round((ccw ? near.t : 1 - near.t) * 1000) / 1000;
            best = { edge, along: Math.max(0.02, Math.min(0.98, along)), distance: near.distance, point: near.point };
        }
    }
    return best;
}

function roomsById(files: FileTrees): Map<string, JsonObject>
{
    const rooms = files['rooms.yml']?.tree.rooms;
    return new Map((Array.isArray(rooms) ? rooms : []).filter((room): room is JsonObject => typeof room === 'object' && room !== null && !Array.isArray(room))
        .map((room) => [String(room.id), room]));
}

// Where one object of objects.yml stands on the plan.
function placeOf(object: JsonObject, list: PlaceList | null, rooms: Map<string, JsonObject>, layout: ViewLayoutResult | null): Placed | null
{
    const roomId = typeof object.room === 'string' ? object.room : undefined;
    const room = roomId ? rooms.get(roomId) : undefined;
    const outline = outlineOf(room, layout);
    const address = typeof object.id === 'string' ? object.id : '';
    const ghost = object[GHOST] === true;
    const own = point(object.at);
    const built = address ? layout?.things.find((thing) => thing.id === address) : undefined;
    let at: Point | null = own;
    let wall: Placed['wall'];
    if (!at && object.wall !== undefined && outline.length >= 3)
    {
        const edge = wallEdge(outline, object.wall);
        if (edge >= 0)
        {
            const along = typeof object.along === 'number' ? object.along : 0.5;
            wall = { edge, along };
            at = wallPoint(outline, edge, along);
        }
    }
    if (!at && built)
    {
        at = [built.at[0], built.at[1]];
    }
    if (!at && outline.length >= 3)
    {
        const middle = roomMiddle(outline);
        const offset = point(object.offset);
        at = offset ? [middle[0] + offset[0], middle[1] + offset[1]] : middle;
    }
    if (!at)
    {
        return null;
    }
    if (own && list?.onWall && outline.length >= 3)
    {
        const near = nearestWall(outline, own);
        if (near)
        {
            wall = { edge: near.edge, along: near.along };
        }
    }
    const radiusField = list?.radius;
    const radius = radiusField && typeof object[radiusField] === 'number' ? (object[radiusField] as number) : undefined;
    const label = typeof object.decoration === 'string' ? object.decoration : object.monster !== undefined ? String(object.monster)
        : typeof object.kind === 'string' ? object.kind : object.item !== undefined ? String(object.item) : typeof object.sound === 'string' ? object.sound
        : typeof object.stands_for === 'string' ? object.stands_for : undefined;
    return { address, list: list?.list ?? 'start', ...(roomId ? { room: roomId } : {}), at, facing: facingDegrees(object.facing),
        ...(radius !== undefined ? { radius } : {}), ...(wall ? { wall } : {}), ghost, ...(label ? { label } : {}) };
}

// Every placed thing of the files (and the start), as the plan draws and picks them in Author mode.
export function placedThings(files: FileTrees | undefined, layout: ViewLayoutResult | null): Placed[]
{
    const tree = files?.['objects.yml']?.tree;
    if (!files || !tree)
    {
        return [];
    }
    const rooms = roomsById(files);
    const out: Placed[] = [];
    for (const list of PLACE_LISTS)
    {
        const items = tree[list.list];
        if (!Array.isArray(items))
        {
            continue;
        }
        for (const item of items)
        {
            if (typeof item === 'object' && item !== null && !Array.isArray(item))
            {
                const placed = placeOf(item, list, rooms, layout);
                if (placed)
                {
                    out.push(placed);
                }
            }
        }
    }
    const start = tree.start;
    if (typeof start === 'object' && start !== null && !Array.isArray(start))
    {
        const placed = placeOf({ ...start, id: 'start' }, null, rooms, layout);
        if (placed)
        {
            // The core's layout knows the start's place exactly (an arrival without `at` stands in the room's middle).
            if (!point(start.at) && layout?.start)
            {
                placed.at = [layout.start.at[0], layout.start.at[1]];
            }
            out.push(placed);
        }
    }
    return out;
}

// The thing nearest a point within `reach`, preferring the smaller distance.
export function placedAt(things: readonly Placed[], at: readonly number[], reach: number): Placed | null
{
    let best: Placed | null = null;
    let bestDistance = reach;
    for (const thing of things)
    {
        const d = distance(thing.at, at);
        if (d <= bestDistance)
        {
            best = thing;
            bestDistance = d;
        }
    }
    return best;
}

// --- operations of the placing tools and handles ---------------------------------------------------------------

// The degrees of a direction, rounded to `step` (0: one degree).
export function degreesOf(dx: number, dy: number, step: number): number
{
    const raw = (Math.atan2(dy, dx) * 180) / Math.PI;
    const rounded = step > 0 ? Math.round(raw / step) * step : Math.round(raw);
    return ((rounded % 360) + 360) % 360;
}

// A thing moved to a point: its `at` (an offset no longer applies), and its room where it left it for another.
export function moveOp(thing: Placed, to: Point, room: string | undefined): Op
{
    if (thing.list === 'start')
    {
        return { op: 'set_value', file: 'objects.yml', path: 'start.at', value: to };
    }
    const fields: Record<string, JsonValue> = { at: to };
    fields.offset = null;
    if (room && room !== thing.room)
    {
        fields.room = room;
    }
    return { op: 'set', id: thing.address, file: 'objects.yml', fields };
}

// A thing on a wall slid along it (or to another wall of its room).
export function slideOp(thing: Placed, wall: string | number, along: number): Op
{
    return { op: 'set', id: thing.address, file: 'objects.yml', fields: { wall, along, at: null } };
}

export function facingOp(thing: Placed, degrees: number): Op
{
    if (thing.list === 'start')
    {
        return { op: 'set_value', file: 'objects.yml', path: 'start.facing', value: degrees };
    }
    return { op: 'set', id: thing.address, file: 'objects.yml', fields: { facing: degrees } };
}

export function radiusOp(thing: Placed, radius: number): Op | null
{
    const field = placeList(thing.list)?.radius;
    return field ? { op: 'set', id: thing.address, file: 'objects.yml', fields: { [field]: radius } } : null;
}
