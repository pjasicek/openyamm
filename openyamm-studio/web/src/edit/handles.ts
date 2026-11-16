// S5b2 (carried from S5b1, S5_BROWSER_EDITOR.md 3.18 "Edit by hand"): plan handles for the blocks of objects.yml
// (lifts, movers, plates: box or outline; ladders: a point and its facing, and a leaning ladder's top) and the room sub-objects drawn as lines
// (parapets and beams: a path; flights: two ends), with ceiling levels picked on the plan. Pure: the shape an address
// gives the Select tool, what a gesture writes (one keyed `patch`), and what lies under a point.
import type { FileTrees, JsonObject, JsonValue, Op } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import { roomById, roomsOf } from './ops.ts';
import { isObject, keysOf, resolvePointer, splitAddress } from './keys.ts';
import { box, distance, nearestOnSegment, pointInPolygon } from './geometry.ts';
import { points } from './toolbase.ts';

// What of the selection the handles change (tools.ts EditShape is this).
export interface EditShape
{
    id: string;
    // The pointer of the object's part the gesture writes ('' for an object of objects.yml itself).
    base: string;
    // polygon (an outline), polyline (a path), box (`at` and `size`), point (`at`: a ladder), ends (`from`, `to`).
    kind: 'polygon' | 'polyline' | 'box' | 'point' | 'ends';
    points: Point[];
    at?: Point;
    size?: Point;
    // The file the patch goes to (rooms.yml when not given).
    file?: keyof FileTrees;
    // A box placed by `offset` from its room's middle (`origin`): the gesture writes the offset.
    offsetFrom?: Point;
    // Whether the size is written in the file (else the gesture adds it).
    sized?: boolean;
    // A point's facing (degrees, counter-clockwise from east) and whether the file has it.
    facing?: number;
    faced?: boolean;
    // The whole shape moves by a drag inside it (blocks and lines; rooms keep a drag inside for picking).
    movable?: boolean;
    // The given point values (a ladder's [x, y, z]; a flight's ends), for the patch's tests.
    given?: JsonValue[];
}

const OBJECT_BLOCKS = ['lifts', 'movers', 'plates', 'ladders'] as const;

function objectsList(files: FileTrees, name: string): JsonObject[]
{
    const value = files['objects.yml']?.tree[name];
    return Array.isArray(value) ? value.filter(isObject) : [];
}

// The middle of a room's outline box (where `offset` counts from, as the plan draws it: blocks.ts objectBlocks).
export function roomMiddle(files: FileTrees, room: string): Point
{
    const outline = points(roomById(files, room)?.outline);
    if (outline.length === 0)
    {
        return [0, 0];
    }
    const xs = outline.map((p) => p[0]);
    const ys = outline.map((p) => p[1]);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
}

function boxPoints(at: Point, size: Point): Point[]
{
    const [w, h] = size;
    return [[at[0] - w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] + h / 2], [at[0] - w / 2, at[1] + h / 2]];
}

// The shape of a block of objects.yml (lift, mover, plate, ladder), or null.
export function objectShape(files: FileTrees | undefined, id: string): EditShape | null
{
    if (!files)
    {
        return null;
    }
    for (const list of OBJECT_BLOCKS)
    {
        const item = objectsList(files, list).find((entry) => entry.id === id);
        if (!item)
        {
            continue;
        }
        const file: keyof FileTrees = 'objects.yml';
        if (list === 'ladders')
        {
            const at = points([item.at])[0];
            if (!at)
            {
                return null;
            }
            // A leaning ladder (S6 L): its top's point on the plan is the second point, moved with the foot.
            const top = points([item.top_at])[0];
            return { id, base: '', kind: 'point', file, points: top ? [at, top] : [at], at, facing: typeof item.facing === 'number' ? item.facing : 0,
                faced: typeof item.facing === 'number', movable: true, given: top ? [item.at as JsonValue, item.top_at as JsonValue] : [item.at as JsonValue] };
        }
        const outline = points(item.outline);
        if (outline.length >= 3)
        {
            return { id, base: '/outline', kind: 'polygon', file, points: outline, movable: true };
        }
        const size = points([item.size])[0];
        const at = points([item.at])[0];
        const sized = size !== undefined;
        const made = size ?? [64, 64];
        if (at)
        {
            return { id, base: '', kind: 'box', file, at, size: made, sized, points: boxPoints(at, made), movable: true };
        }
        const offset = points([item.offset])[0] ?? [0, 0];
        const origin = roomMiddle(files, String(item.room ?? ''));
        const placed: Point = [origin[0] + offset[0], origin[1] + offset[1]];
        return { id, base: '', kind: 'box', file, at: placed, size: made, sized, offsetFrom: origin, points: boxPoints(placed, made), movable: true,
            ...(item.offset !== undefined ? { given: [item.offset as JsonValue] } : {}) };
    }
    return null;
}

