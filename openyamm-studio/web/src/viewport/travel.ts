// The 3D view's travel scrubber (S5_BROWSER_EDITOR.md 3.5 "doors and movers on a scrubber (closed to open)", 3.18
// "scrubber shows travel"; S5b2): a door's, lift's or mover's faces posed at a share of their travel, all on the
// client from view.layout's `moves` (no core call per frame). Pure: the travel of an id, and the pose of points.
import type { ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';

export interface TravelMove
{
    // The middle of the faces as drawn (closed, at the start).
    at: readonly number[];
    // From closed to open (a slide, a lift's rise, a mover's travel).
    by?: readonly number[];
    // A hinged leaf: its vertical hinge line's foot and the turn to open (degrees, counter-clockwise from above).
    pivot?: readonly number[];
    degrees?: number;
}

export interface Travel
{
    id: string;
    kind: 'door' | 'lift' | 'mover';
    // The map starts it open (raised, at its end): the scrubber's resting place is 1, else 0.
    startsOpen: boolean;
    moves: TravelMove[];
}

// The travel of a door, lift or mover of the layout, or null (no such object, or the layout has no moves for it).
export function travelOf(layout: ViewLayoutResult | null | undefined, id: string | null | undefined): Travel | null
{
    if (!layout || !id)
    {
        return null;
    }
    const door = layout.doors.find((entry) => entry.id === id);
    if (door?.moves?.length)
    {
        return { id, kind: 'door', startsOpen: door.starts_open === true, moves: door.moves };
    }
    const lift = layout.lifts.find((entry) => entry.id === id);
    if (lift?.moves?.length)
    {
        return { id, kind: lift.mover ? 'mover' : 'lift', startsOpen: lift.starts_open === true, moves: lift.moves };
    }
    return null;
}

// The move of the mechanism nearest a triangle's middle (a door of two leaves moves each leaf its own way).
export function moveFor(moves: readonly TravelMove[], x: number, y: number, z: number): TravelMove
{
    let best = moves[0];
    let bestDistance = Infinity;
    for (const move of moves)
    {
        const d = (move.at[0] - x) ** 2 + (move.at[1] - y) ** 2 + (move.at[2] - z) ** 2;
        if (d < bestDistance)
        {
            best = move;
            bestDistance = d;
        }
    }
    return best;
}

// A point of the faces at share `t` (0 closed or at its start, 1 open or at its end).
export function posePoint(move: TravelMove, t: number, x: number, y: number, z: number): [number, number, number]
{
    if (move.pivot && move.degrees !== undefined)
    {
        const angle = (move.degrees * t * Math.PI) / 180;
        const dx = x - move.pivot[0];
        const dy = y - move.pivot[1];
        return [move.pivot[0] + dx * Math.cos(angle) - dy * Math.sin(angle), move.pivot[1] + dx * Math.sin(angle) + dy * Math.cos(angle), z];
    }
    const by = move.by ?? [0, 0, 0];
    return [x + by[0] * t, y + by[1] * t, z + by[2] * t];
}

// Triangles (nine numbers each, as drawn) posed at `t` into `out` (the same length).
export function poseTriangles(base: Float32Array, moves: readonly TravelMove[], t: number, out: Float32Array): void
{
    for (let i = 0; i + 8 < base.length; i += 9)
    {
        const move = moves.length === 1 ? moves[0]
            : moveFor(moves, (base[i] + base[i + 3] + base[i + 6]) / 3, (base[i + 1] + base[i + 4] + base[i + 7]) / 3, (base[i + 2] + base[i + 5] + base[i + 8]) / 3);
        for (let k = 0; k < 9; k += 3)
        {
            const [x, y, z] = posePoint(move, t, base[i + k], base[i + k + 1], base[i + k + 2]);
            out[i + k] = x;
            out[i + k + 1] = y;
            out[i + k + 2] = z;
        }
    }
}

// What the scrubber says of a share: "closed", "open", "62 % open" (a lift: down, up; a mover: start, end).
export function travelWords(travel: Travel): [string, string]
{
    return travel.kind === 'lift' ? ['down', 'up'] : travel.kind === 'mover' ? ['start', 'end'] : ['closed', 'open'];
}

export function shareText(travel: Travel, t: number): string
{
    const [low, high] = travelWords(travel);
    return t <= 0 ? low : t >= 1 ? high : `${Math.round(t * 100)} % ${travel.kind === 'door' ? 'open' : `to ${high}`}`;
}

// How far it goes, in words: "rises 256", "slides 192", "turns 90°".
export function travelSize(travel: Travel): string
{
    const move = travel.moves[0];
    if (move.degrees !== undefined)
    {
        return `turns ${Math.abs(move.degrees)}°`;
    }
    const by = move.by ?? [0, 0, 0];
    const length = Math.round(Math.hypot(by[0], by[1], by[2]));
    return Math.abs(by[2]) > Math.hypot(by[0], by[1]) ? `${by[2] > 0 ? 'rises' : 'sinks'} ${length}` : `slides ${length}`;
}
