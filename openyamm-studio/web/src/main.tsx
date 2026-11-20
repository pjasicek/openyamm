// The web app's entry (S5_BROWSER_EDITOR.md 4.9): connects to the host that served the page, with the pairing token
// from the URL's fragment, and opens ?project=<key> when given.
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/global.css';
import './styles/views.css';
import { RpcClient, pairingToken, socketUrl } from './rpc/client.ts';
import { studio } from './state/store.ts';
import { Controller, probe } from './app/controller.ts';
import { StudioContext } from './ui/context.ts';
import { App } from './ui/Frame.tsx';

probe();
window.addEventListener('error', (event) => probe().errors.push(String(event.message)));
window.addEventListener('unhandledrejection', (event) => probe().errors.push(String(event.reason)));

let storage: Storage | null = null;
try
{
    storage = window.sessionStorage;
}
catch
{
    storage = null;
}
const client = new RpcClient({ url: socketUrl(location), token: pairingToken(location, storage) });
const controller = new Controller(client, studio);
controller.start();
probe().app = { store: studio, controller };

createRoot(document.getElementById('root')!).render(
    <StrictMode>
        <StudioContext.Provider value={{ store: studio, actions: controller, controller }}>
            <App />
        </StudioContext.Provider>
    </StrictMode>,
);
