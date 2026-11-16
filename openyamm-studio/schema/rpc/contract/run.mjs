#!/usr/bin/env node
// The RPC contract suite (S5_BROWSER_EDITOR.md 2.3): the calls of cases.mjs against the native core (`oymap serve`)
// and the WebAssembly core (oymap_call under Node), each on its own fresh copy of each fixture; with --worker also the
// browser worker's build itself (oymap_worker.mjs, S5c: the hosted page's core) under Node, its in-memory file system
// with the host's folders mounted (NODEFS) where the suite names them. It checks that
//   - every answer matches its schema (params, result or typed error; x-decimals rounding), with ajv;
//   - an error's kind is one the method declares (or unknown_method, invalid_params, failed);
//   - the two backends answer the same bytes, apart from the pointers a step lists in `differs`;
//   - the native answers equal the recorded ones in expected/<fixture>.json (--record writes them).
//
// node schema/rpc/contract/run.mjs --native <oymap> [--wasm <oymap_rpc.js>] [--worker <oymap_worker.mjs>] [--assets <root>] [--record]
//                                   [--project <folder> ...] [--only <fixture>] [--timings <file.json>] [--verbose]
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { cpSync, mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync, existsSync, readdirSync } from 'node:fs';
import { createRequire } from 'node:module';
import { tmpdir } from 'node:os';
import { basename, dirname, join, resolve } from 'node:path';
import { createInterface } from 'node:readline';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { fixtures, readOnlySteps } from './cases.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const rpcDir = resolve(here, '..');
const studio = resolve(rpcDir, '..', '..');

// --- arguments ----------------------------------------------------------------------------------------------------

const args = process.argv.slice(2);
const option = (name) => {
  const index = args.indexOf(name);
  return index >= 0 ? args[index + 1] : undefined;
};
const options = (name) => args.flatMap((value, index) => (value === name ? [args[index + 1]] : []));
const nativePath = option('--native');
const wasmPath = option('--wasm');
const workerPath = option('--worker');
const assets = option('--assets') ?? resolve(studio, '..', 'assets_dev');
const record = args.includes('--record');
const verbose = args.includes('--verbose');
const only = option('--only');
const timingsFile = option('--timings');
const extraProjects = options('--project');

if (!nativePath) {
  console.error('usage: run.mjs --native <oymap> [--wasm <oymap_rpc.js>] [--assets <root>] [--record] '
    + '[--project <folder> ...] [--only <fixture>] [--timings <file.json>]');
  process.exit(2);
}

// --- schemas ------------------------------------------------------------------------------------------------------

// ajv comes with the host's MCP SDK (host/node_modules); the suite adds no dependency of its own.
const require = createRequire(join(studio, 'host', 'package.json'));
const Ajv2020 = require('ajv/dist/2020').default;
const ajv = new Ajv2020({ strict: false, allErrors: true });
ajv.addKeyword({
  keyword: 'x-decimals',
  type: 'number',
  schemaType: 'number',
  validate: (decimals, value) => Math.abs(Math.round(value * 10 ** decimals) / 10 ** decimals - value) === 0,
});
const base = 'https://openyamm.local/schema/';
const schemaFiles = [
  ...readdirSync(rpcDir).filter((n) => n.endsWith('.rpc.json')).map((n) => join(rpcDir, n)),
  ...readdirSync(join(rpcDir, '..')).filter((n) => n.endsWith('.schema.json')).map((n) => join(rpcDir, '..', n)),
];
const catalogue = {};
for (const file of schemaFiles) {
  const schema = JSON.parse(readFileSync(file, 'utf8'));
  ajv.addSchema({ ...schema, $id: base + basename(file) });
  for (const name of Object.keys(schema.methods ?? {})) {
    catalogue[`${schema['x-group']}.${name}`] = { file: basename(file), name, method: schema.methods[name] };
  }
}
const validator = (ref) => {
  const found = ajv.getSchema(base + ref);
  if (!found) throw new Error(`no schema ${ref}`);
  return found;
};
const errorValidator = validator('common.rpc.json#/$defs/error');
const commonErrors = ['unknown_method', 'invalid_params', 'failed'];

