// The hosted page's core session (S5_BROWSER_EDITOR.md 2.2 "Hosted mode", 2.4.3, 2.11; PLAN.md 9): the WebAssembly
// core with every method of the request list, without a native host. It stands where the local host stands for the
// web app: it answers the host's own methods (host.projects, host.subscribe, host.walk_prepare), adds the hosted
// capabilities to session.hello, sends the notices the host sends after a change (revision_changed, pins_changed),
// and serves the byte routes the views load (/tex, /mesh, /picture, /walk) from the asset root and the projects.
//
// File systems inside the core's module:
//   /a/root      the asset root, read-only (packfs.ts over the player's install, packages or a checkout)
//   /p/<key>     each open project, in memory (MEMFS); written back to where it came from after every call that
//                wrote (a folder the person allowed, Chromium's File System Access; or this browser's private storage,
//                OPFS) by the `Backing` the worker gives
//   /m/<key>     a build installed as a mod folder (build.install), zipped or copied into the install's mods/
//
// One worker, one core, one map at a time (2.4.3, PLAN 9): opening a project releases what the core kept of the
// others (session.release). Runs in the browser's worker (hosted.worker.ts) and under Node (tests/hosted_node.mjs).
import { addEntry, EntryReader, findEntry, isDir, mountTree, newDir } from './packfs.ts';
import type { DirEntry, EmscriptenFS, FileEntry } from './packfs.ts';
import { openInstall } from './install.ts';
import { RPC_METHODS } from '../../../schema/rpc/generated/rpc.ts';
import type { OpenedInstall, PickedFile } from './install.ts';

// What the session needs of the core's module (build-wasm*/oymap_worker.mjs).
export interface CoreModule
{
    _oymap_call(method: number, params: number): number;
    _oymap_free(text: number): void;
    _oymap_unzstd(source: number, size: number, target: number, capacity: number): number;
    _oymap_heap(fields: number): void;
    _malloc(bytes: number): number;
    _free(pointer: number): void;
    stringToNewUTF8(text: string): number;
    UTF8ToString(pointer: number): string;
    HEAPU8: Uint8Array;
    HEAPF64: Float64Array;
    FS: EmscriptenFS & MemFS;
}

interface StatLike
{
    mode: number;
    size: number;
    mtime: Date | number;
}

// The MEMFS calls the session makes.
interface MemFS
{
    mkdirTree(path: string): void;
    writeFile(path: string, data: Uint8Array | string): void;
    readFile(path: string): Uint8Array;
    readdir(path: string): string[];
    stat(path: string): StatLike;
    isDir(mode: number): boolean;
    unlink(path: string): void;
    rmdir(path: string): void;
    analyzePath(path: string): { exists: boolean };
}

export interface Answer
{
    result?: unknown;
    error?: { code: number; message: string; data?: { kind?: string; [key: string]: unknown } };
}

// Where a project's files live besides the core's memory: written after each call that changed them.
export interface Backing
{
    // 'folder': the person's own folder (File System Access, read-write); 'browser': this browser's private storage
    // (OPFS, a working copy exported as a zip); 'memory': nowhere (read-only sources: the page says to export).
    readonly kind: 'folder' | 'browser' | 'memory';
    readonly label: string;
    write(path: string, bytes: Uint8Array): Promise<void>;
    remove(path: string): Promise<void>;
}

export interface OpenedProject
{
    key: string;
    name: string;
    kind: string;
    world: string;
    backing: Backing['kind'];
    label: string;
}

export interface ProjectFile
{
    path: string;
    bytes: Uint8Array;
}

export interface BytesAnswer
{
    status: number;
    headers: Record<string, string>;
    body: Uint8Array;
}

export interface HeapNumbers
{
    // malloc's bytes in use, its arena, the module's memory (only grows), the largest arena at a call's end.
    live: number;
    arena: number;
    memory: number;
    peak: number;
}

type Notice = (method: string, params: Record<string, unknown>) => void;

// A job as the host's jobs.mjs reports it (schema/rpc/jobs.rpc.json).
interface HostedJob
{
    id: string;
    kind: string;
    title: string;
    project: string;
    revision: string;
    state: 'queued' | 'running' | 'done' | 'failed' | 'cancelled';
    background: boolean;
    params: Record<string, unknown>;
    created: string;
    started: string | null;
    finished: string | null;
    seconds: number | null;
    progress: string[];
    error: string | null;
    line: string;
    pictures: string[];
    result?: unknown;
}

