import { describe, expect, it } from 'vitest';
import type { FileTrees, JsonObject, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import { cellCentre, cellToLocal, cellToMap, insideOrOn, localToCell, mapToCell, nearestNode, roadStep, snapCell } from './cells.ts';
import { Stroke, paintDisc, rasterise, sculptMask, smoothed, strokeBlock, strokePatch, traceMask } from './strokes.ts';
import { appendToSketch, shapeAt, sketchShapes } from './sketch.ts';
import { appendManyToSketch, groundPatch, gridOf, spotOps, spotCell } from './outdoortools.ts';
import { bayCount, bayOps, partWalls, parseHouses, ruleBays, wallBays } from './bays.ts';
import { applyOpsLocally } from './ops.ts';

describe('cells and map units', () =>
{
    it('maps cells (x east, y south from the north-west corner) to map units (origin in the middle, y north) and back', () =>
    {
        expect(cellToMap([0, 0])).toEqual([-32768, 32768]);
        expect(cellToMap([64, 64])).toEqual([0, 0]);
        // view.layout's model box of a building at [56, 56] of 3 x 2 cells: x -4096..-2560, y 3072..4096.
        expect(cellToMap([56, 56])).toEqual([-4096, 4096]);
        expect(cellToMap([59, 58])).toEqual([-2560, 3072]);
        expect(mapToCell([-2560, 3072])).toEqual([59, 58]);
        expect(snapCell([12.3, 40.8], 0.5)).toEqual([12.5, 41]);
        expect(snapCell([-3, 140], 1)).toEqual([0, 128]);
        expect(cellCentre([12.9, 0.1])).toEqual([12.5, 0.5]);
        expect(nearestNode([127.8, -1])).toEqual([127, 0]);
        expect(localToCell([10, 20], [1024, 256])).toEqual([12, 20.5]);
        expect(cellToLocal([10, 20], [12, 20.5])).toEqual([1024, 256]);
    });

    it('steps a road square or at 45 degrees on cell centres', () =>
    {
        expect(roadStep([64.5, 64.5], [65.2, 80.1])).toEqual([64.5, 80.5]);
        expect(roadStep([64.5, 80.5], [71, 87.8])).toEqual([71.5, 87.5]);
        expect(roadStep([10.5, 10.5], [20.5, 11.5])).toEqual([20.5, 10.5]);
    });

    it('tells a point inside, on the edge of and outside a polygon', () =>
    {
        const square = [[0, 0], [4, 0], [4, 4], [0, 4]];
        expect(insideOrOn([2, 2], square)).toBe(true);
        expect(insideOrOn([4, 2], square)).toBe(true);
        expect(insideOrOn([4.01, 2], square)).toBe(false);
    });
});

describe('sculpt strokes', () =>
{
    it('lets the brush work inside a patch only (each node with its half cell), anywhere on land made by hand', () =>
    {
        const mask = sculptMask([[[10, 10], [20, 10], [20, 20], [10, 20]]], false);
        expect(mask[15 * 128 + 15]).toBe(1);
        expect(mask[10 * 128 + 10]).toBe(0);
        expect(mask[11 * 128 + 11]).toBe(1);
        expect(mask[30 * 128 + 30]).toBe(0);
        expect(sculptMask([], true).every((value) => value === 1)).toBe(true);
    });

    it('writes a raise stroke as one block of differences in steps of 32, null outside the brush', () =>
    {
        const stroke = new Stroke('raise', 2, 64, sculptMask([], true));
        // A diagonal stroke: the corners of its block lie outside the brush.
        stroke.to([20, 20]);
        stroke.to([26, 26]);
        const block = strokeBlock(stroke.delta)!;
        expect(block.at[0]).toBeLessThanOrEqual(19);
        expect(block.rows.length).toBeGreaterThanOrEqual(7);
        const values = block.rows.flat();
        expect(values.some((value) => value === null)).toBe(true);
        expect(values.filter((value): value is number => value !== null).every((value) => value > 0)).toBe(true);
        // In the block's middle row the stroke's line: its highest values.
        const middle = block.rows[20 - block.at[1]];
        expect(Math.max(...middle.map((value) => value ?? 0))).toBeGreaterThanOrEqual(2);
    });

    it('lowers by negative differences and leaves nodes outside the patch alone', () =>
    {
        const stroke = new Stroke('lower', 3, 64, sculptMask([[[10, 10], [14, 10], [14, 14], [10, 14]]], false));
        stroke.to([12, 12]);
        const block = strokeBlock(stroke.delta)!;
        expect(block.rows.flat().filter((value): value is number => value !== null).every((value) => value < 0)).toBe(true);
        expect(block.at[0]).toBeGreaterThanOrEqual(11);
        expect(block.at[0] + block.rows[0].length - 1).toBeLessThanOrEqual(13);
    });

    it('appends a new block, or patches the rows of the block that holds it whole (keyed, with tests)', () =>
    {
        const block = { at: [5, 5] as [number, number], rows: [[1, null], [2, 3]] };
        expect(strokePatch(block, undefined)).toEqual([{ op: 'add', path: '/heights/strokes', value: [{ at: [5, 5], rows: [[1, null], [2, 3]] }] }]);
        expect(strokePatch(block, [{ key: 'stroke1', at: [0, 0], rows: [[1]] }])).toEqual([{ op: 'add', path: '/heights/strokes/-', value: { at: [5, 5], rows: [[1, null], [2, 3]] } }]);
        const written = [{ key: 'big', at: [4, 4], rows: [[null, null, null], [null, 1, null], [null, null, null]] }];
        const steps = strokePatch(block, written);
        expect(steps).toEqual([
            { op: 'test', path: '/heights/strokes/big/rows/1', value: [null, 1, null] },
            { op: 'replace', path: '/heights/strokes/big/rows/1', value: [null, 2, null] },
            { op: 'test', path: '/heights/strokes/big/rows/2', value: [null, null, null] },
            { op: 'replace', path: '/heights/strokes/big/rows/2', value: [null, 2, 3] },
        ]);
    });

    it('smooths toward the mean around each masked node', () =>
    {
        const heights = new Float32Array(16 * 16);
        heights[8 * 16 + 8] = 160;
        const mask = new Uint8Array(16 * 16);
        mask[8 * 16 + 8] = 1;
        const after = smoothed(heights, mask, 1, 1, 16);
        expect(after[8 * 16 + 8]).toBe(0);
        expect(after[8 * 16 + 7]).toBe(0);
    });
});

describe('masks traced into outlines', () =>
{
    it('traces a block of cells into its four corners', () =>
    {
        const mask = new Uint8Array(8 * 8);
        for (let y = 2; y < 4; ++y)
        {
            for (let x = 1; x < 5; ++x)
            {
                mask[y * 8 + x] = 1;
            }
        }
        expect(traceMask(mask, 8, 8)).toEqual([[[1, 2], [5, 2], [5, 4], [1, 4]]]);
    });

    it('traces an L, two pieces apart, two pieces touching at a corner, and fills a hole', () =>
    {
        const mask = new Uint8Array(10 * 10);
        const set = (cells: [number, number][]) => cells.forEach(([x, y]) => { mask[y * 10 + x] = 1; });
        set([[0, 0], [1, 0], [0, 1]]);
        set([[5, 5], [6, 6]]);
        const loops = traceMask(mask, 10, 10);
        expect(loops.length).toBe(3);
        expect(loops[0]).toEqual([[0, 0], [2, 0], [2, 1], [1, 1], [1, 2], [0, 2]]);
        const ring = new Uint8Array(5 * 5);
        for (let y = 1; y < 4; ++y)
        {
            for (let x = 1; x < 4; ++x)
            {
                ring[y * 5 + x] = x === 2 && y === 2 ? 0 : 1;
            }
        }
        expect(traceMask(ring, 5, 5)).toEqual([[[1, 1], [4, 1], [4, 4], [1, 4]]]);
    });

    it('offsets a node mask by half a cell (a smooth stroke\'s outline round its nodes)', () =>
    {
        const mask = new Uint8Array(4 * 4);
        mask[1 * 4 + 1] = 1;
        expect(traceMask(mask, 4, 4, -0.5)).toEqual([[[0.5, 0.5], [1.5, 0.5], [1.5, 1.5], [0.5, 1.5]]]);
    });

    it('rasterises an outline and paints a round brush', () =>
    {
        const mask = new Uint8Array(16 * 16);
        rasterise([[2, 2], [6, 2], [6, 5], [2, 5]], mask, 16);
        expect(mask.reduce((sum, value) => sum + value, 0)).toBe(12);
        const disc = new Uint8Array(16 * 16);
        paintDisc(disc, 16, [8, 8], 2, 1);
        expect(disc[7 * 16 + 7]).toBe(1);
        expect(disc[8 * 16 + 11]).toBe(0);
    });
});

const files = (sketch: JsonObject): FileTrees => ({ 'project.yml': { tree: { kind: 'outdoor', world: 'mm6' } }, 'sketch.yml': { tree: sketch } });

describe('the sketch\'s words on the plan', () =>
{
    const sketch: JsonObject = {
        heights: { grid: { step: 16, unit: 64, rows: [[4, 4], [4, 4]] }, ridges: [{ line: [[10, 10], [20, 10]], height: 500 }], patches: [{ key: 'p', polygon: [[0, 0], [8, 0], [8, 8], [0, 8]] }] },
        water: { bodies: [{ id: 'zone:pond', polygon: [[40, 40], [44, 40], [44, 44], [40, 44]] }] },
        roads: [{ link: 'link:a', line: [[64.5, 64.5], [64.5, 80.5]] }],
        structures: [{ id: 'thing:hall', kind: 'building', at: [50, 50], size: [4, 2], parts: [{ id: 'main', at: [0, 0], size: [1024, 1024] }, { at: [1024, 0], size: [1024, 512] }] },
            { id: 'thing:well', kind: 'well', at: [60, 60] }, { id: 'thing:wall', kind: 'wall', line: [[70, 70], [74, 70]] }],
        actors: [{ id: 'pop:a', monster: 'Peasant', at: [61, 61] }],
        areas: [{ id: 'pop:wolves', kind: 'encounter', circle: { at: [90, 90], r: 3 } }],
    };

    it('reads every word with a place, addressed by id, by its building, or by its pointer in the file', () =>
    {
        const shapes = sketchShapes(files(sketch));
        const addresses = shapes.map((shape) => shape.address);
        expect(addresses).toContain('/heights/ridges/ridge1');
        expect(addresses).toContain('/heights/patches/p');
        expect(addresses).toContain('/water/bodies/zone:pond');
        expect(addresses).toContain('/roads/road1');
        expect(addresses).toContain('thing:hall/parts/main');
        expect(addresses).toContain('thing:hall/parts/part2');
        const part2 = shapes.find((shape) => shape.address === 'thing:hall/parts/part2')!;
        expect(part2.cells).toEqual([[52, 50], [54, 50], [54, 51], [52, 51]]);
        expect(part2.edit).toMatchObject({ id: 'thing:hall', base: '/parts/part2', kind: 'box', local: true });
        expect(shapes.find((shape) => shape.address === 'thing:wall')?.geom).toBe('polyline');
    });

    it('picks points first, then lines, then the smallest outline; parts only inside an entered building', () =>
    {
        const shapes = sketchShapes(files(sketch));
        expect(shapeAt(shapes, [60.1, 60], 0.5)?.address).toBe('thing:well');
        expect(shapeAt(shapes, [15, 10.2], 0.5)?.address).toBe('/heights/ridges/ridge1');
        expect(shapeAt(shapes, [52.5, 50.5], 0.3)?.address).toBe('thing:hall');
        expect(shapeAt(shapes, [52.5, 50.5], 0.3, 'thing:hall')?.address).toBe('thing:hall/parts/part2');
        expect(shapeAt(shapes, [91, 90], 0.3)?.address).toBe('pop:wolves');
    });

    it('appends to a list of the sketch, making the list and what is above it when missing, keyed lists walked by key', () =>
    {
        expect(appendToSketch(files(sketch), '/heights/ridges', { line: [], height: 1 })).toEqual({ op: 'patch', file: 'sketch.yml', patch: [{ op: 'add', path: '/heights/ridges/-', value: { line: [], height: 1 } }] });
        expect(appendToSketch(files(sketch), '/heights/cliffs', { drop: 1 })).toEqual({ op: 'patch', file: 'sketch.yml', patch: [{ op: 'add', path: '/heights/cliffs', value: [{ drop: 1 }] }] });
        expect(appendToSketch(files(sketch), '/frame/rim', { side: 'north' })).toEqual({ op: 'patch', file: 'sketch.yml', patch: [{ op: 'add', path: '/frame', value: { rim: [{ side: 'north' }] } }] });
        const withDistrict = files({ districts: [{ key: 'town', space: 'zone:t', polygon: [] }] });
        expect(appendToSketch(withDistrict, '/districts/town/plots', { building: 'b' })).toEqual({ op: 'patch', file: 'sketch.yml', patch: [{ op: 'add', path: '/districts/town/plots', value: [{ building: 'b' }] }] });
        const many = appendManyToSketch(files(sketch), '/heights/smooth', [{ polygon: [1] }, { polygon: [2] }]);
        const after = applyOpsLocally(files(sketch), [many]);
        expect(((after['sketch.yml']!.tree.heights as JsonObject).smooth as JsonObject[]).length).toBe(2);
    });

    it('reads the grid\'s spots and writes a painted spot as a positional patch with a test', () =>
    {
        const grid = gridOf(files(sketch))!;
        expect(spotCell(grid, 1, 0)).toEqual([24, 8]);
        expect(spotOps(grid, new Map([['0,1', 10], ['1,1', 4]]))).toEqual({ op: 'patch', file: 'sketch.yml', patch: [
            { op: 'test', path: '/heights/grid/rows/0/1', value: 4 }, { op: 'replace', path: '/heights/grid/rows/0/1', value: 10 }] });
    });
});

describe('the ground brush', () =>
{
    const strip = () =>
    {
        const painted = new Uint8Array(128 * 128);
        for (let x = 10; x < 20; ++x)
        {
            painted[5 * 128 + x] = 1;
            painted[6 * 128 + x] = 1;
        }
        return painted;
    };

    it('lays the world\'s first kind over the whole map, then the painted kind traced, when the sketch has no zones', () =>
    {
        const made = groundPatch(files({}), 'sand', strip());
        expect(made).toEqual({ steps: [{ op: 'add', path: '/ground', value: [
            { material: 'grass', polygon: [[0, 0], [128, 0], [128, 128], [0, 128]] }, { material: 'sand', polygon: [[10, 5], [20, 5], [20, 7], [10, 7]] }] }], kinds: ['grass', 'sand'] });
    });

    it('merges a stroke into the kind\'s zone by key, and takes the cells from the other kinds', () =>
    {
        const sketch = { ground: [{ key: 'base', material: 'grass', polygon: [[0, 0], [128, 0], [128, 128], [0, 128]] }, { key: 'beach', material: 'sand', polygon: [[10, 5], [20, 5], [20, 7], [10, 7]] }] };
        const more = new Uint8Array(128 * 128);
        for (let x = 10; x < 20; ++x)
        {
            more[7 * 128 + x] = 1;
        }
        const made = groundPatch(files(sketch), 'sand', more) as { steps: PatchStep[] };
        expect(made.steps).toEqual([{ op: 'replace', path: '/ground/beach/polygon', value: [[10, 5], [20, 5], [20, 8], [10, 8]] }]);
        // Grass painted over the sand: the sand zone is taken out (the whole-map grass already holds the cells).
        const back = groundPatch(files(sketch), 'grass', strip()) as { steps: PatchStep[] };
        expect(back.steps).toEqual([{ op: 'remove', path: '/ground/beach' }]);
    });

    it('refuses a third kind of land besides dirt', () =>
    {
        const sketch = { ground: [{ material: 'grass', polygon: [[0, 0], [128, 0], [128, 128], [0, 128]] }, { material: 'sand', polygon: [[10, 5], [20, 5], [20, 7], [10, 7]] }] };
        expect('refused' in groundPatch(files(sketch), 'snow', strip())).toBe(true);
    });
});

describe('the wall bay strip', () =>
{
    const building = { id: 'thing:inn', kind: 'building', at: [10, 10], size: [2, 3], parts: [{ id: 'main', size: [1024, 1536] }] } as JsonObject;
    const part = (building.parts as JsonObject[])[0];

    it('gives a box part its four walls and the bays the build lays on each by rule', () =>
    {
        const walls = partWalls(part, [1024, 1536]);
        expect(walls).toEqual([{ name: 's', length: 1024 }, { name: 'e', length: 1536 }, { name: 'n', length: 1024 }, { name: 'w', length: 1536 }]);
        expect(bayCount(1024)).toBe(8);
        expect(ruleBays(8, true)).toEqual(['post_left', 'window', 'wall', 'window', 'door', 'window', 'wall', 'post_right']);
        expect(wallBays(part, walls[0], true, 2).bays[2]).toBe('door');
        expect(partWalls({ shape: 'round', radius: 256, sides: 6 }, [0, 0]).length).toBe(6);
    });

    it('writes the wall whole when a bay becomes the door, and the building\'s door there', () =>
    {
        const walls = partWalls(part, [1024, 1536]);
        const bays = wallBays(part, walls[0], true).bays;
        expect(bayOps('thing:inn', building, 'main', part, walls[0], bays, 2, 'door')).toEqual({ op: 'patch', id: 'thing:inn', file: 'sketch.yml', patch: [
            { op: 'add', path: '/parts/main/walls', value: { s: ['post_left', 'window', 'door', 'window', 'wall', 'window', 'wall', 'post_right'] } },
            { op: 'add', path: '/door', value: { part: 'main', wall: 's', bay: 2 } }] });
    });

    it('reads the house table', () =>
    {
        const text = 'header\n#\t#\tType\tMap\tPicture\tName\n1\t1\tWeapon Shop\t1\t16\tTrue Mettle\tKervin\n228\t228\tTavern\t1\t2\tThe Grog and Grub\tx\n';
        expect(parseHouses(text)).toEqual([{ number: 1, type: 'Weapon Shop', name: 'True Mettle' }, { number: 228, type: 'Tavern', name: 'The Grog and Grub' }]);
    });
});
