// The RPC client (S5_BROWSER_EDITOR.md 2.3, 4.6): JSON-RPC 2.0 over the host's WebSocket, typed by the request list
// generated from schema/rpc (never copied), plus the host's own methods. Framework-free: React panels and the view
// modules use it alike. Byte loads (meshes, textures) go through `fetchBytes`, which sends the pairing token as an
// Authorization header; nothing loads bytes through a bare URL.
import type { Job, RpcMethods, RpcMethodName, RpcError, RpcErrorKind, ErrorData } from '../../../schema/rpc/generated/rpc.ts';

// The host's own methods (not the core's): the project list it allows (its path jail).
export interface HostProject
{
    // What the browser names the project by in every call (`project` param); a path relative to the repository.
    key: string;
    name: string;
    kind: string;
    world: string;
    // A shorter label of the folder (briefs/mm6_cd2/L4).
    label?: string;
}

// A client connected to the host: a browser, or an agent's MCP session (named agent:<its client's name>).
export interface HostClient
{
    id: number;
    kind: 'browser' | 'mcp';
    name: string;
    // The project key a browser has open.
    project: string | null;
    since: string;
}

export interface HostMethods
{
    // roots: each project root's key; a new project (project.new) is named <root key>/<folder>.
    'host.projects': { params: Record<string, never>; result: { projects: HostProject[]; roots?: string[] } };
    // This browser has the project open (null: none): the host watches it and sends its notices.
    'host.subscribe': {
        params: { project: string | null };
        result: { revision: string | null; counter: number | null; unreadable?: string | null; clients: HostClient[] };
    };
    'host.clients': { params: Record<string, never>; result: { clients: HostClient[] } };
    // Walk mode (S5a4): builds the project and names the byte routes of what the walk's worker loads.
    'host.walk_prepare': {
        params: { project: string };
        result: { kind: 'indoor' | 'outdoor'; map: string; files: { map: string; state: string; decorations: string; terrain?: string } };
    };
}

// The game's exit pose (Play here: game/debug/ExitPose.h), as the host read it.
export interface ExitPose
{
    world: string;
    map: string;
    pose: { position: [number, number, number]; yaw_radians: number; pitch_degrees: number; heading_yaw_units: number };
}

// The host's notices (JSON-RPC notifications; host/src/studio.mjs says when each is sent). The pins counter is the
// pins document's own, never a revision.
export interface HostNotices
{
    revision_changed: {
        project: string;
        revision: string;
        previous: string | null;
        // user, agent:<name>, or outside (found on disk, not attributed).
        author: string;
        label: string;
        changes: string[];
        // The history entry, when the change has one.
        entry: number | null;
    };
    project_unreadable: { project: string; message: string; files?: { file: string; message: string }[] };
    pins_changed: { project: string; counter: number; pin?: string | null; action?: string; by?: string | null };
    client_joined: { client: HostClient };
    client_left: { client: HostClient };
    // Play here's game started, and closed (with where the party stood, when the game wrote it).
    game_started: { project: string; run: string; map: string; world: string };
    game_exited: { project: string; run: string; map: string; world: string; code: number | null; exit: ExitPose | null };
    // A job of the project queued or running (its last line), and finished (done, failed or cancelled): its summary
    // (jobs.status gives the result). S5a5, host/src/jobs.mjs.
    job_progress: { project: string; job: Job };
    job_done: { project: string; job: Job };
}

export type NoticeName = keyof HostNotices;

type AllMethods = RpcMethods & HostMethods;
export type MethodName = RpcMethodName | keyof HostMethods;
export type ParamsOf<M extends MethodName> = AllMethods[M]['params'];
export type ResultOf<M extends MethodName> = AllMethods[M]['result'];

// A refusal or failure of a call: `kind` is the typed error's data.kind (or a transport kind of the client's own).
export class RpcCallError extends Error
{
    readonly kind: RpcErrorKind | 'disconnected' | 'transport';
    readonly code: number;
    readonly data: ErrorData | undefined;

    constructor(kind: RpcCallError['kind'], code: number, message: string, data?: ErrorData)
    {
        super(message);
        this.kind = kind;
        this.code = code;
        this.data = data;
    }
}

export type ConnectionState = 'connecting' | 'open' | 'closed';

