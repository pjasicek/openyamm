// S5b2: the travel scrubber's pure part: an object's travel from view.layout, and its faces posed at a share.
import { describe, expect, it } from 'vitest';
import type { ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import { moveFor, poseTriangles, posePoint, shareText, travelOf, travelSize } from './travel.ts';

const layout = {
    revision: 'r', view_revision: 'r', stale: false, kind: 'indoor', world: 'mm6', bounds: { min: [0, 0, 0], max: [1, 1, 1] },
    rooms: [], openings: [], things: [],
    doors: [
        { id: 'door:gate', opening: 'open:a', starts_open: false, moves: [{ at: [100, 0, 128], by: [0, 0, 256] }] },
        { id: 'door:pair', opening: 'open:b', moves: [{ at: [-64, 0, 0], by: [-96, 0, 0] }, { at: [64, 0, 0], by: [96, 0, 0] }] },
        { id: 'door:swing', opening: 'open:c', hinged: true, moves: [{ at: [48, 0, 64], pivot: [0, 0, 0], degrees: 90 }] },
        { id: 'door:old', opening: 'open:d' },
    ],
    lifts: [{ id: 'lift:a', mover: false, starts_open: true, moves: [{ at: [0, 0, 0], by: [0, 0, 512] }] },
        { id: 'mover:b', mover: true, moves: [{ at: [0, 0, 0], by: [0, 192, 0] }] }],
} as unknown as ViewLayoutResult;

describe('the travel scrubber', () =>
{
    it('reads a door\'s, lift\'s or mover\'s travel from the layout; none for one without moves', () =>
    {
        expect(travelOf(layout, 'door:gate')).toMatchObject({ kind: 'door', startsOpen: false });
        expect(travelOf(layout, 'lift:a')).toMatchObject({ kind: 'lift', startsOpen: true });
        expect(travelOf(layout, 'mover:b')?.kind).toBe('mover');
        expect(travelOf(layout, 'door:old')).toBeNull();
        expect(travelOf(layout, 'room:a')).toBeNull();
        expect(travelOf(null, 'door:gate')).toBeNull();
    });

    it('poses a slide, a turn about a hinge, and each leaf of two its own way', () =>
    {
        expect(posePoint({ at: [0, 0, 0], by: [0, 0, 256] }, 0.5, 10, 20, 30)).toEqual([10, 20, 158]);
        const turned = posePoint({ at: [0, 0, 0], pivot: [0, 0, 0], degrees: 90 }, 1, 96, 0, 64);
        expect(turned[0]).toBeCloseTo(0);
        expect(turned[1]).toBeCloseTo(96);
        expect(turned[2]).toBe(64);
        const pair = travelOf(layout, 'door:pair')!;
        expect(moveFor(pair.moves, -10, 0, 0).by).toEqual([-96, 0, 0]);
        // Two triangles, one on each leaf: each slides away from the middle.
        const base = Float32Array.from([-80, 0, 0, -48, 0, 0, -64, 0, 64, 48, 0, 0, 80, 0, 0, 64, 0, 64]);
        const out = new Float32Array(base.length);
        poseTriangles(base, pair.moves, 1, out);
        expect(Array.from(out.slice(0, 3))).toEqual([-176, 0, 0]);
        expect(Array.from(out.slice(9, 12))).toEqual([144, 0, 0]);
        // At 0 the faces are where the mesh draws them.
        poseTriangles(base, pair.moves, 0, out);
        expect(Array.from(out)).toEqual(Array.from(base));
    });

    it('says the share and the size in words', () =>
    {
        const gate = travelOf(layout, 'door:gate')!;
        expect(shareText(gate, 0)).toBe('closed');
        expect(shareText(gate, 0.25)).toBe('25 % open');
        expect(shareText(travelOf(layout, 'lift:a')!, 1)).toBe('up');
        expect(travelSize(gate)).toBe('rises 256');
        expect(travelSize(travelOf(layout, 'mover:b')!)).toBe('slides 192');
        expect(travelSize(travelOf(layout, 'door:swing')!)).toBe('turns 90°');
    });
});
