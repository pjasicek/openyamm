// The event form (S5_BROWSER_EDITOR.md 3.18 "wiring event", W3, W4): a wiring.yml event laid out as a person thinks
// of it, not as the generic rows: its preset and hint; what runs it; the lock (conditions as rows of the condition's
// words, the locked text, a question, once); what it moves (doors, lifts, levers as chips); what it does (effects and
// else-effects as rows of the step words of `$defs/effect`, each with its value's own field and id pickers); and the
// Lua of a script handler with the script reference's functions as completion ("Convert to script"). Every change is
// one transaction through the inspector's edits; the values' widgets are the generated form's.
import { useEffect, useMemo, useRef, useState } from 'react';
import { EditorState } from '@codemirror/state';
import { EditorView, lineNumbers } from '@codemirror/view';
import { autocompletion } from '@codemirror/autocomplete';
import type { CompletionContext } from '@codemirror/autocomplete';
import type { Json, Located, Registry } from '../schema/registry.ts';
import { itemSchema } from '../schema/schemas.ts';
import { Field } from '../form/Fields.tsx';
import { makeDefault } from '../form/plan.ts';
import type { FormEdits } from '../form/context.ts';
import type { FoundObject } from '../model/objects.ts';
import type { FileTrees, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import { MOVE_VERBS, PRESETS, eventsFrom, newEventOp, toScriptOp } from '../edit/wiring.ts';
import { useActions, useS } from './context.ts';
import css from './EventForm.module.css';
import { variablesOf } from './Variables.tsx';

// The words of an effect step, from the schema (its x-variant labels).
export function effectWords(reg: Registry): { word: string; label: string }[]
{
    const effect = reg.resolve(reg.at('wiring.schema.json', '#/$defs/effect')).node;
    const variants = Array.isArray(effect['x-variant']) ? effect['x-variant'] as { label: string; when?: { present?: string } }[] : [];
    const words = variants.filter((variant) => variant.when?.present).map((variant) => ({ word: variant.when!.present!, label: variant.label }));
    return words.length > 0 ? words : Object.keys(effect.properties ?? {}).map((word) => ({ word, label: word }));
}

// The schema of one effect word's value.
function effectLoc(reg: Registry, word: string): Located | null
{
    const effect = reg.resolve(reg.at('wiring.schema.json', '#/$defs/effect'));
    if (effect.node.properties?.[word])
    {
        return reg.child(effect, 'properties', word);
    }
    for (const key of ['oneOf', 'anyOf'] as const)
    {
        const branches = effect.node[key] as Json[] | undefined;
        const index = branches?.findIndex((branch) => typeof branch === 'object' && branch !== null && !Array.isArray(branch)
            && typeof branch.properties === 'object' && branch.properties !== null && word in (branch.properties as Record<string, Json>));
        if (index !== undefined && index >= 0)
        {
            return reg.child(effect, key, index, 'properties', word);
        }
    }
    return null;
}

function conditionLoc(reg: Registry): Located
{
    return reg.resolve(reg.at('common.schema.json', '#/$defs/condition'));
}

const CONDITION_LABELS: Record<string, string> = {
    qbit: 'quest bit set', item: 'the party carries', item_count: 'at least this many', consume: 'take the item', map_var: 'map variable',
    award: 'an award held', player_bit: 'the member\'s bit', autonote: 'autonote known', lua: 'a Lua test', stat: 'a stat or skill',
    time: 'time of day', month: 'month', day: 'day', password: 'a typed answer', choice: 'a dialogue choice', kills: 'monsters killed',
    not: 'not', any: 'any of', all: 'all of',
};

function idsOfLists(files: FileTrees | undefined, lists: string[]): string[]
{
    const tree = files?.['objects.yml']?.tree;
    const out: string[] = [];
    for (const list of lists)
    {
        const items = tree?.[list];
        if (Array.isArray(items))
        {
            items.forEach((item) => typeof item === 'object' && item !== null && !Array.isArray(item) && typeof item.id === 'string' && out.push(item.id));
        }
    }
    return out;
}

export function EventForm({ found, reg, edits }: { found: FoundObject; reg: Registry; edits: FormEdits })
{
    const actions = useActions();
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const event = found.value as JsonObject;
    const eventLoc = useMemo(() => itemSchema(reg, 'wiring.yml', 'events')!, [reg]);
    const prop = (name: string): Located => reg.child(reg.resolve(eventLoc), 'properties', name);
    const field = (name: string, label?: string) => (
        <Field key={name} loc={prop(name)} value={event[name] as Json | undefined} path={[name]} label={label ?? name} removable={event[name] !== undefined && name !== 'preset'} />
    );
    const preset = String(event.preset ?? '');
    const trigger = typeof event.trigger === 'string' ? event.trigger : 'click';
    return (
        <div className={css.form} data-testid="event-form">
            <section className={css.section}>
                <h4 className={css.heading}>Event</h4>
                <div className={css.presets} role="group" aria-label="Preset">
                    {PRESETS.map((name) => (
                        <button key={name} type="button" className={name === preset ? css.presetOn : css.preset} data-testid={`preset-${name}`}
                            onClick={() => name !== preset && edits.field(['preset'], name)}>{name}</button>
                    ))}
                </div>
                {field('title', 'title (the hint)')}
            </section>
            <section className={css.section}>
                <h4 className={css.heading}>Runs on</h4>
                {field('trigger')}
                {trigger === 'click' || trigger === 'step' ? field('source', trigger === 'step' ? 'the floor stepped on' : 'the thing used') : null}
                {trigger === 'timer' ? field('every', 'every (seconds)') : null}
                {preset === 'door' ? field('side', 'one side only') : null}
            </section>
            <section className={css.section}>
                <h4 className={css.heading}>Lock</h4>
                <ConditionRows reg={reg} edits={edits} condition={event.condition} />
                {event.condition !== undefined ? field('locked_text', 'when locked, say') : null}
                {field('once', 'only the first time')}
                {event.question !== undefined ? field('question') : (
                    <button type="button" className={css.add} onClick={() => edits.field(['question'], { ask: 'What is the word?', answers: ['answer'] })}>+ a question first</button>
                )}
            </section>
            <section className={css.section}>
                <h4 className={css.heading}>Moves</h4>
                {MOVE_VERBS.map((verb) => <Chips key={verb} verb={verb} event={event} files={files} edits={edits} />)}
                {preset === 'door' ? field('action', 'the door itself') : null}
                {preset === 'teleport' ? <>{field('to', 'lands at')}{field('direction')}</> : null}
            </section>
            <section className={css.section}>
                <h4 className={css.heading}>Does</h4>
                <EffectRows reg={reg} edits={edits} list="effects" steps={event.effects} />
                {event.condition !== undefined || event.else_effects !== undefined ? (
                    <>
                        <h5 className={css.subheading}>When the lock holds not (else)</h5>
                        <EffectRows reg={reg} edits={edits} list="else_effects" steps={event.else_effects} />
                    </>
                ) : null}
                {field('text', preset === 'text' ? 'text' : 'then say')}
                {preset === 'text' ? field('window', 'in a window') : null}
                {event.sets !== undefined && typeof event.sets === 'object' && event.sets !== null && !Array.isArray(event.sets) && 'map_var' in event.sets
                    && (typeof event.sets.map_var === 'string' || typeof event.sets.map_var === 'number') ? (
                    <VariablePick label="sets the map variable" value={event.sets.map_var as string | number} onPick={(name) => edits.field(['sets'], { map_var: name })}
                        onRemove={() => edits.field(['sets'], undefined)} testId="sets-map_var" />
                ) : event.sets !== undefined ? field('sets') : (
                    <button type="button" className={css.add} data-testid="add-sets"
                        onClick={() => edits.field(['sets'], { map_var: variablesOf(files)[0] ?? 1 })}>+ sets a map variable or quest bit</button>
                )}
            </section>
            <section className={css.section}>
                <h4 className={css.heading}>Script</h4>
                {preset === 'script' || typeof event.lua === 'string' ? (
                    <LuaEditor key={`${found.id}`} value={typeof event.lua === 'string' ? event.lua : ''} onCommit={(text) => edits.field(['lua'], text)} />
                ) : null}
                {preset !== 'script' ? (
                    <button type="button" className={css.add} data-testid="convert-script"
                        title="Make it a script handler: its preset's own work is written as words (a door's click moves its door, a chest's shows its contents) and Lua lines follow"
                        onClick={() => void actions.edit({ label: `${found.id} to a script`, ops: [toScriptOp(event)] })}>Convert to script</button>
                ) : null}
            </section>
        </div>
    );
}

export function ConditionRows({ reg, edits, condition }: { reg: Registry; edits: FormEdits; condition: unknown })
{
    const loc = conditionLoc(reg);
    const variables = variablesOf(useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined)));
    const keys = Object.keys(loc.node.properties ?? {});
    const written = typeof condition === 'object' && condition !== null && !Array.isArray(condition) ? condition as Record<string, Json> : null;
    const [adding, setAdding] = useState('');
    return (
        <div className={css.rows} data-testid="condition-rows">
            {written ? Object.keys(written).map((key) => (
                <div key={key} className={css.row}>
                    {key === 'map_var' && (typeof written[key] === 'string' || typeof written[key] === 'number')
                        ? <VariablePick label="map variable is set" value={written[key] as string | number} onPick={(name) => edits.field(['condition', key], name)}
                            onRemove={() => edits.field(Object.keys(written).length > 1 ? ['condition', key] : ['condition'], undefined)} testId="condition-map_var" />
                        : <Field loc={reg.child(loc, 'properties', key)} value={written[key]} path={['condition', key]} label={CONDITION_LABELS[key] ?? key} removable />}
                </div>
            )) : <p className={css.dim}>No lock: it always acts.</p>}
            <select className={css.adder} value={adding} data-testid="add-condition" onChange={(event) =>
            {
                const key = event.target.value;
                setAdding('');
                if (!key)
                {
                    return;
                }
                const value = key === 'map_var' && variables.length > 0 ? variables[0] : makeDefault(reg, reg.child(loc, 'properties', key));
                edits.field(written ? ['condition', key] : ['condition'], written ? value : { [key]: value });
            }}>
                <option value="">+ condition…</option>
                {keys.filter((key) => !written || !(key in written)).map((key) => <option key={key} value={key}>{CONDITION_LABELS[key] ?? key}</option>)}
            </select>
        </div>
    );
}

