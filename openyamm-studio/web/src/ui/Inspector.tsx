// The inspector (S5_BROWSER_EDITOR.md 3.8): the selected object's Properties from the schemas, its Source as YAML
// (CodeMirror 6), its own issues, its notes. Read only in Review mode; in Author mode (S5b1) Properties edit, each
// committed field one transaction, and the Source tab's Apply replaces the whole object. A keyed sub-object
// (room:hall/pillars/pillar2) shows its own form. Connections and Original come later.
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react';
import { Tabs } from '@base-ui/react/tabs';
import { Switch } from '@base-ui/react/switch';
import { Document, isSeq, isScalar, parse as parseYaml, visit } from 'yaml';
import { EditorState } from '@codemirror/state';
import { EditorView, lineNumbers } from '@codemirror/view';
import { yaml } from '@codemirror/lang-yaml';
import { HighlightStyle, syntaxHighlighting } from '@codemirror/language';
import { tags } from '@lezer/highlight';
import type { ProjectResolveResult } from '../../../schema/rpc/generated/rpc.ts';
import type { Registry } from '../schema/registry.ts';
import type { Json } from '../schema/registry.ts';
import { itemSchema, loadRegistry, schemaAtPlace } from '../schema/schemas.ts';
import { FormContext } from '../form/context.ts';
import type { FormEdits, Resolved } from '../form/context.ts';
import { ObjectForm } from '../form/Fields.tsx';
import { findAddress, issueObject } from '../model/objects.ts';
import { addRowOp, fieldOp, renameKeyOp, replaceOp, rowOp } from '../edit/formops.ts';
import type { Target } from '../edit/formops.ts';
import type { FileName, JsonObject, Op } from '../../../schema/rpc/generated/rpc.ts';
import type { Actions } from '../app/controller.ts';
import type { FoundObject } from '../model/objects.ts';
import { knownIssues, NONE } from '../state/store.ts';
import type { InspectorTab } from '../state/store.ts';
import { probe } from '../app/controller.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import { EventForm, SourceEvents } from './EventForm.tsx';
import { OutdoorEventForm, OutdoorPanels } from './OutdoorInspector.tsx';
import css from './Inspector.module.css';

export function Inspector()
{
    const { store } = useStudioContext();
    const tab = useS((s) => s.inspectorTab);
    const selection = useS((s) => s.selection);
    const project = useS((s) => s.project);
    const author = useS((s) => s.mode === 'author');
    const found = useMemo(() => (project.state === 'ready' && selection
        ? findAddress(project.value.files, project.value.ids, selection) : undefined), [project, selection]);
    return (
        <aside className={css.inspector}>
            <Tabs.Root className={css.tabsRoot} value={tab} onValueChange={(value) => store.setState({ inspectorTab: value as InspectorTab })}>
                <Tabs.List className={css.tabs}>
                    <Tabs.Tab className={css.tab} value="properties">Properties</Tabs.Tab>
                    <Tabs.Tab className={css.tab} value="source">Source</Tabs.Tab>
                    <Tabs.Tab className={css.tab} value="issues">Issues</Tabs.Tab>
                    <Tabs.Tab className={css.tab} value="notes">Notes</Tabs.Tab>
                    <Tabs.Tab className={css.tab} value="connections">Connections</Tabs.Tab>
                    <Tabs.Tab className={css.tab} value="original">Original</Tabs.Tab>
                </Tabs.List>
                <Header found={found} selectionId={selection?.id} />
                <Tabs.Panel className={css.panel} value="properties">{found ? <Properties found={found} /> : author ? <FileProperties /> : <Nothing />}</Tabs.Panel>
                <Tabs.Panel className={css.panel} value="source">{found ? <SourceTab found={found} /> : <Nothing />}</Tabs.Panel>
                <Tabs.Panel className={css.panel} value="issues">{found ? <ObjectIssues found={found} /> : <Nothing />}</Tabs.Panel>
                <Tabs.Panel className={css.panel} value="notes">
                    {found ? <p className={css.notes}>{typeof found.value.notes === 'string' ? found.value.notes : 'No notes on this object.'}</p> : <Nothing />}
                </Tabs.Panel>
                <Tabs.Panel className={css.panel} value="connections"><p className={css.dim}>What drives this object and what it drives: S5a5 (from the flow) and S5b1.</p></Tabs.Panel>
                <Tabs.Panel className={css.panel} value="original"><p className={css.dim}>The original map's matching record: S5a5 (Compare).</p></Tabs.Panel>
            </Tabs.Root>
        </aside>
    );
}

