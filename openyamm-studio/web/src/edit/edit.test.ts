import { describe, expect, it } from 'vitest';
import type { FileTrees, HistoryEntry, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import { KEYED_LISTS, keysOf, pointerOf, resolvePointer, subAddresses } from './keys.ts';
import {
    GHOST, LocalOpError, allocatedId, appendItemOp, appendedKey, applyOpsLocally, doorOp, duplicateOps, heightStepOp, idsOf,
    insertPointOp, movePointsOp, removeOps,
} from './ops.ts';
import { towardEdge, box, counterClockwise, nearCorner, nearEdge, openingPlace, selfCrossing, signedArea, slopeToward, snapPoint, wallPairs } from './geometry.ts';
import { entryTags, openNotice, redoTarget, undoTarget } from './history.ts';
import { nextGrid, stageCounts } from './stages.ts';
import { besideOffset, blocksOf, editShape, roomAt, roomShapes } from './tools.ts';
import { loadSchemas } from '../lint/load.ts';

const files = (): FileTrees => ({
    'rooms.yml': { tree: {
        format: 1,
        rooms: [
            { id: 'room:hall', outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 0, ceiling: 512,
                pillars: [{ at: [256, 256], size: [64, 64] }, { key: 'big', at: [512, 256], size: [128, 128] }] },
            { id: 'room:side', outline: [[1088, 128], [1600, 128], [1600, 640], [1088, 640]], floor: 0, ceiling: 384 },
        ],
        openings: [{ id: 'open:hall_side', from: 'room:hall', to: 'room:side', width: 192, height: 256 }],
    } },
    'objects.yml': { tree: { format: 1, start: { room: 'room:hall' }, doors: [{ id: 'door:gate', opening: 'open:hall_side' }] } },
});

describe('keys', () =>
{
    it('reads missing keys as prefix and position, the next free number on a clash', () =>
    {
        expect(keysOf([{}, { key: 'pillar1' }, {}], 'pillars')).toEqual(['pillar2', 'pillar1', 'pillar3']);
        expect(keysOf([{ wall: 'north' }, { wall: 3 }], 'walls')).toEqual(['north', '3']);
    });

    it('turns form paths into pointers: keys in keyed lists, positions in plain ones', () =>
    {
        const room = files()['rooms.yml']!.tree.rooms as JsonObject[];
        expect(pointerOf(room[0], ['pillars', 1, 'size', 0])).toEqual({ pointer: '/pillars/big/size/0', positional: true });
        expect(pointerOf(room[0], ['pillars', 0, 'at'])).toEqual({ pointer: '/pillars/pillar1/at', positional: false });
        expect(pointerOf(room[0], ['outline', 2])).toEqual({ pointer: '/outline/2', positional: true });
        expect(resolvePointer(room[0], '/pillars/big/size')).toEqual([128, 128]);
        expect(subAddresses('room:hall', room[0]).map((entry) => entry.address)).toEqual(['room:hall/pillars/pillar1', 'room:hall/pillars/big']);
    });

    it('names the same keyed lists and prefixes as the schemas', () =>
    {
        const registry = loadSchemas();
        const found: Record<string, { field: string; prefix?: string }> = {};
        const visit = (node: unknown, name: string) =>
        {
            if (!node || typeof node !== 'object')
            {
                return;
            }
            const schema = node as Record<string, unknown>;
            if (schema.type === 'array' && typeof schema['x-key'] === 'string' && schema['x-key'] !== 'id' && schema['x-key'] !== '#')
            {
                found[name] = { field: schema['x-key'] as string, ...(schema['x-key-prefix'] ? { prefix: schema['x-key-prefix'] as string } : {}) };
            }
            for (const [key, value] of Object.entries(schema))
            {
                visit(value, key === 'properties' || key === 'items' ? name : key);
            }
        };
        for (const file of ['rooms.schema.json', 'objects.schema.json'])
        {
            visit(registry.files[file], '');
        }
        expect(found).toEqual(KEYED_LISTS);
    });
});

describe('local operations', () =>
{
    it('applies a patch of a plain list with its test, and refuses a changed point', () =>
    {
        const before = files();
        const op = movePointsOp('room:hall', '/outline', [{ index: 2, from: [1024, 768], to: [1088, 832] }]);
        const after = applyOpsLocally(before, [op]);
        expect((after['rooms.yml']!.tree.rooms as JsonObject[])[0].outline).toEqual([[0, 0], [1024, 0], [1088, 832], [0, 768]]);
        // The input is never changed.
        expect((before['rooms.yml']!.tree.rooms as JsonObject[])[0].outline).toEqual([[0, 0], [1024, 0], [1024, 768], [0, 768]]);
        expect(() => applyOpsLocally(after, [op])).toThrow(LocalOpError);
    });

    it('inserts a corner after an edge', () =>
    {
        const before = files();
        const points = (before['rooms.yml']!.tree.rooms as JsonObject[])[0].outline as [number, number][];
        const after = applyOpsLocally(before, [insertPointOp('room:hall', '/outline', points, 1, [1024, 384])]);
        expect((after['rooms.yml']!.tree.rooms as JsonObject[])[0].outline).toEqual([[0, 0], [1024, 0], [1024, 384], [1024, 768], [0, 768]]);
    });

    it('appends to a keyed list, making the list when there is none', () =>
    {
        const before = files();
        const [hall, side] = before['rooms.yml']!.tree.rooms as JsonObject[];
        const first = appendItemOp('room:hall', hall, 'pillars', { at: [700, 500], size: [64, 64] });
        const second = appendItemOp('room:side', side, 'levels', { outline: [[1152, 192], [1280, 192], [1280, 320]], floor: 64 });
        expect(first).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/pillars/-', value: { at: [700, 500], size: [64, 64] } }] });
        expect(second.op === 'patch' && second.patch[0].path).toBe('/levels');
        const after = applyOpsLocally(before, [first, second]);
        const rooms = after['rooms.yml']!.tree.rooms as JsonObject[];
        expect((rooms[0].pillars as JsonObject[]).length).toBe(3);
        expect(appendedKey(rooms[0], 'pillars')).toBe('pillar3');
        expect((rooms[1].levels as JsonObject[]).length).toBe(1);
    });

    it('keeps an add without an id as a ghost and never invents an id', () =>
    {
        const after = applyOpsLocally(files(), [{ op: 'add', to: 'rooms', value: { outline: [[0, 0], [1, 0], [1, 1]], floor: 0, ceiling: 1 } }]);
        const added = (after['rooms.yml']!.tree.rooms as JsonObject[])[2];
        expect(added.id).toBeUndefined();
        expect(added[GHOST]).toBe(true);
        expect(idsOf(after).filter((place) => place.list === 'rooms').map((place) => place.id)).toEqual(['room:hall', 'room:side']);
    });

    it('removes a room with its openings and their doors in one transaction', () =>
    {
        const trees = files();
        const ops = removeOps(trees, idsOf(trees), 'room:side', 'rooms.yml');
        expect(ops).toEqual([
            { op: 'remove', id: 'room:side', file: 'rooms.yml' },
            { op: 'remove', id: 'open:hall_side', file: 'rooms.yml' },
            { op: 'remove', id: 'door:gate', file: 'objects.yml' },
        ]);
        expect(removeOps(trees, idsOf(trees), 'room:hall/pillars/big')).toEqual([
            { op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'remove', path: '/pillars/big' }] }]);
        const after = applyOpsLocally(trees, ops);
        expect(idsOf(after).map((place) => place.id)).toEqual(['room:hall']);
    });

    it('duplicates beside the original without id or key', () =>
    {
        const trees = files();
        const [room] = duplicateOps(trees, idsOf(trees), 'room:side', [0, -704]);
        expect(room).toEqual({ op: 'add', to: 'rooms', file: 'rooms.yml', value: { outline: [[1088, -576], [1600, -576], [1600, -64], [1088, -64]], floor: 0, ceiling: 384 } });
        const [pillar] = duplicateOps(trees, idsOf(trees), 'room:hall/pillars/big', [128, 0]);
        expect(pillar).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/pillars/-', value: { at: [640, 256], size: [128, 128] } }] });
    });

    it('moves a floor by a step but never through the ceiling', () =>
    {
        const room = { id: 'room:a', floor: 0, ceiling: 128 };
        expect(heightStepOp(room, 'floor', 64)).toEqual({ op: 'set', id: 'room:a', file: 'rooms.yml', fields: { floor: 64 } });
        expect(heightStepOp(room, 'floor', 128)).toBeNull();
        expect(heightStepOp(room, 'ceiling', -128)).toBeNull();
    });

    it('reads the allocated id and fills a door from its preset', () =>
    {
        expect(allocatedId(['rooms.yml#room:room_3'], 'rooms')).toBe('room:room_3');
        expect(doorOp('open:a_b', 'portcullis')).toEqual({ op: 'add', to: 'doors', file: 'objects.yml', value: { opening: 'open:a_b', kind: 'slide_up' } });
    });

    it('applies keyed moves (reorder) as the core does', () =>
    {
        const after = applyOpsLocally(files(), [{ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'move', from: '/pillars/big', path: '/pillars/pillar1' }] }]);
        const pillars = (after['rooms.yml']!.tree.rooms as JsonObject[])[0].pillars as JsonObject[];
        expect(pillars.map((pillar) => pillar.key ?? '-')).toEqual(['big', '-']);
    });
});

