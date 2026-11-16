// UI state (S5_BROWSER_EDITOR.md 4.6): Zustand stores, small and framework-agnostic, read by React panels and by
// the plan and 3D view modules alike. Project data is read-only data at a revision; the client never owns it.
import { createStore, useStore } from 'zustand';
import type { CheckValidateResult, EditHistoryResult, Issue, Job, Pin, ProjectOpenResult, ViewLayoutAtResult, ViewLayoutResult, ViewMeshResult, ViewOriginalMeshResult, ViewOverlayResult, WalkPose } from '../../../schema/rpc/generated/rpc.ts';
import type { ConnectionState, HostClient, HostProject } from '../rpc/client.ts';
import type { Pose } from '../model/pins.ts';
import type { ObjectRef } from '../model/objects.ts';
import type { ToolName, ToolOptions } from '../edit/stages.ts';
import { DEFAULT_OPTIONS } from '../edit/stages.ts';

export type Loadable<T> =
    | { state: 'idle' }
    | { state: 'loading' }
    | { state: 'ready'; value: T }
    | { state: 'error'; message: string; kind?: string };

// compare: the original and the rebuild side by side, cameras locked (3.14); flow: the flow graph (3.7); board: the
// switch board beside the plan (3.7).
export type ViewMode = 'plan' | 'split' | '3d' | 'compare' | 'flow' | 'board';
export type DrawerTab = 'issues' | 'scorecard' | 'pins' | 'history' | 'jobs' | 'pictures' | 'outline' | 'library' | 'checklist'
    | 'cinematics' | 'overlay';
export type InspectorTab = 'properties' | 'source' | 'issues' | 'connections' | 'notes' | 'original';

export interface Hover
{
    owner: string;
    point?: [number, number, number];
}

// A pin being written (P in the plan or the 3D view): what it is on, where, from which camera, with the view's picture.
export interface PinDraft
{
    where: 'plan' | '3d';
    on?: string;
    file?: string;
    at?: [number, number, number];
    pose?: Pose;
    // The picture as a data URL (JPEG or PNG), shown in the composer and sent with the pin.
    picture?: string;
    sending: boolean;
    error?: string;
}

// A short note of what changed (an agent's edit, a pin answered, someone joining), shown for a few seconds.
export interface ChangeNote
{
    id: number;
    text: string;
    kind: 'change' | 'pins' | 'presence';
    at: number;
}

// Walk mode (S5a4, S5_BROWSER_EDITOR.md 3.6): the party walking the built map in the worker.
export interface WalkState
{
    state: 'off' | 'starting' | 'on' | 'error';
    kind?: 'indoor' | 'outdoor';
    pose?: WalkPose;
    // The pointer is locked to the view (mouse look).
    locked?: boolean;
    message?: string;
}

// Play here's game (S5a4): started by the host; when it closes, the camera goes where the party stood.
export interface PlayState
{
    state: 'idle' | 'starting' | 'running' | 'error';
    run?: string;
    message?: string;
}

// Author mode's edits (S5_BROWSER_EDITOR.md 2.5, 2.7): gestures sent and not answered yet, the last one written,
// the last refusal, and a revert that met objects changed since (shown with "put them back anyway").
export interface EditState
{
    pending: number;
    saved?: { revision: string; at: number; label: string };
    error?: { label: string; message: string } | null;
    conflict?: { kind: 'undo' | 'redo' | 'revert'; sequence?: number; conflicts: string[] } | null;
}

