import { describe, expect, it } from 'vitest';
import type { JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import { SKETCH_KEYED, keyedAt, keysOf, placeOf, placeOfPointer, pointerOf, resolvePointer, subAddresses } from './keys.ts';
import { applyOpsLocally } from './ops.ts';
import { loadSchemas } from '../lint/load.ts';
import type { Registry } from '../schema/registry.ts';

// Every keyed list of a schema by place: property names from the file's root, `*` for a row, through $ref and the
// branches of unions (as keys.ts reads sketch.yml).
function keyedPlaces(registry: Registry, file: string): Record<string, { field: string; prefix?: string }>
{
    const found: Record<string, { field: string; prefix?: string }> = {};
    const visit = (loc: ReturnType<Registry['root']>, place: string, depth: number) =>
    {
        if (depth > 16)
        {
            return;
        }
        const resolved = registry.resolve(loc);
        const node = resolved.node;
        if (typeof node !== 'object' || node === null)
        {
            return;
        }
        if (node.type === 'array' || node.items)
        {
            if (typeof node['x-key'] === 'string' && node['x-key'] !== '#')
            {
                found[place] = { field: node['x-key'], ...(node['x-key-prefix'] ? { prefix: node['x-key-prefix'] } : {}) };
            }
            if (node.items && typeof node.items === 'object' && !Array.isArray(node.items))
            {
                visit(registry.child(resolved, 'items'), `${place}/*`, depth + 1);
            }
        }
        for (const [name] of Object.entries(node.properties ?? {}))
        {
            visit(registry.child(resolved, 'properties', name), `${place}/${name}`, depth + 1);
        }
        for (const key of ['allOf', 'oneOf', 'anyOf'])
        {
            (Array.isArray(node[key]) ? node[key] : []).forEach((_: unknown, index: number) => visit(registry.child(resolved, key, index), place, depth + 1));
        }
    };
    visit(registry.root(file), '', 0);
    return found;
}

describe('keys by place (sketch.yml)', () =>
{
    it('names the same keyed lists and prefixes as sketch.schema.json, place by place', () =>
    {
        expect(keyedPlaces(loadSchemas(), 'sketch.schema.json')).toEqual(SKETCH_KEYED);
    });

    it('tells apart lists of one name by place: a building\'s parts by id, heights.points by key, points by id', () =>
    {
        const scope = { file: 'sketch.yml' };
        expect(keyedAt(scope, '/structures/*/parts')).toEqual({ field: 'id', prefix: 'part' });
        expect(keyedAt(scope, '/heights/points')).toEqual({ field: 'key', prefix: 'point' });
        expect(keyedAt(scope, '/points')).toEqual({ field: 'id' });
        // Indoors the rule stays by name.
        expect(keyedAt({ file: 'objects.yml' }, '/movers/*/parts')).toEqual({ field: 'key', prefix: 'part' });
        expect(keyedAt(undefined, '/pillars')).toEqual({ field: 'key', prefix: 'pillar' });
    });

    it('reads missing keys of sketch lists as the core does (parts without an id as part<n>)', () =>
    {
        expect(keysOf([{ id: 'main' }, {}, { id: 'part2' }], 'parts', keyedAt({ file: 'sketch.yml' }, '/structures/*/parts'))).toEqual(['main', 'part3', 'part2']);
        expect(keysOf([{}, { key: 'ridge1' }], 'ridges', keyedAt({ file: 'sketch.yml' }, '/heights/ridges'))).toEqual(['ridge2', 'ridge1']);
    });

    const sketch = (): JsonObject => ({
        heights: { ridges: [{ line: [[1, 2], [3, 4]], height: 100 }, { key: 'north', line: [[5, 6], [7, 8]], height: 200 }], points: [{ at: [1, 1], h: 5 }] },
        points: [{ id: 'entrance:start', at: [64, 64] }],
        structures: [{ id: 'thing:hall', kind: 'building', at: [10, 10], size: [3, 2], parts: [{ id: 'main' }, { at: [512, 0], size: [512, 512], porches: [{ wall: 's' }] }] }],
        districts: [{ space: 'zone:town', polygon: [[0, 0], [4, 0], [4, 4]], plots: [{ building: 'building:a', at: [1, 1], facing: 's' }] }],
    });

    it('turns form paths into keyed pointers by place, and resolves them back', () =>
    {
        const scope = { file: 'sketch.yml', base: '' };
        const tree = sketch();
        expect(pointerOf(tree, ['heights', 'ridges', 0, 'line', 1], scope)).toEqual({ pointer: '/heights/ridges/ridge1/line/1', positional: true });
        expect(pointerOf(tree, ['heights', 'ridges', 1, 'height'], scope)).toEqual({ pointer: '/heights/ridges/north/height', positional: false });
        expect(pointerOf(tree, ['structures', 0, 'parts', 1, 'porches', 0], scope).pointer).toBe('/structures/thing:hall/parts/part2/porches/porch1');
        expect(resolvePointer(tree, '/districts/district1/plots/plot1/facing', scope)).toBe('s');
        expect(placeOf(tree, '/structures/thing:hall/parts/main', scope)).toBe('/structures/*/parts/*');
        expect(placeOfPointer('/districts/district1/plots/plot1', scope)).toBe('/districts/*/plots/*');
        // From a top-level object (its place given): the building's parts by id.
        const hall = (tree.structures as JsonObject[])[0];
        expect(subAddresses('thing:hall', hall, { file: 'sketch.yml', base: '/structures/*' }).map((entry) => entry.address)).toEqual(['thing:hall/parts/main', 'thing:hall/parts/part2']);
    });

    it('applies keyed patches to the sketch on the client as the core does', () =>
    {
        const files = { 'sketch.yml': { tree: sketch() } };
        const after = applyOpsLocally(files, [
            { op: 'patch', file: 'sketch.yml', patch: [{ op: 'replace', path: '/heights/ridges/north/height', value: 300 }, { op: 'add', path: '/districts/district1/plots/-', value: { building: 'building:b', at: [2, 2], facing: 'n' } }] },
            { op: 'patch', id: 'thing:hall', file: 'sketch.yml', patch: [{ op: 'add', path: '/parts/part2/roof', value: 'flat' }] },
        ]);
        const tree = after['sketch.yml']!.tree;
        expect(resolvePointer(tree, '/heights/ridges/north/height', { file: 'sketch.yml' })).toBe(300);
        expect(((tree.districts as JsonObject[])[0].plots as JsonObject[]).length).toBe(2);
        expect(((tree.structures as JsonObject[])[0].parts as JsonObject[])[1].roof).toBe('flat');
    });
});
