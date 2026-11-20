// S5b2: the plan's section view, its pure part: what a cut crosses, stacked by height.
import { describe, expect, it } from 'vitest';
import type { FileTrees, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import { insideStretches, longAxis, sectionRange, sectionSpans, slopeHeight, spanAt } from './section.ts';

const layout = {
    revision: 'r', view_revision: 'r', stale: false, kind: 'indoor', world: 'mm8', bounds: { min: [0, 0, -512], max: [2048, 1024, 1024] },
    openings: [], doors: [], lifts: [], things: [],
    rooms: [
        { id: 'room:hall', sector: 1, outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]], floor: 0, ceiling: 512,
            levels: [{ outline: [[640, 0], [1024, 0], [1024, 256], [640, 256]], height: 128 }] },
        { id: 'room:ramp', sector: 2, outline: [[1024, 0], [1536, 0], [1536, 512], [1024, 512]], floor: 0, floor_to: 256, ceiling: 512 },
        { id: 'room:cellar', sector: 3, outline: [[256, 0], [768, 0], [768, 512], [256, 512]], floor: -512, ceiling: -64 },
    ],
} as unknown as ViewLayoutResult;

const files: FileTrees = {
    'rooms.yml': { tree: { format: 1, rooms: [
        { id: 'room:hall', outline: [[0, 0], [1024, 0], [1024, 512], [0, 512]], floor: 0, ceiling: 512,
            ceiling_levels: [{ key: 'vault', outline: [[128, 0], [384, 0], [384, 512], [128, 512]], ceiling: 768 }] },
        { id: 'room:ramp', outline: [[1024, 0], [1536, 0], [1536, 512], [1024, 512]], floor: 0, slope: { to: 256, toward: 'east' }, ceiling: 512 },
        { id: 'room:cellar', outline: [[256, 0], [768, 0], [768, 512], [256, 512]], floor: -512, ceiling: -64 },
    ] } },
    'objects.yml': { tree: { format: 1, lifts: [{ id: 'lift:down', room: 'room:cellar', at: [512, 128], size: [128, 128], travel: 448 }],
        movers: [{ id: 'mover:bridge', room: 'room:hall', at: [192, 128], size: [64, 64], height: 32, travel: [0, 0, 96], state: 'end' }] } },
};

describe('the section view', () =>
{
    it('finds where a cut runs inside an outline, also through a notch', () =>
    {
        expect(insideStretches([[0, 0], [100, 0], [100, 100], [0, 100]], [-50, 50], [150, 50])).toEqual([[0.25, 0.75]]);
        // A U: two stretches.
        const u = [[0, 0], [300, 0], [300, 300], [200, 300], [200, 100], [100, 100], [100, 300], [0, 300]];
        expect(insideStretches(u, [-100, 200], [400, 200])).toEqual([[0.2, 0.4], [0.6, 0.8]]);
        expect(insideStretches(u, [-100, 500], [400, 500])).toEqual([]);
    });

    it('cuts rooms stacked over one another, a raised level, a ramp, a ceiling level, a lift and a mover', () =>
    {
        const spans = sectionSpans(layout, files, { a: [-64, 128], b: [1600, 128] });
        const rooms = spans.filter((span) => span.kind === 'room');
        // Lowest floor first: the cellar under the hall.
        expect(rooms.map((span) => span.id)).toEqual(['room:cellar', 'room:hall', 'room:ramp']);
        expect(rooms[0]).toMatchObject({ from: 320, to: 832, floor: -512, ceiling: -64 });
        // The ramp rises to the east: 0 at its west wall, 256 at its east wall.
        expect(rooms[2]).toMatchObject({ floor: 0, floorTo: 256 });
        expect(spans.find((span) => span.kind === 'level')).toMatchObject({ id: 'room:hall', from: 704, to: 1088, floor: 128, ceiling: 0 });
        expect(spans.find((span) => span.kind === 'ceiling')).toMatchObject({ from: 192, to: 448, floor: 512, ceiling: 768 });
        expect(spans.find((span) => span.id === 'lift:down')).toMatchObject({ kind: 'lift', floor: -512, travel: 448, startsUp: false });
        expect(spans.find((span) => span.id === 'mover:bridge')).toMatchObject({ kind: 'mover', floor: 0, thickness: 32, travel: 96, startsUp: true });
        const range = sectionRange(spans);
        expect(range).toMatchObject({ low: -512, high: 768, floors: [-512, 0, 128] });
    });

    it('picks the lift before the room it stands in, the room by its space', () =>
    {
        const spans = sectionSpans(layout, files, { a: [-64, 128], b: [1600, 128] });
        expect(spanAt(spans, 576, -300, 4)?.id).toBe('lift:down');
        expect(spanAt(spans, 400, -300, 4)?.id).toBe('room:cellar');
        expect(spanAt(spans, 200, 300, 4)?.id).toBe('room:hall');
        expect(spanAt(spans, 200, 2000, 4)).toBeNull();
    });

    it('cuts along the long axis of a room, and slopes toward a wall', () =>
    {
        expect(longAxis([[0, 0], [1024, 0], [1024, 512], [0, 512]], 100)).toEqual({ a: [-100, 256], b: [1124, 256] });
        expect(longAxis([[0, 0], [256, 0], [256, 900], [0, 900]], 0)).toEqual({ a: [128, 0], b: [128, 900] });
        expect(slopeHeight([[0, 0], [512, 0], [512, 512], [0, 512]], 'east', 0, 256, [256, 100])).toBe(128);
    });
});
