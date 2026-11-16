// The hosted page's worker (S5_BROWSER_EDITOR.md 2.2 "Hosted mode", 2.4.3 "one worker"): the WebAssembly core with
// the request list, the asset root over the person's install (read by byte range with FileReaderSync), and the open
// projects, written back after each change to the folder the person allowed (File System Access) or to this
// browser's private storage (OPFS). All logic is in session.ts; this file turns messages into its calls and gives it
// the browser's files.
import { unzipSync, zipSync } from 'three/examples/jsm/libs/fflate.module.js';
import { HostedSession, projectFileWanted } from './session.ts';
import type { Backing, CoreModule, ProjectFile } from './session.ts';
import type { ByteSource } from './packfs.ts';
import type { PickedFile } from './install.ts';
import type { HostedNotice, HostedReply, HostedRequest, Picked, ProjectPlace } from './protocol.ts';

const scope = self as unknown as {
    postMessage(message: HostedReply | HostedNotice, transfer?: Transferable[]): void;
    onmessage: ((event: MessageEvent<HostedRequest>) => void) | null;
};

// Workers' synchronous file reader (the app's TypeScript library is the DOM's, which lacks it).
declare const FileReaderSync: { new(): { readAsArrayBuffer(blob: Blob): ArrayBuffer } };

let session: HostedSession | null = null;
let reader: { readAsArrayBuffer(blob: Blob): ArrayBuffer } | null = null;

function fileSource(file: File): ByteSource
{
    reader ??= new FileReaderSync();
    return {
        size: file.size,
        mtime: file.lastModified,
        read: (offset: number, length: number) => new Uint8Array(reader!.readAsArrayBuffer(file.slice(offset, offset + length))),
    };
}

// Every file under a directory handle, with its path inside it.
async function walkHandle(handle: FileSystemDirectoryHandle, wanted: (path: string) => boolean = () => true, prefix = '',
    out: { path: string; file: File }[] = []): Promise<{ path: string; file: File }[]>
{
    const entries = handle as unknown as AsyncIterable<[string, FileSystemHandle]> & { entries(): AsyncIterable<[string, FileSystemHandle]> };
    for await (const [name, child] of entries.entries())
    {
        const path = prefix ? `${prefix}/${name}` : name;
        if (!wanted(path))
        {
            continue;
        }
        if (child.kind === 'directory')
        {
            await walkHandle(child as FileSystemDirectoryHandle, wanted, path, out);
        }
        else
        {
            out.push({ path, file: await (child as FileSystemFileHandle).getFile() });
        }
    }
    return out;
}

async function pickedFiles(picked: Picked, wanted?: (path: string) => boolean): Promise<{ path: string; file: File }[]>
{
    return picked.kind === 'handle' ? walkHandle(picked.handle, wanted) : picked.files.filter((file) => !wanted || wanted(file.path));
}

// A backing over a directory handle: the person's folder, or a folder of this browser's private storage.
function handleBacking(root: FileSystemDirectoryHandle, kind: 'folder' | 'browser', label: string): Backing
{
    const folderOf = async (path: string, create: boolean) =>
    {
        let dir = root;
        for (const part of path.split('/').slice(0, -1))
        {
            dir = await dir.getDirectoryHandle(part, { create });
        }
        return dir;
    };
    return {
        kind, label,
        async write(path: string, bytes: Uint8Array)
        {
            const dir = await folderOf(path, true);
            const handle = await dir.getFileHandle(path.split('/').at(-1)!, { create: true });
            const writable = (handle as unknown as { createWritable?: () => Promise<FileSystemWritableFileStream> }).createWritable;
            if (writable)
            {
                const stream = await writable.call(handle);
                await stream.write(bytes as unknown as BufferSource);
                await stream.close();
                return;
            }
            // OPFS in a worker where streams are missing: a synchronous access handle.
            const access = await (handle as unknown as { createSyncAccessHandle(): Promise<{ truncate(n: number): void; write(b: Uint8Array, o: { at: number }): number; flush(): void; close(): void }> }).createSyncAccessHandle();
            access.truncate(0);
            access.write(bytes, { at: 0 });
            access.flush();
            access.close();
        },
        async remove(path: string)
        {
            try
            {
                const dir = await folderOf(path, false);
                await dir.removeEntry(path.split('/').at(-1)!);
            }
            catch
            {
                // gone already
            }
        },
    };
}

