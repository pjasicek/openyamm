import { describe, expect, it } from 'vitest';
import { pairingToken, RevisionCache, RpcCallError, RpcClient, socketUrl } from './client.ts';
import type { SocketLike } from './client.ts';

class FakeSocket implements SocketLike
{
    readyState = 0;
    sent: string[] = [];
    url: string;
    protocols: string[];
    onopen: ((event: unknown) => void) | null = null;
    onclose: ((event: unknown) => void) | null = null;
    onerror: ((event: unknown) => void) | null = null;
    onmessage: ((event: { data: unknown }) => void) | null = null;

    constructor(url: string, protocols: string[] = [])
    {
        this.url = url;
        this.protocols = protocols;
    }

    send(data: string): void
    {
        this.sent.push(data);
    }

    close(): void
    {
        this.onclose?.({});
    }

    open(): void
    {
        this.readyState = 1;
        this.onopen?.({});
    }

    answer(payload: object): void
    {
        const request = JSON.parse(this.sent.shift()!);
        this.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', id: request.id, ...payload }) });
    }
}

function connected(): { client: RpcClient; socket: FakeSocket }
{
    let socket!: FakeSocket;
    const client = new RpcClient({ url: 'ws://127.0.0.1:8765/rpc', token: 'tok en', reconnectMs: 0, createSocket: (url, protocols) => (socket = new FakeSocket(url, protocols)) });
    client.connect();
    return { client, socket };
}

describe('RpcClient', () =>
{
    it('sends the token as a subprotocol (never in the URL) and queues calls until the socket opens', async () =>
    {
        const { client, socket } = connected();
        expect(socket.url).toBe('ws://127.0.0.1:8765/rpc');
        expect(socket.protocols).toEqual(['oymap', 'oymap.token.746f6b20656e']);
        const answer = client.call('session.hello', {});
        expect(socket.sent).toEqual([]);
        socket.open();
        expect(JSON.parse(socket.sent[0])).toMatchObject({ jsonrpc: '2.0', method: 'session.hello', params: {} });
        socket.answer({ result: { core_version: '0.1.0' } });
        await expect(answer).resolves.toMatchObject({ core_version: '0.1.0' });
    });

    it('turns a typed refusal into an RpcCallError with its kind', async () =>
    {
        const { client, socket } = connected();
        socket.open();
        const answer = client.call('view.mesh', { project: 'x' });
        socket.answer({ error: { code: -32000, message: 'has errors', data: { kind: 'has_errors', issues: [] } } });
        const error = await answer.catch((e) => e);
        expect(error).toBeInstanceOf(RpcCallError);
        expect(error.kind).toBe('has_errors');
        expect(error.code).toBe(-32000);
    });

    it('fails the waiting calls when the socket closes and reports the state', async () =>
    {
        const { client, socket } = connected();
        const states: string[] = [];
        client.onState((state) => states.push(state));
        socket.open();
        const answer = client.call('project.open', { project: 'p' });
        socket.close();
        await expect(answer).rejects.toMatchObject({ kind: 'disconnected' });
        expect(states).toEqual(['open', 'closed']);
        await expect(client.call('session.hello', {})).rejects.toMatchObject({ kind: 'disconnected' });
    });
});

describe('notices', () =>
{
    it('gives each notice to its listeners, never to a waiting call, until they stop listening', async () =>
    {
        const { client, socket } = connected();
        socket.open();
        const pins: unknown[] = [];
        const revisions: unknown[] = [];
        const stop = client.onNotice('pins_changed', (notice) => pins.push(notice));
        client.onNotice('revision_changed', (notice) => revisions.push(notice.revision));
        const answer = client.call('pins.list', { project: 'p' });
        socket.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', method: 'pins_changed', params: { project: 'p', counter: 3 } }) });
        socket.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', id: null, method: 'revision_changed', params: { project: 'p', revision: 'ab', previous: null, author: 'agent:x', label: '', changes: [], entry: 2 } }) });
        expect(pins).toEqual([{ project: 'p', counter: 3 }]);
        expect(revisions).toEqual(['ab']);
        socket.answer({ result: { counter: 3, pins: [] } });
        await expect(answer).resolves.toEqual({ counter: 3, pins: [] });
        stop();
        socket.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', method: 'pins_changed', params: { project: 'p', counter: 4 } }) });
        expect(pins).toHaveLength(1);
    });

    it('ignores notices nobody listens to and messages that are neither', () =>
    {
        const { client, socket } = connected();
        socket.open();
        expect(() => socket.onmessage?.({ data: JSON.stringify({ jsonrpc: '2.0', method: 'client_joined', params: {} }) })).not.toThrow();
        expect(() => socket.onmessage?.({ data: 'not json' })).not.toThrow();
        expect(client.state).toBe('open');
    });
});

describe('pairing and cache', () =>
{
    it('takes the token from the fragment, then from session storage', () =>
    {
        const stored = new Map<string, string>();
        const storage = { getItem: (k: string) => stored.get(k) ?? null, setItem: (k: string, v: string) => void stored.set(k, v) };
        expect(pairingToken({ hash: '#token=abc' }, storage)).toBe('abc');
        expect(pairingToken({ hash: '' }, storage)).toBe('abc');
        expect(socketUrl({ protocol: 'http:', host: '127.0.0.1:8765' })).toBe('ws://127.0.0.1:8765/rpc');
    });

    it('keeps the latest entries by revision', () =>
    {
        const cache = new RevisionCache<number>(2);
        cache.set('a', 1);
        cache.set('b', 2);
        cache.get('a');
        cache.set('c', 3);
        expect(cache.get('b')).toBeUndefined();
        expect(cache.get('a')).toBe(1);
        expect(cache.get('c')).toBe(3);
    });
});
