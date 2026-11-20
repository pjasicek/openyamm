import { describe, expect, it } from 'vitest';
import type { JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import { addRowOp, fieldOp, renameKeyOp, replaceOp, rowOp } from './formops.ts';
import type { Target } from './formops.ts';
import { applyOpsLocally } from './ops.ts';

const hall: JsonObject = { id: 'room:hall', outline: [[0, 0], [512, 0], [512, 512]], floor: 0, ceiling: 384,
    pillars: [{ at: [100, 100], size: [64, 64] }, { key: 'big', at: [300, 300], size: [128, 128] }] };
const room: Target = { id: 'room:hall', file: 'rooms.yml', pointer: '', value: hall };
const pillar: Target = { id: 'room:hall', file: 'rooms.yml', pointer: '/pillars/big', value: (hall.pillars as JsonObject[])[1] };

describe('inspector operations', () =>
{
    it('sets a top-level field, and removes it with null', () =>
    {
        expect(fieldOp(room, ['ceiling'], 512)).toEqual({ op: 'set', id: 'room:hall', file: 'rooms.yml', fields: { ceiling: 512 } });
        expect(fieldOp(room, ['ambient'], undefined)).toEqual({ op: 'set', id: 'room:hall', file: 'rooms.yml', fields: { ambient: null } });
    });

    it('patches deeper fields by key, plain lists by position with a test', () =>
    {
        expect(fieldOp(room, ['pillars', 1, 'size', 0], 192)).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [
            { op: 'test', path: '/pillars/big/size/0', value: 128 }, { op: 'replace', path: '/pillars/big/size/0', value: 192 }] });
        expect(fieldOp(pillar, ['facing'], 45)).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/pillars/big/facing', value: 45 }] });
        expect(fieldOp(pillar, ['at'], [310, 300])).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'replace', path: '/pillars/big/at', value: [310, 300] }] });
    });

    it('adds, removes, duplicates and moves keyed rows by key', () =>
    {
        expect(addRowOp(room, ['levels'], { outline: [], floor: 0 })).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/levels', value: [{ outline: [], floor: 0 }] }] });
        expect(addRowOp(room, ['pillars'], { at: [0, 0] }).op === 'patch' && (addRowOp(room, ['pillars'], { at: [0, 0] }) as { patch: { path: string }[] }).patch[0].path).toBe('/pillars/-');
        expect(rowOp(room, ['pillars'], 0, 'remove')).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'remove', path: '/pillars/pillar1' }] });
        expect(rowOp(room, ['pillars'], 1, 'duplicate')).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'add', path: '/pillars/-', value: { at: [300, 300], size: [128, 128] } }] });
        expect(rowOp(room, ['pillars'], 1, 'up')).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'move', from: '/pillars/big', path: '/pillars/pillar1' }] });
        expect(rowOp(room, ['pillars'], 0, 'down')).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'move', from: '/pillars/pillar1', path: '/pillars/-' }] });
        expect(rowOp(room, ['pillars'], 0, 'up')).toBeNull();
        expect(renameKeyOp(room, ['pillars'], 0, 'west')).toEqual({ op: 'rename', id: 'room:hall', file: 'rooms.yml', path: '/pillars/pillar1', to: 'west' });
    });

    it('moves plain rows by position with a test, as the client applies them', () =>
    {
        const op = rowOp(room, ['outline'], 0, 'down')!;
        expect(op).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'test', path: '/outline/0', value: [0, 0] }, { op: 'move', from: '/outline/0', path: '/outline/1' }] });
        const files = applyOpsLocally({ 'rooms.yml': { tree: { rooms: [hall] } } }, [op]);
        expect(((files['rooms.yml']!.tree.rooms as JsonObject[])[0]).outline).toEqual([[512, 0], [0, 0], [512, 512]]);
    });

    it('replaces the whole object from the Source tab, keeping the id', () =>
    {
        expect(replaceOp(room, { id: 'room:hall', floor: 0, ceiling: 300, outline: [] })).toEqual({ op: 'replace', id: 'room:hall', file: 'rooms.yml', value: { floor: 0, ceiling: 300, outline: [] } });
        expect(replaceOp(pillar, { at: [1, 1] })).toEqual({ op: 'patch', id: 'room:hall', file: 'rooms.yml', patch: [{ op: 'replace', path: '/pillars/big', value: { at: [1, 1] } }] });
    });
});
