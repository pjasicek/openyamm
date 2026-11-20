// The controller's side of the pin loop with a scripted host: a pin made with P in the 3D view (its object, point,
// camera as a pose and picture), an agent's answer arriving as a notice, and a change by an agent refreshing the
// project without moving the cameras.
import { describe, expect, it } from 'vitest';
import { RpcClient } from '../rpc/client.ts';
import type { SocketLike } from '../rpc/client.ts';
import { makeStore } from '../state/store.ts';
import { Controller, pinChanges } from './controller.ts';
import type { ViewportHandle } from './controller.ts';

// The suite runs in Node: the little of a page the controller touches (its probe, the URL it keeps the project in).
const page = globalThis as unknown as Record<string, unknown>;
page.window ??= globalThis;
page.location ??= { href: 'http://127.0.0.1:8765/', search: '' };
page.history ??= { replaceState: () => undefined };

type Handler = (params: Record<string, unknown>) => unknown;

class ScriptedHost implements SocketLike
{
    readyState = 0;
    calls: { method: string; params: Record<string, unknown> }[] = [];
    onopen: ((event: unknown) => void) | null = null;
    onclose: ((event: unknown) => void) | null = null;
    onerror: ((event: unknown) => void) | null = null;
    onmessage: ((event: { data: unknown }) => void) | null = null;
    readonly handlers: Record<string, Handler>;

    constructor(handlers: Record<string, Handler>)
    {
        this.handlers = handlers;
        setTimeout(() =>
        {
            this.readyState = 1;
            this.onopen?.({});
        }, 0);
    }

    send(data: string): void
    {
        const request = JSON.parse(data);
        this.calls.push({ method: request.method, params: request.params });
        const handler = this.handlers[request.method];
        setTimeout(() =>
        {
            let answer: object;
            try
            {
                answer = handler ? { result: handler(request.params) } : { error: { code: -32601, message: 'no', data: { kind: 'unknown_method' } } };
            }
            catch (error)
            {
                answer = { error: { code: -32000, message: (error as Error).message, data: { kind: 'has_errors', issues: [] } } };
            }
            this.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', id: request.id, ...answer }) });
        }, 0);
    }

    notice(method: string, params: unknown): void
    {
        this.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', method, params }) });
    }

    close(): void
    {
        this.onclose?.({});
    }
}

const tick = (ms = 5) => new Promise((resolve) => setTimeout(resolve, ms));

function setup()
{
    let counter = 0;
    let revision = 'r1';
    const pins: Record<string, unknown>[] = [];
    let host!: ScriptedHost;
    const handlers: Record<string, Handler> = {
        'host.projects': () => ({ projects: [] }),
        'host.subscribe': () => ({ revision, counter, clients: [{ id: 1, kind: 'browser', name: 'browser', project: 'p', since: '' }] }),
        'project.open': () => ({ revision, lock_hash: 'none', files: { 'project.yml': { tree: { id: 'gw', kind: 'indoor', world: 'mm6' } } }, ids: [], issues: [] }),
        'view.layout': () => ({ revision, view_revision: revision, stale: false, kind: 'indoor', world: 'mm6', rooms: [], openings: [], doors: [], things: [] }),
        'view.mesh': () => { throw new Error('no mesh in this test'); },
        'check.validate': () => ({ ok: true, with_assets: false, issues: [], notes: [] }),
        'edit.history': () => ({ revision, count: 0, entries: [] }),
        'pins.list': () => ({ counter, pins }),
        'pins.add': (params) =>
        {
            counter += 1;
            const pin = { id: `pin:p${pins.length + 1}`, text: params.text, on: params.on, at: params.at, pose: params.pose, status: 'open', author: 'user', source: 'studio', picture: params.picture ? `.oymap/pins/pictures/p${pins.length + 1}.jpg` : undefined };
            pins.push(pin);
            return { counter, pin };
        },
        'game.play_here': (params) => ({ run: 'studio-play-1', map: 'gw.blv', world: 'mm6', kind: 'indoor', echo: params }),
        'pins.accept': (params) =>
        {
            counter += 1;
            const pin = pins.find((p) => p.id === params.pin)!;
            pin.status = 'accepted';
            return { counter, pin };
        },
    };
    const client = new RpcClient({ url: 'ws://h/rpc', token: 't', reconnectMs: 0, createSocket: () => (host = new ScriptedHost(handlers)) });
    const store = makeStore();
    const controller = new Controller(client, store);
    client.connect();
    const cameraSet: unknown[] = [];
    const viewport = {
        cameraSet,
        loadMesh: () => undefined, textureNames: () => [], renderNow: () => undefined, setTexture: () => undefined,
        capture: () => 'data:image/jpeg;base64,/9j/AAAA',
        camera: () => ({ eye: [100, 200, 160], yaw: Math.PI / 2, pitch: 0 }),
        setCamera: (camera: unknown) => { cameraSet.push(camera); },
        pickCentre: () => null,
        lastHover: { owner: 'room:hall/walls/3', base: 'room:hall', file: 'rooms.yml', point: [120, 260, 64] },
    } as unknown as ViewportHandle & { cameraSet: unknown[] };
    controller.attachViewport(viewport);
    return { controller, store, host: () => host, pins, viewport, setRevision: (value: string) => { revision = value; }, bump: () => ++counter };
}

