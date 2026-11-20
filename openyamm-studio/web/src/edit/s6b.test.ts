// S6, the second run (devdocs/map_studio/S6_PLAN.md item L): a leaning ladder on the plan (its strip from the foot to
// the top) and its handles (the top moves with the foot; dragging the top alone writes `top_at`).
import { describe, expect, it } from 'vitest';
import type { FileTrees } from '../../../schema/rpc/generated/rpc.ts';
import { objectBlocks } from './blocks.ts';
import { movedPoints, objectShape, shapeGestureOp } from './handles.ts';

const files = (ladder: Record<string, unknown>): FileTrees => ({
    'rooms.yml': { tree: { format: 1, rooms: [{ id: 'room:hall', outline: [[0, 0], [1024, 0], [1024, 1024], [0, 1024]], floor: 0, ceiling: 640 }] } },
    'objects.yml': { tree: { format: 1, start: { room: 'room:hall' }, ladders: [{ id: 'ladder:loft', room: 'room:hall', facing: 90, height: 256, ...ladder }] } },
});

describe('a leaning ladder (S6 L)', () =>
{
    it('stands on the plan as a strip from its foot to its top; an upright one as a short strip at its foot', () =>
    {
        const [leaning] = objectBlocks(files({ at: [512, 640], top_at: [512, 760] }), null);
        expect(leaning!.top).toEqual([512, 760]);
        const ys = leaning!.outline.map((point) => point[1]);
        expect(Math.min(...ys)).toBeCloseTo(640, 6);
        expect(Math.max(...ys)).toBeCloseTo(760, 6);
        const [upright] = objectBlocks(files({ at: [512, 640] }), null);
        expect(upright!.top).toBeUndefined();
        expect(Math.max(...upright!.outline.map((point) => point[1]))).toBeCloseTo(640, 6);
        // A top over the foot is upright.
        expect(objectBlocks(files({ at: [512, 640], top_at: [512, 640] }), null)[0]!.top).toBeUndefined();
    });

    it('moves its top with its foot, and its top alone by the top\'s handle', () =>
    {
        const shape = objectShape(files({ at: [512, 640], top_at: [512, 760] }), 'ladder:loft')!;
        expect(shape.kind).toBe('point');
        expect(shape.points).toEqual([[512, 640], [512, 760]]);
        expect(shapeGestureOp(shape, movedPoints(shape, [64, 0]), 'move')).toEqual({ op: 'patch', id: 'ladder:loft', file: 'objects.yml', patch: [
            { op: 'test', path: '/at', value: [512, 640] }, { op: 'replace', path: '/at', value: [576, 640] },
            { op: 'test', path: '/top_at', value: [512, 760] }, { op: 'replace', path: '/top_at', value: [576, 760] },
        ] });
        // The top's handle: the foot stays (its test and the same value), the top moves.
        const topOnly = shapeGestureOp(shape, [[512, 640], [512, 740]], 'corner');
        expect(topOnly?.op === 'patch' ? topOnly.patch.slice(2) : null).toEqual([
            { op: 'test', path: '/top_at', value: [512, 760] }, { op: 'replace', path: '/top_at', value: [512, 740] },
        ]);
        // An upright ladder writes only its foot.
        const upright = objectShape(files({ at: [512, 640] }), 'ladder:loft')!;
        const moved = shapeGestureOp(upright, movedPoints(upright, [0, 32]), 'move');
        expect(moved?.op === 'patch' ? moved.patch.length : 0).toBe(2);
    });
});
