// The schema lint in the unit suite (S5_BROWSER_EDITOR.md 3.8, 4.13): today's issues are the allow list, which may
// only shrink. A word added without its annotations fails here; so does an entry for an issue that is fixed.
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { checkAllowList, issueKey, lintSchemas } from './lint.ts';
import { allowPath, loadSchemas } from './load.ts';
import { Registry } from '../schema/registry.ts';

describe('schema lint', () =>
{
    it('finds no issue outside the allow list, and the list has no stale entry', () =>
    {
        const issues = lintSchemas(loadSchemas());
        const allow: string[] = JSON.parse(readFileSync(allowPath, 'utf8'));
        const { fresh, stale } = checkAllowList(issues, allow);
        expect(fresh.map((issue) => `${issueKey(issue)}: ${issue.message}`)).toEqual([]);
        expect(stale).toEqual([]);
    });

    it('reports a new unannotated list of objects with a number and an id (as a schema change would add)', () =>
    {
        const registry = loadSchemas();
        const rooms = structuredClone(registry.files['rooms.schema.json']);
        rooms.properties.alcoves = {
            type: 'array',
            items: { type: 'object', properties: { id: { $ref: 'common.schema.json#/$defs/id' }, depth: { type: 'number' }, room: { $ref: 'common.schema.json#/$defs/id' } } },
        };
        const issues = lintSchemas(new Registry({ ...registry.files, 'rooms.schema.json': rooms }));
        const allow: string[] = JSON.parse(readFileSync(allowPath, 'utf8'));
        const fresh = checkAllowList(issues, allow).fresh.map(issueKey);
        expect(fresh).toContain('key rooms.schema.json#/properties/alcoves');
        expect(fresh).toContain('unit rooms.schema.json#/properties/alcoves/items/properties/depth');
        expect(fresh).toContain('id-kinds rooms.schema.json#/properties/alcoves/items/properties/room');
    });

    it('reports the group rule per property', () =>
    {
        const props: Record<string, unknown> = {};
        for (let i = 0; i < 11; ++i)
        {
            props[`word_${i}`] = { type: 'string' };
        }
        const grouped = { type: 'object', properties: props, 'x-groups': [['Main', Object.keys(props).slice(0, 10)]] };
        const issues = lintSchemas(new Registry({ 't.schema.json': { $defs: { thing: grouped } } }));
        expect(issues.filter((i) => i.rule === 'group').map((i) => i.where)).toEqual(['t.schema.json#/$defs/thing/properties/word_10']);
    });

    it('flags a stale allow-list entry', () =>
    {
        const { stale } = checkAllowList([], ['unit gone.schema.json#/x']);
        expect(stale).toEqual(['unit gone.schema.json#/x']);
    });
});