describe('the pin loop in the controller', () =>
{
    it('pins what is under the pointer with the camera and the picture, then hears an agent answer', async () =>
    {
        const { controller, store, host, pins, bump } = setup();
        await tick();
        controller.openProject('p');
        await tick(20);
        expect(host().calls.some((call) => call.method === 'host.subscribe' && call.params.project === 'p')).toBe(true);
        expect(store.getState().clients).toHaveLength(1);

        controller.startPin('3d');
        const draft = store.getState().pinDraft!;
        expect(draft.on).toBe('room:hall');
        expect(draft.file).toBe('rooms.yml');
        expect(draft.at).toEqual([120, 260, 64]);
        expect(draft.pose).toEqual({ position: [100, 200, 0], yaw_radians: 1.5708, pitch_degrees: 0, heading_yaw_units: 512 });
        expect(store.getState().drawerTab).toBe('pins');

        await controller.submitPin('Too dark here.');
        const sent = host().calls.find((call) => call.method === 'pins.add')!.params;
        expect(sent).toMatchObject({ project: 'p', text: 'Too dark here.', on: 'room:hall', file: 'rooms.yml', author: 'user', source: 'studio', map: 'gw.blv', world: 'mm6' });
        expect(sent.picture).toEqual({ media_type: 'image/jpeg', base64: '/9j/AAAA' });
        expect(store.getState().pinDraft).toBeNull();
        expect(store.getState().selectedPin).toBe('pin:p1');
        expect(store.getState().pins.state).toBe('ready');

        // An agent resolves it elsewhere: the notice brings the new state.
        pins[0].status = 'resolved';
        pins[0].replies = [{ author: 'agent:x', text: 'Brighter now.', status: 'resolved' }];
        const counter = bump();
        host().notice('pins_changed', { project: 'p', counter, pin: 'pin:p1', action: 'resolve', by: 'agent:x' });
        await tick(20);
        const state = store.getState();
        expect(state.pins.state === 'ready' && state.pins.value.pins[0].status).toBe('resolved');
        expect(state.notes.at(-1)?.text).toBe('agent:x resolved pin:p1: Brighter now.');

        // The person accepts.
        const pin = state.pins.state === 'ready' ? state.pins.value.pins[0] : null;
        expect(await controller.actOnPin(pin!, 'accept', '')).toBeNull();
        const after = store.getState();
        expect(after.pins.state === 'ready' && after.pins.value.pins[0].status).toBe('accepted');
    });

    it('goes to a game pin\'s pose, and refreshes the project when an agent changes it', async () =>
    {
        const { controller, store, host, viewport, setRevision } = setup();
        await tick();
        controller.openProject('p');
        await tick(20);
        controller.goToPin({ id: 'pin:p9', text: 'x', pose: { position: [10, 20, 30], yaw_radians: 0, pitch_degrees: -10 } });
        expect(viewport.cameraSet).toHaveLength(1);
        expect(viewport.cameraSet[0]).toMatchObject({ eye: [10, 20, 190], yaw: 0 });
        expect(store.getState().selectedPin).toBe('pin:p9');

        const before = host().calls.filter((call) => call.method === 'project.open').length;
        setRevision('r2');
        host().notice('revision_changed', { project: 'p', revision: 'r2', previous: 'r1', author: 'agent:x', label: 'more light', changes: ['objects.yml: light:a changed radius'], entry: 3 });
        await tick(30);
        expect(host().calls.filter((call) => call.method === 'project.open').length).toBe(before + 1);
        const state = store.getState();
        expect(state.project.state === 'ready' && state.project.value.revision).toBe('r2');
        expect(state.notes.at(-1)?.text).toContain('agent:x: "more light"');
        // A notice for another project changes nothing.
        host().notice('revision_changed', { project: 'q', revision: 'r9', previous: null, author: 'agent:x', label: '', changes: [], entry: null });
        await tick(10);
        expect(host().calls.filter((call) => call.method === 'project.open').length).toBe(before + 1);
    });
});

