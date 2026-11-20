// The views (S5_BROWSER_EDITOR.md 3.4, 3.5): the plan view and the 3D view, framework-free modules that React
// mounts and feeds from the store. Selection and hover are shared; Q maximises the view under the cursor, F frames
// the selection.
import { useEffect, useMemo, useRef, useState } from 'react';
import { Toggle } from '@base-ui/react/toggle';
import { PlanView, planBands } from '../plan/PlanView.ts';
import type { PlanBand } from '../plan/PlanView.ts';
import { Viewport } from '../viewport/Viewport.ts';
import { treeOf } from '../model/objects.ts';
import { mark, probe } from '../app/controller.ts';
import { NONE } from '../state/store.ts';
import type { CompareJobResult } from '../../../schema/rpc/generated/rpc.ts';
import { planHeat } from '../model/compare.ts';
import { latestJobs } from '../model/scorecard.ts';
import { CompareView } from './Compare.tsx';
import { FlowView } from './Flow.tsx';
import { SwitchBoard } from './Board.tsx';
import { ASSET_MIME } from '../edit/drop.ts';
import type { LibraryAsset } from '../edit/drop.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import { ToolController, besideOffset } from '../edit/tools.ts';
import { PLACING_TOOLS, nextGrid, toolsOf } from '../edit/stages.ts';
import { isOutdoorFiles } from '../edit/outdoortools.ts';
import type { Controller } from '../app/controller.ts';
import type { ToolName } from '../edit/stages.ts';
import type { ToolHost } from '../edit/toolbase.ts';
import type { Store } from '../state/store.ts';
import type { Actions } from '../app/controller.ts';
import { duplicateOps, idsOf, removeOps } from '../edit/ops.ts';
import { ToolBar } from './Author.tsx';
import { TravelScrubber } from './Scrubber.tsx';
import { SectionPanel } from './Section.tsx';
import { ghostOf } from '../plan/ghost.ts';
import css from './Views.module.css';

// The file of an address picked on the plan (rooms and openings live in rooms.yml).
export function fileOfAddress(address: string): string | undefined
{
    return address.startsWith('room:') || address.startsWith('open') ? 'rooms.yml' : address.startsWith('evt:') ? 'wiring.yml'
        : address.startsWith('space:') || address.startsWith('link:') || address.startsWith('goal:') ? 'plan.yml' : undefined;
}

// A Library asset carried by a drag, or null.
function draggedAsset(event: React.DragEvent): LibraryAsset | null
{
    const text = event.dataTransfer.getData(ASSET_MIME);
    try
    {
        return text ? (JSON.parse(text) as LibraryAsset) : null;
    }
    catch
    {
        return null;
    }
}

function acceptsAsset(event: React.DragEvent): boolean
{
    if (!event.dataTransfer.types.includes(ASSET_MIME))
    {
        return false;
    }
    event.preventDefault();
    event.dataTransfer.dropEffect = 'copy';
    return true;
}

