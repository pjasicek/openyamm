// The corpus rule (S5_BROWSER_EDITOR.md 3.8): the lint checks that annotations exist, this checks that they are
// right where the projects can tell. Every number of the 22 calibration projects is read with the schema node it
// stands at; where that node (or the list, tuple, union or geometric field it is in) has an x-unit, the number must
// lie in the unit's range, so a wrong x-unit shows as values out of range. Words of a discriminated object must be
// of its kind (x-kinds), so a kind table that forbids what the projects use shows too. Node only (reads files).

import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { parse } from 'yaml';
import { Registry } from '../schema/registry.ts';
import type { Json, Located, Schema } from '../schema/registry.ts';
import { planUnion } from '../form/plan.ts';
import { unitFor } from '../form/context.ts';

export const repoRoot = join(import.meta.dirname, '..', '..', '..', '..');
export const corpusAllowPath = join(import.meta.dirname, 'corpus_allow.json');
const PROJECT_FOLDERS = ['devdocs/map_studio/briefs', 'devdocs/xeen/briefs'];
// core/Project.cpp projectFileKinds (pins are review records, not calibration data).
const FILE_SCHEMAS: Record<string, string> = {
    'project.yml': 'project.schema.json',
    'plan.yml': 'plan.schema.json',
    'sketch.yml': 'sketch.schema.json',
    'rooms.yml': 'rooms.schema.json',
    'objects.yml': 'objects.schema.json',
    'wiring.yml': 'wiring.schema.json',
    'atmosphere.yml': 'atmosphere.schema.json',
    'ids.lock.yml': 'ids_lock.schema.json',
};

interface Range
{
    test: (v: number) => boolean;
    says: string;
}

const whole = (v: number) => Number.isInteger(v);
// What a number of each unit can be. Map units: the game's coordinates are 16-bit, outdoors and in.
export const RANGES: Record<string, Range> = {
    map: { test: (v) => Math.abs(v) <= 32768, says: 'within ±32768 map units' },
    cell: { test: (v) => v >= 0 && v <= 256, says: '0 to 256 terrain cells (the map side: 128 classic, project.yml terrain.side)' },
    deg: { test: (v) => v >= -360 && v <= 360, says: '-360 to 360 degrees' },
    ratio: { test: (v) => v >= 0 && v <= 1, says: 'a share, 0 to 1' },
    count: { test: (v) => whole(v) && v >= 0, says: 'a whole number, 0 or more' },
    index: { test: (v) => whole(v) && v >= 0, says: 'a whole number, 0 or more' },
    texel: { test: (v) => whole(v) && Math.abs(v) <= 4096, says: 'whole texels within ±4096' },
    gold: { test: (v) => whole(v), says: 'whole gold' },
    angle2048: { test: (v) => whole(v) && v >= 0 && v < 2048, says: '0 to 2047' },
    seconds: { test: (v) => v >= 0, says: '0 seconds or more' },
    minutes: { test: (v) => v >= 0, says: '0 minutes or more' },
    days: { test: (v) => whole(v) && v >= 0, says: 'whole days, 0 or more' },
    percent: { test: (v) => v >= 0 && v <= 100, says: '0 to 100 percent' },
    units_per_second: { test: (v) => v > 0, says: 'above 0' },
    deg_per_second: { test: (v) => v > 0, says: 'above 0' },
    per_second: { test: (v) => v >= 0, says: '0 or more' },
    none: { test: () => true, says: 'anything' },
};

export interface FieldStat
{
    field: string;     // file#pointer of the schema node the numbers stand at
    unit: string;
    values: number;
    outside: number[]; // the values out of range (the first few)
    outsideCount: number;
    where: string[];   // project, file and place of the first few
}

export interface KindFinding
{
    key: string;       // "kinds <file#pointer> <kind>"
    count: number;
    where: string[];
}

export interface CorpusReport
{
    projects: number;
    numbers: number;
    unitless: number;  // numbers at nodes without a unit (unannotated words: the lint's allow list)
    unitlessFields: Map<string, number>;
    fields: Map<string, FieldStat>;
    kinds: Map<string, KindFinding>;
}

export function projectFolders(): string[]
{
    const out: string[] = [];
    for (const folder of PROJECT_FOLDERS)
    {
        const root = join(repoRoot, folder);
        for (const name of readdirSync(root).sort())
        {
            const project = join(root, name, 'L4');
            if (existsSync(join(project, 'project.yml')))
            {
                out.push(project);
            }
        }
    }
    return out;
}

interface Inherited
{
    unit?: unknown;     // an enclosing list's, tuple's or union's x-unit
    space?: string;     // inside a geometric field: its space
}

class Walker
{
    report: CorpusReport = {
        projects: 0, numbers: 0, unitless: 0, unitlessFields: new Map(), fields: new Map(), kinds: new Map(),
    };
    private place = '';
    private reg: Registry;

    constructor(reg: Registry)
    {
        this.reg = reg;
    }

    file(project: string, fileName: string, schema: string, value: Json)
    {
        this.place = `${project}/${fileName}`;
        this.visit(this.reg.root(schema), value, {}, undefined, '');
    }

