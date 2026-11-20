// The project list's world view (devdocs/map_studio/S6_PLAN.md 2.9; S5_BROWSER_EDITOR.md 6.3): the host's projects by
// world (world.view), each world a map of its maps (model/world.ts lays them out) with lines where their exits lead.
// A project's map opens the project; a shipped map is drawn as the place the links reach.
import { useEffect, useMemo, useState } from 'react';
import type { WorldViewResult } from '../../../schema/rpc/generated/rpc.ts';
import { boxEdgePoint, layoutWorld, roleCounts } from '../model/world.ts';
import type { WorldEntry, WorldMap as WorldMapEntry } from '../model/world.ts';
import { useActions, useS } from './context.ts';
import css from './WorldMap.module.css';

const ROLE_WORDS: Record<WorldMapEntry['role'], string> = { new: 'new map', rebuild: 'rebuild', overlay: 'overlay', shipped: 'shipped map' };
const PAD = 24;

// A line of the box's small type cut to its width (about 6.4 units a letter), with an ellipsis.
function fitted(text: string, width: number): string
{
    const letters = Math.floor((width - 16) / 6.4);
    return text.length > letters ? `${text.slice(0, letters - 1)}…` : text;
}

function WorldPicture({ world, onOpen }: { world: WorldEntry; onOpen: (project: number) => void })
{
    const layout = useMemo(() => layoutWorld(world), [world]);
    const [hover, setHover] = useState<number | null>(null);
    const [minX, minY, maxX, maxY] = layout.bounds;
    const width = maxX - minX + 2 * PAD;
    const height = maxY - minY + 2 * PAD;
    const place = (index: number) => layout.maps.find((entry) => entry.index === index)!;
    const touching = (a: number, b: number) => hover !== null && (hover === a || hover === b);
    return (
        <svg className={css.picture} viewBox={`${minX - PAD} ${minY - PAD} ${width} ${height}`} width={Math.round(width)} height={Math.round(height)}
            role="img" aria-label={`The maps of ${world.world} and where their exits lead`} data-testid={`world-map-${world.world}`}>
            <defs>
                <marker id={`arrow-${world.world}`} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
                    <path d="M0,0 L10,5 L0,10 z" className={css.arrowHead} />
                </marker>
            </defs>
            {layout.edges.map((edge) =>
            {
                const a = place(edge.a);
                const b = place(edge.b);
                const from = boxEdgePoint(a, [b.x, b.y]);
                const to = boxEdgePoint(b, [a.x, a.y]);
                const middle: [number, number] = [(from[0] + to[0]) / 2, (from[1] + to[1]) / 2];
                const label = edge.kinds.filter((kind) => kind !== 'door').join(', ');
                return (
                    <g key={`${edge.a}-${edge.b}`} className={touching(edge.a, edge.b) ? css.edgeLit : css.edge} data-edge={`${edge.a}-${edge.b}`}>
                        <title>{edge.titles.join('\n')}</title>
                        <line x1={from[0]} y1={from[1]} x2={to[0]} y2={to[1]} className={edge.viaOriginal ? css.lineVia : css.line}
                            markerEnd={edge.forward ? `url(#arrow-${world.world})` : undefined}
                            markerStart={edge.backward ? `url(#arrow-${world.world})` : undefined} />
                        {label ? <text x={middle[0]} y={middle[1] - 4} className={css.edgeLabel}>{label}</text> : null}
                    </g>);
            })}
            {layout.maps.map((placed) =>
            {
                const map = world.maps[placed.index]!;
                const project = map.project;
                const open = project !== undefined ? () => onOpen(project) : undefined;
                return (
                    <g key={placed.index} className={`${css.map} ${css[map.role]} ${map.kind === 'outdoor' ? css.outdoor : ''}`}
                        transform={`translate(${placed.x - placed.width / 2} ${placed.y - placed.height / 2})`}
                        onMouseEnter={() => setHover(placed.index)} onMouseLeave={() => setHover(null)}
                        onClick={open} role={open ? 'button' : undefined} tabIndex={open ? 0 : undefined}
                        onKeyDown={open ? (event) => event.key === 'Enter' && open() : undefined}
                        data-map={map.map} data-role={map.role}>
                        <title>{`${map.name} (${map.map}): ${ROLE_WORDS[map.role]}${map.stands_for ? ` of ${map.stands_for}` : ''}${open ? '; click to open the project' : ''}`}</title>
                        <rect width={placed.width} height={placed.height} rx={map.kind === 'outdoor' ? 10 : 4} className={css.box} />
                        <text x={10} y={map.kind === 'outdoor' ? 22 : 19} className={css.name}>{map.name.length > 22 ? `${map.name.slice(0, 21)}…` : map.name}</text>
                        <text x={10} y={map.kind === 'outdoor' ? 39 : 34} className={css.file}>
                            {fitted(`${map.map}${map.stands_for && map.role === 'rebuild' ? ` = ${map.stands_for}` : ''}`, placed.width)}
                        </text>
                    </g>);
            })}
        </svg>
    );
}

