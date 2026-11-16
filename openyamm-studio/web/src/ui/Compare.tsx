// The Compare view (S5_BROWSER_EDITOR.md 3.14; S5a5): the original (the shipped map from the asset root,
// view.original_mesh) and the rebuild side by side, their cameras locked (the original moved by the compare's
// vertical offset, so one camera shows the same place in both), and the compare's worst places and, outdoors, the
// 64 regions' scores beside them: a click puts both cameras there and frames it on the plan.
import { useEffect, useRef, useState } from 'react';
import type { CompareJobResult } from '../../../schema/rpc/generated/rpc.ts';
import { Viewport } from '../viewport/Viewport.ts';
import { regionGrid } from '../model/compare.ts';
import { heatColour, latestJobs } from '../model/scorecard.ts';
import { probe } from '../app/controller.ts';
import { NONE } from '../state/store.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Checks.module.css';

export function CompareView()
{
    const { store, controller } = useStudioContext();
    const actions = useActions();
    const leftHost = useRef<HTMLDivElement>(null);
    const rightHost = useRef<HTMLDivElement>(null);
    const original = useS((s) => s.original);
    const mesh = useS((s) => s.mesh);
    const textured = useS((s) => s.textured);
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const results = useS((s) => s.jobResults);
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const { done, pending } = latestJobs(jobs, 'compare', revision);
    const compare = done ? (results[done.id] as CompareJobResult | undefined) ?? null : null;
    const [views, setViews] = useState<{ left: Viewport; right: Viewport } | null>(null);

    useEffect(() =>
    {
        // Locked cameras: a camera change in one view is the other's (guarded, since setting a camera reports one).
        let syncing = false;
        const pair: { left?: Viewport; right?: Viewport } = {};
        const follow = (from: 'left' | 'right') => () =>
        {
            const source = pair[from];
            const other = pair[from === 'left' ? 'right' : 'left'];
            if (syncing || !source || !other)
            {
                return;
            }
            syncing = true;
            other.setCamera(source.camera());
            syncing = false;
        };
        const left = new Viewport(leftHost.current!, { onHover: () => undefined, onPick: () => undefined, onCamera: follow('left') });
        const right = new Viewport(rightHost.current!, {
            onHover: (pick) => store.setState({ hover: pick ? { owner: pick.owner || '(no owner)', point: pick.point } : null, cursor: pick?.point ?? store.getState().cursor }),
            onPick: (pick) => actions.select(pick?.base ? { id: pick.base, file: pick.file } : null),
            onCamera: follow('right'),
        });
        pair.left = left;
        pair.right = right;
        setViews({ left, right });
        probe().viewport = right;
        (probe() as { original?: unknown }).original = left;
        controller?.attachViewport(right);
        controller?.attachOriginalViewport(left);
        left.setCamera(right.camera());
        return () =>
        {
            controller?.attachOriginalViewport(null);
            controller?.attachViewport(null);
            left.dispose();
            right.dispose();
        };
    }, [store, actions, controller]);
    useEffect(() =>
    {
        views?.left.setTextured(textured);
        views?.right.setTextured(textured);
    }, [views, textured]);
    const selection = useS((s) => s.selection);
    useEffect(() => views?.right.setSelection(selection?.id ?? null), [views, selection]);

    const grid = compare ? regionGrid(compare) : [];
    return (
        <div className={css.compare} data-testid="compare">
            <div className={css.comparePane}>
                <div className={css.paneHead}>
                    <b>Original</b>
                    <span className={css.dim}>{original.state === 'ready' ? `${original.value.original} (${original.value.world}), from the asset root` : ''}</span>
                    {compare && compare.vertical_offset !== 0 ? <span className={css.badge}>moved {compare.vertical_offset > 0 ? 'up' : 'down'} {Math.abs(compare.vertical_offset)} to the rebuild's heights</span> : null}
                </div>
                <div ref={leftHost} className={css.surface}>
                    {original.state !== 'ready' ? <div className={css.overlay}>{original.state === 'loading' ? 'Reading the original…'
                        : original.state === 'error' ? `No original: ${original.message}` : ''}</div> : null}
                </div>
            </div>
            <div className={css.comparePane}>
                <div className={css.paneHead}>
                    <b>Rebuild</b>
                    <span className={css.dim}>{mesh.state === 'ready' ? `revision ${mesh.value.view_revision.slice(0, 8)}` : ''}</span>
                    <span className={css.spacer} />
                    <span className={css.dim}>one camera: drag in either view</span>
                </div>
                <div ref={rightHost} className={css.surface} />
            </div>
            <div className={css.places}>
                <div className={css.paneHead}>
                    {compare ? <><b className={compare.band.within ? css.v_good : css.v_bad}>{(compare.score * 100).toFixed(1)} %</b>
                        <span className={css.dim}>{compare.band.within ? 'within' : 'outside'} the band ({compare.band.at_least * 100} %)</span></>
                        : <span className={css.dim}>{pending ? 'comparing…' : 'no compare yet'}</span>}
                    <span className={css.spacer} />
                    <button type="button" className={css.button} onClick={() => actions.startJob('compare')} disabled={Boolean(pending)}>Compare again</button>
                </div>
                {compare && done && done.revision !== revision ? <div className={css.empty}>Measured on an older revision ({done.revision.slice(0, 8)}).</div> : null}
                {compare ? (
                    <>
                        {compare.parts.map((part) => (
                            <div key={part.id} className={css.place} title={part.what} style={{ cursor: 'default' }}>
                                <span />
                                <span className={css.figure}>{(part.score * 100).toFixed(1)}</span>
                                <span>{part.id}{part.weight === 0 ? <span className={css.dim}> (not scored)</span> : null}</span>
                            </div>
                        ))}
                        {grid.length > 0 ? (
                            <div className={css.regions} aria-label="Regions, A1 the north-west">
                                {grid.flat().map((score, index) =>
                                {
                                    const [r, g, b] = heatColour(score);
                                    return <span key={index} className={css.region} style={{ background: `rgb(${r}, ${g}, ${b})` }}
                                        title={`${String.fromCharCode(65 + (index % 8))}${Math.floor(index / 8) + 1}: ${(score / 10).toFixed(1)} %`}>{Math.round(score / 10)}</span>;
                                })}
                            </div>
                        ) : null}
                        <div className={css.paneHead}><b>Worst places</b><span className={css.dim}>{compare.worst.length}</span></div>
                        {compare.worst.map((place, index) => (
                            <button type="button" key={index} className={css.place} onClick={() => actions.goToPlace(place.at, place.yaw_radians)}
                                title={place.what} data-testid="compare-place">
                                <span className={css.dim}>{index + 1}</span>
                                <span className={css.figure}>{(place.score * 100).toFixed(0)} %</span>
                                <span>{place.name}: {place.what}</span>
                            </button>
                        ))}
                    </>
                ) : null}
            </div>
        </div>
    );
}
