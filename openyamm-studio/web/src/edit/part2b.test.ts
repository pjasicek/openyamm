// S5b1 part two's tools, driven through a fake ToolHost as the plan drives them: the Plan stage's bubbles, links and
// goals; the Lift, Mover, Plate, Floor and Ladder tools; Height points, Flight, Parapet, Beam and Ceiling level; a
// switch on a platform's top (its id from the core first); the map's variables renamed with the events that name
// them; a 3D pick turned into a plan point; the Library's monsters, items and sounds dropped.
import { describe, expect, it } from 'vitest';
import type { EditApplyResult, FileTrees, JsonObject, Op } from '../../../schema/rpc/generated/rpc.ts';
import type { Gesture } from './session.ts';
import type { ToolHost } from './toolbase.ts';
import { DEFAULT_OPTIONS } from './stages.ts';
import type { ToolName, ToolOptions } from './stages.ts';
import { makeTool } from './tools.ts';
import { floorHeightAt, objectBlocks } from './blocks.ts';
import { planLinks, spaceAt, spacePlaces } from './plantools.ts';
import { dropPlan } from './drop.ts';
import { renameVariableOps, addVariableOp, variablesOf } from '../ui/Variables.tsx';
import { planPointOfPick } from '../ui/Views.tsx';
import { addRowOp, fieldOp, rowOp } from './formops.ts';

const files = (): FileTrees => ({
    'rooms.yml': { tree: {
        format: 1,
        rooms: [
            { id: 'room:hall', space: 'space:hall', outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 0, ceiling: 512,
                levels: [{ key: 'gallery', outline: [[640, 448], [960, 448], [960, 704], [640, 704]], floor: 64 }],
                platforms: [{ key: 'dais', at: [256, 256], size: [128, 128], rise: 48 }] },
            { id: 'room:crypt', outline: [[1088, 0], [1600, 0], [1600, 512], [1088, 512]], floor: -128, ceiling: 256 },
        ],
    } },
    'objects.yml': { tree: { format: 1, start: { room: 'room:hall' }, lifts: [{ id: 'lift:a', room: 'room:hall', at: [128, 640], size: [128, 128] }],
        plates: [{ id: 'plate:p', room: 'room:hall', at: [512, 128], size: [64, 64] }] } },
    'wiring.yml': { tree: { format: 0, variables: ['open_gate'], events: [
        { id: 'evt:a', preset: 'switch', source: 'plate:p', sets: { map_var: 'open_gate' } },
        { id: 'evt:b', preset: 'door', source: 'door:x', condition: { map_var: { name: 'open_gate', at_least: 1 } }, lua: 'if MapVar(open_gate) then end' },
        { id: 'evt:c', preset: 'text', source: 'door:y', text: 'open_gate' },
    ] } },
    'plan.yml': { tree: { format: 0,
        spaces: [{ id: 'space:hall', kind: 'room' }, { id: 'space:crypt', kind: 'room', size: 'S', at: [2000, 300], name: 'Crypt' }, { id: 'space:loose', kind: 'room' }],
        links: [{ id: 'link:1', from: 'space:hall', to: 'space:crypt', kind: 'door', condition: { qbit: 1 } }],
        goals: [{ id: 'goal:1', space: 'space:crypt', kind: 'kill', what: 'the abbot' }] } },
});

// A host that records what a tool sends, answering each gesture with the ids a core would give.
function fakeHost(over: Partial<ToolOptions> = {}, selection: string | null = null)
{
    const sent: Gesture[] = [];
    let serial = 0;
    const host: ToolHost = {
        files: () => files(),
        layout: () => null,
        options: () => ({ ...DEFAULT_OPTIONS, ...over }),
        selection: () => selection,
        select: () => undefined,
        edit: async (gesture) =>
        {
            sent.push(gesture);
            const first = gesture.ops[0] as Op & { to?: string };
            const made = first.op === 'name' ? [`rooms.yml#platform:hall_${++serial}`] : first.op === 'add' ? [`objects.yml#${String(first.to).replace(/s$/, '')}:made_${++serial}`] : [];
            return { ids_allocated: made, files: {} } as unknown as EditApplyResult;
        },
        hint: () => undefined,
        note: () => undefined,
        redraw: () => undefined,
        unitsPerPixel: () => 1,
        colour: () => '#888888',
    };
    return { host, sent };
}

