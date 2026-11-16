// Reading the project's file trees (project.open): where an object is, what an issue's path names, which object
// a face's owner is. The trees are read-only data at a revision (S5_BROWSER_EDITOR.md 4.6); nothing here edits.
import type { FileTrees, IdPlace, Issue, JsonValue, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import { keyedAt, keysOf, unsegment, walkPointer } from '../edit/keys.ts';

export type FileName = keyof FileTrees;

export interface ObjectRef
{
    id: string;
    // Ids are unique per file, not across files (a plan's space and its room share one).
    file?: string;
}

export interface FoundObject
{
    id: string;
    file: string;
    list: string;
    index: number;
    value: JsonObject;
    // A keyed sub-object (room:hall/pillars/pillar2): the pointer inside the top-level object, the top-level list
    // the object is in (list is then the keyed list's name), and the top-level object itself.
    pointer?: string;
    parentList?: string;
    parent?: JsonObject;
    // sketch.yml: the value's place in the file ('/structures/*/parts/*', '/heights/ridges/*'), by which its schema and
    // its keyed lists are found.
    place?: string;
}

export function treeOf(files: FileTrees | undefined, file: string): JsonObject | undefined
{
    const entry = files?.[file as FileName];
    return entry?.tree as JsonObject | undefined;
}

// The object of an id: in the file named, else the first file holding it (rooms before plan, so a room wins over
// its plan space when no file is named).
export function findObject(files: FileTrees | undefined, ids: IdPlace[], ref: ObjectRef): FoundObject | undefined
{
    const places = ids.filter((place) => place.id === ref.id && (!ref.file || place.file === ref.file));
    if (places.length === 0)
    {
        return undefined;
    }
    const order = ['rooms.yml', 'objects.yml', 'sketch.yml', 'wiring.yml', 'plan.yml', 'project.yml', 'atmosphere.yml'];
    places.sort((a, b) => order.indexOf(a.file) - order.indexOf(b.file));
    const place = places[0];
    const list = treeOf(files, place.file)?.[place.list];
    if (!Array.isArray(list))
    {
        return undefined;
    }
    const index = list.findIndex((item) => isObject(item) && item.id === ref.id);
    if (index < 0)
    {
        return undefined;
    }
    return { id: ref.id, file: place.file, list: place.list, index, value: list[index] as JsonObject };
}

// An address: a top-level id, or a keyed sub-object below one (room:hall/pillars/pillar2; outdoors also deeper,
// thing:hall/parts/main), as author mode selects them (S5_BROWSER_EDITOR.md 2.6 item 2); or a sketch word without an
// id by its pointer in its file (/heights/ridges/ridge2, with file sketch.yml).
export function findAddress(files: FileTrees | undefined, ids: IdPlace[], ref: ObjectRef): FoundObject | undefined
{
    if (ref.id.startsWith('/'))
    {
        const file = ref.file ?? 'sketch.yml';
        const scope = { file, base: '' };
        const tree = treeOf(files, file);
        const walked = walkPointer(tree, ref.id, scope);
        const parts = ref.id.split('/');
        const listPointer = parts.slice(0, -1).join('/');
        const list = walkPointer(tree, listPointer, scope);
        if (!isObject(walked.node) || !Array.isArray(list.node))
        {
            return undefined;
        }
        const listName = unsegment(parts[parts.length - 2]);
        const index = keysOf(list.node, listName, keyedAt(scope, list.place)).indexOf(unsegment(parts[parts.length - 1]));
        return { id: ref.id, file, list: listName, index, value: walked.node, pointer: ref.id, place: walked.place };
    }
    const slash = ref.id.indexOf('/');
    if (slash < 0)
    {
        const found = findObject(files, ids, ref);
        return found && found.file === 'sketch.yml' ? { ...found, place: `/${found.list}/*` } : found;
    }
    const owner = findObject(files, ids, { id: ref.id.slice(0, slash), file: ref.file });
    if (!owner)
    {
        return undefined;
    }
    const pointer = ref.id.slice(slash);
    const sketch = owner.file === 'sketch.yml';
    const scope = sketch ? { file: owner.file, base: `/${owner.list}/*` } : { file: owner.file };
    const parts = pointer.split('/');
    if (parts.length < 3)
    {
        return undefined;
    }
    const walked = walkPointer(owner.value, pointer, scope);
    const list = walkPointer(owner.value, parts.slice(0, -1).join('/'), scope);
    if (!isObject(walked.node) || !Array.isArray(list.node))
    {
        return undefined;
    }
    const listName = unsegment(parts[parts.length - 2]);
    const index = keysOf(list.node, listName, keyedAt(scope, list.place)).indexOf(unsegment(parts[parts.length - 1]));
    return { id: ref.id, file: owner.file, list: listName, index, value: walked.node, pointer, parentList: owner.list, parent: owner.value,
        ...(sketch ? { place: walked.place } : {}) };
}

export function isObject(value: JsonValue | undefined): value is JsonObject
{
    return typeof value === 'object' && value !== null && !Array.isArray(value);
}

// "room:hall/walls/3" -> "room:hall": the top-level id of a face owner or a keyed path.
export function baseId(owner: string): string
{
    const slash = owner.indexOf('/');
    return slash < 0 ? owner : owner.slice(0, slash);
}

// The top-level object an issue's path points into ("rooms[3].floor" in rooms.yml -> the fourth room's id).
export function issueObject(files: FileTrees | undefined, issue: Pick<Issue, 'file' | 'path'>): ObjectRef | undefined
{
    const match = /^([a-z_]+)\[(\d+)\]/.exec(issue.path);
    if (!match)
    {
        return undefined;
    }
    const list = treeOf(files, issue.file)?.[match[1]];
    if (!Array.isArray(list))
    {
        return undefined;
    }
    const item = list[Number(match[2])];
    return isObject(item) && typeof item.id === 'string' ? { id: item.id, file: issue.file } : undefined;
}

// Every id of the project, for search and the pickers.
export function allIds(ids: IdPlace[]): string[]
{
    return [...new Set(ids.map((place) => place.id))];
}

// Search: ids containing every word of the query, those starting with it first.
export function searchIds(ids: IdPlace[], query: string, limit = 50): IdPlace[]
{
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    if (words.length === 0)
    {
        return [];
    }
    const hits = ids.filter((place) => words.every((word) => place.id.toLowerCase().includes(word)));
    hits.sort((a, b) =>
    {
        const aStarts = a.id.toLowerCase().startsWith(words[0]) || a.id.toLowerCase().includes(':' + words[0]) ? 0 : 1;
        const bStarts = b.id.toLowerCase().startsWith(words[0]) || b.id.toLowerCase().includes(':' + words[0]) ? 0 : 1;
        return aStarts - bStarts || a.id.localeCompare(b.id);
    });
    return hits.slice(0, limit);
}