function Header({ found, selectionId }: { found?: FoundObject; selectionId?: string })
{
    if (!selectionId)
    {
        return null;
    }
    // A sketch word without an id is named by its pointer (/heights/ridges/ridge2).
    const parts = selectionId.replace(/^\//, '').split('/');
    return (
        <div className={css.header}>
            <span className={css.id}>{parts.length > 1 ? `${parts[0]} › ${parts.slice(1).join(' › ')}` : selectionId}</span>
            {found ? <span className={css.dim}>{found.file} · {found.parentList ? `${found.parentList} › ` : ''}{found.list}[{found.index}]</span> : <span className={css.dim}>not an object of the project's files</span>}
        </div>
    );
}

// With nothing selected in Author mode: a file's own words in the generated form (S5_BROWSER_EDITOR.md 3.18: the plan's
// keys, height bands and states, "the inspector on project.yml" for the map card, wiring.yml's variables, rooms.yml's
// defaults). Lists of objects with ids add rows by op add (the core gives the id).
const FILE_FORMS: { file: FileName; label: string }[] = [
    { file: 'plan.yml', label: 'the plan' }, { file: 'project.yml', label: 'the map card' }, { file: 'wiring.yml', label: 'the wiring' },
    { file: 'rooms.yml', label: 'rooms\' defaults' },
];
// Outdoors (S5b2): the plan's zones and links, the map card, the sketch's own words (the frame, the grid, the land's
// mark) and the atmosphere.
const OUTDOOR_FILE_FORMS: { file: FileName; label: string }[] = [
    { file: 'plan.yml', label: 'the plan' }, { file: 'project.yml', label: 'the map card' }, { file: 'sketch.yml', label: 'the sketch' },
    { file: 'atmosphere.yml', label: 'the atmosphere' },
];

function FileProperties()
{
    const actions = useActions();
    const stage = useS((s) => s.stage);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const [registry, setRegistry] = useState<Registry | null>(null);
    const [chosen, setChosen] = useState<FileName | null>(null);
    useEffect(() => { void loadRegistry().then(setRegistry); }, []);
    const outdoor = Boolean(files?.['sketch.yml']) && !files?.['rooms.yml'];
    const forms = outdoor ? OUTDOOR_FILE_FORMS : FILE_FORMS;
    const file: FileName = chosen && forms.some((entry) => entry.file === chosen) ? chosen
        : stage === 1 ? 'plan.yml' : outdoor ? (stage === 6 ? 'atmosphere.yml' : stage === 2 ? 'sketch.yml' : 'project.yml') : stage === 4 ? 'wiring.yml' : 'project.yml';
    const tree = (files?.[file]?.tree ?? { format: 0 }) as JsonObject;
    const edits = useMemo<FormEdits>(() =>
    {
        const target: Target = { id: '', file, pointer: '', value: tree };
        const send = (op: Op | null, label: string) => { if (op) { void actions.edit({ label, ops: [op] }); } };
        return {
            field: (path, value) => send(fieldOp(target, path, value), `${value === undefined ? 'remove' : 'set'} ${path.filter((step) => typeof step === 'string').join('.')} of ${file}`),
            addRow: (path, value) => send(addRowOp(target, path, value), `add to ${String(path.at(-1))} of ${file}`),
            row: (path, index, action) => send(rowOp(target, path, index, action), `${action} a row of ${String(path.at(-1))} of ${file}`),
            renameKey: (path, index, to) => send(renameKeyOp(target, path, index, to), `rename a key in ${file} to ${to}`),
        };
    }, [actions, file, tree]);
    const ids = useS((s) => (s.project.state === 'ready' ? s.project.value.ids : NONE));
    const idSet = useMemo(() => new Set(ids.map((place) => place.id)), [ids]);
    if (!registry)
    {
        return <p className={css.dim}>Reading the schemas…</p>;
    }
    const loc = registry.at(file.replace(/\.yml$/, '') + '.schema.json', '#');
    return (
        <div className={css.form} data-testid="file-form">
            <p className={css.dim}>Nothing selected: the words of
                <select className={css.fileSelect} value={file} data-testid="file-form-file" onChange={(event) => setChosen(event.target.value as FileName)}>
                    {forms.map((entry) => <option key={entry.file} value={entry.file}>{entry.file} ({entry.label})</option>)}
                </select>
                (each field is written on Enter or when you leave it).</p>
            <FormContext.Provider value={{ reg: registry, ids: idSet, kind: undefined, expandAll: false, onSelectId: (id) => actions.select({ id }, true), edits }}>
                <ObjectForm key={file} loc={loc} value={tree as Record<string, Json>} path={[]} />
            </FormContext.Provider>
        </div>
    );
}

function Nothing()
{
    return <p className={css.dim}>Select an object in the plan, the 3D view, the outline or by search (Ctrl P).</p>;
}

// The shown object as the inspector's operations address it.
function targetOf(found: FoundObject): Target
{
    // A sketch word without an id is addressed by its pointer in the file (its id is then empty).
    return { id: found.id.startsWith('/') ? '' : found.id.split('/')[0], file: found.file, pointer: found.pointer ?? '', value: found.value as JsonObject,
        ...(found.place !== undefined ? { place: found.place } : {}) };
}

// Each edit of the form is one transaction (S5_BROWSER_EDITOR.md 3.8: "Edits from the inspector are transactions").
function formEdits(actions: Actions, found: FoundObject): FormEdits
{
    const target = targetOf(found);
    const send = (op: Op | null, label: string) =>
    {
        if (op)
        {
            void actions.edit({ label, ops: [op] });
        }
    };
    return {
        field: (path, value) => send(fieldOp(target, path, value), `${value === undefined ? 'remove' : 'set'} ${path.filter((step) => typeof step === 'string').join('.')} of ${found.id}`),
        addRow: (path, value) => send(addRowOp(target, path, value), `add to ${String(path.at(-1))} of ${found.id}`),
        row: (path, index, action) => send(rowOp(target, path, index, action), `${action} a row of ${String(path.at(-1))} of ${found.id}`),
        renameKey: (path, index, to) => send(renameKeyOp(target, path, index, to), `rename a key of ${found.id} to ${to}`),
        rename: found.pointer ? {
            field: 'key',
            to: (to: string) => void actions.edit({ label: `rename ${found.id} to ${to}`, ops: [{ op: 'rename', ...(target.id ? { id: target.id } : {}), file: found.file as FileName, path: found.pointer!, to }] })
                .then((result) => result && actions.select({ id: `${found.id.slice(0, found.id.lastIndexOf('/'))}/${to}`, file: found.file })),
        } : {
            field: 'id',
            to: (to: string) => void actions.edit({ label: `rename ${found.id} to ${to}`, ops: [{ op: 'rename', from: found.id, to, file: found.file as FileName }] })
                .then((result) => result && actions.select({ id: to, file: found.file })),
        },
    };
}

// The schema of the shown object: its list's items, or for a keyed sub-object the items of its list in its owner.
function schemaOf(registry: Registry, found: FoundObject): ReturnType<typeof itemSchema>
{
    if (found.place !== undefined)
    {
        return schemaAtPlace(registry, found.file, found.place);
    }
    if (!found.parentList)
    {
        return itemSchema(registry, found.file, found.list);
    }
    const owner = itemSchema(registry, found.file, found.parentList);
    if (!owner)
    {
        return undefined;
    }
    const resolved = registry.resolve(owner);
    const list = resolved.node.properties?.[found.list];
    if (!list)
    {
        return undefined;
    }
    const listLoc = registry.resolve(registry.child(resolved, 'properties', found.list));
    return listLoc.node.items ? registry.child(listLoc, 'items') : undefined;
}

// The lists whose things an event can run from (a click on them).
const SOURCE_LISTS = new Set(['switches', 'doors', 'chests', 'exits', 'plates', 'lifts', 'movers', 'decorations']);

function Properties({ found }: { found: FoundObject })
{
    const actions = useActions();
    const ids = useS((s) => (s.project.state === 'ready' ? s.project.value.ids : NONE));
    const author = useS((s) => s.mode === 'author');
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : ''));
    const [registry, setRegistry] = useState<Registry | null>(null);
    const [expandAll, setExpandAll] = useState(false);
    // An event's bespoke form, or all its words in the generated form.
    const [allWords, setAllWords] = useState(false);
    const [resolved, setResolved] = useState<{ key: string; fields: Resolved; slots?: ProjectResolveResult['slots'] } | null>(null);
    useEffect(() => { void loadRegistry().then(setRegistry); }, []);
    const idSet = useMemo(() => new Set(ids.map((place) => place.id)), [ids]);
    // The effective values of the absent fields (project.resolve), for a top-level object.
    const resolveKey = `${found.file}#${found.id}@${revision}`;
    useEffect(() =>
    {
        if (found.pointer)
        {
            return;
        }
        let live = true;
        void actions.resolve(found.id, found.file).then((answer) =>
        {
            if (live && answer)
            {
                setResolved({ key: resolveKey, fields: answer.fields as Resolved, ...(answer.slots ? { slots: answer.slots } : {}) });
            }
        });
        return () => { live = false; };
    }, [actions, found.id, found.file, found.pointer, resolveKey]);
    const edits = useMemo(() => (author ? formEdits(actions, found) : undefined), [author, actions, found]);
    if (!registry)
    {
        return <p className={css.dim}>Reading the schemas…</p>;
    }
    const loc = schemaOf(registry, found);
    if (!loc)
    {
        return <p className={css.dim}>No schema for {found.file} {found.list}.</p>;
    }
    const kind = typeof found.value.kind === 'string' ? found.value.kind : undefined;
    // An answer for an earlier revision still helps (the absent fields rarely change) until the new one comes.
    const fields = resolved && resolved.key.startsWith(`${found.file}#${found.id}@`) ? resolved.fields : undefined;
    // A wiring event in Author mode: the event form (3.18), with the generated form a switch away.
    const event = author && edits && found.file === 'wiring.yml' && found.list === 'events' && !found.pointer;
    // Outdoors (S5b2): a sketch event in the event form; a building's, a part's or a structure's own panels.
    const sketchEvent = author && edits && found.file === 'sketch.yml' && found.list === 'events' && !found.pointer;
    const sketchPanels = author && edits && found.file === 'sketch.yml' && !sketchEvent;
    const source = !found.pointer && found.file === 'objects.yml' && SOURCE_LISTS.has(found.list);
    return (
        <div className={css.form}>
            <label className={css.expand}>
                <Switch.Root className={css.switch} checked={expandAll} onCheckedChange={setExpandAll}><Switch.Thumb className={css.thumb} /></Switch.Root>
                expand all
                {event || sketchEvent ? (
                    <>
                        <Switch.Root className={css.switch} checked={allWords} onCheckedChange={setAllWords} data-testid="all-words"><Switch.Thumb className={css.thumb} /></Switch.Root>
                        every word
                    </>
                ) : null}
                {author ? <span className={css.editing}>editing: each field is written on Enter or when you leave it</span> : null}
            </label>
            <FormContext.Provider value={{ reg: registry, ids: idSet, kind, expandAll, onSelectId: (id) => actions.select({ id }, true), edits, resolved: fields }}>
                {source ? <SourceEvents id={found.id} /> : null}
                {found.list === 'spawns' && resolved?.slots ? <SlotNote slot={Number(found.value.slot ?? 0)} kind={String(found.value.kind ?? 'monster')} slots={resolved.slots} /> : null}
                {sketchPanels ? <OutdoorPanels found={found} reg={registry} edits={edits!} /> : null}
                {event && !allWords ? <EventForm key={found.id} found={found} reg={registry} edits={edits!} />
                    : sketchEvent && !allWords ? <OutdoorEventForm key={found.id} found={found} reg={registry} edits={edits!} />
                        : <TimedForm key={`${found.file}:${found.id}:${expandAll}:${author}`} found={found} expandAll={expandAll} loc={loc} />}
            </FormContext.Provider>
        </div>
    );
}

