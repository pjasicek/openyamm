// The flow graph (S5_BROWSER_EDITOR.md 3.7): what opens in which step, from the solve the scorecard's checks ran
// (check.audit with `solve`: its waves name sectors, events and doors by engine number) and the project's own words
// (the id lock turns the numbers into ids; the layout's openings and doors are the edges; wiring.yml's events say
// what each switch does). Nodes are rooms, in columns by the step the party first reaches them; edges are openings,
// a door making one conditional; the critical path from the start to plan.yml's goals is marked. The client draws;
// every fact here comes from the core's answers or the project's files.
import type { ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';

// The solve as check.solve (and check.audit's `solve`) answers it.
export interface SolveLike
{
    sector_rooms?: Record<string, string>;
    sectors_with_floor: number;
    waves: { sectors: number[]; opened_by: string[]; needs: string[] }[];
    never_reached: number[];
    issues: string[];
    waiting: string[];
    notes: string[];
    exits: string[];
}

export interface FlowNode
{
    id: string;
    // The solve's step at which the party first stands in it; null: never reached.
    step: number | null;
    sectors: number[];
    // Plan space it realises, and whether it is a goal's.
    space?: string;
    goal: boolean;
    start: boolean;
}

export interface FlowEdge
{
    // The opening's id.
    id: string;
    from: string;
    to: string;
    door?: string;
    // The events that open the door (ids where the lock names them, else "event <n>"), with the step they act in.
    openedBy: { event: string; title: string; step: number; action: string }[];
    critical: boolean;
}

export interface FlowEvent
{
    id: string;
    title?: string;
    preset?: string;
    source?: string;
    // The room the source stands in (a switch's or a door's), for drawing and selecting.
    room?: string;
    targets: { id: string; verb: string }[];
    condition?: string;
    // The solve's steps in which it acts (empty: never used by the solve).
    steps: number[];
}

export interface FlowGraph
{
    nodes: FlowNode[];
    edges: FlowEdge[];
    events: FlowEvent[];
    // Column count: steps 0..columns-1, then one column for rooms never reached.
    columns: number;
    neverReached: string[];
    issues: string[];
    waiting: string[];
    notes: string[];
    exits: string[];
    needs: string[][];
    // Why there is nothing to draw (an outdoor map, no solve yet).
    empty?: string;
}

type Tree = Record<string, unknown>;

const asList = (value: unknown): Tree[] => (Array.isArray(value) ? (value.filter((item) => item && typeof item === 'object') as Tree[]) : []);
const asStrings = (value: unknown): string[] => (Array.isArray(value) ? value.map(String) : typeof value === 'string' ? [value] : []);

// Engine number to id, per table of ids.lock.yml (sectors, events, doors).
export function lockNames(lock: Tree | undefined): { sectors: Map<number, string>; events: Map<number, string>; doors: Map<number, string> }
{
    const table = (name: string) =>
    {
        const out = new Map<number, string>();
        const entries = lock?.[name];
        if (entries && typeof entries === 'object' && !Array.isArray(entries))
        {
            for (const [id, number] of Object.entries(entries as Record<string, unknown>))
            {
                if (typeof number === 'number')
                {
                    out.set(number, id);
                }
            }
        }
        return out;
    };
    return { sectors: table('sectors'), events: table('events'), doors: table('doors') };
}

// "event 6 (Hoist brake) in sector 11: door 6 open" (core/Reachability's wave lines).
const OPENED_BY = /^event (\d+)(?: \(([^)]*)\))?(?: in sector \d+| \(run by the map\))?: door (\d+) (open|close|toggle)$/;

export function parseOpenedBy(line: string): { event: number; title: string; door: number; action: string } | null
{
    const match = OPENED_BY.exec(line.trim());
    return match ? { event: Number(match[1]), title: match[2] ?? '', door: Number(match[3]), action: match[4] } : null;
}

// A condition of wiring.yml in a few words ({not: {map_var: x}} -> "not map_var x").
export function conditionText(condition: unknown): string
{
    if (condition === null || condition === undefined)
    {
        return '';
    }
    if (typeof condition !== 'object')
    {
        return String(condition);
    }
    if (Array.isArray(condition))
    {
        return condition.map(conditionText).join(', ');
    }
    return Object.entries(condition as Tree).map(([key, value]) =>
    {
        if (key === 'not')
        {
            return `not ${conditionText(value)}`;
        }
        if (key === 'any' || key === 'all')
        {
            return `${key} (${conditionText(value)})`;
        }
        return value !== null && typeof value === 'object' ? `${key} ${conditionText(value)}` : `${key} ${String(value)}`;
    }).join(', ');
}

