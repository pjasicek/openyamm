// What the form shows for a schema node: pure functions, shared by the React form, the coverage script and the lint.
//
// Annotations read here (all optional; without them the generator falls back as noted):
//   x-unit        number's unit: map | cell | deg | ratio | count | index | texel | gold | angle2048 | seconds |
//                 minutes | days | percent | units_per_second | deg_per_second | per_second | none (lint.ts UNITS), or
//                 {kind: unit, '*': unit} on a discriminated object's polysemous property (without: the number shows
//                 bare)
//   x-geom        {shape, space} or false: the field is edited on the map (without: inline numbers; $refs to
//                 the point/line/polygon defs are recognised by name)
//   x-id-kinds    [kinds] an id field accepts; x-id-own: true for the object's own id (without: any id)
//   x-key         the property naming a list's rows ("id", "wall"), "#" for positional rows, false for lists of
//                 things nobody selects (without: rows are numbered)
//   x-variant     per branch of a union whose branches share a JSON type: {label, when: {present|length|items|type}}
//                 (without: the branch is found by shape, offered as "variant 1, 2"); on an object without a oneOf,
//                 entries that all say {when: {present}} (and `props`) are its implicit choice (a room's outline or
//                 path), read as a presence oneOf would be
//   x-labels      labels per branch of a union told apart by JSON type (without: labels from the types)
//   x-discriminator  {property, default} on an object whose enum property selects which properties apply, with
//                 x-kinds: [values] | "all" on each property (without: every property of every kind is offered);
//                 x-discriminator: false on an object whose kind enum selects no properties
//   x-groups      on an object: [[section, [property, ...]], ...], the sections and their properties in form order
//                 (S5_BROWSER_EDITOR.md 3.8, revision 4); x-group/x-order on a property, the spike's first form, are
//                 still read (without either: one section in schema order)
//   x-widget      one of the short list of bespoke widgets (effects: the event form)
//   x-table       a game table a string names (texture, decoration, house, kit, ...): a picker (without: text)

import { Registry } from '../schema/registry.ts';
import type { Json, Located, Schema } from '../schema/registry.ts';

export type JsonType = 'string' | 'number' | 'boolean' | 'null' | 'array' | 'object';

export interface Geom
{
    shape: string;
    space: string;
}

export type Widget =
    | { kind: 'text'; table?: string; pattern?: string; multiline: boolean }
    | { kind: 'number'; integer: boolean; unit?: string; min?: number; max?: number }
    | { kind: 'boolean' }
    | { kind: 'enum'; options: Json[] }
    | { kind: 'const'; value: Json }
    | { kind: 'id'; kinds?: string[]; own: boolean }
    | { kind: 'geom'; geom: Geom; many: boolean; annotated: boolean }
    | { kind: 'tuple'; items: Located[] }
    | { kind: 'list'; item: Located; key?: string | false; prefix?: string; ofObjects: boolean }
    | { kind: 'map'; value: Located; keys?: string[] }
    | { kind: 'object' }
    | { kind: 'union'; union: UnionPlan }
    | { kind: 'bespoke'; name: string }
    | { kind: 'raw'; reason: string };

export interface UnionBranch
{
    label: string;
    loc: Located;
    types: Set<JsonType>;
    test: (value: Json) => boolean;
}

export interface UnionPlan
{
    // type: told apart by JSON type; const: by a constant property; variant: by x-variant; shape: found by trying the
    // branches (no names to offer); presence: an object's oneOf of `required` lists (handled by the object form)
    mode: 'type' | 'const' | 'variant' | 'shape';
    branches: UnionBranch[];
}

const ID_PATTERN = '^[a-z][a-z0-9_]*:[a-z0-9][a-z0-9_]*$';
const GEOM_REFS: Record<string, Geom> = {
    point: { shape: 'point', space: 'cell' },
    point2: { shape: 'point', space: 'map' },
    point3: { shape: 'point3', space: 'map' },
    line: { shape: 'polyline', space: 'cell' },
    polygon: { shape: 'polygon', space: 'cell' },
};