// What a finished job says in one line (as host/src/jobs.mjs's resultLine).
function resultLine(kind: string, result: { findings?: { severity: string }[]; solve?: { waves: unknown[]; never_reached: unknown[] };
    coplanar?: { new: number }; score?: number; band?: { within: boolean; at_least: number } }): string
{
    if (kind === 'checks')
    {
        const counts: Record<string, number> = { error: 0, warning: 0, info: 0 };
        for (const finding of result.findings ?? [])
        {
            counts[finding.severity] = (counts[finding.severity] ?? 0) + 1;
        }
        const solve = result.solve ? `; solve ${result.solve.waves.length} steps, ${result.solve.never_reached.length} never reached` : '';
        return `${counts.error} errors, ${counts.warning} warnings; coplanar ${result.coplanar?.new ?? 0} new${solve}`;
    }
    if (kind === 'compare' && result.score !== undefined && result.band)
    {
        return `${(result.score * 100).toFixed(1)} % (${result.band.within ? 'within' : 'outside'} the band of ${result.band.at_least * 100} %)`;
    }
    return '';
}

// A cooked texture un-framed: its header, every level's blocks (largest first) and their sizes.
interface TextureBody
{
    header: Uint8Array;
    blocks: Uint8Array;
    sizes: number[];
    levels: number;
    scale: number;
}

const HEADER_BYTES = 120;
const TEXTURE_MAGIC = 0x313030584554594fn;
const BLOCK_BYTES: Record<number, number> = { 1: 16, 2: 8, 3: 16, 4: 16, 5: 8, 6: 16, 7: 8, 8: 8, 9: 16 };
const WORLDS = ['mm6', 'mm7', 'mm8', 'mm9'];
// The methods a page may call in hosted mode: the catalogue's exposed ones (as the host forwards), and walk mode's,
// which the local page calls in its own worker.
const WALK_METHODS = new Set(['walk.load', 'walk.place', 'walk.step', 'walk.replay', 'walk.toggle']);
// Methods that write the project's files (the catalogue's `writes`): followed by a write-back and the notices.
const WRITING = /^(edit\.(apply|undo|redo|revert)|project\.(record|lock_prune|new|protect|migrate|fmt|status)|pins\.(add|claim|reply|resolve|accept|reopen|decline|keep)|build\.(run|install))$/;
const SKIP_IN_PROJECT = new Set(['.oymap/view', '.oymap/jobs']);
const MESH_NAME = /^[0-9a-f]+-[0-9a-z]+-[0-9a-f]{12}\.mesh$/;
const PICTURE_PATH = /^(\.oymap\/pins\/pictures|review\/pictures)\/[A-Za-z0-9_.-]+\.(png|jpg)$/;
const WALK_FILE = /^[A-Za-z0-9_-]+\.(blv|odm|walk\.yml|walk\.terrain)$/;

const refusal = (kind: string, message: string, extra: Record<string, unknown> = {}): Answer =>
    ({ error: { code: -32000, message, data: { kind, ...extra } } });

function parentOf(path: string): string
{
    return path.slice(0, Math.max(0, path.lastIndexOf('/')));
}

export class HostedSession
{
    readonly module: CoreModule;
    readonly reader = new EntryReader();
    install: OpenedInstall | null = null;
    private readonly projects = new Map<string, { info: OpenedProject; backing: Backing; synced: Map<string, string>; revision: string | null; counter: number | null }>();
    private notice: Notice;
    private readonly textureBodies = new Map<string, TextureBody>();
    // Where the asset root is mounted (a second install mounts beside the first: the core keys its tables by path).
    private assetPath = '/a/root';
    private textureBytes = 0;
    private readonly textureBudget: number;
    // Calls answered, with the time each took in the core (for the budgets).
    readonly timings: { method: string; ms: number }[] = [];
    version = '';

    constructor(module: CoreModule, notice: Notice = () => undefined, options: { textureBudget?: number } = {})
    {
        this.module = module;
        this.notice = notice;
        this.textureBudget = options.textureBudget ?? 96 * 1024 * 1024;
        module.FS.mkdirTree('/a');
        module.FS.mkdirTree('/p');
        module.FS.mkdirTree('/m');
    }

    setNotice(notice: Notice): void
    {
        this.notice = notice;
    }

    // --- the core ----------------------------------------------------------------------------------------------

    // One call of the request list, as the native core answers it.
    callCore(method: string, params: unknown): Answer
    {
        const m = this.module;
        const methodText = m.stringToNewUTF8(method);
        const paramsText = m.stringToNewUTF8(JSON.stringify(params ?? {}));
        const started = performance.now();
        const answer = m._oymap_call(methodText, paramsText);
        const ms = performance.now() - started;
        const text = m.UTF8ToString(answer);
        m._oymap_free(answer);
        m._free(methodText);
        m._free(paramsText);
        this.timings.push({ method, ms });
        if (this.timings.length > 2000)
        {
            this.timings.splice(0, 1000);
        }
        return JSON.parse(text) as Answer;
    }

    heap(): HeapNumbers
    {
        const m = this.module;
        const at = m._malloc(32);
        m._oymap_heap(at);
        const fields = Array.from(m.HEAPF64.subarray(at / 8, at / 8 + 4));
        m._free(at);
        return { live: fields[0], arena: fields[1], memory: fields[2], peak: fields[3] };
    }

    // --- the asset root ----------------------------------------------------------------------------------------

