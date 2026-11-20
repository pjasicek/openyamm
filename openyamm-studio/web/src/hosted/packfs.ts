// The hosted page's asset root (S5_BROWSER_EDITOR.md 2.11, PLAN.md 9 "Assets in the hosted page"): a read-only file
// system for the WebAssembly core that shows a player's install, or a repository checkout, as the development tree
// the core reads (`engine/...`, `worlds/<world>/...`). Packages are read by byte range and never loaded whole: each
// zip's central directory is read once and kept as a small table; a stored entry (cooked textures, pictures) is read
// as a range of the package; a deflated entry (tables, maps, scenes) is inflated when it is first read and kept in a
// bounded cache. Loose files (a checkout picked as a folder) are read by range the same way.
//
// The core reaches it through its ordinary file calls (std::filesystem, PhysicsFS's folder archiver): the worker
// mounts it at /a/root and configures the session with that path, so the core opens it as it opens assets_dev
// natively. Directory nodes are made on lookup (only what the core walks), names are case-sensitive as on Linux,
// where the native reference builds run.
//
// Framework-free and runnable under Node (tests/hosted_node.mjs passes byte sources over node:fs) as in a worker
// (sources over FileReaderSync).
import { inflateSync } from 'three/examples/jsm/libs/fflate.module.js';

// Synchronous reads of one file or package: the worker's FileReaderSync over a File, or node:fs in tests.
export interface ByteSource
{
    readonly size: number;
    // Unix milliseconds of the file's last change.
    readonly mtime: number;
    read(offset: number, length: number): Uint8Array;
}

// One file of the tree: the whole of a loose file, or one entry of a package.
export interface FileEntry
{
    source: ByteSource;
    size: number;
    mtime: number;
    // A package's entry: its local header's offset, the method (0 stored, 8 deflated) and the compressed size; the
    // data's offset is read from the local header on first use.
    zip?: { header: number; method: number; compressed: number; data?: number };
}

export interface DirEntry
{
    children: Map<string, DirEntry | FileEntry>;
    mtime: number;
}

export function isDir(entry: DirEntry | FileEntry): entry is DirEntry
{
    return (entry as DirEntry).children !== undefined;
}

export function newDir(mtime = 0): DirEntry
{
    return { children: new Map(), mtime };
}

// Puts an entry at a slash-separated path under the root, making the folders on the way. A later entry at the same
// path replaces an earlier one (callers add in the order the game mounts, the winner last).
export function addEntry(root: DirEntry, path: string, entry: FileEntry): void
{
    const parts = path.split('/').filter((part) => part.length > 0 && part !== '.');
    let dir = root;
    for (const part of parts.slice(0, -1))
    {
        if (part === '..')
        {
            return;
        }
        let next = dir.children.get(part);
        if (!next || !isDir(next))
        {
            next = newDir(entry.mtime);
            dir.children.set(part, next);
        }
        dir = next;
    }
    const name = parts.at(-1);
    if (name && name !== '..')
    {
        dir.children.set(name, entry);
    }
}

export function findEntry(root: DirEntry, path: string): DirEntry | FileEntry | undefined
{
    let node: DirEntry | FileEntry = root;
    for (const part of path.split('/').filter((value) => value.length > 0))
    {
        if (!isDir(node))
        {
            return undefined;
        }
        const next: DirEntry | FileEntry | undefined = node.children.get(part);
        if (!next)
        {
            return undefined;
        }
        node = next;
    }
    return node;
}

// --- zip central directories ---------------------------------------------------------------------------------------

export interface ZipRecord
{
    name: string;
    method: number;
    compressed: number;
    size: number;
    header: number;
    mtime: number;
}

const view = (bytes: Uint8Array) => new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);

function dosTime(time: number, date: number): number
{
    const year = ((date >> 9) & 0x7f) + 1980;
    const month = ((date >> 5) & 0x0f) - 1;
    const day = date & 0x1f;
    return Date.UTC(year, month, day, (time >> 11) & 0x1f, (time >> 5) & 0x3f, (time & 0x1f) * 2);
}

const decoder = new TextDecoder();