// A spawn point's slot as the map card gives it (project.resolve's slots: project.yml, or the reference map's row).
function SlotNote({ slot, kind, slots }: { slot: number; kind: string; slots: NonNullable<ProjectResolveResult['slots']> })
{
    if (kind !== 'monster')
    {
        return null;
    }
    const entry = slots.find((candidate) => candidate.slot === slot);
    return (
        <p className={css.slotNote} data-testid="slot-note">
            {entry ? <>Slot {slot}: <b>{entry.monster}</b>{entry.tier ? ` · difficulty ${entry.tier}` : ''}{entry.count ? ` · ${entry.count} per spawn point` : ''}
                <span className={css.dim}> ({entry.source === 'written' ? 'project.yml map_stats.slots' : entry.from})</span></>
                : <>Slot {slot} is empty on the map card: {slots.map((candidate) => `${candidate.slot} ${candidate.monster}`).join(', ') || 'no slots'}.</>}
        </p>
    );
}

// The form, timed from its render to its commit (S5_BROWSER_EDITOR.md 3.8: the in-browser render time, measured
// in the real app; spike 7 measured Node server renders only). The times go to window.__studio.inspector.
function TimedForm({ found, expandAll, loc }: { found: FoundObject; expandAll: boolean; loc: NonNullable<ReturnType<typeof itemSchema>> })
{
    const start = useRef(performance.now());
    start.current = performance.now();
    useLayoutEffect(() =>
    {
        probe().inspector.push({ id: found.id, expanded: expandAll, ms: Math.round((performance.now() - start.current) * 10) / 10 });
    }, [found, expandAll]);
    return <ObjectForm loc={loc} value={found.value as Record<string, Json>} path={[]} />;
}

