// The hosted page's start (S5c; S5_BROWSER_EDITOR.md 1.3 F3, 2.11, 2.12; PLAN.md 9 "What each mode can do"): what this
// browser can do (the capability table), the game's files (a player's install, its packages, or a checkout's
// assets_dev), a project (a folder, a zip, a working copy kept in this browser, or a new one), and pairing with a
// local studio for what needs the person's machine. Shown instead of the host's project list.
import { useEffect, useRef, useState } from 'react';
import type { ChangeEvent } from 'react';
import { useS, useStudioContext } from '../ui/context.ts';
import type { HostedClient } from './client.ts';
import type { InstallSummary, Picked } from './protocol.ts';
import { parsePairing, tryPairing, writePairing } from './pairing.ts';
import type { PairingState } from './pairing.ts';
import { probe } from '../app/controller.ts';
import css from './Hosted.module.css';

interface Capabilities
{
    folders: boolean;
    browserStorage: boolean;
    bc: boolean;
    webgl2: boolean;
    pairing: boolean;
}

export function detectCapabilities(): Capabilities
{
    let webgl2 = false;
    let bc = false;
    try
    {
        const gl = document.createElement('canvas').getContext('webgl2');
        webgl2 = gl !== null;
        bc = Boolean(gl?.getExtension('WEBGL_compressed_texture_s3tc') && gl?.getExtension('EXT_texture_compression_bptc'));
        gl?.getExtension('WEBGL_lose_context')?.loseContext();
    }
    catch
    {
        webgl2 = false;
    }
    const safari = /^((?!chrome|android|crios|fxios).)*safari/i.test(navigator.userAgent);
    return {
        folders: typeof (window as unknown as { showDirectoryPicker?: unknown }).showDirectoryPicker === 'function',
        browserStorage: typeof navigator.storage?.getDirectory === 'function',
        bc, webgl2, pairing: !safari,
    };
}

const megabytes = (bytes: number) => `${(bytes / 1048576).toFixed(bytes < 10485760 ? 1 : 0)} MB`;
const gigabytes = (bytes: number) => `${(bytes / 1073741824).toFixed(2)} GB`;

// The picked files, and the input emptied: a file input keeps its selection in the page's form state, which the
// browser copies into the history entry on every address change (Chrome spent seconds per change on an 81 000-file
// checkout, S8f). The File objects stay readable.
function filesOf(event: ChangeEvent<HTMLInputElement>): { path: string; file: File }[]
{
    const files = Array.from(event.target.files ?? []).map((file) => ({ path: file.webkitRelativePath || file.name, file }));
    event.target.value = '';
    return files;
}

async function pickFolder(mode: 'read' | 'readwrite'): Promise<FileSystemDirectoryHandle | null>
{
    const picker = (window as unknown as { showDirectoryPicker?: (options: object) => Promise<FileSystemDirectoryHandle> }).showDirectoryPicker;
    if (!picker)
    {
        return null;
    }
    try
    {
        return await picker({ mode });
    }
    catch
    {
        // the person closed the picker
        return null;
    }
}