const press = (extra: Partial<PointerEvent> = {}) => ({ button: 0, altKey: false, shiftKey: false, ...extra } as PointerEvent);
const settle = () => new Promise((done) => setTimeout(done, 0));

function gesture(name: ToolName, over: Partial<ToolOptions>, from: [number, number], to: [number, number], selection: string | null = null)
{
    const { host, sent } = fakeHost(over, selection);
    const tool = makeTool(host, name);
    tool.down(from, press());
    tool.move(to, press(), true);
    tool.up(to, press());
    return sent;
}

describe('the plan\'s bubbles', () =>
{
    it('stands a space on its room, at its `at`, or in a row under the map; finds one by its bubble', () =>
    {
        const places = spacePlaces(files(), null);
        expect(places.find((place) => place.id === 'space:hall')).toMatchObject({ room: 'room:hall', at: [512, 384] });
        expect(places.find((place) => place.id === 'space:crypt')).toMatchObject({ room: null, at: [2000, 300], size: [560, 560], goals: ['kill the abbot'] });
        expect(places.find((place) => place.id === 'space:loose')).toMatchObject({ placed: false });
        expect(spaceAt(places, [2010, 290], 16)?.id).toBe('space:crypt');
        // Inside a ghost's box.
        expect(spaceAt(places, [2200, 500], 16)?.id).toBe('space:crypt');
        expect(planLinks(files())).toEqual([{ id: 'link:1', from: 'space:hall', to: 'space:crypt', kind: 'door', locked: true }]);
    });

    it('Space makes a space where clicked; Plan link drags between two; Goal clicks one', async () =>
    {
        const { host, sent } = fakeHost({ spaceKind: 'corridor', spaceSize: 'S' });
        makeTool(host, 'space').down([3010, 1000], press());
        expect(sent[0].ops[0]).toEqual({ op: 'add', to: 'spaces', file: 'plan.yml', value: { kind: 'corridor', size: 'S', at: [3008, 1024] } });
        const link = gesture('planlink', { planLinkKind: 'stairs' }, [512, 384], [2000, 300]);
        expect(link[0].ops[0]).toEqual({ op: 'add', to: 'links', file: 'plan.yml', value: { from: 'space:hall', to: 'space:crypt', kind: 'stairs' } });
        const goal = fakeHost({ goalKind: 'take', goalWhat: 'the ring' });
        makeTool(goal.host, 'goal').down([2000, 300], press());
        expect(goal.sent[0].ops[0]).toEqual({ op: 'add', to: 'goals', file: 'plan.yml', value: { space: 'space:crypt', kind: 'take', what: 'the ring' } });
        // A bubble without a room moves by a drag.
        const move = gesture('space', {}, [2000, 300], [2100, 364]);
        expect(move[0].ops[0]).toEqual({ op: 'patch', id: 'space:crypt', file: 'plan.yml', patch: [{ op: 'add', path: '/at', value: [2112, 352] }] });
        await settle();
    });
});

