// The Overlay tab's own tools (devdocs/map_studio/S6_PLAN.md item O, what remained: "bespoke overlay tools"): what a
// gesture on an overlay project's scene things writes into objects.yml `scene` (S6's words). A base map's thing is
// changed by an entry of `changes` (`of` its lock id and only the words that change; a base ladder is moved by its
// `offset`), taken out by `removals`, put back by dropping it from there; a thing the project adds (a pulsing light,
// a placed sound, a spawn point, and since S8a a ladder, a monster or a floor item) is placed by its absolute position
// and changed or deleted where it stands in its list. Each gesture is one keyed `patch` of
// objects.yml with `test` steps, so it is refused when someone else changed the same words since (S5_BROWSER_EDITOR.md
// 2.6). Pure: the panel draws, this decides.
import type { FileTrees, JsonObject, JsonValue, Op, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import type { OverlayThing } from './overlay.ts';

export type AddedList = 'lights' | 'sounds' | 'spawns' | 'destructibles' | 'water' | 'ladders' | 'monsters' | 'items';
// The lists a click on the plan adds to.
export type NewList = 'lights' | 'sounds' | 'spawns' | 'ladders' | 'monsters' | 'items';

// The kinds of view.overlay and the scene lists that hold a project's own things of each.
export const LIST_OF_KIND: Record<OverlayThing['kind'], AddedList> = {
    light: 'lights', sound: 'sounds', spawn: 'spawns', destructible: 'destructibles', water: 'water',
    ladder: 'ladders', monster: 'monsters', item: 'items',
};

// rgb and xyz: three numbers; pair: two; facing: a compass side or degrees; ref: a table's number or a name.
export type FieldType = 'rgb' | 'xyz' | 'pair' | 'number' | 'integer' | 'boolean' | 'text' | 'facing' | 'ref';

export interface FieldSpec
{
    name: string;
    type: FieldType;
    label: string;
}

// The words a change may carry, by kind (objects.schema.json scene.changes: only those of its kind); a spawn point is
// not changed, only taken out (the overlay's removals) or added anew.
export const CHANGE_FIELDS: Record<OverlayThing['kind'], FieldSpec[]> = {
    light: [
        { name: 'color', type: 'rgb', label: 'Colour [r, g, b]' },
        { name: 'intensity', type: 'pair', label: 'Brightness [low, high]' },
        { name: 'radius', type: 'pair', label: 'Reach [small, large]' },
        { name: 'frequency', type: 'number', label: 'Swings a second' },
        { name: 'phase', type: 'number', label: 'Phase 0 to 1' },
        { name: 'on', type: 'boolean', label: 'On at the start' },
    ],
    sound: [
        { name: 'sound', type: 'text', label: 'Sound file' },
        { name: 'radius', type: 'number', label: 'Heard within' },
        { name: 'inner_radius', type: 'number', label: 'Full volume within' },
        { name: 'volume', type: 'number', label: 'Volume 0 to 1' },
        { name: 'loop', type: 'boolean', label: 'Loops' },
        { name: 'wait', type: 'pair', label: 'Wait [shortest, longest] s' },
        { name: 'on', type: 'boolean', label: 'On at the start' },
    ],
    destructible: [
        { name: 'hp', type: 'integer', label: 'Hit points' },
        { name: 'damage', type: 'boolean', label: 'Blows harm it' },
        { name: 'trigger_only', type: 'boolean', label: 'Only events break it' },
        { name: 'sound', type: 'text', label: 'Breaking sound' },
    ],
    water: [
        { name: 'tint', type: 'rgb', label: 'Tint [r, g, b] 0 to 1' },
        { name: 'current', type: 'pair', label: 'Current [x, y]' },
    ],
    ladder: [
        { name: 'offset', type: 'xyz', label: 'Moved by [dx, dy, dz]' },
        { name: 'facing', type: 'facing', label: 'Climber looks (n, e ... or degrees)' },
        { name: 'width', type: 'number', label: 'Width' },
        { name: 'reach', type: 'number', label: 'Reach' },
        { name: 'exit', type: 'pair', label: 'Steps off at [x, y]' },
        { name: 'grab_at_top', type: 'boolean', label: 'Taken from the top' },
        { name: 'grab_in_air', type: 'boolean', label: 'Taken in the air' },
    ],
    spawn: [],
    monster: [],
    item: [],
};

// The words of a thing the project adds, by its list (objects.schema.json scene.lights, sounds, spawns).
export const ADDED_FIELDS: Partial<Record<AddedList, FieldSpec[]>> = {
    lights: [...CHANGE_FIELDS.light, { name: 'radius_frequency', type: 'number', label: 'Reach swings a second' }],
    sounds: [...CHANGE_FIELDS.sound, { name: 'day_only', type: 'boolean', label: 'Day only' }, { name: 'night_only', type: 'boolean', label: 'Night only' }],
    spawns: [
        { name: 'kind', type: 'text', label: 'monster or item' },
        { name: 'slot', type: 'integer', label: 'Encounter slot 1 to 3' },
        { name: 'treasure_level', type: 'integer', label: 'Treasure level (item)' },
        { name: 'radius', type: 'number', label: 'Spread' },
        { name: 'group', type: 'integer', label: 'Actor group' },
    ],
    ladders: [
        { name: 'facing', type: 'facing', label: 'Climber looks (n, e ... or degrees)' },
        { name: 'height', type: 'number', label: 'Climbs' },
        { name: 'top_at', type: 'pair', label: 'Leaning: top at [x, y]' },
        { name: 'width', type: 'number', label: 'Width' },
        { name: 'reach', type: 'number', label: 'Reach' },
        { name: 'exit', type: 'pair', label: 'Steps off at [x, y]' },
        { name: 'grab_at_top', type: 'boolean', label: 'Taken from the top' },
        { name: 'grab_in_air', type: 'boolean', label: 'Taken in the air' },
    ],
    monsters: [
        { name: 'monster', type: 'ref', label: 'Monster (number or name)' },
        { name: 'facing', type: 'facing', label: 'Looks (n, e ... or degrees)' },
        { name: 'hostile', type: 'boolean', label: 'Hostile whatever its kind' },
        { name: 'group', type: 'integer', label: 'Actor group' },
        { name: 'hp', type: 'integer', label: 'Hit points of its own' },
        { name: 'name', type: 'text', label: 'Name of its own' },
        { name: 'immobile', type: 'boolean', label: 'Keeps its place' },
        { name: 'hidden', type: 'boolean', label: 'Starts hidden (needs a group)' },
        { name: 'carries', type: 'ref', label: 'Carries (item number or name)' },
    ],
    items: [
        { name: 'item', type: 'ref', label: 'Item (number or name)' },
        { name: 'gold', type: 'integer', label: 'Gold (a heap of gold)' },
    ],
};

// What a new thing starts as (the schema's required words and a visible default).
export const NEW_THING: Record<NewList, JsonObject> = {
    lights: { color: [255, 200, 140], intensity: [0.6, 1], radius: [384, 640], frequency: 0.5 },
    sounds: { sound: 'ambient/water/waves02.wav', radius: 900 },
    spawns: { kind: 'monster', slot: 1 },
    ladders: { facing: 'n', height: 256 },
    monsters: { monster: 1 },
    items: { item: 1 },
};

export const PREFIX: Record<NewList, string> = {
    lights: 'light', sounds: 'sound', spawns: 'spawn', ladders: 'ladder', monsters: 'monster', items: 'item',
};

export type OverlayGesture =
    | { kind: 'add'; list: NewList; id: string; position: [number, number, number]; value?: JsonObject }
    | { kind: 'move'; list: AddedList; id: string; position: [number, number, number] }
    | { kind: 'change'; of: string; fields: Record<string, JsonValue | null> }
    | { kind: 'set'; list: AddedList; id: string; fields: Record<string, JsonValue | null> }
    | { kind: 'remove'; of: string }
    | { kind: 'restore'; of: string }
    | { kind: 'delete'; list: AddedList; id: string };

function sceneOf(files: FileTrees | undefined): JsonObject | undefined
{
    const scene = files?.['objects.yml']?.tree.scene;
    return scene && typeof scene === 'object' && !Array.isArray(scene) ? scene as JsonObject : undefined;
}

function listOf(scene: JsonObject | undefined, name: string): JsonValue[] | undefined
{
    const list = scene?.[name];
    return Array.isArray(list) ? list : undefined;
}

// The change entry of a base thing, and where it stands in `changes`.
export function changeOf(files: FileTrees | undefined, of: string): { entry: JsonObject; index: number } | null
{
    const changes = listOf(sceneOf(files), 'changes') ?? [];
    const index = changes.findIndex((entry) => typeof entry === 'object' && entry !== null && !Array.isArray(entry) && entry.of === of);
    return index < 0 ? null : { entry: changes[index] as JsonObject, index };
}

// A thing the project adds, by its list and id.
export function addedOf(files: FileTrees | undefined, list: AddedList, id: string): JsonObject | null
{
    const found = (listOf(sceneOf(files), list) ?? []).find((entry) => typeof entry === 'object' && entry !== null && !Array.isArray(entry) && entry.id === id);
    return (found as JsonObject | undefined) ?? null;
}

// The first id `<prefix>:<word>_<n>` no list of objects.yml's scene uses (a name the person may change before adding).
export function suggestedId(files: FileTrees | undefined, list: NewList, word = 'new'): string
{
    const used = new Set<string>();
    const scene = sceneOf(files);
    for (const name of ['lights', 'sounds', 'spawns', 'destructibles', 'water', 'ladders', 'monsters', 'items'])
    {
        for (const entry of listOf(scene, name) ?? [])
        {
            if (typeof entry === 'object' && entry !== null && !Array.isArray(entry) && typeof entry.id === 'string')
            {
                used.add(entry.id);
            }
        }
    }
    for (let number = 1; ; ++number)
    {
        const id = `${PREFIX[list]}:${word}_${number}`;
        if (!used.has(id))
        {
            return id;
        }
    }
}

const step = (op: PatchStep['op'], path: string, value?: JsonValue): PatchStep =>
    (value === undefined ? { op, path } : { op, path, value }) as PatchStep;
const patchOf = (steps: PatchStep[]): Op => ({ op: 'patch', file: 'objects.yml', patch: steps });
const segment = (text: string) => text.replaceAll('~', '~0').replaceAll('/', '~1');

// The steps that set `fields` on the object at `base` (`null` takes a word out), each tested against what it was.
function fieldSteps(base: string, current: JsonObject, fields: Record<string, JsonValue | null>): PatchStep[]
{
    const steps: PatchStep[] = [];
    for (const [name, value] of Object.entries(fields))
    {
        const path = `${base}/${segment(name)}`;
        const had = current[name];
        if (value === null)
        {
            if (had !== undefined)
            {
                steps.push(step('test', path, had), step('remove', path));
            }
        }
        else if (had === undefined)
        {
            steps.push(step('add', path, value));
        }
        else if (JSON.stringify(had) !== JSON.stringify(value))
        {
            steps.push(step('test', path, had), step('replace', path, value));
        }
    }
    return steps;
}

// The steps that append `value` to the scene's list `name` (the scene and the list made when missing).
function appendSteps(scene: JsonObject | undefined, name: string, value: JsonValue): PatchStep[]
{
    if (!scene)
    {
        return [step('add', '/scene', { [name]: [value] })];
    }
    if (!listOf(scene, name))
    {
        return [step('add', `/scene/${name}`, [value])];
    }
    return [step('add', `/scene/${name}/-`, value)];
}

// One gesture's operation (null when it changes nothing, or names what the project lacks).
export function overlayOps(files: FileTrees | undefined, gesture: OverlayGesture): Op | null
{
    const scene = sceneOf(files);
    switch (gesture.kind)
    {
    case 'add': {
        if (!/^[a-z_]+:[A-Za-z0-9_.-]+$/.test(gesture.id) || addedOf(files, gesture.list, gesture.id))
        {
            return null;
        }
        const value: JsonObject = { id: gesture.id, position: gesture.position.map(Math.round), ...(gesture.value ?? NEW_THING[gesture.list]) };
        return patchOf(appendSteps(scene, gesture.list, value));
    }
    case 'move': {
        const current = addedOf(files, gesture.list, gesture.id);
        if (!current)
        {
            return null;
        }
        const steps = fieldSteps(`/scene/${gesture.list}/${segment(gesture.id)}`, current, { position: gesture.position.map(Math.round) });
        return steps.length > 0 ? patchOf(steps) : null;
    }
    case 'set': {
        const current = addedOf(files, gesture.list, gesture.id);
        if (!current)
        {
            return null;
        }
        const steps = fieldSteps(`/scene/${gesture.list}/${segment(gesture.id)}`, current, gesture.fields);
        return steps.length > 0 ? patchOf(steps) : null;
    }
    case 'change': {
        const known = changeOf(files, gesture.of);
        if (!known)
        {
            const fields = Object.fromEntries(Object.entries(gesture.fields).filter(([, value]) => value !== null)) as JsonObject;
            return Object.keys(fields).length === 0 ? null : patchOf(appendSteps(scene, 'changes', { of: gesture.of, ...fields }));
        }
        const base = `/scene/changes/${known.index}`;
        const steps = [step('test', `${base}/of`, gesture.of), ...fieldSteps(base, known.entry, gesture.fields)];
        // A change left with nothing but its `of` goes.
        const left = Object.keys(known.entry).filter((name) => name !== 'of' && !(name in gesture.fields && gesture.fields[name] === null));
        const adds = Object.entries(gesture.fields).some(([, value]) => value !== null);
        if (left.length === 0 && !adds)
        {
            return patchOf([step('test', base, known.entry), step('remove', base)]);
        }
        return steps.length > 1 ? patchOf(steps) : null;
    }
    case 'remove': {
        const removals = listOf(scene, 'removals') ?? [];
        if (removals.includes(gesture.of))
        {
            return null;
        }
        // Its change goes with it: a thing taken out has nothing to change.
        const known = changeOf(files, gesture.of);
        const steps = known ? [step('test', `/scene/changes/${known.index}`, known.entry), step('remove', `/scene/changes/${known.index}`)] : [];
        return patchOf([...steps, ...appendSteps(scene, 'removals', gesture.of)]);
    }
    case 'restore': {
        const removals = listOf(scene, 'removals') ?? [];
        const index = removals.indexOf(gesture.of);
        if (index < 0)
        {
            return null;
        }
        return patchOf([step('test', `/scene/removals/${index}`, gesture.of), step('remove', `/scene/removals/${index}`)]);
    }
    case 'delete': {
        const current = addedOf(files, gesture.list, gesture.id);
        if (!current)
        {
            return null;
        }
        return patchOf([step('test', `/scene/${gesture.list}/${segment(gesture.id)}`, current), step('remove', `/scene/${gesture.list}/${segment(gesture.id)}`)]);
    }
    }
    return null;
}

// A base ladder moved so that its foot stands at `to` on the plan: the `offset` from where the base map has it (`at`),
// keeping the height the project's change gave it.
export function ladderMove(files: FileTrees | undefined, thing: OverlayThing, to: [number, number]): OverlayGesture
{
    const offset = changeOf(files, thing.id)?.entry.offset;
    const dz = Array.isArray(offset) && typeof offset[2] === 'number' ? offset[2] : 0;
    return { kind: 'change', of: thing.id, fields: { offset: [Math.round(to[0] - thing.at[0]), Math.round(to[1] - thing.at[1]), dz] } };
}

// A field's text in the form, and the value a typed text means (undefined: not of its form; null: empty, the word out).
export function fieldText(value: JsonValue | undefined): string
{
    if (value === undefined || value === null)
    {
        return '';
    }
    return Array.isArray(value) ? value.join(', ') : String(value);
}

export function parseField(type: FieldType, text: string): JsonValue | null | undefined
{
    const trimmed = text.trim();
    if (trimmed === '')
    {
        return null;
    }
    switch (type)
    {
    case 'text':
        return trimmed;
    case 'boolean':
        return trimmed === 'true' ? true : trimmed === 'false' ? false : undefined;
    case 'facing':
        return /^-?\d+(\.\d+)?$/.test(trimmed) ? Number(trimmed)
            : /^(n|ne|e|se|s|sw|w|nw|north|east|south|west)$/.test(trimmed) ? trimmed : undefined;
    case 'ref':
        return /^\d+$/.test(trimmed) ? Number(trimmed) : trimmed;
    case 'integer':
        return /^-?\d+$/.test(trimmed) ? Number(trimmed) : undefined;
    case 'number':
        return Number.isFinite(Number(trimmed)) ? Number(trimmed) : undefined;
    case 'rgb':
    case 'xyz':
    case 'pair': {
        const parts = trimmed.replace(/^\[|\]$/g, '').split(/[\s,]+/).filter(Boolean).map(Number);
        return parts.length === (type === 'pair' ? 2 : 3) && parts.every(Number.isFinite) ? parts : undefined;
    }
    }
    return undefined;
}

// The height a new thing takes where it is put: the nearest thing's (the plan has no floors of the base map), lifted
// for a light or a sound; a ladder, a monster and an item stand on that ground.
export function heightNear(things: readonly OverlayThing[], at: [number, number], list: NewList): number
{
    let best: OverlayThing | null = null;
    for (const thing of things)
    {
        if (!best || Math.hypot(thing.at[0] - at[0], thing.at[1] - at[1]) < Math.hypot(best.at[0] - at[0], best.at[1] - at[1]))
        {
            best = thing;
        }
    }
    const ground = best ? best.at[2] - (best.kind === 'light' ? 160 : best.kind === 'sound' ? 64 : 0) : 0;
    return Math.round(ground + (list === 'lights' ? 160 : list === 'sounds' ? 64 : 0));
}