export function HostedStart()
{
    const { controller, store } = useStudioContext();
    const client = controller?.client as HostedClient | undefined;
    const projects = useS((s) => s.projects);
    const connection = useS((s) => s.connection);
    const [caps] = useState(detectCapabilities);
    const [install, setInstall] = useState<InstallSummary | null>(client?.install ?? null);
    const [busy, setBusy] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [copies, setCopies] = useState<string[]>([]);
    const [keepCopy, setKeepCopy] = useState(caps.browserStorage);
    const [heap, setHeap] = useState<string>('');

    const refreshCopies = () => client?.browserProjects().then(setCopies, () => setCopies([]));
    useEffect(() =>
    {
        if (connection === 'open')
        {
            void refreshCopies();
        }
    }, [connection]);
    const showHeap = () => client?.stats().then((stats) => setHeap(`core memory ${megabytes(stats.heap.memory)} (in use ${megabytes(stats.heap.live)})`), () => undefined);

    if (!client)
    {
        return null;
    }
    const run = async (what: string, work: () => Promise<void>) =>
    {
        setBusy(what);
        setError(null);
        try
        {
            await work();
        }
        catch (failure)
        {
            setError(failure instanceof Error ? failure.message : String(failure));
        }
        finally
        {
            setBusy(null);
            void showHeap();
        }
    };
    // From the pick (the input's change, or the picker's answer) to the mounted root: what the person waits for.
    const openAssets = (picked: Picked) => run('Reading the game\'s files…', async () =>
    {
        const started = performance.now();
        const opened = await client.openAssets(picked);
        probe().assetsOpenMs = performance.now() - started;
        setInstall(opened);
    });
    const opened = (key: string, kind: string, fresh = false) =>
    {
        controller!.listProjects();
        controller!.openProject(key);
        if (fresh)
        {
            store.setState({ mode: 'author', stage: 2, tool: kind === 'outdoor' ? 'spots' : 'room' });
        }
        void refreshCopies();
    };
    const openProject = (picked: Parameters<HostedClient['openProject']>[0], place: 'folder' | 'browser' | 'memory', name: string) =>
        run('Opening the project…', async () =>
        {
            const project = await client.openProject(picked, place, name);
            opened(project.key, project.kind);
        });

    return (
        <main className={css.page} data-testid="hosted-start">
            <h1 className={css.heading}>Map Studio <span className={css.badge}>in the browser</span></h1>
            <p className={css.lead}>The studio's core runs in this page: nothing is uploaded, the game's files and your projects are read
                where they are. Play here, playtests and agents need the studio on your computer: pair with it below.</p>

            <Capabilities caps={caps} />

            <section className={css.step}>
                <h2>1. The game's files</h2>
                <p className={css.dim}>Pick the OpenYAMM folder of your installed game (the one with <code>app</code> and <code>assets</code>),
                    or a repository's <code>assets_dev</code>. The packages are read by range, never loaded whole.</p>
                <div className={css.buttons}>
                    {caps.folders ? (
                        <button type="button" className={css.primary} disabled={busy !== null || connection !== 'open'} data-testid="pick-install"
                            onClick={() => void pickFolder('read').then((handle) => handle && openAssets({ kind: 'handle', handle, writable: false }))}>Choose the game's folder…</button>
                    ) : null}
                    <label className={css.button}>Choose a folder (upload picker)…
                        <input type="file" className={css.hidden} data-testid="install-input" {...{ webkitdirectory: '', directory: '' }}
                            onChange={(event) => openAssets({ kind: 'files', files: filesOf(event) })} />
                    </label>
                    <label className={css.button}>Choose package files (.zip)…
                        <input type="file" className={css.hidden} multiple accept=".zip,.json" data-testid="packages-input"
                            onChange={(event) => openAssets({ kind: 'files', files: filesOf(event) })} />
                    </label>
                </div>
                {install ? (
                    <p className={css.good} data-testid="install-summary">
                        {install.kind === 'install' ? `Installed game, release ${install.release ?? '?'}: ${install.packages} content packs`
                            : install.kind === 'packages' ? `${install.packages} packages` : 'A development tree'}
                        {` · ${install.entries.toLocaleString()} files in ${gigabytes(install.bytes)} · worlds ${install.worlds.join(', ')} · read in ${Math.round(install.ms)} ms`}
                    </p>
                ) : <p className={css.dim}>Not chosen yet: projects open without it, but building, textures and the library need it.</p>}
            </section>

            <section className={css.step}>
                <h2>2. A project</h2>
                <div className={css.buttons}>
                    {caps.folders ? (
                        <button type="button" className={css.primary} disabled={busy !== null || connection !== 'open'} data-testid="pick-project"
                            onClick={() => void pickFolder('readwrite').then((handle) => handle && openProject({ kind: 'handle', handle, writable: true }, 'folder', handle.name))}>
                            Open a project folder…</button>
                    ) : null}
                    <label className={css.button}>{caps.folders ? 'Open a folder read only…' : 'Open a project folder…'}
                        <input type="file" className={css.hidden} data-testid="project-input" {...{ webkitdirectory: '', directory: '' }}
                            onChange={(event) =>
                            {
                                const files = filesOf(event);
                                const name = files[0]?.path.split('/')[0] ?? 'project';
                                openProject({ kind: 'files', files }, keepCopy ? 'browser' : 'memory', name);
                            }} />
                    </label>
                    <label className={css.button}>Open a project zip…
                        <input type="file" className={css.hidden} accept=".zip" data-testid="project-zip"
                            onChange={(event) =>
                            {
                                const file = event.target.files?.[0];
                                event.target.value = '';
                                if (file)
                                {
                                    openProject({ kind: 'zip', file }, keepCopy ? 'browser' : 'memory', file.name.replace(/\.zip$/i, ''));
                                }
                            }} />
                    </label>
                </div>
                {caps.browserStorage ? (
                    <label className={css.check}><input type="checkbox" checked={keepCopy} onChange={(event) => setKeepCopy(event.target.checked)} />
                        Keep a working copy in this browser of what is opened read only (your folder or zip is never changed; export a zip to take it out)</label>
                ) : null}
                {copies.length > 0 ? (
                    <p className={css.copies}>Working copies in this browser: {copies.map((name) => (
                        <button key={name} type="button" className={css.link} disabled={busy !== null}
                            onClick={() => openProject({ kind: 'browser', name }, 'browser', name)}>{name}</button>
                    ))}</p>
                ) : null}
                <NewHostedProject client={client} caps={caps} disabled={busy !== null || connection !== 'open'}
                    onMade={(key, kind) => opened(key, kind, true)} onError={setError} />
                <ImportShippedMap client={client} caps={caps} disabled={busy !== null || connection !== 'open' || !install}
                    onMade={(key) => opened(key, 'overlay')} onError={setError} />
                {projects.state === 'ready' && projects.value.length > 0 ? (
                    <table className={css.table}>
                        <thead><tr><th>Open in this page</th><th>Kind</th><th>World</th><th>Saved to</th></tr></thead>
                        <tbody>
                            {projects.value.map((project) => (
                                <tr key={project.key} onClick={() => controller!.openProject(project.key)} tabIndex={0}>
                                    <td>{project.name}</td><td>{project.kind}</td><td>{project.world}</td><td className={css.dim}>{project.label}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                ) : null}
            </section>

            <PairingPanel caps={caps} />

            {busy ? <p className={css.busy} data-testid="hosted-busy">{busy}</p> : null}
            {error ? <p className={css.bad} data-testid="hosted-error">{error}</p> : null}
            <p className={css.dim}>{connection === 'open' ? `The core is loaded. ${heap}` : connection === 'connecting' ? 'Loading the core…' : 'The core did not load.'}</p>
        </main>
    );
}

function Capabilities({ caps }: { caps: Capabilities })
{
    const rows: [string, boolean | 'pair', string][] = [
        ['View, walk, check, pins', true, 'the core in this page'],
        ['Read the game\'s files from your disk', true, caps.folders ? 'folder picker (File System Access)' : 'upload picker: files are read where they are, nothing is sent'],
        ['Edit a project in its own folder', caps.folders, caps.folders ? 'saved into the folder after every change' : 'this browser cannot write a folder: use a working copy and export a zip'],
        ['Working copy kept in this browser', caps.browserStorage, caps.browserStorage ? 'private storage of this site (OPFS)' : 'not in this browser: changes live until the page closes'],
        ['Build the map (BLV, ODM, scene, Lua)', true, 'the same bytes as the studio on your computer; export the build or the mod folder'],
        ['Textured 3D view', caps.bc, caps.bc ? 'compressed textures straight to the GPU' : caps.webgl2 ? 'no BC texture support: grey views' : 'no WebGL2'],
        ['Play here, playtests, pictures from the game', 'pair', 'need the game: pair with oymap studio'],
        ['Agents beside you (MCP)', 'pair', 'through a paired oymap studio'],
        ['Pairing with a local studio', caps.pairing, caps.pairing ? 'the browser asks for local-network access first' : 'Safari blocks it'],
    ];
    return (
        <table className={css.caps} data-testid="capabilities">
            <thead><tr><th>In this browser</th><th /><th /></tr></thead>
            <tbody>
                {rows.map(([what, can, how]) => (
                    <tr key={what}><td>{what}</td><td className={can === true ? css.yes : can === 'pair' ? css.pair : css.no}>{can === true ? 'yes' : can === 'pair' ? 'paired' : 'no'}</td><td className={css.dim}>{how}</td></tr>
                ))}
            </tbody>
        </table>
    );
}

const WORLDS = ['mm6', 'mm7', 'mm8'];

function NewHostedProject({ client, caps, disabled, onMade, onError }: { client: HostedClient; caps: Capabilities; disabled: boolean;
    onMade: (key: string, kind: string) => void; onError: (message: string | null) => void })
{
    const [open, setOpen] = useState(false);
    const [id, setId] = useState('');
    const [name, setName] = useState('');
    const [world, setWorld] = useState('mm6');
    const [kind, setKind] = useState<'indoor' | 'outdoor'>('indoor');
    const [stats, setStats] = useState('9400');
    if (!open)
    {
        return <p><button type="button" className={css.button} disabled={disabled} onClick={() => setOpen(true)} data-testid="hosted-new">New project…</button></p>;
    }
    const ready = /^[a-z0-9_]{1,24}$/.test(id) && name.trim().length > 0 && /^\d+$/.test(stats);
    const make = async (where: 'folder' | 'browser') =>
    {
        onError(null);
        const params = { id, name: name.trim(), world, kind, stats_id: Number(stats), folder: id };
        try
        {
            let place: Parameters<HostedClient['newProject']>[0];
            if (where === 'folder')
            {
                const handle = await pickFolder('readwrite');
                if (!handle)
                {
                    return;
                }
                place = { kind: 'folder', handle };
            }
            else
            {
                place = { kind: 'browser', name: id };
            }
            const made = await client.newProject(place, params);
            onMade(made.key, kind);
        }
        catch (failure)
        {
            onError(failure instanceof Error ? failure.message : String(failure));
        }
    };
    return (
        <div className={css.newForm} data-testid="hosted-new-form">
            <label>Kind <select value={kind} onChange={(event) => setKind(event.target.value as 'indoor' | 'outdoor')}><option value="indoor">indoor (a dungeon)</option><option value="outdoor">outdoor (land, a town)</option></select></label>
            <label>Map id <input value={id} onChange={(event) => setId(event.target.value)} placeholder="crypt01" data-testid="hosted-new-id" /></label>
            <label>Name <input value={name} onChange={(event) => setName(event.target.value)} placeholder="The Old Crypt" data-testid="hosted-new-name" /></label>
            <label>World <select value={world} onChange={(event) => setWorld(event.target.value)}>{WORLDS.map((entry) => <option key={entry}>{entry}</option>)}</select></label>
            <label>Map table row <input value={stats} onChange={(event) => setStats(event.target.value)} inputMode="numeric" /></label>
            <div className={css.buttons}>
                {caps.folders ? <button type="button" className={css.primary} disabled={!ready} onClick={() => void make('folder')}>Make it in a folder…</button> : null}
                {caps.browserStorage ? <button type="button" className={caps.folders ? css.button : css.primary} disabled={!ready} data-testid="hosted-new-browser" onClick={() => void make('browser')}>Make it as a working copy here</button> : null}
                <button type="button" className={css.button} onClick={() => setOpen(false)}>Cancel</button>
            </div>
        </div>
    );
}

// F3 "change a shipped map": an overlay project of a map of the install (spawns, chests, an event's handler).
function ImportShippedMap({ client, caps, disabled, onMade, onError }: { client: HostedClient; caps: Capabilities; disabled: boolean;
    onMade: (key: string) => void; onError: (message: string | null) => void })
{
    const [map, setMap] = useState('');
    const [world, setWorld] = useState('mm6');
    const ready = /^[A-Za-z0-9_-]+\.(blv|odm)$/.test(map) && !disabled;
    return (
        <p className={css.buttons} data-testid="import-map">
            <span className={css.dim}>Change a shipped map:</span>
            <input value={map} onChange={(event) => setMap(event.target.value)} placeholder="6d01.blv" data-testid="import-map-name" />
            <select value={world} onChange={(event) => setWorld(event.target.value)}>{[...WORLDS, 'mm9'].map((entry) => <option key={entry}>{entry}</option>)}</select>
            <button type="button" className={css.button} disabled={!ready} data-testid="import-map-make"
                onClick={() =>
                {
                    onError(null);
                    const place = caps.browserStorage ? { kind: 'browser' as const, name: `${world}_${map.replace(/\.(blv|odm)$/i, '')}` } : { kind: 'memory' as const };
                    void client.importMap(place, map, world).then((made) => onMade(made.key),
                        (failure: unknown) => onError(failure instanceof Error ? failure.message : String(failure)));
                }}>Import as an overlay project</button>
        </p>
    );
}

// Pairing (S5_BROWSER_EDITOR.md 2.12): from a button, after saying the browser will ask.
function PairingPanel({ caps }: { caps: Capabilities })
{
    const [text, setText] = useState('');
    const [state, setState] = useState<PairingState | null>(null);
    const ready = parsePairing(text);
    const busy = state?.state === 'trying' || state?.state === 'waiting';
    const textRef = useRef<HTMLInputElement>(null);
    return (
        <section className={css.step} data-testid="pairing">
            <h2>3. Pair with the studio on your computer (optional)</h2>
            <p className={css.dim}>For Play here, playtests, the game's pictures and agents: run <code>oymap studio --allow-origin {location.origin}</code> on
                your computer and paste the address it prints. <b>Your browser will ask whether this site may reach devices on your local
                network</b>: allow it, or pairing cannot work. The token stays in this tab.</p>
            {!caps.pairing ? <p className={css.bad}>This browser (Safari) does not let a website reach your computer: use Chrome, Edge or Firefox.</p> : null}
            <div className={css.buttons}>
                <input ref={textRef} className={css.wide} value={text} onChange={(event) => setText(event.target.value)} placeholder="http://127.0.0.1:8765/#token=…" data-testid="pair-text" />
                <button type="button" className={css.primary} disabled={!ready || busy || !caps.pairing} data-testid="pair-button"
                    onClick={() =>
                    {
                        if (!ready)
                        {
                            return;
                        }
                        void tryPairing(ready, setState).then((outcome) =>
                        {
                            if (outcome.state === 'paired')
                            {
                                writePairing(ready);
                                location.reload();
                            }
                        });
                    }}>Pair</button>
            </div>
            {state ? (
                <p className={state.state === 'paired' ? css.good : state.state === 'refused' || state.state === 'no_host' ? css.bad : css.busy} data-testid="pair-state">
                    {state.state === 'trying' ? 'Connecting…'
                        : state.state === 'waiting' ? 'Waiting for your answer in the browser\'s prompt (allow access to devices on your local network)…'
                            : state.state === 'paired' ? `Paired (${Math.round(state.ms)} ms): opening the studio's projects…`
                                : state.message}
                </p>
            ) : null}
        </section>
    );
}

// Shown on the project list of a paired page: whose projects these are, and the way back.
export function PairedBanner()
{
    return (
        <p className={css.paired} data-testid="paired-banner">Paired with the studio on this computer: these are its projects, and Play here and agents work as in local mode.{' '}
            <button type="button" className={css.link} onClick={() =>
            {
                writePairing(null);
                location.reload();
            }}>Unpair</button></p>
    );
}
