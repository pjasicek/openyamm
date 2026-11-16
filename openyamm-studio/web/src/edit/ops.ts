// Operations (S5_BROWSER_EDITOR.md 2.5, 2.6): what a gesture sends to edit.apply, and the client's own copy of the
// same change, applied at once to its file trees so the plan redraws before the core answers (2.13). The core's
// answer replaces the copy; the copy is never the truth. An add without an id stays a ghost here (no id is ever
// invented on the client: 2.6 item 5).
import type { FileTrees, IdPlace, JsonObject, JsonValue, Op, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import { KEYED_LISTS, indexOfKey, isObject, keyedAt, keysOf, resolvePointer, unsegment, walkPointer } from './keys.ts';
import type { KeyedList, Scope } from './keys.ts';

export type Point = [number, number];

// Marks an object added on the client and not answered yet (drawn as a ghost).
export const GHOST = '__ghost';

export class LocalOpError extends Error
{
}

function clone<T>(value: T): T
{
    return structuredClone(value);
}

// Which file holds a list (`to` of an add) when the op does not say.
const LIST_FILES: Record<string, keyof FileTrees> = {
    rooms: 'rooms.yml', openings: 'rooms.yml', themes: 'rooms.yml',
    doors: 'objects.yml', lifts: 'objects.yml', movers: 'objects.yml', plates: 'objects.yml', floors: 'objects.yml',
    ladders: 'objects.yml', sounds: 'objects.yml', lights: 'objects.yml', switches: 'objects.yml', chests: 'objects.yml',
    spawns: 'objects.yml', monsters: 'objects.yml', items: 'objects.yml', decorations: 'objects.yml',
    placeholders: 'objects.yml', exits: 'objects.yml', relations: 'objects.yml',
    events: 'wiring.yml', spaces: 'plan.yml', links: 'plan.yml', goals: 'plan.yml', keys: 'plan.yml', height_bands: 'plan.yml',
    neighbours: 'project.yml',
};

export function fileOfList(list: string, file?: string): keyof FileTrees
{
    return (file as keyof FileTrees | undefined) ?? LIST_FILES[list] ?? 'objects.yml';
}

// Where an id is: its file and list (the file named, else the first file that has it).
function locate(files: FileTrees, id: string, file?: string): { file: keyof FileTrees; list: string; index: number } | null
{
    const names = (file ? [file] : Object.keys(files)) as (keyof FileTrees)[];
    for (const name of names)
    {
        const tree = files[name]?.tree;
        if (!tree)
        {
            continue;
        }
        for (const [list, value] of Object.entries(tree))
        {
            if (Array.isArray(value))
            {
                const index = value.findIndex((item) => isObject(item) && item.id === id);
                if (index >= 0)
                {
                    return { file: name, list, index };
                }
            }
        }
    }
    return null;
}

// The parent of a pointer's last segment and that segment (keyed segments resolved to positions), with the parent's
// keyed-list rule when it is a list.
function parentOf(root: JsonValue, pointer: string, scope?: Scope): { parent: JsonValue; last: string; listName: string; keyed?: KeyedList }
{
    const parts = pointer.split('/').slice(1).map(unsegment);
    if (parts.length === 0)
    {
        throw new LocalOpError('an empty pointer');
    }
    const parentPointer = pointer.slice(0, pointer.lastIndexOf('/'));
    const walked = parentPointer ? walkPointer(root, parentPointer, scope) : { node: root, place: scope?.base ?? '', name: '' };
    if (walked.node === undefined)
    {
        throw new LocalOpError(`nothing at ${parentPointer}`);
    }
    const listName = parts.length >= 2 ? parts[parts.length - 2] : '';
    return { parent: walked.node, last: parts[parts.length - 1], listName, keyed: keyedAt(scope, walked.place) };
}

function listIndex(list: JsonValue[], listName: string, segmentText: string, forInsert: boolean, keyed: KeyedList | undefined): number
{
    if (segmentText === '-' && forInsert)
    {
        return list.length;
    }
    // As the core: a keyed list is addressed by key, except an add at a position (digits).
    if (keyed && !(forInsert && /^\d+$/.test(segmentText)))
    {
        const index = indexOfKey(list, listName, segmentText, keyed);
        if (index < 0)
        {
            throw new LocalOpError(`no item ${segmentText} in ${listName}`);
        }
        return index;
    }
    // A list of objects with ids: by id (as the core).
    if (!/^\d+$/.test(segmentText))
    {
        const found = list.findIndex((item) => isObject(item) && item.id === segmentText);
        if (found < 0)
        {
            throw new LocalOpError(`no item ${segmentText} in ${listName}`);
        }
        return found;
    }
    const index = Number(segmentText);
    if (!Number.isInteger(index) || index < 0 || index > list.length || (!forInsert && index === list.length))
    {
        throw new LocalOpError(`no position ${segmentText}`);
    }
    return index;
}

// JSON Patch on one tree, in place (RFC 6902 with keyed segments, 2.6 item 3).
// `scope`: the root's file and place (the sketch's keyed lists are told by place).
export function applyPatch(root: JsonValue, steps: readonly PatchStep[], scope?: Scope): void
{
    for (const step of steps)
    {
        if (step.op === 'test')
        {
            if (JSON.stringify(resolvePointer(root, step.path, scope)) !== JSON.stringify(step.value))
            {
                throw new LocalOpError(`${step.path} changed since`);
            }
            continue;
        }
        if (step.op === 'move' || step.op === 'copy')
        {
            const value = clone(resolvePointer(root, step.from, scope));
            if (value === undefined)
            {
                throw new LocalOpError(`nothing at ${step.from}`);
            }
            if (step.op === 'move')
            {
                // As RFC 6902: the value is removed first, then added at `path` (a key names the same item either
                // way; a position counts after the removal).
                applyPatch(root, [{ op: 'remove', path: step.from }], scope);
            }
            applyPatch(root, [{ op: 'add', path: step.path, value }], scope);
            continue;
        }
        const { parent, last, listName, keyed } = parentOf(root, step.path, scope);
        if (Array.isArray(parent))
        {
            const index = listIndex(parent, listName, last, step.op === 'add', keyed);
            if (step.op === 'add')
            {
                parent.splice(index, 0, clone(step.value));
            }
            else if (step.op === 'replace')
            {
                parent[index] = clone(step.value);
            }
            else
            {
                parent.splice(index, 1);
            }
        }
        else if (isObject(parent))
        {
            if (step.op === 'remove')
            {
                if (!(last in parent))
                {
                    throw new LocalOpError(`nothing at ${step.path}`);
                }
                delete parent[last];
            }
            else if (step.op === 'replace' && !(last in parent))
            {
                throw new LocalOpError(`nothing at ${step.path}`);
            }
            else
            {
                parent[last] = clone((step as { value: JsonValue }).value);
            }
        }
        else
        {
            throw new LocalOpError(`${step.path} is inside a plain value`);
        }
    }
}

// The client's copy of a transaction: the files after the operations, or LocalOpError (the gesture then waits for
// the core's answer without a ghost). Only the files the operations touch are copied.
export function applyOpsLocally(files: FileTrees, ops: readonly Op[]): FileTrees
{
    const out: FileTrees = { ...files };
    const copied = new Set<string>();
    const tree = (name: keyof FileTrees): JsonObject =>
    {
        if (!copied.has(name))
        {
            out[name] = { tree: clone(files[name]?.tree ?? {}) };
            copied.add(name);
        }
        return out[name]!.tree;
    };
    for (const op of ops)
    {
        switch (op.op)
        {
        case 'add':
        {
            const root = tree(fileOfList(op.to, op.file));
            const list = Array.isArray(root[op.to]) ? (root[op.to] as JsonValue[]) : (root[op.to] = []);
            list.push(op.value.id ? clone(op.value) : { ...clone(op.value), [GHOST]: true });
            break;
        }
        case 'set':
        case 'replace':
        case 'remove':
        case 'patch':
        {
            if (op.op === 'patch' && !op.id)
            {
                if (!op.file)
                {
                    throw new LocalOpError('a patch names an id or a file');
                }
                applyPatch(tree(op.file), op.patch, { file: op.file, base: '' });
                break;
            }
            const place = locate(out, op.id!, op.file);
            if (!place)
            {
                throw new LocalOpError(`no object ${op.id}`);
            }
            const list = tree(place.file)[place.list] as JsonObject[];
            if (op.op === 'remove')
            {
                list.splice(place.index, 1);
            }
            else if (op.op === 'replace')
            {
                list[place.index] = { ...clone(op.value), id: op.id! };
            }
            else if (op.op === 'set')
            {
                const object = list[place.index];
                for (const [name, value] of Object.entries(op.fields))
                {
                    if (value === null)
                    {
                        delete object[name];
                    }
                    else
                    {
                        object[name] = clone(value);
                    }
                }
            }
            else
            {
                applyPatch(list[place.index], op.patch, { file: place.file, base: `/${place.list}/*` });
            }
            break;
        }
        case 'set_value':
        {
            const root = tree(op.file);
            const parts = op.path.split('.');
            let node: JsonObject = root;
            for (const part of parts.slice(0, -1))
            {
                if (!isObject(node[part]))
                {
                    node[part] = {};
                }
                node = node[part] as JsonObject;
            }
            if (op.value === null)
            {
                delete node[parts[parts.length - 1]];
            }
            else
            {
                node[parts[parts.length - 1]] = clone(op.value);
            }
            break;
        }
        default:
            // rename and replace_file wait for the core's answer.
            throw new LocalOpError(`${op.op} is applied by the core only`);
        }
    }
    return out;
}

// Every object with an id, by file and list (what project.open's `ids` lists), from the trees.
export function idsOf(files: FileTrees): IdPlace[]
{
    const out: IdPlace[] = [];
    for (const [file, entry] of Object.entries(files) as [keyof FileTrees, { tree: JsonObject } | undefined][])
    {
        if (!entry?.tree || file === 'ids.lock.yml' || file === 'review/pins.yml')
        {
            continue;
        }
        for (const [list, value] of Object.entries(entry.tree))
        {
            if (Array.isArray(value))
            {
                for (const item of value)
                {
                    if (isObject(item) && typeof item.id === 'string')
                    {
                        out.push({ id: item.id, file, list });
                    }
                }
            }
        }
    }
    return out;
}

// --- operations of the indoor tools (3.18) -------------------------------------------------------------------------

export function roomsOf(files: FileTrees): JsonObject[]
{
    const rooms = files['rooms.yml']?.tree.rooms;
    return Array.isArray(rooms) ? rooms.filter(isObject) : [];
}

export function roomById(files: FileTrees, id: string): JsonObject | undefined
{
    return roomsOf(files).find((room) => room.id === id);
}

// Whether a new room needs the party start set after it: a map without a start does not validate, so nothing of
// it would be drawn. The start names the room, whose id is the core's to give, so it follows the add's answer in a
// second transaction folded into the same history entry (merge_key).
export function needsStart(files: FileTrees): boolean
{
    return !files['objects.yml']?.tree.start;
}

export function startOp(room: string): Op
{
    return { op: 'set_value', file: 'objects.yml', path: 'start', value: { room } };
}

// A point of a plain list (an outline, a path) moved: a test of the old value and the new one.
export function movePointsOp(id: string, base: string, moves: { index: number; from: Point; to: Point }[]): Op
{
    const patch: PatchStep[] = [];
    for (const move of moves)
    {
        patch.push({ op: 'test', path: `${base}/${move.index}`, value: move.from });
        patch.push({ op: 'replace', path: `${base}/${move.index}`, value: move.to });
    }
    return { op: 'patch', id, file: 'rooms.yml', patch };
}

// A corner inserted after `index` (double click on an edge), with tests of the edge's two ends.
export function insertPointOp(id: string, base: string, points: readonly Point[], index: number, point: Point, file: keyof FileTrees = 'rooms.yml'): Op
{
    const next = (index + 1) % points.length;
    return { op: 'patch', id, file, patch: [
        { op: 'test', path: `${base}/${index}`, value: points[index] },
        { op: 'test', path: `${base}/${next}`, value: points[next] },
        { op: 'add', path: `${base}/${index + 1}`, value: point },
    ] };
}

export function removePointOp(id: string, base: string, points: readonly Point[], index: number): Op
{
    return { op: 'patch', id, file: 'rooms.yml', patch: [
        { op: 'test', path: `${base}/${index}`, value: points[index] },
        { op: 'remove', path: `${base}/${index}` },
    ] };
}

// An item appended to a keyed list of an object (a room's levels, platforms, pillars): `/list/-` when the list is
// there, else the list made with the item (the core has no list to append to).
export function appendItemOp(id: string, object: JsonObject, list: string, value: JsonObject, file: keyof FileTrees = 'rooms.yml'): Op
{
    return Array.isArray(object[list])
        ? { op: 'patch', id, file, patch: [{ op: 'add', path: `/${list}/-`, value }] }
        : { op: 'patch', id, file, patch: [{ op: 'add', path: `/${list}`, value: [value] }] };
}

// A room's floor or ceiling moved by a step (PgUp, PgDn), keeping the room at least `minimum` high.
export function heightStepOp(room: JsonObject, which: 'floor' | 'ceiling', step: number): Op | null
{
    const floor = Number(room.floor);
    const ceiling = Number(room.ceiling);
    if (!Number.isFinite(floor) || !Number.isFinite(ceiling))
    {
        return null;
    }
    const value = (which === 'floor' ? floor : ceiling) + step;
    if ((which === 'floor' && value >= ceiling) || (which === 'ceiling' && value <= floor))
    {
        return null;
    }
    return { op: 'set', id: String(room.id), file: 'rooms.yml', fields: { [which]: value } };
}

// What Delete removes, as one transaction: an object, with what cannot stand without it (a room's openings and
// their doors, an opening's doors), or a sub-object by its pointer.
export function removeOps(files: FileTrees, ids: readonly IdPlace[], address: string, file?: string): Op[]
{
    const slash = address.indexOf('/');
    if (slash === 0)
    {
        // A sketch word without an id, by its pointer in the file (/heights/ridges/ridge2).
        return [{ op: 'patch', file: (file as keyof FileTrees | undefined) ?? 'sketch.yml', patch: [{ op: 'remove', path: address }] }];
    }
    if (slash > 0)
    {
        const id = address.slice(0, slash);
        return [{ op: 'patch', id, file: (file as keyof FileTrees | undefined) ?? 'rooms.yml', patch: [{ op: 'remove', path: address.slice(slash) }] }];
    }
    const place = ids.find((entry) => entry.id === address && (!file || entry.file === file));
    const ops: Op[] = [{ op: 'remove', id: address, ...(place ? { file: place.file } : file ? { file: file as keyof FileTrees } : {}) }];
    const openings = (files['rooms.yml']?.tree.openings ?? []) as JsonObject[];
    const doors = (files['objects.yml']?.tree.doors ?? []) as JsonObject[];
    const goneOpenings = new Set<string>();
    if (place?.list === 'rooms')
    {
        for (const opening of openings)
        {
            if (opening.from === address || opening.to === address)
            {
                goneOpenings.add(String(opening.id));
                ops.push({ op: 'remove', id: String(opening.id), file: 'rooms.yml' });
            }
        }
    }
    if (place?.list === 'openings')
    {
        goneOpenings.add(address);
    }
    for (const door of doors)
    {
        if (goneOpenings.has(String(door.opening)))
        {
            ops.push({ op: 'remove', id: String(door.id), file: 'objects.yml' });
        }
    }
    return ops;
}

function shifted(value: JsonValue, by: Point): JsonValue
{
    const point = (p: JsonValue): JsonValue => (Array.isArray(p) && p.length >= 2 && typeof p[0] === 'number' && typeof p[1] === 'number'
        ? [p[0] + by[0], p[1] + by[1], ...p.slice(2)] : p);
    if (!isObject(value))
    {
        return value;
    }
    const out: JsonObject = { ...value };
    for (const name of ['outline', 'path'])
    {
        if (Array.isArray(out[name]))
        {
            out[name] = (out[name] as JsonValue[]).map(point);
        }
    }
    if (Array.isArray(out.at))
    {
        out.at = point(out.at);
    }
    for (const [name, list] of Object.entries(out))
    {
        if (KEYED_LISTS[name] && Array.isArray(list))
        {
            out[name] = list.map((item) => shifted(item, by));
        }
    }
    return out;
}

// Ctrl D: a copy beside the original (by `by`), without its id or key so the core gives new ones.
export function duplicateOps(files: FileTrees, ids: readonly IdPlace[], address: string, by: Point, file?: string): Op[]
{
    const slash = address.indexOf('/');
    if (slash >= 0)
    {
        const id = address.slice(0, slash);
        const pointer = address.slice(slash);
        const place = ids.find((entry) => entry.id === id && (!file || entry.file === file));
        const object = place ? (files[place.file]?.tree[place.list] as JsonObject[] | undefined)?.find((item) => item.id === id) : undefined;
        const item = object ? resolvePointer(object, pointer) : undefined;
        if (!isObject(item))
        {
            return [];
        }
        const listName = unsegment(pointer.split('/')[1]);
        const keyField = KEYED_LISTS[listName]?.field ?? 'key';
        const copy = shifted(item, by) as JsonObject;
        delete copy[keyField];
        delete copy.id;
        return [{ op: 'patch', id, file: place!.file, patch: [{ op: 'add', path: `/${listName}/-`, value: copy }] }];
    }
    const place = ids.find((entry) => entry.id === address && (!file || entry.file === file));
    const list = place ? (files[place.file]?.tree[place.list] as JsonObject[] | undefined) : undefined;
    const object = list?.find((item) => item.id === address);
    if (!place || !object)
    {
        return [];
    }
    const copy = shifted(object, by) as JsonObject;
    delete copy.id;
    // A room's copy realises no plan space of its own.
    delete copy.space;
    return [{ op: 'add', to: place.list, file: place.file, value: copy }];
}

// The id a result gave a gesture's first add ("rooms.yml#room:room_3" -> room:room_3).
export function allocatedId(allocated: readonly string[] | undefined, list?: string): string | null
{
    for (const entry of allocated ?? [])
    {
        const id = entry.slice(entry.indexOf('#') + 1);
        if (!list || id.startsWith(`${list.replace(/s$/, '')}:`) || list === 'rooms' && id.startsWith('room:'))
        {
            return id;
        }
    }
    return null;
}

// The keyed item a patch's append made: its key in the core's answer (the last item of the list).
export function appendedKey(object: JsonObject | undefined, list: string, keyed?: KeyedList): string | null
{
    const items = object?.[list];
    if (!Array.isArray(items) || items.length === 0)
    {
        return null;
    }
    return keysOf(items, list, keyed ?? KEYED_LISTS[list])[items.length - 1];
}

// Door presets of the Door tool's options (3.18 "Door library"): each fills the door words.
export const DOOR_PRESETS: { name: string; label: string; words: JsonObject }[] = [
    { name: 'wooden', label: 'Wooden door', words: { kind: 'hinged' } },
    { name: 'portcullis', label: 'Portcullis', words: { kind: 'slide_up' } },
    { name: 'sliding', label: 'Sliding stone', words: { kind: 'slide_left' } },
    { name: 'double', label: 'Double sliding', words: { kind: 'slide_left', leaves: 2 } },
    { name: 'sinking', label: 'Sinking slab', words: { kind: 'slide_down' } },
    { name: 'secret', label: 'Secret wall', words: { kind: 'slide_up', secret: true } },
];

export function doorOp(opening: string, preset: string): Op
{
    const words = DOOR_PRESETS.find((entry) => entry.name === preset)?.words ?? DOOR_PRESETS[0].words;
    return { op: 'add', to: 'doors', file: 'objects.yml', value: { opening, ...words } };
}