describe('edit geometry', () =>
{
    it('snaps to corners, then 45-degree steps, then walls, then the grid; Shift is free', () =>
    {
        const outlines = [[[0, 0], [512, 0], [512, 512], [0, 512]]];
        expect(snapPoint([520, 505], { grid: 64, outlines, reach: 16 })).toEqual({ point: [512, 512], to: 'corner' });
        expect(snapPoint([700, 30], { grid: 64, previous: [576, 0], reach: 16 })).toEqual({ point: [704, 0], to: 'angle' });
        expect(snapPoint([700, 120], { grid: 64, previous: [576, 0], reach: 16 }).point).toEqual([704, 128]);
        expect(snapPoint([505, 300], { grid: 64, outlines, reach: 16 })).toEqual({ point: [512, 320], to: 'wall' });
        expect(snapPoint([700, 300], { grid: 64, outlines, reach: 16 })).toEqual({ point: [704, 320], to: 'grid' });
        expect(snapPoint([700.4, 301], { grid: 64, outlines, reach: 16, free: true })).toEqual({ point: [700, 301], to: 'free' });
    });

    it('winds outlines counter-clockwise and finds crossings', () =>
    {
        const clockwise: [number, number][] = [[0, 0], [0, 100], [100, 100], [100, 0]];
        expect(signedArea(clockwise)).toBeLessThan(0);
        expect(signedArea(counterClockwise(clockwise))).toBeGreaterThan(0);
        expect(selfCrossing([[0, 0], [100, 100], [100, 0], [0, 100]])).toBe(true);
        expect(selfCrossing(counterClockwise(clockwise))).toBe(false);
        expect(box([100, 50], [0, 0])).toEqual({ outline: [[0, 0], [100, 0], [100, 50], [0, 50]], at: [50, 25], size: [100, 50] });
    });

    it('places an opening across the wall two rooms share, as the core measures it', () =>
    {
        const hall = [[0, 0], [1024, 0], [1024, 768], [0, 768]];
        const side = [[1088, 128], [1600, 128], [1600, 640], [1088, 640]];
        expect(wallPairs(hall, side)).toEqual([{ fromEdge: 1, toEdge: 3, gap: 64, low: 128, high: 640 }]);
        const place = openingPlace(hall, side, [1000, 300], [1120, 300], 192);
        expect('reason' in place).toBe(false);
        if (!('reason' in place))
        {
            // The middle of the drag (y 300) is 172 along a shared stretch of 512 that starts at y 128.
            expect(place.along).toBeCloseTo((300 - 128) / 512, 3);
            expect(place.width).toBe(192);
            expect(place.a).toEqual([1024, 204]);
            expect(place.b).toEqual([1024, 396]);
            expect(place.from_wall).toBeUndefined();
        }
        const far = [[3000, 0], [3500, 0], [3500, 500], [3000, 500]];
        expect('reason' in openingPlace(hall, far, [900, 100], [3100, 100], 192)).toBe(true);
    });

    it('names the wall a slope climbs toward', () =>
    {
        const room = [[0, 0], [512, 0], [512, 1024], [0, 1024]];
        expect(slopeToward(room, [256, 100], [256, 900])).toBe('north');
        expect(slopeToward(room, [400, 500], [100, 520])).toBe('west');
        const triangle = [[0, 0], [512, 0], [0, 512]];
        expect(slopeToward(triangle, [100, 100], [300, 300])).toBe(1);
    });

    it('finds handles near the pointer', () =>
    {
        const points = [[0, 0], [100, 0], [100, 100]];
        expect(nearCorner(points, [97, 4], 8)).toBe(1);
        expect(nearCorner(points, [50, 50], 8)).toBe(-1);
        expect(nearEdge(points, [50, 3], 8, true)).toEqual({ edge: 0, point: [50, 0] });
        expect(nearEdge(points, [50, 48], 8, false)).toBeNull();
        expect(nearEdge(points, [50, 48], 8, true)?.edge).toBe(2);
    });
});

