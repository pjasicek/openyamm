// The hosted page's client (S5c; S5_BROWSER_EDITOR.md 2.2, PLAN.md 9 "one client interface, two backends"): the same
// interface as the local host's RpcClient, answered by the WebAssembly core in the page's one worker. The app above
// it does not know which it has, except through `mode` (the capability table: no game, no jobs).
import type { ConnectionState, HostNotices, MethodName, NoticeName, ParamsOf, ResultOf, StudioClient, WalkChannel,
    WalkChannelReply, WalkChannelRequest } from '../rpc/client.ts';
import { RpcCallError } from '../rpc/client.ts';
import type { ErrorData } from '../../../schema/rpc/generated/rpc.ts';
import type { HostedNotice, HostedReply, HostedRequest, InstallSummary, OpenedProject, Picked, ProjectPlace, WorkerStats } from './protocol.ts';

type Unnumbered<T> = T extends unknown ? Omit<T, 'id'> : never;

export class HostedClient implements StudioClient
{
    readonly mode = 'hosted' as const;
    readonly token = '';
    private readonly worker: Worker;
    private nextId = 1;
    private readonly waiting = new Map<number, { resolve: (reply: HostedReply) => void }>();
    private readonly listeners = new Set<(state: ConnectionState) => void>();
    private readonly noticeListeners = new Map<string, Set<(params: unknown) => void>>();
    private stateValue: ConnectionState = 'closed';
    private ready: Promise<void> | null = null;
    private readonly core: string;
    private readonly version: string;
    // The asset root once opened (the page shows it; methods that need assets say so until then).
    install: InstallSummary | null = null;
    // The last answer's timing inside the worker, by request type (for the budgets).
    readonly lastTiming = new Map<string, Record<string, number>>();

    constructor(options: { coreUrl: string; version: string; createWorker?: () => Worker })
    {
        this.core = options.coreUrl;
        this.version = options.version;
        this.worker = options.createWorker?.() ?? new Worker(new URL('./hosted.worker.ts', import.meta.url), { type: 'module' });
        this.worker.onmessage = (event: MessageEvent<HostedReply | HostedNotice>) =>
        {
            const message = event.data;
            if ('type' in message && message.type === 'notice')
            {
                for (const listener of this.noticeListeners.get(message.method) ?? [])
                {
                    listener(message.params);
                }
                return;
            }
            const reply = message as HostedReply;
            const entry = this.waiting.get(reply.id);
            this.waiting.delete(reply.id);
            entry?.resolve(reply);
        };
        this.worker.onerror = (event) =>
        {
            for (const entry of this.waiting.values())
            {
                entry.resolve({ id: 0, ok: false, message: `the worker failed: ${event.message}` });
            }
            this.waiting.clear();
            this.setState('closed');
        };
    }

    get state(): ConnectionState
    {
        return this.stateValue;
    }