export function Views()
{
    const { store } = useStudioContext();
    const mode = useS((s) => s.viewMode);
    const maximised = useS((s) => s.maximised);
    const author = useS((s) => s.mode === 'author');
    const under = useRef<'plan' | '3d' | null>(null);
    const actions = useActions();
    useEffect(() =>
    {
        // Author mode's keys (3.17): undo and redo, Delete, Ctrl D, the stages 1 to 7, a key per tool, the grid.
        const authorKey = (event: KeyboardEvent): boolean =>
        {
            const state = store.getState();
            const ctrl = event.ctrlKey || event.metaKey;
            if (ctrl && event.code === 'KeyZ' && !event.shiftKey)
            {
                event.preventDefault();
                actions.undo();
                return true;
            }
            if (ctrl && (event.code === 'KeyY' || (event.code === 'KeyZ' && event.shiftKey)))
            {
                event.preventDefault();
                actions.redo();
                return true;
            }
            if (ctrl && event.code === 'KeyS')
            {
                event.preventDefault();
                const saved = state.edits.saved;
                actions.notify(state.edits.pending > 0 ? `Writing ${state.edits.pending} change(s)…` : saved
                    ? `Nothing to save: every change is written (saved at rev ${saved.revision.slice(0, 8)})` : 'Nothing to save: every change is written as you make it');
                return true;
            }
            const files = state.project.state === 'ready' ? state.project.value.files : undefined;
            const selection = state.selection;
            if (ctrl && event.code === 'KeyD' && selection && files)
            {
                event.preventDefault();
                const ops = duplicateOps(files, idsOf(files), selection.id, besideOffset(files, selection.id, state.toolOptions.grid), selection.file);
                if (ops.length > 0)
                {
                    void actions.edit({ label: `duplicate ${selection.id}`, ops });
                }
                return true;
            }
            if (ctrl || event.altKey)
            {
                return false;
            }
            if (event.code === 'Delete' && selection && files)
            {
                event.preventDefault();
                void actions.edit({ label: `remove ${selection.id}`, ops: removeOps(files, idsOf(files), selection.id, selection.file) }).then((result) =>
                {
                    if (result)
                    {
                        actions.select(null);
                    }
                });
                return true;
            }
            const digit = /^Digit([1-7])$/.exec(event.code);
            if (digit)
            {
                actions.setStage(Number(digit[1]));
                return true;
            }
            if (event.code === 'BracketLeft' || event.code === 'BracketRight')
            {
                const grid = nextGrid(state.toolOptions.grid, event.code === 'BracketRight' ? 1 : -1);
                store.setState({ toolOptions: { ...state.toolOptions, grid } });
                return true;
            }
            const tool = toolsOf(isOutdoorFiles(files)).find((entry) => entry.code === event.code && Boolean(entry.shift) === event.shiftKey);
            if (tool)
            {
                actions.setTool(tool.name);
                return true;
            }
            return false;
        };
        const onKey = (event: KeyboardEvent) =>
        {
            const target = event.target as HTMLElement | null;
            if (target?.closest('input, textarea, select, .cm-editor, [contenteditable]'))
            {
                return;
            }
            if ((event.ctrlKey || event.metaKey) && store.getState().mode === 'author' && authorKey(event))
            {
                return;
            }
            if (event.ctrlKey || event.metaKey || event.altKey)
            {
                return;
            }
            const state = store.getState();
            if (state.mode === 'author' && authorKey(event))
            {
                return;
            }
            if (event.code === 'KeyQ' && under.current)
            {
                const current = store.getState().maximised;
                store.setState({ maximised: current ? null : under.current });
            }
            else if (event.code === 'KeyF')
            {
                const selection = store.getState().selection;
                actions.select(selection, true);
                if (!selection)
                {
                    store.setState((s) => ({ frameRequest: { serial: s.frameRequest.serial + 1 } }));
                }
            }
            else if (event.code === 'KeyG' && !event.shiftKey)
            {
                // Walk mode (S5_BROWSER_EDITOR.md 3.6).
                event.preventDefault();
                actions.toggleWalk();
            }
            else if (event.code === 'F5')
            {
                // Play here: the real game at this camera (the browser's reload is taken: 3.17).
                event.preventDefault();
                actions.playHere();
            }
            else if (event.code === 'KeyP' && !event.shiftKey)
            {
                // A pin on what is under the pointer, in the view under it (S5_BROWSER_EDITOR.md 3.13).
                event.preventDefault();
                const state = store.getState();
                const where = under.current ?? (state.viewMode === 'plan' ? 'plan' : '3d');
                actions.startPin(where);
            }
            else if (event.code === 'Escape')
            {
                if (store.getState().pinDraft)
                {
                    actions.cancelPin();
                }
                else
                {
                    actions.select(null);
                }
            }
        };
        window.addEventListener('keydown', onKey);
        return () => window.removeEventListener('keydown', onKey);
    }, [store, actions]);
    if (mode === 'compare')
    {
        return <div className={css.views}><div className={css.pane} onPointerEnter={() => (under.current = '3d')}><CompareView /></div></div>;
    }
    if (mode === 'board')
    {
        // The switch board beside the plan (3.7): a cell clicked is one change of one event.
        return (
            <div className={css.authored}>
                {author ? <ToolBar /> : null}
                <div className={css.views} data-split="" data-flow="">
                    <div className={css.pane}><SwitchBoard /></div>
                    <div className={css.pane} onPointerEnter={() => (under.current = 'plan')}><PlanPane /></div>
                </div>
            </div>
        );
    }
    if (mode === 'flow')
    {
        // The graph beside the plan: a node clicked selects its room there.
        return (
            <div className={css.views} data-split="" data-flow="">
                <div className={css.pane}><FlowView /></div>
                <div className={css.pane} onPointerEnter={() => (under.current = 'plan')}><PlanPane /></div>
            </div>
        );
    }
    const showPlan = maximised ? maximised === 'plan' : mode !== '3d';
    const show3d = maximised ? maximised === '3d' : mode !== 'plan';
    const panes = (
        <div className={css.views} data-split={showPlan && show3d ? '' : undefined}>
            {showPlan ? <div className={css.pane} onPointerEnter={() => (under.current = 'plan')}><PlanPane /></div> : null}
            {show3d ? <div className={css.pane} onPointerEnter={() => (under.current = '3d')}><ViewportPane /></div> : null}
        </div>
    );
    return author ? <div className={css.authored}><ToolBar />{panes}</div> : panes;
}

