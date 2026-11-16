#!/usr/bin/env node
// A local static origin standing in for the hosted page's own origin (S5c; S5_BROWSER_EDITOR.md 2.12, 4.14): serves
// the staged site (scripts/stage_hosted.mjs) as a static host would, with the headers a deploy should send, and each
// file's precompressed copy (Brotli, else gzip) to a browser that accepts it. Nothing
// else: no project, no core, no token. For tests and for looking at the page before a deploy.
//
//   node scripts/hosted_server.mjs [--site <folder>] [--port <n>] [--https <port> --cert <pem> --key <pem>]
// Prints one line per listener: "hosted: http://127.0.0.1:<port>/".
import { createReadStream, existsSync, readFileSync, statSync } from 'node:fs';
import http from 'node:http';
import https from 'node:https';
import { extname, join, resolve, sep } from 'node:path';

const args = process.argv.slice(2);
const option = (name, fallback) => (args.includes(name) ? args[args.indexOf(name) + 1] : fallback);
const site = resolve(option('--site', resolve(import.meta.dirname, '..', '..', 'hosted_site')));
const port = Number(option('--port', '8790'));
const httpsPort = option('--https', null);

const TYPES = {
    '.html': 'text/html; charset=utf-8', '.js': 'text/javascript; charset=utf-8', '.mjs': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8', '.json': 'application/json', '.wasm': 'application/wasm', '.svg': 'image/svg+xml',
    '.png': 'image/png', '.woff2': 'font/woff2', '.txt': 'text/plain; charset=utf-8',
};
// What the page may load and reach: itself, and a paired studio on this computer (2.12).
const CSP = "default-src 'self'; script-src 'self' 'wasm-unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; "
    + "connect-src 'self' http://127.0.0.1:* ws://127.0.0.1:* http://localhost:* ws://localhost:*; worker-src 'self' blob:; "
    + "object-src 'none'; base-uri 'none'; frame-ancestors 'none'";

function handler(request, response)
{
    if (request.method !== 'GET' && request.method !== 'HEAD')
    {
        response.writeHead(405).end();
        return;
    }
    let pathname;
    try
    {
        pathname = decodeURIComponent(new URL(request.url, 'http://x').pathname);
    }
    catch
    {
        response.writeHead(400).end();
        return;
    }
    let file = resolve(site, `.${pathname}`);
    if (file !== site && !file.startsWith(site + sep))
    {
        response.writeHead(404).end();
        return;
    }
    if (existsSync(file) && statSync(file).isDirectory())
    {
        if (!pathname.endsWith('/'))
        {
            response.writeHead(301, { Location: `${pathname}/` }).end();
            return;
        }
        file = join(file, 'index.html');
    }
    if (!existsSync(file) || !statSync(file).isFile())
    {
        response.writeHead(404, { 'Content-Type': 'text/plain' }).end('not found');
        return;
    }
    const type = TYPES[extname(file)] ?? 'application/octet-stream';
    // The file's precompressed copy (stage_hosted.mjs writes <file>.br and <file>.gz) when the browser takes it.
    const accepted = String(request.headers['accept-encoding'] ?? '');
    const encoding = [['br', '.br'], ['gzip', '.gz']].find(([name, suffix]) => new RegExp(`\\b${name}\\b`).test(accepted)
        && existsSync(file + suffix));
    const body = encoding ? file + encoding[1] : file;
    // Hashed app files and a release's core never change under their path; pages, the service worker and the
    // version files are read again.
    const immutable = /\/studio\/[^/]+\/(assets|core)\//.test(pathname);
    const headers = {
        'Content-Type': type, 'Content-Length': statSync(body).size, 'Vary': 'Accept-Encoding',
        ...(encoding ? { 'Content-Encoding': encoding[0] } : {}),
        'Cache-Control': immutable ? 'public, max-age=31536000, immutable' : 'no-cache',
        'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer',
        'Cross-Origin-Opener-Policy': 'same-origin',
    };
    if (type.startsWith('text/html') || type.startsWith('text/javascript'))
    {
        headers['Content-Security-Policy'] = CSP;
    }
    response.writeHead(200, headers);
    if (request.method === 'HEAD')
    {
        response.end();
        return;
    }
    createReadStream(body).pipe(response);
}

const servers = [];
const plain = http.createServer(handler);
await new Promise((done) => plain.listen(port, '127.0.0.1', done));
servers.push(plain);
console.log(`hosted: http://127.0.0.1:${plain.address().port}/`);
if (httpsPort)
{
    const secure = https.createServer({ cert: readFileSync(option('--cert')), key: readFileSync(option('--key')) }, handler);
    await new Promise((done) => secure.listen(Number(httpsPort), '127.0.0.1', done));
    servers.push(secure);
    console.log(`hosted: https://127.0.0.1:${secure.address().port}/`);
}
const stop = () =>
{
    for (const server of servers)
    {
        server.close();
        server.closeAllConnections?.();
    }
    process.exit(0);
};
process.on('SIGINT', stop);
process.on('SIGTERM', stop);
