// An overlay project's scene things (view.overlay, devdocs/map_studio/S6_PLAN.md item O) for the Overlay panel: what
// the project does to the base map's pulsing lights, ambient sounds, destructibles, water volumes, spawn points and
// ladders (and the monsters and floor items it adds, S8a),
// grouped as the panel lists them (the project's own changes first, the base map's untouched things counted).
import type { ViewOverlayResult } from '../../../schema/rpc/generated/rpc.ts';

export type OverlayThing = ViewOverlayResult['things'][number];

export const STATE_ORDER = ['added', 'changed', 'removed', 'kept'] as const;
export const KIND_NAMES: Record<OverlayThing['kind'], string> = {
    light: 'pulsing light', sound: 'ambient sound', destructible: 'destructible', water: 'water volume', spawn: 'spawn point',
    ladder: 'ladder', monster: 'monster', item: 'floor item',
};

export interface OverlayGroup
{
    state: OverlayThing['state'];
    things: OverlayThing[];
}

export interface OverlaySummary
{
    groups: OverlayGroup[];
    // The base map's things by kind, the ones the project leaves alone included.
    baseByKind: Partial<Record<OverlayThing['kind'], number>>;
    changes: number;
}

export function summariseOverlay(result: ViewOverlayResult): OverlaySummary
{
    const groups: OverlayGroup[] = STATE_ORDER.map((state) => ({
        state,
        things: result.things.filter((thing) => thing.state === state)
            .sort((a, b) => a.kind.localeCompare(b.kind) || a.id.localeCompare(b.id)),
    })).filter((group) => group.things.length > 0);
    const baseByKind: Partial<Record<OverlayThing['kind'], number>> = {};

    for (const thing of result.things)
    {
        if (thing.origin === 'base')
        {
            baseByKind[thing.kind] = (baseByKind[thing.kind] ?? 0) + 1;
        }
    }

    const changes = result.things.filter((thing) => thing.state !== 'kept').length;
    return { groups, baseByKind, changes };
}

// The plan's frame round what the project touches (with a margin), or the whole map when it touches nothing.
export function overlayFrame(result: ViewOverlayResult): [number, number, number, number]
{
    const touched = result.things.filter((thing) => thing.state !== 'kept');

    if (touched.length === 0)
    {
        return [...result.bounds] as [number, number, number, number];
    }

    let frame: [number, number, number, number] = [Infinity, Infinity, -Infinity, -Infinity];

    for (const thing of touched)
    {
        const reach = Math.max(thing.radius ?? 0, 256);
        frame = [Math.min(frame[0], thing.at[0] - reach), Math.min(frame[1], thing.at[1] - reach),
            Math.max(frame[2], thing.at[0] + reach), Math.max(frame[3], thing.at[1] + reach)];
    }

    const margin = Math.max(frame[2] - frame[0], frame[3] - frame[1]) * 0.15;
    return [frame[0] - margin, frame[1] - margin, frame[2] + margin, frame[3] + margin];
}
