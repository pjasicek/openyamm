#!/usr/bin/env node
// The hosted page's core under Node (S5c): the browser worker's build (build-wasm*/oymap_worker.mjs) with the asset
// root mounted by the hosted page's own read-only file system (web/src/hosted/packfs.ts, install.ts) over byte sources
// that read with node:fs as the browser's FileReaderSync does. Builds projects from an in-memory copy and writes their
// outputs to a folder, so they can be compared with the native build (tests/hosted_checks.sh).
//
//   node tests/hosted_node.mjs --core <oymap_worker.mjs> --assets <install, package folder or tree>
//        --out <folder> <project folder>...
// Prints one JSON line per project: {name, rc, files, ms, heap}. Run with Node 24 (type stripping of the .ts files).
import { closeSync, fstatSync, mkdirSync, openSync, readdirSync, readFileSync, readSync, statSync, writeFileSync } from 'node:fs';
import { basename, join, relative, resolve, dirname } from 'node:path';
import { performance } from 'node:perf_hooks';
import { mountTree, EntryReader } from '../web/src/hosted/packfs.ts';
import { openInstall } from '../web/src/hosted/install.ts';

const args = process.argv.slice(2);
const option = (name) => (args.includes(name) ? args[args.indexOf(name) + 1] : undefined);
const core = resolve(option('--core') ?? 'build-wasm-s4/oymap_worker.mjs');
const assets = resolve(option('--assets'));
const out = resolve(option('--out') ?? 'hosted_node_out');
const projects = args.filter((value, index) => !value.startsWith('--') && !args[index - 1]?.startsWith('--'));

function nodeSource(path)
{
    const info = statSync(path);
    let fd = null;
    return {
        size: info.size,
        mtime: info.mtimeMs,
        read(offset, length)
        {
            fd ??= openSync(path, 'r');
            const bytes = new Uint8Array(length);
            let done = 0;
            while (done < length)
            {
                const got = readSync(fd, bytes, done, length - done, offset + done);
                if (got <= 0) break;
                done += got;
            }
            return done === length ? bytes : bytes.subarray(0, done);
        },
    };
}

function walk(root, folder = root, list = [])
{
    for (const entry of readdirSync(folder, { withFileTypes: true }))
    {
        const path = join(folder, entry.name);
        if (entry.isDirectory()) walk(root, path, list);
        else if (entry.isFile()) list.push({ path: relative(root, path).split('\\').join('/'), source: nodeSource(path) });
    }
    return list;
}

const started = performance.now();
const { default: createOymapCore } = await import(core);
const module = await createOymapCore({ print: () => undefined, printErr: () => undefined });
const loadMs = performance.now() - started;

const call = (method, params) =>
{
    const methodText = module.stringToNewUTF8(method);
    const paramsText = module.stringToNewUTF8(JSON.stringify(params));
    const answer = module._oymap_call(methodText, paramsText);
    const text = module.UTF8ToString(answer);
    module._oymap_free(answer);
    module._free(methodText);
    module._free(paramsText);
    return JSON.parse(text);
};
const heap = () =>
{
    const at = module._malloc(32);
    module._oymap_heap(at);
    const fields = Array.from(module.HEAPF64.subarray(at / 8, at / 8 + 4));
    module._free(at);
    return { live: fields[0], arena: fields[1], memory: fields[2], peak: fields[3] };
};

// The asset root: what the person would pick, read through the hosted page's file system.
const openStarted = performance.now();
const picked = statSync(assets).isDirectory() ? walk(assets) : [{ path: basename(assets), source: nodeSource(assets) }];
const install = openInstall(picked);
const reader = new EntryReader();
module.FS.mkdirTree('/a');
mountTree(module.FS, install.tree, '/a/root', reader);
const configured = call('session.configure', { asset_root: '/a/root' });
if (!configured.result) throw new Error(`session.configure: ${JSON.stringify(configured)}`);
console.error(`install: ${install.kind} ${install.release ?? ''} ${install.packages} packages ${install.entries} entries, `
    + `opened in ${Math.round(performance.now() - openStarted)} ms (core ${Math.round(loadMs)} ms)`);

function copyIn(folder, target)
{
    module.FS.mkdirTree(target);
    for (const entry of readdirSync(folder, { withFileTypes: true }))
    {
        if (entry.name === 'build' || entry.name === '.oymap') continue;
        const path = join(folder, entry.name);
        if (entry.isDirectory()) copyIn(path, `${target}/${entry.name}`);
        else module.FS.writeFile(`${target}/${entry.name}`, readFileSync(path));
    }
}

function copyOut(source, target)
{
    let count = 0;
    for (const name of module.FS.readdir(source))
    {
        if (name === '.' || name === '..') continue;
        const path = `${source}/${name}`;
        const stat = module.FS.stat(path);
        if (module.FS.isDir(stat.mode)) count += copyOut(path, join(target, name));
        else
        {
            mkdirSync(target, { recursive: true });
            writeFileSync(join(target, name), module.FS.readFile(path));
            count += 1;
        }
    }
    return count;
}

for (const folder of projects)
{
    const name = basename(folder) === 'L4' ? basename(dirname(folder)) : basename(folder);
    const memory = `/p/${name}`;
    copyIn(resolve(folder), memory);
    const buildStarted = performance.now();
    const answer = call('build.run', { project: memory, dry_run: false });
    const ms = performance.now() - buildStarted;
    let files = 0;
    if (answer.result)
    {
        files = copyOut(`${memory}/build`, join(out, name, 'out'));
    }
    writeFileSync(join(out, `${name}.answer.json`), JSON.stringify(answer, null, 1));
    console.log(JSON.stringify({ name, rc: answer.result ? 0 : 1, files, ms: Math.round(ms), heap: heap(),
        error: answer.error?.message?.split('\n')[0] }));
}
console.error(`reads ${reader.stats.reads}, ${(reader.stats.bytesRead / 1e6).toFixed(1)} MB; inflated ${reader.stats.inflated} `
    + `(${(reader.stats.inflatedBytes / 1e6).toFixed(1)} MB)`);
