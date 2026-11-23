// Keys of sub-objects (S5_BROWSER_EDITOR.md 2.6 item 2, format 1): lists a person selects items of carry a key
// unique within their parent, named in pointers (/pillars/pillar2/at) and addresses (room:hall/pillars/pillar2).
// A missing key reads as <prefix><position + 1>, the next free number on a clash, as the core reads it.
//
// Which lists are keyed is the schemas' x-key and x-key-prefix at the list's place. The indoor files' keyed lists are
// named alike wherever they are, so they are told by property name (KEYED_LISTS); sketch.yml's are not (a building's
// `parts` are keyed by id, a mover's by key; `points` are top-level ids and `heights.points` keys), so they are told
// by place: the property names from the file's root with `*` for a row (SKETCH_KEYED). keys.test.ts checks both
// tables against the schemas.
import type { JsonObject, JsonValue } from '../../../schema/rpc/generated/rpc.ts';

export interface KeyedList
{
    // The field holding the key (key, wall, id).
    field: string;
    // What a missing key reads as, with its position.
    prefix?: string;
}

// Where a node lies: its file and the place of the node itself ('/structures/*', '/heights/ridges/*'). Without a
// file the indoor rule (by property name) holds.
export interface Scope
{
    file?: string;
    base?: string;
}

// The keyed lists inside the indoor files' objects, by property name.
export const KEYED_LISTS: Record<string, KeyedList> = {
    pillars: { field: 'key', prefix: 'pillar' },
    platforms: { field: 'key', prefix: 'platform' },
    levels: { field: 'key', prefix: 'level' },
    ceiling_levels: { field: 'key', prefix: 'ceiling_level' },
    flights: { field: 'key', prefix: 'flight' },
    parapets: { field: 'key', prefix: 'parapet' },
    beams: { field: 'key', prefix: 'beam' },
    stalactites: { field: 'key', prefix: 'stalactite' },
    floor_surfaces: { field: 'key', prefix: 'floor_part' },
    ceiling_surfaces: { field: 'key', prefix: 'ceiling_part' },
    panels: { field: 'key', prefix: 'panel' },
    parts: { field: 'key', prefix: 'part' },
    walls: { field: 'wall' },
};

const key = (prefix: string): KeyedList => ({ field: 'key', prefix });
const PART_LISTS = (base: string): Record<string, KeyedList> => ({
    [`${base}/holes`]: key('hole'), [`${base}/porches`]: key('porch'), [`${base}/signs`]: key('sign'),
});

// sketch.yml's keyed lists by place (lists of objects with ids included: they are addressed by id).
export const SKETCH_KEYED: Record<string, KeyedList> = {
    '/frame/edges': key('edge'),
    '/frame/rim': key('rim'),
    '/heights/points': key('point'),
    '/heights/bands': key('band'),
    '/heights/cliffs': key('cliff'),
    '/heights/ridges': key('ridge'),
    '/heights/terraces': key('terrace'),
    '/heights/terraces/*/ramps': key('ramp'),
    '/heights/cuts': key('cut'),
    '/heights/cuts/*/ramps': key('ramp'),
    '/heights/rough': key('rough'),
    '/heights/spires': key('spire'),
    '/heights/nodes': key('block'),
    '/heights/peaks': key('peaks'),
    '/heights/strokes': key('stroke'),
    '/heights/smooth': key('smooth'),
    '/heights/patches': key('patch'),
    '/water/bodies': { field: 'id' },
    '/water/rivers': { field: 'id' },
    '/water/shores': key('shore'),
    '/void': { field: 'id' },
    '/roads': key('road'),
    '/districts': key('district'),
    '/districts/*/plots': key('plot'),
    '/districts/*/plots/*/parts': { field: 'id', prefix: 'part' },
    '/districts/*/plots/*/doors': key('door'),
    ...PART_LISTS('/districts/*/plots/*/parts/*'),
    '/points': { field: 'id' },
    '/areas': { field: 'id' },
    '/views': { field: 'id' },
    '/scatter': { field: 'id' },
    '/ground': key('zone'),
    '/structures': { field: 'id' },
    '/structures/*/holes': key('hole'),
    '/structures/*/gates': key('gate'),
    '/structures/*/parts': { field: 'id', prefix: 'part' },
    '/structures/*/doors': key('door'),
    '/structures/*/arms': key('arm'),
    ...PART_LISTS('/structures/*/parts/*'),
    '/actors': { field: 'id' },
    '/events': { field: 'id' },
};

// The keyed list at a place of a file, or undefined (a plain list, or not a list).
export function keyedAt(scope: Scope | undefined, place: string): KeyedList | undefined
{
    if (scope?.file === 'sketch.yml')
    {
        return SKETCH_KEYED[place];
    }
    return KEYED_LISTS[place.slice(place.lastIndexOf('/') + 1)];
}

