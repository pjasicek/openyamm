// The map's variables (wiring.yml `variables`, S5_BROWSER_EDITOR.md 3.18 "wiring event"): the names presets and
// steps use as {map_var: name}. Shown with the switch board (the Wire stage) and the event form's pickers: add one,
// rename one (the events that name it follow, in the same transaction), take one out. Each change is one transaction
// of the file's list.
import { useState } from 'react';
import type { FileTrees, JsonObject, JsonValue, Op } from '../../../schema/rpc/generated/rpc.ts';
import { useActions, useS } from './context.ts';
import css from './Board.module.css';

export function variablesOf(files: FileTrees | undefined): string[]
{
    const value = files?.['wiring.yml']?.tree.variables;
    return Array.isArray(value) ? value.filter((entry): entry is string => typeof entry === 'string') : [];
}

const NAME = /^[a-z][a-z0-9_]*$/;

// A value with every {map_var: from} (and {name: from} under map_var) renamed; whether anything changed.
function renamed(value: JsonValue, from: string, to: string): { value: JsonValue; changed: boolean }
{
    if (Array.isArray(value))
    {
        let changed = false;
        const out = value.map((item) =>
        {
            const made = renamed(item, from, to);
            changed = changed || made.changed;
            return made.value;
        });
        return { value: out, changed };
    }
    if (typeof value === 'object' && value !== null)
    {
        let changed = false;
        const out: JsonObject = {};
        for (const [key, item] of Object.entries(value))
        {
            if (key === 'map_var' && item === from)
            {
                out[key] = to;
                changed = true;
            }
            else if (key === 'map_var' && typeof item === 'object' && item !== null && !Array.isArray(item) && item.name === from)
            {
                out[key] = { ...item, name: to };
                changed = true;
            }
            else if (key === 'lua' && typeof item === 'string' && item.includes(`MapVar(${from})`))
            {
                out[key] = item.split(`MapVar(${from})`).join(`MapVar(${to})`);
                changed = true;
            }
            else
            {
                const made = renamed(item, from, to);
                out[key] = made.value;
                changed = changed || made.changed;
            }
        }
        return { value: out, changed };
    }
    return { value, changed: false };
}

// The operations of a rename: the list's entry and every event that names the variable.
export function renameVariableOps(files: FileTrees | undefined, from: string, to: string): Op[]
{
    const names = variablesOf(files);
    const index = names.indexOf(from);
    if (index < 0)
    {
        return [];
    }
    const ops: Op[] = [{ op: 'patch', file: 'wiring.yml', patch: [{ op: 'test', path: `/variables/${index}`, value: from }, { op: 'replace', path: `/variables/${index}`, value: to }] }];
    const events = files?.['wiring.yml']?.tree.events;
    for (const event of Array.isArray(events) ? events : [])
    {
        if (typeof event !== 'object' || event === null || Array.isArray(event) || typeof event.id !== 'string')
        {
            continue;
        }
        const made = renamed(event, from, to);
        if (made.changed)
        {
            const { id, ...rest } = made.value as JsonObject;
            ops.push({ op: 'replace', id: String(id), file: 'wiring.yml', value: rest });
        }
    }
    return ops;
}

export function addVariableOp(files: FileTrees | undefined, name: string): Op
{
    return Array.isArray(files?.['wiring.yml']?.tree.variables)
        ? { op: 'patch', file: 'wiring.yml', patch: [{ op: 'add', path: '/variables/-', value: name }] }
        : { op: 'patch', file: 'wiring.yml', patch: [{ op: 'add', path: '/variables', value: [name] }] };
}

export function VariablesPanel()
{
    const actions = useActions();
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const author = useS((s) => s.mode === 'author');
    const names = variablesOf(files);
    const [adding, setAdding] = useState('');
    const [editing, setEditing] = useState<{ from: string; to: string } | null>(null);
    const add = () =>
    {
        const name = adding.trim();
        if (!NAME.test(name))
        {
            actions.notify('A variable\'s name is lower case letters, digits and _, starting with a letter');
            return;
        }
        if (names.includes(name))
        {
            actions.notify(`${name} is declared already`);
            return;
        }
        void actions.edit({ label: `variable ${name}`, ops: [addVariableOp(files, name)] }).then((result) => result && setAdding(''));
    };
    const rename = () =>
    {
        if (!editing)
        {
            return;
        }
        const to = editing.to.trim();
        setEditing(null);
        if (to === editing.from)
        {
            return;
        }
        if (!NAME.test(to) || names.includes(to))
        {
            actions.notify(`${to} is not a free variable name`);
            return;
        }
        void actions.edit({ label: `rename variable ${editing.from} to ${to}`, ops: renameVariableOps(files, editing.from, to) });
    };
    const remove = (name: string) =>
    {
        const index = names.indexOf(name);
        void actions.edit({ label: `remove variable ${name}`, ops: [{ op: 'patch', file: 'wiring.yml', patch: names.length > 1
            ? [{ op: 'test', path: `/variables/${index}`, value: name }, { op: 'remove', path: `/variables/${index}` }]
            : [{ op: 'remove', path: '/variables' }] }] });
    };
    return (
        <div className={css.variables} data-testid="variables">
            <b>Map variables</b>
            <span className={css.dim}>names events test and set ({'{map_var: name}'}): the build gives each a number of the map's 75</span>
            {names.map((name) => editing?.from === name ? (
                <input key={name} className={css.variableInput} value={editing.to} autoFocus data-testid={`variable-edit-${name}`}
                    onChange={(event) => setEditing({ from: name, to: event.target.value })}
                    onKeyDown={(event) => { if (event.key === 'Enter') { rename(); } else if (event.key === 'Escape') { setEditing(null); } }}
                    onBlur={rename} />
            ) : (
                <span key={name} className={css.variable} data-testid={`variable-${name}`}>
                    <button type="button" className={css.variableName} disabled={!author} title="Rename it (the events that name it follow)"
                        onClick={() => setEditing({ from: name, to: name })}>{name}</button>
                    {author ? <button type="button" className={css.variableX} title={`take ${name} out`} onClick={() => remove(name)}>×</button> : null}
                </span>
            ))}
            {author ? (
                <>
                    <input className={css.variableInput} value={adding} placeholder="new_variable" data-testid="variable-new"
                        onChange={(event) => setAdding(event.target.value)} onKeyDown={(event) => { if (event.key === 'Enter') { add(); } }} />
                    <button type="button" className={css.variableAdd} onClick={add} data-testid="variable-add">+ variable</button>
                </>
            ) : null}
        </div>
    );
}
