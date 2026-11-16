// The schema lint (S5_BROWSER_EDITOR.md 3.8, D5; from spike 7's draft): fails a schema change that lacks what the
// generated form needs. It uses the form generator's own classification (plan.ts), so it fails exactly where the
// form would draw badly.
// It walks every schema node of every file at its own place (a $ref is checked where its target is written) and
// reports one issue per node and rule. A checked-in allow list holds today's issues; the lint fails on an issue not
// in the list and on a list entry that no longer occurs, so the list can only shrink.

import { Registry } from '../schema/registry.ts';
import type { Located, Schema } from '../schema/registry.ts';
import { classify, isPresenceUnion, isPresenceVariant, looksGeometric, planUnion } from '../form/plan.ts';

export interface LintIssue
{
    rule: string;
    where: string; // file#pointer
    message: string;
}

// Time and rates were added in S5b1 (seconds, minutes, days, percent, units a second, degrees a second, times a
// second): the indoor words have them, and 'none' would hide what the number counts.
export const UNITS = ['map', 'cell', 'deg', 'ratio', 'count', 'index', 'texel', 'gold', 'angle2048', 'none', 'seconds',
    'minutes', 'days', 'percent', 'units_per_second', 'deg_per_second', 'per_second'];
export const GEOM_SHAPES = ['point', 'point3', 'size', 'polygon', 'polyline', 'polylines', 'points3', 'plane3', 'wall',
    'walls', 'bays'];
export const GEOM_SPACES = ['map', 'cell', 'local', 'part', 'room', 'wall', 'section', 'other_map'];
export const ID_KINDS = ['thing', 'building', 'room', 'corridor', 'space', 'theme', 'panel', 'platform', 'level', 'region',
    'door', 'lift', 'mover', 'evt', 'zone', 'link', 'switch', 'spawn', 'chest', 'npc', 'pop', 'loot', 'goal', 'poi',
    'set', 'entrance', 'neighbour', 'area', 'road', 'district', 'plot', 'point', 'view', 'scatter', 'actor', 'event',
    'pin', 'light', 'sound', 'floor', 'trap', 'puzzle',
    // S5b1, the indoor files: a kind is the list an id belongs to (objects.yml `exits` are exit, rooms.yml `openings`
    // opening, plan.yml `regions` plan_region), not its prefix, which projects choose freely (exit:, door:, edge: are
    // all neighbours).
    'opening', 'monster', 'item', 'decoration', 'placeholder', 'exit', 'ladder', 'plate', 'plan_region', 'loop',
    'teleport_set', 'lock_group', 'key', 'container', 'landmark', 'sightline', 'set_piece', 'height_band', 'state',
    // S6: the scene's MM9 things (destructibles, water volumes) and cinematics.
    'destructible', 'water', 'cinematic'];
export const WIDGETS = ['effects'];
const GROUP_THRESHOLD = 10;   // an object with this many properties needs sections
const KIND_THRESHOLD = 12;    // an object with a kind enum and this many properties is a union in disguise

const NUMERIC = (t: unknown) => t === 'number' || t === 'integer' || (Array.isArray(t) && t.every((x) => x === 'number' || x === 'integer'));

export function lintSchemas(reg: Registry): LintIssue[]
{
    const issues: LintIssue[] = [];
    for (const file of Object.keys(reg.files).sort())
    {
        walk(reg, reg.root(file), issues, { unitAbove: false, geomAbove: false, widgetAbove: false, isProperty: false });
    }
    return issues;
}

interface Context
{
    unitAbove: boolean;   // an enclosing array or tuple carries x-unit (its numbers share it)
    geomAbove: boolean;   // inside a geometric field (its numbers are positions in its space)
    widgetAbove: boolean; // inside a bespoke widget
    isProperty: boolean;  // the node is a property's schema (or a list's/map's item), i.e. a field
    discriminated?: { property: string; values: unknown[] };
}

function add(issues: LintIssue[], loc: Located, rule: string, message: string)
{
    issues.push({ rule, where: `${loc.file}${loc.ptr}`, message });
}

