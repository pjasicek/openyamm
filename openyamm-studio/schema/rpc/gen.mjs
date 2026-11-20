#!/usr/bin/env node
// The RPC catalogue's checker and type generator (S5_BROWSER_EDITOR.md 2.3). Plain Node, no dependencies.
//
//   node schema/rpc/gen.mjs           lint the catalogue and write generated/rpc.ts
//   node schema/rpc/gen.mjs --check   lint, and fail when generated/rpc.ts is not what the catalogue gives
//
// Lint rules (the rules of the list, common.rpc.json): every method states its metadata; params and results are
// closed objects (additionalProperties false) except trees marked x-tree and maps whose additionalProperties is a
// schema; every non-integer number in a result carries x-decimals; every $ref resolves; error kinds exist.
import { readFileSync, readdirSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const projectSchemaDir = join(here, '..');
const outFile = join(here, 'generated', 'rpc.ts');

const files = new Map();
for (const name of readdirSync(here).filter((n) => n.endsWith('.rpc.json')).sort()) {
  files.set(name, JSON.parse(readFileSync(join(here, name), 'utf8')));
}
for (const name of readdirSync(projectSchemaDir).filter((n) => n.endsWith('.schema.json')).sort()) {
  files.set(name, JSON.parse(readFileSync(join(projectSchemaDir, name), 'utf8')));
}

const problems = [];
const problem = (where, text) => problems.push(`${where}: ${text}`);

// --- references ---------------------------------------------------------------------------------------------------

function splitRef(ref, fromFile) {
  const hash = ref.indexOf('#');
  const file = hash < 0 ? ref : ref.slice(0, hash);
  const pointer = hash < 0 ? '' : ref.slice(hash + 1);
  return { file: file || fromFile, pointer };
}

function lookup(file, pointer) {
  let node = files.get(file);
  if (node === undefined) return undefined;
  for (const part of pointer.split('/').filter(Boolean)) {
    node = node?.[part.replaceAll('~1', '/').replaceAll('~0', '~')];
  }
  return node;
}

// --- lint ---------------------------------------------------------------------------------------------------------

const common = files.get('common.rpc.json');
const errorKinds = Object.keys(common.$defs.errors);
const metaValues = {
  lane: ['interactive', 'jobs', 'host'],
  writes: ['none', 'record', 'project', 'mount'],
  assets: ['none', 'optional', 'required'],
};

function lintSchema(schema, file, where, inResult, seen) {
  if (schema === undefined || schema === null || typeof schema !== 'object') return;
  if (schema.$ref) {
    const { file: target, pointer } = splitRef(schema.$ref, file);
    const resolved = lookup(target, pointer);
    if (resolved === undefined) {
      problem(where, `$ref ${schema.$ref} does not resolve`);
      return;
    }
    // References into the project format are that format's business (its own schemas and lint).
    if (!target.endsWith('.rpc.json')) return;
    const key = `${target}#${pointer}:${inResult}`;
    if (seen.has(key)) return;
    seen.add(key);
    lintSchema(resolved, target, `${where} -> ${schema.$ref}`, inResult, seen);
    return;
  }
  const types = [].concat(schema.type ?? []);
  const isObject = types.includes('object') || schema.properties !== undefined;
  if (isObject && !schema['x-tree']) {
    const additional = schema.additionalProperties;
    if (additional !== false && (typeof additional !== 'object' || additional === null)) {
      problem(where, 'an object must be closed (additionalProperties: false), a map (additionalProperties: <schema>) '
        + 'or a tree (x-tree: true)');
    }
  }
  if (inResult && types.includes('number') && !Number.isInteger(schema['x-decimals'])) {
    problem(where, 'a number in a result needs x-decimals (the core rounds to it), or type integer');
  }
  for (const [name, child] of Object.entries(schema.properties ?? {})) {
    lintSchema(child, file, `${where}.${name}`, inResult, seen);
  }
  if (typeof schema.additionalProperties === 'object') {
    lintSchema(schema.additionalProperties, file, `${where}.*`, inResult, seen);
  }
  if (schema.items) lintSchema(schema.items, file, `${where}[]`, inResult, seen);
  for (const keyword of ['oneOf', 'anyOf']) {
    (schema[keyword] ?? []).forEach((branch, index) => lintSchema(branch, file, `${where}.${keyword}[${index}]`,
      inResult, seen));
  }
}

const methods = [];
for (const [file, document] of files) {
  if (!file.endsWith('.rpc.json') || !document.methods) continue;
  const group = document['x-group'];
  if (group !== file.replace('.rpc.json', '')) problem(file, `x-group must be "${file.replace('.rpc.json', '')}"`);
  for (const [name, method] of Object.entries(document.methods)) {
    const where = `${group}.${name}`;
    if (!/^[a-z][a-z_]*$/.test(name)) problem(where, 'a method name is lower case with underscores');
    for (const key of ['summary', 'since', 'lane', 'backends', 'exposed', 'writes', 'assets', 'errors', 'params',
      'result']) {
      if (method[key] === undefined) problem(where, `missing ${key}`);
    }
    for (const [key, allowed] of Object.entries(metaValues)) {
      if (method[key] !== undefined && !allowed.includes(method[key])) problem(where, `${key} is one of ${allowed}`);
    }
    for (const kind of method.errors ?? []) {
      if (!errorKinds.includes(kind)) problem(where, `unknown error kind ${kind}`);
    }
    lintSchema(method.params, file, `${where} params`, false, new Set());
    lintSchema(method.result, file, `${where} result`, true, new Set());
    methods.push({ group, name, full: where, file, method });
  }
  // Definitions no method names but clients read (x-export: the jobs' output schemas) are results too.
  for (const [name, schema] of Object.entries(document.$defs ?? {})) {
    if (schema['x-export']) lintSchema(schema, file, `${file} $defs/${name}`, true, new Set());
  }
}

if (problems.length > 0) {
  console.error(`the RPC catalogue has ${problems.length} problem(s):\n  ${problems.join('\n  ')}`);
  process.exit(1);
}

// --- TypeScript ---------------------------------------------------------------------------------------------------

const pascal = (text) => text.split(/[^A-Za-z0-9]+/).filter(Boolean)
  .map((part) => part[0].toUpperCase() + part.slice(1)).join('');
const identifier = (key) => (/^[A-Za-z_$][A-Za-z0-9_$]*$/.test(key) ? key : JSON.stringify(key));

// Named types: every $defs entry of the catalogue (common.rpc.json's errors as Error<Kind>).
const named = new Map();
const declarations = [];
function typeNameOf(file, pointer) {
  const parts = pointer.split('/').filter(Boolean);
  if (parts[0] !== '$defs') return null;
  if (parts.length === 3 && parts[1] === 'errors') return `Error${pascal(parts[2])}`;
  return parts.length === 2 ? pascal(parts[1]) : null;
}

function jsDoc(text, indent) {
  if (!text) return '';
  const lines = [];
  let line = '';
  for (const word of text.split(/\s+/)) {
    if (line.length + word.length + 1 > 110 - indent.length) {
      lines.push(line);
      line = word;
    } else {
      line = line ? `${line} ${word}` : word;
    }
  }
  if (line) lines.push(line);
  return lines.length === 1 ? `${indent}/** ${lines[0]} */\n`
    : `${indent}/**\n${lines.map((l) => `${indent} * ${l}`).join('\n')}\n${indent} */\n`;
}

function refType(ref, file, indent) {
  const { file: target, pointer } = splitRef(ref, file);
  if (target.endsWith('.rpc.json')) {
    const name = typeNameOf(target, pointer);
    if (name) {
      const key = `${target}#${pointer}`;
      if (!named.has(key)) {
        if ([...named.values()].includes(name)) throw new Error(`two catalogue types named ${name}`);
        named.set(key, name);
        const schema = lookup(target, pointer);
        const body = tsType(schema, target, '');
        declarations.push({ name, text: `${jsDoc(schema.description, '')}export type ${name} = ${body};\n` });
      }
      return named.get(key);
    }
  }
  // References into the project format, and to anything but a $def, are written out in place.
  return tsType(lookup(target, pointer), target, indent);
}

function tsType(schema, file, indent) {
  if (schema === undefined || schema === true) return 'JsonValue';
  if (schema.$ref) return refType(schema.$ref, file, indent);
  if (schema['x-tree']) {
    if (schema.type !== 'object') return 'JsonValue';
    // A tree with some fields fixed (an added object's id): those fields, and anything else.
    const fixed = Object.keys(schema.properties ?? {}).length > 0
      ? tsType({ ...schema, 'x-tree': undefined, additionalProperties: false }, file, indent) : null;
    return fixed ? `${fixed} & JsonObject` : 'JsonObject';
  }
  if (schema.const !== undefined) return JSON.stringify(schema.const);
  if (schema.enum) return schema.enum.map((value) => JSON.stringify(value)).join(' | ');
  const branches = schema.oneOf ?? schema.anyOf;
  const typed = schema.type !== undefined || schema.properties !== undefined;
  if (branches && !typed) return branches.map((branch) => tsType(branch, file, indent)).join(' | ');
  const types = [].concat(schema.type ?? (schema.properties ? 'object' : []));
  if (types.length === 0) return 'JsonValue';
  const one = (type) => {
    switch (type) {
      case 'string': return 'string';
      case 'integer':
      case 'number': return 'number';
      case 'boolean': return 'boolean';
      case 'null': return 'null';
      case 'array': {
        const item = tsType(schema.items, file, indent);
        if (schema.minItems !== undefined && schema.minItems === schema.maxItems && schema.minItems <= 4) {
          return `[${Array(schema.minItems).fill(item).join(', ')}]`;
        }
        return /[|&]/.test(item) ? `(${item})[]` : `${item}[]`;
      }
      case 'object': {
        const inner = `${indent}  `;
        const required = new Set(schema.required ?? []);
        let text = '';
        for (const [key, child] of Object.entries(schema.properties ?? {})) {
          const description = child.description
            ?? (child.$ref ? undefined : undefined);
          text += jsDoc(description, inner);
          text += `${inner}${identifier(key)}${required.has(key) ? '' : '?'}: ${tsType(child, file, inner)};\n`;
        }
        if (typeof schema.additionalProperties === 'object') {
          text += `${inner}[key: string]: ${tsType(schema.additionalProperties, file, inner)};\n`;
        }
        return text ? `{\n${text}${indent}}` : 'Record<string, never>';
      }
      default: throw new Error(`no TypeScript for type ${type}`);
    }
  };
  return types.map(one).join(' | ');
}

let methodTypes = '';
let methodMap = '';
let methodTable = '';
for (const { group, name, full, file, method } of methods) {
  const base = `${pascal(group)}${pascal(name)}`;
  const paramsType = tsType(method.params, file, '');
  const resultType = tsType(method.result, file, '');
  methodTypes += `${jsDoc(`${full}: ${method.summary}`, '')}export type ${base}Params = ${paramsType};\n`;
  methodTypes += `export type ${base}Result = ${resultType};\n\n`;
  const errors = method.errors.length ? method.errors.map((kind) => JSON.stringify(kind)).join(' | ') : 'never';
  methodMap += `  ${JSON.stringify(full)}: { params: ${base}Params; result: ${base}Result; errors: ${errors} };\n`;
  const literal = (value) => (Array.isArray(value) ? `[${value.map(literal).join(', ')}]` : JSON.stringify(value));
  const meta = { since: method.since, lane: method.lane, backends: method.backends, exposed: method.exposed,
    writes: method.writes, assets: method.assets };
  methodTable += `  ${JSON.stringify(full)}: { ${Object.entries(meta).map(([k, v]) => `${k}: ${literal(v)}`)
    .join(', ')} },\n`;
}
// The error data union, declared through the common definition.
const errorDataType = refType('common.rpc.json#/$defs/error_data', 'common.rpc.json', '');
// Definitions no method names but clients read (marked x-export: the jobs' output schemas), declared too.
for (const [file, document] of files) {
  if (!file.endsWith('.rpc.json')) continue;
  for (const [name, schema] of Object.entries(document.$defs ?? {})) {
    if (schema['x-export']) refType(`#/$defs/${name}`, file, '');
  }
}

const text = `// Generated by openyamm-studio/schema/rpc/gen.mjs from schema/rpc/*.rpc.json: do not edit.
// The typed request list of the studio core (devdocs/map_studio/S5_BROWSER_EDITOR.md 2.3).

export const RPC_VERSION = ${common['x-rpc-version']};

export type JsonValue = string | number | boolean | null | JsonValue[] | { [key: string]: JsonValue };
export type JsonObject = { [key: string]: JsonValue };

${declarations.map((d) => d.text).join('\n')}
${methodTypes}export interface RpcMethods {
${methodMap}}

export type RpcMethodName = keyof RpcMethods;
export type RpcErrorKind = ${errorDataType}['kind'];
/** Errors any method may answer besides its own. */
export type RpcCommonErrorKind = 'unknown_method' | 'invalid_params' | 'failed';

export interface RpcError<K extends RpcErrorKind = RpcErrorKind> {
  code: number;
  message: string;
  data: Extract<${errorDataType}, { kind: K }>;
}

/** What oymap_call returns and what a JSON-RPC response carries besides its id. */
export type RpcAnswer<M extends RpcMethodName> =
  | { result: RpcMethods[M]['result'] }
  | { error: RpcError<RpcMethods[M]['errors'] | RpcCommonErrorKind> };

/** Each method's metadata: the host's allow-list passes on only exposed methods. */
export const RPC_METHODS = {
${methodTable}} as const;
`;

if (process.argv.includes('--check')) {
  let current = '';
  try {
    current = readFileSync(outFile, 'utf8');
  } catch {
    // missing: differs
  }
  if (current !== text) {
    console.error(`${outFile} is not what the catalogue gives: run node schema/rpc/gen.mjs`);
    process.exit(1);
  }
  console.log(`catalogue: ${methods.length} methods, lint clean; generated/rpc.ts up to date`);
} else {
  mkdirSync(dirname(outFile), { recursive: true });
  writeFileSync(outFile, text);
  console.log(`catalogue: ${methods.length} methods, lint clean; wrote ${outFile}`);
}