const entry = (sequence: number, author: string, extra: Partial<HistoryEntry> = {}): HistoryEntry => ({
    sequence, author, kind: 'transaction', revision_before: '', revision_after: '', changes: [], undone: false, ...extra,
});

describe('tools', () =>
{
    it('reads the wall a slope names, and puts a copy beside the original', () =>
    {
        const room = [[0, 0], [512, 0], [512, 1024], [0, 1024]];
        expect(towardEdge(room, 'north')).toBe(2);
        expect(towardEdge(room, 1)).toBe(1);
        expect(towardEdge(room, 9)).toBe(-1);
        expect(besideOffset(files(), 'room:side', 64)).toEqual([512 + 128, 0]);
        expect(besideOffset(files(), 'room:hall/pillars/big', 64)).toEqual([128 + 64, 0]);
    });

    it('finds the room under a point and the selection\'s handles', () =>
    {
        const shapes = roomShapes(files(), null);
        expect(roomAt(shapes, [1200, 300])?.id).toBe('room:side');
        expect(roomAt(shapes, [1050, 300])).toBeNull();
        expect(editShape(files(), 'room:hall')?.kind).toBe('polygon');
        expect(editShape(files(), 'room:hall/pillars/big')).toMatchObject({ kind: 'box', base: '/pillars/big', at: [512, 256], size: [128, 128] });
        expect(blocksOf((files()['rooms.yml']!.tree.rooms as JsonObject[])[0]).map((block) => block.address)).toEqual(['room:hall/pillars/pillar1', 'room:hall/pillars/big']);
    });
});