    // Mounts what the person picked as the asset root and gives it to the core. A second install replaces the first.
    openAssets(picked: PickedFile[]): OpenedInstall
    {
        const install = openInstall(picked);
        const fs = this.module.FS;
        if (this.install)
        {
            // The old root stays mounted under a new name: the core drops its tables when the root's path changes.
            this.reader.dropCaches();
        }
        const mountpoint = this.install ? `/a/root${Date.now().toString(36)}` : '/a/root';
        mountTree(fs, install.tree, mountpoint, this.reader);
        const configured = this.callCore('session.configure', { asset_root: mountpoint });
        if (configured.error)
        {
            throw new Error(configured.error.message);
        }
        this.install = install;
        this.assetPath = mountpoint;
        this.textureBodies.clear();
        this.textureBytes = 0;
        return install;
    }

    // --- projects ----------------------------------------------------------------------------------------------

    private slug(name: string): string
    {
        const base = name.replace(/[^A-Za-z0-9_-]+/g, '_').replace(/^_+|_+$/g, '') || 'project';
        let key = base;
        for (let n = 2; this.projects.has(key) || this.module.FS.analyzePath(`/p/${key}`).exists; ++n)
        {
            key = `${base}_${n}`;
        }
        return key;
    }

    folderOf(key: string): string | null
    {
        return this.projects.has(key) ? `/p/${key}` : null;
    }

    list(): OpenedProject[]
    {
        return [...this.projects.values()].map((entry) => entry.info);
    }

    // Puts a project's files into memory and opens it; the others are released (one map at a time).
    openProject(name: string, files: ProjectFile[], backing: Backing): OpenedProject
    {
        // A picked folder may hold the project one level down (the person picked its parent).
        const top = files.some((file) => file.path === 'project.yml') ? '' : (() =>
        {
            const found = files.find((file) => /^[^/]+\/project\.yml$/.test(file.path));
            return found ? found.path.slice(0, found.path.indexOf('/') + 1) : null;
        })();
        if (top === null)
        {
            throw new Error('not a studio project: no project.yml in what was picked (pick the project\'s own folder)');
        }
        const key = this.slug(name);
        const folder = `/p/${key}`;
        const fs = this.module.FS;
        fs.mkdirTree(folder);
        for (const file of files)
        {
            if (!file.path.startsWith(top))
            {
                continue;
            }
            const relative = file.path.slice(top.length);
            if (!relative || relative.split('/').some((part) => part === '..' || part === '.'))
            {
                continue;
            }
            fs.mkdirTree(parentOf(`${folder}/${relative}`));
            fs.writeFile(`${folder}/${relative}`, file.bytes);
        }
        const opened = this.callCore('project.open', { project: folder });
        if (opened.error)
        {
            this.removeTree(folder);
            throw new Error(opened.error.message);
        }
        const card = (opened.result as { files?: Record<string, { tree?: Record<string, unknown> }> }).files?.['project.yml']?.tree ?? {};
        const info: OpenedProject = {
            key, name: String(card.name ?? name), kind: String(card.kind ?? (files.some((file) => file.path.endsWith('sketch.yml')) ? 'outdoor' : 'indoor')),
            world: String(card.world ?? 'mm6'), backing: backing.kind, label: backing.label,
        };
        this.releaseOthers(key);
        this.projects.set(key, { info, backing, synced: this.snapshot(folder), revision: null, counter: null });
        return info;
    }

    // A shipped map as an overlay project (F3 "change a shipped map"; project.import), made in memory and written to
    // its backing.
    async importMap(map: string, world: string, backing: Backing): Promise<OpenedProject>
    {
        const key = this.slug(`${world}_${map.replace(/\.(blv|odm)$/i, '')}`);
        const folder = `/p/${key}`;
        const made = this.callCore('project.import', { project: folder, map, world });
        if (made.error)
        {
            this.removeTree(folder);
            throw new Error(made.error.message);
        }
        const info: OpenedProject = { key, name: `${map} (overlay)`, kind: 'overlay', world, backing: backing.kind, label: backing.label };
        this.releaseOthers(key);
        this.projects.set(key, { info, backing, synced: new Map(), revision: null, counter: null });
        await this.writeBack(key);
        return info;
    }

    // A new project made by the core (project.new) in memory, then written to its backing.
    async newProject(params: Record<string, unknown>, backing: Backing): Promise<OpenedProject>
    {
        const key = this.slug(String(params.folder ?? params.id ?? 'project'));
        const folder = `/p/${key}`;
        const { root: unusedRoot, folder: unusedFolder, ...rest } = params;
        void unusedRoot;
        void unusedFolder;
        const made = this.callCore('project.new', { ...rest, project: folder });
        if (made.error)
        {
            this.removeTree(folder);
            throw new Error(made.error.message);
        }
        const info: OpenedProject = { key, name: String(params.name ?? key), kind: String(params.kind ?? 'indoor'),
            world: String(params.world ?? 'mm6'), backing: backing.kind, label: backing.label };
        this.releaseOthers(key);
        this.projects.set(key, { info, backing, synced: new Map(), revision: null, counter: null });
        await this.writeBack(key);
        return info;
    }

