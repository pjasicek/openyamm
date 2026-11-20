#!/usr/bin/env node
// Stages the hosted page as its own origin would serve it (S5c; S5_BROWSER_EDITOR.md 2.14, 2.15, 4.14; decision D12:
// "the hosted page later on its own origin, versioned on the release server"). Nothing is uploaded: the folder is what
// a deploy would copy to the origin's web root.
//
//   node scripts/stage_hosted.mjs [--version <v>] [--core <folder with oymap_worker.mjs/.wasm>] [--out <site folder>]
//        [--dist <the web app's build, default web/dist>]
//
// Writes <out>/studio/<v>/ (the web app with hosted.html as its index.html, the core under core/, version.json, the
// service worker sw.js listing this release's files, and each text and wasm file also as <file>.br and <file>.gz), <out>/studio/versions.json (every staged version, the newest
// first) and <out>/index.html (sends a visitor to the newest version). Each version keeps its own path, so a page
// open in an older release keeps working and its offline copy stays its own. Run `npm run build` first.
import { copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { brotliCompressSync, constants as zlibConstants, gzipSync } from 'node:zlib';
import { dirname, join, relative, resolve } from 'node:path';

const web = resolve(import.meta.dirname, '..');
const studio = resolve(web, '..');
const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const pkg = JSON.parse(readFileSync(join(web, 'package.json'), 'utf8'));
const version = option('--version', pkg.version);
const core = resolve(option('--core', existsSync(join(studio, 'build-wasm-s4', 'oymap_worker.mjs')) ? join(studio, 'build-wasm-s4') : join(studio, 'build-wasm')));
const out = resolve(option('--out', join(studio, 'hosted_site')));
const dist = resolve(option('--dist', join(web, 'dist')));

if (!/^[0-9A-Za-z][0-9A-Za-z._-]*$/.test(version))
{
    throw new Error(`a version is letters, digits, dots, dashes: ${version}`);
}
if (!existsSync(join(dist, 'hosted.html')))
{
    throw new Error('web/dist has no hosted.html: run `npm run build` in openyamm-studio/web first');
}

// A version's folder is written whole: staging the same version again replaces it (its old hashed files go).
const target = join(out, 'studio', version);
if (existsSync(target) && resolve(target).startsWith(join(out, 'studio') + '/'))
{
    rmSync(target, { recursive: true });
}
mkdirSync(target, { recursive: true });

function copyTree(from, to, skip = () => false)
{
    for (const entry of readdirSync(from, { withFileTypes: true }))
    {
        const source = join(from, entry.name);
        const destination = join(to, entry.name);
        if (skip(relative(dist, source)))
        {
            continue;
        }
        if (entry.isDirectory())
        {
            mkdirSync(destination, { recursive: true });
            copyTree(source, destination, skip);
        }
        else
        {
            copyFileSync(source, destination);
        }
    }
}

// The app (the local page and the gallery are not part of the hosted site).
copyTree(dist, target, (path) => path === 'index.html' || path === 'gallery.html' || path === 'hosted.html');
copyFileSync(join(dist, 'hosted.html'), join(target, 'index.html'));
mkdirSync(join(target, 'core'), { recursive: true });
for (const name of ['oymap_worker.mjs', 'oymap_worker.wasm'])
{
    copyFileSync(join(core, name), join(target, 'core', name));
}

// What this release is, and the files a visit needs offline.
const files = [];
const walk = (folder) =>
{
    for (const entry of readdirSync(folder, { withFileTypes: true }))
    {
        const path = join(folder, entry.name);
        if (entry.isDirectory())
        {
            walk(path);
        }
        else if (entry.name !== 'sw.js')
        {
            files.push(relative(target, path).split('\\').join('/'));
        }
    }
};
walk(target);
files.sort();
const digest = createHash('sha256');
for (const file of files)
{
    digest.update(file).update(readFileSync(join(target, file)));
}
const build = digest.digest('hex').slice(0, 16);
writeFileSync(join(target, 'version.json'), `${JSON.stringify({ version, build, staged: new Date().toISOString(),
    core_bytes: statSync(join(target, 'core', 'oymap_worker.wasm')).size }, null, 1)}\n`);
if (!files.includes('version.json'))
{
    files.push('version.json');
}

// The service worker (S5_BROWSER_EDITOR.md 2.14): this release's files kept in a cache of its own; requests inside
// its folder answered from the cache first, so the page opens offline after the first visit.
writeFileSync(join(target, 'sw.js'), `// Map Studio ${version} (${build}): offline copy of this release (staged by web/scripts/stage_hosted.mjs).
const CACHE = 'oymap-studio-${version}-${build}';
const FILES = ${JSON.stringify(['./', ...files.map((file) => `./${file}`)])};
self.addEventListener('install', (event) =>
{
    event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(FILES)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (event) =>
{
    // Older builds of this same version go; other versions keep their own copies.
    event.waitUntil(caches.keys().then((names) => Promise.all(names
        .filter((name) => name.startsWith('oymap-studio-${version}-') && name !== CACHE)
        .map((name) => caches.delete(name)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (event) =>
{
    const request = event.request;
    if (request.method !== 'GET' || new URL(request.url).origin !== self.location.origin)
    {
        return;
    }
    event.respondWith(caches.match(request, { ignoreSearch: true }).then((hit) => hit ?? fetch(request)));
});
`);

// Each text and wasm file also compressed beside itself (<file>.br, <file>.gz; S8f): a host sends these to browsers
// that accept them (hosted_server.mjs does), as static hosts do with precompressed files. Brotli at its best: the
// core's 10 MB of wasm is about 2.2 MB as Brotli, 3.1 MB as gzip.
let compressed = 0;
const compress = (folder) =>
{
    for (const entry of readdirSync(folder, { withFileTypes: true }))
    {
        const path = join(folder, entry.name);
        if (entry.isDirectory())
        {
            compress(path);
            continue;
        }
        if (!/\.(wasm|mjs|js|css|html|json|svg|txt)$/.test(entry.name) || statSync(path).size < 1024)
        {
            continue;
        }
        const bytes = readFileSync(path);
        writeFileSync(`${path}.br`, brotliCompressSync(bytes, { params: { [zlibConstants.BROTLI_PARAM_QUALITY]: 11,
            [zlibConstants.BROTLI_PARAM_LGWIN]: 24, [zlibConstants.BROTLI_PARAM_SIZE_HINT]: bytes.length } }));
        writeFileSync(`${path}.gz`, gzipSync(bytes, { level: 9 }));
        compressed += 1;
    }
};
compress(target);

// Every staged version, newest first; the root page sends a visitor to the first.
const versionsFile = join(out, 'studio', 'versions.json');
const known = existsSync(versionsFile) ? JSON.parse(readFileSync(versionsFile, 'utf8')).versions ?? [] : [];
const versions = [version, ...known.filter((entry) => entry !== version)];
writeFileSync(versionsFile, `${JSON.stringify({ latest: version, versions }, null, 1)}\n`);
mkdirSync(dirname(join(out, 'index.html')), { recursive: true });
writeFileSync(join(out, 'index.html'), `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Map Studio</title>
<meta http-equiv="refresh" content="0; url=studio/${version}/"></head>
<body><p><a href="studio/${version}/">Map Studio ${version}</a></p></body></html>
`);
console.log(`staged Map Studio ${version} (${build}): ${files.length} files in ${target} (${compressed} also as .br and .gz; core `
    + `${statSync(join(target, 'core', 'oymap_worker.wasm')).size} bytes, Brotli ${statSync(join(target, 'core', 'oymap_worker.wasm.br')).size})`);