function checkAnswer(method, params, answer) {
  const problems = [];
  const entry = catalogue[method];
  if (entry) {
    const paramsValid = validator(`${entry.file}#/methods/${entry.name}/params`);
    // Steps that test refused params send invalid ones on purpose.
    if (!paramsValid(params) && !(answer.error?.data?.kind === 'invalid_params')) {
      problems.push(`params do not match: ${ajv.errorsText(paramsValid.errors)}`);
    }
  }
  if ('result' in answer) {
    if (!entry) problems.push('a result for a method the catalogue lacks');
    else {
      const resultValid = validator(`${entry.file}#/methods/${entry.name}/result`);
      if (!resultValid(answer.result)) problems.push(`result does not match: ${ajv.errorsText(resultValid.errors)}`);
    }
  } else if ('error' in answer) {
    if (!errorValidator(answer.error)) problems.push(`error does not match: ${ajv.errorsText(errorValidator.errors)}`);
    const kind = answer.error?.data?.kind;
    if (entry && !commonErrors.includes(kind) && !entry.method.errors.includes(kind)) {
      problems.push(`error kind ${kind} is not one ${method} declares`);
    }
  } else {
    problems.push('neither result nor error');
  }
  return problems;
}

// --- backends -----------------------------------------------------------------------------------------------------

class NativeCore {
  constructor(path) {
    this.name = 'native';
    this.child = spawn(path, ['serve'], { stdio: ['pipe', 'pipe', 'inherit'] });
    this.lines = createInterface({ input: this.child.stdout });
    this.waiting = [];
    this.lines.on('line', (line) => this.waiting.shift()?.(line));
    this.nextId = 1;
  }

  // The answer as the core wrote it, without the envelope: the text the wasm core returns.
  call(method, params) {
    const id = this.nextId++;
    return new Promise((resolveLine) => {
      this.waiting.push((line) => {
        const prefix = `{"jsonrpc":"2.0","id":${id},`;
        resolveLine(line.startsWith(prefix) ? `{${line.slice(prefix.length)}` : line);
      });
      this.child.stdin.write(`${JSON.stringify({ jsonrpc: '2.0', id, method, params })}\n`);
    });
  }

  close() {
    this.child.stdin.end();
  }
}

class WasmCore {
  static async load(path) {
    const core = new WasmCore();
    core.name = 'wasm';
    const createOymapCore = createRequire(import.meta.url)(resolve(path));
    core.module = await createOymapCore();
    return core;
  }

  call(method, params) {
    const m = this.module;
    const methodText = m.stringToNewUTF8(method);
    const paramsText = m.stringToNewUTF8(JSON.stringify(params));
    const answer = m._oymap_call(methodText, paramsText);
    const text = m.UTF8ToString(answer);
    m._oymap_free(answer);
    m._free(methodText);
    m._free(paramsText);
    return Promise.resolve(text);
  }

  close() {}
}

// The browser worker's build under Node: the same module the hosted page loads, with the folders the suite reads and
// writes (its work folder, the repository, the asset root) mounted from the host at their own paths.
class WorkerCore extends WasmCore {
  static async load(path, folders) {
    const core = new WorkerCore();
    core.name = 'worker';
    const { pathToFileURL } = await import('node:url');
    const { default: createOymapCore } = await import(pathToFileURL(resolve(path)).href);
    core.module = await createOymapCore({ print: () => undefined, printErr: () => undefined });
    const fs = core.module.FS;
    const mounted = [];
    for (const folder of folders) {
      if (mounted.some((done) => folder === done || folder.startsWith(`${done}/`))) continue;
      fs.mkdirTree(folder);
      fs.mount(core.module.NODEFS, { root: folder }, folder);
      mounted.push(folder);
    }
    return core;
  }
}

// --- running ------------------------------------------------------------------------------------------------------

function freshCopy(source, work, name) {
  const target = join(work, name);
  cpSync(source, target, {
    recursive: true,
    filter: (path) => !['build', '.oymap'].includes(basename(path)),
  });
  return target;
}

