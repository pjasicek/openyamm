// The world view's layout (S6_PLAN.md 2.9): outdoor maps on a grid by their map edges, dungeons round the outdoor map
// they link to, loose maps in a row below; no two boxes overlap; one line per pair of maps.
import { describe, expect, it } from 'vitest';
import { boxEdgePoint, layoutWorld, roleCounts, worldEdges } from './world.ts';
import type { WorldEntry } from './world.ts';

// MM6 in small: New Sorpigal's rebuild with Castle Ironfist west of it (both ways), Goblinwatch's rebuild and a
// shipped temple off New Sorpigal, a dungeon off Ironfist, a shipped map north of Ironfist, and a dungeon on its own.
const world: WorldEntry = {
    world: 'mm6',
    maps: [
        { map: 'calib_newsorpigal.odm', kind: 'outdoor', role: 'rebuild', name: 'New Sorpigal', project: 0, stands_for: 'oute3.odm' },
        { map: 'calib_ironfist.odm', kind: 'outdoor', role: 'rebuild', name: 'Castle Ironfist', project: 1, stands_for: 'outd3.odm' },
        { map: 'cal6d01.blv', kind: 'indoor', role: 'rebuild', name: 'Goblinwatch', project: 2, stands_for: '6d01.blv' },
        { map: 'loose.blv', kind: 'indoor', role: 'new', name: 'Loose', project: 3 },
        { map: '6d02.blv', kind: 'indoor', role: 'shipped', name: 'Abandoned Temple' },
        { map: '6d05.blv', kind: 'indoor', role: 'shipped', name: 'Dragoons\' Caverns' },
        { map: 'outd2.odm', kind: 'outdoor', role: 'shipped', name: 'Frozen Highlands' },
    ],
    links: [
        { from: 0, to: 1, id: 'edge:west', kind: 'edge', side: 'west', days: 5, target: 'outd3.odm', via_original: true, exits: ['entrance:west'] },
        { from: 1, to: 0, id: 'edge:east', kind: 'edge', side: 'east', target: 'oute3.odm', via_original: true, exits: [] },
        { from: 0, to: 2, id: 'door:goblinwatch', kind: 'door', target: '6d01.blv', via_original: true, exits: ['thing:building_29'] },
        { from: 2, to: 0, id: 'exit:new_sorpigal', kind: 'door', target: 'oute3.odm', via_original: true, exits: ['exit:way_out'] },
        { from: 0, to: 4, id: 'door:temple', kind: 'door', target: '6d02.blv', via_original: false, exits: [] },
        { from: 1, to: 5, id: 'door:d05', kind: 'door', target: '6d05.blv', via_original: false, exits: [] },
        { from: 1, to: 6, id: 'edge:north', kind: 'edge', side: 'north', target: 'outd2.odm', via_original: false, exits: [] },
    ],
};

describe('the world map', () =>
{
    it('joins the links of a pair into one line, with both directions and their kinds', () =>
    {
        const edges = worldEdges(world);
        const sorpigalIronfist = edges.find((edge) => edge.a === 0 && edge.b === 1)!;
        expect(sorpigalIronfist.forward && sorpigalIronfist.backward).toBe(true);
        expect(sorpigalIronfist.kinds).toEqual(['edge']);
        expect(sorpigalIronfist.viaOriginal).toBe(true);
        expect(sorpigalIronfist.titles[0]).toBe('calib_newsorpigal.odm to outd3.odm (edge, west, 5 days): edge:west, used by entrance:west');
        const temple = edges.find((edge) => edge.b === 4)!;
        expect([temple.forward, temple.backward]).toEqual([true, false]);
        expect(temple.viaOriginal).toBe(false);
        expect(edges).toHaveLength(5);
    });

    it('puts outdoor maps where their map edges say, dungeons round theirs, the loose one below', () =>
    {
        const layout = layoutWorld(world);
        const at = (index: number) => layout.maps.find((place) => place.index === index)!;
        expect(layout.maps.map((place) => place.index)).toEqual([0, 1, 2, 3, 4, 5, 6]);
        // Ironfist west of New Sorpigal, on its row; the Highlands north of Ironfist.
        expect(at(1).x).toBeLessThan(at(0).x);
        expect(at(1).y).toBe(at(0).y);
        expect(at(6).y).toBeLessThan(at(1).y);
        expect(at(6).x).toBe(at(1).x);
        const distance = (a: number, b: number) => Math.hypot(at(a).x - at(b).x, at(a).y - at(b).y);
        // Goblinwatch and the temple round New Sorpigal, the caverns round Ironfist.
        expect(distance(2, 0)).toBeLessThan(distance(2, 1));
        expect(distance(4, 0)).toBeLessThan(distance(4, 1));
        expect(distance(5, 1)).toBeLessThan(distance(5, 0));
        // The loose dungeon under everything else.
        expect(at(3).y).toBeGreaterThan(Math.max(...[0, 1, 2, 4, 5, 6].map((index) => at(index).y)));
        // No two boxes overlap.
        for (const p of layout.maps)
        {
            for (const q of layout.maps)
            {
                if (p !== q)
                {
                    const apart = Math.abs(p.x - q.x) >= (p.width + q.width) / 2 || Math.abs(p.y - q.y) >= (p.height + q.height) / 2;
                    expect(apart).toBe(true);
                }
            }
        }
        expect(layout.bounds[0]).toBeLessThanOrEqual(Math.min(...layout.maps.map((place) => place.x - place.width / 2)));
        // The same answer, the same picture.
        expect(layoutWorld(world)).toEqual(layout);
    });

    it('puts a second group of outdoor maps beside the first, and counts the roles', () =>
    {
        const two: WorldEntry = { world: 'mm7', maps: [
            { map: 'a.odm', kind: 'outdoor', role: 'new', name: 'A', project: 0 },
            { map: 'b.odm', kind: 'outdoor', role: 'new', name: 'B', project: 1 },
        ], links: [] };
        const layout = layoutWorld(two);
        expect(layout.maps[1]!.x).toBeGreaterThan(layout.maps[0]!.x);
        expect(roleCounts(world)).toEqual({ new: 1, rebuild: 3, overlay: 0, shipped: 3 });
        // A line ends on the box's edge, toward the other box.
        expect(boxEdgePoint({ index: 0, x: 0, y: 0, width: 100, height: 40 }, [200, 0])).toEqual([50, 0]);
        expect(boxEdgePoint({ index: 0, x: 0, y: 0, width: 100, height: 40 }, [0, -90])).toEqual([0, -20]);
    });
});
