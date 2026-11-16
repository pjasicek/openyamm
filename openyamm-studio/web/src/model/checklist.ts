// The drawer's Checklist (S5_BROWSER_EDITOR.md 3.10): the plan's spaces not built yet, each stage's "done when", and
// REBUILD_PROCEDURE.md's "what the measure does not see" as items to tick. Counts from the files and the issues the
// client already has; what only the game or a person can judge is a tick.
import type { FileTrees, Issue, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import { STAGES } from '../edit/stages.ts';

function list(files: FileTrees | undefined, file: keyof FileTrees, name: string): JsonObject[]
{
    const value = files?.[file]?.tree[name];
    return Array.isArray(value) ? value.filter((entry): entry is JsonObject => typeof entry === 'object' && entry !== null && !Array.isArray(entry)) : [];
}

export interface SpaceItem
{
    id: string;
    name: string;
    purpose?: string;
}

// Plan spaces no room realises (a room's `space`, or a room with the space's own id).
export function spacesWithoutRoom(files: FileTrees | undefined): SpaceItem[]
{
    const realised = new Set(list(files, 'rooms.yml', 'rooms').map((room) => String(room.space ?? room.id)));
    return list(files, 'plan.yml', 'spaces').filter((space) => !realised.has(String(space.id))).map((space) => ({
        id: String(space.id), name: typeof space.name === 'string' ? space.name : String(space.id),
        ...(typeof space.purpose === 'string' ? { purpose: space.purpose } : {}),
    }));
}

export interface StageItem
{
    stage: number;
    name: string;
    done: string;
    // done, open (with what is open), or a person's to judge.
    state: 'done' | 'open' | 'judge';
    why: string;
}

// Things a player uses that no event names as its source (the Wire stage's "no unbound clicked face", as far as the
// files say it: the core's audit says it of the built map).
export function unwired(files: FileTrees | undefined): string[]
{
    const sources = new Set(list(files, 'wiring.yml', 'events').map((event) => event.source).filter((source): source is string => typeof source === 'string'));
    const out: string[] = [];
    for (const name of ['switches', 'chests', 'exits'])
    {
        for (const object of list(files, 'objects.yml', name))
        {
            if (!object.box_of && !sources.has(String(object.id)))
            {
                out.push(String(object.id));
            }
        }
    }
    return out;
}

export function stageItems(files: FileTrees | undefined, issues: readonly Issue[]): StageItem[]
{
    const spaces = list(files, 'plan.yml', 'spaces');
    const rooms = list(files, 'rooms.yml', 'rooms');
    const missing = spacesWithoutRoom(files);
    const errors = issues.filter((issue) => issue.severity === 'error');
    const loose = unwired(files);
    return STAGES.map((stage): StageItem =>
    {
        switch (stage.number)
        {
        case 1:
        {
            const vague = spaces.filter((space) => typeof space.purpose !== 'string' || !space.purpose);
            return { stage: 1, name: stage.name, done: stage.done, state: spaces.length === 0 ? 'judge' : vague.length === 0 ? 'done' : 'open',
                why: spaces.length === 0 ? 'no plan spaces (plan.yml): a new map may go without' : vague.length ? `${vague.length} spaces without a purpose` : `${spaces.length} spaces, each with a purpose` };
        }
        case 2:
            return { stage: 2, name: stage.name, done: stage.done, state: rooms.length === 0 || missing.length > 0 ? 'open' : 'done',
                why: rooms.length === 0 ? 'no rooms yet' : missing.length ? `${missing.length} planned spaces without a room` : `${rooms.length} rooms; reach: walk and the flow graph` };
        case 4:
            return { stage: 4, name: stage.name, done: stage.done, state: loose.length === 0 ? 'done' : 'open',
                why: loose.length ? `used by no event: ${loose.slice(0, 6).join(', ')}${loose.length > 6 ? ' …' : ''}` : 'every switch, chest and exit runs an event' };
        case 7:
            return { stage: 7, name: stage.name, done: stage.done, state: errors.length === 0 && missing.length === 0 ? 'done' : 'open',
                why: errors.length ? `${errors.length} errors in Issues` : missing.length ? 'planned spaces not built' : 'no errors; the ticks below are yours' };
        default:
            return { stage: stage.number, name: stage.name, done: stage.done, state: 'judge', why: stage.number === 5 ? 'the scale bands (Scorecard) and your eye'
                : stage.number === 6 ? 'thing.floating and geometry.coplanar of the audit (Scorecard), and a look in 3D' : 'a look in 3D and a walk' };
        }
    });
}

// REBUILD_PROCEDURE.md, "What the measure does not see": what a person checks in every new dungeon.
export const UNSEEN: { id: string; text: string }[] = [
    { id: 'interactive-form', text: 'Every interactive thing takes the original\'s form: levers, buttons, chests, doors, clicked panels and blocks (things: textures, sizes, which door record moves them).' },
    { id: 'looked-at', text: 'Every kind of interactive thing looked at in the game from where a player uses it, before and after use (a lever pulled and back, a chest from above, a door half open, a lift top and bottom).' },
    { id: 'over-moving', text: 'Things over moving parts: what stands on a lift, bridge or deck is on it at the start.' },
    { id: 'panels', text: 'Panel walls on exact corners, panels at full texture width; tunnels with side rooms built as rooms; side doors of sloping tunnels walked.' },
    { id: 'liquids-secrets', text: 'Untouchable liquids are ways down; secret faces counted.' },
    { id: 'caves-lights', text: 'Caves curve; lights hang from something; torches in wall sconces at the shipped height; stalactites where caverns are wide; nothing beside a door a player cannot name.' },
    { id: 'no-flicker', text: 'No flicker: no geometry.coplanar pair the project causes, at the start and with moving parts moved.' },
    { id: 'standing-high', text: 'A picture from the top of every platform, flight, ledge and mover the party can stand on, looking round (no eye in the room above).' },
];

// The person's ticks, kept in this browser per project (a per-viewer convenience: the core keeps no checklist).
export function readTicks(project: string): Set<string>
{
    try
    {
        const text = localStorage.getItem(`oymap-checklist:${project}`);
        return new Set(text ? (JSON.parse(text) as string[]) : []);
    }
    catch
    {
        return new Set();
    }
}

export function writeTicks(project: string, ticks: ReadonlySet<string>): void
{
    try
    {
        localStorage.setItem(`oymap-checklist:${project}`, JSON.stringify([...ticks]));
    }
    catch
    {
        // Storage refused (a private window): the ticks last this page only.
    }
}