// The core marks a hand-edited project with the local date (edited_by_hand since ...): the answers record it as
// $TODAY so they do not change at midnight.
function localDate() {
  const now = new Date();
  const pad = (value) => String(value).padStart(2, '0');
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

function normalise(text, project) {
  const date = localDate();
  return text.split(project).join('$PROJECT').split(assets).join('$ASSETS')
    .split(`"since": "${date}"`).join('"since": "$TODAY"').split(`"since":"${date}"`).join('"since":"$TODAY"')
    .split(`edited_by_hand since ${date}`).join('edited_by_hand since $TODAY');
}

// A project marked edited by hand holds the date in its project.yml, so every revision hashed after the mark changes
// each day. In an answer that carries the mark ($TODAY), and in every later answer of that suite, revisions become
// $REV1, $REV2, ... in order of first appearance: equal revisions stay equal, and the answers stop changing at
// midnight. The cores are still compared with each other on the real hashes.
function withDatedRevisions(text, tokens) {
  if (!tokens.size && !text.includes('$TODAY')) return text;
  if (!tokens.size) tokens.set('', '');
  return text.replace(/("(?:view_)?revision(?:_before|_after)?": ?")([0-9a-f]{32})(")/g, (match, head, hash, tail) => {
    if (!tokens.has(hash)) tokens.set(hash, `$REV${tokens.size}`);
    return `${head}${tokens.get(hash)}${tail}`;
  });
}

function withoutPointers(text, pointers) {
  if (!pointers?.length) return text;
  const value = JSON.parse(text);
  for (const pointer of pointers) {
    // JSON pointers (RFC 6901): ~1 is a slash in a key (review~1pins.yml), ~0 a tilde.
    const parts = pointer.split('/').slice(1).map((part) => part.replaceAll('~1', '/').replaceAll('~0', '~'));
    let node = value;
    for (const part of parts.slice(0, -1)) node = node?.[part];
    if (node) delete node[parts.at(-1)];
  }
  return JSON.stringify(value);
}

async function runSteps(core, steps, project) {
  const state = { project };
  const answers = [];
  for (const step of steps) {
    if (step.touch) {
      const file = join(project, step.touch.file);
      writeFileSync(file, readFileSync(file, 'utf8').replace(step.touch.from, step.touch.to));
      answers.push({ step, touch: true });
      continue;
    }
    if (step.write) {
      // A file written outside the tool (the game's pin inbox beside the project): an absolute path and its text.
      for (const { path, text } of step.write(state)) {
        mkdirSync(dirname(path), { recursive: true });
        writeFileSync(path, text);
      }
      answers.push({ step, touch: true });
      continue;
    }
    const params = typeof step.params === 'function' ? step.params(state) : step.params;
    if (verbose) console.error(`${core.name}: ${step.name} (${step.method})`);
    const started = performance.now();
    const text = await core.call(step.method, params);
    const milliseconds = performance.now() - started;
    const answer = JSON.parse(text);
    if (step.save && answer.result) step.save(answer.result, state);
    let compared = normalise(text, project);
    // A mesh's bytes are a file the answer names: its hash joins what the backends must agree on.
    if (step.method === 'view.mesh' && answer.result?.file) {
      const bytes = readFileSync(join(project, answer.result.file));
      const hash = createHash('sha256').update(bytes).digest('hex');
      compared = `${compared.slice(0, -1)},"mesh_sha256":"${hash}","mesh_bytes_match":${
        bytes.length === answer.result.bytes}}`;
    }
    answers.push({ step, params, text: compared, answer, milliseconds });
  }
  return answers;
}

async function main() {
  const work = mkdtempSync(join(tmpdir(), 'oymap_contract_'));
  const backends = [new NativeCore(nativePath)];
  if (wasmPath) backends.push(await WasmCore.load(wasmPath));
  if (workerPath) backends.push(await WorkerCore.load(workerPath, [work, resolve(studio, '..'), resolve(assets)]));
  const suites = [
    ...fixtures.filter((f) => !only || f.name === only).map((f) => ({ ...f, source: join(studio, f.source) })),
    ...extraProjects.map((p) => ({ name: resolve(p).split('/').slice(-2).join('_'), source: resolve(p),
      steps: readOnlySteps, extra: true })),
  ];
  let failures = 0;
  const timings = [];

  try {
    for (const core of backends) {
      const configured = JSON.parse(await core.call('session.configure', { asset_root: assets }));
      if (!configured.result) throw new Error(`${core.name}: session.configure failed: ${JSON.stringify(configured)}`);
    }

    for (const suite of suites) {
      const runs = [];
      for (const core of backends) {
        const project = freshCopy(suite.source, work, `${core.name}_${suite.name}`);
        runs.push({ core, answers: await runSteps(core, suite.steps, project) });
      }
      const expectedFile = join(here, 'expected', `${suite.name}.json`);
      const expected = !suite.extra && !record && existsSync(expectedFile)
        ? JSON.parse(readFileSync(expectedFile, 'utf8')) : null;
      const recorded = {};
      const revisionTokens = new Map();
      console.log(`\n${suite.name}`);

      suite.steps.forEach((step, index) => {
        if (step.touch || step.write) {
          console.log(`  -- ${step.name}`);
          return;
        }
        const problems = [];
        for (const { core, answers } of runs) {
          const { params, answer, text } = answers[index];
          const kind = answer.result ? 'result' : answer.error?.data?.kind;
          if (kind !== step.expect) {
            const first = answer.error?.data?.issues?.[0];
            const why = answer.error ? `: ${answer.error.message.split('\n')[0]}${
              first ? ` (first: ${first.file} ${first.path}: ${first.message})` : ''}` : '';
            problems.push(`${core.name}: expected ${step.expect}, got ${kind}${why}`);
          }
          for (const problem of checkAnswer(step.method, params, answer)) problems.push(`${core.name}: ${problem}`);
          void text;
        }
        const nativeText = withoutPointers(runs[0].answers[index].text, step.differs);
        for (const { core, answers } of runs.slice(1)) {
          const other = withoutPointers(answers[index].text, step.differs);
          if (other !== nativeText) {
            let at = 0;
            while (at < nativeText.length && nativeText[at] === other[at]) at += 1;
            problems.push(`${core.name} differs from native at byte ${at}: native ...${
              nativeText.slice(Math.max(0, at - 40), at + 60)}... ${core.name} ...${
              other.slice(Math.max(0, at - 40), at + 60)}...`);
          }
        }
        const key = `${String(index).padStart(2, '0')} ${step.name}`;
        recorded[key] = JSON.parse(withDatedRevisions(withoutPointers(runs[0].answers[index].text, step.differs),
          revisionTokens));
        if (expected && JSON.stringify(expected[key]) !== JSON.stringify(recorded[key])) {
          problems.push('native differs from the recorded answer (expected/; --record after checking the change)');
        }
        const times = runs.map(({ core, answers }) => `${core.name} ${answers[index].milliseconds.toFixed(1)} ms`);
        timings.push({ suite: suite.name, step: step.name, method: step.method,
          ...Object.fromEntries(runs.map(({ core, answers }) => [core.name, +answers[index].milliseconds.toFixed(2)])),
          bytes: runs[0].answers[index].text.length });
        console.log(`  ${problems.length ? 'FAIL' : 'ok  '} ${step.name} (${step.method}; ${times.join(', ')})`);
        for (const problem of problems) console.log(`         ${problem}`);
        failures += problems.length ? 1 : 0;
      });

      if (record && !suite.extra) {
        writeFileSync(expectedFile, `${JSON.stringify(recorded, null, 1)}\n`);
        console.log(`  recorded ${expectedFile}`);
      }
    }
  } finally {
    for (const core of backends) core.close();
    rmSync(work, { recursive: true, force: true });
  }

  if (timingsFile) writeFileSync(timingsFile, `${JSON.stringify(timings, null, 1)}\n`);
  console.log(failures ? `\n${failures} step(s) failed` : '\nall steps passed');
  process.exit(failures ? 1 : 0);
}

await main();
