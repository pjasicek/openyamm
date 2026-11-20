// What the app does, between the RPC client and the store (S5_BROWSER_EDITOR.md 2.5, "Opening a project"):
// project.open, then view.layout (the plan first), then view.mesh (grey 3D), then textures (lowest mips first);
// check.validate and pins.list beside them. Timing marks for the screenshot run go to window.__studio.
import type { AssetsSearchResult, CompareJobResult, EditApplyResult, Job, JobParams, Pin, PinsAddParams, ModListResult, ModMapNumberResult, ModPackResult, ProjectMigrateResult, ProjectNewParams, ProjectResolveResult, ViewMeshResult, ViewOriginalMeshResult, ViewOverlayResult, WorldViewResult } from '../../../schema/rpc/generated/rpc.ts';
import { RevisionCache, RpcCallError } from '../rpc/client.ts';
import type { StudioClient } from '../rpc/client.ts';
import type { HostNotices } from '../rpc/client.ts';
import type { ChangeNote, PinDraft, Store } from '../state/store.ts';
import { frameAt, select } from '../state/store.ts';
import type { ObjectRef } from '../model/objects.ts';
import { baseId } from '../model/objects.ts';
import { EYE_HEIGHT, cameraOfPose, changeNote, pictureRoute, pinPlace, poseOfCamera } from '../model/pins.ts';
import type { Camera, PinAction } from '../model/pins.ts';
import { loadTextures } from '../viewport/textures.ts';
import type { TextureLoadReport, TextureSink } from '../viewport/textures.ts';
import { WalkMode } from '../walk/WalkMode.ts';
import type { WalkView } from '../walk/WalkMode.ts';
import { cameraOfExitPose } from '../walk/input.ts';
import { latestJobs } from '../model/scorecard.ts';
import type { JobKind } from '../model/scorecard.ts';
import { shiftedMesh, jobRoute } from '../model/compare.ts';
import { EditSession } from '../edit/session.ts';
import type { Gesture } from '../edit/session.ts';
import { stagesOf } from '../edit/stages.ts';
import { isOutdoorFiles, outdoorDrop } from '../edit/outdoortools.ts';
import type { ToolName } from '../edit/stages.ts';
import { dropPlan } from '../edit/drop.ts';
import type { DropPlan, DropTarget, LibraryAsset, LibraryKind } from '../edit/drop.ts';
import { roomSurfacePlan, surfaceOf, themeSurfaceOp } from '../edit/surfaces.ts';
import type { SurfacePart } from '../edit/surfaces.ts';
import { allocatedId } from '../edit/ops.ts';

// What the controller asks of the 3D view (viewport/Viewport.ts) and of the plan (plan/PlanView.ts).
export interface ViewportHandle extends TextureSink, Partial<WalkView>
{
    loadMesh(meta: ViewMeshResult, bytes: ArrayBuffer, frame: boolean): void;
    textureNames(): string[];
    renderNow(): void;
    capture(maxWidth?: number, quality?: number): string;
    camera(): Camera;
    setCamera(camera: Camera): void;
    pickCentre(): { owner: string; base: string; file?: string; point: [number, number, number] } | null;
    lastHover: { owner: string; base: string; file?: string; point: [number, number, number] } | null;
}

export interface PlanHandle
{
    capture(): string;
    pointerTarget(): { owner: string | null; at: [number, number, number] } | null;
    frameObject(id: string | null, at?: [number, number, number]): void;
}

export interface StudioProbe
{
    marks: Record<string, number>;
    textures?: TextureLoadReport;
    inspector: { id: string; expanded: boolean; ms: number }[];
    errors: string[];
    viewport?: unknown;
    plan?: unknown;
    // Walk mode's session and the game's last exit pose, for scripted runs.
    walk?: unknown;
    exitPose?: unknown;
    capabilities?: unknown;
    // The store and the controller, for the screenshot run's scripted steps.
    app?: unknown;
    // The hosted page (S5c): its version and client, for scripted runs.
    hosted?: unknown;
    // From the pick to the mounted asset root, milliseconds (hosted page).
    assetsOpenMs?: number;
    // The project revision whose plan and 3D view are shown (after an open, a refresh, or an edit's views).
    viewsRevision?: string;
}

declare global
{
    interface Window
    {
        __studio?: StudioProbe;
    }
}

export function probe(): StudioProbe
{
    window.__studio ??= { marks: {}, inspector: [], errors: [] };
    return window.__studio;
}

export function mark(name: string): void
{
    probe().marks[name] = Math.round(performance.now());
}

// What the panels may ask of the app. The gallery passes a quiet one.
export interface Actions
{
    openProject(key: string): void;
    closeProject(): void;
    select(ref: ObjectRef | null, frame?: boolean): void;
    frameAt(at: [number, number, number]): void;
    revalidate(): void;
    // Pins (S5a3): a new one from the view under the pointer, its text sent; answers; going to one.
    startPin(where: 'plan' | '3d'): void;
    submitPin(text: string): Promise<void>;
    cancelPin(): void;
    actOnPin(pin: Pin, action: PinAction | 'keep', text: string): Promise<string | null>;
    selectPin(id: string | null): void;
    goToPin(pin: Pin): void;
    // An object URL of a pin's picture (read with the pairing token), or null when it is not on this machine.
    picture(relative: string): Promise<string | null>;
    loadHistory(): void;
    // Walk mode (G) and Play here (F5) (S5a4).
    toggleWalk(): void;
    // Shown unless asked otherwise; scripted runs pass a duration and more console lines (test switches).
    playHere(options?: PlayOptions): void;
    // Jobs (S5a5): started, cancelled; a job's file as an object URL (read with the pairing token), or null.
    startJob(kind: JobKind, params?: JobParams): void;
    cancelJob(id: string): void;
    jobFile(job: Job, relative: string): Promise<string | null>;
    // A picture full size.
    openLightbox(url: string, caption: string): void;
    // A reply (or resolve) to a pin with a job's picture (a pins tour's after picture); null, or the refusal's words.
    answerWithPicture(pin: Pin, job: Job, relative: string, action: 'reply' | 'resolve', text: string): Promise<string | null>;
    // The Compare view (the original beside the rebuild) and the plan's heat; a place shown in every view.
    enterCompare(): void;
    goToPlace(at: readonly number[], yaw?: number): void;
    // Author mode (S5b1): the mode, stage and tool; a gesture as one transaction; the person's undo and redo and the
    // revert of any entry (2.7); the project's protection (the hand-edit mark, 2.8), the keys' migration; a new
    // project; the effective values of an object for the inspector (project.resolve; null when the core lacks it).
    setMode(mode: 'review' | 'author'): void;
    setStage(stage: number): void;
    setTool(tool: ToolName): void;
    edit(gesture: Gesture): Promise<EditApplyResult | null>;
    undo(): void;
    redo(): void;
    revertEntry(sequence: number, force?: boolean): void;
    protect(clear: boolean): Promise<string | null>;
    migrate(dryRun: boolean): Promise<ProjectMigrateResult | string>;
    newProject(params: NewProjectInput): Promise<string | null>;
    resolve(id: string, file?: string): Promise<ProjectResolveResult | null>;
    // The map card as the game reads it (project.resolve card): its encounter slots for the Spawn tool.
    resolveCard(): Promise<ProjectResolveResult | null>;
    // History's "show as it was" (view.layout_at): the layout before an entry drawn as a ghost; null puts it away.
    showGhost(sequence: number | null): void;
    dismissNotice(sequence: number): void;
    // A short note over the views (a tool's refusal before anything is sent).
    notify(text: string): void;
    // The drawer's Library (S5b1 part 2): the asset catalogue searched; a dragged asset dropped on the plan or the
    // 3D view; a texture laid on the selected room's walls, floor or ceiling, or on a theme. The script reference's
    // function names for the Lua editor.
    searchAssets(query: string, kind: LibraryKind): Promise<AssetsSearchResult | string>;
    dropAsset(asset: LibraryAsset, target: DropTarget): void;
    applySurface(asset: LibraryAsset, target: { room: string } | { theme: string }, part: SurfacePart): void;
    scriptFunctions(): Promise<string[]>;
    // S6: an overlay project's scene things (view.overlay), or the refusal's words.
    sceneOverlay(): Promise<ViewOverlayResult | string>;
    // S6 (the second run): the world view of the host's projects (world.view); the host's mods folder (mod.list); a
    // free map number for a new project of a world, of a mod when named (mod.map_number); projects packed into a mod
    // in the host's mods folder (mod.pack). Each a result, or the refusal's words.
    worldView(): Promise<WorldViewResult | string>;
    listMods(): Promise<ModListResult | string>;
    mapNumber(world: string, mod?: string): Promise<ModMapNumberResult | string>;
    packMod(input: ModPackInput): Promise<ModPackResult | string>;
}