describe('Play here and the game\'s exit pose', () =>
{
    it('starts the game at the camera, and the camera follows where the party stood when it closed', async () =>
    {
        const { controller, store, host, viewport } = setup();
        await tick();
        controller.openProject('p');
        await tick(20);
        controller.playHere({ visible: false, commands: ['gold 5000'], seconds: 6 });
        expect(store.getState().play.state).toBe('starting');
        await tick(20);
        const sent = host().calls.find((call) => call.method === 'game.play_here')!.params;
        // The pose is the camera's, as the game's `loc` gives it: the feet under the eye.
        expect(sent).toEqual({ project: 'p', pose: { position: [100, 200, 0], yaw_radians: 1.5708, pitch_degrees: 0, heading_yaw_units: 512 },
            visible: false, commands: ['gold 5000'], seconds: 6 });
        expect(store.getState().play).toEqual({ state: 'running', run: 'studio-play-1' });

        host().notice('game_exited', { project: 'p', run: 'studio-play-1', map: 'gw.blv', world: 'mm6', code: 0,
            exit: { world: 'mm6', map: 'gw.blv', pose: { position: [640, 6976, 192], yaw_radians: 1.571, pitch_degrees: -12.5, heading_yaw_units: 512 } } });
        await tick(10);
        expect(store.getState().play.state).toBe('idle');
        expect(viewport.cameraSet.at(-1)).toMatchObject({ eye: [640, 6976, 352], yaw: 1.571 });
        expect(store.getState().notes.at(-1)?.text).toContain('where the party stood (640, 6976, 192)');

        // A game that closed on another map (the party left by an exit) leaves the camera.
        const cameras = viewport.cameraSet.length;
        host().notice('game_exited', { project: 'p', run: 'studio-play-2', map: 'gw.blv', world: 'mm6', code: 0,
            exit: { world: 'mm6', map: 'oute3.odm', pose: { position: [1, 2, 3], yaw_radians: 0, pitch_degrees: 0, heading_yaw_units: 0 } } });
        await tick(10);
        expect(viewport.cameraSet.length).toBe(cameras);
        expect(store.getState().notes.at(-1)?.text).toContain('another map (oute3.odm)');
    });
});

describe('notes of what others did to the pins', () =>
{
    it('says what came from the game and what an agent claimed or answered, not the person\'s own steps', () =>
    {
        const before = [
            { id: 'pin:p1', text: 'a', status: 'open' as const, author: 'user' },
            { id: 'pin:p2', text: 'b', status: 'resolved' as const, author: 'user', replies: [{ author: 'agent:x', text: 'done', status: 'resolved' as const }] },
        ];
        const after = [
            { id: 'pin:p1', text: 'a', status: 'claimed' as const, author: 'user', claimed_by: 'agent:x' },
            { id: 'pin:p2', text: 'b', status: 'accepted' as const, author: 'user', replies: [{ author: 'agent:x', text: 'done', status: 'resolved' as const }, { author: 'user', status: 'accepted' as const }] },
            { id: 'pin:p3', text: 'the door sticks', status: 'open' as const, author: 'user', source: 'game' as const },
            { id: 'pin:p4', text: 'c', status: 'open' as const, author: 'agent:y', source: 'agent' as const },
        ];
        expect(pinChanges(before, after)).toEqual(['agent:x claimed pin:p1', 'A pin from the game arrived: pin:p3 "the door sticks"', 'agent:y pinned pin:p4']);
    });
});

