// The real schemas from disk, for the lint's test and script (Node only).
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { Registry } from '../schema/registry.ts';
import type { Schema } from '../schema/registry.ts';

export const schemaDir = join(import.meta.dirname, '..', '..', '..', 'schema');
export const allowPath = join(import.meta.dirname, 'allow.json');

export function loadSchemas(dir = schemaDir): Registry
{
    const files: Record<string, Schema> = {};
    for (const name of readdirSync(dir).filter((n) => n.endsWith('.schema.json')).sort())
    {
        files[name] = JSON.parse(readFileSync(join(dir, name), 'utf8'));
    }
    return new Registry(files);
}