// The Mods form's words (mod.pack into the host's mods folder): the projects by their keys.
export interface ModPackInput
{
    projects: string[];
    id: string;
    name?: string;
    version?: string;
    maps?: [number, number];
}

// The New project form's words (project.new, with the folder under one of the host's roots).
export interface NewProjectInput
{
    root: string;
    folder: string;
    id: string;
    name: string;
    world: string;
    stats_id?: number;
    // indoor (the default) or outdoor (S5b2).
    kind?: 'indoor' | 'outdoor';
}

export interface PlayOptions
{
    visible?: boolean;
    commands?: string[];
    seconds?: number;
}

export const quietActions: Actions = {
    openProject: () => undefined,
    closeProject: () => undefined,
    select: () => undefined,
    frameAt: () => undefined,
    revalidate: () => undefined,
    startPin: () => undefined,
    submitPin: async () => undefined,
    cancelPin: () => undefined,
    actOnPin: async () => null,
    selectPin: () => undefined,
    goToPin: () => undefined,
    picture: async () => null,
    loadHistory: () => undefined,
    toggleWalk: () => undefined,
    playHere: () => undefined,
    startJob: () => undefined,
    cancelJob: () => undefined,
    jobFile: async () => null,
    openLightbox: () => undefined,
    answerWithPicture: async () => null,
    enterCompare: () => undefined,
    goToPlace: () => undefined,
    setMode: () => undefined,
    setStage: () => undefined,
    setTool: () => undefined,
    edit: async () => null,
    undo: () => undefined,
    redo: () => undefined,
    revertEntry: () => undefined,
    protect: async () => null,
    migrate: async () => 'no host',
    newProject: async () => 'no host',
    resolve: async () => null,
    dismissNotice: () => undefined,
    notify: () => undefined,
    searchAssets: async () => 'no host',
    resolveCard: async () => null,
    showGhost: () => undefined,
    dropAsset: () => undefined,
    applySurface: () => undefined,
    scriptFunctions: async () => [],
    sceneOverlay: async () => 'no host',
    worldView: async () => 'no host',
    listMods: async () => 'no host',
    mapNumber: async () => 'no host',
    packMod: async () => 'no host',
};

// What others did to the pins between two readings, as notes: a pin from the game, an agent's claim or answer. The
// person's own steps say nothing (they see them happen).
export function pinChanges(before: readonly Pin[], after: readonly Pin[]): string[]
{
    const lines: string[] = [];
    const old = new Map(before.map((pin) => [pin.id, pin]));
    const verb: Record<string, string> = { claimed: 'claimed', resolved: 'resolved', declined: 'declined', open: 'reopened',
        accepted: 'accepted' };
    for (const pin of after)
    {
        const was = old.get(pin.id);
        if (!was)
        {
            if (pin.source === 'game')
            {
                lines.push(`A pin from the game arrived: ${pin.id} "${pin.text}"`);
            }
            else if (pin.author && pin.author !== 'user')
            {
                lines.push(`${pin.author} pinned ${pin.id}`);
            }
            continue;
        }
        const replies = pin.replies ?? [];
        const last = replies.at(-1);
        if (replies.length > (was.replies?.length ?? 0) && last && last.author !== 'user')
        {
            lines.push(`${last.author} ${last.status ? verb[last.status] ?? last.status : 'replied to'} ${pin.id}${last.text ? `: ${last.text}` : ''}`);
        }
        else if (pin.status === 'claimed' && was.status !== 'claimed' && pin.claimed_by && pin.claimed_by !== 'user')
        {
            lines.push(`${pin.claimed_by} claimed ${pin.id}`);
        }
    }
    return lines;
}

// A data URL's bytes as the request list takes a picture.
function pictureOf(dataUrl: string): { media_type: 'image/png' | 'image/jpeg'; base64: string } | undefined
{
    const match = /^data:(image\/(?:png|jpeg));base64,(.+)$/.exec(dataUrl);
    return match ? { media_type: match[1] as 'image/png' | 'image/jpeg', base64: match[2] } : undefined;
}

function message(error: unknown): { message: string; kind?: string }
{
    if (error instanceof RpcCallError)
    {
        return { message: error.message, kind: error.kind };
    }
    return { message: error instanceof Error ? error.message : String(error) };
}

export class Controller implements Actions
{
    readonly client: StudioClient;
    readonly store: Store;
    private serial = 0;
    private readonly meshBytes = new RevisionCache<{ meta: ViewMeshResult; bytes: ArrayBuffer }>(4);
    // The 3D view and the plan register themselves here when they mount.
    viewport: ViewportHandle | null = null;
    plan: PlanHandle | null = null;
    private pendingMesh: { meta: ViewMeshResult; bytes: ArrayBuffer } | null = null;
    private pendingCamera: Camera | null = null;
    private readonly pictures = new Map<string, Promise<string | null>>();
    private nextNote = 1;
    // A refresh after a notice: one at a time, the latest wins.
    private refreshSerial = 0;
    // Walk mode's session (walk/WalkMode.ts), while it is on.
    walk: WalkMode | null = null;

    // Author mode's gestures, written one transaction each (edit/session.ts).
    readonly session: EditSession;
    // A revision notice that came while gestures were in flight (it is usually this browser's own).
    private deferredNotice: HostNotices['revision_changed'] | null = null;
    private validateTimer: ReturnType<typeof setTimeout> | null = null;
    // project.resolve is missing from an older core: the inspector shows written values only.
    private resolveMissing = false;

    constructor(client: StudioClient, store: Store)
    {
        this.client = client;
        this.store = store;
        this.session = new EditSession(client, store, {
            committed: (key, reload) => this.afterEdits(key, reload),
            note: (text) => this.note(text, 'change'),
        });
        client.onState((state) =>
        {
            store.setState({ connection: state });
            if (state === 'open' && store.getState().projects.state !== 'ready')
            {
                this.listProjects();
            }
            if (state === 'open')
            {
                // The host's capabilities: whether it runs the Python checks (D10).
                this.client.call('session.hello', {}).then((hello) => store.setState({ python: hello.host?.python !== false }), () => undefined);
            }
            // Back after a lost connection: the host forgot this browser; tell it again and catch up.
            if (state === 'open' && this.subscribed && store.getState().projectKey)
            {
                void this.subscribe(store.getState().projectKey!, true);
            }
        });
        client.onNotice('revision_changed', (notice) => this.onRevisionChanged(notice));
        client.onNotice('pins_changed', (notice) => this.onPinsChanged(notice));
        client.onNotice('project_unreadable', (notice) =>
        {
            if (notice.project === this.store.getState().projectKey)
            {
                this.store.setState({ unreadable: notice.message });
            }
        });
        client.onNotice('client_joined', ({ client: joined }) =>
        {
            this.store.setState((s) => ({ clients: [...s.clients.filter((c) => c.id !== joined.id), joined] }));
            if (joined.kind === 'mcp')
            {
                this.note(`${joined.name} connected`, 'presence');
            }
        });
        client.onNotice('game_started', (notice) =>
        {
            if (notice.project === this.store.getState().projectKey)
            {
                this.store.setState({ play: { state: 'running', run: notice.run } });
            }
        });
        client.onNotice('game_exited', (notice) => this.onGameExited(notice));
        client.onNotice('job_progress', (notice) => this.onJob(notice.project, notice.job, false));
        client.onNotice('job_done', (notice) => this.onJob(notice.project, notice.job, true));
        client.onNotice('client_left', ({ client: left }) =>
        {
            this.store.setState((s) => ({ clients: s.clients.filter((c) => c.id !== left.id) }));
            if (left.kind === 'mcp')
            {
                this.note(`${left.name} left`, 'presence');
            }
        });
    }

