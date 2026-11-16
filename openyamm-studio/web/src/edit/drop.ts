// Something dragged from the Library onto the plan or the 3D view (S5_BROWSER_EDITOR.md 3.10: "drag onto the plan or
// 3D to place"): a decoration stands where it is dropped (on a wall it hangs there); a texture goes on the surface it
// is dropped on (on the plan: a wall near the drop, else the room's floor, Shift its ceiling, Alt its walls; in 3D:
// the face's wall, floor or ceiling). What the drop does is a plan of operations the controller sends.
import type { FileTrees, JsonObject, Op, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import { roomAt, roomShapes } from './tools.ts';
import { nearestWall, wallName } from './things.ts';
import { roomSurfacePlan, surfaceOf, wallSurfaceOp } from './surfaces.ts';
import type { Surface, SurfacePart } from './surfaces.ts';

// What the Library's rows carry in a drag (the MIME type below).
export type LibraryKind = 'texture' | 'decoration' | 'monster' | 'item' | 'sound';

export interface LibraryAsset
{
    kind: LibraryKind;
    name: string;
    // A monster's or an item's row number (what objects.yml names it by).
    number?: number;
    size?: number[];
    width?: number;
    height?: number;
}

export const ASSET_MIME = 'application/x-oymap-asset';

export type DropTarget =
    | { where: 'plan'; at: Point; shift: boolean; alt: boolean; reach: number }
    | { where: '3d'; owner: string; point: [number, number, number]; normal?: [number, number, number]; alt: boolean };

export type DropPlan =
    | { kind: 'ops'; label: string; ops: Op[]; select: boolean }
    | { kind: 'theme'; label: string; add: Op; assign: (themeId: string) => Op }
    | { kind: 'note'; text: string };

function surfacePlan(files: FileTrees, roomId: string, part: SurfacePart, surface: Surface): DropPlan
{
    const plan = roomSurfacePlan(files, roomId, part, surface);
    if (!plan)
    {
        return { kind: 'note', text: `${roomId} is not a room of rooms.yml` };
    }
    const label = `${surface.texture} on the ${part === 'wall' ? 'walls' : part} of ${roomId}`;
    return plan.kind === 'set' ? { kind: 'ops', label, ops: [plan.op], select: false } : { kind: 'theme', label, add: plan.add, assign: plan.assign };
}

// The room and wall a 3D face belongs to (room:hall/walls/2), or the room alone.
function faceOwner(owner: string): { room: string; edge: number | null } | null
{
    const match = /^(room:[^/]+)(?:\/walls\/(\d+))?$/.exec(owner);
    return match ? { room: match[1], edge: match[2] !== undefined ? Number(match[2]) : null } : null;
}

export function dropPlan(files: FileTrees, layout: ViewLayoutResult | null, asset: LibraryAsset, target: DropTarget, wallHeight: number): DropPlan
{
    const shapes = roomShapes(files, layout);
    if (asset.kind === 'monster' || asset.kind === 'item' || asset.kind === 'sound')
    {
        // A monster or an item stands, a sound is heard, where it is dropped.
        let room: string | null = null;
        let at: Point | null = null;
        if (target.where === 'plan')
        {
            const shape = roomAt(shapes, target.at);
            room = shape && !shape.ghost ? shape.id : null;
            at = [Math.round(target.at[0]), Math.round(target.at[1])];
        }
        else
        {
            const face = faceOwner(target.owner);
            room = face?.room ?? null;
            // On a wall: a step into the room along the face's normal.
            const n = target.normal ?? [0, 0, 1];
            at = [Math.round(target.point[0] + n[0] * 48), Math.round(target.point[1] + n[1] * 48)];
        }
        if (!room || !at)
        {
            return { kind: 'note', text: `Drop ${asset.name} inside a room` };
        }
        const list = asset.kind === 'monster' ? 'monsters' : asset.kind === 'item' ? 'items' : 'sounds';
        const value: JsonObject = asset.kind === 'sound' ? { room, at, sound: asset.name, radius: 1024 }
            : { room, at, [asset.kind]: asset.number ?? asset.name };
        return { kind: 'ops', label: `${asset.name} in ${room}`, ops: [{ op: 'add', to: list, file: 'objects.yml', value }], select: true };
    }
    if (asset.kind === 'decoration')
    {
        let room: string | null = null;
        let at: Point | null = null;
        let wall: { name: string | number; along: number } | null = null;
        if (target.where === 'plan')
        {
            const shape = roomAt(shapes, target.at);
            if (shape && !shape.ghost)
            {
                room = shape.id;
                const near = shape.path ? null : nearestWall(shape.outline, target.at);
                if (near && near.distance <= target.reach)
                {
                    wall = { name: wallName(shape.outline, near.edge), along: near.along };
                }
                else
                {
                    at = [Math.round(target.at[0]), Math.round(target.at[1])];
                }
            }
        }
        else
        {
            const face = faceOwner(target.owner);
            const shape = face ? shapes.find((entry) => entry.id === face.room) : undefined;
            if (face && shape)
            {
                room = face.room;
                const point: Point = [target.point[0], target.point[1]];
                if (face.edge !== null && !shape.path)
                {
                    const near = nearestWall(shape.outline, point);
                    wall = { name: wallName(shape.outline, face.edge), along: near && near.edge === face.edge ? near.along : 0.5 };
                }
                else
                {
                    at = [Math.round(point[0]), Math.round(point[1])];
                }
            }
        }
        if (!room)
        {
            return { kind: 'note', text: `Drop ${asset.name} inside a room` };
        }
        const value: JsonObject = wall ? { room, wall: wall.name, along: wall.along, height: wallHeight, decoration: asset.name } : { room, at: at!, decoration: asset.name };
        return { kind: 'ops', label: `${asset.name} in ${room}`, ops: [{ op: 'add', to: 'decorations', file: 'objects.yml', value }], select: true };
    }
    const surface = surfaceOf(asset);
    if (target.where === 'plan')
    {
        const shape = roomAt(shapes, target.at);
        if (!shape || shape.ghost)
        {
            return { kind: 'note', text: `Drop ${asset.name} on a room (near a wall for that wall; Shift: its ceiling; Alt: its walls)` };
        }
        if (target.shift)
        {
            return surfacePlan(files, shape.id, 'ceiling', surface);
        }
        if (target.alt)
        {
            return surfacePlan(files, shape.id, 'wall', surface);
        }
        const near = shape.path ? null : nearestWall(shape.outline, target.at);
        if (near && near.distance <= target.reach)
        {
            const op = wallSurfaceOp(files, shape.id, near.edge, surface);
            return op ? { kind: 'ops', label: `${asset.name} on wall ${wallName(shape.outline, near.edge)} of ${shape.id}`, ops: [op], select: false } : { kind: 'note', text: 'no such wall' };
        }
        return surfacePlan(files, shape.id, 'floor', surface);
    }
    const face = faceOwner(target.owner);
    if (!face)
    {
        return { kind: 'note', text: `${target.owner || 'that face'} is not a room's wall, floor or ceiling: drop on one of those` };
    }
    if (face.edge !== null)
    {
        if (target.alt)
        {
            return surfacePlan(files, face.room, 'wall', surface);
        }
        const op = wallSurfaceOp(files, face.room, face.edge, surface);
        return op ? { kind: 'ops', label: `${asset.name} on wall ${face.edge} of ${face.room}`, ops: [op], select: false } : { kind: 'note', text: 'no such wall' };
    }
    const up = target.normal ? target.normal[2] : 1;
    return surfacePlan(files, face.room, up < -0.5 ? 'ceiling' : up > 0.5 ? 'floor' : 'wall', surface);
}
