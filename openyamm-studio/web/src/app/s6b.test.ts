// S6, the second run: the controller's world view and mods calls (world.view with the host's project keys; mod.list
// and mod.pack on the host's own mods folder; mod.map_number for a world or a mod, with the projects' numbers taken).
import { describe, expect, it } from 'vitest';
import { RpcClient } from '../rpc/client.ts';
import type { SocketLike } from '../rpc/client.ts';
import { makeStore } from '../state/store.ts';
import { Controller } from './controller.ts';

const page = globalThis as unknown as Record<string, unknown>;
page.window ??= globalThis;
page.location ??= { href: 'http://127.0.0.1:8765/', search: '' };
page.history ??= { replaceState: () => undefined };

type Handler = (params: Record<string, unknown>) => unknown;

class Host implements SocketLike
{
    readyState = 0;
    calls: { method: string; params: Record<string, unknown> }[] = [];
    onopen: ((event: unknown) => void) | null = null;
    onclose: ((event: unknown) => void) | null = null;
    onerror: ((event: unknown) => void) | null = null;
    onmessage: ((event: { data: unknown }) => void) | null = null;

    readonly handlers: Record<string, Handler>;

    constructor(handlers: Record<string, Handler>)
    {
        this.handlers = handlers;
        setTimeout(() =>
        {
            this.readyState = 1;
            this.onopen?.({});
        }, 0);
    }

    send(data: string): void
    {
        const request = JSON.parse(data);
        this.calls.push({ method: request.method, params: request.params });
        const handler = this.handlers[request.method];
        setTimeout(() =>
        {
            let answer: object;
            try
            {
                answer = handler ? { result: handler(request.params) } : { error: { code: -32601, message: 'no', data: { kind: 'unknown_method' } } };
            }
            catch (error)
            {
                answer = { error: { code: -32000, message: (error as Error).message, data: { kind: 'bad_request' } } };
            }
            this.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', id: request.id, ...answer }) });
        }, 0);
    }

    close(): void
    {
        this.onclose?.({});
    }
}

const tick = (ms = 5) => new Promise((resolve) => setTimeout(resolve, ms));

describe('the world view and the mods in the controller (S6)', () =>
{
    it('asks for the world view of the listed projects, the mods folder, a map number and a pack', async () =>
    {
        let host!: Host;
        const handlers: Record<string, Handler> = {
            'host.projects': () => ({ projects: [
                { key: 'devdocs/xeen/briefs/x1/L4', name: 'Vertigo Meadows', id: 'xeen_x1', kind: 'outdoor', world: 'mm7', root: 1 },
                { key: 'devdocs/xeen/briefs/xd01/L4', name: 'Joe\'s Warehouse', id: 'xeen_xd01', kind: 'indoor', world: 'mm7', root: 1 },
            ], roots: ['devdocs/map_studio/briefs', 'devdocs/xeen/briefs'] }),
            'world.view': (params) => ({ worlds: [{ world: 'mm7', maps: [], links: [] }], skipped: [], echo: params }),
            'mod.list': () => ({ merged: [], named: [{ id: 'lofts', name: 'The lofts', version: '1.0', enabled: false, maps: 2, map_numbers: [9470], map_range: [9470, 9479] }] }),
            'mod.map_number': (params) =>
            {
                if (params.mod === 'nothing')
                {
                    throw new Error('no mod nothing in the mods folder');
                }
                return { number: params.mod ? 9471 : 9400, range: params.mod ? [9470, 9479] : [9400, 9999], from: params.mod ? `mod:${String(params.mod)}` : 'studio', taken: 1, warnings: [] };
            },
            'mod.pack': (params) => ({ id: params.id, files: ['mod.yml'], maps: [], tables: [], warnings: [] }),
        };
        const client = new RpcClient({ url: 'ws://h/rpc', token: 't', reconnectMs: 0, createSocket: () => (host = new Host(handlers)) });
        const store = makeStore();
        const controller = new Controller(client, store);
        client.connect();
        await tick(20);
        expect(store.getState().projects.state).toBe('ready');

        const world = await controller.worldView();
        expect(typeof world).toBe('object');
        const keys = ['devdocs/xeen/briefs/x1/L4', 'devdocs/xeen/briefs/xd01/L4'];
        expect(host.calls.find((call) => call.method === 'world.view')!.params).toEqual({ projects: keys });

        const mods = await controller.listMods();
        expect(typeof mods === 'object' && mods.named[0]!.map_range).toEqual([9470, 9479]);
        expect(host.calls.find((call) => call.method === 'mod.list')!.params).toEqual({ mods: 'default' });

        const ofWorld = await controller.mapNumber('mm7');
        expect(typeof ofWorld === 'object' && ofWorld.from).toBe('studio');
        const ofMod = await controller.mapNumber('mm7', 'lofts');
        expect(typeof ofMod === 'object' && ofMod.number).toBe(9471);
        expect(host.calls.filter((call) => call.method === 'mod.map_number').map((call) => call.params)).toEqual([
            { world: 'mm7', mods: 'default', projects: keys },
            { world: 'mm7', mods: 'default', projects: keys, mod: 'lofts' },
        ]);
        // A refusal comes back as its words.
        expect(await controller.mapNumber('mm7', 'nothing')).toBe('no mod nothing in the mods folder');

        const packed = await controller.packMod({ projects: keys, id: 'xeen', name: 'Xeen', maps: [9130, 9139] });
        expect(typeof packed === 'object' && packed.id).toBe('xeen');
        expect(host.calls.find((call) => call.method === 'mod.pack')!.params).toEqual({ projects: keys, id: 'xeen', out: 'default', name: 'Xeen', maps: [9130, 9139] });
    });
});
