#!/usr/bin/env node
// oymap host (devdocs/map_studio/PLAN.md section 8, S5_BROWSER_EDITOR.md 2.2): the MCP server and the browser
// editor's local host over `oymap serve`.
//   node src/host.mjs mcp    [options]   MCP over standard input and output (for Claude Code, Codex and others)
//   node src/host.mjs studio [options]   the web app, its byte routes, the request list over WebSocket and the MCP
//                                        tools over Streamable HTTP on 127.0.0.1 (studio.mjs); `serve` is the same
//   node src/host.mjs relay  [options]   `oymap mcp`: MCP over standard input and output, relayed to the running
//                                        studio host (found through its discovery file), so the agent and the
//                                        browser share one host and see each other (S5_BROWSER_EDITOR.md F4); with no
//                                        host running, the same as `mcp`
// Options: --oymap <binary>  --assets <asset root>  --game <openyamm binary>  --mount <folder builds are installed into>
//          --port <n> (8765)  --roots <dir,dir,...> (project folders a browser may open)  --web <dist folder>
//          --token <t> (default: random)  --inbox <pins inbox folder>  --mods <the mods folder a browser packs into
//          and lists: mod.pack, mod.list, mod.map_number name it "default"; default output/studio_host/mods)
//          --blender <command> (the lighting_bake job's Blender; default blender on the PATH)
//          --discovery <file> (where the studio host
//          writes its port and token for the relay; default output/studio_host/host.json)
//          --texture-cache <folder> (the textures' small levels kept across runs; default
//          output/studio_host/texture_cache)  --core-wasm <folder holding oymap_worker.mjs and .wasm> (the browser's
//          worker; default openyamm-studio/build-wasm-s4, else build-wasm)  --background on|off (the scorecard's
//          background checks when a browser opens or changes a project: lane J and the Python checks; default on)
//          --allow-origin <origin,...> (a hosted page's origin that may pair with this host: S5c,
//          S5_BROWSER_EDITOR.md 2.12; it still needs the token and the browser's local-network permission)
import { existsSync, readFileSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { Core } from './core.mjs';
import { INSTRUCTIONS, registerTools } from './tools.mjs';

const here = path.dirname(fileURLToPath(import.meta.url));
const studio = path.resolve(here, '../..');
const repo = path.resolve(studio, '..');

export function readOptions(argv) {
  const ownBuild = path.join(studio, 'build-s4/oymap');
  const options = {
    oymap: existsSync(ownBuild) ? ownBuild : path.join(studio, 'build/oymap'),
    assets: path.join(repo, 'assets_dev'),
    game: path.join(repo, 'build/game/openyamm'),
    mount: path.join(repo, 'output/studio_host/mount'),
    port: 8765,
    roots: ['devdocs/map_studio/briefs', 'devdocs/xeen/briefs', 'openyamm-studio/examples'].map((root) => path.join(repo, root)),
    web: path.join(studio, 'web/dist'),
    token: null,
    inbox: path.join(repo, 'pins_inbox'),
    mods: path.join(repo, 'output/studio_host/mods'),
    discovery: path.join(repo, 'output/studio_host/host.json'),
    textureCache: path.join(repo, 'output/studio_host/texture_cache'),
    coreWasm: [path.join(studio, 'build-wasm-s4'), path.join(studio, 'build-wasm')]
      .find((folder) => existsSync(path.join(folder, 'oymap_worker.mjs'))) ?? path.join(studio, 'build-wasm'),
    mountGiven: false,
    background: true,
    allowOrigins: [],
  };
  const keys = { '--oymap': 'oymap', '--assets': 'assets', '--game': 'game', '--mount': 'mount', '--port': 'port',
    '--roots': 'roots', '--web': 'web', '--token': 'token', '--inbox': 'inbox', '--mods': 'mods', '--blender': 'blender',
    '--discovery': 'discovery',
    '--texture-cache': 'textureCache', '--core-wasm': 'coreWasm', '--background': 'background',
    '--allow-origin': 'allowOrigins' };
  for (let index = 0; index + 1 < argv.length; index += 2) {
    const key = keys[argv[index]];
    if (!key) throw new Error(`unknown option ${argv[index]}`);
    const value = argv[index + 1];
    if (key === 'port') options.port = Number(value);
    else if (key === 'token') options.token = value;
    else if (key === 'background') options.background = value !== 'off';
    else if (key === 'allowOrigins') {
      options.allowOrigins = value.split(',').filter(Boolean).map((origin) => {
        const parsed = new URL(origin);
        if (parsed.origin !== origin.replace(/\/$/, '') || !/^https?:$/.test(parsed.protocol)) {
          throw new Error(`--allow-origin takes origins (scheme://host[:port]), not ${origin}`);
        }
        return parsed.origin;
      });
    }
    else if (key === 'roots') options.roots = value.split(',').filter(Boolean).map((root) => path.resolve(root));
    else if (key === 'blender') options.blender = value.includes('/') ? path.resolve(value) : value;
    else options[key] = path.resolve(value);
    if (key === 'mount') options.mountGiven = true;
  }
  return options;
}

export function createMcpServer(options) {
  // The session's asset root is the core's own (serve --assets): methods of the request list that read assets use it.
  const core = new Core(options.oymap, { assets: options.assets });
  const server = new McpServer({ name: 'openyamm-map-studio', version: '0.1.0' }, { instructions: INSTRUCTIONS });
  registerTools(server, { core, assets: options.assets, game: options.game, mount: options.mount });
  return { server, core };
}

async function runMcp(options) {
  const { server } = createMcpServer(options);
  await server.connect(new StdioServerTransport());
}

// The studio host this relay talks to: its discovery file, when the process it names is alive and answers.
async function findHost(discovery) {
  let found;
  try {
    found = JSON.parse(readFileSync(discovery, 'utf8'));
    process.kill(found.pid, 0);
  } catch {
    return null;
  }
  try {
    const response = await fetch(`http://127.0.0.1:${found.port}/health`, { signal: AbortSignal.timeout(2000) });
    return response.ok ? found : null;
  } catch {
    return null;
  }
}

// `oymap mcp`: stdio to the agent, Streamable HTTP to the host, message by message (the relay holds no state).
async function runRelay(options) {
  const host = await findHost(options.discovery);
  if (!host) {
    console.error('oymap mcp: no studio host is running; serving the tools in this process (the browser will not see '
      + 'this agent; start one with `oymap studio`)');
    await runMcp(options);
    return;
  }
  const { StreamableHTTPClientTransport } = await import('@modelcontextprotocol/sdk/client/streamableHttp.js');
  const upstream = new StreamableHTTPClientTransport(new URL(`http://127.0.0.1:${host.port}/mcp`),
    { requestInit: { headers: { Authorization: `Bearer ${host.token}` } } });
  const downstream = new StdioServerTransport();
  const fail = (error) => {
    console.error(`oymap mcp: ${error?.message ?? error}`);
  };
  downstream.onmessage = (message) => void upstream.send(message).catch(fail);
  upstream.onmessage = (message) => void downstream.send(message).catch(fail);
  upstream.onerror = fail;
  // The agent went (its end of standard input closed, or it stopped the relay): the host's session ends with it, so
  // the host says the agent left.
  let leaving = false;
  const leave = () => {
    if (leaving) return;
    leaving = true;
    void upstream.terminateSession().catch(() => undefined).finally(() => upstream.close())
      .finally(() => process.exit(0));
  };
  downstream.onclose = leave;
  process.stdin.on('end', leave);
  process.on('SIGTERM', leave);
  process.on('SIGINT', leave);
  upstream.onclose = () => process.exit(0);
  await upstream.start();
  await downstream.start();
  console.error(`oymap mcp: relaying to the studio host on port ${host.port}`);
}

async function runStudio(options) {
  const { startStudio } = await import('./studio.mjs');
  const token = options.token ?? randomBytes(18).toString('base64url');
  const host = await startStudio({ ...options, token, repo, rpcDir: path.join(studio, 'schema/rpc'),
    // Textures are looked for in the mount only when one was named: the default mount holds MCP test builds.
    mount: options.mountGiven ? options.mount : null, toolsMount: options.mount,
    log: process.env.OYMAP_HOST_LOG ? (line) => console.error(`oymap studio: ${line}`) : undefined });
  console.log(`oymap studio: http://127.0.0.1:${options.port}/#token=${token}`);
  // Stopped: the discovery file goes with the host, so a relay does not look for it.
  const stop = () => void host.close().finally(() => process.exit(0));
  process.on('SIGINT', stop);
  process.on('SIGTERM', stop);
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const [mode, ...rest] = process.argv.slice(2);
  const options = readOptions(rest);
  if (!existsSync(options.oymap)) {
    console.error(`oymap host: ${options.oymap} is not built (run openyamm-studio/build.sh)`);
    process.exit(1);
  }
  if (mode === 'mcp') await runMcp(options);
  else if (mode === 'relay') await runRelay(options);
  else if (mode === 'studio' || mode === 'serve') await runStudio(options);
  else {
    console.error('usage: host.mjs mcp|relay|studio [--oymap <binary>] [--assets <root>] [--game <binary>] [--mount <folder>] '
      + '[--port <n>] [--roots <dir,dir>] [--web <dist>] [--token <t>] [--inbox <folder>]');
    process.exit(2);
  }
}