export function EffectRows({ reg, edits, list, steps }: { reg: Registry; edits: FormEdits; list: 'effects' | 'else_effects'; steps: unknown })
{
    const words = useMemo(() => effectWords(reg), [reg]);
    const rows = Array.isArray(steps) ? steps as Json[] : [];
    const labelOf = (word: string) => words.find((entry) => entry.word === word)?.label ?? word;
    const defaultFor = (word: string): Json =>
    {
        const loc = effectLoc(reg, word);
        return loc ? makeDefault(reg, loc) : '';
    };
    return (
        <div className={css.rows} data-testid={`${list}-rows`}>
            {rows.map((step, index) =>
            {
                const word = typeof step === 'object' && step !== null && !Array.isArray(step) ? Object.keys(step)[0] : undefined;
                const loc = word ? effectLoc(reg, word) : null;
                return (
                    <div key={index} className={css.step}>
                        <div className={css.stepHead}>
                            <span className={css.number}>{index + 1}</span>
                            <select className={css.word} value={word ?? ''} title="the step's word" onChange={(event) =>
                            {
                                const next = event.target.value;
                                if (next && next !== word)
                                {
                                    edits.field([list, index], { [next]: defaultFor(next) });
                                }
                            }}>
                                {word ? null : <option value="">?</option>}
                                {words.map((entry) => <option key={entry.word} value={entry.word}>{entry.label}</option>)}
                            </select>
                            <span className={css.spacer} />
                            <button type="button" className={css.icon} disabled={index === 0} title="earlier" onClick={() => edits.row([list], index, 'up')}>↑</button>
                            <button type="button" className={css.icon} disabled={index === rows.length - 1} title="later" onClick={() => edits.row([list], index, 'down')}>↓</button>
                            <button type="button" className={css.icon} title="remove this step" onClick={() => edits.row([list], index, 'remove')}>×</button>
                        </div>
                        {word && loc ? <Field loc={loc} value={(step as Record<string, Json>)[word]} path={[list, index, word]} label={labelOf(word)} /> : null}
                    </div>
                );
            })}
            <select className={css.adder} value="" data-testid={`add-${list}`} onChange={(event) =>
            {
                const word = event.target.value;
                if (word)
                {
                    edits.addRow([list], { [word]: defaultFor(word) });
                }
            }}>
                <option value="">+ step…</option>
                {words.map((entry) => <option key={entry.word} value={entry.word}>{entry.label}</option>)}
            </select>
        </div>
    );
}

