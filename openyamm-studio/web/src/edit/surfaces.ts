// A texture from the Library laid on a surface (S5_BROWSER_EDITOR.md 3.10, 3.18 "single walls ... surface from the
// library", "theme ... apply to rooms by drag"): one wall of a room (its `walls` entry), or a room's walls, floor or
// ceiling (the room's own theme, made from the theme it had when other rooms share that one), or a theme for every
// room that uses it. Operations only; the core builds what they say.
import type { FileTrees, JsonObject, JsonValue, Op } from '../../../schema/rpc/generated/rpc.ts';
import { isObject, keysOf, segment } from './keys.ts';
import { roomById, roomsOf } from './ops.ts';
import type { Point } from './ops.ts';
import { wallEdge, wallName } from './things.ts';

export interface Surface
{
    texture: string;
    size?: [number, number];
}

export type SurfacePart = 'wall' | 'floor' | 'ceiling';

// The texture as a surface of rooms.yml (its size in texels, which every texture with a picture needs).
export function surfaceOf(texture: { name: string; size?: number[]; width?: number; height?: number }): Surface
{
    const size = texture.size?.length === 2 ? [texture.size[0], texture.size[1]] as [number, number]
        : texture.width && texture.height ? [texture.width, texture.height] as [number, number] : undefined;
    return { texture: texture.name, ...(size ? { size } : {}) };
}

function outline(room: JsonObject): Point[]
{
    return Array.isArray(room.outline) ? (room.outline as JsonValue[]).filter((p): p is number[] => Array.isArray(p) && typeof p[0] === 'number')
        .map((p) => [p[0] as number, p[1] as number] as Point) : [];
}

// One wall of a room: its entry in `walls` gets the surface (made when the wall has none).
export function wallSurfaceOp(files: FileTrees, roomId: string, edge: number, surface: Surface): Op | null
{
    const room = roomById(files, roomId);
    if (!room)
    {
        return null;
    }
    const shape = outline(room);
    const walls = Array.isArray(room.walls) ? (room.walls as JsonValue[]) : [];
    const keys = keysOf(walls, 'walls');
    const index = walls.findIndex((entry) => isObject(entry) && wallEdge(shape, entry.wall) === edge);
    if (index >= 0)
    {
        const path = `/walls/${segment(keys[index])}/surface`;
        const had = isObject(walls[index]) && (walls[index] as JsonObject).surface !== undefined;
        return { op: 'patch', id: roomId, file: 'rooms.yml', patch: [{ op: had ? 'replace' : 'add', path, value: surface as unknown as JsonValue }] };
    }
    const entry: JsonObject = { wall: shape.length >= 3 ? wallName(shape, edge) : edge, surface: surface as unknown as JsonValue };
    return Array.isArray(room.walls)
        ? { op: 'patch', id: roomId, file: 'rooms.yml', patch: [{ op: 'add', path: '/walls/-', value: entry }] }
        : { op: 'patch', id: roomId, file: 'rooms.yml', patch: [{ op: 'add', path: '/walls', value: [entry] }] };
}

// The theme a room is drawn with: its own `theme`, else the file's default.
export function themeOfRoom(files: FileTrees, room: JsonObject): string | null
{
    if (typeof room.theme === 'string')
    {
        return room.theme;
    }
    const defaults = files['rooms.yml']?.tree.defaults;
    return isObject(defaults) && typeof defaults.theme === 'string' ? defaults.theme : null;
}

export function themeById(files: FileTrees, id: string): JsonObject | undefined
{
    const themes = files['rooms.yml']?.tree.themes;
    return Array.isArray(themes) ? themes.filter(isObject).find((theme) => theme.id === id) : undefined;
}

// What a room's walls, floor or ceiling take a texture by: the room's own theme changed in place when no other room
// uses it; else a new theme copied from the one the room had, with the part changed (the core gives its id; the room
// names it in a second step of the same gesture).
export function roomSurfacePlan(files: FileTrees, roomId: string, part: SurfacePart, surface: Surface):
    { kind: 'set'; op: Op } | { kind: 'new'; add: Op; assign: (themeId: string) => Op } | null
{
    const room = roomById(files, roomId);
    if (!room)
    {
        return null;
    }
    const themeId = themeOfRoom(files, room);
    const theme = themeId ? themeById(files, themeId) : undefined;
    const users = roomsOf(files).filter((other) => themeOfRoom(files, other) === themeId);
    if (theme && typeof room.theme === 'string' && users.length === 1)
    {
        return { kind: 'set', op: { op: 'set', id: themeId!, file: 'rooms.yml', fields: { [part]: surface as unknown as JsonValue } } };
    }
    const copy: JsonObject = theme ? { ...theme } : {};
    delete copy.id;
    copy[part] = surface as unknown as JsonValue;
    copy.notes = `Made for ${roomId} in the studio${themeId ? ` from ${themeId}` : ''}.`;
    return {
        kind: 'new',
        add: { op: 'add', to: 'themes', file: 'rooms.yml', value: copy },
        assign: (id) => ({ op: 'set', id: roomId, file: 'rooms.yml', fields: { theme: id } }),
    };
}

// A theme's part for every room that uses it.
export function themeSurfaceOp(themeId: string, part: SurfacePart, surface: Surface): Op
{
    return { op: 'set', id: themeId, file: 'rooms.yml', fields: { [part]: surface as unknown as JsonValue } };
}