function walk(reg: Registry, loc: Located, issues: LintIssue[], ctx: Context)
{
    const node: Schema = loc.node;
    if (!node || typeof node !== 'object')
    {
        return;
    }
    const isRef = typeof node.$ref === 'string';
    const widget = ctx.isProperty ? classify(reg, loc) : undefined;
    const resolved = isRef ? reg.resolve(loc).node : node;
    let unitAbove = ctx.unitAbove || node['x-unit'] !== undefined;
    let geomAbove = ctx.geomAbove;
    const widgetAbove = ctx.widgetAbove || typeof node['x-widget'] === 'string';

    if (ctx.isProperty && !widgetAbove)
    {
        // Ids: every id field says which kinds it names (its own kind for the object's own id).
        if (widget?.kind === 'id' && !Array.isArray(node['x-id-kinds']) && !loc.ptr.endsWith('/$defs/id'))
        {
            add(issues, loc, 'id-kinds', 'an id field without x-id-kinds');
        }
        // Geometry: a point, size, outline or line says how it is edited on the map, or x-geom: false.
        if (!ctx.geomAbove && node['x-geom'] === undefined && looksGeometric(reg, loc) && !isRef)
        {
            add(issues, loc, 'geom', 'a geometric field without x-geom (or x-geom: false)');
        }
        // Numbers: every number has a unit (none, count and index included), here or on its list or tuple.
        if (!isRef && NUMERIC(node.type) && node.enum === undefined && node.const === undefined && !unitAbove && !ctx.geomAbove)
        {
            add(issues, loc, 'unit', 'a number without x-unit');
        }
        // Lists of objects: rows are keyed (x-key: a property, '#' positional, false not selectable).
        if (widget?.kind === 'list' && widget.ofObjects && node['x-key'] === undefined)
        {
            add(issues, loc, 'key', 'a list of objects without x-key');
        }
        // Anything the generator would show as raw JSON needs a schema or a bespoke widget.
        if (widget?.kind === 'raw')
        {
            add(issues, loc, 'raw', `the form cannot draw this (${widget.reason}); give it a schema or x-widget`);
        }
        // Discriminated objects: every property says which kinds it belongs to.
        if (ctx.discriminated && node['x-kinds'] === undefined)
        {
            add(issues, loc, 'kinds', `a property of an object discriminated by ${ctx.discriminated.property} without x-kinds`);
        }
    }
    if (node['x-geom'] !== undefined && node['x-geom'] !== false)
    {
        geomAbove = true;
    }

    // Unions: branches of one JSON type need a constant or x-variant; presence unions need x-variant labels.
    if (!isRef)
    {
        const plan = planUnion(reg, loc);
        if (plan?.mode === 'shape')
        {
            add(issues, loc, 'union', 'a union whose branches share a JSON type, without a const discriminator or x-variant');
        }
        if (Array.isArray(node.oneOf) && isPresenceUnion(node, 'oneOf') && !Array.isArray(node['x-variant']))
        {
            add(issues, loc, 'union', 'a presence union (oneOf of required) without x-variant labels');
        }
        if (Array.isArray(node['x-variant']))
        {
            const branches = node.oneOf ?? node.anyOf ?? (Array.isArray(node.type) ? node.type : []);
            if (isPresenceVariant(node))
            {
                // An object's implicit choice (a room's outline or path) written as x-variant alone, without a
                // oneOf that would change what validates: each entry names a property that selects it.
                for (const v of node['x-variant'])
                {
                    for (const p of [v.when.present, ...(v.props ?? [])])
                    {
                        if (!(p in node.properties))
                        {
                            add(issues, loc, 'annotation', `x-variant names ${p}, no property of this object`);
                        }
                    }
                }
            }
            else if (branches.length !== node['x-variant'].length)
            {
                add(issues, loc, 'annotation', 'x-variant has not one entry per branch');
            }
        }
    }

    // Objects: sections for long forms; a kind enum with many properties is a union in disguise.
    const props: Schema | undefined = node.properties;
    let discriminated: Context['discriminated'];
    if (props && !isRef)
    {
        const names = Object.keys(props);
        // Sections per object (x-groups, revision 4): every property in exactly one section, reported per
        // property so that a new property on an allowed object does not pass unseen.
        if (names.length >= GROUP_THRESHOLD && !widgetAbove)
        {
            const sections: [string, string[]][] = Array.isArray(node['x-groups']) ? node['x-groups'] : [];
            const count = new Map<string, number>();
            for (const [, members] of sections)
            {
                for (const member of members)
                {
                    count.set(member, (count.get(member) ?? 0) + 1);
                }
            }
            for (const name of names)
            {
                const times = count.get(name) ?? 0;
                if (times !== 1 && props[name]['x-group'] === undefined)
                {
                    add(issues, reg.child(loc, 'properties', name), 'group', times === 0
                        ? `a property of an object of ${names.length} properties in no x-groups section`
                        : `a property in ${times} x-groups sections`);
                }
            }
            for (const member of count.keys())
            {
                if (!(member in props))
                {
                    add(issues, loc, 'annotation', `x-groups names ${member}, no property of this object`);
                }
            }
        }
        const kindProp = ['kind', 'shape', 'form', 'type'].find((k) => props[k] && Array.isArray(props[k].enum));
        if (node['x-discriminator'])
        {
            const d = node['x-discriminator'];
            const target = props[d.property];
            if (!target || !Array.isArray(target.enum))
            {
                add(issues, loc, 'annotation', `x-discriminator names ${d.property}, which is no enum property`);
            }
            else
            {
                discriminated = { property: d.property, values: target.enum };
                if (!(node.required ?? []).includes(d.property) && d.default === undefined && target.default === undefined)
                {
                    add(issues, loc, 'annotation', `discriminator ${d.property} is neither required nor has a default`);
                }
            }
        }
        // x-discriminator: false says the enum selects no properties (a pack's `shape`, a treasure's `kind`).
        else if (kindProp && names.length >= KIND_THRESHOLD && !widgetAbove && node['x-discriminator'] !== false)
        {
            add(issues, loc, 'kinds', `${names.length} properties and a ${kindProp} enum without x-discriminator`);
        }
    }

    checkAnnotationValues(reg, loc, issues, discriminated ?? ctx.discriminated);

    // Children.
    const child = (keys: (string | number)[], c: Partial<Context>) =>
        walk(reg, reg.child(loc, ...keys), issues, { unitAbove: false, geomAbove, widgetAbove, isProperty: false, ...c });
    if (props)
    {
        for (const name of Object.keys(props))
        {
            child(['properties', name], { isProperty: true, discriminated });
        }
    }
    const carryUnit = node.type === 'array' || Array.isArray(node.type) ? unitAbove : false;
    if (node.items && typeof node.items === 'object')
    {
        child(['items'], { isProperty: true, unitAbove: carryUnit });
    }
    if (Array.isArray(node.prefixItems))
    {
        node.prefixItems.forEach((_: Schema, i: number) => child(['prefixItems', i], { isProperty: true, unitAbove: carryUnit }));
    }
    if (node.additionalProperties && typeof node.additionalProperties === 'object')
    {
        child(['additionalProperties'], { isProperty: true });
    }
    for (const key of ['oneOf', 'anyOf'])
    {
        if (Array.isArray(node[key]))
        {
            node[key].forEach((_: Schema, i: number) => child([key, i], { isProperty: !isPresenceUnion(node, key as 'oneOf'), unitAbove }));
        }
    }
    if (node.not && typeof node.not === 'object')
    {
        child(['not'], { isProperty: false });
    }
    if (node.$defs)
    {
        for (const name of Object.keys(node.$defs))
        {
            child(['$defs', name], { isProperty: true });
        }
    }
    void resolved;
}

