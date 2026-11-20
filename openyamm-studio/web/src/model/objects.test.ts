import { describe, expect, it } from 'vitest';
import type { FileTrees, IdPlace } from '../../../schema/rpc/generated/rpc.ts';
import { baseId, findObject, issueObject, searchIds } from './objects.ts';

const files = {
    'rooms.yml': { tree: { rooms: [{ id: 'room:entry', floor: 0 }, { id: 'room:hall', floor: 64 }] } },
    'plan.yml': { tree: { spaces: [{ id: 'room:entry', purpose: 'arrival' }] } },
} as unknown as FileTrees;
const ids: IdPlace[] = [
    { id: 'room:entry', file: 'plan.yml', list: 'spaces' },
    { id: 'room:entry', file: 'rooms.yml', list: 'rooms' },
    { id: 'room:hall', file: 'rooms.yml', list: 'rooms' },
];

describe('project objects', () =>
{
    it('finds an id in the file named, else the room before the plan space', () =>
    {
        expect(findObject(files, ids, { id: 'room:entry' })?.file).toBe('rooms.yml');
        expect(findObject(files, ids, { id: 'room:entry', file: 'plan.yml' })?.value).toMatchObject({ purpose: 'arrival' });
        expect(findObject(files, ids, { id: 'room:none' })).toBeUndefined();
    });

    it('maps an issue path and a face owner to their object', () =>
    {
        expect(issueObject(files, { file: 'rooms.yml', path: 'rooms[1].floor' })).toEqual({ id: 'room:hall', file: 'rooms.yml' });
        expect(issueObject(files, { file: 'sketch.yml', path: 'heights.cliffs[1].line' })).toBeUndefined();
        expect(baseId('room:hall/walls/3')).toBe('room:hall');
    });

    it('searches ids by every word', () =>
    {
        expect(searchIds(ids, 'hall').map((p) => p.id)).toEqual(['room:hall']);
        expect(searchIds(ids, '')).toEqual([]);
    });
});
