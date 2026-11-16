// History's "show as it was" outdoors (S5_BROWSER_EDITOR.md 3.12; S5b2): view.layout_at of an outdoor project gives the
// land and the models as they were; the plan draws the models' boxes dashed and the land that has changed since
// tinted, the 3D view the models' boxes as lines (as the rooms indoors). Pure.
import type { ViewLand, ViewLayoutAtResult, ViewModel } from '../../../schema/rpc/generated/rpc.ts';

// What the views draw of an earlier state: rooms (indoors) or models as boxes (outdoors), and the land then.
export interface GhostShape
{
    outline: readonly (readonly number[])[];
    floor: number;
    ceiling: number;
}

export interface Ghost
{
    sequence: number;
    rooms: GhostShape[];
    land?: ViewLand;
}

function modelBox(model: ViewModel): GhostShape
{
    const [x0, y0, z0] = model.min;
    const [x1, y1, z1] = model.max;
    return { outline: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], floor: z0, ceiling: z1 };
}

// The shapes of an earlier state's layout: its rooms, or its models as boxes.
export function ghostOf(sequence: number, layout: ViewLayoutAtResult): Ghost
{
    const rooms: GhostShape[] = layout.rooms.map((room) => ({ outline: room.outline, floor: room.floor, ceiling: room.ceiling }));
    for (const model of layout.models ?? [])
    {
        rooms.push(modelBox(model));
    }
    return { sequence, rooms, ...(layout.land ? { land: layout.land } : {}) };
}

// The land's change from then to now, cell by cell: the height steps it rose (positive) or sank, 0 where the same;
// water gained or lost counts as a change of 1 when the height is the same. Null when the sizes differ.
export interface LandChange
{
    size: number;
    delta: Int32Array;
    changed: number;
    // The largest rise and fall, in height steps.
    rise: number;
    fall: number;
}

export function landChange(then: ViewLand, now: ViewLand | undefined | null): LandChange | null
{
    if (!now || now.size !== then.size || now.heights.length !== then.heights.length)
    {
        return null;
    }
    const delta = new Int32Array(then.heights.length);
    let changed = 0;
    let rise = 0;
    let fall = 0;
    for (let index = 0; index < then.heights.length; ++index)
    {
        let d = now.heights[index] - then.heights[index];
        if (d === 0 && (now.water[index] ? 1 : 0) !== (then.water[index] ? 1 : 0))
        {
            d = now.water[index] ? -1 : 1;
        }
        delta[index] = d;
        if (d !== 0)
        {
            changed += 1;
            rise = Math.max(rise, d);
            fall = Math.min(fall, d);
        }
    }
    return { size: then.size, delta, changed, rise, fall };
}

// The change as an image of size x size (RGBA): risen land amber, sunk land blue, more opaque the larger the change;
// unchanged cells clear.
export function landChangePixels(change: LandChange): Uint8ClampedArray
{
    const pixels = new Uint8ClampedArray(change.size * change.size * 4);
    const most = Math.max(1, change.rise, -change.fall);
    for (let index = 0; index < change.delta.length; ++index)
    {
        const d = change.delta[index];
        if (d === 0)
        {
            continue;
        }
        const strength = 0.35 + 0.5 * Math.min(1, Math.abs(d) / most);
        pixels.set(d > 0 ? [224, 160, 32] : [58, 123, 213], index * 4);
        pixels[index * 4 + 3] = Math.round(strength * 255);
    }
    return pixels;
}
