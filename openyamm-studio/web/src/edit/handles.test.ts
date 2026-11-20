// S5b2 (carried from S5b1): the Select tool's handles on the blocks of objects.yml (lift, mover, plate, ladder) and on a
// room's lines (parapet, beam, flight), driven as the plan drives them; each gesture one keyed patch, applied locally
// to check what it writes; and what the plan picks under a point.
import { describe, expect, it } from 'vitest';
import type { EditApplyResult, FileTrees, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import type { Gesture } from './session.ts';
import type { ToolHost } from './toolbase.ts';
import { DEFAULT_OPTIONS } from './stages.ts';
import type { ToolOptions } from './stages.ts';
import { editShape, makeTool } from './tools.ts';
import { applyOpsLocally } from './ops.ts';
import { ceilingLevelAt, degreesTo, roomLineAt, shapeGestureOp } from './handles.ts';

const files = (): FileTrees => ({
    'rooms.yml': { tree: {
        format: 1,
        rooms: [
            { id: 'room:hall', outline: [[0, 0], [1024, 0], [1024, 768], [0, 768]], floor: 0, ceiling: 512,
                levels: [{ key: 'gallery', outline: [[640, 448], [960, 448], [960, 704], [640, 704]], floor: 64 }],
                flights: [{ key: 'flight1', from: [800, 300], to: [800, 448] }],
                parapets: [{ key: 'parapet1', path: [[640, 448], [960, 448]], height: 40 }],
                beams: [{ key: 'beam1', path: [[64, 128], [960, 128]], width: 32, depth: 32, bottom: 448 }],
                ceiling_levels: [{ key: 'vault', outline: [[128, 256], [384, 256], [384, 512], [128, 512]], ceiling: 640 }] },
        ],
    } },
    'objects.yml': { tree: { format: 1, start: { room: 'room:hall' },
        lifts: [{ id: 'lift:a', room: 'room:hall', at: [128, 640], size: [128, 128], travel: 256 }],
        movers: [{ id: 'mover:m', room: 'room:hall', outline: [[448, 512], [576, 512], [576, 640], [448, 640]], height: 32, travel: [0, 0, 128] }],
        plates: [{ id: 'plate:p', room: 'room:hall', offset: [0, -256], size: [64, 64] }],
        ladders: [{ id: 'ladder:l', room: 'room:hall', at: [600, 560, 0], facing: 90, height: 64 }] } },
});

function fakeHost(selection: string, over: Partial<ToolOptions> = {})
{
    const sent: Gesture[] = [];
    const host: ToolHost = {
        files: () => files(),
        layout: () => null,
        options: () => ({ ...DEFAULT_OPTIONS, grid: 32, ...over }),
        selection: () => selection,
        select: () => undefined,
        edit: async (gesture) =>
        {
            sent.push(gesture);
            return { ids_allocated: [], files: {} } as unknown as EditApplyResult;
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

// A drag with the Select tool on the selection; the gesture it sends, and the files after it (applied locally).
function drag(selection: string, from: [number, number], to: [number, number], over: Partial<ToolOptions> = {})
{
    const { host, sent } = fakeHost(selection, over);
    const tool = makeTool(host, 'select');
    const took = tool.down(from, press());
    tool.move(to, press(), true);
    tool.up(to, press());
    const after = sent.length > 0 ? applyOpsLocally(files(), sent[0].ops) : null;
    return { took, sent, after, passed: tool.passClick?.() ?? false };
}

const objectOf = (tree: FileTrees | null, list: string, id: string) =>
    ((tree?.['objects.yml']?.tree[list] as JsonObject[] | undefined) ?? []).find((entry) => entry.id === id);
const hallOf = (tree: FileTrees | null) => ((tree?.['rooms.yml']?.tree.rooms as JsonObject[] | undefined) ?? [])[0];

describe('handles on the blocks of objects.yml', () =>
{
    it('a lift moves by a drag inside it and resizes by a corner, each one patch of objects.yml', () =>
    {
        const moved = drag('lift:a', [128, 640], [192, 608]);
        expect(moved.took).toBe(true);
        expect(moved.sent).toHaveLength(1);
        expect(moved.sent[0].ops[0]).toMatchObject({ op: 'patch', id: 'lift:a', file: 'objects.yml' });
        expect(moved.sent[0].mergeKey).toBe('drag lift:a move');
        expect(objectOf(moved.after, 'lifts', 'lift:a')).toMatchObject({ at: [192, 608], size: [128, 128] });
        // The north-east corner (64, 576 + 128) dragged out: the box grows from its far corner.
        const sized = drag('lift:a', [192, 704], [256, 768]);
        expect(objectOf(sized.after, 'lifts', 'lift:a')).toMatchObject({ at: [160, 672], size: [192, 192] });
    });

    it('a mover\'s outline moves whole, its corner and side by their handles', () =>
    {
        const moved = drag('mover:m', [512, 576], [576, 576]);
        expect(objectOf(moved.after, 'movers', 'mover:m')?.outline).toEqual([[512, 512], [640, 512], [640, 640], [512, 640]]);
        const corner = drag('mover:m', [576, 640], [608, 672]);
        expect(objectOf(corner.after, 'movers', 'mover:m')?.outline).toEqual([[448, 512], [576, 512], [608, 672], [448, 640]]);
    });

    it('a plate placed by offset keeps its offset when moved', () =>
    {
        // The hall's middle is (512, 384): the plate stands at (512, 128).
        const shape = editShape(files(), 'plate:p');
        expect(shape).toMatchObject({ kind: 'box', at: [512, 128], file: 'objects.yml' });
        const moved = drag('plate:p', [512, 128], [576, 160]);
        expect(objectOf(moved.after, 'plates', 'plate:p')).toMatchObject({ offset: [64, -224], size: [64, 64] });
        expect(objectOf(moved.after, 'plates', 'plate:p')?.at).toBeUndefined();
    });

    it('a ladder moves by its foot (keeping its height) and turns by its facing handle', () =>
    {
        const moved = drag('ladder:l', [600, 560], [640, 592]);
        // Moved by whole grid steps (32), as blocks move: its place against a wall's edge is kept.
        expect(objectOf(moved.after, 'ladders', 'ladder:l')?.at).toEqual([632, 592, 0]);
        // The facing handle stands 34 pixels along its facing (90: north, +y).
        const turned = drag('ladder:l', [600, 594], [640, 560]);
        expect(objectOf(turned.after, 'ladders', 'ladder:l')?.facing).toBe(0);
        expect(turned.sent[0].label).toBe('turn ladder:l');
        expect(degreesTo([0, 0], [-1, -1])).toBe(225);
    });
});

describe('handles on a room\'s lines and parts', () =>
{
    it('a beam\'s and a parapet\'s points move; a beam moves whole by its line', () =>
    {
        const end = drag('room:hall/beams/beam1', [960, 128], [992, 160]);
        expect(end.sent[0].ops[0]).toMatchObject({ op: 'patch', id: 'room:hall', file: 'rooms.yml' });
        expect((hallOf(end.after).beams as JsonObject[])[0].path).toEqual([[64, 128], [992, 160]]);
        const whole = drag('room:hall/beams/beam1', [500, 128], [500, 192]);
        expect((hallOf(whole.after).beams as JsonObject[])[0].path).toEqual([[64, 192], [960, 192]]);
        const parapet = drag('room:hall/parapets/parapet1', [640, 448], [608, 448]);
        expect((hallOf(parapet.after).parapets as JsonObject[])[0].path).toEqual([[608, 448], [960, 448]]);
    });

    it('a flight\'s ends move one by one or both together', () =>
    {
        const top = drag('room:hall/flights/flight1', [800, 448], [800, 480]);
        expect((hallOf(top.after).flights as JsonObject[])[0]).toMatchObject({ from: [800, 300], to: [800, 480] });
        const patch = (top.sent[0].ops[0] as { patch: JsonObject[] }).patch;
        expect(patch.map((step) => step.path)).toEqual(['/flights/flight1/to', '/flights/flight1/to']);
        const both = drag('room:hall/flights/flight1', [800, 370], [864, 370]);
        expect((hallOf(both.after).flights as JsonObject[])[0]).toMatchObject({ from: [864, 300], to: [864, 448] });
    });

    it('a level and a ceiling level move whole; a press not moved picks through', () =>
    {
        const level = drag('room:hall/levels/gallery', [700, 600], [732, 600]);
        expect((hallOf(level.after).levels as JsonObject[])[0].outline).toEqual([[672, 448], [992, 448], [992, 704], [672, 704]]);
        const vault = drag('room:hall/ceiling_levels/vault', [256, 384], [256, 320]);
        expect((hallOf(vault.after).ceiling_levels as JsonObject[])[0].outline).toEqual([[128, 192], [384, 192], [384, 448], [128, 448]]);
        const still = drag('room:hall/levels/gallery', [700, 600], [700, 600]);
        expect(still.sent).toHaveLength(0);
        expect(still.passed).toBe(true);
        // The room itself is not moved by a drag inside it.
        expect(drag('room:hall', [500, 300], [600, 300]).took).toBe(false);
    });

    it('the plan picks a line near it, then a ceiling level inside it', () =>
    {
        expect(roomLineAt(files(), [500, 133], 8)).toBe('room:hall/beams/beam1');
        expect(roomLineAt(files(), [804, 380], 8)).toBe('room:hall/flights/flight1');
        expect(roomLineAt(files(), [500, 300], 8)).toBeNull();
        expect(ceilingLevelAt(files(), [200, 300])).toBe('room:hall/ceiling_levels/vault');
        expect(ceilingLevelAt(files(), [600, 100])).toBeNull();
    });

    it('a box without a size gets one written', () =>
    {
        const shape = { id: 'plate:q', base: '', kind: 'box' as const, file: 'objects.yml' as const, at: [0, 0] as [number, number], size: [64, 64] as [number, number],
            sized: false, points: [[-32, -32], [32, -32], [32, 32], [-32, 32]] as [number, number][] };
        const op = shapeGestureOp(shape, [[-32, -32], [64, -32], [64, 32], [-32, 32]], 'box');
        expect((op as { patch: JsonObject[] }).patch).toEqual([
            { op: 'test', path: '/at', value: [0, 0] }, { op: 'replace', path: '/at', value: [16, 0] }, { op: 'add', path: '/size', value: [96, 64] }]);
    });
});
