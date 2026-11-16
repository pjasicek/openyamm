// Walk mode's worker (S5_BROWSER_EDITOR.md 2.2, 2.10; D7): the WebAssembly core in a Web Worker, serving the request
// list's walk.* methods through oymap_call. The host serves the core at /core/ and the walk's files at /walk/ (with
// the pairing token); the worker copies them into the core's in-memory file system and names them in walk.load, as
// the native core takes paths of its own. Every call goes through the request list, so the browser walks with the
// same code, the same checks and the same answers as the contract suite's recorded walk.
import type { WalkRequest, WalkReply } from './protocol.ts';

interface CoreModule
{
    _oymap_call(method: number, params: number): number;
    _oymap_free(text: number): void;
    _free(pointer: number): void;
    stringToNewUTF8(text: string): number;
    UTF8ToString(pointer: number): string;
    FS: { mkdirTree(path: string): void; writeFile(path: string, data: Uint8Array): void };
}

const scope = self as unknown as { postMessage(message: WalkReply): void; onmessage: ((event: MessageEvent<WalkRequest>) => void) | null };
let core: CoreModule | null = null;

async function loadCore(coreUrl?: string): Promise<CoreModule>
{
    if (!core)
    {
        // The host's /core/, or where the page says (a hosted page paired with a host loads its own copy).
        const url = coreUrl ?? new URL('/core/oymap_worker.mjs', self.location.origin).href;
        const module = await import(/* @vite-ignore */ url) as { default: (options?: object) => Promise<CoreModule> };
        core = await module.default();
    }
    return core;
}

// One call of the request list: {result} or {error}, as the native core answers.
function call(module: CoreModule, method: string, params: unknown): { result?: unknown; error?: { message: string; data?: { kind?: string } } }
{
    const methodText = module.stringToNewUTF8(method);
    const paramsText = module.stringToNewUTF8(JSON.stringify(params));
    const answer = module._oymap_call(methodText, paramsText);
    const text = module.UTF8ToString(answer);
    module._oymap_free(answer);
    module._free(methodText);
    module._free(paramsText);
    return JSON.parse(text);
}

async function fetchInto(module: CoreModule, url: string, token: string, path: string): Promise<number>
{
    const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
    if (!response.ok)
    {
        throw new Error(`${url}: ${response.status} ${response.statusText}`);
    }
    const bytes = new Uint8Array(await response.arrayBuffer());
    module.FS.writeFile(path, bytes);
    return bytes.length;
}

scope.onmessage = async (event) =>
{
    const request = event.data;
    try
    {
        if (request.type === 'load')
        {
            const started = performance.now();
            const module = await loadCore(request.coreUrl);
            const coreMs = performance.now() - started;
            module.FS.mkdirTree('/walk');
            const fetchStarted = performance.now();
            const names = { map: '/walk/map', state: '/walk/state.yml', decorations: '/walk/decoration_data.txt', terrain: '/walk/terrain' };
            let bytes = 0;
            bytes += await fetchInto(module, request.files.map, request.token, names.map);
            bytes += await fetchInto(module, request.files.state, request.token, names.state);
            bytes += await fetchInto(module, request.files.decorations, request.token, names.decorations);
            if (request.files.terrain)
            {
                bytes += await fetchInto(module, request.files.terrain, request.token, names.terrain);
            }
            const fetchMs = performance.now() - fetchStarted;
            const loadStarted = performance.now();
            const answer = call(module, 'walk.load', { map: names.map, state: names.state, decorations: names.decorations,
                ...(request.files.terrain ? { terrain: names.terrain } : {}) });
            const loadMs = performance.now() - loadStarted;
            scope.postMessage({ id: request.id, answer, timing: { coreMs, fetchMs, loadMs, bytes } });
            return;
        }
        const module = await loadCore();
        const started = performance.now();
        const answer = call(module, request.method, request.params);
        scope.postMessage({ id: request.id, answer, timing: { callMs: performance.now() - started } });
    }
    catch (error)
    {
        scope.postMessage({ id: request.id, answer: { error: { message: error instanceof Error ? error.message : String(error), data: { kind: 'failed' } } } });
    }
};