export function jsonType(value: Json): JsonType
{
    if (value === null)
    {
        return 'null';
    }
    if (Array.isArray(value))
    {
        return 'array';
    }
    return typeof value as JsonType;
}

export function humanise(name: string): string
{
    return name.replace(/_/g, ' ');
}

function typesOf(reg: Registry, loc: Located): Set<JsonType>
{
    const node = reg.resolve(loc).node;
    const out = new Set<JsonType>();
    if ('const' in node)
    {
        out.add(jsonType(node.const));
        return out;
    }
    if (Array.isArray(node.enum))
    {
        node.enum.forEach((v: Json) => out.add(jsonType(v)));
        return out;
    }
    const types: string[] = Array.isArray(node.type) ? node.type : node.type ? [node.type] : [];
    for (const t of types)
    {
        out.add(t === 'integer' ? 'number' : (t as JsonType));
    }
    for (const key of ['oneOf', 'anyOf'])
    {
        if (Array.isArray(node[key]))
        {
            node[key].forEach((_: Schema, i: number) => typesOf(reg, reg.child({ ...loc, node }, key, i)).forEach((t) => out.add(t)));
        }
    }
    if (out.size === 0)
    {
        if (node.properties || node.required)
        {
            out.add('object');
        }
        else if (node.items || node.prefixItems)
        {
            out.add('array');
        }
    }
    return out;
}

// A small structural check, enough to tell union branches apart by shape (the core validates for real).
export function matches(reg: Registry, loc: Located, value: Json): boolean
{
    const node = reg.resolve(loc).node;
    if ('const' in node)
    {
        return JSON.stringify(node.const) === JSON.stringify(value);
    }
    if (Array.isArray(node.enum))
    {
        return node.enum.some((v: Json) => JSON.stringify(v) === JSON.stringify(value));
    }
    for (const key of ['oneOf', 'anyOf'])
    {
        if (Array.isArray(node[key]) && !node[key].some((_: Schema, i: number) => matches(reg, reg.child({ ...loc, node }, key, i), value)))
        {
            return false;
        }
    }
    const types = typesOf(reg, { ...loc, node: { type: node.type } });
    if (node.type && !types.has(jsonType(value)))
    {
        return false;
    }
    if (node.type === 'integer' && !Number.isInteger(value))
    {
        return false;
    }
    if (Array.isArray(node.required) && (jsonType(value) !== 'object' || !node.required.every((k: string) => k in (value as object))))
    {
        return false;
    }
    if (Array.isArray(value))
    {
        if (node.minItems !== undefined && value.length < node.minItems)
        {
            return false;
        }
        if (node.maxItems !== undefined && value.length > node.maxItems)
        {
            return false;
        }
        if (node.items && !value.every((v) => matches(reg, reg.child({ ...loc, node }, 'items'), v)))
        {
            return false;
        }
    }
    return true;
}

function typeLabel(types: Set<JsonType>, node: Schema): string
{
    if ('const' in node)
    {
        return node.const === false ? 'none' : String(node.const);
    }
    if (Array.isArray(node.enum))
    {
        return node.enum.length <= 2 ? node.enum.join(' / ') : 'word';
    }
    const t = [...types][0];
    if (t === 'number')
    {
        return node.type === 'integer' ? 'number' : 'value';
    }
    return { string: 'name', boolean: 'yes/no', null: 'nothing', array: 'list', object: 'details' }[t as string] ?? t;
}

export function isPresenceUnion(node: Schema, key: 'oneOf' | 'anyOf'): boolean
{
    return Array.isArray(node[key]) && node[key].every((b: Schema) => Object.keys(b).every((k) => k === 'required'));
}

// An object's implicit choice written as x-variant alone (no oneOf): every entry selected by a present property.
export function isPresenceVariant(node: Schema): boolean
{
    const variants = node['x-variant'];
    return Array.isArray(variants) && variants.length > 0 && !node.oneOf && !node.anyOf && !Array.isArray(node.type)
        && node.properties !== undefined && variants.every((v: Schema) => typeof v?.when?.present === 'string');
}

