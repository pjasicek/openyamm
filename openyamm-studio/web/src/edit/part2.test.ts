// S5b1 part 2's pure parts: the placed things' geometry and operations, the Wire stage's link and switch board, the
// Library's surfaces and drops, the Checklist.
import { describe, expect, it } from 'vitest';
import type { FileTrees, JsonObject, Op } from '../../../schema/rpc/generated/rpc.ts';
import { applyOpsLocally } from './ops.ts';
import { degreesOf, facingDegrees, facingOp, moveOp, nearestWall, placedAt, placedThings, radiusOp, slideOp, wallEdge, wallName, wallPoint } from './things.ts';
import { boardOf, cellChange, eventsFrom, linkChange, links, nextVerb, toScriptOp, verbOf } from './wiring.ts';
import { roomSurfacePlan, surfaceOf, wallSurfaceOp } from './surfaces.ts';
import { dropPlan } from './drop.ts';
import { spacesWithoutRoom, stageItems, unwired } from '../model/checklist.ts';

const files = (): FileTrees => ({
    'rooms.yml': { tree: {
        format: 1,
        themes: [{ id: 'theme:stone', wall: { texture: 't1w11a', size: [128, 256] }, floor: { texture: 'oflr', size: [128, 128] } }],
        defaults: { theme: 'theme:stone' },
        rooms: [
            { id: 'room:hall', outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 0, ceiling: 512 },
            { id: 'room:side', outline: [[1088, 128], [1600, 128], [1600, 640], [1088, 640]], floor: 0, ceiling: 384, space: 'space:side' },
            // An L: two walls face east.
            { id: 'room:ell', outline: [[0, 1000], [512, 1000], [512, 1256], [256, 1256], [256, 1512], [0, 1512]], floor: 0, ceiling: 384 },
        ],
        openings: [{ id: 'open:hall_side', from: 'room:hall', to: 'room:side', width: 192, height: 256 }],
    } },
    'objects.yml': { tree: {
        format: 1,
        start: { room: 'room:hall', at: [100, 100], facing: 'n' },
        doors: [{ id: 'door:gate', opening: 'open:hall_side' }, { id: 'door:back', opening: 'open:hall_side' }],
        switches: [{ id: 'switch:lever', room: 'room:hall', wall: 'north', along: 0.25, kind: 'lever' }, { id: 'switch:spare', room: 'room:hall', wall: 2 }],
        chests: [{ id: 'chest:box', room: 'room:side', at: [1300, 400], facing: 90 }],
        lights: [{ id: 'light:lamp', room: 'room:hall', offset: [100, 0], radius: 512 }],
        spawns: [{ id: 'spawn:rats', room: 'room:hall', at: [700, 300] }],
    } },
    'wiring.yml': { tree: {
        format: 0,
        events: [
            { id: 'evt:lever', preset: 'switch', source: 'switch:lever', toggles: ['door:gate'] },
            { id: 'evt:gate', preset: 'door', source: 'door:gate', title: 'Gate' },
            { id: 'evt:chest', preset: 'chest', source: 'chest:box' },
            { id: 'evt:timer', preset: 'text', source: 'switch:lever', trigger: 'timer', every: 10 },
        ],
    } },
    'plan.yml': { tree: { format: 1, spaces: [{ id: 'space:side', purpose: 'store' }, { id: 'space:crypt', name: 'Crypt', purpose: 'the end' }] } },
});

const rooms = (f: FileTrees) => f['rooms.yml']!.tree.rooms as JsonObject[];
const outline = (f: FileTrees, id: string) => (rooms(f).find((room) => room.id === id)!.outline as number[][]);