// What a tool asks of the app (edit/toolbase.ts ToolHost), for the plan or the 3D view.
function toolHost(store: Store, actions: Actions, view: { redraw(): void; unitsPerPixel(): number }, controller?: Controller | null): ToolHost
{
    return {
        // Outdoors (S5b2): the brush's preview in the 3D view, and the built land's heights (view.terrain_query).
        landPreview: (delta) => (probe().viewport as Viewport | undefined)?.previewLand(delta),
        terrainHeights: async (cells) =>
        {
            const project = store.getState().projectKey;
            if (!controller || !project)
            {
                return null;
            }
            try
            {
                const answer = await controller.client.call('view.terrain_query', { project, points: cells.map((cell) => [cell[0], cell[1]]) });
                return answer.points.map((point) => point.height);
            }
            catch
            {
                return null;
            }
        },
        files: () => { const project = store.getState().project; return project.state === 'ready' ? project.value.files : undefined; },
        layout: () => { const current = store.getState().layout; return current.state === 'ready' ? current.value : null; },
        options: () => store.getState().toolOptions,
        selection: () => store.getState().selection?.id ?? null,
        select: (address, file) => actions.select(address ? { id: address, file: file ?? fileOfAddress(address) } : null),
        edit: (gesture) => actions.edit(gesture),
        hint: (text) => store.setState({ hint: text }),
        note: (text) => actions.notify(text),
        redraw: () => view.redraw(),
        unitsPerPixel: () => view.unitsPerPixel(),
        colour: (name) => getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim() || '#888888',
        setTool: (name) => actions.setTool(name),
        setOptions: (change) => store.setState((s) => ({ toolOptions: { ...s.toolOptions, ...change } })),
    };
}

// Placing in 3D (S5_BROWSER_EDITOR.md 3.18: "click (a wall for wall decorations and torches)"): a click on a face with a
// placing tool (or Floor) is the same tool's click on the plan at the place the face says: on a wall a step into the
// room in front of it (the tool finds the wall), on a floor or a block's top that point.
export function planPointOfPick(pick: { point: [number, number, number]; normal?: [number, number, number] }, tool: ToolName): [number, number]
{
    const n = pick.normal ?? [0, 0, 1];
    const wall = Math.abs(n[2]) < 0.5;
    const onWall = tool === 'switch' || tool === 'exit' || tool === 'decoration';
    const step = wall ? (onWall ? 6 : 64) : 0;
    return [Math.round(pick.point[0] + n[0] * step), Math.round(pick.point[1] + n[1] * step)];
}

