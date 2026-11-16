// The flow graph (S5_BROWSER_EDITOR.md 3.7; S5a5): rooms in columns by the solve's step at which the party first
// stands in them, openings between them (a door dashed, with the events that open it and their step), the critical
// path from the start to the plan's goals thick, rooms never reached last; beside it the wiring (each event, its
// source and what it moves, and the steps it acts in) and the solve's faults, every id a link to its object.
import { useMemo } from 'react';
import type { ChecksJobResult } from '../../../schema/rpc/generated/rpc.ts';
import { buildFlow, placeFlow } from '../model/flow.ts';
import type { FlowGraph } from '../model/flow.ts';
import { latestJobs } from '../model/scorecard.ts';
import { NONE } from '../state/store.ts';
import { useActions, useS } from './context.ts';
import css from './Checks.module.css';

const SIZES = { column: 186, row: 30, width: 150, height: 22, margin: 20 };

export function FlowView()
{
    const actions = useActions();
    const layout = useS((s) => (s.layout.state === 'ready' ? s.layout.value : null));
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const results = useS((s) => s.jobResults);
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const selection = useS((s) => s.selection);
    const { done, pending } = latestJobs(jobs, 'checks', revision);
    const checks = done ? (results[done.id] as ChecksJobResult | undefined) ?? null : null;
    const graph = useMemo<FlowGraph>(() => buildFlow(checks?.solve ?? null, layout, files as Record<string, { tree?: unknown }> | undefined),
        [checks, layout, files]);
    const placed = useMemo(() => placeFlow(graph, SIZES), [graph]);
    // What moves the map first (switches, doors, what the solve uses), then chests and texts.
    const wiring = useMemo(() => [...graph.events].sort((a, b) =>
    {
        const rank = (event: typeof a) => (event.steps.length > 0 ? 0 : event.targets.some((target) => target.verb !== 'chest') ? 1 : 2);
        return rank(a) - rank(b);
    }), [graph]);
    const stale = Boolean(done && revision && done.revision !== revision);
    let width = 400;
    let height = 200;
    for (const place of placed.values())
    {
        width = Math.max(width, place.x + place.width + SIZES.margin);
        height = Math.max(height, place.y + place.height + SIZES.margin);
    }
    const select = (id: string, file?: string) => actions.select({ id, file }, true);
    const fileOf = (id: string) => (id.startsWith('room:') || id.startsWith('open:') ? 'rooms.yml' : id.startsWith('evt:') ? 'wiring.yml' : undefined);
    const centre = (id: string, side: 'left' | 'right') =>
    {
        const place = placed.get(id);
        return place ? [side === 'left' ? place.x : place.x + place.width, place.y + place.height / 2] : null;
    };
    return (
        <div className={css.flow} data-testid="flow">
            <div className={css.flowGraph}>
                {graph.empty && graph.nodes.length === 0 ? <div className={css.empty}>{graph.empty}</div> : null}
                {!checks ? <div className={css.empty}>{pending ? 'The checks are running: the solve fills the graph when they finish.' : 'No solve yet: run the checks (Scorecard).'}</div> : null}
                {stale ? <div className={css.empty}>The solve is of an older revision ({done!.revision.slice(0, 8)}); the checks run again by themselves.</div> : null}
                <svg width={width} height={height} role="img" aria-label="Flow graph">
                    {Array.from({ length: graph.columns + 1 }, (unused, column) => (
                        <text key={column} className={css.columnLabel} x={SIZES.margin + column * SIZES.column} y={SIZES.margin + 10}>
                            {column < graph.columns ? `step ${column}${graph.needs[column]?.length ? ` · needs ${graph.needs[column].join(', ')}` : ''}` : 'never reached'}
                        </text>
                    ))}
                    {graph.edges.map((edge) =>
                    {
                        const a = placed.get(edge.from);
                        const b = placed.get(edge.to);
                        if (!a || !b)
                        {
                            return null;
                        }
                        const forward = a.x <= b.x;
                        const from = centre(forward ? edge.from : edge.to, 'right')!;
                        const to = centre(forward ? edge.to : edge.from, 'left')!;
                        const same = a.x === b.x;
                        const bend = same ? 40 : Math.max(30, (to[0] - from[0]) / 2);
                        const d = same
                            ? `M ${from[0]} ${from[1]} C ${from[0] + bend} ${from[1]}, ${from[0] + bend} ${to[1] === from[1] ? to[1] + 1 : to[1]}, ${from[0]} ${to[1]}`
                            : `M ${from[0]} ${from[1]} C ${from[0] + bend} ${from[1]}, ${to[0] - bend} ${to[1]}, ${to[0]} ${to[1]}`;
                        const label = edge.door ? `${edge.door}${edge.openedBy.length ? ` ← ${edge.openedBy.map((by) => `${by.event} (step ${by.step})`).slice(0, 2).join(', ')}` : ''}` : '';
                        return (
                            <g key={edge.id} onClick={() => select(edge.door ?? edge.id, edge.door ? 'objects.yml' : 'rooms.yml')} style={{ cursor: 'pointer' }}>
                                <path d={d} className={`${edge.door ? css.edgeDoor : css.edge} ${edge.critical ? css.edgeCritical : ''}`}>
                                    <title>{`${edge.id}: ${edge.from} – ${edge.to}${label ? `\n${label}` : ''}`}</title>
                                </path>
                                {edge.door && !same ? <text className={css.doorLabel} x={(from[0] + to[0]) / 2} y={(from[1] + to[1]) / 2 - 3} textAnchor="middle">{edge.door.replace(/^door:/, '')}</text> : null}
                            </g>
                        );
                    })}
                    {graph.nodes.map((node) =>
                    {
                        const place = placed.get(node.id);
                        if (!place)
                        {
                            return null;
                        }
                        const classes = [css.node, node.step === null && checks ? css.nodeNever : '', node.goal ? css.nodeGoal : '', node.start ? css.nodeStart : '',
                            selection?.id === node.id ? css.nodeSelected : ''].join(' ');
                        return (
                            <g key={node.id} className={classes} onClick={() => select(node.id, 'rooms.yml')} data-room={node.id}>
                                <rect x={place.x} y={place.y} width={place.width} height={place.height} />
                                <text x={place.x + 6} y={place.y + place.height / 2 + 4}>{`${node.start ? '▶ ' : ''}${node.goal ? '★ ' : ''}${node.id.replace(/^room:/, '')}`}</text>
                                <title>{`${node.id}${node.space && node.space !== node.id ? ` (space ${node.space})` : ''}\n${node.step === null ? 'never reached' : `reached at step ${node.step}`}; sectors ${node.sectors.join(', ') || '–'}`}</title>
                            </g>
                        );
                    })}
                </svg>
            </div>
            <div className={css.flowSide}>
                {graph.issues.length + graph.waiting.length > 0 ? (
                    <>
                        <h3 className={css.v_bad}>Order faults and waits</h3>
                        <ul>{[...graph.issues, ...graph.waiting].map((line, index) => <li key={index}>{line}</li>)}</ul>
                    </>
                ) : null}
                {graph.neverReached.length > 0 ? (
                    <>
                        <h3 className={css.v_warn}>Never reached ({graph.neverReached.length})</h3>
                        <ul>{graph.neverReached.map((id) => <li key={id}><button type="button" className={css.link} onClick={() => select(id, fileOf(id))}>{id}</button></li>)}</ul>
                    </>
                ) : null}
                <h3>Wiring ({graph.events.length} events)</h3>
                <ul>
                    {wiring.map((event) => (
                        <li key={event.id}>
                            <button type="button" className={css.link} onClick={() => select(event.id, 'wiring.yml')}>{event.id}</button>
                            {event.title ? <span className={css.dim}> “{event.title}”</span> : null}
                            {event.preset ? <span className={css.dim}> {event.preset}</span> : null}
                            {event.steps.length ? <span className={css.badge}>step {event.steps.join(', ')}</span> : null}
                            <div>
                                {event.source ? <>from <button type="button" className={css.link} onClick={() => select(event.source!)}>{event.source}</button>{event.room ? <span className={css.dim}> in {event.room}</span> : null}</> : null}
                                {event.targets.map((target, index) => (
                                    <span key={index}> · {target.verb} <button type="button" className={css.link} onClick={() => select(target.id)}>{target.id}</button></span>
                                ))}
                            </div>
                            {event.condition ? <div className={css.dim}>when {event.condition}</div> : null}
                        </li>
                    ))}
                </ul>
                {graph.exits.length > 0 ? (
                    <>
                        <h3>Ways out</h3>
                        <ul>{graph.exits.map((line, index) => <li key={index} className={css.dim}>{line}</li>)}</ul>
                    </>
                ) : null}
                {graph.notes.length > 0 ? (
                    <>
                        <h3>Notes</h3>
                        <ul>{graph.notes.map((line, index) => <li key={index} className={css.dim}>{line}</li>)}</ul>
                    </>
                ) : null}
            </div>
        </div>
    );
}