    onState(listener: (state: ConnectionState) => void): () => void
    {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    onNotice<N extends NoticeName>(name: N, listener: (params: HostNotices[N]) => void): () => void
    {
        let set = this.noticeListeners.get(name);
        if (!set)
        {
            set = new Set();
            this.noticeListeners.set(name, set);
        }
        const entry = listener as (params: unknown) => void;
        set.add(entry);
        return () => set.delete(entry);
    }

    // Loads the core in the worker; the app is "connected" once it answers.
    connect(): void
    {
        if (this.ready)
        {
            return;
        }
        this.setState('connecting');
        this.ready = this.request({ type: 'init', coreUrl: this.core, version: this.version }).then(() => this.setState('open'),
            (error: Error) =>
            {
                this.setState('closed');
                throw error;
            });
        this.ready.catch(() => undefined);
    }

    whenReady(): Promise<void>
    {
        this.connect();
        return this.ready!;
    }

    close(): void
    {
        this.worker.terminate();
        this.setState('closed');
    }

    private setState(state: ConnectionState): void
    {
        this.stateValue = state;
        for (const listener of this.listeners)
        {
            listener(state);
        }
    }

    private send(request: Unnumbered<HostedRequest>, transfer: Transferable[] = []): Promise<HostedReply>
    {
        const id = this.nextId++;
        return new Promise((resolve) =>
        {
            this.waiting.set(id, { resolve });
            this.worker.postMessage({ ...request, id } as HostedRequest, transfer);
        });
    }

    // A request of the worker's own (not the request list): its value, or an Error with the worker's words.
    async request<T = unknown>(request: Unnumbered<HostedRequest>): Promise<T>
    {
        const reply = await this.send(request);
        if (!reply.ok)
        {
            throw new Error(reply.message);
        }
        if (reply.timing)
        {
            this.lastTiming.set(request.type, reply.timing);
        }
        return reply.value as T;
    }

    async call<M extends MethodName>(method: M, params: ParamsOf<M>): Promise<ResultOf<M>>
    {
        await this.whenReady();
        const reply = await this.send({ type: 'call', method, params: (params ?? {}) as Record<string, unknown> });
        if (!reply.ok)
        {
            throw new RpcCallError('failed', -32603, reply.message);
        }
        if (reply.timing)
        {
            this.lastTiming.set(`call:${method}`, reply.timing);
        }
        const answer = reply.value as { result?: unknown; error?: { code: number; message: string; data?: ErrorData } };
        if (answer.error)
        {
            throw new RpcCallError(answer.error.data?.kind ?? 'failed', answer.error.code, answer.error.message, answer.error.data);
        }
        return answer.result as ResultOf<M>;
    }

    async fetchBytes(path: string): Promise<{ bytes: ArrayBuffer; headers: Headers }>
    {
        await this.whenReady();
        const value = await this.request<{ status: number; headers: Record<string, string>; body: Uint8Array }>({ type: 'bytes', path });
        if (value.status !== 200)
        {
            throw new RpcCallError('transport', value.status, `${path}: ${value.status} ${new TextDecoder().decode(value.body)}`);
        }
        const body = value.body;
        const bytes = body.byteOffset === 0 && body.byteLength === body.buffer.byteLength ? body.buffer as ArrayBuffer : body.slice().buffer as ArrayBuffer;
        return { bytes, headers: new Headers(value.headers) };
    }

    routeUrl(path: string): string
    {
        return path;
    }

    coreUrl(): string
    {
        return this.core;
    }

    // Walk mode in the page's one worker: the walk's files are there already (host.walk_prepare built them).
    walkChannel(): WalkChannel
    {
        return {
            send: async (request: WalkChannelRequest): Promise<WalkChannelReply> =>
            {
                const started = performance.now();
                if (request.type === 'load')
                {
                    const reply = await this.send({ type: 'walk_load', files: request.files });
                    return reply.ok ? { answer: reply.value as WalkChannelReply['answer'], timing: { coreMs: 0, fetchMs: 0, loadMs: reply.timing?.loadMs ?? performance.now() - started, bytes: 0 } }
                        : { answer: { error: { message: reply.message } } };
                }
                const reply = await this.send({ type: 'call', method: request.method, params: request.params as Record<string, unknown> });
                return reply.ok ? { answer: reply.value as WalkChannelReply['answer'], timing: { callMs: reply.timing?.ms } }
                    : { answer: { error: { message: reply.message } } };
            },
            terminate: () => undefined,
        };
    }

    // --- what only the hosted page does ------------------------------------------------------------------------

    async openAssets(picked: Picked): Promise<InstallSummary>
    {
        await this.whenReady();
        this.install = await this.request<InstallSummary>({ type: 'open_assets', picked });
        return this.install;
    }

    async openProject(picked: Picked | { kind: 'zip'; file: File } | { kind: 'browser'; name: string }, place: 'folder' | 'browser' | 'memory', name: string): Promise<OpenedProject>
    {
        await this.whenReady();
        return this.request<OpenedProject>({ type: 'open_project', picked, place, name });
    }

    async newProject(place: ProjectPlace, params: Record<string, unknown>): Promise<OpenedProject>
    {
        await this.whenReady();
        return this.request<OpenedProject>({ type: 'new_project', place, params });
    }

    // A shipped map of the install as an overlay project (project.import).
    async importMap(place: ProjectPlace, map: string, world: string): Promise<OpenedProject>
    {
        await this.whenReady();
        return this.request<OpenedProject>({ type: 'import_map', place, map, world });
    }

    async browserProjects(): Promise<string[]>
    {
        await this.whenReady();
        return this.request<string[]>({ type: 'browser_projects' });
    }

    async exportZip(key: string, what: 'project' | 'build' | 'mod'): Promise<{ bytes: Uint8Array; files: number }>
    {
        return this.request({ type: 'export', key, what });
    }

    async saveTo(key: string, what: 'build' | 'mod', handle: FileSystemDirectoryHandle): Promise<{ files: number }>
    {
        return this.request({ type: 'save_to', key, what, handle });
    }

    async stats(timings = false): Promise<WorkerStats>
    {
        return this.request({ type: 'stats', timings });
    }
}