export interface StudioState
{
    connection: ConnectionState;
    projects: Loadable<HostProject[]>;
    projectKey: string | null;
    project: Loadable<ProjectOpenResult>;
    layout: Loadable<ViewLayoutResult>;
    mesh: Loadable<ViewMeshResult>;
    validation: Loadable<CheckValidateResult>;
    pins: Loadable<{ counter: number; pins: Pin[] }>;
    selection: ObjectRef | null;
    hover: Hover | null;
    cursor: [number, number, number] | null;
    viewMode: ViewMode;
    maximised: 'plan' | '3d' | null;
    drawerTab: DrawerTab;
    // An overlay project's scene things given by the gallery (the app reads them with view.overlay; S6 item O).
    overlay?: ViewOverlayResult | string;
    inspectorTab: InspectorTab;
    textured: boolean;
    cutaway: boolean;
    band: number | null;
    // Increments ask the views to frame something: the selection, or a place.
    frameRequest: { serial: number; at?: [number, number, number] };
    textureNote: string | null;
    // The project's history (edit.history), read on open and after every change.
    history: Loadable<EditHistoryResult>;
    // Who is connected to the host: browsers and agents' MCP sessions.
    clients: HostClient[];
    notes: ChangeNote[];
    // A file of the open project does not parse: the views keep the last good state, read only.
    unreadable: string | null;
    pinDraft: PinDraft | null;
    selectedPin: string | null;
    pinFilter: 'active' | 'all';
    walk: WalkState;
    play: PlayState;
    // The project's jobs (S5a5: jobs.list, kept current by job_progress and job_done) and the results read so far, by
    // job id (jobs.status).
    jobs: Loadable<Job[]>;
    jobResults: Record<string, unknown>;
    // The compare's heat and worst places drawn over the plan.
    compareHeat: boolean;
    // The original's mesh for the Compare view (view.original_mesh).
    original: Loadable<ViewOriginalMeshResult>;
    // The host runs the Python checks (session.hello's host.python): false hides their buttons.
    python: boolean;
    // A picture opened full size (Pictures, the scorecard): its object URL and caption.
    lightbox: { url: string; caption: string } | null;
    // Review (nothing edits) or Author (the stage bar, the tools, the editable inspector): 3.2.
    mode: 'review' | 'author';
    stage: number;
    tool: ToolName;
    toolOptions: ToolOptions;
    edits: EditState;
    // What the active tool says to do next (the status bar).
    hint: string | null;
    // Outside rewrites whose notice the person put away (history sequences).
    dismissedNotices: number[];
    // The host's project roots (host.projects): where a new project can be made.
    projectRoots: string[];
    // History's "show as it was" (3.12): the layout before an entry, drawn as a ghost over the current (null: none).
    ghost: { sequence: number; layout: ViewLayoutAtResult | null } | null;
}

export const initialState: StudioState = {
    connection: 'closed',
    projects: { state: 'idle' },
    projectKey: null,
    project: { state: 'idle' },
    layout: { state: 'idle' },
    mesh: { state: 'idle' },
    validation: { state: 'idle' },
    pins: { state: 'idle' },
    selection: null,
    hover: null,
    cursor: null,
    viewMode: 'split',
    maximised: null,
    drawerTab: 'issues',
    inspectorTab: 'properties',
    textured: true,
    cutaway: false,
    band: null,
    frameRequest: { serial: 0 },
    textureNote: null,
    history: { state: 'idle' },
    clients: [],
    notes: [],
    unreadable: null,
    pinDraft: null,
    selectedPin: null,
    pinFilter: 'active',
    walk: { state: 'off' },
    play: { state: 'idle' },
    jobs: { state: 'idle' },
    jobResults: {},
    compareHeat: false,
    original: { state: 'idle' },
    python: true,
    lightbox: null,
    mode: 'review',
    stage: 2,
    tool: 'select',
    toolOptions: DEFAULT_OPTIONS,
    edits: { pending: 0 },
    hint: null,
    dismissedNotices: [],
    projectRoots: [],
    ghost: null,
};

export type Store = ReturnType<typeof makeStore>;

export function makeStore(initial: Partial<StudioState> = {})
{
    return createStore<StudioState>()(() => ({ ...initialState, ...initial }));
}

// The app's one store; the gallery makes its own per panel state.
export const studio = makeStore();

export function useStudio<T>(select: (state: StudioState) => T, store: Store = studio): T
{
    return useStore(store, select);
}

// One empty list for every selector that has nothing to give: a selector must return the same value for the same
// state (zustand compares by reference; a fresh [] each call re-renders without end).
export const NONE: never[] = [];

// Every issue the client knows: the full check when it has answered, else what project.open found.
export function knownIssues(state: Pick<StudioState, 'project' | 'validation'>): Issue[]
{
    if (state.validation.state === 'ready')
    {
        return state.validation.value.issues;
    }
    return state.project.state === 'ready' ? state.project.value.issues : NONE;
}

export function select(store: Store, ref: ObjectRef | null, frame = false): void
{
    store.setState((state) => ({
        selection: ref,
        frameRequest: frame ? { serial: state.frameRequest.serial + 1 } : state.frameRequest,
    }));
}

export function frameAt(store: Store, at: [number, number, number]): void
{
    store.setState((state) => ({ frameRequest: { serial: state.frameRequest.serial + 1, at } }));
}
