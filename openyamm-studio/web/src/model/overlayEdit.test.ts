// The Overlay tab's own tools (S6_PLAN.md item O): what each gesture writes into objects.yml `scene` (a change of a base
// thing by its lock id, its removal and putting back, a new pulsing light or sound placed on the plan, moved, changed
// and deleted), each one keyed patch with its tests, checked by applying it as the client does.
import { describe, expect, it } from 'vitest';
import type { FileTrees, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import { applyOpsLocally } from '../edit/ops.ts';
import { addedOf, changeOf, fieldText, heightNear, ladderMove, overlayOps, parseField, suggestedId } from './overlayEdit.ts';
import type { OverlayGesture } from './overlayEdit.ts';
import type { OverlayThing } from './overlay.ts';

const files = (scene?: JsonObject): FileTrees => ({
    'project.yml': { tree: { format: 0, id: 'isle_beacon', base: 'isleofashes.blv', world: 'mm9' } },
    'objects.yml': { tree: { format: 1, ...(scene ? { scene } : {}) } },
});

const run = (before: FileTrees, gesture: OverlayGesture): FileTrees =>
{
    const op = overlayOps(before, gesture);
    expect(op).not.toBeNull();
    return applyOpsLocally(before, [op!]);
};

const sceneOf = (trees: FileTrees) => trees['objects.yml']!.tree.scene as JsonObject;

describe('the Overlay tab\'s gestures', () =>
{
    it('adds a light to a project without a scene, then a second beside it; names a free id', () =>
    {
        const empty = files();
        expect(suggestedId(empty, 'lights')).toBe('light:new_1');
        const one = run(empty, { kind: 'add', list: 'lights', id: 'light:new_1', position: [1400.4, 4800, 1000] });
        expect(overlayOps(empty, { kind: 'add', list: 'lights', id: 'light:new_1', position: [0, 0, 0] })).toEqual({ op: 'patch', file: 'objects.yml',
            patch: [{ op: 'add', path: '/scene', value: { lights: [{ id: 'light:new_1', position: [0, 0, 0], color: [255, 200, 140], intensity: [0.6, 1], radius: [384, 640], frequency: 0.5 }] } }] });
        expect(addedOf(one, 'lights', 'light:new_1')!.position).toEqual([1400, 4800, 1000]);
        expect(suggestedId(one, 'lights')).toBe('light:new_2');
        const two = run(one, { kind: 'add', list: 'lights', id: 'light:new_2', position: [0, 0, 0] });
        expect((sceneOf(two).lights as JsonObject[]).map((light) => light.id)).toEqual(['light:new_1', 'light:new_2']);
        // A sound into a scene that has no sounds yet; an id taken or out of form is refused.
        const sound = run(two, { kind: 'add', list: 'sounds', id: 'sound:surf', position: [10, 20, 30] });
        expect(addedOf(sound, 'sounds', 'sound:surf')).toMatchObject({ sound: 'ambient/water/waves02.wav', radius: 900 });
        expect(overlayOps(two, { kind: 'add', list: 'lights', id: 'light:new_1', position: [0, 0, 0] })).toBeNull();
        expect(overlayOps(two, { kind: 'add', list: 'lights', id: 'no colon', position: [0, 0, 0] })).toBeNull();
    });

    it('moves, changes and deletes a thing the project adds, by its id in its list', () =>
    {
        const start = files({ lights: [{ id: 'light:beacon', position: [0, 0, 0], color: [255, 160, 60], frequency: 0.5 }] });
        const moved = overlayOps(start, { kind: 'move', list: 'lights', id: 'light:beacon', position: [5, 6, 7] });
        expect(moved).toEqual({ op: 'patch', file: 'objects.yml', patch: [
            { op: 'test', path: '/scene/lights/light:beacon/position', value: [0, 0, 0] },
            { op: 'replace', path: '/scene/lights/light:beacon/position', value: [5, 6, 7] }] });
        const changed = run(start, { kind: 'set', list: 'lights', id: 'light:beacon', fields: { color: [10, 20, 30], frequency: null, on: false } });
        expect(addedOf(changed, 'lights', 'light:beacon')).toEqual({ id: 'light:beacon', position: [0, 0, 0], color: [10, 20, 30], on: false });
        // Nothing that changes nothing.
        expect(overlayOps(start, { kind: 'set', list: 'lights', id: 'light:beacon', fields: { color: [255, 160, 60] } })).toBeNull();
        const gone = run(start, { kind: 'delete', list: 'lights', id: 'light:beacon' });
        expect(sceneOf(gone).lights).toEqual([]);
        expect(overlayOps(start, { kind: 'delete', list: 'lights', id: 'light:none' })).toBeNull();
    });

    it('changes a base thing by an entry of changes, which goes when nothing is left in it', () =>
    {
        const start = files({ changes: [{ of: 'sound:a527', volume: 0.5 }] });
        const first = run(files(), { kind: 'change', of: 'destructible:k520', fields: { hp: 40 } });
        expect(sceneOf(first).changes).toEqual([{ of: 'destructible:k520', hp: 40 }]);
        // Into its entry, the `of` tested.
        const op = overlayOps(start, { kind: 'change', of: 'sound:a527', fields: { volume: 0.8, loop: false } });
        expect(op).toEqual({ op: 'patch', file: 'objects.yml', patch: [
            { op: 'test', path: '/scene/changes/0/of', value: 'sound:a527' },
            { op: 'test', path: '/scene/changes/0/volume', value: 0.5 }, { op: 'replace', path: '/scene/changes/0/volume', value: 0.8 },
            { op: 'add', path: '/scene/changes/0/loop', value: false }] });
        expect(changeOf(applyOpsLocally(start, [op!]), 'sound:a527')!.entry).toEqual({ of: 'sound:a527', volume: 0.8, loop: false });
        // Its last word taken out: the entry goes.
        const cleared = run(start, { kind: 'change', of: 'sound:a527', fields: { volume: null } });
        expect(sceneOf(cleared).changes).toEqual([]);
        expect(overlayOps(files(), { kind: 'change', of: 'sound:a1', fields: { volume: null } })).toBeNull();
    });

    it('takes a base thing out (its change with it) and puts it back', () =>
    {
        const start = files({ changes: [{ of: 'spawn:s6', radius: 64 }], removals: ['light:k40123'] });
        const out = run(start, { kind: 'remove', of: 'spawn:s6' });
        expect(sceneOf(out).removals).toEqual(['light:k40123', 'spawn:s6']);
        expect(sceneOf(out).changes).toEqual([]);
        expect(overlayOps(out, { kind: 'remove', of: 'spawn:s6' })).toBeNull();
        const back = run(out, { kind: 'restore', of: 'light:k40123' });
        expect(sceneOf(back).removals).toEqual(['spawn:s6']);
        expect(overlayOps(back, { kind: 'restore', of: 'light:k40123' })).toBeNull();
        // Into a project with no removals yet.
        expect(sceneOf(run(files({ lights: [] }), { kind: 'remove', of: 'water:pool' })).removals).toEqual(['water:pool']);
    });

    it('reads the form\'s fields and puts a new thing at the height of what is near', () =>
    {
        expect(parseField('rgb', '255, 128 , 0')).toEqual([255, 128, 0]);
        expect(parseField('rgb', '[1 2 3]')).toEqual([1, 2, 3]);
        expect(parseField('rgb', '1, 2')).toBeUndefined();
        expect(parseField('pair', '0.4, 1')).toEqual([0.4, 1]);
        expect(parseField('integer', '40')).toBe(40);
        expect(parseField('integer', '4.5')).toBeUndefined();
        expect(parseField('number', '0.75')).toBe(0.75);
        expect(parseField('boolean', 'false')).toBe(false);
        expect(parseField('boolean', 'no')).toBeUndefined();
        expect(parseField('text', ' a.wav ')).toBe('a.wav');
        expect(parseField('number', '')).toBeNull();
        expect(fieldText([1, 2, 3])).toBe('1, 2, 3');
        expect(fieldText(undefined)).toBe('');
        const things: OverlayThing[] = [
            { id: 'spawn:s1', kind: 'spawn', origin: 'base', state: 'kept', at: [0, 0, 400], label: '' },
            { id: 'light:k1', kind: 'light', origin: 'base', state: 'kept', at: [5000, 0, 900], label: '' },
        ];
        expect(heightNear(things, [100, 0], 'lights')).toBe(560);
        expect(heightNear(things, [4900, 0], 'spawns')).toBe(740);
        expect(heightNear([], [0, 0], 'sounds')).toBe(64);
        // S8a: a facing, a reference, an offset.
        expect(parseField('facing', 'ne')).toBe('ne');
        expect(parseField('facing', '135')).toBe(135);
        expect(parseField('facing', 'up')).toBeUndefined();
        expect(parseField('ref', '9183')).toBe(9183);
        expect(parseField('ref', 'Skeletoid')).toBe('Skeletoid');
        expect(parseField('xyz', '10, 0, -5')).toEqual([10, 0, -5]);
        expect(heightNear(things, [100, 0], 'ladders')).toBe(400);
    });

    it('adds a ladder, a monster and an item (S8a), and moves a base ladder by its offset', () =>
    {
        const ladder = run(files(), { kind: 'add', list: 'ladders', id: suggestedId(files(), 'ladders'), position: [1324, 3310, 656] });
        expect(addedOf(ladder, 'ladders', 'ladder:new_1')).toEqual({ id: 'ladder:new_1', position: [1324, 3310, 656], facing: 'n', height: 256 });
        const monster = run(ladder, { kind: 'add', list: 'monsters', id: 'monster:guard', position: [1800, 3500, 987], value: { monster: 9183, immobile: true } });
        const item = run(monster, { kind: 'add', list: 'items', id: suggestedId(monster, 'items'), position: [1450, 3450, 995] });
        expect(addedOf(item, 'items', 'item:new_1')).toEqual({ id: 'item:new_1', position: [1450, 3450, 995], item: 1 });
        expect(suggestedId(item, 'monsters')).toBe('monster:new_1');
        const moved = run(item, { kind: 'move', list: 'monsters', id: 'monster:guard', position: [1700, 3500, 987] });
        expect(addedOf(moved, 'monsters', 'monster:guard')).toEqual({ id: 'monster:guard', position: [1700, 3500, 987], monster: 9183, immobile: true });
        // A base ladder: moved by `offset` from where the base map has it, the height its change gave kept.
        const base: OverlayThing = { id: 'ladder:ladder0', kind: 'ladder', origin: 'base', state: 'kept', at: [9155, 297, -1257], label: '' };
        const once = run(files(), ladderMove(files(), base, [9255, 297]));
        expect(sceneOf(once).changes).toEqual([{ of: 'ladder:ladder0', offset: [100, 0, 0] }]);
        const raised = run(once, { kind: 'change', of: 'ladder:ladder0', fields: { offset: [100, 0, 32], facing: 'n' } });
        const twice = run(raised, ladderMove(raised, base, [9155, 397]));
        expect(sceneOf(twice).changes).toEqual([{ of: 'ladder:ladder0', offset: [0, 100, 32], facing: 'n' }]);
        expect(sceneOf(run(twice, { kind: 'remove', of: 'ladder:ladder0' })).removals).toEqual(['ladder:ladder0']);
    });
});