// Outdoors (S5b2) the tools that place at a point: a click on the land or a model in 3D places there.
const PLACE_IN_3D: ToolName[] = [...PLACING_TOOLS, 'floor', 'actor', 'structure', 'arrival', 'hpoint', 'spire'];

function PlanPane()
{
    const { store, controller } = useStudioContext();
    const actions = useActions();
    const host = useRef<HTMLDivElement>(null);
    const [plan, setPlan] = useState<PlanView | null>(null);
    const layout = useS((s) => s.layout);
    const pins = useS((s) => (s.pins.state === 'ready' ? s.pins.value.pins : NONE));
    const selection = useS((s) => s.selection);
    const hover = useS((s) => s.hover);
    const bandIndex = useS((s) => s.band);
    const frameRequest = useS((s) => s.frameRequest);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));

    const bands = useMemo<PlanBand[]>(() =>
    {
        if (layout.state !== 'ready' || layout.value.kind !== 'indoor')
        {
            return [];
        }
        const spaces = new Map<string, string>();
        const rooms = treeOf(files, 'rooms.yml')?.rooms;
        if (Array.isArray(rooms))
        {
            for (const room of rooms as Record<string, unknown>[])
            {
                if (typeof room.id === 'string')
                {
                    spaces.set(room.id, typeof room.space === 'string' ? room.space : room.id);
                }
            }
        }
        return planBands(layout.value, treeOf(files, 'plan.yml') as Record<string, unknown> | undefined, spaces);
    }, [layout, files]);

    useEffect(() =>
    {
        const view = new PlanView(host.current!, {
            onHover: (owner, world) => store.setState({
                hover: owner ? { owner } : null,
                cursor: world ? [Math.round(world[0]), Math.round(world[1]), store.getState().cursor?.[2] ?? 0] : store.getState().cursor,
            }),
            onPick: (owner) =>
            {
                if (owner?.startsWith('pin:'))
                {
                    actions.selectPin(owner);
                    store.setState({ drawerTab: 'pins' });
                    return;
                }
                // A plan bubble or link names its file (plan.yml#space:x): a space may share its id with its room.
                const hash = owner ? owner.indexOf('#') : -1;
                actions.select(owner ? hash > 0 ? { id: owner.slice(hash + 1), file: owner.slice(0, hash) } : { id: owner, file: fileOfAddress(owner) } : null);
            },
        });
        setPlan(view);
        probe().plan = view;
        controller?.attachPlan(view);
        return () =>
        {
            controller?.attachPlan(null);
            view.dispose();
        };
    }, [store, actions, controller]);
    useEffect(() =>
    {
        if (plan)
        {
            plan.setLayout(layout.state === 'ready' ? layout.value : null);
            if (layout.state === 'ready')
            {
                plan.drawNow();
                mark('plan');
            }
        }
    }, [plan, layout]);
    // Author mode (S5b1): the files drawn as they are, and the active tool on the plan.
    const author = useS((s) => s.mode === 'author');
    const toolName = useS((s) => s.tool);
    const tools = useMemo(() => (plan ? new ToolController(toolHost(store, actions, { redraw: () => plan.redraw(), unitsPerPixel: () => plan.unitsPerPixel() }, controller)) : null),
        [plan, store, actions, controller]);
    const outdoor = isOutdoorFiles(files);
    useEffect(() =>
    {
        if (!plan)
        {
            return;
        }
        if (author && tools)
        {
            tools.setTool(toolName);
            plan.setTool(tools);
        }
        else
        {
            plan.setTool(null);
        }
        probe().plan = plan;
        (probe() as { tools?: unknown }).tools = tools;
    }, [plan, tools, author, toolName, outdoor]);
    const planStage = useS((s) => s.stage === 1);
    useEffect(() => plan?.setSource(author && files ? { files, selection: selection?.id ?? null, planStage, outdoor } : null), [plan, author, files, selection, planStage, outdoor]);
    const selectedPin = useS((s) => s.selectedPin);
    const ghost = useS((s) => s.ghost);
    useEffect(() => plan?.setGhost(ghost?.layout ? ghostOf(ghost.sequence, ghost.layout) : null), [plan, ghost]);
    // The compare's heat (S5a5): the newest compare's points and worst places, when shown.
    const compareHeat = useS((s) => s.compareHeat);
    const compare = useS((s) =>
    {
        const { done } = latestJobs(s.jobs.state === 'ready' ? s.jobs.value : NONE, 'compare', null);
        return done ? (s.jobResults[done.id] as CompareJobResult | undefined) ?? null : null;
    });
    useEffect(() => plan?.setHeat(compareHeat ? planHeat(compare) : null), [plan, compareHeat, compare]);
    useEffect(() => plan?.setPins(pins), [plan, pins]);
    useEffect(() => plan?.setSelectedPin(selectedPin), [plan, selectedPin]);
    useEffect(() => plan?.setSelection(selection?.id ?? null), [plan, selection]);
    useEffect(() => plan?.setHover(hover?.owner.split('/')[0] ?? null), [plan, hover]);
    useEffect(() => plan?.setBand(bandIndex !== null ? bands[bandIndex] ?? null : null), [plan, bands, bandIndex]);
    const firstFrame = useRef(frameRequest.serial);
    useEffect(() =>
    {
        if (plan && frameRequest.serial !== firstFrame.current)
        {
            if (frameRequest.at)
            {
                plan.frameObject(null, frameRequest.at);
            }
            else if (store.getState().selection)
            {
                plan.frameObject(store.getState().selection!.id);
            }
            else
            {
                plan.frameAll();
            }
        }
    }, [plan, frameRequest, store]);

    return (
        <div className={css.inner}>
            <div className={css.toolbar}>
                <span className={css.label}>Plan</span>
                {bands.length > 0 ? (
                    <span className={css.bands} role="tablist" aria-label="Height bands">
                        <button type="button" className={bandIndex === null ? css.bandOn : css.band} onClick={() => store.setState({ band: null })}>all</button>
                        {bands.map((band, index) => (
                            <button type="button" key={index} className={bandIndex === index ? css.bandOn : css.band}
                                onClick={() => store.setState({ band: index })} title={`${band.rooms.size} rooms`}>{band.label}</button>
                        ))}
                    </span>
                ) : null}
                <span className={css.spacer} />
                {compare ? (
                    <Toggle className={css.toggle} pressed={compareHeat} onPressedChange={(on) => store.setState({ compareHeat: on })}
                        title={`The compare's score at every ${compare.kind === 'outdoor' ? 'block of 16 x 16 cells' : 'stand point'} (green 100 %, yellow 70 %, red 40 % and under) and its worst places`}
                        data-testid="heat-toggle">compare heat</Toggle>
                ) : null}
                <button type="button" className={css.button} onClick={() => plan?.frameAll()}>Frame all</button>
            </div>
            <div ref={host} className={css.surface} data-testid="plan-surface"
                onDragOver={(event) => acceptsAsset(event)}
                onDrop={(event) =>
                {
                    const asset = draggedAsset(event);
                    const at = asset ? plan?.worldAt(event.clientX, event.clientY) : null;
                    if (asset && at && plan)
                    {
                        event.preventDefault();
                        actions.dropAsset(asset, { where: 'plan', at: [Math.round(at[0]), Math.round(at[1])], shift: event.shiftKey, alt: event.altKey, reach: 14 * plan.unitsPerPixel() });
                    }
                }}>
                {author && layout.state === 'error' ? <div className={css.overlayBottom}>No built view yet: {layout.message}. The plan draws the files.</div>
                    : <ViewState state={layout} what="plan" />}
                {layout.state === 'ready' && layout.value.kind === 'indoor' ? <SectionPanel plan={plan} /> : null}
            </div>
        </div>
    );
}