export function buildFlow(
    solve: SolveLike | null,
    layout: ViewLayoutResult | null,
    files: Record<string, { tree?: unknown } | undefined> | undefined): FlowGraph
{
    const graph: FlowGraph = { nodes: [], edges: [], events: [], columns: 0, neverReached: [], issues: [], waiting: [], notes: [],
        exits: [], needs: [] };
    if (!layout || layout.kind !== 'indoor')
    {
        graph.empty = layout?.kind === 'outdoor' ? 'The flow graph is of indoor maps: the solve walks indoor maps (outdoor maps have their events in the wiring list).' : 'No layout yet.';
    }
    const tree = (name: string) => (files?.[name]?.tree ?? undefined) as Tree | undefined;
    const lock = lockNames(tree('ids.lock.yml'));
    const roomOfSector = new Map<number, string>();
    for (const room of layout?.rooms ?? [])
    {
        roomOfSector.set(room.sector, room.id);
    }
    for (const [sector, room] of Object.entries(solve?.sector_rooms ?? {}))
    {
        roomOfSector.set(Number(sector), room);
    }
    for (const [sector, room] of lock.sectors)
    {
        if (!roomOfSector.has(sector))
        {
            roomOfSector.set(sector, room);
        }
    }

    // Steps by room: the first wave that reaches one of its sectors.
    const stepOf = new Map<string, number>();
    const sectorsOf = new Map<string, number[]>();
    (solve?.waves ?? []).forEach((wave, index) =>
    {
        for (const sector of wave.sectors)
        {
            const room = roomOfSector.get(sector) ?? `sector:${sector}`;
            if (!stepOf.has(room) || stepOf.get(room)! > index)
            {
                stepOf.set(room, index);
            }
            sectorsOf.set(room, [...(sectorsOf.get(room) ?? []), sector]);
        }
    });
    graph.columns = solve?.waves.length ?? 0;
    graph.needs = (solve?.waves ?? []).map((wave) => wave.needs);
    graph.issues = solve?.issues ?? [];
    graph.waiting = solve?.waiting ?? [];
    graph.notes = solve?.notes ?? [];
    graph.exits = solve?.exits ?? [];

    // Rooms: every room of the layout, and any room the solve names that the layout lacks.
    const rooms = asList(tree('rooms.yml')?.rooms);
    const spaceOf = new Map(rooms.filter((room) => typeof room.id === 'string').map((room) => [String(room.id), typeof room.space === 'string' ? room.space : String(room.id)]));
    const goals = new Set(asList(tree('plan.yml')?.goals).map((goal) => String(goal.space ?? goal.room ?? '')).filter(Boolean));
    const objects = tree('objects.yml');
    const start = objects?.start && typeof objects.start === 'object' ? String((objects.start as Tree).room ?? '') : '';
    const ids = new Set<string>([...(layout?.rooms ?? []).map((room) => room.id), ...stepOf.keys()]);
    for (const id of ids)
    {
        const space = spaceOf.get(id) ?? id;
        graph.nodes.push({ id, step: solve ? stepOf.get(id) ?? null : null, sectors: sectorsOf.get(id) ?? [], space,
            goal: goals.has(space) || goals.has(id), start: id === start });
    }
    graph.neverReached = (solve?.never_reached ?? []).map((sector) => roomOfSector.get(sector) ?? `sector:${sector}`);

    // Doors: which events open each, in which step.
    const opened = new Map<string, FlowEdge['openedBy']>();
    const eventSteps = new Map<string, number[]>();
    (solve?.waves ?? []).forEach((wave, index) =>
    {
        for (const line of wave.opened_by)
        {
            const parsed = parseOpenedBy(line);
            if (!parsed)
            {
                continue;
            }
            const door = lock.doors.get(parsed.door) ?? `door ${parsed.door}`;
            const event = lock.events.get(parsed.event) ?? `event ${parsed.event}`;
            opened.set(door, [...(opened.get(door) ?? []), { event, title: parsed.title, step: index, action: parsed.action }]);
            const steps = eventSteps.get(event) ?? [];
            if (!steps.includes(index))
            {
                eventSteps.set(event, [...steps, index]);
            }
        }
    });
    const doorOf = new Map((layout?.doors ?? []).map((door) => [door.opening, door.id]));
    for (const opening of layout?.openings ?? [])
    {
        const door = doorOf.get(opening.id);
        graph.edges.push({ id: opening.id, from: opening.from, to: opening.to, door, openedBy: door ? opened.get(door) ?? [] : [],
            critical: false });
    }

    // The wiring: each event, its source and what it moves.
    const roomOfObject = new Map<string, string>();
    for (const list of ['switches', 'doors', 'chests', 'plates', 'decorations', 'lights', 'movers'])
    {
        for (const item of asList(objects?.[list]))
        {
            if (typeof item.id === 'string' && typeof item.room === 'string')
            {
                roomOfObject.set(item.id, item.room);
            }
        }
    }
    for (const opening of layout?.openings ?? [])
    {
        const door = doorOf.get(opening.id);
        if (door)
        {
            roomOfObject.set(door, opening.from);
        }
    }
    for (const event of asList(tree('wiring.yml')?.events))
    {
        if (typeof event.id !== 'string')
        {
            continue;
        }
        const targets: FlowEvent['targets'] = [];
        for (const verb of ['opens', 'closes', 'toggles', 'lights_on', 'lights_off'])
        {
            for (const id of asStrings(event[verb]))
            {
                targets.push({ id, verb: verb.replace(/s$/, '').replace('_', ' ') });
            }
        }
        if (typeof event.door === 'string')
        {
            targets.push({ id: event.door, verb: typeof event.action === 'string' ? event.action : 'door' });
        }
        if (typeof event.container === 'string')
        {
            targets.push({ id: event.container, verb: 'chest' });
        }
        for (const effect of asList(event.effects))
        {
            for (const verb of ['lights_on', 'lights_off'])
            {
                for (const id of asStrings(effect[verb]))
                {
                    targets.push({ id, verb: verb.replace('_', ' ') });
                }
            }
        }
        const source = typeof event.source === 'string' ? event.source : undefined;
        graph.events.push({ id: event.id, title: typeof event.title === 'string' ? event.title : undefined,
            preset: typeof event.preset === 'string' ? event.preset : undefined, source,
            room: source ? roomOfObject.get(source) ?? (source.startsWith('room:') ? source : undefined) : undefined,
            targets, condition: conditionText(event.condition) || undefined, steps: eventSteps.get(event.id) ?? [] });
    }

    markCriticalPath(graph, start);
    return graph;
}