const memoryBacking: Backing = {
    kind: 'memory', label: 'in this page only (read-only folder: export a zip to keep changes)',
    write: async () => undefined, remove: async () => undefined,
};

async function browserFolder(name: string, create: boolean): Promise<FileSystemDirectoryHandle>
{
    const root = await navigator.storage.getDirectory();
    const projects = await root.getDirectoryHandle('projects', { create: true });
    return projects.getDirectoryHandle(name, { create });
}

async function readProjectFiles(list: { path: string; file: File }[]): Promise<ProjectFile[]>
{
    return Promise.all(list.filter((entry) => projectFileWanted(entry.path))
        .map(async (entry) => ({ path: entry.path, bytes: new Uint8Array(await entry.file.arrayBuffer()) })));
}

// A picked folder's files may all start with the folder's own name (webkitRelativePath): take it off.
function withoutTop(list: { path: string; file: File }[]): { path: string; file: File }[]
{
    const first = list[0]?.path.split('/')[0];
    if (first && list.every((entry) => entry.path.startsWith(`${first}/`)) && !list.some((entry) => entry.path === 'project.yml'))
    {
        return list.map((entry) => ({ ...entry, path: entry.path.slice(first.length + 1) }));
    }
    return list;
}

async function handle(request: HostedRequest): Promise<{ value: unknown; transfer?: Transferable[]; timing?: Record<string, number> }>
{
    if (request.type === 'init')
    {
        const started = performance.now();
        const module = await import(/* @vite-ignore */ request.coreUrl) as { default: (options?: object) => Promise<CoreModule> };
        const core = await module.default({ print: () => undefined, printErr: () => undefined });
        session = new HostedSession(core, (method, params) => scope.postMessage({ type: 'notice', method, params }));
        session.version = request.version;
        return { value: { ms: performance.now() - started } };
    }
    if (!session)
    {
        throw new Error('the core is not loaded');
    }
    switch (request.type)
    {
    case 'open_assets':
    {
        const started = performance.now();
        const list = await pickedFiles(request.picked);
        const listed = performance.now();
        const picked: PickedFile[] = withoutTop(list).map((entry) => ({ path: entry.path, source: fileSource(entry.file) }));
        const install = session.openAssets(picked);
        return { value: { kind: install.kind, release: install.release, packages: install.packages, entries: install.entries,
            worlds: install.worlds, bytes: install.bytes, ms: performance.now() - started },
        timing: { listMs: listed - started, mountMs: performance.now() - listed } };
    }
    case 'open_project':
    {
        const started = performance.now();
        let files: ProjectFile[];
        let backing: Backing = memoryBacking;
        const source = request.picked;
        if (source.kind === 'zip')
        {
            const unzipped = unzipSync(new Uint8Array(await source.file.arrayBuffer()));
            files = Object.entries(unzipped).filter(([path]) => !path.endsWith('/') && projectFileWanted(path)).map(([path, bytes]) => ({ path, bytes }));
            const top = files.find((file) => /^[^/]+\/project\.yml$/.test(file.path)) && !files.some((file) => file.path === 'project.yml');
            if (top)
            {
                const first = files[0].path.split('/')[0];
                files = files.map((file) => ({ ...file, path: file.path.startsWith(`${first}/`) ? file.path.slice(first.length + 1) : file.path }));
            }
        }
        else if (source.kind === 'browser')
        {
            const handle = await browserFolder(source.name, false);
            files = await readProjectFiles(await walkHandle(handle, projectFileWanted));
            backing = handleBacking(handle, 'browser', 'a working copy in this browser (export a zip to share it)');
        }
        else
        {
            files = await readProjectFiles(source.kind === 'handle' ? await walkHandle(source.handle, projectFileWanted) : withoutTop(source.files));
            if (source.kind === 'handle' && source.writable)
            {
                backing = handleBacking(source.handle, 'folder', `your folder ${source.handle.name} (saved after every change)`);
            }
        }
        const read = performance.now();
        // A read-only source becomes a working copy in this browser when asked (Firefox, Safari, a zip).
        if (request.place === 'browser' && backing.kind === 'memory')
        {
            const name = request.name.replace(/[^A-Za-z0-9_-]+/g, '_') || 'project';
            const handle = await browserFolder(name, true);
            backing = handleBacking(handle, 'browser', 'a working copy in this browser (export a zip to share it)');
            for (const file of files)
            {
                await backing.write(file.path, file.bytes);
            }
        }
        const opened = session.openProject(request.name, files, backing);
        return { value: opened, timing: { readMs: read - started, openMs: performance.now() - read, files: files.length } };
    }
    case 'new_project':
    case 'import_map':
    {
        let backing: Backing = memoryBacking;
        const place: ProjectPlace = request.place;
        if (place.kind === 'folder')
        {
            backing = handleBacking(place.handle, 'folder', `your folder ${place.handle.name} (saved after every change)`);
        }
        else if (place.kind === 'browser')
        {
            backing = handleBacking(await browserFolder(place.name, true), 'browser', 'a working copy in this browser (export a zip to share it)');
        }
        const started = performance.now();
        const made = request.type === 'import_map' ? await session.importMap(request.map, request.world, backing)
            : await session.newProject(request.params, backing);
        return { value: made, timing: { ms: performance.now() - started } };
    }
    case 'browser_projects':
    {
        try
        {
            const root = await navigator.storage.getDirectory();
            const projects = await root.getDirectoryHandle('projects', { create: true });
            const names: string[] = [];
            for await (const [name, child] of (projects as unknown as { entries(): AsyncIterable<[string, FileSystemHandle]> }).entries())
            {
                if (child.kind === 'directory')
                {
                    names.push(name);
                }
            }
            return { value: names.sort() };
        }
        catch
        {
            return { value: [] };
        }
    }
    case 'call':
    {
        const started = performance.now();
        const answer = await session.call(request.method, request.params ?? {});
        return { value: answer, timing: { ms: performance.now() - started } };
    }
    case 'walk_load':
    {
        const started = performance.now();
        const answer = session.walkLoad(request.files);
        return { value: answer, timing: { loadMs: performance.now() - started } };
    }
    case 'bytes':
    {
        const answer = session.bytes(request.path);
        const body = answer.body.byteOffset === 0 && answer.body.byteLength === answer.body.buffer.byteLength ? answer.body : answer.body.slice();
        return { value: { status: answer.status, headers: answer.headers, body }, transfer: [body.buffer as ArrayBuffer] };
    }
    case 'export':
    {
        if (request.what === 'mod')
        {
            const installed = session.installMod(request.key);
            if (installed.error)
            {
                throw new Error(installed.error.message);
            }
        }
        const files = session.files(request.key, request.what);
        if (files.length === 0)
        {
            throw new Error(request.what === 'build' ? 'nothing built yet: build the map first' : 'no files to export');
        }
        const zip = zipSync(Object.fromEntries(files.map((file) => [file.path, file.bytes])), { level: 6 });
        return { value: { bytes: zip, files: files.length }, transfer: [zip.buffer as ArrayBuffer] };
    }
    case 'save_to':
    {
        if (request.what === 'mod')
        {
            const installed = session.installMod(request.key);
            if (installed.error)
            {
                throw new Error(installed.error.message);
            }
        }
        const files = session.files(request.key, request.what);
        const target = handleBacking(request.handle, 'folder', '');
        for (const file of files)
        {
            await target.write(file.path, file.bytes);
        }
        return { value: { files: files.length } };
    }
    case 'close':
        session.close(request.key);
        return { value: true };
    case 'stats':
        return { value: { heap: session.heap(), reads: { ...session.reader.stats }, textures: session.textureCache(),
            timings: request.timings ? session.timings.slice() : [] } };
    default:
        throw new Error('unknown request');
    }
}

// One request at a time, in order: a change is written back before the next request runs.
let queue: Promise<void> = Promise.resolve();
scope.onmessage = (event) =>
{
    const request = event.data;
    queue = queue.then(async () =>
    {
        try
        {
            const { value, transfer, timing } = await handle(request);
            scope.postMessage({ id: request.id, ok: true, value, ...(timing ? { timing } : {}) }, transfer ?? []);
        }
        catch (error)
        {
            scope.postMessage({ id: request.id, ok: false, message: error instanceof Error ? error.message : String(error) });
        }
    });
};