// The entries of a zip (directories left out): from its end-of-central-directory record, ZIP64 included.
export function readZipDirectory(source: ByteSource): ZipRecord[]
{
    const tailLength = Math.min(source.size, 65557);
    const tail = source.read(source.size - tailLength, tailLength);
    const tailView = view(tail);
    let end = -1;
    for (let at = tail.length - 22; at >= 0; --at)
    {
        if (tailView.getUint32(at, true) === 0x06054b50)
        {
            end = at;
            break;
        }
    }
    if (end < 0)
    {
        throw new Error('not a zip archive (no end of central directory)');
    }
    let count = tailView.getUint16(end + 10, true);
    let directorySize = tailView.getUint32(end + 12, true);
    let directoryOffset = tailView.getUint32(end + 16, true);
    if (count === 0xffff || directorySize === 0xffffffff || directoryOffset === 0xffffffff)
    {
        // ZIP64: the locator sits just before the end record and names the ZIP64 end record.
        const locator = end - 20;
        if (locator < 0 || tailView.getUint32(locator, true) !== 0x07064b50)
        {
            throw new Error('a ZIP64 archive without its locator');
        }
        const record = Number(tailView.getBigUint64(locator + 8, true));
        const zip64 = view(source.read(record, 56));
        if (zip64.getUint32(0, true) !== 0x06064b50)
        {
            throw new Error('a ZIP64 archive without its end record');
        }
        count = Number(zip64.getBigUint64(32, true));
        directorySize = Number(zip64.getBigUint64(40, true));
        directoryOffset = Number(zip64.getBigUint64(48, true));
    }
    const directory = source.read(directoryOffset, directorySize);
    const dir = view(directory);
    const records: ZipRecord[] = [];
    let at = 0;
    for (let index = 0; index < count && at + 46 <= directory.length; ++index)
    {
        if (dir.getUint32(at, true) !== 0x02014b50)
        {
            throw new Error(`a broken central directory (entry ${index})`);
        }
        const method = dir.getUint16(at + 10, true);
        const mtime = dosTime(dir.getUint16(at + 12, true), dir.getUint16(at + 14, true));
        let compressed = dir.getUint32(at + 20, true);
        let size = dir.getUint32(at + 24, true);
        const nameLength = dir.getUint16(at + 28, true);
        const extraLength = dir.getUint16(at + 30, true);
        const commentLength = dir.getUint16(at + 32, true);
        let header = dir.getUint32(at + 42, true);
        const name = decoder.decode(directory.subarray(at + 46, at + 46 + nameLength));
        // The ZIP64 extra field holds, in order, the sizes and the offset that the record marks 0xffffffff.
        let extra = at + 46 + nameLength;
        const extraEnd = extra + extraLength;
        while (extra + 4 <= extraEnd)
        {
            const id = dir.getUint16(extra, true);
            const length = dir.getUint16(extra + 2, true);
            if (id === 0x0001)
            {
                let field = extra + 4;
                if (size === 0xffffffff)
                {
                    size = Number(dir.getBigUint64(field, true));
                    field += 8;
                }
                if (compressed === 0xffffffff)
                {
                    compressed = Number(dir.getBigUint64(field, true));
                    field += 8;
                }
                if (header === 0xffffffff)
                {
                    header = Number(dir.getBigUint64(field, true));
                }
            }
            extra += 4 + length;
        }
        at = extraEnd + commentLength;
        if (!name.endsWith('/'))
        {
            records.push({ name, method, compressed, size, header, mtime });
        }
    }
    return records;
}

// Adds every entry of a package under `mount` (a folder of the tree, "" for its root).
export function addZip(root: DirEntry, source: ByteSource, mount: string): number
{
    const records = readZipDirectory(source);
    const prefix = mount.replace(/^\/+|\/+$/g, '');
    for (const record of records)
    {
        addEntry(root, prefix ? `${prefix}/${record.name}` : record.name, {
            source, size: record.size, mtime: record.mtime,
            zip: { header: record.header, method: record.method, compressed: record.compressed },
        });
    }
    return records.length;
}

// --- reading -------------------------------------------------------------------------------------------------------

// What the reads cost, for the budgets (S5_BROWSER_EDITOR.md 2.13): bytes read from the user's files, inflated
// bytes, and the inflate cache.
export interface ReadStats
{
    reads: number;
    bytesRead: number;
    inflated: number;
    inflatedBytes: number;
    cacheBytes: number;
}