// The doors, lifts, movers and levers an event moves by one verb, as chips (× takes one out; the picker adds one).
function Chips({ verb, event, files, edits }: { verb: string; event: JsonObject; files: FileTrees | undefined; edits: FormEdits })
{
    const actions = useActions();
    const list = Array.isArray(event[verb]) ? (event[verb] as Json[]).filter((entry): entry is string => typeof entry === 'string') : [];
    const candidates = idsOfLists(files, ['doors', 'lifts', 'movers', 'switches']).filter((id) => !list.includes(id));
    return (
        <div className={css.chips} data-testid={`chips-${verb}`}>
            <span className={css.verb}>{verb}</span>
            {list.map((id) => (
                <span key={id} className={css.chip}>
                    <button type="button" className={css.chipName} onClick={() => actions.select({ id, file: 'objects.yml' }, true)}>{id}</button>
                    <button type="button" className={css.chipX} title={`no longer ${verb} ${id}`}
                        onClick={() => edits.field([verb], list.length > 1 ? list.filter((entry) => entry !== id) : undefined)}>×</button>
                </span>
            ))}
            <select className={css.chipAdd} value="" data-testid={`add-${verb}`} onChange={(change) =>
            {
                const id = change.target.value;
                if (id)
                {
                    edits.field([verb], [...list, id]);
                }
            }}>
                <option value="">+</option>
                {candidates.map((id) => <option key={id} value={id}>{id}</option>)}
            </select>
        </div>
    );
}