describe('placed things', () =>
{
    it('reads facings as compass words or degrees', () =>
    {
        expect(facingDegrees('n')).toBe(90);
        expect(facingDegrees('southwest')).toBe(225);
        expect(facingDegrees(30)).toBe(30);
        expect(facingDegrees('up')).toBeUndefined();
        expect(degreesOf(0, 1, 15)).toBe(90);
        expect(degreesOf(-1, -0.01, 15)).toBe(180);
        expect(degreesOf(1, -1, 0)).toBe(315);
    });

    it('names walls by compass side where one wall alone faces it, else by edge', () =>
    {
        const hall = outline(files(), 'room:hall');
        expect(wallEdge(hall, 'north')).toBe(2);
        expect(wallEdge(hall, 'e')).toBe(1);
        expect(wallName(hall, 2)).toBe('north');
        const ell = outline(files(), 'room:ell');
        // Edges 1 and 3 both face east: the edge number is exact.
        expect(wallName(ell, 1)).toBe(1);
        expect(wallName(ell, 3)).toBe(3);
        expect(wallName(ell, 0)).toBe('south');
    });

    it('finds the place along a wall counter-clockwise, and back', () =>
    {
        const hall = outline(files(), 'room:hall');
        expect(wallPoint(hall, 2, 0.25)).toEqual([768, 768]);
        const near = nearestWall(hall, [770, 760])!;
        expect(near.edge).toBe(2);
        expect(near.along).toBeCloseTo(0.248, 2);
        expect(Math.round(near.distance)).toBe(8);
    });

    it('places every thing of the files: points, walls, offsets from the middle, the start', () =>
    {
        const things = placedThings(files(), null);
        const at = (address: string) => things.find((thing) => thing.address === address);
        expect(at('switch:lever')!.at).toEqual([768, 768]);
        expect(at('switch:lever')!.wall).toEqual({ edge: 2, along: 0.25 });
        expect(at('switch:spare')!.at).toEqual([512, 768]);
        expect(at('light:lamp')!.at).toEqual([612, 384]);
        expect(at('light:lamp')!.radius).toBe(512);
        expect(at('chest:box')!.facing).toBe(90);
        expect(at('start')!.facing).toBe(90);
        expect(placedAt(things, [705, 296], 10)!.address).toBe('spawn:rats');
        expect(placedAt(things, [900, 100], 10)).toBeNull();
    });

    it('marks a thing added on the client as a ghost until the core gives its id', () =>
    {
        const after = applyOpsLocally(files(), [{ op: 'add', to: 'lights', file: 'objects.yml', value: { room: 'room:hall', at: [50, 50] } }]);
        expect(placedThings(after, null).find((thing) => thing.at[0] === 50)!.ghost).toBe(true);
    });

    it('moves, slides, turns and sizes things by operations the client applies too', () =>
    {
        const f = files();
        const things = placedThings(f, null);
        const lamp = things.find((thing) => thing.address === 'light:lamp')!;
        const ops: Op[] = [moveOp(lamp, [200, 200], 'room:hall'), radiusOp(lamp, 640)!,
            slideOp(things.find((thing) => thing.address === 'switch:lever')!, 'east', 0.5),
            facingOp(things.find((thing) => thing.address === 'chest:box')!, 180), moveOp(things.find((thing) => thing.address === 'start')!, [300, 300], undefined)];
        const after = applyOpsLocally(f, ops);
        const objects = after['objects.yml']!.tree;
        const light = (objects.lights as JsonObject[])[0];
        expect(light.at).toEqual([200, 200]);
        expect(light.offset).toBeUndefined();
        expect(light.radius).toBe(640);
        expect((objects.switches as JsonObject[])[0]).toMatchObject({ wall: 'east', along: 0.5 });
        expect((objects.chests as JsonObject[])[0].facing).toBe(180);
        expect((objects.start as JsonObject).at).toEqual([300, 300]);
        // A thing moved into another room names it.
        expect(moveOp(lamp, [1300, 300], 'room:side')).toMatchObject({ fields: { room: 'room:side' } });
    });
});

