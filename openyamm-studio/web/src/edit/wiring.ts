// The Wire stage's operations (S5_BROWSER_EDITOR.md 3.7, 3.18, W3): the `L` link from a source to a target, the
// switch board's cells, "+ event" of a preset, and "Convert to script". Each a list of operations on wiring.yml; the
// words are the schema's (`opens`, `closes`, `toggles` of an event; its `preset` and `source`), never a rule of the
// game's: what an event does is the core's to say (flow, solve).
import type { FileTrees, JsonObject, JsonValue, Op, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import { isObject } from './keys.ts';

export const MOVE_VERBS = ['toggles', 'opens', 'closes'] as const;
export type MoveVerb = (typeof MOVE_VERBS)[number];

export const PRESETS = ['door', 'switch', 'chest', 'exit', 'teleport', 'text', 'script'] as const;

export function eventsOf(files: FileTrees | undefined): JsonObject[]
{
    const events = files?.['wiring.yml']?.tree.events;
    return Array.isArray(events) ? events.filter(isObject) : [];
}

function listOf(files: FileTrees | undefined, file: keyof FileTrees, list: string): JsonObject[]
{
    const value = files?.[file]?.tree[list];
    return Array.isArray(value) ? value.filter(isObject) : [];
}

function ids(value: JsonValue | undefined): string[]
{
    return Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === 'string') : [];
}

// The events a thing runs when it is used (its click events: the first is the one a link adds to).
export function eventsFrom(files: FileTrees | undefined, source: string): JsonObject[]
{
    return eventsOf(files).filter((event) => event.source === source && (event.trigger === undefined || event.trigger === 'click'));
}

// Which list of an event names a target, or null.
export function verbOf(event: JsonObject | undefined, target: string): MoveVerb | null
{
    if (!event)
    {
        return null;
    }
    return MOVE_VERBS.find((verb) => ids(event[verb]).includes(target)) ?? null;
}

// The preset an event made by a link from this source takes: a door's own click moves it and what it names; any other
// source (a switch, a plate, a lift) moves only what it names.
export function linkPreset(source: string): 'door' | 'switch'
{
    return source.startsWith('door:') ? 'door' : 'switch';
}

// The hint a new event of a source shows (its `title`), from the source's kind.
export function titleFor(files: FileTrees | undefined, source: string): string
{
    const kind = source.slice(0, source.indexOf(':'));
    if (kind === 'switch')
    {
        const object = listOf(files, 'objects.yml', 'switches').find((entry) => entry.id === source);
        return object?.kind === 'lever' ? 'Lever' : object?.kind === 'button' ? 'Button' : 'Switch';
    }
    const names: Record<string, string> = { door: 'Door', chest: 'Chest', exit: 'Leave', plate: 'Plate', lift: 'Lift', mover: 'Lever',
        deco: 'Look', decoration: 'Look', room: 'Floor', level: 'Floor', platform: 'Block', panel: 'Panel' };
    return names[kind] ?? 'Use';
}

// The id an event's operation names in a list, removed with a test of its place (a plain list).
function removeFromList(event: JsonObject, verb: string, target: string): PatchStep[]
{
    const list = ids(event[verb]);
    const index = list.indexOf(target);
    if (index < 0)
    {
        return [];
    }
    if (list.length === 1)
    {
        return [{ op: 'test', path: `/${verb}/0`, value: target }, { op: 'remove', path: `/${verb}` }];
    }
    return [{ op: 'test', path: `/${verb}/${index}`, value: target }, { op: 'remove', path: `/${verb}/${index}` }];
}

function addToList(event: JsonObject, verb: string, target: string): PatchStep[]
{
    return Array.isArray(event[verb]) ? [{ op: 'add', path: `/${verb}/-`, value: target }] : [{ op: 'add', path: `/${verb}`, value: [target] }];
}

export interface WireChange
{
    ops: Op[];
    label: string;
}

// A new event of a preset for a source (the "+ event" buttons): the source and its hint, the preset's own words left
// to the event form.
export function newEventOp(files: FileTrees | undefined, preset: string, source: string | null, extra: JsonObject = {}): Op
{
    return { op: 'add', to: 'events', file: 'wiring.yml', value: { preset, ...(source ? { source, title: titleFor(files, source) } : {}), ...extra } };
}

// `L` and a click on a target: the source's click event names the target in `verb` (made when there is none); a
// target it names already is taken out again (a second click undoes a link).
export function linkChange(files: FileTrees | undefined, source: string, target: string, verb: MoveVerb): WireChange | null
{
    if (source === target)
    {
        return null;
    }
    const event = eventsFrom(files, source)[0];
    if (!event)
    {
        // A pressure plate acts when the party steps on it.
        const trigger: JsonObject = source.startsWith('plate:') ? { trigger: 'step' } : {};
        return { ops: [newEventOp(files, linkPreset(source), source, { ...trigger, [verb]: [target] })], label: `link ${source} → ${target}` };
    }
    const id = String(event.id);
    const has = verbOf(event, target);
    if (has)
    {
        return { ops: [{ op: 'patch', id, file: 'wiring.yml', patch: removeFromList(event, has, target) }], label: `unlink ${source} → ${target}` };
    }
    return { ops: [{ op: 'patch', id, file: 'wiring.yml', patch: addToList(event, verb, target) }], label: `link ${source} → ${target} (${verb})` };
}

