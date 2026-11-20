import { createContext, useContext } from 'react';
import { Registry } from '../schema/registry.ts';
import type { Json } from '../schema/registry.ts';

export type Path = (string | number)[];

// What the editable inspector emits (S5b1, Author mode): each a transaction, sent when a field is committed (Enter
// or leaving it), a row is added, removed, duplicated or moved, or a key renamed. Paths are relative to the shown
// object.
export interface FormEdits
{
    field(path: Path, value: Json | undefined): void;
    addRow(path: Path, value: Json): void;
    row(path: Path, index: number, action: 'remove' | 'duplicate' | 'up' | 'down'): void;
    renameKey(path: Path, index: number, to: string): void;
    // The shown object's own name renamed by op rename: a top-level object's `id` (every reference, the id lock and
    // the pins follow) or a sub-object's `key` (its pins and selection follow).
    rename?: { field: 'id' | 'key'; to(name: string): void };
}

// What the core says an absent field of the shown object takes (project.resolve): its value and where it comes from.
export type Resolved = Record<string, { value: Json; source: string; from?: string }>;

// What every field of the generated inspector reads (S5_BROWSER_EDITOR.md 3.8). In Review mode nothing emits.
export interface FormContextValue
{
    reg: Registry;
    // The project's ids, for links that select and for the id pickers.
    ids: Set<string>;
    // The root object's discriminator value (for per-kind units).
    kind?: string;
    expandAll: boolean;
    onSelectId: (id: string) => void;
    // Author mode: the edits (absent in Review mode).
    edits?: FormEdits;
    // The shown object's effective values, when the core gives them.
    resolved?: Resolved;
}

export const FormContext = createContext<FormContextValue | null>(null);

export function useForm(): FormContextValue
{
    const ctx = useContext(FormContext);
    if (!ctx)
    {
        throw new Error('no form context');
    }
    return ctx;
}

// The unit of a number: per-kind maps ({building: cell, '*': map}) read with the root's kind.
export function unitFor(unit: unknown, kind?: string): string | undefined
{
    if (unit && typeof unit === 'object')
    {
        const map = unit as Record<string, string>;
        return (kind && map[kind]) ?? map['*'];
    }
    return unit as string | undefined;
}
