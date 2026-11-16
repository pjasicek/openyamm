// The corpus rule in the unit suite (S5_BROWSER_EDITOR.md 3.8): the numbers of the calibration projects (the 22 of S5
// and every L4 added since, such as the Xeen maps) lie in
// the ranges of their x-units, and their words are of the kinds x-kinds lists. A field that is right out of range
// is in corpus_allow.json with the reason; the list may only shrink, as the lint's.
import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { checkCorpus, corpusAllowPath, corpusFindings, projectFolders } from './corpus.ts';
import { loadSchemas } from './load.ts';
import { Registry } from '../schema/registry.ts';

describe('corpus rule', () =>
{
    it('finds every number of the projects in its unit\'s range and every word on a kind it belongs to', () =>
    {
        const folders = projectFolders();
        expect(folders.length).toBeGreaterThanOrEqual(22);
        const report = checkCorpus(loadSchemas(), folders);
        const allow: Record<string, string> = JSON.parse(readFileSync(corpusAllowPath, 'utf8'));
        const { fresh, stale } = corpusFindings(report, allow);
        expect(fresh.map((f) => `${f.key}: ${f.message}`)).toEqual([]);
        expect(stale).toEqual([]);
        expect(report.fields.size).toBeGreaterThan(100);
    }, 60000);

    it('reports a wrong unit and a word on the wrong kind', () =>
    {
        const registry = loadSchemas();
        const objects = structuredClone(registry.files['objects.schema.json']);
        // A door's travel said to be a share: the projects' travels (64 and more) fall outside 0 to 1.
        objects.properties.doors.items.properties.travel['x-unit'] = 'ratio';
        // Hinged doors said to have no speed.
        objects.properties.doors.items.properties.speed['x-kinds'] = ['slide_up'];
        const report = checkCorpus(new Registry({ ...registry.files, 'objects.schema.json': objects }));
        const { fresh } = corpusFindings(report, JSON.parse(readFileSync(corpusAllowPath, 'utf8')));
        const keys = fresh.map((f) => f.key);
        expect(keys).toContain('range objects.schema.json#/properties/doors/items/properties/travel');
        expect(keys).toContain('kinds objects.schema.json#/properties/doors/items/properties/speed hinged');
    }, 60000);
});