function ViewState({ state, what }: { state: { state: string; message?: string; kind?: string }; what: string })
{
    if (state.state === 'ready')
    {
        return null;
    }
    const text = state.state === 'loading' ? `Making the ${what}…`
        : state.state === 'error' ? (state.kind === 'has_errors'
            ? `The project has errors, so it does not lower and there is no ${what} yet (the Issues drawer lists them; S5b1 draws the rest of such a map).`
            : `No ${what}: ${state.message}`)
        : state.state === 'idle' ? '' : '';
    return text ? <div className={state.state === 'error' ? css.overlayBad : css.overlay}>{text}</div> : null;
}

// What walk mode is and is not (S5_BROWSER_EDITOR.md 3.6), and how to get the mouse.
function WalkBanner({ state, message, locked }: { state: string; message?: string; locked: boolean })
{
    if (state === 'starting' || state === 'error')
    {
        return <div className={state === 'error' ? css.overlayBad : css.overlay} data-testid="walk-banner">{state === 'error' ? `Walk mode: ${message}` : message}</div>;
    }
    return (
        <div className={css.walkBanner} data-testid="walk-banner">
            Walk mode collides like the game. Events, monsters and traps do not run: use Play here (F5).
            {locked ? null : <b> Click the view to look around.</b>}
        </div>
    );
}