// What the app needs of its connection to a core: the local host over WebSocket (RpcClient), or the hosted page's
// worker (hosted/client.ts, S5c). Both answer the same methods and byte routes and send the same notices.
export interface StudioClient
{
    readonly state: ConnectionState;
    readonly token: string;
    // 'local': a host on this machine serves the page; 'paired': a hosted page paired with a local host; 'hosted': the
    // core runs in the page's worker (no game, no jobs).
    readonly mode: 'local' | 'paired' | 'hosted';
    onState(listener: (state: ConnectionState) => void): () => void;
    onNotice<N extends NoticeName>(name: N, listener: (params: HostNotices[N]) => void): () => void;
    connect(): void;
    close(): void;
    call<M extends MethodName>(method: M, params: ParamsOf<M>): Promise<ResultOf<M>>;
    fetchBytes(path: string): Promise<{ bytes: ArrayBuffer; headers: Headers }>;
    // The absolute URL of a byte route (walk mode's worker fetches its files itself).
    routeUrl(path: string): string;
    // Where walk mode's worker loads the core from.
    coreUrl(): string;
    // Hosted mode: walk mode runs in the page's one worker (S5_BROWSER_EDITOR.md 2.4.3); null: its own worker.
    walkChannel(): WalkChannel | null;
}

// Walk mode's requests and their replies (walk/protocol.ts), over whichever worker runs the walk.
export interface WalkChannel
{
    send(request: WalkChannelRequest): Promise<WalkChannelReply>;
    terminate(): void;
}

export type WalkChannelRequest =
    | { type: 'load'; files: { map: string; state: string; decorations: string; terrain?: string }; token: string; coreUrl?: string }
    | { type: 'call'; method: string; params: unknown };

export interface WalkChannelReply
{
    answer: { result?: unknown; error?: { message: string; data?: { kind?: string } } };
    timing?: { coreMs?: number; fetchMs?: number; loadMs?: number; bytes?: number; callMs?: number };
}

// What the client needs of a WebSocket: the browser's, or a fake one in tests.
export interface SocketLike
{
    readyState: number;
    send(data: string): void;
    close(): void;
    onopen: ((event: unknown) => void) | null;
    onclose: ((event: unknown) => void) | null;
    onerror: ((event: unknown) => void) | null;
    onmessage: ((event: { data: unknown }) => void) | null;
}

interface Waiting
{
    resolve: (value: unknown) => void;
    reject: (error: RpcCallError) => void;
    method: string;
}

export interface RpcClientOptions
{
    url: string;
    token: string;
    // Makes the socket (tests pass a fake one). `protocols` carry the token (never the URL).
    createSocket?: (url: string, protocols: string[]) => SocketLike;
    // Where the byte routes are (a paired hosted page: the host's http://127.0.0.1:<port>); default the page's origin.
    byteBase?: string;
    // Where walk mode's worker loads the core from; default the host's /core/.
    coreUrl?: string;
    mode?: 'local' | 'paired';
    // Reconnects after this many milliseconds when the socket closes (0: never).
    reconnectMs?: number;
}

// The token as a WebSocket subprotocol (S5_BROWSER_EDITOR.md 2.12: no token in a URL): the host accepts
// `oymap.token.<the token's UTF-8 bytes in hex>` beside the plain `oymap`.
export function tokenProtocols(token: string): string[]
{
    const hex = Array.from(new TextEncoder().encode(token), (byte) => byte.toString(16).padStart(2, '0')).join('');
    return ['oymap', `oymap.token.${hex}`];
}

export class RpcClient implements StudioClient
{
    private readonly options: RpcClientOptions;
    private socket: SocketLike | null = null;
    private nextId = 1;
    private readonly waiting = new Map<number, Waiting>();
    private readonly queue: string[] = [];
    private readonly listeners = new Set<(state: ConnectionState) => void>();
    private readonly noticeListeners = new Map<string, Set<(params: unknown) => void>>();
    private stateValue: ConnectionState = 'closed';
    private stopped = false;

    constructor(options: RpcClientOptions)
    {
        this.options = options;
    }

    get state(): ConnectionState
    {
        return this.stateValue;
    }

    get token(): string
    {
        return this.options.token;
    }

    get mode(): 'local' | 'paired'
    {
        return this.options.mode ?? 'local';
    }

    routeUrl(path: string): string
    {
        return `${this.options.byteBase ?? ''}${path}`;
    }

    coreUrl(): string
    {
        return this.options.coreUrl ?? new URL('/core/oymap_worker.mjs', location.origin).href;
    }

    walkChannel(): WalkChannel | null
    {
        return null;
    }

    onState(listener: (state: ConnectionState) => void): () => void
    {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }

    // Listens to one kind of the host's notices; returns the function that stops listening.
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