describe('blocks that move or mark a floor', () =>
{
    it('Lift, Mover and Plate make their objects from a box in a room', () =>
    {
        expect(gesture('lift', { liftTravel: 192 }, [64, 64], [192, 192])[0].ops[0]).toEqual({ op: 'add', to: 'lifts', file: 'objects.yml',
            value: { room: 'room:hall', at: [128, 128], size: [128, 128], travel: 192 } });
        expect(gesture('mover', { moverHeight: 32, moverTravelZ: 96 }, [64, 64], [192, 192])[0].ops[0]).toEqual({ op: 'add', to: 'movers', file: 'objects.yml',
            value: { room: 'room:hall', at: [128, 128], size: [128, 128], height: 32, travel: [0, 0, 96] } });
        expect(gesture('plate', {}, [64, 64], [192, 192])[0].ops[0]).toEqual({ op: 'add', to: 'plates', file: 'objects.yml',
            value: { room: 'room:hall', at: [128, 128], size: [128, 128] } });
        const blocks = objectBlocks(files(), null);
        expect(blocks.map((block) => block.id)).toEqual(['lift:a', 'plate:p']);
    });

    it('Floor names a level without an id first (op name), then makes it lava', async () =>
    {
        const { host, sent } = fakeHost({ floorKind: 'water' });
        makeTool(host, 'floor').down([800, 600], press());
        await settle();
        await settle();
        expect(sent[0].ops[0]).toEqual({ op: 'name', id: 'room:hall', file: 'rooms.yml', path: '/levels/gallery' });
        expect(sent[1].ops[0]).toEqual({ op: 'add', to: 'floors', file: 'objects.yml', value: { of: 'platform:hall_1', kind: 'water' } });
        expect(sent[0].mergeKey).toBe(sent[1].mergeKey);
        // A room's own floor needs no name.
        const room = fakeHost({ floorKind: 'lava' });
        makeTool(room.host, 'floor').down([1300, 300], press());
        expect(room.sent[0].ops[0]).toEqual({ op: 'add', to: 'floors', file: 'objects.yml', value: { of: 'room:crypt', kind: 'lava' } });
    });

    it('Ladder stands against the edge of what it climbs, as high as the climb, facing it', () =>
    {
        const sent = gesture('ladder', {}, [800, 300], [800, 520]);
        expect(sent[0].ops[0]).toEqual({ op: 'add', to: 'ladders', file: 'objects.yml', value: { room: 'room:hall', at: [800, 446], facing: 90, height: 64 } });
        expect(floorHeightAt(files(), null, [800, 600])).toBe(64);
        expect(floorHeightAt(files(), null, [256, 256])).toBe(48);
        // Nothing higher: refused.
        expect(gesture('ladder', {}, [100, 100], [300, 100])).toEqual([]);
    });

    it('a plate switch on a platform\'s top names the platform first; a lever goes on its nearest side', async () =>
    {
        const plate = fakeHost({ switchKind: 'plate' });
        const tool = makeTool(plate.host, 'switch');
        tool.move([256, 250], press(), false);
        tool.down([256, 250], press());
        await settle();
        await settle();
        expect(plate.sent[0].ops[0]).toEqual({ op: 'name', id: 'room:hall', file: 'rooms.yml', path: '/platforms/dais' });
        expect(plate.sent[1].ops[0]).toEqual({ op: 'add', to: 'switches', file: 'objects.yml',
            value: { room: 'room:hall', block: 'platform:hall_1', kind: 'plate', side: 'top', at: [256, 256], size: [32, 32] } });
        const lever = fakeHost({ switchKind: 'lever' });
        const leverTool = makeTool(lever.host, 'switch');
        leverTool.move([310, 256], press(), false);
        leverTool.down([310, 256], press());
        await settle();
        await settle();
        expect((lever.sent[1].ops[0] as { value: JsonObject }).value).toMatchObject({ block: 'platform:hall_1', kind: 'lever', side: 'e' });
    });
});

describe('the per-word tools of a room', () =>
{
    it('Height points adds a point at the options\' height above the floor or ceiling, snapped onto a wall near one', () =>
    {
        const add = fakeHost({ pointsOn: 'floor', pointHeight: -16 });
        makeTool(add.host, 'points').down([500, 300], press());
        expect(add.sent[0].ops[0]).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/floor_points', value: [[496, 304, -16]] }] });
        const ceiling = fakeHost({ pointsOn: 'ceiling', pointHeight: 64 });
        makeTool(ceiling.host, 'points').down([1020, 384], press());
        // On the wall: it snaps onto the wall.
        expect(ceiling.sent[0].ops[0]).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/ceiling_points', value: [[1024, 384, 576]] }] });
    });

    it('Flight climbs from a lower floor to a higher one; Parapet and Beam are lines; Ceiling level a box', () =>
    {
        expect(gesture('flight', {}, [700, 300], [700, 470])[0].ops[0]).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml',
            patch: [{ op: 'add', path: '/flights', value: [{ from: [704, 304], to: [704, 464] }] }] });
        expect(gesture('flight', {}, [700, 470], [700, 300])).toEqual([]);
        const parapet = fakeHost({ parapetHeight: 40 });
        const line = makeTool(parapet.host, 'parapet');
        line.down([640, 640], press());
        line.down([960, 640], press());
        line.key({ code: 'Enter' } as KeyboardEvent);
        expect(parapet.sent[0].ops[0]).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/parapets', value: [{ path: [[640, 640], [960, 640]], height: 40 }] }] });
        const beam = fakeHost({ beamWidth: 32, beamDepth: 32, beamBottom: 0 });
        const bar = makeTool(beam.host, 'beam');
        bar.down([64, 384], press());
        bar.down([960, 384], press());
        bar.key({ code: 'Enter' } as KeyboardEvent);
        expect((beam.sent[0].ops[0] as { patch: { value: JsonObject[] }[] }).patch[0].value[0]).toEqual({ path: [[64, 384], [960, 384]], width: 32, depth: 32, bottom: 448 });
        const ceiling = gesture('ceiling', { ceilingRise: 128 }, [128, 384], [384, 640], 'room:hall');
        expect(ceiling[0].ops[0]).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml',
            patch: [{ op: 'add', path: '/ceiling_levels', value: [{ outline: [[128, 384], [384, 384], [384, 640], [128, 640]], ceiling: 640 }] }] });
    });
});