// The handler's Lua (plain CodeMirror) with the game's script functions as completion; written on leaving it or by
// the button.
function LuaEditor({ value, onCommit }: { value: string; onCommit: (text: string) => void })
{
    const actions = useActions();
    const host = useRef<HTMLDivElement>(null);
    const view = useRef<EditorView | null>(null);
    const names = useRef<string[]>([]);
    const [dirty, setDirty] = useState(false);
    const commit = useRef(onCommit);
    commit.current = onCommit;
    useEffect(() =>
    {
        void actions.scriptFunctions().then((list) => { names.current = list; });
    }, [actions]);
    useEffect(() =>
    {
        if (!host.current)
        {
            return;
        }
        const complete = (context: CompletionContext) =>
        {
            const word = context.matchBefore(/[A-Za-z_][\w.]*/);
            if (!word || (word.from === word.to && !context.explicit))
            {
                return null;
            }
            return { from: word.from, options: names.current.map((name) => ({ label: name, type: 'function' })) };
        };
        const editor = new EditorView({
            parent: host.current,
            state: EditorState.create({
                doc: value,
                extensions: [lineNumbers(), autocompletion({ override: [complete] }), EditorView.lineWrapping,
                    EditorView.updateListener.of((update) => { if (update.docChanged) { setDirty(true); } }),
                    EditorView.domEventHandlers({ blur: () => { if (editor.state.doc.toString() !== value) { commit.current(editor.state.doc.toString()); setDirty(false); } } })],
            }),
        });
        view.current = editor;
        return () => editor.destroy();
    }, [value]);
    return (
        <div className={css.lua}>
            <div ref={host} className={css.luaEditor} data-testid="lua-editor" />
            <div className={css.luaBar}>
                <span className={css.dim}>Lua run after the condition, the doors and the effects · Ctrl Space: the game's functions</span>
                <button type="button" className={css.add} disabled={!dirty} onClick={() =>
                {
                    if (view.current)
                    {
                        commit.current(view.current.state.doc.toString());
                        setDirty(false);
                    }
                }}>Write the Lua</button>
            </div>
        </div>
    );
}