    private visit(loc: Located, value: Json, inherited: Inherited, kind: string | undefined, path: string)
    {
        const resolved = this.reg.resolve(loc);
        const node: Schema = resolved.node;
        const own = node['x-unit'];
        const geom = node['x-geom'];
        const next: Inherited = {
            unit: own ?? inherited.unit,
            space: geom && typeof geom === 'object' ? (typeof geom.space === 'string' ? geom.space : 'map') : inherited.space,
        };

        const union = planUnion(this.reg, loc);
        if (union)
        {
            const branch = union.branches.find((b) => b.test(value));
            if (branch)
            {
                // Numbers in a branch are reported at the union (a type list's branches are no schema nodes).
                this.visit({ ...branch.loc, ptr: branch.loc.ptr.includes('/type/') ? loc.ptr : branch.loc.ptr },
                    value, next, kind, path);
            }
            return;
        }

        if (typeof value === 'number')
        {
            this.number(loc, value, own, inherited, next, kind, path);
            return;
        }
        if (Array.isArray(value))
        {
            value.forEach((item, i) => {
                const child = Array.isArray(node.prefixItems) && i < node.prefixItems.length
                    ? this.reg.child(resolved, 'prefixItems', i)
                    : node.items && typeof node.items === 'object' ? this.reg.child(resolved, 'items') : undefined;
                if (child)
                {
                    this.visit(child, item, next, undefined, `${path}[${i}]`);
                }
            });
            return;
        }
        if (value !== null && typeof value === 'object')
        {
            const props: Schema = node.properties ?? {};
            const disc = node['x-discriminator'];
            const kindHere = disc ? String(value[disc.property] ?? disc.default) : undefined;
            for (const [key, child] of Object.entries(value))
            {
                if (key in props)
                {
                    const propLoc = this.reg.child(resolved, 'properties', key);
                    const kinds = propLoc.node['x-kinds'];
                    if (kindHere !== undefined && Array.isArray(kinds) && !kinds.includes(kindHere))
                    {
                        this.kindFinding(`kinds ${propLoc.file}${propLoc.ptr} ${kindHere}`, `${path}.${key}`);
                    }
                    this.visit(propLoc, child, { space: next.space }, kindHere, `${path}.${key}`);
                }
                else if (node.additionalProperties && typeof node.additionalProperties === 'object')
                {
                    this.visit(this.reg.child(resolved, 'additionalProperties'), child, { space: next.space }, undefined,
                        `${path}.${key}`);
                }
            }
        }
    }

    private number(loc: Located, value: number, own: unknown, inherited: Inherited, next: Inherited,
        kind: string | undefined, path: string)
    {
        this.report.numbers += 1;
        // Its own unit, else the enclosing list's or union's, else the geometric field's space.
        let unit = unitFor(own ?? inherited.unit, kind);
        if (unit === undefined && next.space !== undefined)
        {
            unit = next.space === 'cell' ? 'cell' : 'map';
        }
        if (unit === undefined)
        {
            this.report.unitless += 1;
            this.report.unitlessFields.set(`${loc.file}${loc.ptr}`, (this.report.unitlessFields.get(`${loc.file}${loc.ptr}`) ?? 0) + 1);
            return;
        }
        const field = `${loc.file}${loc.ptr}`;
        let stat = this.report.fields.get(field);
        if (!stat)
        {
            stat = { field, unit, values: 0, outside: [], outsideCount: 0, where: [] };
            this.report.fields.set(field, stat);
        }
        stat.values += 1;
        const range = RANGES[unit];
        if (range && !range.test(value))
        {
            stat.outsideCount += 1;
            if (stat.outside.length < 5)
            {
                stat.outside.push(value);
                stat.where.push(`${this.place} ${path}`);
            }
        }
    }

    private kindFinding(key: string, path: string)
    {
        let finding = this.report.kinds.get(key);
        if (!finding)
        {
            finding = { key, count: 0, where: [] };
            this.report.kinds.set(key, finding);
        }
        finding.count += 1;
        if (finding.where.length < 3)
        {
            finding.where.push(`${this.place} ${path}`);
        }
    }
}

export function checkCorpus(reg: Registry, folders = projectFolders()): CorpusReport
{
    const walker = new Walker(reg);
    for (const folder of folders)
    {
        const project = folder.split('/').slice(-2, -1)[0];
        for (const [fileName, schema] of Object.entries(FILE_SCHEMAS))
        {
            const path = join(folder, fileName);
            if (existsSync(path) && reg.files[schema])
            {
                walker.file(project, fileName, schema, parse(readFileSync(path, 'utf8')) as Json);
            }
        }
        walker.report.projects += 1;
    }
    return walker.report;
}

// What fails: a field with numbers out of its unit's range, a word on a kind its x-kinds does not list; each unless
// the allow list gives the reason it is right. Stale allow entries fail too.
export function corpusFindings(report: CorpusReport, allow: Record<string, string>)
{
    const found: { key: string; message: string }[] = [];
    for (const stat of report.fields.values())
    {
        if (stat.outsideCount > 0)
        {
            found.push({
                key: `range ${stat.field}`,
                message: `${stat.outsideCount} of ${stat.values} values are not ${RANGES[stat.unit]?.says ?? stat.unit}`
                    + ` (x-unit ${stat.unit}): ${stat.outside.join(', ')} at ${stat.where.join('; ')}`,
            });
        }
    }
    for (const finding of report.kinds.values())
    {
        found.push({ key: finding.key, message: `${finding.count} times: ${finding.where.join('; ')}` });
    }
    const keys = new Set(found.map((f) => f.key));
    return {
        fresh: found.filter((f) => !(f.key in allow)),
        stale: Object.keys(allow).filter((k) => !keys.has(k)),
        all: found,
    };
}