export function planUnion(reg: Registry, loc: Located): UnionPlan | undefined
{
    const node = reg.resolve(loc).node;
    const resolved: Located = { ...reg.resolve(loc) };
    let branchLocs: Located[] = [];
    if (Array.isArray(node.type) && node.type.length > 1)
    {
        branchLocs = node.type.map((t: string) => ({ node: { ...node, type: t }, file: resolved.file, ptr: resolved.ptr + `/type/${t}` }));
    }
    else
    {
        const key = Array.isArray(node.oneOf) && !isPresenceUnion(node, 'oneOf') ? 'oneOf'
            : Array.isArray(node.anyOf) && !isPresenceUnion(node, 'anyOf') ? 'anyOf' : undefined;
        if (!key)
        {
            return undefined;
        }
        branchLocs = node[key].map((_: Schema, i: number) => reg.child(resolved, key, i));
    }
    const typeSets = branchLocs.map((b) => typesOf(reg, b));
    const disjoint = typeSets.every((a, i) => typeSets.every((b, j) => i === j || [...a].every((t) => !b.has(t))));
    const variants: Schema[] | undefined = node['x-variant'];
    const labels: string[] | undefined = node['x-labels'];
    if (disjoint)
    {
        return {
            mode: 'type',
            branches: branchLocs.map((b, i) => ({
                label: labels?.[i] ?? variants?.[i]?.label ?? typeLabel(typeSets[i], reg.resolve(b).node),
                loc: b,
                types: typeSets[i],
                test: (v: Json) => typeSets[i].has(jsonType(v)),
            })),
        };
    }
    if (Array.isArray(variants) && variants.length === branchLocs.length)
    {
        return {
            mode: 'variant',
            branches: branchLocs.map((b, i) => ({
                label: variants[i].label,
                loc: b,
                types: typeSets[i],
                test: (v: Json) => whenHolds(variants[i].when, v) ?? matches(reg, b, v),
            })),
        };
    }
    const constKey = commonConstKey(reg, branchLocs);
    if (constKey)
    {
        return {
            mode: 'const',
            branches: branchLocs.map((b, i) => {
                const c = reg.resolve(reg.child(reg.resolve(b), 'properties', constKey)).node.const;
                return {
                    label: String(c),
                    loc: b,
                    types: typeSets[i],
                    test: (v: Json) => jsonType(v) === 'object' && (v as Record<string, Json>)[constKey] === c,
                };
            }),
        };
    }
    return {
        mode: 'shape',
        branches: branchLocs.map((b, i) => ({
            label: `variant ${i + 1}`,
            loc: b,
            types: typeSets[i],
            test: (v: Json) => matches(reg, b, v),
        })),
    };
}

function whenHolds(when: Schema | undefined, value: Json): boolean | undefined
{
    if (!when)
    {
        return undefined;
    }
    if (when.present !== undefined)
    {
        return jsonType(value) === 'object' && when.present in (value as object);
    }
    if (when.length !== undefined)
    {
        return Array.isArray(value) && value.length === when.length;
    }
    if (when.items !== undefined)
    {
        return Array.isArray(value) && value.length > 0 && jsonType(value[0]) === when.items;
    }
    if (when.type !== undefined)
    {
        return jsonType(value) === when.type;
    }
    return undefined;
}

function commonConstKey(reg: Registry, branches: Located[]): string | undefined
{
    const props = branches.map((b) => reg.resolve(b).node.properties ?? {});
    const first = Object.keys(props[0] ?? {});
    return first.find((k) => props.every((p: Schema) => p[k] && 'const' in reg.resolve({ node: p[k], file: branches[0].file, ptr: '' }).node));
}