// On a thing that can run an event (a switch, door, chest, exit ...): its events, and "+ event" of a preset.
export function SourceEvents({ id }: { id: string })
{
    const actions = useActions();
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const author = useS((s) => s.mode === 'author');
    const events = eventsFrom(files, id);
    const presets = id.startsWith('door:') ? ['door', 'switch', 'text', 'script'] : id.startsWith('chest:') ? ['chest', 'text', 'script']
        : id.startsWith('exit:') ? ['exit', 'text', 'script'] : ['switch', 'text', 'teleport', 'script'];
    return (
        <section className={css.sourceEvents} data-testid="source-events">
            <h4 className={css.heading}>Events</h4>
            {events.length === 0 ? <p className={css.dim}>Nothing happens when it is used: no event names it as its source.</p> : null}
            {events.map((event) => (
                <button key={String(event.id)} type="button" className={css.eventLink} onClick={() => actions.select({ id: String(event.id), file: 'wiring.yml' })}>
                    {String(event.id)} <span className={css.dim}>{String(event.preset)}{event.title ? ` · ${String(event.title)}` : ''}</span>
                </button>
            ))}
            {author ? (
                <div className={css.presets}>
                    {presets.map((preset) => (
                        <button key={preset} type="button" className={css.preset} data-testid={`new-event-${preset}`}
                            onClick={() => void actions.edit({ label: `${preset} event of ${id}`, ops: [newEventOp(files, preset, id)] }).then((result) =>
                            {
                                const made = result?.ids_allocated?.[0];
                                if (made)
                                {
                                    actions.select({ id: made.slice(made.indexOf('#') + 1), file: 'wiring.yml' });
                                }
                            })}>+ {preset}</button>
                    ))}
                    <span className={css.dim}>or L and a click on a door (Wire stage)</span>
                </div>
            ) : null}
        </section>
    );
}

// A map variable picked by its name from wiring.yml `variables` (a number, the old way, stays shown as it is).
function VariablePick({ label, value, onPick, onRemove, testId }: { label: string; value: string | number; onPick: (name: string | number) => void;
    onRemove: () => void; testId: string })
{
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const names = variablesOf(files);
    const options = typeof value === 'number' || !names.includes(String(value)) ? [String(value), ...names] : names;
    return (
        <div className={css.variablePick}>
            <span className={css.dim}>{label}</span>
            <select value={String(value)} data-testid={testId} onChange={(event) =>
            {
                const next = event.target.value;
                onPick(/^\d+$/.test(next) ? Number(next) : next);
            }}>
                {options.map((name) => <option key={name} value={name}>{name}{names.includes(name) ? '' : ' (not declared)'}</option>)}
            </select>
            {names.length === 0 ? <span className={css.dim}>declare one with the switch board's “+ variable”</span> : null}
            <button type="button" className={css.icon} title="remove" onClick={onRemove}>×</button>
        </div>
    );
}
