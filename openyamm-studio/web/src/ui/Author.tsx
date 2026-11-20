// Author mode's frame parts (S5_BROWSER_EDITOR.md 3.2, 3.3, 3.9, 2.8): the Review/Author switch, the stage bar, the
// tool rail, the tool options above the views, the project's settings (its protection and keys), and the banners
// for an outside rewrite of a hand-edited project and for an undo that left objects alone.
import { useEffect, useMemo, useState } from 'react';
import { Popover } from '@base-ui/react/popover';
import { Tooltip } from '@base-ui/react/tooltip';
import { Toggle } from '@base-ui/react/toggle';
import { ToggleGroup } from '@base-ui/react/toggle-group';
import type { ProjectMigrateResult } from '../../../schema/rpc/generated/rpc.ts';
import { CHEST_KINDS, GRIDS, OUTDOOR_TOOLS, outdoorStageCounts, stageCounts, stagesOf, toolInfo, toolsOf } from '../edit/stages.ts';
import { isOutdoorFiles } from '../edit/outdoortools.ts';
import { HandMadeSetting, OutdoorOptionsBar, OutdoorRailExtras } from './OutdoorAuthor.tsx';
import type { ToolOptions } from '../edit/stages.ts';
import { DOOR_PRESETS } from '../edit/ops.ts';
import { openNotice, redoTarget, undoTarget } from '../edit/history.ts';
import { NumberInput, TextInput } from '../form/inputs.tsx';
import { knownIssues, NONE } from '../state/store.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Author.module.css';

export function ModeSwitch()
{
    const actions = useActions();
    const mode = useS((s) => s.mode);
    return (
        <ToggleGroup className={css.modes} value={[mode]} aria-label="Mode"
            onValueChange={(value) => value.length > 0 && actions.setMode(value[0] as 'review' | 'author')}>
            <Toggle value="review" className={css.mode} title="Review: nothing on the map changes by a click or a drag">Review</Toggle>
            <Toggle value="author" className={css.mode} data-testid="mode-author" title="Author: the stages, the tools and the editable inspector (every change is written at once)">Author</Toggle>
        </ToggleGroup>
    );
}

// The seven stages with what is open in each (3.3), keys 1 to 7.
export function StageBar()
{
    const actions = useActions();
    const stage = useS((s) => s.stage);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const issues = useS((s) => knownIssues(s));
    const outdoor = isOutdoorFiles(files);
    const counts = useMemo(() => (outdoor ? outdoorStageCounts(files, issues) : stageCounts(files, issues)), [files, issues, outdoor]);
    return (
        <nav className={css.stages} aria-label="Stages" data-testid="stage-bar">
            {stagesOf(outdoor).map((entry) => (
                <button key={entry.number} type="button" className={entry.number === stage ? css.stageOn : css.stage}
                    onClick={() => actions.setStage(entry.number)} title={`${entry.name} (${entry.number}): done when ${entry.done}`}>
                    <span className={css.stageNumber}>{entry.number}</span> {entry.name}
                    {counts[entry.number] !== undefined ? <span className={css.stageCount}>{counts[entry.number]}</span> : null}
                </button>
            ))}
            <span className={css.spacer} />
            <EditStatus />
        </nav>
    );
}

// Autosave's state: what is being written, when it was last written, the last refusal.
function EditStatus()
{
    const edits = useS((s) => s.edits);
    if (edits.pending > 0)
    {
        return <span className={css.saving} data-testid="edit-status">writing {edits.pending}…</span>;
    }
    if (edits.error)
    {
        return <span className={css.refused} title={edits.error.message} data-testid="edit-status">not written: {edits.error.label}: {edits.error.message}</span>;
    }
    if (edits.saved)
    {
        return <span className={css.saved} data-testid="edit-status" title={`revision ${edits.saved.revision}`}>saved: {edits.saved.label} · rev {edits.saved.revision.slice(0, 8)}</span>;
    }
    return <span className={css.saved} data-testid="edit-status">every change is written as you make it</span>;
}

