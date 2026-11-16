// The wall bay strip's logic (S5_BROWSER_EDITOR.md 3.18 "the wall bay strip (W3) for each wall; doors by clicking a
// bay"): a building part's walls with their lengths, how many bays the build lays on each (as many as fit at 128,
// each 96 to 192 wide), the bays as written or as the build lays them by rule, and the operations of a bay changed
// (the whole wall written, and the building's door when the bay becomes the door).
import type { JsonObject, JsonValue, Op, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import { isObject, segment } from './keys.ts';

export interface PartWall
{
    // The wall's name: s, e, n, w on a box; 0, 1, 2 ... on an outline or a round part.
    name: string;
    // Map units.
    length: number;
}

// A part's walls (before `turn`). `size` is the part's box in map units (a part without one: its plot's).
export function partWalls(part: JsonObject, size: readonly number[]): PartWall[]
{
    const shape = typeof part.shape === 'string' ? part.shape : 'box';
    if (shape === 'outline' && Array.isArray(part.outline))
    {
        const points = part.outline.filter((p): p is number[] => Array.isArray(p) && typeof p[0] === 'number' && typeof p[1] === 'number');
        return points.map((p, i) =>
        {
            const q = points[(i + 1) % points.length];
            return { name: String(i), length: Math.round(Math.hypot(q[0] - p[0], q[1] - p[1])) };
        });
    }
    if (shape === 'round')
    {
        const sides = typeof part.sides === 'number' ? part.sides : 8;
        const radius = typeof part.radius === 'number' ? part.radius : 128;
        const side = Math.round(2 * radius * Math.sin(Math.PI / sides));
        return Array.from({ length: sides }, (_, i) => ({ name: String(i), length: side }));
    }
    const [width, depth] = Array.isArray(part.size) ? (part.size as number[]) : size;
    return [{ name: 's', length: width }, { name: 'e', length: depth }, { name: 'n', length: width }, { name: 'w', length: depth }];
}

// How many bays the build lays on a wall: as many as fit at 128 (a bay may be 96 to 192 wide).
export function bayCount(length: number): number
{
    return Math.max(1, Math.round(length / 128));
}

export type Bay = string | [string, number];

// The bays of a wall as the build lays them when the wall is not listed: posts at the ends, the door in the middle
// of the door's wall, windows every second bay (beside the door on the door's wall).
export function ruleBays(count: number, doorWall: boolean, windows: string = 'alternate'): string[]
{
    const bays = Array.from({ length: count }, () => 'wall');
    if (count >= 3)
    {
        bays[0] = 'post_left';
        bays[count - 1] = 'post_right';
    }
    const door = doorWall ? Math.floor(count / 2) : -1;
    if (door >= 0)
    {
        bays[door] = 'door';
    }
    const inner = count >= 3 ? [1, count - 2] : [0, count - 1];
    for (let i = inner[0]; i <= inner[1]; ++i)
    {
        if (i === door)
        {
            continue;
        }
        if (windows === 'all' || (windows === 'alternate' && (door >= 0 ? Math.abs(i - door) % 2 === 1 : (i - inner[0]) % 2 === 1)))
        {
            bays[i] = 'window';
        }
    }
    return bays;
}

// The role or texture a bay names ([word, width] gives its word).
export function bayWord(bay: Bay): string
{
    return Array.isArray(bay) ? String(bay[0]) : bay;
}

// The building's door: where it is ({part, wall, bay}), or by default the first part's front wall.
export function doorOf(building: JsonObject, partKeys: readonly string[]): { part: string; wall: string; bay?: number } | null
{
    const door = building.door;
    if (door === 'none')
    {
        return null;
    }
    const facing = typeof building.facing === 'string' ? building.facing : 's';
    if (isObject(door))
    {
        return { part: typeof door.part === 'string' ? door.part : partKeys[0], wall: typeof door.wall === 'string' ? door.wall : facing,
            ...(typeof door.bay === 'number' ? { bay: door.bay } : {}) };
    }
    return { part: partKeys[0], wall: facing };
}

// A wall's bays: as written in the part's `walls`, else by rule.
export function wallBays(part: JsonObject, wall: PartWall, doorWall: boolean, doorBay?: number): { bays: Bay[]; written: boolean }
{
    const walls = isObject(part.walls) ? part.walls : null;
    const written = walls ? walls[wall.name] : undefined;
    if (Array.isArray(written) && written.length > 0)
    {
        return { bays: written as Bay[], written: true };
    }
    const bays: Bay[] = ruleBays(bayCount(wall.length), doorWall && doorBay === undefined, typeof part.windows === 'string' ? part.windows : 'alternate');
    if (doorWall && doorBay !== undefined && doorBay < bays.length)
    {
        bays[doorBay] = 'door';
    }
    return { bays, written: false };
}

// One bay of a wall made `word`: the wall written whole (its other bays as shown), with a door bay also the
// building's door, and every other door bay of the building's parts' written walls made a plain wall (one door: more
// doors are the building's `doors`).
export function bayOps(buildingId: string, building: JsonObject, partKey: string, part: JsonObject, wall: PartWall, bays: readonly Bay[], index: number, word: string): Op
{
    const next: JsonValue[] = bays.map((bay, i) => (i === index ? word : Array.isArray(bay) ? [...bay] : bay));
    const walls: JsonObject = isObject(part.walls) ? structuredClone(part.walls) : {};
    if (word === 'door')
    {
        for (const [name, list] of Object.entries(walls))
        {
            if (name !== wall.name && Array.isArray(list))
            {
                walls[name] = list.map((bay) => (bayWord(bay as Bay) === 'door' ? 'wall' : bay));
            }
        }
        next.forEach((bay, i) =>
        {
            if (i !== index && bayWord(bay as Bay) === 'door')
            {
                next[i] = 'wall';
            }
        });
    }
    walls[wall.name] = next;
    const steps: PatchStep[] = [{ op: 'add', path: `/parts/${segment(partKey)}/walls`, value: walls }];
    if (word === 'door')
    {
        steps.push({ op: 'add', path: '/door', value: { part: partKey, wall: wall.name, bay: index } });
    }
    else if (isObject(building.door) && building.door.part === partKey && building.door.wall === wall.name && building.door.bay === index)
    {
        // The door's bay made something else: the building keeps no door there.
        steps.push({ op: 'remove', path: '/door' });
    }
    return { op: 'patch', id: buildingId, file: 'sketch.yml', patch: steps };
}

// The house table's rows (engine/data_tables/house_data.txt: number, type, name), for the house picker.
export interface House
{
    number: number;
    type: string;
    name: string;
}

export function parseHouses(text: string): House[]
{
    const out: House[] = [];
    for (const line of text.split(/\r?\n/))
    {
        const columns = line.split('\t');
        if (!/^\d+$/.test(columns[0] ?? '') || columns.length < 6)
        {
            continue;
        }
        const name = columns[5].trim();
        if (name)
        {
            out.push({ number: Number(columns[0]), type: columns[2].trim(), name });
        }
    }
    return out;
}