export function WorldView()
{
    const actions = useActions();
    const projects = useS((s) => s.projects);
    const [answer, setAnswer] = useState<WorldViewResult | string | null>(null);
    const [chosen, setChosen] = useState<string | null>(null);
    const ready = projects.state === 'ready';
    const keys = ready ? projects.value.map((project) => project.key) : [];
    const keyList = keys.join('\n');

    useEffect(() =>
    {
        let live = true;
        if (ready)
        {
            setAnswer(null);
            void actions.worldView().then((value) => { if (live) setAnswer(value); });
        }
        return () => { live = false; };
    }, [actions, ready, keyList]);

    if (answer === null)
    {
        return <p className={css.dim}>Reading the projects' map cards…</p>;
    }
    if (typeof answer === 'string')
    {
        return <p className={css.bad}>The world view did not come: {answer}</p>;
    }
    if (answer.worlds.length === 0)
    {
        return <p className={css.dim}>No project has a world.</p>;
    }
    const world = answer.worlds.find((entry) => entry.world === chosen) ?? answer.worlds[0]!;
    const counts = roleCounts(world);
    return (
        <div className={css.view} data-testid="world-view">
            <div className={css.tabs} role="tablist">
                {answer.worlds.map((entry) => (
                    <button key={entry.world} type="button" role="tab" aria-selected={entry.world === world.world}
                        className={entry.world === world.world ? css.tabOn : css.tab} onClick={() => setChosen(entry.world)}>
                        {`${entry.world} (${entry.maps.filter((map) => map.project !== undefined).length})`}
                    </button>))}
            </div>
            <p className={css.dim}>
                {`${world.world}: ${counts.new} new, ${counts.rebuild} rebuilt, ${counts.overlay} overlaid, ${counts.shipped} shipped map(s) the exits reach; ${world.links.length} link(s). `}
                Outdoor maps stand where their map edges join; dungeons round the map they open from. A dashed line reaches a map through the project that rebuilds or overlays it. Click a project's map to open it.
            </p>
            <div className={css.legend}>
                {(['new', 'rebuild', 'overlay', 'shipped'] as const).map((role) => (
                    <span key={role} className={`${css.chip} ${css[role]}`}><svg width="14" height="10"><rect width="14" height="10" rx="2" className={css.box} /></svg>{ROLE_WORDS[role]}</span>))}
            </div>
            <div className={css.scroll}>
                <WorldPicture world={world} onOpen={(project) => { const key = keys[project]; if (key) actions.openProject(key); }} />
            </div>
            {answer.skipped.length > 0 ? <p className={css.bad}>{`Left out: ${answer.skipped.map((entry) => `${keys[entry.project] ?? entry.project} (${entry.reason})`).join(', ')}`}</p> : null}
        </div>
    );
}