function ObjectIssues({ found }: { found: FoundObject })
{
    const issues = useS((s) => knownIssues(s));
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const own = issues.filter((issue) => issueObject(files, issue)?.id === found.id && issue.file === found.file);
    if (own.length === 0)
    {
        return <p className={css.dim}>No issues on this object.</p>;
    }
    return (
        <ul className={css.issues}>
            {own.map((issue, index) => (
                <li key={index} className={css[`issue_${issue.severity}`]}>
                    <b>{issue.severity}</b> {issue.path}: {issue.message}
                </li>
            ))}
        </ul>
    );
}

// The Source tab's colours, from the design tokens (light and dark alike).
const sourceStyle = HighlightStyle.define([
    { tag: [tags.propertyName, tags.definition(tags.propertyName)], color: 'var(--accent)' },
    { tag: [tags.number, tags.bool, tags.null], color: 'var(--geom)' },
    { tag: [tags.string, tags.content], color: 'var(--text)' },
    { tag: [tags.comment], color: 'var(--text-dim)', fontStyle: 'italic' },
    { tag: [tags.punctuation, tags.separator, tags.squareBracket, tags.brace], color: 'var(--text-dim)' },
]);

// The Source tab: the object's YAML; in Author mode edited and applied as a whole (op replace, 2.6 item 10).
function SourceTab({ found }: { found: FoundObject })
{
    const actions = useActions();
    const author = useS((s) => s.mode === 'author');
    const [error, setError] = useState<string | null>(null);
    const [dirty, setDirty] = useState(false);
    const text = useRef<() => string>(() => '');
    const apply = () =>
    {
        let value: unknown;
        try
        {
            value = parseYaml(text.current());
        }
        catch (problem)
        {
            setError(`Not YAML: ${problem instanceof Error ? problem.message : String(problem)}`);
            return;
        }
        if (!value || typeof value !== 'object' || Array.isArray(value))
        {
            setError('The source of an object is a map of its words');
            return;
        }
        setError(null);
        void actions.edit({ label: `source of ${found.id}`, ops: [replaceOp(targetOf(found), value as JsonObject)] }).then((result) =>
        {
            if (result)
            {
                setDirty(false);
            }
        });
    };
    return (
        <div className={css.sourceTab}>
            {author ? (
                <div className={css.sourceBar}>
                    <button type="button" className={css.apply} disabled={!dirty} onClick={apply} data-testid="source-apply">Apply</button>
                    <span className={error ? css.sourceError : css.dim}>{error ?? (dirty ? 'changed: Apply writes the whole object' : 'edit the YAML, then Apply')}</span>
                </div>
            ) : null}
            <SourceView value={found.value as Json} editable={author} onText={(read) => (text.current = read)} onChange={() => setDirty(true)} />
        </div>
    );
}