// The shape of a room's part drawn as a line (a parapet's or beam's path, a flight's ends), or null.
export function roomLineShape(files: FileTrees | undefined, address: string): EditShape | null
{
    if (!files)
    {
        return null;
    }
    const { id, pointer } = splitAddress(address);
    const room = roomById(files, id);
    const target = room && pointer ? resolvePointer(room, pointer) : undefined;
    if (!isObject(target))
    {
        return null;
    }
    const path = points(target.path);
    if (path.length >= 2)
    {
        return { id, base: `${pointer}/path`, kind: 'polyline', points: path, movable: true };
    }
    const from = points([target.from])[0];
    const to = points([target.to])[0];
    if (from && to && pointer.startsWith('/flights/'))
    {
        return { id, base: pointer, kind: 'ends', points: [from, to], movable: true, given: [target.from as JsonValue, target.to as JsonValue] };
    }
    return null;
}

// A point's value as written, moved to `to` (a third number, a ladder's foot height, kept).
function movedValue(given: JsonValue | undefined, to: Point): JsonValue
{
    return Array.isArray(given) && given.length > 2 ? [to[0], to[1], given[2]] : [to[0], to[1]];
}

function step(op: 'test' | 'replace' | 'add' | 'remove', path: string, value?: JsonValue): JsonObject
{
    return value === undefined ? { op, path } : { op, path, value };
}

export type GestureKind = 'corner' | 'edge' | 'move' | 'box' | 'facing';

// What a gesture on one of these shapes writes: one keyed `patch` of the shape's object. `after` is the points as the
// drag leaves them (a box: its four corners); `facing` the new facing of a point's facing handle.
export function shapeGestureOp(shape: EditShape, after: readonly Point[], how: GestureKind, facing?: number): Op | null
{
    const file = shape.file ?? 'rooms.yml';
    const patch: JsonObject[] = [];
    if (how === 'facing')
    {
        if (facing === undefined)
        {
            return null;
        }
        patch.push(...(shape.faced ? [step('test', `${shape.base}/facing`, shape.facing), step('replace', `${shape.base}/facing`, facing)]
            : [step('add', `${shape.base}/facing`, facing)]));
        return { op: 'patch', id: shape.id, file, patch: patch as never };
    }
    if (shape.kind === 'box')
    {
        const made = box(after[0], after[2]);
        if (!made || !shape.at)
        {
            return null;
        }
        if (shape.offsetFrom)
        {
            const offset: Point = [made.at[0] - Math.round(shape.offsetFrom[0]), made.at[1] - Math.round(shape.offsetFrom[1])];
            patch.push(...(shape.given ? [step('test', `${shape.base}/offset`, shape.given[0]), step('replace', `${shape.base}/offset`, offset)]
                : [step('add', `${shape.base}/offset`, offset)]));
        }
        else
        {
            patch.push(step('test', `${shape.base}/at`, shape.at), step('replace', `${shape.base}/at`, made.at));
        }
        if (how !== 'move' || !shape.sized)
        {
            patch.push(...(shape.sized ? [step('test', `${shape.base}/size`, shape.size), step('replace', `${shape.base}/size`, made.size)]
                : [step('add', `${shape.base}/size`, made.size)]));
        }
        return { op: 'patch', id: shape.id, file, patch: patch as never };
    }
    if (shape.kind === 'point')
    {
        const to = after[0];
        patch.push(step('test', `${shape.base}/at`, shape.given?.[0] ?? shape.at), step('replace', `${shape.base}/at`, movedValue(shape.given?.[0], to)));
        const top = after[1];
        const topBefore = shape.points[1];
        if (top && topBefore && (top[0] !== topBefore[0] || top[1] !== topBefore[1]))
        {
            patch.push(step('test', `${shape.base}/top_at`, shape.given?.[1] ?? topBefore), step('replace', `${shape.base}/top_at`, movedValue(shape.given?.[1], top)));
        }
        return { op: 'patch', id: shape.id, file, patch: patch as never };
    }
    if (shape.kind === 'ends')
    {
        ['from', 'to'].forEach((field, index) =>
        {
            const from = shape.points[index];
            const to = after[index];
            if (from[0] !== to[0] || from[1] !== to[1])
            {
                patch.push(step('test', `${shape.base}/${field}`, shape.given?.[index] ?? from), step('replace', `${shape.base}/${field}`, movedValue(shape.given?.[index], to)));
            }
        });
        return patch.length > 0 ? { op: 'patch', id: shape.id, file, patch: patch as never } : null;
    }
    after.forEach((to, index) =>
    {
        const from = shape.points[index];
        if (from && (from[0] !== to[0] || from[1] !== to[1]))
        {
            patch.push(step('test', `${shape.base}/${index}`, from), step('replace', `${shape.base}/${index}`, to));
        }
    });
    return patch.length > 0 ? { op: 'patch', id: shape.id, file, patch: patch as never } : null;
}

