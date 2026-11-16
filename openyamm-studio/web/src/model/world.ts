// The world view's map (devdocs/map_studio/S6_PLAN.md 2.9; S5_BROWSER_EDITOR.md 6.3): the maps of one world from
// world.view laid out as a world map. Outdoor maps stand on a grid placed by their map edges (a link with a side: the
// neighbour lies that way), as the games' outdoor maps join; each dungeon stands round the outdoor map it shares the
// most links with; maps linked to no outdoor map stand in a row under the rest. Pure and deterministic: the same
// answer gives the same picture.
import type { WorldViewResult } from '../../../schema/rpc/generated/rpc.ts';

export type WorldEntry = WorldViewResult['worlds'][number];
export type WorldMap = WorldEntry['maps'][number];
export type WorldLink = WorldEntry['links'][number];

export interface PlacedMap
{
    index: number;
    x: number;
    y: number;
    width: number;
    height: number;
}

// One line between two maps: the links of both directions together.
export interface WorldEdge
{
    a: number;
    b: number;
    // a to b and b to a.
    forward: boolean;
    backward: boolean;
    kinds: string[];
    // Every link of it reaches a map through the project that stands for it (a rebuild, an overlay).
    viaOriginal: boolean;
    // The neighbours' ids and the objects that use them, for the line's tooltip.
    titles: string[];
}

export interface WorldLayout
{
    maps: PlacedMap[];
    edges: WorldEdge[];
    // [min x, min y, max x, max y] of the boxes.
    bounds: [number, number, number, number];
}

export const MAP_WIDTH = 150;
export const MAP_HEIGHT = 44;
const OUTDOOR_WIDTH = 176;
const OUTDOOR_HEIGHT = 52;
const SIDES: Record<string, [number, number]> = { north: [0, -1], south: [0, 1], east: [1, 0], west: [-1, 0] };
const GAP = 14;

// The lines between maps: one per pair, with the kinds of its links.
export function worldEdges(world: WorldEntry): WorldEdge[]
{
    const byPair = new Map<string, WorldEdge>();
    for (const link of world.links)
    {
        if (link.from === link.to)
        {
            continue;
        }
        const a = Math.min(link.from, link.to);
        const b = Math.max(link.from, link.to);
        const key = `${a}-${b}`;
        const edge = byPair.get(key) ?? { a, b, forward: false, backward: false, kinds: [], viaOriginal: true, titles: [] };
        if (link.from === a)
        {
            edge.forward = true;
        }
        else
        {
            edge.backward = true;
        }
        if (link.kind && !edge.kinds.includes(link.kind))
        {
            edge.kinds.push(link.kind);
        }
        edge.viaOriginal = edge.viaOriginal && link.via_original;
        edge.titles.push(`${world.maps[link.from]?.map ?? '?'} to ${link.target}${link.kind ? ` (${link.kind}${link.side ? `, ${link.side}` : ''}${link.days !== undefined ? `, ${link.days} days` : ''})` : ''}`
            + `${link.id ? `: ${link.id}` : ''}${link.exits.length > 0 ? `, used by ${link.exits.join(', ')}` : ''}`);
        byPair.set(key, edge);
    }
    return [...byPair.values()].sort((left, right) => left.a - right.a || left.b - right.b);
}

function cellKey(cell: [number, number]): string
{
    return `${cell[0]},${cell[1]}`;
}

