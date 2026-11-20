#!/usr/bin/env node
// One MCP tool call from a shell, through the same server an MCP client talks to (for agents without an MCP
// connection, scripts and the agent evaluation):
//   node src/call.mjs --list                      the tools as a client sees them: name, description, input schema
//   node src/call.mjs <tool> '<json arguments>'   prints the result's text; an image is saved and its path printed
// Options after the arguments: --mount <folder>  --assets <root>  --game <binary>  --oymap <binary>
import { writeFile, mkdtemp } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { InMemoryTransport } from '@modelcontextprotocol/sdk/inMemory.js';
import { createMcpServer, readOptions } from './host.mjs';

const [name, ...rest] = process.argv.slice(2);
if (!name) {
  console.error("usage: call.mjs --list | <tool> '<json arguments>' [--mount <folder>] [--assets <root>]");
  process.exit(2);
}
const hasArguments = rest.length > 0 && !rest[0].startsWith('--');
const { server, core } = createMcpServer(readOptions(hasArguments ? rest.slice(1) : rest));
const [clientSide, serverSide] = InMemoryTransport.createLinkedPair();
await server.connect(serverSide);
const client = new Client({ name: 'oymap-call', version: '0' });
await client.connect(clientSide);
let failed = false;
if (name === '--list') {
  console.log(client.getInstructions());
  for (const tool of (await client.listTools()).tools) {
    console.log(`\n${tool.name}: ${tool.description}\n  arguments: ${JSON.stringify(tool.inputSchema.properties)}` +
      `\n  required: ${JSON.stringify(tool.inputSchema.required ?? [])}`);
  }
} else {
  const result = await client.callTool({ name, arguments: hasArguments ? JSON.parse(rest[0]) : {} });
  failed = result.isError === true;
  for (const part of result.content) {
    if (part.type === 'text') console.log(part.text);
    if (part.type === 'image') {
      const file = path.join(await mkdtemp(path.join(tmpdir(), 'oymap-image-')), 'image.png');
      await writeFile(file, Buffer.from(part.data, 'base64'));
      console.log(`image: ${file}`);
    }
  }
}
await client.close();
core.stop();
process.exit(failed ? 1 : 0);