function ViewportPane()
{
    const { store, controller } = useStudioContext();
    const actions = useActions();
    const host = useRef<HTMLDivElement>(null);
    const [viewport, setViewport] = useState<Viewport | null>(null);
    const mesh = useS((s) => s.mesh);
    const textured = useS((s) => s.textured);
    const cutaway = useS((s) => s.cutaway);
    const selection = useS((s) => s.selection);
    const hover = useS((s) => s.hover);
    const frameRequest = useS((s) => s.frameRequest);
    const [note, setNote] = useState<string | null>(null);
    const walk = useS((s) => s.walk);
    const play = useS((s) => s.play);
    // The hosted page (S5c) has no game: Play here needs a paired studio.
    const hostedPage = useStudioContext().controller?.client.mode === 'hosted';
    const author = useS((s) => s.mode === 'author');

    useEffect(() =>
    {
        const view = new Viewport(host.current!, {
            onHover: (pick) => store.setState({ hover: pick ? { owner: pick.owner || '(no owner)', point: pick.point } : null, cursor: pick?.point ?? store.getState().cursor }),
            onPick: (pick) =>
            {
                const state = store.getState();
                if (pick && state.mode === 'author' && PLACE_IN_3D.includes(state.tool))
                {
                    const placing = new ToolController(toolHost(store, actions, { redraw: () => undefined, unitsPerPixel: () => 1 }, controller));
                    placing.setTool(state.tool);
                    const at = planPointOfPick(pick, state.tool);
                    const press = { button: 0, altKey: false, shiftKey: false, ctrlKey: false } as PointerEvent;
                    placing.move(at, press, false);
                    placing.down(at, press);
                    return;
                }
                actions.select(pick?.base ? { id: pick.base, file: pick.file } : null);
            },
        });
        setViewport(view);
        probe().viewport = view;
        probe().capabilities = view.capabilities;
        if (!view.capabilities.bc7 || !view.capabilities.bc1)
        {
            setNote('This browser lacks the BC texture extensions: the view is drawn untextured.');
        }
        controller?.attachViewport(view);
        const theme = window.matchMedia('(prefers-color-scheme: dark)');
        const onTheme = () => view.applyTokens();
        theme.addEventListener('change', onTheme);
        return () =>
        {
            theme.removeEventListener('change', onTheme);
            controller?.attachViewport(null);
            view.dispose();
        };
    }, [store, actions, controller]);
    const pins = useS((s) => (s.pins.state === 'ready' ? s.pins.value.pins : NONE));
    const selectedPin = useS((s) => s.selectedPin);
    useEffect(() => viewport?.setPins(pins, selectedPin), [viewport, pins, selectedPin]);
    useEffect(() => viewport?.setTextured(textured), [viewport, textured]);
    const ghost = useS((s) => s.ghost);
    useEffect(() => viewport?.setGhost(ghost?.layout ? ghostOf(ghost.sequence, ghost.layout).rooms : null), [viewport, ghost]);
    useEffect(() => viewport?.setCutaway(cutaway), [viewport, cutaway]);
    useEffect(() => viewport?.setSelection(selection?.id ?? null), [viewport, selection]);
    useEffect(() => viewport?.setHoverId(hover?.owner.split('/')[0] ?? null), [viewport, hover]);
    const firstFrame = useRef(frameRequest.serial);
    useEffect(() =>
    {
        if (viewport && frameRequest.serial !== firstFrame.current)
        {
            if (frameRequest.at)
            {
                viewport.framePoint(frameRequest.at);
            }
            else
            {
                viewport.frameObject(store.getState().selection?.id ?? null);
            }
        }
    }, [viewport, frameRequest, store]);

    return (
        <div className={css.inner}>
            <div className={css.toolbar}>
                <span className={css.label}>3D</span>
                <Toggle className={css.toggle} pressed={textured} onPressedChange={(on) => store.setState({ textured: on })}>{textured ? 'textured' : 'grey'}</Toggle>
                <Toggle className={css.toggle} pressed={cutaway} onPressedChange={(on) => store.setState({ cutaway: on })}>cutaway</Toggle>
                {mesh.state === 'ready' && mesh.value.stale ? <span className={css.stale}>stale: revision {mesh.value.view_revision.slice(0, 8)}</span> : null}
                <span className={css.spacer} />
                <span className={css.hint}>{walk.state === 'on'
                    ? 'click: look (Esc gives the mouse back) · WASD/arrows walk · Shift run · Space jump · click a door: open/shut · Esc Esc: leave'
                    : 'drag: orbit · shift/middle: pan · right: look, WASD fly · F frame · Q maximise · P pin · G walk · F5 play here'}</span>
                <Toggle className={css.toggle} pressed={walk.state === 'on' || walk.state === 'starting'} onPressedChange={() => actions.toggleWalk()}
                    data-testid="walk-toggle" title="Walk mode (G): the game's movement and collision">walk</Toggle>
                <button type="button" className={css.playButton} disabled={play.state === 'starting' || hostedPage} onClick={() => actions.playHere()}
                    data-testid="play-here" title={hostedPage ? 'Play here needs the game on your computer: pair this page with oymap studio, or export the mod and start the game'
                        : 'Play here (F5): build, install and start the game at this camera'}>
                    {play.state === 'starting' ? 'starting…' : play.state === 'running' ? 'playing…' : 'Play here'}</button>
                {walk.state === 'on' ? null : <button type="button" className={css.button} onClick={() => viewport?.frameObject(null)}>Frame all</button>}
            </div>
            <div ref={host} className={css.surface} data-testid="viewport-surface"
                onDragOver={(event) => acceptsAsset(event)}
                onDrop={(event) =>
                {
                    const asset = draggedAsset(event);
                    const pick = asset ? viewport?.pickClient(event.clientX, event.clientY) : null;
                    if (asset && pick)
                    {
                        event.preventDefault();
                        actions.dropAsset(asset, { where: '3d', owner: pick.owner, point: pick.point, ...(pick.normal ? { normal: pick.normal } : {}), alt: event.altKey });
                    }
                    else if (asset)
                    {
                        actions.notify('Drop it on a wall, a floor or a ceiling in the view');
                    }
                }}>
                {author && mesh.state === 'error' ? <div className={css.overlay}>No 3D view yet: {mesh.message}. Draw rooms on the plan; a room the core cannot build is left out and hatched there.</div>
                    : <ViewState state={mesh} what="3D view" />}
                {note ? <div className={css.overlayBottom}>{note}</div> : null}
                {walk.state !== 'off' ? <WalkBanner state={walk.state} message={walk.message} locked={walk.locked === true} /> : null}
                {walk.state === 'on' && walk.locked ? <div className={css.crosshair} aria-hidden="true" /> : null}
                <TravelScrubber viewport={viewport} />
            </div>
        </div>
    );
}