describe('wiring', () =>
{
    it('lists a thing\'s click events (not its timer)', () =>
    {
        expect(eventsFrom(files(), 'switch:lever').map((event) => event.id)).toEqual(['evt:lever']);
    });

    it('links: a new target added to the source\'s event, a linked one taken out, a new event for a source without one', () =>
    {
        const f = files();
        const add = linkChange(f, 'switch:lever', 'door:back', 'opens')!;
        let after = applyOpsLocally(f, add.ops);
        expect((after['wiring.yml']!.tree.events as JsonObject[])[0].opens).toEqual(['door:back']);
        const remove = linkChange(after, 'switch:lever', 'door:gate', 'toggles')!;
        after = applyOpsLocally(after, remove.ops);
        expect((after['wiring.yml']!.tree.events as JsonObject[])[0].toggles).toBeUndefined();
        const made = linkChange(f, 'switch:spare', 'door:gate', 'toggles')!;
        expect(made.ops[0]).toMatchObject({ op: 'add', to: 'events', value: { preset: 'switch', source: 'switch:spare', toggles: ['door:gate'], title: 'Switch' } });
        expect(linkChange(f, 'door:gate', 'door:gate', 'toggles')).toBeNull();
        // A door's own click event takes the link (an airlock).
        expect(linkChange(f, 'door:gate', 'door:back', 'closes')!.ops[0]).toMatchObject({ op: 'patch', id: 'evt:gate', patch: [{ op: 'add', path: '/closes', value: ['door:back'] }] });
    });

    it('builds the switch board and cycles a cell: none, toggles, opens, closes, none', () =>
    {
        const board = boardOf(files());
        expect(board.columns).toEqual(['door:gate', 'door:back']);
        expect(board.rows.map((row) => row.event?.id ?? row.source)).toEqual(['evt:lever', 'evt:timer', 'switch:spare']);
        expect([null, 'toggles', 'opens', 'closes'].map((verb) => nextVerb(verb as never))).toEqual(['toggles', 'opens', 'closes', null]);
        let f = files();
        const seen: (string | null)[] = [];
        for (let i = 0; i < 4; ++i)
        {
            const row = boardOf(f).rows[0];
            f = applyOpsLocally(f, cellChange(f, row, 'door:back')!.ops);
            seen.push(verbOf((f['wiring.yml']!.tree.events as JsonObject[])[0], 'door:back'));
        }
        expect(seen).toEqual(['toggles', 'opens', 'closes', null]);
        // The gate keeps its toggle all along.
        expect(verbOf((f['wiring.yml']!.tree.events as JsonObject[])[0], 'door:gate')).toBe('toggles');
        const spare = boardOf(f).rows[2];
        expect(cellChange(f, spare, 'door:gate')!.ops[0]).toMatchObject({ op: 'add', value: { source: 'switch:spare', toggles: ['door:gate'] } });
    });

    it('converts to a script keeping the preset\'s own work as words', () =>
    {
        const events = files()['wiring.yml']!.tree.events as JsonObject[];
        expect(toScriptOp(events[1])).toMatchObject({ op: 'set', id: 'evt:gate', fields: { preset: 'script', toggles: ['door:gate'] } });
        expect(toScriptOp(events[2])).toMatchObject({ fields: { preset: 'script', effects: [{ open_chest: 'chest:box' }] } });
        expect(typeof (toScriptOp(events[0]) as { fields: JsonObject }).fields.lua).toBe('string');
    });

    it('draws links between sources and what they move', () =>
    {
        expect(links(files())).toEqual([{ event: 'evt:lever', source: 'switch:lever', target: 'door:gate', verb: 'toggles' }]);
    });
});