export class EntryReader
{
    readonly stats: ReadStats = { reads: 0, bytesRead: 0, inflated: 0, inflatedBytes: 0, cacheBytes: 0 };
    // Inflated entries, least recently used first, bounded by bytes.
    private readonly inflatedCache = new Map<FileEntry, Uint8Array>();
    // The last range read of a stored entry or loose file (reads come in small pieces: PhysicsFS and the C++
    // streams read a few kilobytes at a time).
    private ahead: { entry: FileEntry; start: number; bytes: Uint8Array } | null = null;
    private readonly budget: number;

    constructor(budgetBytes = 64 * 1024 * 1024)
    {
        this.budget = budgetBytes;
    }

    private rawRead(entry: FileEntry, offset: number, length: number): Uint8Array
    {
        this.stats.reads += 1;
        this.stats.bytesRead += length;
        return entry.source.read(offset, length);
    }

    private dataOffset(entry: FileEntry): number
    {
        const zip = entry.zip!;
        if (zip.data === undefined)
        {
            const header = view(this.rawRead(entry, zip.header, 30));
            if (header.getUint32(0, true) !== 0x04034b50)
            {
                throw new Error('a broken local header');
            }
            zip.data = zip.header + 30 + header.getUint16(26, true) + header.getUint16(28, true);
        }
        return zip.data;
    }

    private inflated(entry: FileEntry): Uint8Array
    {
        const kept = this.inflatedCache.get(entry);
        if (kept)
        {
            this.inflatedCache.delete(entry);
            this.inflatedCache.set(entry, kept);
            return kept;
        }
        const zip = entry.zip!;
        const compressed = this.rawRead(entry, this.dataOffset(entry), zip.compressed);
        const bytes = inflateSync(compressed, { out: new Uint8Array(entry.size) });
        this.stats.inflated += 1;
        this.stats.inflatedBytes += bytes.length;
        this.inflatedCache.set(entry, bytes);
        this.stats.cacheBytes += bytes.length;
        for (const [old, oldBytes] of this.inflatedCache)
        {
            if (this.stats.cacheBytes <= this.budget || old === entry)
            {
                break;
            }
            this.inflatedCache.delete(old);
            this.stats.cacheBytes -= oldBytes.length;
        }
        return bytes;
    }

    // Up to `length` bytes of the entry from `position` (fewer at its end).
    read(entry: FileEntry, position: number, length: number): Uint8Array
    {
        if (position >= entry.size || length <= 0)
        {
            return new Uint8Array(0);
        }
        const count = Math.min(length, entry.size - position);
        if (entry.zip && entry.zip.method === 8)
        {
            return this.inflated(entry).subarray(position, position + count);
        }
        if (entry.zip && entry.zip.method !== 0)
        {
            throw new Error(`zip method ${entry.zip.method} is not read`);
        }
        const ahead = this.ahead;
        if (ahead && ahead.entry === entry && position >= ahead.start && position + count <= ahead.start + ahead.bytes.length)
        {
            return ahead.bytes.subarray(position - ahead.start, position - ahead.start + count);
        }
        const base = entry.zip ? this.dataOffset(entry) : 0;
        // Small pieces read a larger range once; a large read is read as asked.
        const span = count >= 256 * 1024 ? count : Math.min(entry.size - position, 256 * 1024);
        const bytes = this.rawRead(entry, base + position, span);
        this.ahead = { entry, start: position, bytes };
        return bytes.subarray(0, count);
    }

    // The whole entry (a texture, a table).
    readAll(entry: FileEntry): Uint8Array
    {
        if (entry.zip && entry.zip.method === 8)
        {
            return this.inflated(entry);
        }
        const base = entry.zip ? this.dataOffset(entry) : 0;
        return this.rawRead(entry, base, entry.size);
    }

    dropCaches(): void
    {
        this.inflatedCache.clear();
        this.stats.cacheBytes = 0;
        this.ahead = null;
    }
}

// --- the Emscripten file system ------------------------------------------------------------------------------------