describe('the map\'s variables', () =>
{
    it('a rename changes the list and every event that names the variable, in one transaction', () =>
    {
        const ops = renameVariableOps(files(), 'open_gate', 'gate_open');
        expect(ops[0]).toEqual({ op: 'patch', file: 'wiring.yml', patch: [{ op: 'test', path: '/variables/0', value: 'open_gate' }, { op: 'replace', path: '/variables/0', value: 'gate_open' }] });
        expect(ops.slice(1)).toEqual([
            { op: 'replace', id: 'evt:a', file: 'wiring.yml', value: { preset: 'switch', source: 'plate:p', sets: { map_var: 'gate_open' } } },
            { op: 'replace', id: 'evt:b', file: 'wiring.yml', value: { preset: 'door', source: 'door:x', condition: { map_var: { name: 'gate_open', at_least: 1 } }, lua: 'if MapVar(gate_open) then end' } },
        ]);
        expect(variablesOf(files())).toEqual(['open_gate']);
        expect(addVariableOp(files(), 'second')).toEqual({ op: 'patch', file: 'wiring.yml', patch: [{ op: 'add', path: '/variables/-', value: 'second' }] });
    });
});

describe('placing in 3D and the Library\'s new kinds', () =>
{
    it('turns a pick on a wall into a point a step into the room, on a floor into its point', () =>
    {
        expect(planPointOfPick({ point: [1024, 300, 100], normal: [-1, 0, 0] }, 'switch')).toEqual([1018, 300]);
        expect(planPointOfPick({ point: [1024, 300, 100], normal: [-1, 0, 0] }, 'chest')).toEqual([960, 300]);
        expect(planPointOfPick({ point: [500, 300, 0], normal: [0, 0, 1] }, 'light')).toEqual([500, 300]);
    });

    it('drops a monster or an item by its number and a sound by its name where it lands', () =>
    {
        const monster = dropPlan(files(), null, { kind: 'monster', name: 'Goblin', number: 271 }, { where: 'plan', at: [300, 300], shift: false, alt: false, reach: 8 }, 144);
        expect(monster).toMatchObject({ kind: 'ops', ops: [{ op: 'add', to: 'monsters', file: 'objects.yml', value: { room: 'room:hall', at: [300, 300], monster: 271 } }] });
        const sound = dropPlan(files(), null, { kind: 'sound', name: 'waterdrip' }, { where: '3d', owner: 'room:crypt/walls/1', point: [1600, 200, 0], normal: [-1, 0, 0], alt: false }, 144);
        expect(sound).toMatchObject({ kind: 'ops', ops: [{ op: 'add', to: 'sounds', value: { room: 'room:crypt', at: [1552, 200], sound: 'waterdrip', radius: 1024 } }] });
    });
});

describe('the file inspector', () =>
{
    it('writes a file\'s own words by file patches, and adds an object with an id by op add', () =>
    {
        const target = { id: '', file: 'plan.yml', pointer: '', value: { format: 0, keys: [{ id: 'key:abbot', how: 'chest' }] } as JsonObject };
        expect(fieldOp(target, ['purpose'], 'why')).toEqual({ op: 'patch', file: 'plan.yml', patch: [{ op: 'add', path: '/purpose', value: 'why' }] });
        expect(addRowOp(target, ['keys'], { id: '', how: 'a lever' })).toEqual({ op: 'add', to: 'keys', file: 'plan.yml', value: { how: 'a lever' } });
        expect(rowOp(target, ['keys'], 0, 'remove')).toEqual({ op: 'patch', file: 'plan.yml', patch: [{ op: 'test', path: '/keys/key:abbot', value: { id: 'key:abbot', how: 'chest' } },
            { op: 'remove', path: '/keys/key:abbot' }] });
        // A row of a list of objects with ids is named by its id (as the core names it), with no test.
        expect(fieldOp(target, ['keys', 0, 'how'], 'a ring')).toEqual({ op: 'patch', file: 'plan.yml', patch: [{ op: 'replace', path: '/keys/key:abbot/how', value: 'a ring' }] });
    });
});