function checkAnnotationValues(reg: Registry, loc: Located, issues: LintIssue[], disc?: Context['discriminated'])
{
    const node = loc.node;
    const unit = node['x-unit'];
    const unitValues = typeof unit === 'object' && unit !== null ? Object.values(unit) : unit === undefined ? [] : [unit];
    for (const u of unitValues)
    {
        if (!UNITS.includes(u as string))
        {
            add(issues, loc, 'annotation', `x-unit ${String(u)} is not one of ${UNITS.join(', ')}`);
        }
    }
    const geom = node['x-geom'];
    if (geom !== undefined && geom !== false)
    {
        const spaces = typeof geom.space === 'object' ? Object.values(geom.space) : [geom.space];
        if (!GEOM_SHAPES.includes(geom.shape) || spaces.some((s) => !GEOM_SPACES.includes(s as string)))
        {
            add(issues, loc, 'annotation', `x-geom ${JSON.stringify(geom)} is not in the vocabulary`);
        }
    }
    const kinds = node['x-id-kinds'];
    if (Array.isArray(kinds))
    {
        kinds.filter((k) => !ID_KINDS.includes(k)).forEach((k) => add(issues, loc, 'annotation', `x-id-kinds names an unknown kind ${k}`));
    }
    const key = node['x-key'];
    if (typeof key === 'string' && key !== '#')
    {
        // At a $ref site (a list written once in $defs, keyed where it is used) the items are the target's.
        const list = typeof node.$ref === 'string' ? reg.resolve(loc) : loc;
        const item = list.node.items ? reg.resolve(reg.child(list, 'items')).node : undefined;
        if (!item?.properties?.[key])
        {
            add(issues, loc, 'annotation', `x-key ${key} is no property of the list's items`);
        }
    }
    const xk = node['x-kinds'];
    if (Array.isArray(xk) && disc)
    {
        xk.filter((k) => !disc.values.includes(k)).forEach((k) => add(issues, loc, 'annotation', `x-kinds names ${k}, not a value of ${disc.property}`));
    }
    if (typeof node['x-widget'] === 'string' && !WIDGETS.includes(node['x-widget']))
    {
        add(issues, loc, 'annotation', `x-widget ${node['x-widget']} is not on the bespoke list`);
    }
}

export interface AllowCheck
{
    fresh: LintIssue[];   // issues not in the allow list: the lint fails
    stale: string[];      // allow entries that no longer occur: the lint fails until they are removed
}

export function issueKey(i: LintIssue): string
{
    return `${i.rule} ${i.where}`;
}

export function checkAllowList(issues: LintIssue[], allow: string[]): AllowCheck
{
    const allowed = new Set(allow);
    const found = new Set(issues.map(issueKey));
    return {
        fresh: issues.filter((i) => !allowed.has(issueKey(i))),
        stale: allow.filter((a) => !found.has(a)),
    };
}