    close(key: string): void
    {
        if (!this.projects.has(key))
        {
            return;
        }
        this.callCore('session.release', { project: `/p/${key}` });
        this.projects.delete(key);
        this.removeTree(`/p/${key}`);
    }

    private releaseOthers(key: string): void
    {
        for (const other of this.projects.keys())
        {
            if (other !== key)
            {
                this.callCore('session.release', { project: `/p/${other}` });
            }
        }
    }

    private removeTree(path: string): void
    {
        const fs = this.module.FS;
        if (!fs.analyzePath(path).exists)
        {
            return;
        }
        for (const name of fs.readdir(path))
        {
            if (name === '.' || name === '..')
            {
                continue;
            }
            const child = `${path}/${name}`;
            if (fs.isDir(fs.stat(child).mode))
            {
                this.removeTree(child);
            }
            else
            {
                fs.unlink(child);
            }
        }
        fs.rmdir(path);
    }

    // Every file of a folder in memory: relative path -> its modification time and size.
    private snapshot(folder: string, prefix = '', into = new Map<string, string>()): Map<string, string>
    {
        const fs = this.module.FS;
        for (const name of fs.readdir(prefix ? `${folder}/${prefix}` : folder))
        {
            if (name === '.' || name === '..')
            {
                continue;
            }
            const relative = prefix ? `${prefix}/${name}` : name;
            if (SKIP_IN_PROJECT.has(relative))
            {
                continue;
            }
            const stat = fs.stat(`${folder}/${relative}`);
            if (fs.isDir(stat.mode))
            {
                this.snapshot(folder, relative, into);
            }
            else
            {
                into.set(relative, `${stat.mtime instanceof Date ? stat.mtime.getTime() : Number(stat.mtime)}:${stat.size}`);
            }
        }
        return into;
    }

    // Writes what changed in memory since the last write-back to the project's backing: new and changed files
    // (by modification time and size) and removed ones. Returns the paths written.
    async writeBack(key: string): Promise<string[]>
    {
        const entry = this.projects.get(key);
        if (!entry || entry.backing.kind === 'memory')
        {
            if (entry)
            {
                entry.synced = this.snapshot(`/p/${key}`);
            }
            return [];
        }
        const folder = `/p/${key}`;
        const now = this.snapshot(folder);
        const written: string[] = [];
        for (const [path, stamp] of now)
        {
            if (entry.synced.get(path) !== stamp)
            {
                await entry.backing.write(path, this.module.FS.readFile(`${folder}/${path}`));
                written.push(path);
            }
        }
        for (const path of entry.synced.keys())
        {
            if (!now.has(path))
            {
                await entry.backing.remove(path);
                written.push(`-${path}`);
            }
        }
        entry.synced = now;
        return written;
    }

    // The project's files (for a zip): the sources and review/ (without build/ and .oymap/), or its build/.
    files(key: string, what: 'project' | 'build' | 'mod'): ProjectFile[]
    {
        const root = what === 'mod' ? `/m/${key}` : `/p/${key}`;
        const fs = this.module.FS;
        const out: ProjectFile[] = [];
        const walk = (relative: string) =>
        {
            const path = relative ? `${root}/${relative}` : root;
            if (!fs.analyzePath(path).exists)
            {
                return;
            }
            for (const name of fs.readdir(path))
            {
                if (name === '.' || name === '..')
                {
                    continue;
                }
                const child = relative ? `${relative}/${name}` : name;
                if (what === 'project' && !relative && (name === 'build' || name === '.oymap'))
                {
                    continue;
                }
                if (fs.isDir(fs.stat(`${root}/${child}`).mode))
                {
                    walk(child);
                }
                else
                {
                    out.push({ path: child, bytes: fs.readFile(`${root}/${child}`) });
                }
            }
        };
        walk(what === 'build' ? 'build' : '');
        return what === 'build' ? out.map((file) => ({ ...file, path: file.path.slice('build/'.length) })) : out;
    }

    // The build installed as a mod folder (build.install into /m/<key>): what goes into an install's mods/.
    installMod(key: string): Answer
    {
        const folder = this.folderOf(key);
        if (!folder)
        {
            return refusal('not_a_project', `no project ${key} is open`);
        }
        this.removeTree(`/m/${key}`);
        this.module.FS.mkdirTree(`/m/${key}`);
        const configured = this.callCore('session.configure', { asset_root: this.assetPath, mount: `/m/${key}` });
        if (configured.error)
        {
            return configured;
        }
        const answer = this.callCore('build.install', { project: folder });
        this.callCore('session.configure', { asset_root: this.assetPath });
        return answer;
    }

    // --- the request list, as the host answers it --------------------------------------------------------------

