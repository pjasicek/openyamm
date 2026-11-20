// The project schemas (openyamm-studio/schema/*.schema.json) as one registry for the generated inspector. Loaded
// on first use: the sketch schema alone is 370 KB.
import { Registry } from './registry.ts';
import type { Located, Schema } from './registry.ts';

const modules = import.meta.glob<{ default: Schema }>('../../../schema/*.schema.json');

let loading: Promise<Registry> | null = null;

export function loadRegistry(): Promise<Registry>
{
    loading ??= (async () =>
    {
        const files: Record<string, Schema> = {};
        await Promise.all(Object.entries(modules).map(async ([path, load]) =>
        {
            files[path.split('/').pop()!] = (await load()).default;
        }));
        return new Registry(files);
    })();
    return loading;
}

// The schema of a file's list item (rooms.yml rooms -> rooms.schema.json#/properties/rooms/items).
export function itemSchema(reg: Registry, file: string, list: string): Located | undefined
{
    const schemaFile = file.replace(/^review\//, '').replace(/\.yml$/, '').replace('ids.lock', 'ids_lock') + '.schema.json';
    if (!reg.files[schemaFile]?.properties?.[list]?.items)
    {
        return undefined;
    }
    return reg.at(schemaFile, `#/properties/${list}/items`);
}

// The schema of a node by its place in a file ('/structures/*/parts/*', '/heights/ridges/*'): properties by name, `*`
// a list's items, through $ref and the branches of a union (the first that has the property).
export function schemaAtPlace(reg: Registry, file: string, place: string): Located | undefined
{
    const schemaFile = file.replace(/^review\//, '').replace(/\.yml$/, '').replace('ids.lock', 'ids_lock') + '.schema.json';
    if (!reg.files[schemaFile])
    {
        return undefined;
    }
    let loc: Located = reg.at(schemaFile, '#');
    for (const part of place.split('/').filter((entry) => entry.length > 0))
    {
        const found = childAt(reg, loc, part);
        if (!found)
        {
            return undefined;
        }
        loc = found;
    }
    return loc;
}

function childAt(reg: Registry, loc: Located, part: string): Located | undefined
{
    const resolved = reg.resolve(loc);
    const node = resolved.node;
    if (part === '*')
    {
        return node.items && typeof node.items === 'object' ? reg.child(resolved, 'items') : undefined;
    }
    if (node.properties?.[part])
    {
        return reg.child(resolved, 'properties', part);
    }
    for (const key of ['allOf', 'oneOf', 'anyOf'] as const)
    {
        const branches = node[key];
        if (Array.isArray(branches))
        {
            for (let index = 0; index < branches.length; ++index)
            {
                const found = childAt(reg, reg.child(resolved, key, index), part);
                if (found)
                {
                    return found;
                }
            }
        }
    }
    return undefined;
}