describe('surfaces and drops', () =>
{
    it('lays a texture on one wall: a walls entry, by compass side', () =>
    {
        const f = files();
        const op = wallSurfaceOp(f, 'room:hall', 2, surfaceOf({ name: 't1w11b', size: [128, 256] }))!;
        expect(op).toMatchObject({ op: 'patch', id: 'room:hall', patch: [{ op: 'add', path: '/walls', value: [{ wall: 'north', surface: { texture: 't1w11b', size: [128, 256] } }] }] });
        const after = applyOpsLocally(f, [op]);
        const again = wallSurfaceOp(after, 'room:hall', 2, surfaceOf({ name: 't1w12', width: 64, height: 64 }))!;
        expect(again).toMatchObject({ patch: [{ op: 'replace', path: '/walls/north/surface', value: { texture: 't1w12', size: [64, 64] } }] });
    });

    it('gives a room its own theme for a floor or ceiling when others share the theme, else changes its own', () =>
    {
        const f = files();
        const plan = roomSurfacePlan(f, 'room:hall', 'floor', { texture: 'd2ceil1', size: [256, 256] })!;
        expect(plan.kind).toBe('new');
        if (plan.kind === 'new')
        {
            expect(plan.add).toMatchObject({ op: 'add', to: 'themes', value: { wall: { texture: 't1w11a' }, floor: { texture: 'd2ceil1' } } });
            expect(plan.assign('theme:theme_1')).toEqual({ op: 'set', id: 'room:hall', file: 'rooms.yml', fields: { theme: 'theme:theme_1' } });
        }
        const own = applyOpsLocally(f, [{ op: 'add', to: 'themes', file: 'rooms.yml', value: { id: 'theme:own' } }, { op: 'set', id: 'room:hall', file: 'rooms.yml', fields: { theme: 'theme:own' } }]);
        expect(roomSurfacePlan(own, 'room:hall', 'ceiling', { texture: 'd2ceil4' })).toEqual({ kind: 'set', op: { op: 'set', id: 'theme:own', file: 'rooms.yml', fields: { ceiling: { texture: 'd2ceil4' } } } });
    });

    it('decides a drop by where it lands: a wall near it, the floor, Shift the ceiling; a decoration on a wall or the floor', () =>
    {
        const f = files();
        const texture = { kind: 'texture' as const, name: 't1w15', size: [128, 256] };
        expect(dropPlan(f, null, texture, { where: 'plan', at: [500, 760], shift: false, alt: false, reach: 20 }, 144)).toMatchObject({ kind: 'ops', ops: [{ op: 'patch', id: 'room:hall' }] });
        expect(dropPlan(f, null, texture, { where: 'plan', at: [500, 400], shift: false, alt: false, reach: 20 }, 144)).toMatchObject({ kind: 'theme' });
        expect(dropPlan(f, null, texture, { where: 'plan', at: [5000, 400], shift: false, alt: false, reach: 20 }, 144).kind).toBe('note');
        expect(dropPlan(f, null, texture, { where: '3d', owner: 'room:hall/walls/1', point: [1024, 300, 100], alt: false }, 144)).toMatchObject({ kind: 'ops', ops: [{ patch: [{ value: [{ wall: 'east' }] }] }] });
        const ceiling = dropPlan(f, null, texture, { where: '3d', owner: 'room:hall', point: [500, 300, 512], normal: [0, 0, -1], alt: false }, 144);
        expect(ceiling.kind === 'theme' && ceiling.label.includes('ceiling')).toBe(true);
        const torch = { kind: 'decoration' as const, name: 'torch01' };
        expect(dropPlan(f, null, torch, { where: 'plan', at: [500, 762], shift: false, alt: false, reach: 20 }, 144))
            .toMatchObject({ kind: 'ops', ops: [{ op: 'add', to: 'decorations', value: { room: 'room:hall', wall: 'north', height: 144, decoration: 'torch01' } }] });
        expect(dropPlan(f, null, torch, { where: 'plan', at: [500, 400], shift: false, alt: false, reach: 20 }, 144))
            .toMatchObject({ ops: [{ value: { room: 'room:hall', at: [500, 400], decoration: 'torch01' } }] });
    });
});

describe('the checklist', () =>
{
    it('lists planned spaces without a room, things no event uses, and each stage\'s state', () =>
    {
        const f = files();
        expect(spacesWithoutRoom(f).map((space) => space.id)).toEqual(['space:crypt']);
        expect(unwired(f)).toEqual(['switch:spare']);
        const items = stageItems(f, []);
        expect(items.find((item) => item.stage === 2)!.state).toBe('open');
        expect(items.find((item) => item.stage === 4)!.why).toContain('switch:spare');
        expect(items.find((item) => item.stage === 7)!.state).toBe('open');
        expect(items.find((item) => item.stage === 5)!.state).toBe('judge');
    });
});