    private subscribed = false;
    // The original's mesh for the Compare view, and the 3D view that draws it.
    private originalMesh: { meta: ViewMeshResult; bytes: ArrayBuffer } | null = null;
    originalViewport: ViewportHandle | null = null;
    private readonly files = new Map<string, Promise<string | null>>();

    private async subscribe(key: string, catchUp: boolean): Promise<void>
    {
        try
        {
            const answer = await this.client.call('host.subscribe', { project: key });
            this.subscribed = true;
            if (key !== this.store.getState().projectKey)
            {
                return;
            }
            this.store.setState({ clients: answer.clients, unreadable: answer.unreadable ?? null });
            const project = this.store.getState().project;
            if (catchUp && project.state === 'ready' && answer.revision && answer.revision !== project.value.revision)
            {
                void this.refreshProject(key);
            }
            const pins = this.store.getState().pins;
            if (catchUp && answer.counter !== null && (pins.state !== 'ready' || pins.value.counter !== answer.counter))
            {
                void this.reloadPins(key);
            }
        }
        catch
        {
            // An older host without notices: the browser works without them.
        }
    }

    private note(text: string, kind: ChangeNote['kind']): void
    {
        const id = this.nextNote++;
        const now = Date.now();
        this.store.setState((s) => ({ notes: [...s.notes.filter((n) => now - n.at < 8000), { id, text, kind, at: now }].slice(-5) }));
        setTimeout(() => this.store.setState((s) => ({ notes: s.notes.filter((n) => n.id !== id) })), 8000);
    }

    private onRevisionChanged(notice: HostNotices['revision_changed']): void
    {
        const state = this.store.getState();
        if (notice.project !== state.projectKey)
        {
            return;
        }
        probe().marks.revision_notice = Math.round(performance.now());
        if (this.session.busy)
        {
            // Most likely this browser's own gesture: looked at again when the queue runs dry.
            this.deferredNotice = notice;
            return;
        }
        this.store.setState({ unreadable: null });
        if (notice.author !== 'user')
        {
            this.note(changeNote(notice.author, notice.label, notice.changes), 'change');
        }
        if (state.project.state === 'ready' && state.project.value.revision === notice.revision)
        {
            return;
        }
        void this.refreshProject(notice.project);
    }

    private onPinsChanged(notice: HostNotices['pins_changed']): void
    {
        const state = this.store.getState();
        if (notice.project !== state.projectKey)
        {
            return;
        }
        probe().marks.pins_notice = Math.round(performance.now());
        if (state.pins.state === 'ready' && state.pins.value.counter === notice.counter)
        {
            return;
        }
        void this.reloadPins(notice.project);
    }

    private async reloadPins(key: string): Promise<void>
    {
        try
        {
            const pins = await this.client.call('pins.list', { project: key });
            if (key === this.store.getState().projectKey)
            {
                const before = this.store.getState().pins;
                if (before.state === 'ready')
                {
                    for (const line of pinChanges(before.value.pins, pins.pins))
                    {
                        this.note(line, 'pins');
                    }
                }
                this.store.setState({ pins: { state: 'ready', value: pins } });
                probe().marks.pins_shown = Math.round(performance.now());
            }
        }
        catch (error)
        {
            if (key === this.store.getState().projectKey)
            {
                this.store.setState({ pins: { state: 'error', ...message(error) } });
            }
        }
    }

    // The project again after a change (an agent's edit, a text editor): its files, plan, mesh, checks and history,
    // keeping the selection and the cameras.
    private async refreshProject(key: string): Promise<void>
    {
        const serial = ++this.refreshSerial;
        const current = () => serial === this.refreshSerial && key === this.store.getState().projectKey;
        try
        {
            const opened = await this.client.call('project.open', { project: key });
            if (!current())
            {
                return;
            }
            this.store.setState({ project: { state: 'ready', value: opened } });
            this.loadHistory();
            try
            {
                const layout = await this.client.call('view.layout', { project: key });
                if (!current())
                {
                    return;
                }
                this.store.setState({ layout: { state: 'ready', value: layout } });
                await this.loadMesh(key, current, false);
            }
            catch (error)
            {
                // A project with no view yet (empty, or errors before any view was made): the plan draws its files.
                if (current())
                {
                    this.store.setState({ layout: { state: 'error', ...message(error) } });
                }
            }
            void this.loadJobs(key);
            this.revalidateFor(key, current);
            probe().marks.refreshed = Math.round(performance.now());
            probe().viewsRevision = opened.revision;
        }
        catch (error)
        {
            if (current())
            {
                this.note(`Could not read the changed project: ${message(error).message}`, 'change');
            }
        }
    }

    start(): void
    {
        this.client.connect();
        const fromUrl = new URLSearchParams(location.search).get('project');
        if (fromUrl)
        {
            this.openProject(fromUrl);
        }
    }

    listProjects(): void
    {
        this.store.setState({ projects: { state: 'loading' } });
        this.client.call('host.projects', {}).then(
            (answer) => this.store.setState({ projects: { state: 'ready', value: Array.isArray(answer) ? answer : answer.projects },
                projectRoots: Array.isArray(answer) ? [] : answer.roots ?? [] }),
            (error) => this.store.setState({ projects: { state: 'error', ...message(error) } }));
    }

    openProject(key: string): void
    {
        this.leaveWalk();
        this.session.reset();
        const serial = ++this.serial;
        const current = () => serial === this.serial;
        const probeState = probe();
        probeState.marks = { navigation: 0 };
        mark('open_start');
        const url = new URL(location.href);
        url.searchParams.set('project', key);
        history.replaceState(null, '', url);
        this.store.setState({
            projectKey: key, project: { state: 'loading' }, layout: { state: 'idle' }, mesh: { state: 'idle' },
            validation: { state: 'idle' }, pins: { state: 'idle' }, selection: null, hover: null, band: null,
            textureNote: null, history: { state: 'idle' }, unreadable: null, pinDraft: null, selectedPin: null,
            jobs: { state: 'idle' }, jobResults: {}, original: { state: 'idle' }, compareHeat: false,
            edits: { pending: 0 }, hint: null, dismissedNotices: [],
        });
        this.originalMesh = null;
        const project = key;
        this.client.call('project.open', { project }).then(async (opened) =>
        {
            if (!current())
            {
                return;
            }
            mark('project_open');
            this.store.setState({ project: { state: 'ready', value: opened } });
            void this.subscribe(project, false);
            this.loadHistory();
            void this.loadJobs(project);
            this.client.call('pins.list', { project }).then(
                (pins) => current() && this.store.setState({ pins: { state: 'ready', value: pins } }),
                (error) => current() && this.store.setState({ pins: { state: 'error', ...message(error) } }));
            this.store.setState({ layout: { state: 'loading' } });
            try
            {
                const layout = await this.client.call('view.layout', { project });
                if (!current())
                {
                    return;
                }
                mark('layout');
                this.store.setState({ layout: { state: 'ready', value: layout } });
            }
            catch (error)
            {
                if (current())
                {
                    this.store.setState({ layout: { state: 'error', ...message(error) } });
                }
            }
            await this.loadMesh(project, current);
            if (current())
            {
                probe().viewsRevision = opened.revision;
            }
            // The full check after the views (it takes 0.2 to 1.7 s).
            this.revalidateFor(project, current);
        }, (error) =>
        {
            if (current())
            {
                this.store.setState({ project: { state: 'error', ...message(error) } });
            }
        });
    }