describe('undo positions', () =>
{
    it('undoes only the person\'s own latest change, never an agent\'s', () =>
    {
        const log = [entry(1, 'user', { label: 'room' }), entry(2, 'agent:gw'), entry(3, 'outside', { kind: 'outside' })];
        expect(undoTarget(log, 'user')?.sequence).toBe(1);
        expect(undoTarget(log, 'agent:gw')?.sequence).toBe(2);
        expect(redoTarget(log, 'user')).toBeNull();
    });

    it('walks back through undos and forward through redos until a new change ends the chain', () =>
    {
        let log = [entry(1, 'user'), entry(2, 'user')];
        // Undo #2, then #1.
        log = [entry(1, 'user'), entry(2, 'user', { undone: true }), entry(3, 'user', { kind: 'revert', revert_kind: 'undo', reverts: 2 })];
        expect(undoTarget(log, 'user')?.sequence).toBe(1);
        expect(redoTarget(log, 'user')?.sequence).toBe(3);
        log = [entry(1, 'user', { undone: true }), entry(2, 'user', { undone: true }), entry(3, 'user', { kind: 'revert', revert_kind: 'undo', reverts: 2 }),
            entry(4, 'agent:gw'), entry(5, 'user', { kind: 'revert', revert_kind: 'undo', reverts: 1 })];
        expect(undoTarget(log, 'user')).toBeNull();
        expect(redoTarget(log, 'user')?.sequence).toBe(5);
        // Redo of #5 (the undo of #1): #3 is next to redo.
        const redone = [...log.slice(0, 4), { ...log[4], undone: true }, entry(6, 'user', { kind: 'revert', revert_kind: 'redo', reverts: 5 })];
        redone[0] = { ...redone[0], undone: false };
        expect(redoTarget(redone, 'user')?.sequence).toBe(3);
        // A new change ends the redo chain.
        expect(redoTarget([...redone, entry(7, 'user')], 'user')).toBeNull();
    });

    it('shows an outside rewrite\'s notice until it is reverted or dismissed, and tags entries', () =>
    {
        const log = [entry(1, 'user'), entry(2, 'outside', { kind: 'outside', notice: ['rooms.yml rewritten: room:hall a person changed last'] })];
        expect(openNotice(log, new Set())?.sequence).toBe(2);
        expect(openNotice(log, new Set([2]))).toBeNull();
        expect(openNotice([log[0], { ...log[1], undone: true }], new Set())).toBeNull();
        expect(entryTags(entry(4, 'user', { kind: 'revert', revert_kind: 'undo', reverts: 2, merged: 3 }))).toEqual(['undo of #2', '3 edits']);
    });
});

describe('stages', () =>
{
    it('counts what each stage has open', () =>
    {
        const trees = files();
        trees['plan.yml'] = { tree: { spaces: [{ id: 'room:hall' }, { id: 'room:crypt' }] } };
        const counts = stageCounts(trees, [{ severity: 'error', code: 'x', file: 'rooms.yml', path: '', message: '' }]);
        expect(counts[2]).toBe('1/2');
        expect(counts[3]).toBe('1/1');
        expect(counts[7]).toBe('1');
    });

    it('steps the grid through its sizes', () =>
    {
        expect(nextGrid(64, 1)).toBe(128);
        expect(nextGrid(8, -1)).toBe(8);
        expect(nextGrid(512, 1)).toBe(512);
    });
});
