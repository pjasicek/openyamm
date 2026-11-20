import { describe, expect, it } from 'vitest';
import { cellToWorld, distanceToSegment, emptyBounds, extend, fit, floorClusters, pointInPolygon, polygonArea, toScreen, toWorld, zoomAt } from './geometry.ts';

describe('plan geometry', () =>
{
    it('maps world to screen with north up and back', () =>
    {
        const view = fit(extend(extend(emptyBounds(), [0, 0]), [1000, 500]), 1000, 500, 0);
        expect(toScreen(view, 0, 500)).toEqual([0, 0]);
        expect(toScreen(view, 1000, 0)).toEqual([1000, 500]);
        expect(toWorld(view, 250, 125)).toEqual([250, 375]);
    });

    it('zooms about the cursor', () =>
    {
        const view = fit(extend(extend(emptyBounds(), [0, 0]), [1000, 1000]), 500, 500, 0);
        const zoomed = zoomAt(view, 100, 100, 2);
        expect(toWorld(zoomed, 100, 100).map(Math.round)).toEqual(toWorld(view, 100, 100).map(Math.round));
        expect(zoomed.scale).toBeCloseTo(view.scale * 2);
    });

    it('tests points, segments and areas', () =>
    {
        const square = [[0, 0], [10, 0], [10, 10], [0, 10]];
        expect(pointInPolygon([5, 5], square)).toBe(true);
        expect(pointInPolygon([15, 5], square)).toBe(false);
        expect(distanceToSegment([5, 5], [0, 0], [10, 0])).toBe(5);
        expect(polygonArea(square)).toBe(100);
    });

    it('clusters floors into bands at gaps', () =>
    {
        expect(floorClusters([0, 64, -512, 1024, 1100], 384)).toEqual([[-512, -512], [0, 64], [1024, 1100]]);
    });

    it('puts outdoor cells with the north-west corner first', () =>
    {
        expect(cellToWorld(0, 0, 128, 512)).toEqual([-32768, 32768]);
        expect(cellToWorld(64, 64, 128, 512)).toEqual([0, 0]);
    });
});
