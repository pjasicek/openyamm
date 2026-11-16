// S5b2: History's ghost outdoors: the models of then as boxes, and the land's change since, cell by cell.
import { describe, expect, it } from 'vitest';
import type { ViewLand, ViewLayoutAtResult } from '../../../schema/rpc/generated/rpc.ts';
import { ghostOf, landChange, landChangePixels } from './ghost.ts';

const land = (heights: number[], water = heights.map(() => 0)): ViewLand => ({ size: 2, cell: 512, height_unit: 32, heights, water });

describe('the ghost outdoors', () =>
{
    it('draws the models of then as boxes, the rooms of an indoor state as they were', () =>
    {
        const outdoor = { sequence: 3, side: 'before', revision: 'r', kind: 'outdoor', world: 'mm6', bounds: { min: [0, 0, 0], max: [1, 1, 1] },
            rooms: [], openings: [], doors: [], lifts: [], things: [], land: land([1, 2, 3, 4]),
            models: [{ id: 'house', min: [100, 200, 0], max: [300, 500, 400] }] } as unknown as ViewLayoutAtResult;
        const ghost = ghostOf(3, outdoor);
        expect(ghost.rooms).toEqual([{ outline: [[100, 200], [300, 200], [300, 500], [100, 500]], floor: 0, ceiling: 400 }]);
        expect(ghost.land?.heights).toEqual([1, 2, 3, 4]);
        const indoor = { ...outdoor, kind: 'indoor', land: undefined, models: undefined,
            rooms: [{ id: 'room:a', sector: 1, outline: [[0, 0], [1, 0], [1, 1]], floor: 0, ceiling: 256 }] } as unknown as ViewLayoutAtResult;
        expect(ghostOf(1, indoor)).toEqual({ sequence: 1, rooms: [{ outline: [[0, 0], [1, 0], [1, 1]], floor: 0, ceiling: 256 }] });
    });

    it('finds the land risen, sunk, made water, and the same', () =>
    {
        const change = landChange(land([10, 10, 10, 10], [0, 0, 0, 0]), land([12, 7, 10, 10], [0, 0, 1, 0]))!;
        expect(Array.from(change.delta)).toEqual([2, -3, -1, 0]);
        expect(change).toMatchObject({ changed: 3, rise: 2, fall: -3 });
        const pixels = landChangePixels(change);
        expect(Array.from(pixels.slice(0, 3))).toEqual([224, 160, 32]);
        expect(Array.from(pixels.slice(4, 7))).toEqual([58, 123, 213]);
        expect(pixels[15]).toBe(0);
        expect(landChange(land([1, 2, 3, 4]), { ...land([1]), size: 1 })).toBeNull();
    });
});