    closeProject(): void
    {
        ++this.serial;
        this.leaveWalk();
        const url = new URL(location.href);
        url.searchParams.delete('project');
        history.replaceState(null, '', url);
        this.store.setState({ projectKey: null, project: { state: 'idle' }, layout: { state: 'idle' }, mesh: { state: 'idle' },
            pinDraft: null, selectedPin: null, unreadable: null });
        if (this.subscribed)
        {
            void this.client.call('host.subscribe', { project: null }).catch(() => undefined);
        }
    }

    loadHistory(): void
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return;
        }
        if (this.store.getState().history.state !== 'ready')
        {
            this.store.setState({ history: { state: 'loading' } });
        }
        this.client.call('edit.history', { project: key, limit: 200 }).then(
            (history) => key === this.store.getState().projectKey && this.store.setState({ history: { state: 'ready', value: history } }),
            (error) => key === this.store.getState().projectKey && this.store.setState({ history: { state: 'error', ...message(error) } }));
    }

    // --- author mode (S5b1) ------------------------------------------------------------------------------------------

    setMode(mode: 'review' | 'author'): void
    {
        this.store.setState({ mode, tool: 'select', hint: null });
    }

    // An outdoor project has its own stages and tools (S5b2).
    private outdoor(): boolean
    {
        const project = this.store.getState().project;
        return project.state === 'ready' && isOutdoorFiles(project.value.files);
    }

    setStage(stage: number): void
    {
        const info = stagesOf(this.outdoor()).find((entry) => entry.number === stage);
        if (!info)
        {
            return;
        }
        const state = this.store.getState();
        this.store.setState({ stage, viewMode: state.viewMode === 'compare' || state.viewMode === 'flow' ? state.viewMode : info.view,
            maximised: null, tool: info.tools.includes(state.tool) ? state.tool : 'select' });
    }

    setTool(tool: ToolName): void
    {
        const state = this.store.getState();
        if (state.mode !== 'author')
        {
            return;
        }
        const stages = stagesOf(this.outdoor());
        const stage = stages.find((entry) => entry.number === state.stage);
        // A tool of another stage brings its stage (stages filter, never lock: 3.3).
        const other = stage?.tools.includes(tool) ? null : stages.find((entry) => entry.tools.includes(tool));
        this.store.setState({ tool, hint: null, ...(other ? { stage: other.number } : {}) });
        if (this.store.getState().viewMode === '3d')
        {
            this.store.setState({ viewMode: 'split' });
        }
    }

    edit(gesture: Gesture): Promise<EditApplyResult | null>
    {
        return this.session.apply(gesture);
    }

    undo(): void
    {
        void this.session.revert('undo');
    }

    redo(): void
    {
        void this.session.revert('redo');
    }

    revertEntry(sequence: number, force = false): void
    {
        void this.session.revert('revert', sequence, force);
    }

    notify(text: string): void
    {
        this.note(text, 'change');
    }

    // --- the Library (S5b1 part 2) -----------------------------------------------------------------------------

    async searchAssets(query: string, kind: LibraryKind): Promise<AssetsSearchResult | string>
    {
        const state = this.store.getState();
        const card = state.project.state === 'ready' ? (state.project.value.files['project.yml']?.tree as Record<string, unknown> | undefined) : undefined;
        try
        {
            return await this.client.call('assets.search', { query, kind, limit: 80, ...(typeof card?.world === 'string' ? { world: card.world } : {}) });
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    async sceneOverlay(): Promise<ViewOverlayResult | string>
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return 'no project';
        }
        try
        {
            return await this.client.call('view.overlay', { project: key });
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    // The keys of the host's projects (the project list, read on connecting).
    private projectKeys(): string[]
    {
        const projects = this.store.getState().projects;
        return projects.state === 'ready' ? projects.value.map((project) => project.key) : [];
    }

    async worldView(): Promise<WorldViewResult | string>
    {
        try
        {
            return await this.client.call('world.view', { projects: this.projectKeys() });
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    async listMods(): Promise<ModListResult | string>
    {
        try
        {
            return await this.client.call('mod.list', { mods: 'default' });
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    async mapNumber(world: string, mod?: string): Promise<ModMapNumberResult | string>
    {
        try
        {
            return await this.client.call('mod.map_number', { world, mods: 'default', projects: this.projectKeys(), ...(mod ? { mod } : {}) });
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    async packMod(input: ModPackInput): Promise<ModPackResult | string>
    {
        try
        {
            return await this.client.call('mod.pack', { projects: input.projects, id: input.id, out: 'default',
                ...(input.name ? { name: input.name } : {}), ...(input.version ? { version: input.version } : {}),
                ...(input.maps ? { maps: input.maps } : {}) });
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    private scriptNames: Promise<string[]> | null = null;

    scriptFunctions(): Promise<string[]>
    {
        const state = this.store.getState();
        const card = state.project.state === 'ready' ? (state.project.value.files['project.yml']?.tree as Record<string, unknown> | undefined) : undefined;
        this.scriptNames ??= this.client.call('assets.script_reference', typeof card?.world === 'string' ? { world: card.world } : {})
            .then((answer) => answer.functions, () => []);
        return this.scriptNames;
    }

    // A drop's operations: one transaction, or a new theme and the room naming it (one history entry).
    private runPlan(plan: DropPlan): void
    {
        if (plan.kind === 'note')
        {
            this.note(plan.text, 'change');
            return;
        }
        if (plan.kind === 'ops')
        {
            void this.edit({ label: plan.label, ops: plan.ops }).then((result) =>
            {
                const id = plan.select ? allocatedId(result?.ids_allocated) : null;
                if (id)
                {
                    this.select({ id, file: 'objects.yml' });
                }
            });
            return;
        }
        const mergeKey = `theme ${plan.label} ${Date.now()}`;
        void this.edit({ label: plan.label, mergeKey, ops: [plan.add] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                void this.edit({ label: plan.label, mergeKey, ops: [plan.assign(id)] });
            }
        });
    }

    dropAsset(asset: LibraryAsset, target: DropTarget): void
    {
        const state = this.store.getState();
        if (state.project.state !== 'ready')
        {
            return;
        }
        if (state.mode !== 'author')
        {
            this.note('Switch to Author mode to place or texture by dragging from the Library', 'change');
            return;
        }
        if (isOutdoorFiles(state.project.value.files))
        {
            // Outdoors (S5b2): a decoration, a monster or a texture where it is dropped.
            const at: [number, number] = target.where === 'plan' ? target.at : [target.point[0], target.point[1]];
            const plan = outdoorDrop(state.project.value.files, asset.kind, asset.name, at, state.selection?.id ?? null);
            if ('note' in plan)
            {
                this.note(plan.note, 'change');
                return;
            }
            if (plan.options)
            {
                this.store.setState((s) => ({ toolOptions: { ...s.toolOptions, outdoor: { ...s.toolOptions.outdoor, ...plan.options } } }));
            }
            void this.edit({ label: plan.label, ops: plan.ops }).then((result) =>
            {
                const made = result?.ids_allocated?.find((entry) => entry.startsWith('sketch.yml#'));
                if (made)
                {
                    this.select({ id: made.slice(made.indexOf('#') + 1), file: 'sketch.yml' });
                }
            });
            return;
        }
        this.runPlan(dropPlan(state.project.value.files, state.layout.state === 'ready' ? state.layout.value : null, asset, target, state.toolOptions.wallHeight));
    }

    applySurface(asset: LibraryAsset, target: { room: string } | { theme: string }, part: SurfacePart): void
    {
        const state = this.store.getState();
        if (state.project.state !== 'ready')
        {
            return;
        }
        const surface = surfaceOf(asset);
        if ('theme' in target)
        {
            this.runPlan({ kind: 'ops', label: `${asset.name} on the ${part === 'wall' ? 'walls' : part} of ${target.theme}`, ops: [themeSurfaceOp(target.theme, part, surface)], select: false });
            return;
        }
        const plan = roomSurfacePlan(state.project.value.files, target.room, part, surface);
        const label = `${asset.name} on the ${part === 'wall' ? 'walls' : part} of ${target.room}`;
        this.runPlan(!plan ? { kind: 'note', text: `${target.room} is not a room` } : plan.kind === 'set' ? { kind: 'ops', label, ops: [plan.op], select: false }
            : { kind: 'theme', label, add: plan.add, assign: plan.assign });
    }

    dismissNotice(sequence: number): void
    {
        this.store.setState((s) => ({ dismissedNotices: [...s.dismissedNotices, sequence] }));
    }

    // "Protect this project" (or clear it) in the project's settings: the hand-edit mark, a person's only (2.8).
    async protect(clear: boolean): Promise<string | null>
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return 'no project open';
        }
        try
        {
            const answer = await this.client.call('project.protect', { project: key, ...(clear ? { clear: true } : {}) });
            this.store.setState((s) => (s.project.state === 'ready' ? { project: { state: 'ready', value: { ...s.project.value,
                revision: answer.revision, hand_edited: answer.hand_edited } } } : {}));
            if (answer.sequence)
            {
                await this.refreshProject(key);
            }
            return null;
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    // Writes every file's keys and canonical form (asked first: dry_run gives what would change).
    async migrate(dryRun: boolean): Promise<ProjectMigrateResult | string>
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return 'no project open';
        }
        try
        {
            const answer = await this.client.call('project.migrate', { project: key, ...(dryRun ? { dry_run: true } : {}) });
            if (!dryRun)
            {
                await this.refreshProject(key);
            }
            return answer;
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    // A new project from the project list: made by the core in a new folder under one of the host's roots, then
    // opened in Author mode. Null, or the refusal's words.
    async newProject(input: NewProjectInput): Promise<string | null>
    {
        const key = `${input.root}/${input.folder}`;
        try
        {
            const params: ProjectNewParams = { project: key, id: input.id, name: input.name, world: input.world,
                ...(input.stats_id ? { stats_id: input.stats_id } : {}), ...(input.kind === 'outdoor' ? { kind: 'outdoor' as const } : {}) };
            await this.client.call('project.new', params);
            this.listProjects();
            this.openProject(key);
            // Outdoors the land first: the grid editor's spot heights (S5b2).
            this.store.setState({ mode: 'author', stage: 2, tool: input.kind === 'outdoor' ? 'spots' : 'room' });
            return null;
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    async resolveCard(): Promise<ProjectResolveResult | null>
    {
        const key = this.store.getState().projectKey;
        if (!key || this.resolveMissing)
        {
            return null;
        }
        try
        {
            return await this.client.call('project.resolve', { project: key, card: true });
        }
        catch
        {
            return null;
        }
    }

    showGhost(sequence: number | null): void
    {
        const key = this.store.getState().projectKey;
        if (!key || sequence === null)
        {
            this.store.setState({ ghost: null });
            return;
        }
        this.store.setState({ ghost: { sequence, layout: null } });
        this.client.call('view.layout_at', { project: key, sequence, side: 'before' }).then((layout) =>
        {
            if (this.store.getState().ghost?.sequence === sequence)
            {
                this.store.setState({ ghost: { sequence, layout } });
            }
        }, (error: unknown) =>
        {
            this.store.setState({ ghost: null });
            this.note(`The state before #${sequence} cannot be drawn: ${message(error).message}`, 'change');
        });
    }

    async resolve(id: string, file?: string): Promise<ProjectResolveResult | null>
    {
        const key = this.store.getState().projectKey;
        if (!key || this.resolveMissing)
        {
            return null;
        }
        try
        {
            return await this.client.call('project.resolve', { project: key, id, ...(file ? { file: file as ProjectResolveResult['file'] } : {}) });
        }
        catch (error)
        {
            if (error instanceof RpcCallError && error.kind === 'unknown_method')
            {
                this.resolveMissing = true;
            }
            return null;
        }
    }

    // The queue ran dry: the views of the new revision, the history, and the full check a moment later.
    private afterEdits(key: string, reload: boolean): void
    {
        if (key !== this.store.getState().projectKey)
        {
            return;
        }
        const notice = this.deferredNotice;
        this.deferredNotice = null;
        const project = this.store.getState().project;
        if (reload || (notice && project.state === 'ready' && notice.revision !== project.value.revision))
        {
            void this.refreshProject(key);
            return;
        }
        void this.refreshViews(key);
    }

    private async refreshViews(key: string): Promise<void>
    {
        const serial = ++this.refreshSerial;
        const current = () => serial === this.refreshSerial && key === this.store.getState().projectKey && !this.session.busy;
        try
        {
            const layout = await this.client.call('view.layout', { project: key });
            if (current())
            {
                this.store.setState({ layout: { state: 'ready', value: layout } });
                mark('edit_layout');
                await this.loadMesh(key, current, false);
            }
        }
        catch (error)
        {
            // An empty or broken project has no view yet: the plan draws the files.
            if (current())
            {
                this.store.setState({ layout: { state: 'error', ...message(error) } });
            }
        }
        // The history after the views: one core answers in order (the hosted page's worker), so the 3D view after a
        // gesture does not wait for it (S8f).
        this.loadHistory();
        if (current())
        {
            // The revision whose views are shown (scripted runs wait for it).
            const project = this.store.getState().project;
            probe().viewsRevision = project.state === 'ready' ? project.value.revision : undefined;
        }
        if (this.validateTimer)
        {
            clearTimeout(this.validateTimer);
        }
        this.validateTimer = setTimeout(() =>
        {
            this.validateTimer = null;
            if (current())
            {
                this.revalidateFor(key, current);
            }
        }, 700);
    }

    // --- walk mode and Play here (S5a4) -----------------------------------------------------------------------------

    // G: walk mode on (the project built, its walk loaded in the worker, the party at the camera's eye) or off.
    toggleWalk(): void
    {
        if (this.walk || this.store.getState().walk.state === 'starting')
        {
            this.leaveWalk();
            return;
        }
        void this.enterWalk();
    }

    private async enterWalk(): Promise<void>
    {
        const state = this.store.getState();
        const key = state.projectKey;
        if (!key || state.project.state !== 'ready')
        {
            return;
        }
        if (state.viewMode === 'plan' || state.maximised === 'plan')
        {
            this.store.setState({ viewMode: 'split', maximised: null });
        }
        const viewport = this.viewport;
        if (!viewport?.canvasElement || !viewport.setWalkCamera || !viewport.setWalking || !viewport.setHiddenObjects)
        {
            this.store.setState({ walk: { state: 'error', message: 'the 3D view is not open' } });
            return;
        }
        this.store.setState({ walk: { state: 'starting', message: 'building the map for walk mode…' } });
        const started = performance.now();
        try
        {
            const prepared = await this.client.call('host.walk_prepare', { project: key });
            mark('walk_prepared');
            probe().marks.walk_prepare_ms = Math.round(performance.now() - started);
            if (key !== this.store.getState().projectKey || this.store.getState().walk.state !== 'starting')
            {
                return;
            }
            this.store.setState({ walk: { state: 'starting', kind: prepared.kind, message: 'loading the walk…' } });
            const walk = new WalkMode(viewport as WalkView, {
                onPose: (pose) => this.store.setState((s) => ({ walk: { ...s.walk, pose } })),
                onLocked: (locked) => this.store.setState((s) => ({ walk: { ...s.walk, locked } })),
                onDoor: (id, open) => this.note(`${id} ${open ? 'opened' : 'shut'} (walk mode only: the game's doors move by their events)`, 'change'),
                onNote: (text) => this.note(text, 'change'),
                onLeave: () => this.leaveWalk(),
            }, this.client.walkChannel());
            this.walk = walk;
            // The routes as the walk's worker fetches them (a paired hosted page: the host's address).
            const files = { map: this.client.routeUrl(prepared.files.map), state: this.client.routeUrl(prepared.files.state),
                decorations: this.client.routeUrl(prepared.files.decorations),
                ...(prepared.files.terrain ? { terrain: this.client.routeUrl(prepared.files.terrain) } : {}) };
            await walk.start(this.client.mode === 'hosted' ? prepared.files : files, this.client.token, this.client.coreUrl());
            probe().marks.walk_ready_ms = Math.round(performance.now() - started);
            probe().walk = walk;
            this.store.setState((s) => ({ walk: { ...s.walk, state: 'on', kind: prepared.kind, message: undefined } }));
        }
        catch (error)
        {
            this.walk?.stop();
            this.walk = null;
            this.store.setState({ walk: { state: 'error', message: message(error).message } });
            this.note(`Walk mode: ${message(error).message}`, 'change');
        }
    }

    private leaveWalk(): void
    {
        this.walk?.stop();
        this.walk = null;
        this.store.setState({ walk: { state: 'off' } });
    }

    // F5: the game at this camera (or where the party stands in walk mode), its window shown.
    playHere(options: PlayOptions = {}): void
    {
        const state = this.store.getState();
        const key = state.projectKey;
        if (!key || state.project.state !== 'ready' || state.play.state === 'starting')
        {
            return;
        }
        let pose;
        const walkPose = this.walk?.pose;
        if (walkPose && this.viewport)
        {
            const camera = this.viewport.camera();
            pose = poseOfCamera({ eye: [walkPose.position[0], walkPose.position[1], walkPose.eye_z], yaw: camera.yaw, pitch: camera.pitch },
                walkPose.eye_z - walkPose.position[2]);
        }
        else if (this.viewport)
        {
            pose = poseOfCamera(this.viewport.camera(), this.eyeHeight());
        }
        else
        {
            return;
        }
        pose.pitch_degrees = Math.max(-89, Math.min(89, pose.pitch_degrees));
        this.store.setState({ play: { state: 'starting', message: 'building, installing and starting the game…' } });
        const started = performance.now();
        this.client.call('game.play_here', { project: key, pose, visible: options.visible ?? true,
            ...(options.commands?.length ? { commands: options.commands } : {}),
            ...(options.seconds ? { seconds: options.seconds } : {}) }).then((answer) =>
        {
            probe().marks.play_started_ms = Math.round(performance.now() - started);
            this.store.setState({ play: { state: 'running', run: answer.run } });
            this.note(`The game is starting on ${answer.map} at the camera (${answer.run}); close it to come back here`, 'change');
        }, (error) =>
        {
            this.store.setState({ play: { state: 'error', message: message(error).message } });
            this.note(`Play here: ${message(error).message}`, 'change');
        });
    }

    private onGameExited(notice: HostNotices['game_exited']): void
    {
        const state = this.store.getState();
        if (notice.project !== state.projectKey)
        {
            return;
        }
        this.store.setState({ play: { state: 'idle' } });
        probe().marks.game_exited = Math.round(performance.now());
        if (!notice.exit)
        {
            this.note('The game closed without saying where the party stood (it left before the map loaded)', 'change');
            return;
        }
        if (notice.exit.map.toLowerCase() !== notice.map.toLowerCase())
        {
            this.note(`The game closed on another map (${notice.exit.map}): the camera stays`, 'change');
            return;
        }
        const camera = cameraOfExitPose(notice.exit.pose, this.eyeHeight());
        probe().exitPose = notice.exit;
        if (this.walk)
        {
            void this.walk.placeAt(camera);
        }
        else if (this.viewport)
        {
            this.viewport.setCamera(camera);
        }
        else
        {
            this.pendingCamera = camera;
        }
        this.plan?.frameObject(null, notice.exit.pose.position);
        this.note(`The game closed: the camera is where the party stood (${notice.exit.pose.position.map((v) => Math.round(v)).join(', ')})`, 'change');
    }

    // --- jobs, the scorecard and compare (S5a5) ------------------------------------------------------------------

    // The project's jobs, and the results of the newest finished job of each kind (the scorecard, the pictures).
    private async loadJobs(key: string): Promise<void>
    {
        if (this.store.getState().jobs.state !== 'ready')
        {
            this.store.setState({ jobs: { state: 'loading' } });
        }
        try
        {
            const answer = await this.client.call('jobs.list', { project: key });
            if (key !== this.store.getState().projectKey)
            {
                return;
            }
            this.store.setState({ jobs: { state: 'ready', value: answer.jobs } });
            const kinds: JobKind[] = ['checks', 'compare', 'scale_bands', 'town_feel', 'playtest', 'pins_tour', 'building_shots'];
            await Promise.all(kinds.map((kind) =>
            {
                const { done } = latestJobs(answer.jobs, kind, null);
                return done && done.has_result ? this.loadResult(key, done) : Promise.resolve();
            }));
            mark('jobs');
        }
        catch (error)
        {
            if (key === this.store.getState().projectKey)
            {
                this.store.setState({ jobs: { state: 'error', ...message(error) } });
            }
        }
    }

    private async loadResult(key: string, job: Job): Promise<void>
    {
        if (this.store.getState().jobResults[job.id] !== undefined)
        {
            return;
        }
        const answer = await this.client.call('jobs.status', { project: key, job: job.id });
        if (key === this.store.getState().projectKey && answer.job.result !== undefined)
        {
            this.store.setState((s) => ({ jobResults: { ...s.jobResults, [job.id]: answer.job.result } }));
            if (job.kind === 'compare' && this.originalMesh)
            {
                // The original moves by the new compare's vertical offset.
                this.originalMesh = null;
                if (this.store.getState().viewMode === 'compare')
                {
                    void this.loadOriginal(key);
                }
            }
        }
    }

    private onJob(project: string, job: Job, finished: boolean): void
    {
        const state = this.store.getState();
        if (project !== state.projectKey)
        {
            return;
        }
        probe().marks[`job_${job.kind}_${job.state}`] = Math.round(performance.now());
        this.store.setState((s) =>
        {
            const list = s.jobs.state === 'ready' ? s.jobs.value : [];
            const others = list.filter((entry) => entry.id !== job.id);
            return { jobs: { state: 'ready', value: [job, ...others].sort((a, b) => (a.created < b.created ? 1 : a.created > b.created ? -1 : 0)) } };
        });
        if (!finished)
        {
            return;
        }
        if (job.has_result)
        {
            void this.loadResult(project, job).catch(() => undefined);
        }
        if (!job.background || job.state === 'failed')
        {
            this.note(`${job.title}: ${job.state === 'done' ? job.line : job.state === 'failed' ? `failed: ${job.error ?? ''}` : job.state}`, 'change');
        }
    }

    startJob(kind: JobKind, params: JobParams = {}): void
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return;
        }
        this.client.call('jobs.start', { project: key, kind, params }).then((answer) =>
        {
            this.onJob(key, answer.job, false);
            this.store.setState({ drawerTab: kind === 'pins_tour' ? this.store.getState().drawerTab : 'jobs' });
        }, (error) => this.note(`${kind}: ${message(error).message}`, 'change'));
    }

    cancelJob(id: string): void
    {
        const key = this.store.getState().projectKey;
        if (key)
        {
            this.client.call('jobs.cancel', { project: key, job: id }).catch((error) => this.note(`cancel: ${message(error).message}`, 'change'));
        }
    }

    jobFile(job: Job, relative: string): Promise<string | null>
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return Promise.resolve(null);
        }
        const route = jobRoute(key, job, relative);
        let found = this.files.get(route);
        if (!found)
        {
            found = this.client.fetchBytes(route).then(
                ({ bytes }) => URL.createObjectURL(new Blob([bytes], { type: relative.endsWith('.png') ? 'image/png' : relative.endsWith('.jpg') ? 'image/jpeg' : 'text/plain' })),
                () => null);
            this.files.set(route, found);
        }
        return found;
    }

    openLightbox(url: string, caption: string): void
    {
        this.store.setState({ lightbox: { url, caption } });
    }

    async answerWithPicture(pin: Pin, job: Job, relative: string, action: 'reply' | 'resolve', text: string): Promise<string | null>
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return 'no project open';
        }
        try
        {
            const { bytes } = await this.client.fetchBytes(jobRoute(key, job, relative));
            const base64 = btoa(Array.from(new Uint8Array(bytes), (byte) => String.fromCharCode(byte)).join(''));
            const words = text.trim() || `The game's picture at the pin's pose (revision ${job.revision.slice(0, 8)}).`;
            await this.client.call(`pins.${action}`, { project: key, pin: pin.id, by: 'user', text: words,
                pictures: [{ media_type: relative.endsWith('.jpg') ? 'image/jpeg' : 'image/png', base64 }] });
            await this.reloadPins(key);
            return null;
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    // The newest compare's result, when one is read.
    private compareResult(): CompareJobResult | null
    {
        const state = this.store.getState();
        const jobs = state.jobs.state === 'ready' ? state.jobs.value : [];
        const { done } = latestJobs(jobs, 'compare', null);
        return done ? (state.jobResults[done.id] as CompareJobResult | undefined) ?? null : null;
    }

    enterCompare(): void
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return;
        }
        this.leaveWalk();
        this.store.setState({ viewMode: 'compare', maximised: null, compareHeat: true });
        if (!this.originalMesh)
        {
            void this.loadOriginal(key);
        }
    }

    private async loadOriginal(key: string): Promise<void>
    {
        this.store.setState({ original: { state: 'loading' } });
        try
        {
            const compare = this.compareResult();
            const meta: ViewOriginalMeshResult = await this.client.call('view.original_mesh', { project: key,
                ...(compare ? { original: compare.original } : {}) });
            const name = meta.file.split('/').pop()!;
            const { bytes } = await this.client.fetchBytes(`/mesh/${encodeURIComponent(key)}/${encodeURIComponent(name)}`);
            if (key !== this.store.getState().projectKey)
            {
                return;
            }
            // The original drawn where the rebuild lies (a rebuild may lie lower or higher as a whole).
            this.originalMesh = shiftedMesh(meta, bytes, compare?.vertical_offset ?? 0);
            this.store.setState({ original: { state: 'ready', value: meta } });
            mark('original_mesh');
            this.showOriginal();
        }
        catch (error)
        {
            if (key === this.store.getState().projectKey)
            {
                this.store.setState({ original: { state: 'error', ...message(error) } });
            }
        }
    }

    private showOriginal(): void
    {
        const viewport = this.originalViewport;
        if (!viewport || !this.originalMesh)
        {
            return;
        }
        viewport.loadMesh(this.originalMesh.meta, this.originalMesh.bytes, false);
        if (this.viewport)
        {
            viewport.setCamera(this.viewport.camera());
        }
        viewport.renderNow();
        void loadTextures(this.client, viewport, this.originalMesh.meta.world, viewport.textureNames(), () => viewport.renderNow(),
            () => this.originalViewport === viewport).then(() =>
        {
            viewport.renderNow();
            mark('original_textured');
        });
    }

    attachOriginalViewport(viewport: ViewportHandle | null): void
    {
        this.originalViewport = viewport;
        if (viewport && this.originalMesh)
        {
            this.showOriginal();
        }
    }

    // A place (a compare's worst point or block, a finding's): the 3D views at the party's eye there, the plan on it.
    goToPlace(at: readonly number[], yaw?: number): void
    {
        const layout = this.store.getState().layout;
        const outdoor = layout.state === 'ready' && layout.value.kind === 'outdoor';
        const current = this.viewport?.camera();
        const camera: Camera = outdoor
            // Outdoors a block of 16 x 16 cells (8192 across), seen steeply from above its south edge, over any rim.
            ? { eye: [at[0], at[1] - 2600, at[2] + 5600], yaw: Math.PI / 2, pitch: -1.1 }
            : { eye: [at[0], at[1], at[2] + this.eyeHeight()], yaw: yaw ?? current?.yaw ?? 0, pitch: -0.12 };
        if (this.viewport)
        {
            this.viewport.setCamera(camera);
        }
        else
        {
            this.pendingCamera = camera;
        }
        this.plan?.frameObject(null, [at[0], at[1], at[2]]);
    }

    // --- pins -------------------------------------------------------------------------------------------------------

    // The party's eye over its feet: the walk's own (the game's party for the world), else the MM6-MM8 heights.
    private eyeHeight(): number
    {
        const party = this.walk?.load?.party;
        if (party)
        {
            return party.eye_height;
        }
        const layout = this.store.getState().layout;
        return layout.state === 'ready' && layout.value.kind === 'outdoor' ? EYE_HEIGHT.outdoor : EYE_HEIGHT.indoor;
    }

    // A new pin on what is under the pointer in the view it was asked in: the object (its top-level id and file, from
    // the provenance table), the point, the 3D camera as a pose, and the view's picture.
    startPin(where: 'plan' | '3d'): void
    {
        const state = this.store.getState();
        if (!state.projectKey || state.project.state !== 'ready')
        {
            return;
        }
        let draft: PinDraft = { where, sending: false };
        if (where === '3d' && this.viewport)
        {
            const pick = this.viewport.lastHover ?? this.viewport.pickCentre();
            if (pick?.base)
            {
                draft.on = pick.base;
                draft.file = pick.file;
            }
            if (pick)
            {
                draft.at = pick.point;
            }
            draft.pose = poseOfCamera(this.viewport.camera(), this.eyeHeight());
            draft.picture = this.viewport.capture();
        }
        else if (where === 'plan' && this.plan)
        {
            const target = this.plan.pointerTarget();
            if (target?.owner)
            {
                draft.on = baseId(target.owner);
                draft.file = draft.on.startsWith('room:') ? 'rooms.yml' : undefined;
            }
            if (target)
            {
                draft.at = target.at;
            }
            draft.picture = this.plan.capture();
        }
        else
        {
            return;
        }
        if (!draft.on && !draft.at)
        {
            draft = { ...draft, error: 'Nothing under the pointer: point at the map, then press P.' };
        }
        this.store.setState({ pinDraft: draft, drawerTab: 'pins' });
    }

    cancelPin(): void
    {
        this.store.setState({ pinDraft: null });
    }

    async submitPin(text: string): Promise<void>
    {
        const state = this.store.getState();
        const draft = state.pinDraft;
        const key = state.projectKey;
        if (!draft || !key || !text.trim())
        {
            return;
        }
        this.store.setState({ pinDraft: { ...draft, sending: true, error: undefined } });
        const card = state.project.state === 'ready' ? (state.project.value.files['project.yml']?.tree as Record<string, unknown> | undefined) : undefined;
        const params: PinsAddParams = { project: key, text: text.trim(), author: 'user', source: 'studio' };
        if (draft.at)
        {
            params.at = draft.at;
        }
        if (draft.pose)
        {
            params.pose = draft.pose;
        }
        if (typeof card?.world === 'string')
        {
            params.world = card.world;
        }
        if (typeof card?.id === 'string')
        {
            params.map = `${card.id}.${card.kind === 'outdoor' ? 'odm' : 'blv'}`;
        }
        const picture = draft.picture ? pictureOf(draft.picture) : undefined;
        if (picture)
        {
            params.picture = picture;
        }
        const started = performance.now();
        try
        {
            let answer;
            try
            {
                answer = await this.client.call('pins.add', draft.on
                    ? { ...params, on: draft.on, ...(draft.file ? { file: draft.file as PinsAddParams['file'] } : {}) } : params);
            }
            catch (error)
            {
                // An object the pins cannot name (a part with no id of its own): the point instead.
                if (!(error instanceof RpcCallError) || error.kind !== 'bad_request' || !draft.on || !draft.at)
                {
                    throw error;
                }
                answer = await this.client.call('pins.add', params);
                this.note(`Pinned as a point: ${error.message}`, 'pins');
            }
            probe().marks.pin_add_ms = Math.round(performance.now() - started);
            this.store.setState({ pinDraft: null, selectedPin: answer.pin.id });
            await this.reloadPins(key);
        }
        catch (error)
        {
            this.store.setState({ pinDraft: { ...draft, sending: false, error: message(error).message } });
        }
    }

    // An answer to a pin through the request list, as the user; null, or the refusal's words.
    async actOnPin(pin: Pin, action: PinAction | 'keep', text: string): Promise<string | null>
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return 'no project open';
        }
        const words = text.trim();
        try
        {
            switch (action)
            {
            case 'claim':
                await this.client.call('pins.claim', { project: key, pin: pin.id, by: 'user' });
                break;
            case 'keep':
                await this.client.call('pins.keep', { project: key, pin: pin.id });
                break;
            case 'reply':
            case 'resolve':
            case 'decline':
                await this.client.call(`pins.${action}`, { project: key, pin: pin.id, by: 'user', text: words });
                break;
            case 'accept':
            case 'reopen':
                await this.client.call(`pins.${action}`, { project: key, pin: pin.id, by: 'user', ...(words ? { text: words } : {}) });
                break;
            }
            await this.reloadPins(key);
            return null;
        }
        catch (error)
        {
            return message(error).message;
        }
    }

    selectPin(id: string | null): void
    {
        this.store.setState({ selectedPin: id });
    }

    // "Go to": the camera where the pin was made from (its pose), else its object or its point.
    goToPin(pin: Pin): void
    {
        this.store.setState({ selectedPin: pin.id });
        const place = pinPlace(pin);
        if (pin.pose)
        {
            const camera = cameraOfPose(pin.pose, this.eyeHeight());
            if (this.store.getState().viewMode === 'plan')
            {
                this.store.setState({ viewMode: 'split', maximised: null });
            }
            if (this.viewport)
            {
                this.viewport.setCamera(camera);
            }
            else
            {
                this.pendingCamera = camera;
            }
            if (place)
            {
                this.plan?.frameObject(null, place);
            }
            if (pin.on)
            {
                select(this.store, { id: pin.on, file: pin.file }, false);
            }
            return;
        }
        if (pin.on)
        {
            this.select({ id: pin.on, file: pin.file }, true);
        }
        else if (place)
        {
            this.frameAt(place);
        }
    }

    picture(relative: string): Promise<string | null>
    {
        const key = this.store.getState().projectKey;
        if (!key)
        {
            return Promise.resolve(null);
        }
        const cacheKey = `${key}|${relative}`;
        let found = this.pictures.get(cacheKey);
        if (!found)
        {
            found = this.client.fetchBytes(pictureRoute(key, relative)).then(
                ({ bytes }) => URL.createObjectURL(new Blob([bytes], { type: relative.endsWith('.png') ? 'image/png' : 'image/jpeg' })),
                () => null);
            this.pictures.set(cacheKey, found);
        }
        return found;
    }

    attachPlan(plan: PlanHandle | null): void
    {
        this.plan = plan;
    }

    revalidate(): void
    {
        const key = this.store.getState().projectKey;
        if (key)
        {
            const serial = this.serial;
            this.revalidateFor(key, () => serial === this.serial);
        }
    }

    select(ref: ObjectRef | null, frame = false): void
    {
        select(this.store, ref, frame);
    }

    frameAt(at: [number, number, number]): void
    {
        frameAt(this.store, at);
    }

    // The 3D view mounted (or mounted again after a split change): give it the mesh it missed.
    attachViewport(viewport: Controller['viewport']): void
    {
        if (viewport !== this.viewport && this.walk)
        {
            // The view the walk drew into went (a split change): walk mode ends with it.
            this.leaveWalk();
        }
        this.viewport = viewport;
        if (viewport && this.pendingCamera)
        {
            viewport.setCamera(this.pendingCamera);
            this.pendingCamera = null;
        }
        if (viewport && this.pendingMesh)
        {
            viewport.loadMesh(this.pendingMesh.meta, this.pendingMesh.bytes, true);
            const world = this.pendingMesh.meta.world;
            void this.texture(world, () => true);
        }
    }

    private revalidateFor(project: string, current: () => boolean): void
    {
        this.store.setState({ validation: { state: 'loading' } });
        const start = performance.now();
        this.client.call('check.validate', { project }).then(
            (result) =>
            {
                if (current())
                {
                    probe().marks.validate_ms = Math.round(performance.now() - start);
                    this.store.setState({ validation: { state: 'ready', value: result } });
                }
            },
            (error) => current() && this.store.setState({ validation: { state: 'error', ...message(error) } }));
    }

    private async loadMesh(project: string, current: () => boolean, frame = true): Promise<void>
    {
        if (frame || this.store.getState().mesh.state !== 'ready')
        {
            this.store.setState({ mesh: { state: 'loading' } });
        }
        try
        {
            const meta = await this.client.call('view.mesh', { project });
            if (!current())
            {
                return;
            }
            mark('mesh_meta');
            const cacheKey = `${project}@${meta.view_revision}-${meta.lock_hash}`;
            let entry = this.meshBytes.get(cacheKey);
            if (!entry)
            {
                const name = meta.file.split('/').pop()!;
                const { bytes } = await this.client.fetchBytes(`/mesh/${encodeURIComponent(project)}/${encodeURIComponent(name)}`);
                entry = { meta, bytes };
                this.meshBytes.set(cacheKey, entry);
            }
            if (!current())
            {
                return;
            }
            mark('mesh_bytes');
            this.store.setState({ mesh: { state: 'ready', value: meta } });
            this.pendingMesh = entry;
            if (this.viewport)
            {
                this.viewport.loadMesh(entry.meta, entry.bytes, frame);
                this.viewport.renderNow();
                mark('grey');
                await this.texture(meta.world, current);
            }
        }
        catch (error)
        {
            if (current())
            {
                this.store.setState({ mesh: { state: 'error', ...message(error) } });
            }
        }
    }

    private async texture(world: string, current: () => boolean): Promise<void>
    {
        const viewport = this.viewport;
        if (!viewport)
        {
            return;
        }
        const report = await loadTextures(this.client, viewport, world, viewport.textureNames(), () =>
        {
            viewport.renderNow();
            mark('textured_low');
        }, current);
        if (!current())
        {
            return;
        }
        viewport.renderNow();
        mark('textured_full');
        probe().textures = report;
        // A liquid without a picture is expected (the game draws it): only other textures are missing.
        const liquids = new Set((this.pendingMesh?.meta.groups ?? []).filter((group) => group.kind === 'liquid').map((group) => group.texture));
        const failed = report.low.failed.filter((name) => !liquids.has(name));
        const missing = failed.length;
        this.store.setState({ textureNote: missing > 0 ? `${missing} of ${report.names} textures not found (drawn grey): ${failed.slice(0, 6).join(', ')}${missing > 6 ? ' …' : ''}` : null });
    }
}