// The critical path: the fewest openings from the start room to each goal's room, ties broken by the earlier step.
export function markCriticalPath(graph: FlowGraph, start: string): void
{
    const goals = graph.nodes.filter((node) => node.goal).map((node) => node.id);
    if (!start || goals.length === 0)
    {
        return;
    }
    const step = new Map(graph.nodes.map((node) => [node.id, node.step ?? Number.MAX_SAFE_INTEGER]));
    const links = new Map<string, FlowEdge[]>();
    for (const edge of graph.edges)
    {
        links.set(edge.from, [...(links.get(edge.from) ?? []), edge]);
        links.set(edge.to, [...(links.get(edge.to) ?? []), edge]);
    }
    const came = new Map<string, FlowEdge | null>([[start, null]]);
    let frontier = [start];
    while (frontier.length > 0)
    {
        const next: string[] = [];
        for (const room of frontier)
        {
            const edges = [...(links.get(room) ?? [])].sort((a, b) =>
                (step.get(a.from === room ? a.to : a.from) ?? 0) - (step.get(b.from === room ? b.to : b.from) ?? 0) || (a.id < b.id ? -1 : 1));
            for (const edge of edges)
            {
                const other = edge.from === room ? edge.to : edge.from;
                if (!came.has(other))
                {
                    came.set(other, edge);
                    next.push(other);
                }
            }
        }
        frontier = next;
    }
    for (const goal of goals)
    {
        let room = goal;
        while (came.get(room))
        {
            const edge = came.get(room)!;
            edge.critical = true;
            room = edge.from === room ? edge.to : edge.from;
        }
    }
}

export interface FlowPlacement
{
    x: number;
    y: number;
    width: number;
    height: number;
}

// Columns by step (left to right), rooms never reached in a last column; within a column, by the step of the room
// they are reached from, then by id. Units are the view's pixels.
export function placeFlow(graph: FlowGraph, sizes = { column: 220, row: 34, width: 180, height: 24, margin: 24 }): Map<string, FlowPlacement>
{
    const columns = new Map<number, string[]>();
    const last = graph.columns;
    for (const node of graph.nodes)
    {
        const column = node.step ?? last;
        columns.set(column, [...(columns.get(column) ?? []), node.id]);
    }
    const placed = new Map<string, FlowPlacement>();
    for (const [column, ids] of [...columns.entries()].sort((a, b) => a[0] - b[0]))
    {
        ids.sort();
        ids.forEach((id, row) =>
        {
            placed.set(id, { x: sizes.margin + column * sizes.column, y: sizes.margin + 28 + row * sizes.row, width: sizes.width,
                height: sizes.height });
        });
    }
    return placed;
}