export function geomOf(reg: Registry, loc: Located): Geom | false | undefined
{
    const node = reg.resolve(loc).node;
    if (node['x-geom'] !== undefined)
    {
        return node['x-geom'];
    }
    const name = reg.refName(loc);
    if (name && GEOM_REFS[name])
    {
        return GEOM_REFS[name];
    }
    if (node.type === 'array' && node.items)
    {
        const itemName = reg.refName(reg.child(reg.resolve(loc), 'items'));
        if (itemName === 'point2' || itemName === 'point')
        {
            return { shape: 'polyline', space: itemName === 'point' ? 'cell' : 'map' };
        }
        if (itemName === 'point3')
        {
            return { shape: 'points3', space: 'map' };
        }
    }
    return undefined;
}

export function classify(reg: Registry, loc: Located): Widget
{
    const resolved = reg.resolve(loc);
    const node = resolved.node;
    if (typeof node['x-widget'] === 'string')
    {
        return { kind: 'bespoke', name: node['x-widget'] };
    }
    const union = planUnion(reg, loc);
    if (union)
    {
        return { kind: 'union', union };
    }
    if (reg.refName(loc) === 'id' || (node.type === 'string' && node.pattern === ID_PATTERN))
    {
        return { kind: 'id', kinds: node['x-id-kinds'], own: node['x-id-own'] === true };
    }
    const geom = geomOf(reg, loc);
    if (geom)
    {
        return { kind: 'geom', geom, many: !['point', 'point3', 'size'].includes(geom.shape), annotated: node['x-geom'] !== undefined };
    }
    if ('const' in node)
    {
        return { kind: 'const', value: node.const };
    }
    if (Array.isArray(node.enum))
    {
        return { kind: 'enum', options: node.enum };
    }
    switch (node.type)
    {
    case 'string':
        return { kind: 'text', table: node['x-table'], pattern: node.pattern, multiline: /lua|notes|text/.test(loc.ptr.split('/').pop() ?? '') };
    case 'number':
    case 'integer':
        return { kind: 'number', integer: node.type === 'integer', unit: node['x-unit'], min: node.minimum, max: node.maximum };
    case 'boolean':
        return { kind: 'boolean' };
    case 'array':
    {
        if (Array.isArray(node.prefixItems))
        {
            return { kind: 'tuple', items: node.prefixItems.map((_: Schema, i: number) => reg.child(resolved, 'prefixItems', i)) };
        }
        if (!node.items)
        {
            return { kind: 'raw', reason: 'array without items' };
        }
        const item = reg.child(resolved, 'items');
        const itemNode = reg.resolve(item).node;
        const scalar = ['number', 'integer'].includes(itemNode.type);
        if (scalar && node.minItems !== undefined && node.minItems === node.maxItems && node.minItems <= 4)
        {
            return { kind: 'tuple', items: Array.from({ length: node.minItems }, () => item) };
        }
        const ofObjects = typesOf(reg, item).has('object') && !planUnion(reg, item);
        return { kind: 'list', item, key: node['x-key'], ...(typeof node['x-key-prefix'] === 'string' ? { prefix: node['x-key-prefix'] } : {}), ofObjects };
    }
    case 'object':
        if (node.properties)
        {
            return { kind: 'object' };
        }
        if (node.additionalProperties && typeof node.additionalProperties === 'object')
        {
            const keys = node.propertyNames?.enum ?? node['x-keys'];
            return { kind: 'map', value: reg.child(resolved, 'additionalProperties'), keys };
        }
        return { kind: 'raw', reason: 'object without properties' };
    default:
        if (node.properties)
        {
            return { kind: 'object' };
        }
        return { kind: 'raw', reason: node.type ? `type ${node.type}` : 'no type' };
    }
}

export interface FieldEntry
{
    name: string;
    loc: Located;
    required: boolean;
    present: boolean;
    group: string;
    order: number;
    description: string;
    kinds?: string[] | 'all';
}

export interface ObjectPlan
{
    discriminator?: { property: string; value: Json; options: Json[] };
    variant?: { labels: string[]; props: string[][]; active: number; when: string[] };
    groups: { name: string; fields: FieldEntry[] }[];
    addable: FieldEntry[];
    hiddenByKind: number;
    unknown: string[];
}