// The object's YAML (CodeMirror 6); read only unless `editable`.
export function SourceView({ value, editable = false, onText, onChange }: { value: Json; editable?: boolean; onText?: (read: () => string) => void; onChange?: () => void })
{
    const host = useRef<HTMLDivElement>(null);
    const text = useMemo(() => objectYaml(value), [value]);
    // Callbacks through refs: a new callback must not make a new editor (it would drop what was typed).
    const changed = useRef(onChange);
    changed.current = onChange;
    const reader = useRef(onText);
    reader.current = onText;
    useEffect(() =>
    {
        if (!host.current)
        {
            return;
        }
        const view = new EditorView({
            parent: host.current,
            state: EditorState.create({
                doc: text,
                extensions: [lineNumbers(), yaml(), syntaxHighlighting(sourceStyle), EditorState.readOnly.of(!editable), EditorView.editable.of(editable), EditorView.lineWrapping,
                    EditorView.updateListener.of((update) => { if (update.docChanged) { changed.current?.(); } })],
            }),
        });
        reader.current?.(() => view.state.doc.toString());
        return () => view.destroy();
    }, [text, editable]);
    return <div ref={host} className={css.source} data-testid="source" />;
}

// The object as YAML in the files' own style: lists of plain values on one line ([0, 512]), the rest as blocks.
export function objectYaml(value: Json): string
{
    const document = new Document(value);
    visit(document, {
        Seq(_, node)
        {
            if (isSeq(node) && node.items.every((item) => isScalar(item) || (isSeq(item) && item.items.every((inner) => isScalar(inner)))))
            {
                if (node.items.every((item) => isScalar(item)))
                {
                    node.flow = true;
                }
            }
        },
    });
    return document.toString({ lineWidth: 0, flowCollectionPadding: false });
}