// What PACKFS needs of Emscripten's FS object (exported by the core's build as Module.FS).
interface EmscriptenNode
{
    id: number;
    mode: number;
    name: string;
    parent: EmscriptenNode;
    node_ops: object;
    stream_ops: object;
    mtime: number;
    atime: number;
    ctime: number;
    entry: DirEntry | FileEntry;
}

export interface EmscriptenFS
{
    createNode(parent: EmscriptenNode | null, name: string, mode: number, rdev: number): EmscriptenNode;
    mount(type: object, options: object, mountpoint: string): unknown;
    mkdirTree(path: string): void;
    ErrnoError: new (errno: number) => Error;
}

const S_IFDIR = 0o040000;
const S_IFREG = 0o100000;
const DIR_MODE = S_IFDIR | 0o555;
const FILE_MODE = S_IFREG | 0o444;
// Emscripten's errno numbers (musl's wasm numbering).
const ENOENT = 44;
const EPERM = 63;
const EINVAL = 28;
const EROFS = 69;

// Mounts the tree read-only at `mountpoint` (whose parent must exist and be writable: the core makes an
// assets_editor_dev folder beside its asset root, as natively).
export function mountTree(FS: EmscriptenFS, tree: DirEntry, mountpoint: string, reader: EntryReader): void
{
    const refuse = (errno: number) => () =>
    {
        throw new FS.ErrnoError(errno);
    };
    const makeNode = (parent: EmscriptenNode | null, name: string, entry: DirEntry | FileEntry): EmscriptenNode =>
    {
        const node = FS.createNode(parent, name, isDir(entry) ? DIR_MODE : FILE_MODE, 0);
        node.node_ops = nodeOps;
        node.stream_ops = streamOps;
        node.entry = entry;
        node.mtime = node.atime = node.ctime = entry.mtime || 0;
        return node;
    };
    const nodeOps = {
        getattr(node: EmscriptenNode)
        {
            const entry = node.entry;
            const size = isDir(entry) ? 4096 : entry.size;
            return {
                dev: 1, ino: node.id, mode: node.mode, nlink: 1, uid: 0, gid: 0, rdev: 0, size,
                atime: new Date(node.atime), mtime: new Date(node.mtime), ctime: new Date(node.ctime),
                blksize: 4096, blocks: Math.ceil(size / 4096),
            };
        },
        setattr: refuse(EROFS),
        lookup(parent: EmscriptenNode, name: string)
        {
            const entry = parent.entry;
            const child = isDir(entry) ? entry.children.get(name) : undefined;
            if (!child)
            {
                throw new FS.ErrnoError(ENOENT);
            }
            return makeNode(parent, name, child);
        },
        mknod: refuse(EROFS),
        rename: refuse(EROFS),
        unlink: refuse(EROFS),
        rmdir: refuse(EROFS),
        readdir(node: EmscriptenNode)
        {
            const entry = node.entry;
            return ['.', '..', ...(isDir(entry) ? entry.children.keys() : [])];
        },
        symlink: refuse(EROFS),
        readlink: refuse(EINVAL),
    };
    const streamOps = {
        read(stream: { node: EmscriptenNode }, buffer: Int8Array, offset: number, length: number, position: number)
        {
            const entry = stream.node.entry;
            if (isDir(entry))
            {
                throw new FS.ErrnoError(EPERM);
            }
            const bytes = reader.read(entry, position, length);
            // A byte copy into the heap (buffer is the module's Int8Array view).
            new Uint8Array(buffer.buffer, buffer.byteOffset + offset, bytes.length).set(bytes);
            return bytes.length;
        },
        write: refuse(EROFS),
        llseek(stream: { node: EmscriptenNode; position: number }, offset: number, whence: number)
        {
            let position = offset;
            if (whence === 1)
            {
                position += stream.position;
            }
            else if (whence === 2)
            {
                const entry = stream.node.entry;
                position += isDir(entry) ? 0 : entry.size;
            }
            if (position < 0)
            {
                throw new FS.ErrnoError(EINVAL);
            }
            return position;
        },
    };
    const type = {
        mount: () => makeNode(null, '/', tree),
    };
    FS.mkdirTree(mountpoint);
    FS.mount(type, {}, mountpoint);
}
