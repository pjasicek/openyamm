// What the person picked as the game's assets, made into the tree the core reads (packfs.ts). Three kinds, tried in
// this order (S5_BROWSER_EDITOR.md 2.11; PLAN.md 9):
//   - a player's install: `app/current` names the release, `app/<release>/index.json` lists the content packs and
//     where they are stored (`assets/packs/`); every pack's entries go under its mount (`/engine/...`,
//     `/worlds/mm6/textures_x4`, ...). Language packs are left out (the core reads none);
//   - the older single packages: `engine.zip` and `worlds/<world>.zip` (also picked one by one): engine.zip under
//     engine/, each world's under worlds/<world>/;
//   - a development tree (a repository checkout's assets_dev, or a play root): a folder with engine/ and worlds/,
//     its loose files read by range.
// A pack named by the index but missing, or of the wrong size, refuses the install as the game does.
import { addEntry, addZip, newDir } from './packfs.ts';
import type { ByteSource, DirEntry } from './packfs.ts';

export interface PickedFile
{
    // The path inside what was picked, slash-separated (webkitRelativePath without its first folder, or the
    // directory handle's walk), or the bare name of a single picked file.
    path: string;
    source: ByteSource;
}

export interface OpenedInstall
{
    kind: 'install' | 'packages' | 'tree';
    tree: DirEntry;
    // Words for the page: the release, the packs or packages mounted, the files of a tree.
    release: string | null;
    packages: number;
    entries: number;
    worlds: string[];
    // Bytes of the packages or files the tree reads from (never read whole).
    bytes: number;
}

interface PackRecord
{
    id: string;
    package: string;
    mount: string;
    file: string;
    size: number;
    language?: string;
}

const text = (source: ByteSource) => new TextDecoder().decode(source.read(0, source.size));

function dirname(path: string): string
{
    const at = path.lastIndexOf('/');
    return at < 0 ? '' : path.slice(0, at);
}

// a/b/../c -> a/c; leading ../ beyond the root is refused (null).
function normalise(path: string): string | null
{
    const parts: string[] = [];
    for (const part of path.split('/'))
    {
        if (part === '' || part === '.')
        {
            continue;
        }
        if (part === '..')
        {
            if (parts.length === 0)
            {
                return null;
            }
            parts.pop();
            continue;
        }
        parts.push(part);
    }
    return parts.join('/');
}

function worldsOf(tree: DirEntry): string[]
{
    const worlds = tree.children.get('worlds');
    return worlds && 'children' in worlds ? [...worlds.children.keys()].sort() : [];
}

export function openInstall(picked: PickedFile[]): OpenedInstall
{
    const byPath = new Map(picked.map((file) => [file.path, file]));

    // A player's install: the index of the current release.
    const current = [...byPath.keys()].filter((path) => path === 'app/current' || path.endsWith('/app/current'));
    const indexes = [...byPath.keys()].filter((path) => /(^|\/)index\.json$/.test(path));
    let indexPath: string | null = null;
    for (const path of current)
    {
        const release = text(byPath.get(path)!.source).trim();
        const candidate = `${dirname(path)}/${release}/index.json`.replace(/^\//, '');
        if (byPath.has(candidate))
        {
            indexPath = candidate;
            break;
        }
    }
    if (!indexPath)
    {
        indexPath = indexes.find((path) =>
        {
            try
            {
                const parsed = JSON.parse(text(byPath.get(path)!.source));
                return Array.isArray(parsed.packs) && typeof parsed.store === 'string';
            }
            catch
            {
                return false;
            }
        }) ?? null;
    }
    if (indexPath)
    {
        const index = JSON.parse(text(byPath.get(indexPath)!.source)) as { release?: string; store: string; packs: PackRecord[] };
        const store = normalise(`${dirname(indexPath)}/${index.store}`);
        if (store === null)
        {
            throw new Error(`the install's index names its packs outside the folder picked (${index.store}): pick the install's own folder`);
        }
        const tree = newDir();
        let entries = 0;
        let bytes = 0;
        for (const pack of index.packs)
        {
            if (pack.language)
            {
                continue;
            }
            const path = store ? `${store}/${pack.file}` : pack.file;
            const file = byPath.get(path);
            if (!file)
            {
                throw new Error(`the install is missing the content pack ${pack.file} (the game would refuse it too: let the launcher repair it)`);
            }
            if (file.source.size !== pack.size)
            {
                throw new Error(`the content pack ${pack.file} has the wrong size (the game would refuse it too: let the launcher repair it)`);
            }
            entries += addZip(tree, file.source, pack.mount);
            bytes += file.source.size;
        }
        return { kind: 'install', tree, release: index.release ?? null, packages: index.packs.filter((pack) => !pack.language).length,
            entries, worlds: worldsOf(tree), bytes };
    }

    // The single packages: engine.zip and the worlds' zips.
    const engineZip = [...byPath.keys()].find((path) => /(^|\/)engine\.zip$/i.test(path));
    if (engineZip)
    {
        const tree = newDir();
        let entries = addZip(tree, byPath.get(engineZip)!.source, '/engine');
        let bytes = byPath.get(engineZip)!.source.size;
        let packages = 1;
        for (const [path, file] of byPath)
        {
            const match = /(^|\/)(mm[0-9]+)\.zip$/i.exec(path);
            if (match)
            {
                entries += addZip(tree, file.source, `/worlds/${match[2].toLowerCase()}`);
                bytes += file.source.size;
                packages += 1;
            }
        }
        return { kind: 'packages', tree, release: null, packages, entries, worlds: worldsOf(tree), bytes };
    }

    // A development tree: the folder that holds engine/ and worlds/ (the one picked, or one level down).
    const prefixes = new Set<string>();
    for (const path of byPath.keys())
    {
        const match = /^(?:(.+?)\/)?(?:engine|worlds)\//.exec(path);
        if (match)
        {
            prefixes.add(match[1] ?? '');
        }
    }
    const prefix = [...prefixes].sort((a, b) => a.length - b.length)[0];
    if (prefix !== undefined)
    {
        const tree = newDir();
        let entries = 0;
        let bytes = 0;
        const start = prefix ? `${prefix}/` : '';
        for (const [path, file] of byPath)
        {
            if (!path.startsWith(start))
            {
                continue;
            }
            addEntry(tree, path.slice(start.length), { source: file.source, size: file.source.size, mtime: file.source.mtime });
            entries += 1;
            bytes += file.source.size;
        }
        if (tree.children.has('engine') && tree.children.has('worlds'))
        {
            return { kind: 'tree', tree, release: null, packages: 0, entries, worlds: worldsOf(tree), bytes };
        }
    }
    throw new Error('not the game\'s files: pick the OpenYAMM folder of an install (the one with app/ and assets/), '
        + 'its engine.zip and world packages, or a development tree with engine/ and worlds/ (assets_dev)');
}
