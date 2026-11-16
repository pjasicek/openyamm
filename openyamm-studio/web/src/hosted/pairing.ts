// Pairing the hosted page with a local studio (S5c; S5_BROWSER_EDITOR.md 2.12, spike 5): for what needs the person's
// machine (Play here, playtests, jobs, agents), the page talks to `oymap studio` on 127.0.0.1. The browser asks the
// person first: Chrome and Firefox gate a public page's requests to this computer behind a local-network permission
// prompt. So pairing starts from a button, says the browser will ask, and reads the first request's fate: an answer
// is paired; a failure at once is "refused" (Chrome records a denial); a request that hangs is "waiting for your
// answer in the browser's prompt" (Firefox holds it open while its prompt is up).
//
// The person gives the address the studio printed (`oymap studio: http://127.0.0.1:8765/#token=...`): its port and
// token are kept in this tab's session storage, never put in a URL; the socket carries the token as a subprotocol.
import { tokenProtocols } from '../rpc/client.ts';

export interface Pairing
{
    port: number;
    token: string;
}

const KEY = 'oymap.paired';

export function readPairing(storage: Pick<Storage, 'getItem'> | null = safeStorage()): Pairing | null
{
    try
    {
        const value = JSON.parse(storage?.getItem(KEY) ?? 'null') as Pairing | null;
        return value && Number.isInteger(value.port) && typeof value.token === 'string' && value.token ? value : null;
    }
    catch
    {
        return null;
    }
}

export function writePairing(pairing: Pairing | null, storage: Pick<Storage, 'setItem' | 'removeItem'> | null = safeStorage()): void
{
    if (pairing)
    {
        storage?.setItem(KEY, JSON.stringify(pairing));
    }
    else
    {
        storage?.removeItem(KEY);
    }
}

function safeStorage(): Storage | null
{
    try
    {
        return window.sessionStorage;
    }
    catch
    {
        return null;
    }
}

// The port and token of what the person pasted: the studio's printed address, or "port token".
export function parsePairing(text: string): Pairing | null
{
    const trimmed = text.trim();
    const fromLink = /^https?:\/\/(?:127\.0\.0\.1|localhost):(\d+)\/?#token=([A-Za-z0-9_\-.~%]+)$/.exec(trimmed);
    if (fromLink)
    {
        return { port: Number(fromLink[1]), token: decodeURIComponent(fromLink[2]) };
    }
    const plain = /^(\d{2,5})\s+([A-Za-z0-9_\-.~]+)$/.exec(trimmed);
    return plain ? { port: Number(plain[1]), token: plain[2] } : null;
}

export type PairingState =
    | { state: 'trying' }
    | { state: 'waiting' }
    | { state: 'paired'; ms: number }
    | { state: 'refused'; message: string; ms: number }
    | { state: 'no_host'; message: string; ms: number };

// Tries the host: a WebSocket with the token, then session.hello. `onState` hears "waiting" when the first answer
// takes longer than `waitingMs` (the browser's prompt is up). Resolves with the outcome.
export function tryPairing(pairing: Pairing, onState: (state: PairingState) => void, options: { waitingMs?: number; timeoutMs?: number } = {}): Promise<PairingState>
{
    const started = performance.now();
    onState({ state: 'trying' });
    return new Promise((resolve) =>
    {
        let done = false;
        let opened = false;
        const finish = (state: PairingState) =>
        {
            if (done)
            {
                return;
            }
            done = true;
            clearTimeout(waiting);
            clearTimeout(timeout);
            try
            {
                socket?.close();
            }
            catch
            {
                // closed already
            }
            onState(state);
            resolve(state);
        };
        const waiting = setTimeout(() => !done && onState({ state: 'waiting' }), options.waitingMs ?? 1500);
        const timeout = setTimeout(() => finish({ state: 'no_host', ms: performance.now() - started,
            message: 'no answer: the browser\'s prompt was not answered, or no studio runs on that port' }), options.timeoutMs ?? 120000);
        let socket: WebSocket | null = null;
        try
        {
            socket = new WebSocket(`ws://127.0.0.1:${pairing.port}/rpc`, tokenProtocols(pairing.token));
        }
        catch (error)
        {
            finish({ state: 'refused', ms: performance.now() - started, message: error instanceof Error ? error.message : String(error) });
            return;
        }
        socket.onopen = () =>
        {
            opened = true;
            socket!.send(JSON.stringify({ jsonrpc: '2.0', id: 1, method: 'session.hello', params: {} }));
        };
        socket.onmessage = (event) =>
        {
            const answer = JSON.parse(String(event.data)) as { id?: number; result?: unknown };
            if (answer.id === 1)
            {
                finish(answer.result ? { state: 'paired', ms: performance.now() - started }
                    : { state: 'no_host', ms: performance.now() - started, message: 'the studio answered with an error' });
            }
        };
        socket.onclose = () =>
        {
            const ms = performance.now() - started;
            // Closed before it opened: the browser refused (the local-network permission denied, or not given in
            // Chrome, which fails at once), the token was wrong, or no studio listens there.
            finish(opened ? { state: 'no_host', ms, message: 'the studio closed the connection' }
                : { state: 'refused', ms, message: 'the browser or the studio refused the connection: allow this site to reach '
                    + 'devices on your local network (the site\'s settings), check the address and token, and that `oymap studio` runs' });
        };
    });
}