    private mapParams(params: Record<string, unknown>): { ok: true; params: Record<string, unknown> } | { ok: false; answer: Answer }
    {
        const mapped: Record<string, unknown> = { ...params };
        if (typeof mapped.project === 'string')
        {
            const folder = this.folderOf(mapped.project);
            if (!folder)
            {
                const what = `no project ${JSON.stringify(mapped.project)} is open in this page`;
                return { ok: false, answer: refusal('not_a_project', what, { issues: [{ severity: 'error', code: 'project', file: '', path: '', message: what }] }) };
            }
            mapped.project = folder;
        }
        if (Array.isArray(mapped.projects))
        {
            mapped.projects = mapped.projects.map((key) => this.folderOf(String(key)) ?? String(key));
        }
        if ('inbox' in mapped)
        {
            return { ok: false, answer: refusal('bad_request', 'the hosted page has no pins inbox (the game writes it on the person\'s machine: pair with a local studio)') };
        }
        return { ok: true, params: mapped };
    }

    async call(method: string, params: Record<string, unknown> = {}): Promise<Answer>
    {
        switch (method)
        {
        case 'host.projects':
            return { result: { projects: this.list().map((project) => ({ ...project, label: project.label })), roots: [] } };
        case 'host.clients':
            return { result: { clients: [] } };
        case 'host.subscribe':
            return this.subscribe(params.project === null || params.project === undefined ? null : String(params.project));
        case 'host.walk_prepare':
            return this.walkPrepare(String(params.project ?? ''));
        case 'game.play_here':
        case 'game.playtest':
            return refusal('bad_request', 'the hosted page cannot start the game: build the map and install it into the '
                + 'game\'s mods folder (Install), or pair with a local studio (oymap studio) for Play here');
        case 'jobs.list':
        case 'jobs.start':
        case 'jobs.status':
        case 'jobs.cancel':
            return this.jobsAnswer(method, params);
        default:
            break;
        }
        const allowed = this.exposed(method) || WALK_METHODS.has(method);
        if (!allowed)
        {
            return { error: { code: -32601, message: `unknown method '${method}'`, data: { kind: 'unknown_method' } } };
        }
        const mapped = this.mapParams(params);
        if (!mapped.ok)
        {
            return mapped.answer;
        }
        const answer = this.callCore(method, mapped.params);
        if (method === 'session.hello' && answer.result)
        {
            (answer.result as Record<string, unknown>).host = { mode: 'hosted', game: false, assets: this.install !== null,
                version: this.version, jobs: false, python: false };
        }
        const key = typeof params.project === 'string' ? params.project : null;
        if (key && WRITING.test(method) && !answer.error)
        {
            await this.afterWrite(key, method, params, answer);
        }
        return answer;
    }

    // The catalogue's methods a browser may call (as the host forwards: `exposed`).
    private exposed(method: string): boolean
    {
        const entry = (RPC_METHODS as Record<string, { exposed: boolean; backends: readonly string[] }>)[method];
        return entry !== undefined && entry.exposed && entry.backends.includes('wasm');
    }

    private subscribe(key: string | null): Answer
    {
        if (key === null)
        {
            return { result: { revision: null, counter: null, clients: [] } };
        }
        const folder = this.folderOf(key);
        if (!folder)
        {
            return refusal('not_a_project', `no project ${key} is open in this page`);
        }
        this.releaseOthers(key);
        const status = this.callCore('project.status', { project: folder });
        const pins = this.callCore('pins.list', { project: folder });
        const entry = this.projects.get(key)!;
        entry.revision = (status.result as { revision?: string } | undefined)?.revision ?? null;
        entry.counter = (pins.result as { counter?: number } | undefined)?.counter ?? null;
        return { result: { revision: entry.revision, counter: entry.counter, unreadable: status.error?.message ?? null, clients: [] } };
    }

    // As the host's afterWrite: the change announced at once (the page's own edits included, as in local mode), and
    // the files written back.
    private async afterWrite(key: string, method: string, params: Record<string, unknown>, answer: Answer): Promise<void>
    {
        const entry = this.projects.get(key);
        if (!entry)
        {
            return;
        }
        await this.writeBack(key);
        const folder = `/p/${key}`;
        if (method.startsWith('pins.'))
        {
            const counter = (answer.result as { counter?: number }).counter ?? null;
            if (counter !== entry.counter)
            {
                entry.counter = counter;
                this.notice('pins_changed', { project: key, counter, pin: (answer.result as { pin?: { id?: string } }).pin?.id ?? null,
                    action: method.slice('pins.'.length), by: params.by ?? params.author ?? null });
            }
            return;
        }
        if (method === 'edit.apply')
        {
            const result = answer.result as { applied?: boolean; revision_after?: string; changes?: string[] };
            if (result.applied && result.revision_after !== entry.revision)
            {
                const previous = entry.revision;
                entry.revision = result.revision_after ?? null;
                this.notice('revision_changed', { project: key, revision: result.revision_after, previous,
                    author: params.author ?? 'agent', label: params.label ?? '', changes: result.changes ?? [], entry: null });
            }
            return;
        }
        if (method === 'project.status' || method.startsWith('build.'))
        {
            return;
        }
        const status = this.callCore('project.status', { project: folder });
        const revision = (status.result as { revision?: string } | undefined)?.revision ?? null;
        if (revision && revision !== entry.revision)
        {
            const previous = entry.revision;
            entry.revision = revision;
            const history = this.callCore('edit.history', { project: folder, limit: 1 });
            const last = (history.result as { entries?: { revision_after: string; author: string; label?: string; changes: string[]; sequence: number }[] } | undefined)?.entries?.at(-1);
            const fromEntry = last && last.revision_after === revision;
            this.notice('revision_changed', { project: key, revision, previous, author: fromEntry ? last.author : 'outside',
                label: fromEntry ? last.label ?? '' : '', changes: fromEntry ? last.changes : [], entry: fromEntry ? last.sequence : null });
        }
    }