    connect(): void
    {
        this.stopped = false;
        const make = this.options.createSocket ?? ((u: string, protocols: string[]) => new WebSocket(u, protocols) as unknown as SocketLike);
        const socket = make(this.options.url, tokenProtocols(this.options.token));
        this.socket = socket;
        this.setState('connecting');
        socket.onopen = () =>
        {
            this.setState('open');
            for (const message of this.queue.splice(0))
            {
                socket.send(message);
            }
        };
        socket.onmessage = (event) => this.receive(String(event.data));
        socket.onerror = () => undefined;
        socket.onclose = () =>
        {
            if (this.socket !== socket)
            {
                return;
            }
            this.socket = null;
            this.setState('closed');
            for (const entry of this.waiting.values())
            {
                entry.reject(new RpcCallError('disconnected', 0, `the host closed the connection during ${entry.method}`));
            }
            this.waiting.clear();
            const delay = this.options.reconnectMs ?? 2000;
            if (!this.stopped && delay > 0)
            {
                setTimeout(() => { if (!this.stopped && !this.socket) { this.connect(); } }, delay);
            }
        };
    }

    close(): void
    {
        this.stopped = true;
        this.socket?.close();
    }

    call<M extends MethodName>(method: M, params: ParamsOf<M>): Promise<ResultOf<M>>
    {
        const id = this.nextId++;
        const message = JSON.stringify({ jsonrpc: '2.0', id, method, params });
        return new Promise<ResultOf<M>>((resolve, reject) =>
        {
            this.waiting.set(id, { resolve: resolve as (value: unknown) => void, reject, method });
            if (this.socket && this.stateValue === 'open')
            {
                this.socket.send(message);
            }
            else if (this.socket)
            {
                this.queue.push(message);
            }
            else
            {
                this.waiting.delete(id);
                reject(new RpcCallError('disconnected', 0, `not connected to the host (${method})`));
            }
        });
    }

    // Bytes from the host's byte routes, with the token (S5_BROWSER_EDITOR.md 2.12).
    async fetchBytes(path: string): Promise<{ bytes: ArrayBuffer; headers: Headers }>
    {
        const response = await fetch(this.routeUrl(path), { headers: { Authorization: `Bearer ${this.options.token}` } });
        if (!response.ok)
        {
            throw new RpcCallError('transport', response.status, `${path}: ${response.status} ${response.statusText}`);
        }
        return { bytes: await response.arrayBuffer(), headers: response.headers };
    }

    private setState(state: ConnectionState): void
    {
        this.stateValue = state;
        for (const listener of this.listeners)
        {
            listener(state);
        }
    }

    private receive(text: string): void
    {
        let message: { id?: number | null; method?: string; params?: unknown; result?: unknown; error?: RpcError | { code: number; message: string; data?: ErrorData } };
        try
        {
            message = JSON.parse(text);
        }
        catch
        {
            return;
        }
        // A notice: a method without an id.
        if ((message.id === undefined || message.id === null) && typeof message.method === 'string')
        {
            for (const listener of this.noticeListeners.get(message.method) ?? [])
            {
                listener(message.params);
            }
            return;
        }
        if (typeof message.id !== 'number')
        {
            return;
        }
        const entry = this.waiting.get(message.id);
        if (!entry)
        {
            return;
        }
        this.waiting.delete(message.id);
        if (message.error)
        {
            const error = message.error;
            const kind = (error.data as ErrorData | undefined)?.kind ?? 'failed';
            entry.reject(new RpcCallError(kind, error.code, error.message, error.data as ErrorData | undefined));
        }
        else
        {
            entry.resolve(message.result);
        }
    }
}

// The pairing token: from the URL's fragment (#token=..., never sent in requests), then kept in session storage.
export function pairingToken(location: { hash: string }, storage: Pick<Storage, 'getItem' | 'setItem'> | null): string
{
    const fromHash = new URLSearchParams(location.hash.replace(/^#/, '')).get('token');
    if (fromHash)
    {
        storage?.setItem('oymap.token', fromHash);
        return fromHash;
    }
    return storage?.getItem('oymap.token') ?? '';
}

// The WebSocket URL of the host that served the page.
export function socketUrl(location: { protocol: string; host: string }): string
{
    return `${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/rpc`;
}

// A small revision-keyed cache of answers (layout and mesh by view revision): a new revision is a new key, so
// nothing is invalidated by hand.
export class RevisionCache<T>
{
    private readonly entries = new Map<string, T>();
    private readonly limit: number;

    constructor(limit = 8)
    {
        this.limit = limit;
    }

    get(key: string): T | undefined
    {
        const value = this.entries.get(key);
        if (value !== undefined)
        {
            this.entries.delete(key);
            this.entries.set(key, value);
        }
        return value;
    }

    set(key: string, value: T): void
    {
        this.entries.delete(key);
        this.entries.set(key, value);
        while (this.entries.size > this.limit)
        {
            this.entries.delete(this.entries.keys().next().value as string);
        }
    }
}

export function isRefusal(error: unknown, kind: string): boolean
{
    return error instanceof RpcCallError && error.kind === kind;
}