describe('jobs in the controller (S5a5)', () =>
{
    const job = (id: string, kind: string, state: string, extra: Record<string, unknown> = {}) => ({ id, kind, title: kind, project: 'p', revision: 'r1', state,
        background: true, params: {}, created: `2026-11-15T00:00:0${id.slice(1, 2)}`, started: null, finished: null, seconds: null, progress: [], error: null,
        line: '', pictures: [], has_result: state === 'done', ...extra });

    it('reads the jobs and their results on open, follows the notices, starts and cancels, and answers a pin with a tour picture', async () =>
    {
        const { controller, store, host, viewport } = setup();
        const results: Record<string, unknown> = {
            j1: { kind: 'indoor', score: 0.98, band: { at_least: 0.97, within: true }, worst: [], heat: { cell: 256, points: [] }, vertical_offset: 0 },
            j3: { map: 'gw.blv', world: 'mm6', shots: [{ pin: 'pin:p1', name: 'p1', picture: 'pictures/00-p1.png' }], skipped: [] },
        };
        const handlers = host().handlers;
        handlers['jobs.list'] = () => ({ jobs: [job('j1', 'compare', 'done'), job('j2', 'checks', 'running')] });
        handlers['jobs.status'] = (params) => ({ job: { ...job(String(params.job), 'compare', 'done'), result: results[String(params.job)] } });
        handlers['jobs.start'] = (params) => ({ job: job('j9', String(params.kind), 'queued', { background: false, params: params.params }) });
        handlers['jobs.cancel'] = (params) => ({ job: job(String(params.job), 'checks', 'running') });
        handlers['pins.reply'] = () => ({ counter: 1, pin: { id: 'pin:p1', text: 't', status: 'open' } });
        await tick();
        controller.openProject('p');
        await tick(30);
        const state = store.getState();
        expect(state.jobs.state).toBe('ready');
        expect(state.jobs.state === 'ready' && state.jobs.value.map((entry) => entry.id)).toEqual(['j1', 'j2']);
        expect(state.jobResults.j1).toMatchObject({ score: 0.98 });

        // A job's progress and its end, by notice; its result read when it has one; a note for a job asked for.
        host().notice('job_progress', { project: 'p', job: job('j2', 'checks', 'running', { line: 'check.audit' }) });
        host().notice('job_done', { project: 'p', job: job('j3', 'pins_tour', 'done', { background: false, line: '1 of 1 pins pictured', pictures: ['pictures/00-p1.png'] }) });
        await tick(20);
        const jobs = store.getState().jobs;
        expect(jobs.state === 'ready' && jobs.value[0].id).toBe('j3');
        expect(store.getState().jobResults.j3).toMatchObject({ shots: [{ pin: 'pin:p1' }] });
        expect(store.getState().notes.at(-1)?.text).toContain('1 of 1 pins pictured');
        // Another project's notice is not this one's.
        host().notice('job_done', { project: 'q', job: job('j4', 'checks', 'done') });
        await tick(10);
        expect((store.getState().jobs as unknown as { value: { id: string }[] }).value.some((entry) => entry.id === 'j4')).toBe(false);

        controller.startJob('playtest', { runs: 4 });
        await tick(10);
        expect(host().calls.find((call) => call.method === 'jobs.start')!.params).toEqual({ project: 'p', kind: 'playtest', params: { runs: 4 } });
        expect(store.getState().drawerTab).toBe('jobs');
        controller.cancelJob('j2');
        await tick(10);
        expect(host().calls.some((call) => call.method === 'jobs.cancel' && call.params.job === 'j2')).toBe(true);

        // The tour's picture as a reply: the bytes from the job's byte route, base64 in pins.reply.
        const fetched: string[] = [];
        (controller.client as unknown as { fetchBytes: (path: string) => Promise<{ bytes: ArrayBuffer }> }).fetchBytes = async (path: string) =>
        {
            fetched.push(path);
            return { bytes: new Uint8Array([137, 80, 78, 71]).buffer };
        };
        const tour = (store.getState().jobs as unknown as { value: { id: string }[] }).value.find((entry) => entry.id === 'j3')! as never;
        const refused = await controller.answerWithPicture({ id: 'pin:p1', text: 't' } as never, tour, 'pictures/00-p1.png', 'reply', 'In the game now.');
        expect(refused).toBeNull();
        expect(fetched).toEqual(['/job/p/r1/j3/pictures/00-p1.png']);
        const reply = host().calls.find((call) => call.method === 'pins.reply')!.params;
        expect(reply).toMatchObject({ project: 'p', pin: 'pin:p1', by: 'user', text: 'In the game now.', pictures: [{ media_type: 'image/png', base64: 'iVBORw==' }] });

        // A place: the camera at the party's eye there.
        controller.goToPlace([100, 200, 0], 1);
        expect(viewport.cameraSet.at(-1)).toEqual({ eye: [100, 200, 160], yaw: 1, pitch: -0.12 });
    });
});
