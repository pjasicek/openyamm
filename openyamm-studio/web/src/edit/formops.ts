// The inspector's edits as operations (S5_BROWSER_EDITOR.md 3.8, 2.6): a field of a top-level object is a `set`;
// anything deeper, and anything of a keyed sub-object, a `patch` whose pointer names keyed rows by their key and
// plain rows by position with a `test` of the old value. Rows of keyed lists are added, removed, duplicated and
// moved by key; a key is renamed by op rename (its pins follow).
import type { Json } from '../schema/registry.ts';
import type { FileName, JsonObject, JsonValue, Op, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import { isObject, keyedAt, keysOf, placeOf, pointerOf, resolvePointer, segment } from './keys.ts';
import type { KeyedList, Scope } from './keys.ts';

export type Path = (string | number)[];

// What the inspector shows: a top-level object, or a keyed sub-object of one (its pointer inside it).
export interface Target
{
    // The top-level id; '' for a file's own words (the inspector of plan.yml, project.yml with nothing selected).
    id: string;
    file: string;
    // The pointer of a sub-object inside the top-level object ('' for the object itself).
    pointer: string;
    // The shown object's value (the sub-object's for a sub-object).
    value: JsonObject;
    // The value's place in its file ('/structures/*', '/heights/ridges/*'): how sketch.yml's keyed lists are told.
    // Left out: the indoor rule (keyed lists by name).
    place?: string;
}

function scopeOf(target: Target): Scope
{
    return { file: target.file, ...(target.place !== undefined ? { base: target.place } : {}) };
}

function patch(target: Target, steps: PatchStep[]): Op
{
    return target.id ? { op: 'patch', id: target.id, file: target.file as FileName, patch: steps } : { op: 'patch', file: target.file as FileName, patch: steps };
}

// A field's new value (undefined: remove it).
export function fieldOp(target: Target, path: Path, value: Json | undefined): Op
{
    if (target.id && !target.pointer && path.length === 1 && typeof path[0] === 'string')
    {
        return { op: 'set', id: target.id, file: target.file as FileName, fields: { [path[0]]: (value ?? null) as JsonValue } };
    }
    const scope = scopeOf(target);
    const { pointer, positional } = pointerOf(target.value, path, scope);
    const full = target.pointer + pointer;
    const old = resolvePointer(target.value, pointer, scope);
    const steps: PatchStep[] = [];
    if (positional && old !== undefined)
    {
        steps.push({ op: 'test', path: full, value: old });
    }
    if (value === undefined)
    {
        steps.push({ op: 'remove', path: full });
    }
    else
    {
        steps.push({ op: old === undefined ? 'add' : 'replace', path: full, value: value as JsonValue });
    }
    return patch(target, steps);
}

// The list at `path`, its name and its keyed-list rule (the last property name on the way).
function listAt(target: Target, path: Path): { pointer: string; list: JsonValue[] | undefined; name: string; positional: boolean; keyed?: KeyedList }
{
    const scope = scopeOf(target);
    const { pointer, positional } = pointerOf(target.value, path, scope);
    const list = resolvePointer(target.value, pointer, scope);
    const name = String([...path].reverse().find((step) => typeof step === 'string') ?? '');
    const place = target.place !== undefined || target.file === 'sketch.yml' ? placeOf(target.value, pointer, scope) : `/${name}`;
    return { pointer: target.pointer + pointer, list: Array.isArray(list) ? list : undefined, name, positional, keyed: keyedAt(scope, place) };
}

function rowSegment(list: JsonValue[], name: string, index: number, keyed: KeyedList | undefined): string
{
    const item = list[index];
    if (keyed && (keyed.field !== 'id' || !(isObject(item) && typeof item.id === 'string')))
    {
        return segment(keysOf(list, name, keyed)[index]);
    }
    // A list of objects with ids is addressed by id (as the core addresses it).
    return isObject(item) && typeof item.id === 'string' ? segment(item.id) : String(index);
}

export type RowAction = 'remove' | 'duplicate' | 'up' | 'down';

// A row added to the list at `path` (made when absent).
export function addRowOp(target: Target, path: Path, value: Json): Op
{
    // An object of a file's own list of objects with ids (plan.yml keys, height bands, states): added by op add, so
    // the core gives its id.
    if (!target.id && !target.pointer && path.length === 1 && typeof path[0] === 'string' && isObject(value as JsonValue))
    {
        const { id: _id, ...rest } = value as JsonObject;
        void _id;
        return { op: 'add', to: path[0], file: target.file as FileName, value: rest };
    }
    const { pointer, list } = listAt(target, path);
    return patch(target, list ? [{ op: 'add', path: `${pointer}/-`, value: value as JsonValue }] : [{ op: 'add', path: pointer, value: [value as JsonValue] }]);
}

export function rowOp(target: Target, path: Path, index: number, action: RowAction): Op | null
{
    const { pointer, list, name, positional, keyed: rule } = listAt(target, path);
    if (!list || index < 0 || index >= list.length)
    {
        return null;
    }
    const keyed = Boolean(rule);
    const at = `${pointer}/${rowSegment(list, name, index, rule)}`;
    const tests: PatchStep[] = !keyed || positional ? [{ op: 'test', path: at, value: list[index] }] : [];
    switch (action)
    {
    case 'remove':
        return patch(target, [...tests, { op: 'remove', path: at }]);
    case 'duplicate':
    {
        const copy = structuredClone(list[index]);
        if (keyed && isObject(copy))
        {
            delete copy[rule!.field];
            delete copy.id;
        }
        return patch(target, [...tests, { op: 'add', path: keyed ? `${pointer}/-` : `${pointer}/${index + 1}`, value: copy }]);
    }
    case 'up':
        if (index === 0)
        {
            return null;
        }
        return patch(target, [...tests, { op: 'move', from: at, path: `${pointer}/${rowSegment(list, name, index - 1, rule)}` }]);
    case 'down':
        if (index >= list.length - 1)
        {
            return null;
        }
        if (!keyed)
        {
            return patch(target, [...tests, { op: 'move', from: at, path: `${pointer}/${index + 1}` }]);
        }
        // Before the row after next, or at the end.
        return patch(target, [...tests, { op: 'move', from: at, path: index + 2 < list.length ? `${pointer}/${rowSegment(list, name, index + 2, rule)}` : `${pointer}/-` }]);
    }
}

// A keyed row's key renamed (selections and pins on it follow, 2.6 item 4).
export function renameKeyOp(target: Target, path: Path, index: number, to: string): Op | null
{
    const { pointer, list, name, keyed } = listAt(target, path);
    if (!list || !keyed || keyed.field !== 'key')
    {
        return null;
    }
    return { op: 'rename', ...(target.id ? { id: target.id } : {}), file: target.file as FileName, path: `${pointer}/${rowSegment(list, name, index, keyed)}`, to };
}

// The Source tab's Apply: the whole object replaced (a sub-object: replaced by a patch at its pointer).
export function replaceOp(target: Target, value: JsonObject): Op
{
    if (!target.pointer)
    {
        const { id: _id, ...rest } = value;
        void _id;
        return { op: 'replace', id: target.id, file: target.file as FileName, value: rest };
    }
    return patch(target, [{ op: 'replace', path: target.pointer, value }]);
}