    // --- jobs: the core's checks on request (2.4.3: one worker, so no background checks; edits wait meanwhile) ----

    private readonly jobs = new Map<string, HostedJob>();

    private jobsAnswer(method: string, params: Record<string, unknown>): Answer
    {
        const key = typeof params.project === 'string' ? params.project : '';
        const folder = this.folderOf(key);
        if (!folder)
        {
            return refusal('not_a_project', `no project ${JSON.stringify(key)} is open in this page`);
        }
        const summary = (job: HostedJob) =>
        {
            const { result, ...rest } = job;
            return { ...rest, has_result: result !== undefined && result !== null };
        };
        if (method === 'jobs.list')
        {
            return { result: { jobs: [...this.jobs.values()].filter((job) => job.project === key).reverse().map(summary) } };
        }
        if (method === 'jobs.status' || method === 'jobs.cancel')
        {
            const job = this.jobs.get(String(params.job ?? ''));
            if (!job || job.project !== key)
            {
                return refusal('no_such_object', `no job ${String(params.job)} of the project`);
            }
            // A job runs to its end in the one core: there is nothing to stop.
            return { result: { job: method === 'jobs.status' ? job : summary(job) } };
        }
        const kind = String(params.kind ?? '');
        if (kind !== 'checks' && kind !== 'compare')
        {
            return refusal('bad_request', `${kind} runs the game or a Python check: it needs the studio on your computer (pair with oymap studio)`);
        }
        const status = this.callCore('project.status', { project: folder });
        const revision = (status.result as { revision?: string } | undefined)?.revision ?? '';
        const id = `j${Date.now().toString(36)}-${Math.floor(Math.random() * 0xffffff).toString(16).padStart(6, '0')}`;
        const given = (params.params ?? {}) as Record<string, unknown>;
        const job: HostedJob = { id, kind, title: kind === 'checks' ? 'Audit, reach and solve' : 'Compare with the original', project: key,
            revision, state: 'queued', background: false, params: given, created: new Date().toISOString(), started: null, finished: null,
            seconds: null, progress: [], error: null, line: '', pictures: [] };
        this.jobs.set(id, job);
        this.notice('job_progress', { project: key, job: summary(job) });
        // After this answer: the worker runs it before the next message.
        setTimeout(() =>
        {
            job.state = 'running';
            job.started = new Date().toISOString();
            this.notice('job_progress', { project: key, job: summary(job) });
            const started = performance.now();
            const card = this.projects.get(key)?.info;
            const answer = kind === 'checks'
                ? this.callCore('check.audit', { map: folder, reach: true, solve: card?.kind !== 'outdoor' })
                : this.callCore('compare.run', { map: folder, ...(typeof given.original === 'string' ? { original: given.original } : {}) });
            job.seconds = Math.round(performance.now() - started) / 1000;
            job.finished = new Date().toISOString();
            if (answer.error)
            {
                job.state = 'failed';
                job.error = answer.error.message;
            }
            else
            {
                job.state = 'done';
                job.result = answer.result;
                job.line = resultLine(kind, answer.result as Record<string, never>);
            }
            this.notice('job_done', { project: key, job: summary(job) });
        }, 0);
        return { result: { job: summary(job) } };
    }

    // Walk mode: the project built (into its build/), and the routes of what walk.load reads.
    private async walkPrepare(key: string): Promise<Answer>
    {
        const folder = this.folderOf(key);
        if (!folder)
        {
            return refusal('not_a_project', `no project ${key} is open in this page`);
        }
        const built = this.callCore('build.run', { project: folder, dry_run: false });
        if (built.error)
        {
            return built;
        }
        await this.writeBack(key);
        const { kind, map, files } = built.result as { kind: string; map: string; files: string[] };
        if (kind === 'overlay')
        {
            return refusal('bad_request', 'an overlay project changes a shipped map: walk mode walks new maps only');
        }
        const stem = map.replace(/\.(blv|odm)$/, '');
        if (!files.includes(`${stem}.walk.yml`))
        {
            return refusal('bad_request', 'the build wrote no movement state for walk mode (an outdoor map needs the asset root to read its tile tables)');
        }
        const route = (name: string) => `/walk/${encodeURIComponent(key)}/${encodeURIComponent(name)}`;
        return { result: { kind, map, files: { map: route(map), state: route(`${stem}.walk.yml`),
            ...(kind === 'outdoor' ? { terrain: route(`${stem}.walk.terrain`) } : {}), decorations: route('decoration_data.txt') } } };
    }