export function planObject(reg: Registry, loc: Located, value: Record<string, Json>, allVariants = false, allKinds = false): ObjectPlan
{
    const resolved = reg.resolve(loc);
    const node = resolved.node;
    const props: Schema = node.properties ?? {};
    const required = new Set<string>(node.required ?? []);
    const plan: ObjectPlan = { groups: [], addable: [], hiddenByKind: 0, unknown: [] };

    const disc = node['x-discriminator'];
    let kindValue: Json | undefined;
    if (disc)
    {
        const propLoc = reg.child(resolved, 'properties', disc.property);
        kindValue = value[disc.property] ?? disc.default;
        plan.discriminator = { property: disc.property, value: kindValue ?? null, options: reg.resolve(propLoc).node.enum ?? [] };
    }

    // An object whose oneOf is `required` lists: the variant is the branch whose property is present.
    let hidden = new Set<string>();
    const variants: Schema[] | undefined = node['x-variant'];
    const presence = Array.isArray(node.oneOf) && isPresenceUnion(node, 'oneOf') ? node.oneOf
        : isPresenceVariant(node) ? variants!.map((v: Schema) => ({ required: [v.when.present] })) : undefined;
    if (presence)
    {
        const when = presence.map((b: Schema) => b.required[0]);
        const active = Math.max(0, when.findIndex((p: string) => p in value));
        const labels = presence.map((b: Schema, i: number) => variants?.[i]?.label ?? `with ${b.required.join(', ')}`);
        const branchProps: string[][] = presence.map((b: Schema, i: number) => variants?.[i]?.props ?? b.required);
        plan.variant = { labels, props: branchProps, active, when };
        branchProps.forEach((ps, i) => {
            if (i !== active)
            {
                ps.forEach((p) => hidden.add(p));
            }
        });
        branchProps[active].forEach((p) => hidden.delete(p));
    }

    // Sections per object (x-groups) first; a property in none falls back to its own x-group/x-order.
    const sectionOf = new Map<string, { group: string; order: number }>();
    if (Array.isArray(node['x-groups']))
    {
        let order = 0;
        for (const [section, names] of node['x-groups'] as [string, string[]][])
        {
            for (const name of names)
            {
                sectionOf.set(name, { group: section, order: order++ });
            }
        }
    }
    const entries: FieldEntry[] = Object.keys(props).map((name, index) => {
        const propLoc = reg.child(resolved, 'properties', name);
        const propNode = propLoc.node;
        const section = sectionOf.get(name);
        return {
            name,
            loc: propLoc,
            required: required.has(name),
            present: name in value,
            group: section?.group ?? propNode['x-group'] ?? '',
            order: section?.order ?? propNode['x-order'] ?? 1000 + index,
            description: propNode.description ?? reg.resolve(propLoc).node.description ?? '',
            kinds: propNode['x-kinds'],
        };
    });
    const applicable = entries.filter((e) => {
        if (hidden.has(e.name) && !e.present && !allVariants)
        {
            return false;
        }
        if (disc && !allKinds && kindValue !== undefined && Array.isArray(e.kinds) && !e.kinds.includes(kindValue as string) && !e.present)
        {
            plan.hiddenByKind += 1;
            return false;
        }
        return true;
    });
    applicable.sort((a, b) => a.order - b.order);
    const groupOrder: string[] = [];
    for (const e of applicable)
    {
        if (!groupOrder.includes(e.group))
        {
            groupOrder.push(e.group);
        }
    }
    for (const name of groupOrder)
    {
        const fields = applicable.filter((e) => e.group === name && (e.present || e.required));
        if (fields.length > 0)
        {
            plan.groups.push({ name, fields });
        }
    }
    plan.addable = applicable.filter((e) => !e.present && !e.required);
    plan.unknown = Object.keys(value).filter((k) => !(k in props));
    return plan;
}

