// The drawer's Checklist (S5_BROWSER_EDITOR.md 3.10): the plan's spaces without a room (each with "draw its room":
// the Room tool, the next room realising it), each stage's "done when" with what the files and issues say of it, and
// REBUILD_PROCEDURE.md's "what the measure does not see" to tick.
import { useEffect, useMemo, useState } from 'react';
import { UNSEEN, readTicks, spacesWithoutRoom, stageItems, writeTicks } from '../model/checklist.ts';
import { knownIssues } from '../state/store.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Checklist.module.css';

export function ChecklistPanel()
{
    const actions = useActions();
    const { store } = useStudioContext();
    const key = useS((s) => s.projectKey);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const issues = useS((s) => knownIssues(s));
    const author = useS((s) => s.mode === 'author');
    const pendingSpace = useS((s) => s.toolOptions.space);
    const spaces = useMemo(() => spacesWithoutRoom(files), [files]);
    const stages = useMemo(() => stageItems(files, issues), [files, issues]);
    const [ticks, setTicks] = useState<Set<string>>(new Set());
    useEffect(() => setTicks(key ? readTicks(key) : new Set()), [key]);
    const tick = (id: string) =>
    {
        const next = new Set(ticks);
        if (next.has(id))
        {
            next.delete(id);
        }
        else
        {
            next.add(id);
        }
        setTicks(next);
        if (key)
        {
            writeTicks(key, next);
        }
    };
    const open = spaces.length + stages.filter((stage) => stage.state === 'open').length + UNSEEN.filter((item) => !ticks.has(item.id)).length;
    return (
        <div className={css.checklist} data-testid="checklist">
            <p className={css.summary}>{open === 0 ? 'Nothing open.' : `${open} open`} · ticks are kept in this browser for this project</p>
            <section className={css.section}>
                <h4 className={css.heading}>Planned spaces without a room <span className={css.count}>{spaces.length}</span></h4>
                {spaces.length === 0 ? <p className={css.dim}>Every space of plan.yml has its room (or the map has no plan).</p> : null}
                {spaces.map((space) => (
                    <div key={space.id} className={css.item}>
                        <span className={css.box} aria-hidden="true">{pendingSpace === space.id ? '✎' : '○'}</span>
                        <span className={css.text}><b>{space.name}</b> <span className={css.dim}>{space.id}{space.purpose ? ` · ${space.purpose}` : ''}</span></span>
                        {author ? (
                            <button type="button" className={css.button} data-testid={`draw-${space.id}`} onClick={() =>
                            {
                                store.setState((s) => ({ toolOptions: { ...s.toolOptions, space: space.id } }));
                                actions.setStage(2);
                                actions.setTool('room');
                            }}>{pendingSpace === space.id ? 'drawing…' : 'draw its room'}</button>
                        ) : null}
                    </div>
                ))}
            </section>
            <section className={css.section}>
                <h4 className={css.heading}>The stages: done when</h4>
                {stages.map((stage) => (
                    <div key={stage.stage} className={css.item} data-testid={`stage-item-${stage.stage}`}>
                        <span className={stage.state === 'done' ? css.done : stage.state === 'open' ? css.open : css.box}
                            aria-label={stage.state}>{stage.state === 'done' ? '✓' : stage.state === 'open' ? '!' : '?'}</span>
                        <span className={css.text}>
                            <button type="button" className={css.stage} onClick={() => actions.setStage(stage.stage)}>{stage.stage} {stage.name}</button>
                            {' '}{stage.done} <span className={css.dim}>· {stage.why}</span>
                        </span>
                    </div>
                ))}
            </section>
            <section className={css.section}>
                <h4 className={css.heading}>What the measure does not see <span className={css.dim}>(REBUILD_PROCEDURE.md)</span></h4>
                {UNSEEN.map((item) => (
                    <label key={item.id} className={css.item}>
                        <input type="checkbox" checked={ticks.has(item.id)} onChange={() => tick(item.id)} data-testid={`tick-${item.id}`} />
                        <span className={`${css.text} ${ticks.has(item.id) ? css.ticked : ''}`}>{item.text}</span>
                    </label>
                ))}
            </section>
        </div>
    );
}