    // walk.load with the routes walkPrepare named: the files are in this module's file system already.
    walkLoad(files: { map: string; state: string; decorations: string; terrain?: string }): Answer
    {
        const path = (route: string): string | null =>
        {
            const match = /^\/walk\/([^/]+)\/([^/]+)$/.exec(route);
            if (!match)
            {
                return null;
            }
            const key = decodeURIComponent(match[1]);
            const name = decodeURIComponent(match[2]);
            if (name === 'decoration_data.txt' || name === 'house_data.txt')
            {
                return `${this.assetPath}/engine/data_tables/${name}`;
            }
            const folder = this.folderOf(key);
            return folder && WALK_FILE.test(name) ? `${folder}/build/${name}` : null;
        };
        const map = path(files.map);
        const state = path(files.state);
        const decorations = path(files.decorations);
        const terrain = files.terrain ? path(files.terrain) : null;
        if (!map || !state || !decorations || (files.terrain && !terrain))
        {
            return refusal('bad_request', 'walk mode\'s files are not this page\'s');
        }
        return this.callCore('walk.load', { map, state, decorations, ...(terrain ? { terrain } : {}) });
    }

    // --- byte routes ---------------------------------------------------------------------------------------------

    bytes(route: string): BytesAnswer
    {
        const notFound = (body: string): BytesAnswer => ({ status: 404, headers: {}, body: new TextEncoder().encode(body) });
        const url = new URL(route, 'http://hosted.invalid');
        const fs = this.module.FS;
        let match: RegExpExecArray | null;
        try
        {
            if ((match = /^\/tex\/([^/]+)\/([^/]+)$/.exec(url.pathname)))
            {
                const from = url.searchParams.has('from') ? Number(url.searchParams.get('from')) : 0;
                return this.texture(decodeURIComponent(match[1]), decodeURIComponent(match[2]).toLowerCase(), Number.isInteger(from) && from >= 0 ? from : 0);
            }
            if ((match = /^\/mesh\/([^/]+)\/([^/]+)$/.exec(url.pathname)))
            {
                const folder = this.folderOf(decodeURIComponent(match[1]));
                const name = decodeURIComponent(match[2]);
                if (!folder || !MESH_NAME.test(name) || !fs.analyzePath(`${folder}/.oymap/view/${name}`).exists)
                {
                    return notFound('no such mesh');
                }
                return { status: 200, headers: { 'Content-Type': 'application/octet-stream' }, body: fs.readFile(`${folder}/.oymap/view/${name}`) };
            }
            if ((match = /^\/picture\/([^/]+)\/([^/]+)$/.exec(url.pathname)))
            {
                const folder = this.folderOf(decodeURIComponent(match[1]));
                const relative = decodeURIComponent(match[2]);
                if (!folder || !PICTURE_PATH.test(relative) || !fs.analyzePath(`${folder}/${relative}`).exists)
                {
                    return notFound('no such picture');
                }
                return { status: 200, headers: { 'Content-Type': relative.endsWith('.png') ? 'image/png' : 'image/jpeg' }, body: fs.readFile(`${folder}/${relative}`) };
            }
            if ((match = /^\/walk\/([^/]+)\/([^/]+)$/.exec(url.pathname)))
            {
                const key = decodeURIComponent(match[1]);
                const name = decodeURIComponent(match[2]);
                if ((name === 'decoration_data.txt' || name === 'house_data.txt') && this.install)
                {
                    const entry = findEntry(this.install.tree, `engine/data_tables/${name}`);
                    return entry && !isDir(entry) ? { status: 200, headers: {}, body: this.reader.readAll(entry).slice() } : notFound('no such table');
                }
                const folder = this.folderOf(key);
                if (!folder || !WALK_FILE.test(name) || !fs.analyzePath(`${folder}/build/${name}`).exists)
                {
                    return notFound('no such walk file');
                }
                return { status: 200, headers: {}, body: fs.readFile(`${folder}/build/${name}`) };
            }
        }
        catch (error)
        {
            return { status: 500, headers: {}, body: new TextEncoder().encode(error instanceof Error ? error.message : String(error)) };
        }
        return notFound('not found (the hosted page has no jobs)');
    }

