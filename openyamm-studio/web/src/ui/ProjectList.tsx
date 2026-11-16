// The project list (no project open): what the host allows, by its path jail (S5_BROWSER_EDITOR.md 2.12), and a
// new project made in one of the host's project folders (S5b1, F5: a dungeon from an empty project). S6: the list as
// a world map (WorldMap.tsx), the host's mods folder with projects packed into a mod, and a new project's map number
// proposed from its mod's or its world's declared range.
import { useEffect, useRef, useState } from 'react';
import type { ModListResult, ModMapNumberResult, ModPackResult } from '../../../schema/rpc/generated/rpc.ts';
import { useActions, useS } from './context.ts';
import { WorldView } from './WorldMap.tsx';

import css from './ProjectList.module.css';

type ListView = 'list' | 'world' | 'mods';

// The view of the list, kept per browser (a convenience: the page works without it).
function savedView(): ListView
{
    try
    {
        const value = window.localStorage.getItem('oymap.projectList.view');
        return value === 'world' || value === 'mods' ? value : 'list';
    }
    catch
    {
        return 'list';
    }
}

export function ProjectList()
{
    const projects = useS((s) => s.projects);
    const connection = useS((s) => s.connection);
    const actions = useActions();
    const [view, setViewState] = useState<ListView>(savedView);
    const setView = (next: ListView) =>
    {
        setViewState(next);
        try
        {
            window.localStorage.setItem('oymap.projectList.view', next);
        }
        catch
        {
            // the view is only remembered where the browser keeps it
        }
    };
    return (
        <main className={css.page}>
            <h1 className={css.heading}>Map Studio</h1>
            <p className={css.lead}>Open a project to look at it (Review mode: the plan, the 3D view, its issues and pins), or make a new one and build it by hand (Author mode).</p>
            <NewProject />
            {connection !== 'open' && projects.state !== 'ready' && projects.state !== 'error' ? <p className={css.bad}>The host is not connected ({connection}).</p> : null}
            {projects.state === 'loading' ? <p className={css.dim}>Reading the project list…</p> : null}
            {projects.state === 'error' ? <p className={css.bad}>The host did not give the list: {projects.message}</p> : null}
            {projects.state === 'ready' && projects.value.length === 0 ? <p className={css.dim}>The host allows no project folder.</p> : null}
            {projects.state === 'ready' && projects.value.length > 0 ? (
                <div className={css.views} role="tablist" aria-label="How the projects are shown">
                    {([['list', 'List'], ['world', 'World map'], ['mods', 'Mods']] as const).map(([name, label]) => (
                        <button key={name} type="button" role="tab" aria-selected={view === name} data-testid={`list-view-${name}`}
                            className={view === name ? css.viewOn : css.viewButton} onClick={() => setView(name)}>{label}</button>))}
                </div>) : null}
            {projects.state === 'ready' && projects.value.length > 0 && view === 'world' ? <WorldView /> : null}
            {projects.state === 'ready' && projects.value.length > 0 && view === 'mods' ? <Mods /> : null}
            {projects.state === 'ready' && projects.value.length > 0 && view === 'list' ? (
                <table className={css.table}>
                    <thead>
                        <tr><th>Name</th><th>Kind</th><th>World</th><th>Folder</th></tr>
                    </thead>
                    <tbody>
                        {projects.value.map((project) => (
                            <tr key={project.key} onClick={() => actions.openProject(project.key)} tabIndex={0}
                                onKeyDown={(event) => event.key === 'Enter' && actions.openProject(project.key)}>
                                <td className={css.name}>{project.name}</td>
                                <td>{project.kind}</td>
                                <td>{project.world}</td>
                                <td className={css.key}>{project.label ?? project.key}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            ) : null}
        </main>
    );
}

const WORLDS = ['mm6', 'mm7', 'mm8'];

function NewProject()
{
    const actions = useActions();
    const roots = useS((s) => s.projectRoots);
    const [open, setOpen] = useState(false);
    const [root, setRoot] = useState<string | null>(null);
    const [folder, setFolder] = useState('');
    const [id, setId] = useState('');
    const [name, setName] = useState('');
    const [world, setWorld] = useState('mm6');
    const [stats, setStats] = useState('9400');
    const [kind, setKind] = useState<'indoor' | 'outdoor'>('indoor');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    // S6: the mods of the host's mods folder that declare map numbers, and the number proposed for the world or mod.
    const [mods, setMods] = useState<ModListResult | null>(null);
    const [mod, setMod] = useState('');
    const [proposal, setProposal] = useState<ModMapNumberResult | string | null>(null);
    // A number typed by hand stays until the world or the mod changes.
    const [typed, setTyped] = useState(false);
    useEffect(() =>
    {
        let live = true;
        if (open)
        {
            void actions.listMods().then((value) => { if (live && typeof value !== 'string') setMods(value); });
        }
        return () => { live = false; };
    }, [actions, open]);
    const typedRef = useRef(typed);
    typedRef.current = typed;
    useEffect(() =>
    {
        let live = true;
        if (open)
        {
            void actions.mapNumber(world, mod || undefined).then((value) =>
            {
                if (!live)
                {
                    return;
                }
                setProposal(value);
                if (typeof value !== 'string')
                {
                    setStats((before) => (typedRef.current ? before : String(value.number)));
                }
            });
        }
        return () => { live = false; };
    }, [actions, open, world, mod]);
    if (roots.length === 0)
    {
        return null;
    }
    const ranged = [...(mods?.named ?? []), ...(mods?.merged ?? [])].filter((entry) => entry.map_range)
        .filter((entry, index, list) => list.findIndex((other) => other.id === entry.id) === index);
    if (!open)
    {
        return <p><button type="button" className={css.button} onClick={() => setOpen(true)} data-testid="new-project">New project…</button></p>;
    }
    const where = root ?? roots[roots.length - 1];
    const ready = /^[a-z0-9][a-z0-9_-]*$/.test(folder) && /^[a-z0-9_]+$/.test(id) && name.trim().length > 0 && /^\d*$/.test(stats) && !busy;
    return (
        <form className={css.newForm} data-testid="new-project-form" onSubmit={(event) =>
        {
            event.preventDefault();
            if (!ready)
            {
                return;
            }
            setBusy(true);
            setError(null);
            void actions.newProject({ root: where, folder, id, name: name.trim(), world, kind, ...(stats ? { stats_id: Number(stats) } : {}) }).then((refusal) =>
            {
                setBusy(false);
                setError(refusal);
            });
        }}>
            <h2 className={css.formTitle}>New {kind} project</h2>
            <label className={css.field}><span>Kind</span>
                <select className={css.select} value={kind} onChange={(event) => setKind(event.target.value as 'indoor' | 'outdoor')} data-testid="new-kind"
                    title="indoor: a dungeon of rooms (BLV); outdoor: a map of land, water, roads and buildings (ODM)">
                    <option value="indoor">indoor (a dungeon)</option>
                    <option value="outdoor">outdoor (land, a town)</option>
                </select>
            </label>
            <label className={css.field}><span>Folder</span>
                <span className={css.where}>
                    <select className={css.select} value={where} onChange={(event) => setRoot(event.target.value)}>
                        {roots.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                    </select>/
                    <input className={css.input} value={folder} onChange={(event) => setFolder(event.target.value)} placeholder="crypt" data-testid="new-folder" />
                </span>
            </label>
            <label className={css.field}><span>Map id</span><input className={css.input} value={id} onChange={(event) => setId(event.target.value)} placeholder={kind === 'outdoor' ? 'vale01 (builds vale01.odm)' : 'crypt01 (builds crypt01.blv)'} data-testid="new-id" /></label>
            <label className={css.field}><span>Name</span><input className={css.input} value={name} onChange={(event) => setName(event.target.value)} placeholder="The Old Crypt" data-testid="new-name" /></label>
            <label className={css.field}><span>World</span>
                <select className={css.select} value={world} onChange={(event) => { setWorld(event.target.value); setTyped(false); }}>
                    {WORLDS.map((entry) => <option key={entry} value={entry}>{entry}</option>)}
                </select>
            </label>
            <label className={css.field}><span>For the mod</span>
                <select className={css.select} value={mod} onChange={(event) => { setMod(event.target.value); setTyped(false); }} data-testid="new-mod"
                    title="A mod of the host's mods folder that declares its map numbers (mod.yml idRanges.maps): the new map takes the first free one">
                    <option value="">none (the world's numbers)</option>
                    {ranged.map((entry) => <option key={entry.id} value={entry.id}>{`${entry.name} (${entry.map_range![0]} to ${entry.map_range![1]})`}</option>)}
                </select>
            </label>
            <label className={css.field}><span>Map table row</span><input className={css.input} value={stats} inputMode="numeric" onChange={(event) => { setStats(event.target.value); setTyped(true); }} data-testid="new-stats"
                title="The number of the map's row in the map table (map_stats id): each new map needs its own" /></label>
            <p className={css.dim} data-testid="new-stats-note">{proposal === null ? 'Finding a free map number…'
                : typeof proposal === 'string' ? `No number proposed: ${proposal}`
                : `${proposal.number} is the first free number of ${proposal.from === 'studio' ? 'the studio\'s band' : proposal.from.replace(':', ' ')} (${proposal.range[0]} to ${proposal.range[1]}, ${proposal.taken} taken by shipped maps, mods and projects).`
                    + (proposal.warnings.length > 0 ? ` ${proposal.warnings.join('; ')}.` : '')}</p>
            <p className={css.dim}>{kind === 'outdoor'
                ? 'The core makes the folder with a map card, a plan with one zone and the arrival point, and level land given by spot heights; the project opens in Author mode with the grid editor.'
                : 'The core makes the folder with an empty map card, rooms, objects and wiring; the project opens in Author mode with the Room tool.'}</p>
            {error ? <p className={css.bad}>{error}</p> : null}
            <div className={css.formButtons}>
                <button type="submit" className={css.primary} disabled={!ready} data-testid="new-project-make">Make it</button>
                <button type="button" className={css.button} onClick={() => setOpen(false)}>Cancel</button>
            </div>
        </form>
    );
}

// The host's mods folder (S6 item M): its mods (mod.list), and projects packed into a new one (mod.pack: each built
// first, the mod's map numbers declared). Installing into a game and switching mods off stay on the command line.
function Mods()
{
    const actions = useActions();
    const projects = useS((s) => s.projects);
    const [list, setList] = useState<ModListResult | string | null>(null);
    const [picked, setPicked] = useState<string[]>([]);
    const [id, setId] = useState('');
    const [name, setName] = useState('');
    const [range, setRange] = useState('');
    const [busy, setBusy] = useState(false);
    const [packed, setPacked] = useState<ModPackResult | string | null>(null);
    const reload = () => { void actions.listMods().then(setList); };
    useEffect(reload, [actions]);
    const all = projects.state === 'ready' ? projects.value : [];
    const rangeMatch = /^\s*(\d+)\s*(?:-|to)\s*(\d+)\s*$/.exec(range);
    const ready = picked.length > 0 && /^[a-z0-9_]+$/.test(id) && (range.trim() === '' || rangeMatch !== null) && !busy;
    const mods = typeof list === 'string' || list === null ? [] : [...list.named.map((entry) => ({ ...entry, layout: 'packed or named' })),
        ...list.merged.map((entry) => ({ ...entry, layout: 'merged' }))];
    return (
        <section className={css.mods} data-testid="mods-view">
            <p className={css.dim}>The host's mods folder. A mod holds projects' builds as the game's packages hold them, with the rows they add to the engine's tables; it declares the map numbers its new maps take, and a new project of the mod is given the first free one. Install it into a game with <code>oymap mod install</code>.</p>
            {list === null ? <p className={css.dim}>Reading the mods folder…</p> : null}
            {typeof list === 'string' ? <p className={css.bad}>{list}</p> : null}
            {mods.length > 0 ? (
                <table className={css.table} data-testid="mods-table">
                    <thead><tr><th>Mod</th><th>Version</th><th>Maps</th><th>Map numbers</th><th>Layout</th></tr></thead>
                    <tbody>
                        {mods.map((entry) => (
                            <tr key={`${entry.layout}-${entry.id}`} className={css.still}>
                                <td><span className={css.name}>{entry.name}</span> <span className={css.key}>{entry.id}</span></td>
                                <td>{entry.version}</td>
                                <td>{entry.maps ?? entry.files ?? 0}</td>
                                <td>{`${entry.map_numbers.join(', ') || 'none'}${entry.map_range ? ` (its range ${entry.map_range[0]} to ${entry.map_range[1]})` : ''}`}</td>
                                <td>{entry.layout}{entry.layout === 'merged' ? (entry.enabled ? ', on' : ', off') : ''}</td>
                            </tr>))}
                    </tbody>
                </table>) : list !== null && typeof list !== 'string' ? <p className={css.dim}>No mod yet.</p> : null}
            <form className={css.newForm} data-testid="mod-pack-form" onSubmit={(event) =>
            {
                event.preventDefault();
                if (!ready)
                {
                    return;
                }
                setBusy(true);
                setPacked(null);
                void actions.packMod({ projects: picked, id, ...(name.trim() ? { name: name.trim() } : {}),
                    ...(rangeMatch ? { maps: [Number(rangeMatch[1]), Number(rangeMatch[2])] as [number, number] } : {}) }).then((answer) =>
                {
                    setBusy(false);
                    setPacked(answer);
                    reload();
                });
            }}>
                <h2 className={css.formTitle}>Pack a mod</h2>
                <label className={css.field}><span>Mod id</span><input className={css.input} value={id} onChange={(event) => setId(event.target.value)} placeholder="sorpigal_cellars" data-testid="mod-id" /></label>
                <label className={css.field}><span>Name</span><input className={css.input} value={name} onChange={(event) => setName(event.target.value)} placeholder="The Sorpigal cellars" data-testid="mod-name" /></label>
                <label className={css.field}><span>Map numbers</span><input className={css.input} value={range} onChange={(event) => setRange(event.target.value)} placeholder="9500-9549 (optional)" data-testid="mod-range"
                    title="The map_stats numbers the mod declares as its own: first-last" /></label>
                <div className={css.pickList} data-testid="mod-projects">
                    {all.map((project) => (
                        <label key={project.key} className={css.pick}>
                            <input type="checkbox" checked={picked.includes(project.key)} onChange={(event) =>
                                setPicked(event.target.checked ? [...picked, project.key] : picked.filter((key) => key !== project.key))} />
                            <span className={css.name}>{project.name}</span> <span className={css.key}>{project.world} {project.kind}, {project.label ?? project.key}</span>
                        </label>))}
                </div>
                <div className={css.formButtons}>
                    <button type="submit" className={css.primary} disabled={!ready} data-testid="mod-pack">{busy ? 'Building and packing…' : `Pack ${picked.length} project(s)`}</button>
                </div>
                {typeof packed === 'string' ? <p className={css.bad}>{packed}</p> : null}
                {packed && typeof packed !== 'string' ? (
                    <div className={css.dim} data-testid="mod-packed">
                        {`Packed ${packed.id}: ${packed.maps.map((map) => `${map.file} (${map.kind}${map.map_number ? `, ${map.map_number}` : ''})`).join(', ')}; `}
                        {`${packed.files.length} files, rows of ${packed.tables.join(', ') || 'no table'}.`}
                        {packed.warnings.map((warning) => <div key={warning} className={css.warn}>{warning}</div>)}
                    </div>) : null}
            </form>
        </section>
    );
}