// A point moved by a drag inside the shape (snapped to the grid by the caller): every point by the same step.
export function movedPoints(shape: EditShape, by: Point): Point[]
{
    return shape.points.map((p) => [p[0] + by[0], p[1] + by[1]]);
}

// Whether a press at `at` grabs the whole shape (inside its outline or box, or on its line).
export function grabsShape(shape: EditShape, at: Point, reach: number): boolean
{
    if (!shape.movable)
    {
        return false;
    }
    if (shape.kind === 'polygon' || shape.kind === 'box')
    {
        return pointInPolygon(at, shape.points);
    }
    if (shape.kind === 'point')
    {
        return distance(shape.points[0], at) <= reach * 2;
    }
    for (let i = 0; i + 1 < shape.points.length; ++i)
    {
        if (nearestOnSegment(at, shape.points[i], shape.points[i + 1]).distance <= reach)
        {
            return true;
        }
    }
    return false;
}

// Degrees counter-clockwise from east of a direction (the plan's y runs north, as the files' do), snapped to `step`.
export function degreesTo(from: Point, to: Point, step = 15): number
{
    const degrees = (Math.atan2(to[1] - from[1], to[0] - from[0]) * 180) / Math.PI;
    return ((Math.round(degrees / step) * step) % 360 + 360) % 360;
}

// The room parts drawn as lines that the plan picks before the room's blocks: parapets, beams and flights, the one
// whose line passes nearest within `reach`. Its address (room:hall/beams/beam1), or null.
export function roomLineAt(files: FileTrees | undefined, at: Point, reach: number): string | null
{
    if (!files)
    {
        return null;
    }
    let best: { address: string; d: number } | null = null;
    for (const room of roomsOf(files))
    {
        const id = String(room.id ?? '');
        for (const name of ['parapets', 'beams', 'flights'] as const)
        {
            const items = room[name];
            if (!Array.isArray(items))
            {
                continue;
            }
            const keys = keysOf(items, name);
            items.forEach((item, index) =>
            {
                if (!isObject(item))
                {
                    return;
                }
                const pts = name === 'flights' ? [points([item.from])[0], points([item.to])[0]].filter((p): p is Point => !!p) : points(item.path);
                for (let i = 0; i + 1 < pts.length; ++i)
                {
                    const d = nearestOnSegment(at, pts[i], pts[i + 1]).distance;
                    if (d <= reach && (!best || d < best.d))
                    {
                        best = { address: `${id}/${name}/${keys[index]}`, d };
                    }
                }
            });
        }
    }
    return (best as { address: string } | null)?.address ?? null;
}

// The ceiling level under a point (picked after the floor's blocks), or null.
export function ceilingLevelAt(files: FileTrees | undefined, at: Point): string | null
{
    if (!files)
    {
        return null;
    }
    let best: { address: string; area: number } | null = null;
    for (const room of roomsOf(files))
    {
        const items = room.ceiling_levels;
        if (!Array.isArray(items))
        {
            continue;
        }
        const keys = keysOf(items, 'ceiling_levels');
        items.forEach((item, index) =>
        {
            const outline = isObject(item) ? points(item.outline) : [];
            if (outline.length >= 3 && pointInPolygon(at, outline))
            {
                const xs = outline.map((p) => p[0]);
                const ys = outline.map((p) => p[1]);
                const area = (Math.max(...xs) - Math.min(...xs)) * (Math.max(...ys) - Math.min(...ys));
                if (!best || area < best.area)
                {
                    best = { address: `${String(room.id)}/ceiling_levels/${keys[index]}`, area };
                }
            }
        });
    }
    return (best as { address: string } | null)?.address ?? null;
}