    // A cooked texture as the host's /tex answers it (host/src/textures.mjs): its header and the un-framed blocks
    // of the levels from `from` down, found in the same folders in the same order; un-framed by the core's zstd.
    private texture(world: string, name: string, from: number): BytesAnswer
    {
        if (!/^mm[0-9]$/.test(world) || !/^[a-z0-9_\-.]+$/.test(name) || name.includes('..') || !this.install)
        {
            return { status: 404, headers: {}, body: new TextEncoder().encode('no texture of that name') };
        }
        let body = this.textureBodies.get(`${world}/${name}`);
        if (!body)
        {
            const found = this.findTexture(world, name);
            if (!found)
            {
                return { status: 404, headers: {}, body: new TextEncoder().encode('no texture of that name') };
            }
            body = { ...this.unframe(this.reader.readAll(found.entry)), scale: found.scale };
            this.textureBodies.set(`${world}/${name}`, body);
            this.textureBytes += body.blocks.length + HEADER_BYTES;
            for (const [key, old] of this.textureBodies)
            {
                if (this.textureBytes <= this.textureBudget || key === `${world}/${name}`)
                {
                    break;
                }
                this.textureBodies.delete(key);
                this.textureBytes -= old.blocks.length + HEADER_BYTES;
            }
        }
        else
        {
            this.textureBodies.delete(`${world}/${name}`);
            this.textureBodies.set(`${world}/${name}`, body);
        }
        const scale = body.scale;
        const level = Math.max(0, Math.min(from, body.levels - 1));
        const skip = body.sizes.slice(0, level).reduce((sum, size) => sum + size, 0);
        const out = new Uint8Array(HEADER_BYTES + body.blocks.length - skip);
        out.set(body.header, 0);
        out.set(body.blocks.subarray(skip), HEADER_BYTES);
        return {
            status: 200,
            headers: { 'Content-Type': 'application/octet-stream', 'X-Texture-Scale': String(scale), 'X-Texture-From': String(level),
                'X-Texture-Levels': String(body.levels) },
            body: out,
        };
    }

    private findTexture(world: string, name: string): { entry: FileEntry; scale: number } | null
    {
        const tree = this.install!.tree;
        for (const each of [world, ...WORLDS.filter((other) => other !== world)])
        {
            for (const [folder, scale] of [[`worlds/${each}/textures_x4`, 4], [`worlds/${each}/textures`, 1]] as const)
            {
                const entry = findEntry(tree, `${folder}/${name}.oytex`);
                if (entry && !isDir(entry))
                {
                    return { entry, scale };
                }
            }
        }
        for (const [folder, scale] of [['engine/textures_x4', 4], ['engine/textures', 1]] as const)
        {
            const entry = findEntry(tree, `${folder}/${name}.oytex`);
            if (entry && !isDir(entry))
            {
                return { entry, scale };
            }
        }
        return null;
    }

    private unframe(bytes: Uint8Array): Omit<TextureBody, 'scale'>
    {
        if (bytes.length < HEADER_BYTES)
        {
            throw new Error('not a cooked texture (too short)');
        }
        const view = new DataView(bytes.buffer, bytes.byteOffset, HEADER_BYTES);
        const field = (index: number) => view.getBigUint64(index * 8, true);
        if (field(0) !== TEXTURE_MAGIC || Number(field(1)) !== 3)
        {
            throw new Error('not a cooked texture of version 3');
        }
        const codec = Number(field(2));
        const width = Number(field(5));
        const height = Number(field(6));
        const levels = Number(field(7));
        const blockBytes = Number(field(9));
        const zstdBytes = Number(field(11));
        const block = BLOCK_BYTES[codec];
        if (!block)
        {
            throw new Error(`unknown texture codec ${codec}`);
        }
        const sizes: number[] = [];
        for (let level = 0; level < levels; ++level)
        {
            sizes.push(Math.ceil(Math.max(1, width >> level) / 4) * Math.ceil(Math.max(1, height >> level) / 4) * block);
        }
        const m = this.module;
        const source = m._malloc(zstdBytes);
        const target = m._malloc(blockBytes);
        try
        {
            m.HEAPU8.set(bytes.subarray(HEADER_BYTES, HEADER_BYTES + zstdBytes), source);
            const written = m._oymap_unzstd(source, zstdBytes, target, blockBytes);
            if (written !== blockBytes)
            {
                throw new Error(`a texture's blocks did not un-frame (${written} of ${blockBytes} bytes)`);
            }
            return { header: bytes.slice(0, HEADER_BYTES), blocks: m.HEAPU8.slice(target, target + blockBytes), sizes, levels };
        }
        finally
        {
            m._free(source);
            m._free(target);
        }
    }

    textureCache(): { textures: number; bytes: number }
    {
        return { textures: this.textureBodies.size, bytes: this.textureBytes };
    }
}

// The files of a folder picked as a project that the hosted page reads: everything but the build and the caches
// the core makes again (meshes, jobs).
export function projectFileWanted(path: string): boolean
{
    return !/^(build|\.oymap\/view|\.oymap\/jobs)(\/|$)/.test(path);
}

export { addEntry, newDir };
export type { DirEntry };