export function layoutWorld(world: WorldEntry): WorldLayout
{
    const count = world.maps.length;
    const outdoor = (index: number) => world.maps[index]?.kind === 'outdoor';
    // Outdoor maps on a grid of cells: first the projects' (by index), then the shipped ones.
    const order = [...Array(count).keys()].filter(outdoor)
        .sort((left, right) => Number(world.maps[left]!.project === undefined) - Number(world.maps[right]!.project === undefined) || left - right);
    const cells = new Map<number, [number, number]>();
    const taken = new Set<string>();
    const put = (index: number, cell: [number, number]) =>
    {
        cells.set(index, cell);
        taken.add(cellKey(cell));
    };
    // The nearest free cell to `cell` that way (or round it, without a way).
    const free = (cell: [number, number], way: [number, number] | null): [number, number] =>
    {
        if (way)
        {
            let next: [number, number] = cell;
            while (taken.has(cellKey(next)))
            {
                next = [next[0] + way[0], next[1] + way[1]];
            }
            return next;
        }
        for (let ring = 0; ring < 64; ++ring)
        {
            for (let dy = -ring; dy <= ring; ++dy)
            {
                for (let dx = -ring; dx <= ring; ++dx)
                {
                    const next: [number, number] = [cell[0] + dx, cell[1] + dy];
                    if (Math.max(Math.abs(dx), Math.abs(dy)) === ring && !taken.has(cellKey(next)))
                    {
                        return next;
                    }
                }
            }
        }
        return [cell[0] + 64, cell[1]];
    };
    // Where `other` lies seen from `index`, by the links between them that have a side.
    const wayTo = (index: number, other: number): [number, number] | null =>
    {
        for (const link of world.links)
        {
            const side = link.side ? SIDES[link.side] : undefined;
            if (!side)
            {
                continue;
            }
            if (link.from === index && link.to === other)
            {
                return side;
            }
            if (link.from === other && link.to === index)
            {
                return [-side[0], -side[1]];
            }
        }
        return null;
    };
    const linked = (index: number, other: number) => world.links.some((link) =>
        (link.from === index && link.to === other) || (link.from === other && link.to === index));

    for (const start of order)
    {
        if (cells.has(start))
        {
            continue;
        }
        // A new group of outdoor maps: right of what stands already.
        const right = cells.size === 0 ? 0 : Math.max(...[...cells.values()].map((cell) => cell[0])) + 2;
        put(start, free([right, 0], [1, 0]));
        const queue = [start];
        while (queue.length > 0)
        {
            const index = queue.shift()!;
            const here = cells.get(index)!;
            // By map edges first (their side places them), then by other links (boats, stables): round it.
            for (const pass of ['side', 'other'] as const)
            {
                for (const other of order)
                {
                    if (cells.has(other) || !linked(index, other))
                    {
                        continue;
                    }
                    const way = wayTo(index, other);
                    if ((pass === 'side') !== (way !== null))
                    {
                        continue;
                    }
                    put(other, way ? free([here[0] + way[0], here[1] + way[1]], way) : free(here, null));
                    queue.push(other);
                }
            }
        }
    }

    // The others round the outdoor map they share the most links with.
    const satellites = new Map<number, number[]>();
    const loose: number[] = [];
    for (let index = 0; index < count; ++index)
    {
        if (outdoor(index))
        {
            continue;
        }
        let best = -1;
        let most = 0;
        for (const other of order)
        {
            const shared = world.links.filter((link) => (link.from === index && link.to === other) || (link.from === other && link.to === index)).length;
            if (shared > most)
            {
                best = other;
                most = shared;
            }
        }
        if (best < 0)
        {
            loose.push(index);
        }
        else
        {
            satellites.set(best, [...(satellites.get(best) ?? []), index]);
        }
    }
    const ringOf = (n: number) => Math.max(150, (n * (MAP_WIDTH * 0.62)) / (2 * Math.PI) + 90);
    const largest = Math.max(0, ...[...satellites.values()].map((list) => list.length));
    const cellSize = 2 * ringOf(largest) + MAP_WIDTH + 2 * GAP;

    const placed: PlacedMap[] = [];
    for (const [index, cell] of cells)
    {
        placed.push({ index, x: cell[0] * cellSize, y: cell[1] * cellSize, width: OUTDOOR_WIDTH, height: OUTDOOR_HEIGHT });
        const around = satellites.get(index) ?? [];
        const radius = ringOf(around.length);
        around.forEach((satellite, at) =>
        {
            // Clockwise from the top, a half step turned so that none stands right on a map edge's line.
            const angle = -Math.PI / 2 + ((at + 0.5) / around.length) * 2 * Math.PI;
            placed.push({ index: satellite, x: cell[0] * cellSize + Math.cos(angle) * radius, y: cell[1] * cellSize + Math.sin(angle) * radius * 0.8,
                width: MAP_WIDTH, height: MAP_HEIGHT });
        });
    }
    const lowest = placed.length === 0 ? 0 : Math.max(...placed.map((place) => place.y + place.height / 2));
    const leftmost = placed.length === 0 ? 0 : Math.min(...placed.map((place) => place.x - place.width / 2));
    loose.forEach((index, at) =>
    {
        placed.push({ index, x: leftmost + MAP_WIDTH / 2 + at * (MAP_WIDTH + GAP * 2), y: lowest + MAP_HEIGHT + GAP * 4, width: MAP_WIDTH, height: MAP_HEIGHT });
    });

    // Boxes that overlap pushed apart along the line between their middles (a few rounds; the same every time).
    for (let round = 0; round < 60; ++round)
    {
        let moved = false;
        for (let i = 0; i < placed.length; ++i)
        {
            for (let j = i + 1; j < placed.length; ++j)
            {
                const p = placed[i]!;
                const q = placed[j]!;
                const overlapX = (p.width + q.width) / 2 + GAP - Math.abs(p.x - q.x);
                const overlapY = (p.height + q.height) / 2 + GAP - Math.abs(p.y - q.y);
                if (overlapX <= 0 || overlapY <= 0)
                {
                    continue;
                }
                moved = true;
                // Along the shorter way out; an outdoor map (on its cell) stays, the other moves.
                const fixedP = outdoor(p.index) && !outdoor(q.index);
                const fixedQ = outdoor(q.index) && !outdoor(p.index);
                const share = fixedP ? [0, 1] : fixedQ ? [1, 0] : [0.5, 0.5];
                if (overlapX < overlapY)
                {
                    const sign = p.x < q.x || (p.x === q.x && i < j) ? -1 : 1;
                    p.x += sign * overlapX * share[0]!;
                    q.x -= sign * overlapX * share[1]!;
                }
                else
                {
                    const sign = p.y < q.y || (p.y === q.y && i < j) ? -1 : 1;
                    p.y += sign * overlapY * share[0]!;
                    q.y -= sign * overlapY * share[1]!;
                }
            }
        }
        if (!moved)
        {
            break;
        }
    }

    placed.sort((left, right) => left.index - right.index);
    const bounds: [number, number, number, number] = placed.length === 0 ? [0, 0, 1, 1] : [
        Math.min(...placed.map((place) => place.x - place.width / 2)), Math.min(...placed.map((place) => place.y - place.height / 2)),
        Math.max(...placed.map((place) => place.x + place.width / 2)), Math.max(...placed.map((place) => place.y + place.height / 2))];
    return { maps: placed, edges: worldEdges(world), bounds };
}

// Where a line between two boxes meets the edge of `box` (from its middle toward `toward`).
export function boxEdgePoint(box: PlacedMap, toward: [number, number]): [number, number]
{
    const dx = toward[0] - box.x;
    const dy = toward[1] - box.y;
    if (dx === 0 && dy === 0)
    {
        return [box.x, box.y];
    }
    const scale = Math.min(dx === 0 ? Infinity : (box.width / 2) / Math.abs(dx), dy === 0 ? Infinity : (box.height / 2) / Math.abs(dy));
    return [box.x + dx * scale, box.y + dy * scale];
}

// A world's maps counted by role, for the heading.
export function roleCounts(world: WorldEntry): Record<WorldMap['role'], number>
{
    const counts: Record<WorldMap['role'], number> = { new: 0, rebuild: 0, overlay: 0, shipped: 0 };
    for (const map of world.maps)
    {
        counts[map.role] += 1;
    }
    return counts;
}