export function isObject(value: JsonValue | undefined): value is JsonObject
{
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

// The keys of a keyed list's items, in order: written ones as written, missing ones as the core reads them. `keyed`
// is the list's rule (by default the indoor one of its name).
export function keysOf(list: readonly JsonValue[], name: string, keyed: KeyedList | undefined = KEYED_LISTS[name]): string[]
{
    if (!keyed)
    {
        return list.map((_, index) => String(index));
    }
    const written = new Set<string>();
    for (const item of list)
    {
        const value = isObject(item) ? item[keyed.field] : undefined;
        if (value !== undefined && value !== null)
        {
            written.add(String(value));
        }
    }
    const used = new Set(written);
    const prefix = keyed.prefix ?? name;
    return list.map((item, index) =>
    {
        const value = isObject(item) ? item[keyed.field] : undefined;
        if (value !== undefined && value !== null)
        {
            return String(value);
        }
        let number = index + 1;
        while (used.has(`${prefix}${number}`))
        {
            ++number;
        }
        const made = `${prefix}${number}`;
        used.add(made);
        return made;
    });
}

// The position of an item in a keyed list by its key (or -1).
export function indexOfKey(list: readonly JsonValue[], name: string, key: string, keyed: KeyedList | undefined = KEYED_LISTS[name]): number
{
    return keysOf(list, name, keyed).indexOf(key);
}

// A JSON pointer segment (~0 and ~1 escaped).
export function segment(text: string | number): string
{
    return String(text).replace(/~/g, '~0').replace(/\//g, '~1');
}

export function unsegment(text: string): string
{
    return text.replace(/~1/g, '/').replace(/~0/g, '~');
}

// The position a segment names in a list: a keyed list's key, a list of objects with ids' id, else a position.
function positionIn(list: readonly JsonValue[], name: string, keyed: KeyedList | undefined, part: string): number
{
    if (keyed)
    {
        return indexOfKey(list, name, part, keyed);
    }
    if (/^\d+$/.test(part))
    {
        return Number(part);
    }
    return list.findIndex((item) => isObject(item) && item.id === part);
}

// A pointer into an object from a path of property names and positions: a position in a keyed list becomes the
// item's key, a position in a plain list stays a position. `positional` says whether the pointer passes through a
// plain list (then a patch needs a test step of the old value).
export function pointerOf(root: JsonValue, path: readonly (string | number)[], scope?: Scope): { pointer: string; positional: boolean }
{
    let node: JsonValue | undefined = root;
    let parentName = '';
    let place = scope?.base ?? '';
    let positional = false;
    const parts: string[] = [];
    for (const step of path)
    {
        if (typeof step === 'number' && Array.isArray(node))
        {
            const item = node[step];
            const keyed = keyedAt(scope, place);
            if (keyed && keyed.field !== 'id')
            {
                parts.push(segment(keysOf(node, parentName, keyed)[step] ?? String(step)));
            }
            else if (isObject(item) && typeof item.id === 'string')
            {
                // A list of objects with ids is addressed by id, as the core addresses it (a file's own lists).
                parts.push(segment(item.id));
            }
            else if (keyed)
            {
                // An id-keyed list's item without an id (a building's part): by the key the core reads.
                parts.push(segment(keysOf(node, parentName, keyed)[step] ?? String(step)));
            }
            else
            {
                parts.push(String(step));
                positional = true;
            }
            node = node[step];
            place += '/*';
        }
        else
        {
            parts.push(segment(step));
            parentName = String(step);
            place += `/${parentName}`;
            node = isObject(node) ? node[String(step)] : undefined;
        }
    }
    return { pointer: parts.map((part) => `/${part}`).join(''), positional };
}

// What a pointer names inside a tree, and its place (keyed segments read as keys), or undefined.
export function walkPointer(root: JsonValue | undefined, pointer: string, scope?: Scope): { node: JsonValue | undefined; place: string; name: string }
{
    let node = root;
    let parentName = '';
    let place = scope?.base ?? '';
    for (const raw of pointer.split('/').slice(1))
    {
        const part = unsegment(raw);
        if (Array.isArray(node))
        {
            const index = positionIn(node, parentName, keyedAt(scope, place), part);
            node = index >= 0 ? node[index] : undefined;
            place += '/*';
        }
        else if (isObject(node))
        {
            node = node[part];
            parentName = part;
            place += `/${part}`;
        }
        else
        {
            return { node: undefined, place, name: parentName };
        }
    }
    return { node, place, name: parentName };
}

export function resolvePointer(root: JsonValue | undefined, pointer: string, scope?: Scope): JsonValue | undefined
{
    return walkPointer(root, pointer, scope).node;
}

// The place of what a pointer names ('/heights/ridges' for /heights/ridges, '/heights/ridges/*' for a ridge).
export function placeOf(root: JsonValue | undefined, pointer: string, scope?: Scope): string
{
    return walkPointer(root, pointer, scope).place;
}

// The place of a pointer without the tree: each segment after a list's name is a row (the pointers the tools write:
// /structures/thing:hall/parts/main -> /structures/*/parts/*).
export function placeOfPointer(pointer: string, scope?: Scope): string
{
    let place = scope?.base ?? '';
    let afterList = false;
    for (const raw of pointer.split('/').slice(1))
    {
        if (afterList)
        {
            place += '/*';
            afterList = false;
            continue;
        }
        place += `/${unsegment(raw)}`;
        afterList = keyedAt(scope, place) !== undefined;
    }
    return place;
}

// An address (room:hall/pillars/pillar2) split into the top-level id and the pointer inside it. A sketch word
// without an id is addressed by its pointer in the file (/heights/ridges/ridge2): its id is empty.
export function splitAddress(address: string): { id: string; pointer: string }
{
    const slash = address.indexOf('/');
    return slash < 0 ? { id: address, pointer: '' } : { id: address.slice(0, slash), pointer: address.slice(slash) };
}

// The addresses of an object's keyed sub-objects one level down (room:hall/pillars/pillar1, ...), list by list.
export function subAddresses(id: string, object: JsonObject, scope?: Scope): { address: string; list: string; key: string; index: number }[]
{
    const out: { address: string; list: string; key: string; index: number }[] = [];
    for (const [name, value] of Object.entries(object))
    {
        const keyed = keyedAt(scope, `${scope?.base ?? ''}/${name}`);
        if (keyed && Array.isArray(value))
        {
            keysOf(value, name, keyed).forEach((key, index) => out.push({ address: `${id}/${name}/${segment(key)}`, list: name, key, index }));
        }
    }
    return out;
}