// The current stage's tools, one key each (3.9); hovering explains.
export function ToolRail()
{
    const actions = useActions();
    const stage = useS((s) => s.stage);
    const tool = useS((s) => s.tool);
    const outdoor = useS((s) => (s.project.state === 'ready' ? isOutdoorFiles(s.project.value.files) : false));
    const tools = stagesOf(outdoor).find((entry) => entry.number === stage)?.tools ?? ['select'];
    return (
        <Tooltip.Provider delay={250}>
            <aside className={css.rail} aria-label="Tools" data-testid="tool-rail">
                {toolsOf(outdoor).filter((entry) => tools.includes(entry.name)).map((entry) => (
                    <Tooltip.Root key={entry.name}>
                        <Tooltip.Trigger render={<button type="button" className={entry.name === tool ? css.toolOn : css.tool}
                            onClick={() => actions.setTool(entry.name)} data-testid={`tool-${entry.name}`} />}>
                            <span className={css.toolLabel}>{entry.label}</span>
                            <span className={css.toolKey}>{entry.key}</span>
                        </Tooltip.Trigger>
                        <Tooltip.Portal>
                            <Tooltip.Positioner side="right" sideOffset={6}>
                                <Tooltip.Popup className={css.tip}><b>{entry.label} ({entry.key})</b> {entry.help}</Tooltip.Popup>
                            </Tooltip.Positioner>
                        </Tooltip.Portal>
                    </Tooltip.Root>
                ))}
                {stage === 1 && !outdoor ? <p className={css.later}>Space: a bubble per planned room; Plan link: drag between two; Goal: click one. The inspector holds the rest (locks, keys).</p> : null}
                {stage === 1 && outdoor ? <p className={css.later}>The plan's zones, links and populations: the inspector of plan.yml with nothing selected; the tools make the entries their words name.</p> : null}
                {stage === 7 ? <p className={css.later}>Test: walk (G), Play here (F5), the Checklist and Issues in the drawer.</p> : null}
                {outdoor ? <OutdoorRailExtras /> : null}
            </aside>
        </Tooltip.Provider>
    );
}

function Option({ label, children }: { label: string; children: React.ReactNode })
{
    return <label className={css.option}><span className={css.optionLabel}>{label}</span>{children}</label>;
}

// The active tool's settings, above the views (3.9): never the selection's properties.
export function ToolBar()
{
    const { store } = useStudioContext();
    const actions = useActions();
    const tool = useS((s) => s.tool);
    const options = useS((s) => s.toolOptions);
    const hint = useS((s) => s.hint);
    const history = useS((s) => (s.history.state === 'ready' ? s.history.value.entries : NONE));
    const undo = undoTarget(history, 'user');
    const redo = redoTarget(history, 'user');
    const set = (change: Partial<ToolOptions>) => store.setState((s) => ({ toolOptions: { ...s.toolOptions, ...change } }));
    const number = (name: keyof ToolOptions, label: string, extra: { min?: number; title?: string } = {}) => (
        <Option label={label}><NumberInput value={options[name] as number} onCommit={(value) => set({ [name]: value })} width="narrow" integer testId={`option-${name}`} {...extra} /></Option>
    );
    const info = toolInfo(tool);
    const outdoor = useS((s) => (s.project.state === 'ready' ? isOutdoorFiles(s.project.value.files) : false));
    if (outdoor)
    {
        const own = OUTDOOR_TOOLS.find((entry) => entry.name === tool) ?? info;
        return (
            <div className={css.toolbar} data-testid="tool-options">
                <span className={css.toolName}>{own.label}</span>
                <OutdoorOptionsBar tool={tool} />
                <span className={css.hint} title={hint ?? own.help}>{hint ?? own.help}</span>
                <button type="button" className={css.button} disabled={!undo} onClick={() => actions.undo()} data-testid="undo"
                    title={undo ? `Undo your "${undo.label ?? `#${undo.sequence}`}" (Ctrl Z): agents' changes are never undone by it` : 'Nothing of yours to undo'}>Undo</button>
                <button type="button" className={css.button} disabled={!redo} onClick={() => actions.redo()} data-testid="redo"
                    title={redo ? `Redo (Ctrl Y): ${redo.label ?? `#${redo.sequence}`}` : 'Nothing to redo'}>Redo</button>
            </div>
        );
    }
    return (
        <div className={css.toolbar} data-testid="tool-options">
            <span className={css.toolName}>{info.label}</span>
            <Option label="grid">
                <select className={css.select} value={options.grid} onChange={(event) => set({ grid: Number(event.target.value) })} title="[ and ] change it">
                    {GRIDS.map((grid) => <option key={grid} value={grid}>{grid}</option>)}
                </select>
            </Option>
            <Toggle className={css.toggle} pressed={options.snap} onPressedChange={(snap) => set({ snap })} title="Snap to the grid, to other rooms' corners and walls and to 45° (Shift or Alt while drawing: free)">snap</Toggle>
            {tool === 'room' || tool === 'corridor' ? <>{number('floor', 'floor')}{number('ceiling', 'ceiling')}</> : null}
            {tool === 'corridor' ? number('width', 'width', { min: 64 }) : null}
            {tool === 'opening' ? <>{number('openingWidth', 'width', { min: 32 })}{number('openingHeight', 'height', { min: 64 })}</> : null}
            {tool === 'stairs' ? <>{number('rise', 'rise', { title: 'How far the floor climbs from the low side to the high side' })}{number('steps', 'steps', { min: 0, title: '0: a ramp' })}</> : null}
            {tool === 'level' ? number('levelRise', 'rise', { title: 'The level\'s floor above the room\'s (below zero: sunken)' }) : null}
            {tool === 'platform' ? number('platformRise', 'rise', { min: 1 }) : null}
            <PlacingOptions set={set} />
            <PartTwoOptions set={set} />
            {tool === 'door' ? (
                <ToggleGroup className={css.presets} value={[options.door]} onValueChange={(value) => value.length > 0 && set({ door: String(value[0]) })} aria-label="Door presets">
                    {DOOR_PRESETS.map((preset) => (
                        <Toggle key={preset.name} value={preset.name} className={css.preset} title={Object.entries(preset.words).map(([k, v]) => `${k}: ${String(v)}`).join(', ')}
                            data-testid={`door-${preset.name}`}>{preset.label}</Toggle>
                    ))}
                </ToggleGroup>
            ) : null}
            <span className={css.hint} title={hint ?? info.help}>{hint ?? info.help}</span>
            <button type="button" className={css.button} disabled={!undo} onClick={() => actions.undo()} data-testid="undo"
                title={undo ? `Undo your "${undo.label ?? `#${undo.sequence}`}" (Ctrl Z): agents' changes are never undone by it` : 'Nothing of yours to undo'}>Undo</button>
            <button type="button" className={css.button} disabled={!redo} onClick={() => actions.redo()} data-testid="redo"
                title={redo ? `Redo (Ctrl Y): ${redo.label ?? `#${redo.sequence}`}` : 'Nothing to redo'}>Redo</button>
        </div>
    );
}

// The placing tools' and the link's options (3.9: the active tool's settings).
function PlacingOptions({ set }: { set: (change: Partial<ToolOptions>) => void })
{
    const actions = useActions();
    const tool = useS((s) => s.tool);
    const options = useS((s) => s.toolOptions);
    const tree = useS((s) => (s.project.state === 'ready' ? s.project.value.files['project.yml']?.tree : undefined));
    const [neighbour, setNeighbour] = useState('');
    // Where the party arrives on the other map ([x, y, z]): an exit cannot lead to a neighbour without it.
    const [arrival, setArrival] = useState<[number, number, number]>([0, 0, 0]);
    const number = (name: keyof ToolOptions, label: string, extra: { min?: number; title?: string } = {}) => (
        <Option label={label}><NumberInput value={options[name] as number} onCommit={(value) => set({ [name]: value })} width="narrow" integer testId={`option-${name}`} {...extra} /></Option>
    );
    const text = (name: keyof ToolOptions, label: string, placeholder: string) => (
        <Option label={label}><TextInput value={options[name] as string} onCommit={(value) => set({ [name]: value })} placeholder={placeholder} testId={`option-${name}`} /></Option>
    );
    const pick = <T extends string>(name: keyof ToolOptions, values: readonly T[], label: string) => (
        <Option label={label}>
            <select className={css.select} value={String(options[name])} onChange={(event) => set({ [name]: typeof options[name] === 'number' ? Number(event.target.value) : event.target.value })} data-testid={`option-${name}`}>
                {values.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
        </Option>
    );
    const withEvent = <Toggle className={css.toggle} pressed={options.withEvent} onPressedChange={(on) => set({ withEvent: on })} title="Make its own event with it (preset chest or exit), in the same history entry">with event</Toggle>;
    const neighbours = Array.isArray(tree?.neighbours) ? (tree!.neighbours as Record<string, unknown>[]).map((entry) => String(entry.id)) : [];
    // The map card's slots as the game reads them (project.resolve card: project.yml, or the reference map's row).
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : ''));
    const [slots, setSlots] = useState<string[]>([]);
    useEffect(() =>
    {
        if (tool !== 'spawn')
        {
            return;
        }
        let live = true;
        void actions.resolveCard().then((card) =>
        {
            if (live)
            {
                setSlots((card?.slots ?? []).map((slot) => `${slot.slot} ${slot.monster}`));
            }
        });
        return () => { live = false; };
    }, [actions, tool, revision]);
    switch (tool)
    {
    case 'switch':
        return <>{pick('switchKind', ['lever', 'button', 'plate'], 'kind')}{number('switchHeight', 'height', { min: 0, title: '0: the kind\'s own (a lever 122, a plate 96)' })}</>;
    case 'chest':
        return <>{pick('chestKind', CHEST_KINDS, 'kind')}{withEvent}</>;
    case 'exit':
        return (
            <>
                <Option label="leads to">
                    <select className={css.select} value={options.exitTo} onChange={(event) => set({ exitTo: event.target.value })} data-testid="option-exitTo">
                        <option value="">(a neighbour)</option>
                        {neighbours.map((id) => <option key={id} value={id}>{id}</option>)}
                    </select>
                </Option>
                <Option label="new neighbour">
                    <TextInput value={neighbour} onCommit={setNeighbour} placeholder="map stem (oute3)" testId="option-new-neighbour" />
                </Option>
                <Option label="arriving at">
                    {arrival.map((value, index) => (
                        <NumberInput key={index} value={value} width="narrow" integer testId={`option-arrival-${index}`}
                            onCommit={(next) => setArrival((old) => old.map((entry, i) => (i === index ? next : entry)) as [number, number, number])} />
                    ))}
                </Option>
                <button type="button" className={css.button} disabled={!neighbour.trim()} data-testid="add-neighbour"
                    title="Add a neighbour to the map card (project.yml neighbours): where an exit leads"
                    onClick={() => void actions.edit({ label: `neighbour ${neighbour}`, ops: [{ op: 'add', to: 'neighbours', file: 'project.yml', value: { to: neighbour.trim(), kind: 'door', arrival } }] })
                        .then((result) =>
                        {
                            const made = result?.ids_allocated?.[0];
                            if (made)
                            {
                                set({ exitTo: made.slice(made.indexOf('#') + 1) });
                                setNeighbour('');
                            }
                        })}>+ neighbour</button>
                {withEvent}
            </>
        );
    case 'spawn':
        return <>{pick('spawnSlot', ['1', '2', '3'], `slot${slots.length ? ` (${slots.join(', ')})` : ''}`)}{pick('spawnTier', ['a', 'b', 'c'], 'tier')}{number('spawnRadius', 'radius', { min: 0 })}</>;
    case 'monster':
        return text('monster', 'monster', 'number or name');
    case 'item':
        return text('item', 'item', 'number or name');
    case 'decoration':
        return <>{text('decoration', 'decoration', 'torch01 (or the Library)')}{number('wallHeight', 'on a wall: height', { min: 0 })}</>;
    case 'light':
        return <>{number('lightRadius', 'radius', { min: 16 })}{number('lightHeight', 'height', { min: 0, title: '0: three quarters of the room\'s height' })}</>;
    case 'sound':
        return <>{text('sound', 'sound', 'the world\'s sound file')}{number('soundRadius', 'radius', { min: 16 })}</>;
    case 'placeholder':
        return text('standsFor', 'stands for', 'a statue of the founder');
    case 'link':
        return pick('linkVerb', ['toggles', 'opens', 'closes'], 'verb');
    default:
        return null;
    }
}

// Part two's tools' settings: the plan's words, the moving blocks, floors, ladders and the per-word tools of a room.
const SPACE_KINDS = ['room', 'corridor', 'void', 'zone', 'junction'];
const SIZE_CLASSES = ['XS', 'S', 'M', 'L', 'XL'];
const LINK_KINDS = ['open', 'door', 'double_door', 'secret_door', 'portcullis', 'stairs', 'ramp', 'lift', 'drop', 'ladder', 'teleport', 'overlook'];
const GOAL_KINDS = ['reach', 'take', 'kill', 'use', 'set'];

function PartTwoOptions({ set }: { set: (change: Partial<ToolOptions>) => void })
{
    const tool = useS((s) => s.tool);
    const options = useS((s) => s.toolOptions);
    const plan = useS((s) => (s.project.state === 'ready' ? s.project.value.files['plan.yml']?.tree : undefined));
    const rooms = useS((s) => (s.project.state === 'ready' ? s.project.value.files['rooms.yml']?.tree.rooms : undefined));
    const number = (name: keyof ToolOptions, label: string, extra: { min?: number; title?: string } = {}) => (
        <Option label={label}><NumberInput value={options[name] as number} onCommit={(value) => set({ [name]: value })} width="narrow" integer testId={`option-${name}`} {...extra} /></Option>
    );
    const pick = (name: keyof ToolOptions, values: readonly string[], label: string, labels?: Record<string, string>) => (
        <Option label={label}>
            <select className={css.select} value={String(options[name])} onChange={(event) => set({ [name]: event.target.value })} data-testid={`option-${name}`}>
                {values.map((value) => <option key={value} value={value}>{labels?.[value] ?? value}</option>)}
            </select>
        </Option>
    );
    switch (tool)
    {
    case 'room':
    case 'corridor':
    {
        // A planned space the room realises (else the bubble it is drawn over, if any).
        const realised = new Set((Array.isArray(rooms) ? rooms as Record<string, unknown>[] : []).map((room) => String(room.space ?? room.id)));
        const open = (Array.isArray(plan?.spaces) ? plan!.spaces as Record<string, unknown>[] : []).map((space) => String(space.id)).filter((id) => !realised.has(id));
        return open.length > 0 ? pick('space', ['', ...open], 'for space', { '': '(the bubble under it)' }) : null;
    }
    case 'space':
        return <>{pick('spaceKind', SPACE_KINDS, 'kind')}{pick('spaceSize', SIZE_CLASSES, 'size')}</>;
    case 'planlink':
        return pick('planLinkKind', LINK_KINDS, 'kind');
    case 'goal':
        return (
            <>
                {pick('goalKind', GOAL_KINDS, 'goal')}
                <Option label="what"><TextInput value={options.goalWhat} onCommit={(value) => set({ goalWhat: value })} placeholder="the abbot's ring" testId="option-goalWhat" /></Option>
            </>
        );
    case 'lift':
        return number('liftTravel', 'travel', { min: 16, title: 'How far it rises' });
    case 'mover':
        return <>{number('moverHeight', 'height', { min: 1 })}{number('moverTravelX', 'travel x')}{number('moverTravelY', 'y')}{number('moverTravelZ', 'z')}</>;
    case 'plate':
        return number('plateRise', 'rise', { min: 0, title: '0 to 8 above the floor' });
    case 'floor':
        return pick('floorKind', ['lava', 'water', 'liquid'], 'becomes');
    case 'ladder':
        return number('ladderHeight', 'height if unmeasured', { min: 0, title: '0: the climb from the foot\'s floor to the floor the drag ends on' });
    case 'points':
        return <>{pick('pointsOn', ['floor', 'ceiling'], 'on the')}{number('pointHeight', 'height', { title: 'Above the room\'s floor (or ceiling) when made' })}{number('pointStep', 'PgUp/PgDn step', { min: 1 })}</>;
    case 'parapet':
        return number('parapetHeight', 'height', { min: 8 });
    case 'beam':
        return <>{number('beamWidth', 'width', { min: 8 })}{number('beamDepth', 'depth', { min: 8 })}{number('beamBottom', 'underside above floor', { min: 0, title: '0: its depth and 32 under the ceiling' })}</>;
    case 'ceiling':
        return number('ceilingRise', 'rise', { min: 16, title: 'How far above the room\'s ceiling' });
    default:
        return null;
    }
}

// The project's settings (2.8, 2.15): its protection (the hand-edit mark: set by a person's first change or here,
// cleared only here) and its keys (format 1, written on the next write of each file, or all at once).
export function ProjectSettings()
{
    const actions = useActions();
    const project = useS((s) => (s.project.state === 'ready' ? s.project.value : null));
    const [clearing, setClearing] = useState(false);
    const [busy, setBusy] = useState(false);
    const [message, setMessage] = useState<string | null>(null);
    const [migration, setMigration] = useState<ProjectMigrateResult | null>(null);
    if (!project)
    {
        return null;
    }
    const card = project.files['project.yml']?.tree as Record<string, unknown> | undefined;
    const mark = project.hand_edited;
    const formats = (['rooms.yml', 'objects.yml', 'wiring.yml', 'plan.yml', 'sketch.yml'] as const)
        .filter((file) => project.files[file] && Number(project.files[file]!.tree.format ?? 0) < 1);
    const run = async (work: () => Promise<string | null>) =>
    {
        setBusy(true);
        setMessage(await work());
        setBusy(false);
    };
    return (
        <Popover.Root onOpenChange={(open) => { if (!open) { setClearing(false); setMigration(null); setMessage(null); } }}>
            <Popover.Trigger className={`${css.settingsButton} ${mark ? css.marked : ''}`} data-testid="project-settings"
                title={mark ? 'Edited by hand: the project\'s settings' : 'The project\'s settings'}>
                Project{mark ? <span className={css.markTag}>by hand</span> : null}
            </Popover.Trigger>
            <Popover.Portal>
                <Popover.Positioner sideOffset={6} align="end" className={css.positioner}>
                    <Popover.Popup className={css.settings} data-testid="settings-popup">
                        <h3 className={css.settingsTitle}>{String(card?.name ?? '')} <span className={css.dim}>{String(card?.id ?? '')} · {String(card?.world ?? '')} · {String(card?.kind ?? '')}</span></h3>
                        <section className={css.settingsSection}>
                            <h4>Protection</h4>
                            {mark ? (
                                <>
                                    <p className={css.markLine}><b>Edited by hand</b> since {mark.since} (the last state agents alone made: revision {mark.revision.slice(0, 8)}).</p>
                                    <p className={css.dim}>{mark.message}</p>
                                    {mark.history_known_from ? <p className={css.dim}>History before {mark.history_known_from} is not known here: objects changed by hand then are not listed.</p> : null}
                                    {clearing ? (
                                        <div className={css.confirm}>
                                            <p>Without the mark a generator may be run on this project again, and a generator run erases every hand edit. Clear it?</p>
                                            <button type="button" className={css.danger} disabled={busy} onClick={() => run(async () => { const error = await actions.protect(true); setClearing(false); return error; })}>Clear the mark</button>
                                            <button type="button" className={css.button} onClick={() => setClearing(false)}>Keep it</button>
                                        </div>
                                    ) : <button type="button" className={css.button} onClick={() => setClearing(true)} data-testid="clear-mark">Clear the mark…</button>}
                                </>
                            ) : (
                                <>
                                    <p>Not marked: agents may still regenerate this project from its scripts. A person's first change here marks it; a person who edits its files in a text editor marks it here.</p>
                                    <button type="button" className={css.button} disabled={busy} onClick={() => run(() => actions.protect(false))} data-testid="protect">Protect this project</button>
                                </>
                            )}
                        </section>
                        {isOutdoorFiles(project.files) ? <HandMadeSetting /> : null}
                        <section className={css.settingsSection}>
                            <h4>Keys</h4>
                            {formats.length > 0 ? (
                                <p>{formats.join(', ')} {formats.length === 1 ? 'is' : 'are'} format 0: the keys of pillars, platforms, levels and parts are read from their places and written with each file's next change.</p>
                            ) : <p className={css.dim}>The files are format 1: every selectable part has its key.</p>}
                            {migration ? (
                                <div className={css.confirm}>
                                    <p>{migration.keys_written} keys in {migration.files.length} files ({migration.files.join(', ') || 'none'}) would be written, as one history entry.</p>
                                    <button type="button" className={css.button} disabled={busy || migration.files.length === 0}
                                        onClick={() => run(async () => { const answer = await actions.migrate(false); setMigration(null); return typeof answer === 'string' ? answer : `Written: ${answer.keys_written} keys.`; })}>Write them</button>
                                    <button type="button" className={css.button} onClick={() => setMigration(null)}>Not now</button>
                                </div>
                            ) : (
                                <button type="button" className={css.button} disabled={busy} data-testid="migrate"
                                    onClick={() => run(async () => { const answer = await actions.migrate(true); if (typeof answer === 'string') { return answer; } setMigration(answer); return null; })}>Write all keys now…</button>
                            )}
                        </section>
                        {message ? <p className={css.message}>{message}</p> : null}
                    </Popover.Popup>
                </Popover.Positioner>
            </Popover.Portal>
        </Popover.Root>
    );
}

// Above the views: an outside rewrite of a hand-edited project (2.8 point 3) with its one revert step, and an undo
// or revert that left objects alone because someone changed them since (2.7).
export function AuthorBanners()
{
    const actions = useActions();
    const { store } = useStudioContext();
    const history = useS((s) => (s.history.state === 'ready' ? s.history.value.entries : NONE));
    const dismissed = useS((s) => s.dismissedNotices);
    const conflict = useS((s) => s.edits.conflict ?? null);
    const notice = useMemo(() => openNotice(history, new Set(dismissed)), [history, dismissed]);
    if (!notice && !conflict)
    {
        return null;
    }
    return (
        <div className={css.banners}>
            {notice ? (
                <div className={css.noticeBad} role="alert" data-testid="outside-notice">
                    <span><b>Entry #{notice.sequence} ({notice.author}) rewrote hand-edited work:</b> {notice.notice!.join(' ')}</span>
                    <button type="button" className={css.danger} onClick={() => actions.revertEntry(notice.sequence)} data-testid="revert-notice">Revert entry #{notice.sequence}</button>
                    <button type="button" className={css.button} onClick={() => actions.dismissNotice(notice.sequence)}>Keep it</button>
                </div>
            ) : null}
            {conflict ? (
                <div className={css.noticeWarn} data-testid="conflict">
                    <span><b>{conflict.kind === 'redo' ? 'Redo' : conflict.kind === 'undo' ? 'Undo' : 'Revert'} left {conflict.conflicts.length} {conflict.conflicts.length === 1 ? 'object' : 'objects'} alone</b>, changed by someone since: {conflict.conflicts.join(', ')}</span>
                    {conflict.sequence ? <button type="button" className={css.button} onClick={() => { actions.revertEntry(conflict.sequence!, true); store.setState((s) => ({ edits: { ...s.edits, conflict: null } })); }}>Put them back anyway</button> : null}
                    <button type="button" className={css.button} onClick={() => store.setState((s) => ({ edits: { ...s.edits, conflict: null } }))}>Leave them</button>
                </div>
            ) : null}
        </div>
    );
}
