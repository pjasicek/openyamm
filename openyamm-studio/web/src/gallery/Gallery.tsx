// The panel gallery (S5_BROWSER_EDITOR.md 4.13, review A7 3): every panel in each of its states with fixed data,
// screenshotted by the shots script, so that an agent building a panel can look at all of it. Fixtures come from
// the example project gatehouse_cellars (scripts/make-fixtures.mjs).
import { useMemo } from 'react';
import type { AssetsSearchResult, CheckValidateResult, EditHistoryResult, Issue, Job, Pin, ProjectOpenResult, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import { makeStore, select, frameAt } from '../state/store.ts';
import type { StudioState, Store } from '../state/store.ts';
import type { Actions } from '../app/controller.ts';
import { quietActions } from '../app/controller.ts';
import { StudioContext } from '../ui/context.ts';
import { ProjectList } from '../ui/ProjectList.tsx';
import { TitleBar, StatusBar } from '../ui/Bars.tsx';
import { IssuesPanel, OutlinePanel } from '../ui/Drawer.tsx';
import { PinsPanel } from '../ui/Pins.tsx';
import { HistoryPanel } from '../ui/History.tsx';
import { Inspector } from '../ui/Inspector.tsx';
import { Views } from '../ui/Views.tsx';
import { JobsPanel, PicturesPanel, ScorecardPanel } from '../ui/Checks.tsx';
import { FlowView } from '../ui/Flow.tsx';
import { AuthorBanners, ModeSwitch, ProjectSettings, StageBar, ToolBar, ToolRail } from '../ui/Author.tsx';
import { DEFAULT_OPTIONS } from '../edit/stages.ts';
import { SwitchBoard } from '../ui/Board.tsx';
import { LibraryPanel } from '../ui/Library.tsx';
import { ChecklistPanel } from '../ui/Checklist.tsx';
import { CinematicsPanel, OverlayPanel } from '../ui/S6Panels.tsx';
import overlayFixture from './fixtures/s6_overlay.json';
import projectOpen from './fixtures/project_open.json';
import layoutFixture from './fixtures/layout.json';
import validateFixture from './fixtures/validate.json';
import checksFixture from './fixtures/jobs_checks.json';
import compareFixture from './fixtures/jobs_compare.json';
import scaleFixture from './fixtures/jobs_scale_bands.json';
import townFixture from './fixtures/jobs_town_feel.json';
import outdoorOpenFixture from './fixtures/outdoor_open.json';
import outdoorLayoutFixture from './fixtures/outdoor_layout.json';
import { HandMadeSetting } from '../ui/OutdoorAuthor.tsx';
import css from './Gallery.module.css';

const opened = projectOpen as unknown as ProjectOpenResult;
const layout = layoutFixture as unknown as ViewLayoutResult;
const validate = validateFixture as unknown as CheckValidateResult;
// S5b2: the hand-author exit test's outdoor map (scripts/make-outdoor-fixtures.mjs).
const outdoorOpened = outdoorOpenFixture as unknown as ProjectOpenResult;
const outdoorLayout = outdoorLayoutFixture as unknown as ViewLayoutResult;

const ready = <T,>(value: T) => ({ state: 'ready' as const, value });

function localActions(store: Store): Actions
{
    return {
        openProject: () => undefined,
        closeProject: () => undefined,
        select: (ref, frame) => select(store, ref, frame),
        frameAt: (at) => frameAt(store, at),
        revalidate: () => undefined,
        startPin: () => undefined,
        submitPin: async () => undefined,
        cancelPin: () => store.setState({ pinDraft: null }),
        actOnPin: async () => null,
        selectPin: (id) => store.setState({ selectedPin: id }),
        goToPin: (pin) => store.setState({ selectedPin: pin.id }),
        picture: async () => null,
        loadHistory: () => undefined,
        toggleWalk: () => undefined,
        playHere: () => undefined,
        startJob: () => undefined,
        cancelJob: () => undefined,
        // A small picture drawn here: the gallery has no host to read job pictures from.
        jobFile: async (job, relative) => galleryPicture(relative),
        openLightbox: (url, caption) => store.setState({ lightbox: { url, caption } }),
        answerWithPicture: async () => null,
        enterCompare: () => store.setState({ viewMode: 'compare' }),
        goToPlace: () => undefined,
        edit: quietActions.edit, undo: quietActions.undo, redo: quietActions.redo, revertEntry: quietActions.revertEntry,
        protect: quietActions.protect, notify: quietActions.notify, migrate: quietActions.migrate, newProject: quietActions.newProject, resolve: quietActions.resolve,
        setMode: (mode) => store.setState({ mode }),
        setStage: (stage) => store.setState({ stage }),
        setTool: (tool) => store.setState({ tool }),
        dismissNotice: (sequence) => store.setState((s) => ({ dismissedNotices: [...s.dismissedNotices, sequence] })),
        // The Library's search over a small fixed catalogue (the gallery has no asset root).
        searchAssets: async (query, kind) => libraryAnswer(query, kind),
        resolveCard: async () => null,
        sceneOverlay: async () => store.getState().overlay ?? 'no host',
        worldView: quietActions.worldView, listMods: quietActions.listMods, mapNumber: quietActions.mapNumber, packMod: quietActions.packMod,
        showGhost: () => undefined,
        dropAsset: () => undefined,
        applySurface: () => undefined,
        scriptFunctions: async () => ['evt.SetDoorState', 'evt.StatusText', 'evt.MoveToMap', 'evt.GiveItem', 'evt.SummonMonsters'],
    };
}

const LIBRARY = {
    textures: [
        { name: 't1w11a', width: 128, height: 256, size: [128, 256], usable_on_faces: true },
        { name: 't1w11b', width: 128, height: 256, size: [128, 256], usable_on_faces: true },
        { name: 'd2ceil4', width: 256, height: 256, size: [256, 256], usable_on_faces: true },
        { name: 'oflr', width: 128, height: 128, size: [128, 128], usable_on_faces: true },
        { name: 't1cl1', width: 128, height: 128, size: [128, 128], usable_on_faces: true },
        { name: '7wtrtyl', liquid: 'water', usable_on_faces: true, note: 'a liquid: no picture' },
    ],
    decorations: [
        { name: 'torch01', hint: 'torch', number: 20, radius: 8, height: 52, light_radius: 512, indoor_model: 'every dungeon' },
        { name: 'barrel', hint: 'barrel', number: 5, radius: 32, height: 64, light_radius: 0, indoor_model: 'every dungeon' },
        { name: 'chandelr', hint: 'chandelier', number: 61, radius: 40, height: 96, light_radius: 640, indoor_model: 'only on d01, d05' },
    ],
};

function libraryAnswer(query: string, kind: string): AssetsSearchResult
{
    const words = query.toLowerCase().split(/\s+/).filter(Boolean);
    const match = (entry: { name: string; hint?: string }) => words.every((word) => `${entry.name} ${entry.hint ?? ''}`.toLowerCase().includes(word));
    return kind === 'texture'
        ? { textures: LIBRARY.textures.filter(match) as AssetsSearchResult['textures'], matches: LIBRARY.textures.filter(match).length }
        : { decorations: LIBRARY.decorations.filter(match), matches: LIBRARY.decorations.filter(match).length };
}

function galleryPicture(label: string): string
{
    const hue = [...label].reduce((sum, character) => sum + character.charCodeAt(0), 0) % 360;
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="320" height="180"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">`
        + `<stop offset="0" stop-color="hsl(${hue},35%,55%)"/><stop offset="1" stop-color="hsl(${(hue + 40) % 360},30%,22%)"/></linearGradient></defs>`
        + `<rect width="320" height="180" fill="url(#g)"/><rect x="40" y="70" width="240" height="90" fill="hsl(${hue},15%,30%)"/>`
        + `<text x="12" y="24" font-family="sans-serif" font-size="14" fill="white">${label.replace(/[<&>]/g, '')}</text></svg>`;
    return `data:image/svg+xml;base64,${btoa(svg)}`;
}

const REV = (opened as { revision: string }).revision;
const OLD = 'aa00bb11cc22dd33ee44ff5566778899';
const job = (id: string, kind: Job['kind'], state: Job['state'], extra: Partial<Job> = {}): Job => ({
    id: `j${id}-abc123`, kind, title: ({ checks: 'Audit, reach and solve', compare: 'Compare with the original', scale_bands: 'Room sizes against the shipped dungeons',
        town_feel: 'Town feel against the shipped towns', building_shots: 'Buildings beside the original\'s, in the game', pins_tour: 'The game\'s pictures at the pins\' poses',
        playtest: 'The project\'s playtest in the game' } as Record<Job['kind'], string>)[kind],
    project: 'openyamm-studio/examples/gatehouse_cellars', revision: REV, state, background: kind === 'checks' || kind === 'compare',
    params: {}, created: `2026-11-15T00:0${id.length % 10}:00.000Z`, started: state === 'queued' ? null : '2026-11-15T00:01:00.000Z',
    finished: state === 'done' || state === 'failed' || state === 'cancelled' ? '2026-11-15T00:01:04.000Z' : null,
    seconds: state === 'done' || state === 'failed' ? 4.2 : null, progress: ['check.audit'], error: state === 'failed' ? 'oymap metrics: the project does not build' : null,
    line: '', pictures: [], has_result: state === 'done', ...extra,
});
const doneChecks = job('1', 'checks', 'done', { line: '0 errors, 2 warnings; coplanar 0 new; solve 2 steps, 0 never reached', seconds: 0.4 });
const doneCompare = job('2', 'compare', 'done', { line: '41.2 % (outside the band of 97 %)', seconds: 2.4 });
const doneScale = job('3', 'scale_bands', 'done', { line: '1 of 5 figures below the shipped 25th percentile', seconds: 1.1, background: true });
const doneTown = job('4', 'town_feel', 'done', { line: '4 of 22 figures outside the shipped ranges', seconds: 2.0, background: true });
const tourPictures = ['pictures/00-p1.png', 'pictures/01-p2.png', 'pictures/02-p3.png'];
const doneTour = job('5', 'pins_tour', 'done', { pictures: tourPictures, line: '3 of 3 pins pictured', seconds: 6.2, background: false });
const shotsPictures = ['shots/b1/door.jpg', 'shots/b1/n.jpg', 'shots/b1/e.jpg', 'shots/b2/door.jpg', 'shots/b2/s.jpg'];
const doneShots = job('6', 'building_shots', 'done', { pictures: shotsPictures, line: '2 buildings, 5 pictures', seconds: 412, background: false, revision: OLD });
const jobResults = {
    [doneChecks.id]: checksFixture, [doneCompare.id]: compareFixture, [doneScale.id]: scaleFixture, [doneTown.id]: townFixture,
    [doneTour.id]: { map: 'studio01.blv', world: 'mm6', shots: tourPictures.map((picture, index) => ({ pin: `pin:p${index + 1}`, name: `p${index + 1}`, picture })), skipped: ['pin:p5'] },
    [doneShots.id]: { original: 'oute3.odm', rebuilt: 'calib_newsorpigal.odm', views: 5, pictures: 5, buildings: [
        { id: 'b1', title: 'thing:temple', views: ['door', 'n', 'e'], skipped: ['w (no clear place)'], pictures: shotsPictures.slice(0, 3), contact: null },
        { id: 'b2', title: 'thing:inn', views: ['door', 's'], skipped: [], pictures: shotsPictures.slice(3), contact: null }] },
};


const history: EditHistoryResult = {
    revision: '0123456789abcdef0123456789abcdef', count: 4,
    entries: [
        { sequence: 1, kind: 'transaction', author: 'agent:gw', label: 'first rooms', time: '2026-11-14T20:01:10', revision_before: '', revision_after: 'aa', changes: ['rooms.yml: added room:hall', 'rooms.yml: added room:entry'], undone: false },
        { sequence: 2, kind: 'outside', author: 'outside', time: '2026-11-14T20:05:42', revision_before: 'aa', revision_after: 'bb', changes: ['objects.yml: light:entry changed radius (900 -> 950)'], undone: false },
        { sequence: 3, kind: 'transaction', author: 'agent:dress', label: 'lights in the crypt', time: '2026-11-14T20:09:03', revision_before: 'bb', revision_after: 'cc', changes: Array.from({ length: 12 }, (_, i) => `objects.yml: added light:crypt_${i + 1}`), undone: true },
        { sequence: 4, kind: 'revert', author: 'user', label: 'undo: lights in the crypt', time: '2026-11-14T20:10:00', revision_before: 'cc', revision_after: 'bb', changes: ['objects.yml: removed light:crypt_1'], undone: false, reverts: 3 },
    ],
};

// Author mode's history: a person's edits, a merged drag, an undo and a redo, an agent's change, an outside rewrite
// of the hand-edited project with its notice.
const authorHistory: EditHistoryResult = {
    revision: '7c1e0a5566778899aabbccddeeff0011', count: 9,
    entries: [
        { sequence: 1, kind: 'transaction', author: 'agent:gw', label: 'first rooms', time: '2026-11-15T09:01:10', revision_before: '', revision_after: 'a1', changes: ['rooms.yml: added room:hall'], undone: false, objects: ['rooms.yml#room:hall'] },
        { sequence: 2, kind: 'transaction', author: 'user', label: 'new room', time: '2026-11-15T09:05:00', revision_before: 'a1', revision_after: 'a2', changes: ['rooms.yml: added room:room_1', 'project.yml: marked as edited by hand'], undone: false, objects: ['rooms.yml#room:room_1'] },
        { sequence: 3, kind: 'transaction', author: 'user', label: 'move corner of room:hall', time: '2026-11-15T09:06:12', revision_before: 'a2', revision_after: 'a3', changes: ['rooms.yml: room:hall changed outline'], undone: false, merged: 4, objects: ['rooms.yml#room:hall'] },
        { sequence: 4, kind: 'transaction', author: 'user', label: 'floor of room:room_1', time: '2026-11-15T09:07:40', revision_before: 'a3', revision_after: 'a4', changes: ['rooms.yml: room:room_1 changed floor (0 -> 128)'], undone: true, merged: 2, objects: ['rooms.yml#room:room_1'] },
        { sequence: 5, kind: 'revert', revert_kind: 'undo', reverts: 4, author: 'user', label: 'undo: floor of room:room_1', time: '2026-11-15T09:07:52', revision_before: 'a4', revision_after: 'a5', changes: ['undone: rooms.yml: room:room_1 changed floor (128 -> 0)'], undone: true, objects: ['rooms.yml#room:room_1'] },
        { sequence: 6, kind: 'revert', revert_kind: 'redo', reverts: 5, author: 'user', label: 'redo: undo: floor of room:room_1', time: '2026-11-15T09:07:58', revision_before: 'a5', revision_after: 'a6', changes: ['redone: rooms.yml: room:room_1 changed floor (0 -> 128)'], undone: false, objects: ['rooms.yml#room:room_1'] },
        { sequence: 7, kind: 'transaction', author: 'agent:dress', label: 'torches', time: '2026-11-15T09:10:03', revision_before: 'a6', revision_after: 'a7', changes: ['objects.yml: added light:hall_1', 'objects.yml: added light:hall_2'], undone: false },
        { sequence: 8, kind: 'outside', author: 'outside', time: '2026-11-15T09:12:44', revision_before: 'a7', revision_after: 'a8', changes: ['rooms.yml: room:hall changed outline, pillars'], undone: false,
            notice: ['this project is edited by hand, and a change made outside the tool (a generator run?) replaced 1 object a person changed last: rooms.yml#room:hall; it dropped 2 written keys (rooms.yml#room:hall/pillars/big, /pillars/west).'] },
        { sequence: 9, kind: 'transaction', author: 'user', label: 'set ceiling of room:hall', time: '2026-11-15T09:14:00', revision_before: 'a8', revision_after: '7c1e0a5566778899aabbccddeeff0011', changes: ['rooms.yml: room:hall changed ceiling (512 -> 576)'], undone: false, objects: ['rooms.yml#room:hall'] },
    ],
};

function manyIssues(count: number): Issue[]
{
    const severities: Issue['severity'][] = ['error', 'warning', 'note'];
    return Array.from({ length: count }, (_, i) => ({
        severity: severities[i % 7 === 0 ? 0 : i % 3 === 0 ? 2 : 1],
        code: ['geometry', 'reference', 'heights', 'schema'][i % 4],
        file: ['rooms.yml', 'objects.yml', 'sketch.yml'][i % 3],
        path: i % 3 === 0 ? `rooms[${i % 3}].outline` : `items[${i}]`,
        message: `finding ${i + 1}: a cliff ends ${(i * 37) % 900} short of the ridge it should meet; the build takes the points as drawn`,
    }));
}

const pins: Pin[] = [
    { id: 'pin:p1', text: 'The gate leaf flickers where it meets the jamb.', on: 'room:hall', status: 'open', author: 'user', source: 'game', pose: { position: [400, 900, 0] } },
    { id: 'pin:p2', text: 'This chest floats a hand above the floor.', at: [300, 300, 0], status: 'claimed', author: 'user', source: 'game', claimed_by: 'agent:gw' },
    { id: 'pin:p3', text: 'Torch missing by the stair.', on: 'room:entry', status: 'resolved', author: 'user', source: 'studio', created: '2026-11-14T20:12:00',
        replies: [{ author: 'agent:gw', text: 'Claimed.', created: '2026-11-14T20:13:00', status: 'claimed' },
            { author: 'agent:gw', text: 'Added light:stair_torch beside the stair, radius 700; built and pictured in the game.', created: '2026-11-14T20:18:30', revision: 'cc00ff00aa11bb22', status: 'resolved' }] as Pin['replies'] },
    { id: 'pin:p4', text: 'Fine now.', on: 'room:entry', status: 'accepted', author: 'user' },
    { id: 'pin:p5', text: 'Not a fault: the original has it.', status: 'declined', author: 'user' },
];

const base: Partial<StudioState> = {
    connection: 'open',
    projectKey: 'openyamm-studio/examples/gatehouse_cellars',
    project: ready(opened),
    layout: ready(layout),
    validation: ready(validate),
    pins: ready({ counter: 9, pins }),
};

function Card({ title, state, height = 240, width, children }: { title: string; state: Partial<StudioState>; height?: number; width?: number; children: React.ReactNode })
{
    const store = useMemo(() => makeStore(state), [state]);
    const value = useMemo(() => ({ store, actions: localActions(store) }), [store]);
    return (
        <figure className={css.card} data-card={title}>
            <figcaption className={css.caption}>{title}</figcaption>
            <div className={css.body} style={{ height, width }}>
                <StudioContext.Provider value={value}>{children}</StudioContext.Provider>
            </div>
        </figure>
    );
}

// S6: the test map's arrival cinematic (examples/s6_breakwater/wiring.yml) on the gallery's project, and an overlay of
// the Isle of Ashes (view.overlay of output/studio_s6/isle, its untouched things cut to 40).
const s6Arrival = {
    id: 'cinematic:arrival',
    shots: [
        { seconds: 2.5, at: [120, 120, 420], look_at: 'chest:store', fov: 70 },
        { seconds: 3, at: [800, 300, 200], look_at: [1120, 384, 128], easing: 'smooth', keys: [{ seconds: 3, at: [960, 384, 180], look_at: [1120, 384, 128] }] },
        { seconds: 1, party: true },
    ],
    cues: [
        { at: 0, fade: 'in', seconds: 1 },
        { at: 2.5, subtitle: 'The store is barred from within.', seconds: 2.5 },
        { at: 3, event: 'evt:arrival_lamp' },
        { at: 5, shake: 0.3, seconds: 1 },
    ],
};

// One state object per card, made once (a new object would make a new store each render).
const states = {
    listReady: { ...base, projects: ready([
        { key: 'devdocs/map_studio/briefs/mm6_cd2/L4', name: 'Castle Darkmoor', kind: 'indoor', world: 'mm6', label: 'briefs/mm6_cd2/L4' },
        { key: 'devdocs/map_studio/briefs/mm7_7out02/L4', name: 'Harmondale', kind: 'outdoor', world: 'mm7', label: 'briefs/mm7_7out02/L4' },
        { key: 'devdocs/xeen/briefs/xd02/L4', name: 'The Ore Mines', kind: 'indoor', world: 'mm7', label: 'xeen/briefs/xd02/L4' },
    ]) },
    listLoading: { ...base, projects: { state: 'loading' as const } },
    listDisconnected: { ...base, connection: 'closed' as const, projects: { state: 'error' as const, message: 'not connected to the host (host.projects)', kind: 'disconnected' } },
    titleOk: { ...base, cursor: [384, 512, 0] as [number, number, number], hover: { owner: 'room:hall/walls/3' } },
    titleDisconnected: { ...base, connection: 'closed' as const, textureNote: '3 of 48 textures not found (drawn grey): t1wall, t2floor, x' },
    titleStale: { ...base, layout: ready({ ...layout, stale: true }) },
    issuesReady: base,
    cinematicsReady: { ...base, drawerTab: 'cinematics' as const, project: ready({ ...opened, files: { ...opened.files, 'wiring.yml': { ...opened.files['wiring.yml']!, tree: { ...(opened.files['wiring.yml']!.tree as object), cinematics: [s6Arrival] } as never } } }) },
    cinematicsNone: { ...base, drawerTab: 'cinematics' as const },
    overlayReady: { ...base, drawerTab: 'overlay' as const, overlay: overlayFixture as never, project: ready({ ...opened, files: { ...opened.files, 'project.yml': { ...opened.files['project.yml']!, tree: { ...(opened.files['project.yml']!.tree as object), base: 'isleofashes.blv', profile: 'region' } } } }) },
    overlayNewMap: { ...base, drawerTab: 'overlay' as const },
    issuesChecking: { ...base, validation: { state: 'loading' as const } },
    issuesEmpty: { ...base, project: ready({ ...opened, issues: [] }), validation: ready({ ...validate, ok: true, issues: [] }) },
    issuesFailed: { ...base, validation: { state: 'error' as const, message: 'the core stopped; call again', kind: 'failed' } },
    issuesMany: { ...base, validation: ready({ ...validate, ok: false, issues: manyIssues(2000) }) },
    pinsReady: base,
    pinsEmpty: { ...base, pins: ready({ counter: 0, pins: [] }) },
    pinsLoading: { ...base, pins: { state: 'loading' as const } },
    pinsFailed: { ...base, pins: { state: 'error' as const, message: 'review/pins.yml: not valid YAML', kind: 'failed' } },
    pinsThread: { ...base, selectedPin: 'pin:p3' },
    pinsComposer: { ...base, pinDraft: { where: '3d' as const, on: 'room:hall', file: 'rooms.yml', at: [412, 980, 0] as [number, number, number], sending: false } },
    pinsComposerNothing: { ...base, pinDraft: { where: 'plan' as const, sending: false, error: 'Nothing under the pointer: point at the map, then press P.' } },
    historyReady: { ...base, history: ready(history) },
    historyEmpty: { ...base, history: ready({ revision: history.revision, count: 0, entries: [] }) },
    historyFailed: { ...base, history: { state: 'error' as const, message: 'another oymap process holds the project', kind: 'locked' } },
    barsPresence: { ...base, clients: [
        { id: 1, kind: 'browser' as const, name: 'browser', project: base.projectKey ?? null, since: '' },
        { id: 2, kind: 'mcp' as const, name: 'agent:claude-code', project: null, since: '' }],
    notes: [{ id: 1, kind: 'change' as const, text: 'agent:claude-code: "brighter entry" · objects.yml: light:entry changed radius (900 -> 950)', at: 0 }] },
    barsUnreadable: { ...base, unreadable: 'wiring.yml: not valid YAML: yaml-cpp: error at line 12, column 3: end of sequence not found' },
    outline: { ...base, selection: { id: 'room:hall', file: 'rooms.yml' } },
    inspectorNone: base,
    inspectorRoom: { ...base, selection: { id: 'room:hall', file: 'rooms.yml' } },
    inspectorSource: { ...base, selection: { id: 'room:hall', file: 'rooms.yml' }, inspectorTab: 'source' as const },
    inspectorDoor: { ...base, selection: { id: (opened.ids.find((p) => p.list === 'doors')?.id ?? 'door:gate'), file: 'objects.yml' } },
    planReady: { ...base, viewMode: 'plan' as const, selection: { id: 'room:hall' }, hover: { owner: 'room:entry' } },
    planLoading: { ...base, viewMode: 'plan' as const, layout: { state: 'loading' as const } },
    planErrors: { ...base, viewMode: 'plan' as const, layout: { state: 'error' as const, kind: 'has_errors', message: 'the project has 2 issue(s)' } },
    planStale: { ...base, viewMode: 'plan' as const, layout: ready({ ...layout, stale: true, view_revision: '0123456789abcdef0123456789abcdef' }) },
    viewNoMesh: { ...base, viewMode: '3d' as const, mesh: { state: 'error' as const, kind: 'has_errors', message: 'has errors' } },
    scorecardRebuild: { ...base, jobs: ready([doneCompare, doneChecks, job('7', 'playtest', 'done', { line: '4 of 4 runs passed', has_result: false, seconds: 212 })]), jobResults },
    scorecardNew: { ...base, project: ready({ ...opened, files: { ...opened.files, 'project.yml': { ...opened.files['project.yml']!, tree: { ...(opened.files['project.yml']!.tree as object), map_stats: { id: 9301 } } } } }),
        jobs: ready([doneScale, doneChecks]), jobResults },
    scorecardOutdoor: { ...base, project: ready({ ...opened, files: { ...opened.files, 'project.yml': { ...opened.files['project.yml']!, tree: { ...(opened.files['project.yml']!.tree as object), kind: 'outdoor', map_stats: { id: 9301 } } } } }),
        jobs: ready([doneTown, job('8', 'checks', 'running', { line: 'check.audit' })]), jobResults },
    scorecardStale: { ...base, jobs: ready([job('9', 'compare', 'queued'), job('10', 'checks', 'running'), { ...doneCompare, revision: OLD }, { ...doneChecks, revision: OLD }]), jobResults },
    scorecardFailed: { ...base, jobs: ready([job('11', 'checks', 'failed', { line: 'the project does not build', error: 'the project does not build: rooms.yml: room:hall: outline must run counter-clockwise' })]), jobResults },
    scorecardLoading: { ...base, jobs: { state: 'loading' as const } },
    jobsMany: { ...base, jobs: ready([job('12', 'playtest', 'running', { line: 'run 2 of 4', params: { runs: 4 } }), job('13', 'pins_tour', 'queued'), doneTour, doneShots, doneCompare,
        job('14', 'checks', 'cancelled', { line: 'cancelled', revision: OLD }), job('15', 'scale_bands', 'failed', { line: 'scale_bands.py gave no answer' }), doneChecks]), jobResults },
    jobsNone: { ...base, jobs: ready([]) },
    pictures: { ...base, jobs: ready([doneTour, doneShots]), jobResults },
    picturesNone: { ...base, jobs: ready([doneChecks]), jobResults },
    pinsTour: { ...base, selectedPin: 'pin:p1', jobs: ready([doneTour]), jobResults },
    planHeat: { ...base, viewMode: 'plan' as const, compareHeat: true, jobs: ready([doneCompare]), jobResults },
    flowReady: { ...base, jobs: ready([doneChecks]), jobResults, selection: { id: 'room:hall', file: 'rooms.yml' } },
    flowRunning: { ...base, jobs: ready([job('16', 'checks', 'running')]), jobResults: {} },
    // Author mode (S5b1).
    authorShape: { ...base, mode: 'author' as const, stage: 2, tool: 'room' as const, history: ready(authorHistory),
        edits: { pending: 0, saved: { revision: '7c1e0a5566778899aabbccddeeff0011', at: 0, label: 'new room' } } },
    authorWriting: { ...base, mode: 'author' as const, stage: 2, tool: 'opening' as const, history: ready(authorHistory), edits: { pending: 2 },
        hint: 'opening room:hall → room:store: release to make it' },
    authorRefused: { ...base, mode: 'author' as const, stage: 3, tool: 'door' as const, toolOptions: { ...DEFAULT_OPTIONS, door: 'portcullis' }, history: ready(authorHistory),
        edits: { pending: 0, error: { label: 'door in open:hall_store', message: 'operation 0: the wall of open:hall_store is 32 thick; a door needs 48' } } },
    authorStairs: { ...base, mode: 'author' as const, stage: 2, tool: 'stairs' as const, history: ready(authorHistory) },
    authorSelect: { ...base, mode: 'author' as const, stage: 2, tool: 'select' as const, viewMode: 'plan' as const, selection: { id: 'room:hall', file: 'rooms.yml' }, history: ready(authorHistory) },
    authorPlanTool: { ...base, mode: 'author' as const, stage: 2, tool: 'pillar' as const, viewMode: 'plan' as const, selection: { id: 'room:hall', file: 'rooms.yml' }, history: ready(authorHistory) },
    authorInspector: { ...base, mode: 'author' as const, selection: { id: 'room:hall', file: 'rooms.yml' } },
    authorInspectorDoor: { ...base, mode: 'author' as const, selection: { id: (opened.ids.find((p) => p.list === 'doors')?.id ?? 'door:gate'), file: 'objects.yml' } },
    authorSource: { ...base, mode: 'author' as const, selection: { id: 'room:hall', file: 'rooms.yml' }, inspectorTab: 'source' as const },
    authorHistory: { ...base, mode: 'author' as const, history: ready(authorHistory) },
    authorNotice: { ...base, mode: 'author' as const, history: ready(authorHistory),
        edits: { pending: 0, conflict: { kind: 'undo' as const, sequence: 6, conflicts: ['rooms.yml#room:hall'] } } },
    // S5b1 part 2: the placing tools, the Wire stage, the Library and the Checklist.
    authorSwitch: { ...base, mode: 'author' as const, stage: 3, tool: 'switch' as const, history: ready(authorHistory), hint: 'switch on wall north of room:hall, 35 % along: click to place' },
    authorExit: { ...base, mode: 'author' as const, stage: 3, tool: 'exit' as const, history: ready(authorHistory) },
    authorSpawn: { ...base, mode: 'author' as const, stage: 5, tool: 'spawn' as const, history: ready(authorHistory) },
    authorLight: { ...base, mode: 'author' as const, stage: 6, tool: 'light' as const, history: ready(authorHistory) },
    authorLink: { ...base, mode: 'author' as const, stage: 4, tool: 'link' as const, history: ready(authorHistory), selection: { id: 'switch:gate_lever', file: 'objects.yml' },
        hint: 'click: switch:gate_lever toggles door:gate' },
    authorWirePlan: { ...base, mode: 'author' as const, stage: 4, tool: 'select' as const, viewMode: 'board' as const, selection: { id: 'switch:gate_lever', file: 'objects.yml' }, history: ready(authorHistory) },
    authorEvent: { ...base, mode: 'author' as const, stage: 4, selection: { id: 'evt:gate_lever', file: 'wiring.yml' } },
    authorDoorEvent: { ...base, mode: 'author' as const, stage: 4, selection: { id: 'evt:vault_door', file: 'wiring.yml' } },
    authorLever: { ...base, mode: 'author' as const, stage: 4, selection: { id: 'switch:gate_lever', file: 'objects.yml' } },
    authorLibrary: { ...base, mode: 'author' as const, stage: 6, selection: { id: 'room:hall', file: 'rooms.yml' }, drawerTab: 'library' as const },
    authorChecklist: { ...base, mode: 'author' as const, stage: 7, drawerTab: 'checklist' as const },
    authorMarked: { ...base, mode: 'author' as const, project: ready({ ...opened, hand_edited: { since: '2026-11-15', revision: '642d90046c35fe8133d02112cc81caeb',
        message: 'this project is edited by hand (project.yml edited_by_hand): change it through operations, never by running a generator again' } }) },
};

// Author mode outdoors (S5b2): the outdoor map, its town feel of the same revision.
const outdoorTown = job('17', 'town_feel', 'done', { line: '3 of 22 figures outside the shipped ranges', seconds: 2.4, background: true, revision: outdoorOpened.revision,
    project: 'output/s5b2_web/hollow_vale' });
const outdoorBase: Partial<StudioState> = {
    connection: 'open', projectKey: 'output/s5b2_web/hollow_vale', project: ready(outdoorOpened), layout: ready(outdoorLayout),
    validation: ready({ ok: true, with_assets: true, issues: [], notes: [] } as unknown as CheckValidateResult), pins: ready({ counter: 0, pins: [] }), mode: 'author',
    jobs: ready([outdoorTown]), jobResults: { [outdoorTown.id]: townFixture }, history: ready({ revision: outdoorOpened.revision, count: 0, entries: [] }),
};
const outdoorStates = {
    shape: { ...outdoorBase, stage: 2, tool: 'sculpt' as const, hint: 'raise r3: drag over the land (inside a patch, or anywhere on land made by hand)' },
    spots: { ...outdoorBase, stage: 2, tool: 'spots' as const, viewMode: 'plan' as const },
    build: { ...outdoorBase, stage: 3, tool: 'building' as const },
    road: { ...outdoorBase, stage: 2, tool: 'road' as const },
    area: { ...outdoorBase, stage: 5, tool: 'area' as const },
    structure: { ...outdoorBase, stage: 3, tool: 'structure' as const },
    plot: { ...outdoorBase, stage: 3, tool: 'plot' as const },
    wire: { ...outdoorBase, stage: 4, tool: 'select' as const },
    planPart: { ...outdoorBase, stage: 3, tool: 'select' as const, viewMode: 'plan' as const, selection: { id: 'thing:structure_2/parts/main', file: 'sketch.yml' } },
    planRoad: { ...outdoorBase, stage: 2, tool: 'select' as const, viewMode: 'plan' as const, selection: { id: '/roads/road1', file: 'sketch.yml' } },
    part: { ...outdoorBase, stage: 3, selection: { id: 'thing:structure_2/parts/main', file: 'sketch.yml' } },
    well: { ...outdoorBase, stage: 4, selection: { id: 'thing:structure_3', file: 'sketch.yml' } },
    event: { ...outdoorBase, stage: 4, selection: { id: 'evt:event_1', file: 'sketch.yml' } },
    ridge: { ...outdoorBase, stage: 2, selection: { id: '/heights/ridges/ridge1', file: 'sketch.yml' } },
};

export function Gallery()
{
    return (
        <main className={css.gallery}>
            <h1 className={css.title}>Map Studio: panel gallery</h1>
            <p className={css.lead}>Every panel in each of its states with fixed data (S5_BROWSER_EDITOR.md 4.13). Judge against devdocs/map_studio/s5_mockups/wireframes.html (W1).</p>

            <h2 className={css.section}>Project list</h2>
            <div className={css.grid}>
                <Card title="project list: ready" state={states.listReady} height={220}><ProjectList /></Card>
                <Card title="project list: loading" state={states.listLoading} height={160}><ProjectList /></Card>
                <Card title="project list: host disconnected" state={states.listDisconnected} height={160}><ProjectList /></Card>
            </div>

            <h2 className={css.section}>Title bar and status bar</h2>
            <div className={css.wide}>
                <Card title="bars: connected, hovering a wall" state={states.titleOk} height={64}><TitleBar /><StatusBar /></Card>
                <Card title="bars: disconnected, textures missing" state={states.titleDisconnected} height={64}><TitleBar /><StatusBar /></Card>
                <Card title="bars: stale view" state={states.titleStale} height={64}><TitleBar /><StatusBar /></Card>
                <Card title="bars: an agent connected, its change noted" state={states.barsPresence} height={110}><TitleBar /><StatusBar /></Card>
                <Card title="bars: a file does not parse" state={states.barsUnreadable} height={100}><TitleBar /><StatusBar /></Card>
            </div>

            <h2 className={css.section}>Issues</h2>
            <div className={css.grid}>
                <Card title="issues: checked" state={states.issuesReady}><IssuesPanel /></Card>
                <Card title="issues: checking" state={states.issuesChecking}><IssuesPanel /></Card>
                <Card title="issues: none" state={states.issuesEmpty}><IssuesPanel /></Card>
                <Card title="issues: the check failed" state={states.issuesFailed}><IssuesPanel /></Card>
                <Card title="issues: 2 000 (virtualised)" state={states.issuesMany} height={300}><IssuesPanel /></Card>
            </div>

            <h2 className={css.section}>Pins</h2>
            <div className={css.grid}>
                <Card title="pins: every status" state={states.pinsReady}><PinsPanel /></Card>
                <Card title="pins: none" state={states.pinsEmpty}><PinsPanel /></Card>
                <Card title="pins: loading" state={states.pinsLoading}><PinsPanel /></Card>
                <Card title="pins: failed" state={states.pinsFailed}><PinsPanel /></Card>
                <Card title="pins: a thread (resolved, waiting for the person)" state={states.pinsThread} height={360}><PinsPanel /></Card>
                <Card title="pins: a new pin from the 3D view" state={states.pinsComposer} height={300}><PinsPanel /></Card>
                <Card title="pins: P with nothing under the pointer" state={states.pinsComposerNothing}><PinsPanel /></Card>
            </div>

            <h2 className={css.section}>History</h2>
            <div className={css.grid}>
                <Card title="history: entries (an outside edit, an undone one, a revert)" state={states.historyReady} height={300}><HistoryPanel /></Card>
                <Card title="history: none" state={states.historyEmpty} height={120}><HistoryPanel /></Card>
                <Card title="history: failed" state={states.historyFailed} height={120}><HistoryPanel /></Card>
            </div>

            <h2 className={css.section}>Outline and inspector</h2>
            <div className={css.grid}>
                <Card title="outline: a room selected" state={states.outline} height={300}><OutlinePanel /></Card>
                <Card title="inspector: nothing selected" state={states.inspectorNone} height={300} width={420}><Inspector /></Card>
                <Card title="inspector: a room, properties" state={states.inspectorRoom} height={420} width={420}><Inspector /></Card>
                <Card title="inspector: a room, source" state={states.inspectorSource} height={300} width={420}><Inspector /></Card>
                <Card title="inspector: a door" state={states.inspectorDoor} height={360} width={420}><Inspector /></Card>
            </div>

            <h2 className={css.section}>Cinematics and overlays (S6)</h2>
            <div className={css.grid} data-section="s6">
                <Card title="cinematics: the test map's arrival" state={states.cinematicsReady} height={300} width={760}><CinematicsPanel /></Card>
                <Card title="cinematics: none" state={states.cinematicsNone} height={120}><CinematicsPanel /></Card>
                <Card title="overlay: the Isle of Ashes' beacon overlay" state={states.overlayReady} height={380} width={760}><OverlayPanel /></Card>
                <Card title="overlay: a new map" state={states.overlayNewMap} height={140}><OverlayPanel /></Card>
            </div>

            <h2 className={css.section}>Plan and 3D views</h2>
            <div className={css.grid}>
                <Card title="plan: ready, a room selected and one hovered" state={states.planReady} height={320}><Views /></Card>
                <Card title="plan: loading" state={states.planLoading} height={200}><Views /></Card>
                <Card title="plan: the project has errors" state={states.planErrors} height={200}><Views /></Card>
                <Card title="plan: stale" state={states.planStale} height={320}><Views /></Card>
                <Card title="3D: no mesh (errors)" state={states.viewNoMesh} height={200}><Views /></Card>
                <Card title="plan: the compare's heat and worst places" state={states.planHeat} height={320}><Views /></Card>
            </div>

            <h2 className={css.section}>Scorecard (S5a5)</h2>
            <div className={css.grid}>
                <Card title="scorecard: a rebuild (compare, checks, playtest)" state={states.scorecardRebuild} height={420} width={760}><ScorecardPanel /></Card>
                <Card title="scorecard: a new dungeon (scale bands)" state={states.scorecardNew} height={360} width={760}><ScorecardPanel /></Card>
                <Card title="scorecard: a new outdoor map (town feel; checks running)" state={states.scorecardOutdoor} height={360} width={760}><ScorecardPanel /></Card>
                <Card title="scorecard: results of an older revision, new ones waiting" state={states.scorecardStale} height={300} width={760}><ScorecardPanel /></Card>
                <Card title="scorecard: a check failed" state={states.scorecardFailed} height={200} width={760}><ScorecardPanel /></Card>
                <Card title="scorecard: reading" state={states.scorecardLoading} height={100}><ScorecardPanel /></Card>
            </div>

            <h2 className={css.section}>Jobs and pictures (S5a5)</h2>
            <div className={css.grid}>
                <Card title="jobs: running, waiting, done, cancelled, failed" state={states.jobsMany} height={280} width={900}><JobsPanel /></Card>
                <Card title="jobs: none" state={states.jobsNone} height={120} width={900}><JobsPanel /></Card>
                <Card title="pictures: a pins tour and building shots (older revision)" state={states.pictures} height={420} width={900}><PicturesPanel /></Card>
                <Card title="pictures: none" state={states.picturesNone} height={100}><PicturesPanel /></Card>
                <Card title="pins: a thread with the pins tour's picture" state={states.pinsTour} height={380} width={900}><PinsPanel /></Card>
            </div>

            <h2 className={css.section}>Author mode (S5b1)</h2>
            <div className={css.wide}>
                <Card title="author: the mode switch and the project's settings button (marked by hand)" state={states.authorMarked} height={40}><span className={css.inline}><ProjectSettings /><ModeSwitch /></span></Card>
                <Card title="author: stage bar (Shape), saved" state={states.authorShape} height={34}><StageBar /></Card>
                <Card title="author: stage bar, writing two gestures" state={states.authorWriting} height={34}><StageBar /></Card>
                <Card title="author: stage bar, the last gesture refused" state={states.authorRefused} height={34}><StageBar /></Card>
                <Card title="author: tool options, Room (grid, snap, floor, ceiling; undo of the person's own)" state={states.authorShape} height={34}><ToolBar /></Card>
                <Card title="author: tool options, Opening, with the tool's hint" state={states.authorWriting} height={34}><ToolBar /></Card>
                <Card title="author: tool options, Door presets" state={states.authorRefused} height={34}><ToolBar /></Card>
                <Card title="author: tool options, Stairs (rise, steps)" state={states.authorStairs} height={34}><ToolBar /></Card>
                <Card title="author: an outside rewrite's notice and an undo that left an object alone" state={states.authorNotice} height={110}><AuthorBanners /></Card>
            </div>
            <div className={css.grid}>
                <Card title="author: tool rail, Shape" state={states.authorShape} height={300} width={120}><ToolRail /></Card>
                <Card title="author: tool rail, Build" state={states.authorRefused} height={200} width={120}><ToolRail /></Card>
                <Card title="author: tool rail, Wire (part 2)" state={{ ...states.authorShape, stage: 4 }} height={140} width={120}><ToolRail /></Card>
                <Card title="author: the plan with the Select tool's handles on room:hall" state={states.authorSelect} height={360}><Views /></Card>
                <Card title="author: the plan with the Pillar tool" state={states.authorPlanTool} height={360}><Views /></Card>
                <Card title="author: inspector, a room (editable)" state={states.authorInspector} height={520} width={420}><Inspector /></Card>
                <Card title="author: inspector, a door (editable, enum and id pickers)" state={states.authorInspectorDoor} height={420} width={420}><Inspector /></Card>
                <Card title="author: inspector, the Source tab with Apply" state={states.authorSource} height={320} width={420}><Inspector /></Card>
                <Card title="author: history with undo, redo, merged edits, an outside notice, Revert this entry" state={states.authorHistory} height={520} width={760}><HistoryPanel /></Card>
                <Card title="author: the project's settings (open it: the gallery shows the trigger)" state={states.authorMarked} height={60}><ProjectSettings /></Card>
            </div>

            <h2 className={css.section}>Author mode, part 2 (S5b1): placing, wiring, Library, Checklist</h2>
            <div className={css.wide}>
                <Card title="author: tool options, Switch (kind, height) with the wall under the pointer" state={states.authorSwitch} height={34}><ToolBar /></Card>
                <Card title="author: tool options, Exit (neighbour, a new one with its arrival, with event)" state={states.authorExit} height={34}><ToolBar /></Card>
                <Card title="author: tool options, Spawn (slot, tier, radius)" state={states.authorSpawn} height={34}><ToolBar /></Card>
                <Card title="author: tool options, Light (radius, height)" state={states.authorLight} height={34}><ToolBar /></Card>
                <Card title="author: tool options, Link (verb) from the selected lever" state={states.authorLink} height={34}><ToolBar /></Card>
                <Card title="author: the Wire stage, the switch board beside the plan (the wiring dashed gold)" state={states.authorWirePlan} height={380}><Views /></Card>
            </div>
            <div className={css.grid}>
                <Card title="author: tool rail, Build (part 2: Switch, Chest, Exit)" state={states.authorSwitch} height={330} width={120}><ToolRail /></Card>
                <Card title="author: tool rail, Wire" state={states.authorLink} height={120} width={120}><ToolRail /></Card>
                <Card title="author: tool rail, Populate" state={states.authorSpawn} height={230} width={120}><ToolRail /></Card>
                <Card title="author: tool rail, Dress" state={states.authorLight} height={190} width={120}><ToolRail /></Card>
                <Card title="author: the switch board alone" state={states.authorWirePlan} height={260} width={520}><SwitchBoard /></Card>
                <Card title="author: inspector, the event form of a switch event (moves, steps, script)" state={states.authorEvent} height={900} width={420}><Inspector /></Card>
                <Card title="author: inspector, the event form of a locked door (condition rows, else)" state={states.authorDoorEvent} height={900} width={420}><Inspector /></Card>
                <Card title="author: inspector, a lever with its events and + event" state={states.authorLever} height={520} width={420}><Inspector /></Card>
                <Card title="author: the Library, textures (lay on the selected room)" state={states.authorLibrary} height={300} width={760}><LibraryPanel /></Card>
                <Card title="author: the Checklist" state={states.authorChecklist} height={420} width={760}><ChecklistPanel /></Card>
            </div>

            <div data-section="outdoor">
                <h2 className={css.section}>Author mode outdoors (S5b2)</h2>
                <div className={css.wide}>
                    <Card title="outdoor: stage bar (Shape) with the outdoor counts" state={outdoorStates.shape} height={34}><StageBar /></Card>
                    <Card title="outdoor: tool options, Sculpt (mode, radius, strength)" state={outdoorStates.shape} height={34}><ToolBar /></Card>
                    <Card title="outdoor: tool options, Building (roof, pitch, front, kit)" state={outdoorStates.build} height={34}><ToolBar /></Card>
                    <Card title="outdoor: tool options, Road (width, surface, square / 45°)" state={outdoorStates.road} height={34}><ToolBar /></Card>
                    <Card title="outdoor: tool options, Area (kind, circle, slot, markers, population)" state={outdoorStates.area} height={34}><ToolBar /></Card>
                    <Card title="outdoor: tool options, Structure (the kind)" state={outdoorStates.structure} height={34}><ToolBar /></Card>
                    <Card title="outdoor: tool options, Plot (plan building, front, + plan building)" state={outdoorStates.plot} height={34}><ToolBar /></Card>
                </div>
                <div className={css.grid}>
                    <Card title="outdoor: tool rail, Shape (with the town feel figures)" state={outdoorStates.shape} height={640} width={150}><ToolRail /></Card>
                    <Card title="outdoor: tool rail, Build" state={outdoorStates.build} height={420} width={150}><ToolRail /></Card>
                    <Card title="outdoor: tool rail, Wire (+ event)" state={outdoorStates.wire} height={420} width={150}><ToolRail /></Card>
                    <Card title="outdoor: the plan, the grid editor's spot heights over the sketch" state={outdoorStates.spots} height={420}><Views /></Card>
                    <Card title="outdoor: the plan, a building entered (its parts), Select" state={outdoorStates.planPart} height={420}><Views /></Card>
                    <Card title="outdoor: the plan, a road selected (its points' handles)" state={outdoorStates.planRoad} height={420}><Views /></Card>
                    <Card title="outdoor: inspector, a building's part: parts, roof, the wall bay strip, the door's house" state={outdoorStates.part} height={980} width={460}><Inspector /></Card>
                    <Card title="outdoor: inspector, a well's Click words (the event form's rows)" state={outdoorStates.well} height={620} width={460}><Inspector /></Card>
                    <Card title="outdoor: inspector, a sketch event in the event form" state={outdoorStates.event} height={460} width={460}><Inspector /></Card>
                    <Card title="outdoor: inspector, a ridge (a word without an id, by its pointer)" state={outdoorStates.ridge} height={420} width={460}><Inspector /></Card>
                    <Card title="outdoor: the project settings' Land section" state={outdoorStates.shape} height={160} width={460}><HandMadeSetting /></Card>
                </div>
            </div>

            <h2 className={css.section}>Flow graph (S5a5)</h2>
            <div className={css.wide}>
                <Card title="flow: the example's solve, wiring and openings" state={states.flowReady} height={420}><FlowView /></Card>
                <Card title="flow: the checks running" state={states.flowRunning} height={200}><FlowView /></Card>
            </div>
        </main>
    );
}