// --- the switch board (3.7): sources down the side, targets across -----------------------------------------------

export interface BoardRow
{
    // The event, or null for a switch no event uses yet.
    event: JsonObject | null;
    source: string | null;
    label: string;
}

export interface Board
{
    rows: BoardRow[];
    // Doors, lifts, movers and switches an event can move.
    columns: string[];
}

export function boardOf(files: FileTrees | undefined): Board
{
    const events = eventsOf(files);
    const rows: BoardRow[] = [];
    const used = new Set<string>();
    for (const event of events)
    {
        const moves = MOVE_VERBS.some((verb) => ids(event[verb]).length > 0);
        const source = typeof event.source === 'string' ? event.source : null;
        if (moves || event.preset === 'switch' || source?.startsWith('switch:') || source?.startsWith('plate:'))
        {
            rows.push({ event, source, label: `${String(event.id)}${source ? ` (${source})` : ''}` });
            if (source)
            {
                used.add(source);
            }
        }
    }
    for (const list of ['switches', 'plates'])
    {
        for (const object of listOf(files, 'objects.yml', list))
        {
            const id = String(object.id);
            if (!used.has(id))
            {
                rows.push({ event: null, source: id, label: `${id} (no event yet)` });
            }
        }
    }
    const columns: string[] = [];
    for (const list of ['doors', 'lifts', 'movers'])
    {
        listOf(files, 'objects.yml', list).forEach((object) => columns.push(String(object.id)));
    }
    // Switches an event moves (a lever thrown by another) are targets too.
    for (const event of events)
    {
        for (const verb of MOVE_VERBS)
        {
            for (const target of ids(event[verb]))
            {
                if (!columns.includes(target))
                {
                    columns.push(target);
                }
            }
        }
    }
    return { rows, columns };
}

// The next state of a board cell: none, toggles, opens, closes, none again.
export function nextVerb(verb: MoveVerb | null): MoveVerb | null
{
    return verb === null ? 'toggles' : verb === 'toggles' ? 'opens' : verb === 'opens' ? 'closes' : null;
}

// A board cell clicked: one patch of one event (or a new event for a switch without one).
export function cellChange(files: FileTrees | undefined, row: BoardRow, target: string): WireChange | null
{
    if (!row.event)
    {
        return row.source ? { ops: [newEventOp(files, linkPreset(row.source), row.source, { toggles: [target] })], label: `link ${row.source} → ${target}` } : null;
    }
    const id = String(row.event.id);
    const was = verbOf(row.event, target);
    const next = nextVerb(was);
    const steps: PatchStep[] = [];
    if (was)
    {
        steps.push(...removeFromList(row.event, was, target));
    }
    if (next)
    {
        // The event as it stands after the removal, for whether the next list exists.
        const after: JsonObject = { ...row.event };
        if (was && ids(row.event[was]).length === 1)
        {
            delete after[was];
        }
        steps.push(...addToList(after, next, target));
    }
    return { ops: [{ op: 'patch', id, file: 'wiring.yml', patch: steps }], label: `${id}: ${target} ${next ?? 'not moved'}` };
}

// "Convert to script": the event's preset becomes `script` and its own work is written as the words that say it
// (the schema's: a door's click moves its door, a chest's shows its contents), so nothing it did is lost; the Lua
// field then holds what no word says.
export function toScriptOp(event: JsonObject): Op
{
    const id = String(event.id);
    const fields: Record<string, JsonValue> = { preset: 'script' };
    const source = typeof event.source === 'string' ? event.source : null;
    if (event.preset === 'door' && source)
    {
        const verb = event.action === 'open' ? 'opens' : 'toggles';
        const list = ids(event[verb]);
        if (!list.includes(source))
        {
            fields[verb] = [source, ...list];
        }
        fields.action = null;
    }
    if (event.preset === 'chest' && source)
    {
        const effects = Array.isArray(event.effects) ? event.effects : [];
        fields.effects = [{ open_chest: source }, ...effects];
    }
    if (typeof event.lua !== 'string')
    {
        fields.lua = '-- Lua run after the condition, the doors and the effects (MapVar(name) names a declared variable).\n';
    }
    return { op: 'set', id, file: 'wiring.yml', fields };
}

// The ids a link can be drawn between on the plan: each event's source and the targets it moves.
export function links(files: FileTrees | undefined): { event: string; source: string; target: string; verb: MoveVerb }[]
{
    const out: { event: string; source: string; target: string; verb: MoveVerb }[] = [];
    for (const event of eventsOf(files))
    {
        if (typeof event.source !== 'string')
        {
            continue;
        }
        for (const verb of MOVE_VERBS)
        {
            for (const target of ids(event[verb]))
            {
                if (target !== event.source)
                {
                    out.push({ event: String(event.id), source: event.source, target, verb });
                }
            }
        }
    }
    return out;
}