// A new value for a schema node: what "+ add field" and a branch switch put in.
export function makeDefault(reg: Registry, loc: Located): Json
{
    const node = reg.resolve(loc).node;
    if ('const' in node)
    {
        return node.const;
    }
    if (Array.isArray(node.enum))
    {
        return node.enum[0];
    }
    if (node.default !== undefined)
    {
        return node.default;
    }
    const union = planUnion(reg, loc);
    if (union)
    {
        return makeDefault(reg, union.branches[0].loc);
    }
    const type = Array.isArray(node.type) ? node.type[0] : node.type;
    switch (type)
    {
    case 'string':
        return '';
    case 'number':
    case 'integer':
        return node.minimum ?? 0;
    case 'boolean':
        return false;
    case 'array':
    {
        if (Array.isArray(node.prefixItems))
        {
            return node.prefixItems.map((_: Schema, i: number) => makeDefault(reg, reg.child(reg.resolve(loc), 'prefixItems', i)));
        }
        const n = node.minItems ?? 0;
        return Array.from({ length: n }, () => makeDefault(reg, reg.child(reg.resolve(loc), 'items')));
    }
    default:
    {
        const out: Record<string, Json> = {};
        for (const r of node.required ?? [])
        {
            out[r] = makeDefault(reg, reg.child(reg.resolve(loc), 'properties', r));
        }
        return out;
    }
    }
}

// Arithmetic in number fields: 512*3, (1024 - 64) / 2. Returns undefined when the text is no expression.
export function evaluate(text: string): number | undefined
{
    const tokens = text.match(/\d+(?:\.\d+)?|\.\d+|[-+*/()]/g);
    if (!tokens || tokens.join('') !== text.replace(/\s+/g, ''))
    {
        return undefined;
    }
    let i = 0;
    const peek = () => tokens[i];
    const expr = (): number => {
        let v = term();
        while (peek() === '+' || peek() === '-')
        {
            v = tokens[i++] === '+' ? v + term() : v - term();
        }
        return v;
    };
    const term = (): number => {
        let v = factor();
        while (peek() === '*' || peek() === '/')
        {
            v = tokens[i++] === '*' ? v * factor() : v / factor();
        }
        return v;
    };
    const factor = (): number => {
        const t = tokens[i++];
        if (t === '-')
        {
            return -factor();
        }
        if (t === '(')
        {
            const v = expr();
            if (tokens[i++] !== ')')
            {
                throw new Error('missing )');
            }
            return v;
        }
        const n = Number(t);
        if (Number.isNaN(n))
        {
            throw new Error('not a number');
        }
        return n;
    };
    try
    {
        const v = expr();
        return i === tokens.length && Number.isFinite(v) ? v : undefined;
    }
    catch
    {
        return undefined;
    }
}

export const UNIT_LABELS: Record<string, string> = {
    map: 'units',
    cell: 'cells',
    deg: '°',
    ratio: '×',
    count: '',
    index: '#',
    texel: 'texels',
    gold: 'gold',
    angle2048: '/2048',
    seconds: 's',
    minutes: 'min',
    days: 'days',
    percent: '%',
    units_per_second: 'units/s',
    deg_per_second: '°/s',
    per_second: '/s',
    none: '',
};

// Whether a field holds geometry by its shape (a fixed pair or triple of numbers, a list of such): what needs an
// x-geom (or x-geom: false) in the lint (spike 7's census).
export function looksGeometric(reg: Registry, loc: Located): boolean
{
    const node = reg.resolve(loc).node;
    if (geomOf(reg, loc))
    {
        return true;
    }
    if (node.type !== 'array' || !node.items)
    {
        return false;
    }
    const item = reg.resolve(reg.child(reg.resolve(loc), 'items')).node;
    const numeric = (t: unknown) => t === 'number' || t === 'integer';
    if (numeric(item.type) && node.minItems !== undefined && node.minItems === node.maxItems && node.minItems >= 2 && node.minItems <= 3)
    {
        return true;
    }
    if (item.type === 'array' && item.items && numeric(reg.resolve(reg.child(reg.resolve(reg.child(reg.resolve(loc), 'items')), 'items')).node.type))
    {
        return true;
    }
    return false;
}
