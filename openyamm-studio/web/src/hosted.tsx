// The hosted page's entry (S5c; S5_BROWSER_EDITOR.md 2.2 "Hosted mode", 4.14): the same app as local mode, over the
// WebAssembly core in the page's worker (hosted/client.ts) instead of a host. When the person paired the page with a
// local studio (hosted/Pairing.tsx), it talks to that host instead, as local mode does, with the host's address and
// token kept in this tab's session storage (never in the URL).
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/global.css';
import './styles/views.css';
import { RpcClient } from './rpc/client.ts';
import type { StudioClient } from './rpc/client.ts';
import { HostedClient } from './hosted/client.ts';
import { readPairing } from './hosted/pairing.ts';
import { studio } from './state/store.ts';
import { Controller, probe } from './app/controller.ts';
import { StudioContext } from './ui/context.ts';
import { App } from './ui/Frame.tsx';
import { registerOffline } from './hosted/offline.ts';

probe();
window.addEventListener('error', (event) => probe().errors.push(String(event.message)));
window.addEventListener('unhandledrejection', (event) => probe().errors.push(String(event.reason)));

let version = 'dev';
try
{
    const answer = await fetch(new URL('./version.json', location.href), { cache: 'no-cache' });
    if (answer.ok)
    {
        version = String((await answer.json() as { version?: string }).version ?? 'dev');
    }
}
catch
{
    // a development build without the staged version file
}

const coreUrl = new URL('./core/oymap_worker.mjs', location.href).href;
const pairing = readPairing();
const client: StudioClient = pairing
    ? new RpcClient({ url: `ws://127.0.0.1:${pairing.port}/rpc`, token: pairing.token, byteBase: `http://127.0.0.1:${pairing.port}`,
        coreUrl, mode: 'paired', reconnectMs: 0 })
    : new HostedClient({ coreUrl, version });
const controller = new Controller(client, studio);
controller.start();
probe().app = { store: studio, controller };
probe().hosted = { version, client };
registerOffline(version);

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <StudioContext.Provider value={{ store: studio, actions: controller, controller }}>
            <App />
        </StudioContext.Provider>
    </StrictMode>,
);
