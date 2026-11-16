// The History drawer (S5_BROWSER_EDITOR.md 3.12): the project's entries, newest first, with their author (user,
// agent:<name>, or outside: an edit found on disk nobody attributed), label, time and semantic changes. Every undo,
// redo and revert is an entry of its own that names the entry it reverts; an entry reverted since is marked; merged
// entries (merge_key) show how many edits they hold; an outside rewrite of a hand-edited project carries its error
// notice. In Author mode: Undo and Redo (the person's own, 2.7) and "Revert this entry" on any entry.
import { useEffect } from 'react';
import type { HistoryEntry } from '../../../schema/rpc/generated/rpc.ts';
import { entryTags, redoTarget, undoTarget } from '../edit/history.ts';
import { useActions, useS } from './context.ts';
import css from './Pins.module.css';
import own from './History.module.css';

// "rooms.yml#room:hall" -> the object to select.
function objectOf(entry: HistoryEntry): { id: string; file: string } | null
{
    const first = entry.objects?.find((object) => object.includes('#') && !object.includes('#/'));
    if (!first)
    {
        return null;
    }
    const at = first.indexOf('#');
    return { file: first.slice(0, at), id: first.slice(at + 1) };
}

export function HistoryPanel()
{
    const actions = useActions();
    const history = useS((s) => s.history);
    const author = useS((s) => s.mode === 'author');
    const ghost = useS((s) => s.ghost?.sequence ?? null);
    useEffect(() =>
    {
        if (history.state === 'idle')
        {
            actions.loadHistory();
        }
    }, [actions, history.state]);
    if (history.state === 'idle' || history.state === 'loading')
    {
        return <div className={css.empty}>Reading the history…</div>;
    }
    if (history.state === 'error')
    {
        return <div className={css.empty}><span className={css.bad}>The history could not be read: {history.message}</span></div>;
    }
    const entries = [...history.value.entries].reverse();
    const undo = undoTarget(history.value.entries, 'user');
    const redo = redoTarget(history.value.entries, 'user');
    return (
        <div className={css.history} data-testid="history">
            <div className={css.toolbar}>
                <span className={css.dim}>{history.value.count} {history.value.count === 1 ? 'entry' : 'entries'}{history.value.count > entries.length ? ` (the latest ${entries.length} shown)` : ''} · rev {history.value.revision.slice(0, 8)}</span>
                <span className={css.spacer} />
                {author ? (
                    <>
                        <button type="button" className={css.button} disabled={!undo} onClick={() => actions.undo()} title={undo ? `Ctrl Z: reverts your #${undo.sequence}` : 'Nothing of yours to undo'}>
                            Undo{undo ? ` #${undo.sequence}` : ''}</button>
                        <button type="button" className={css.button} disabled={!redo} onClick={() => actions.redo()} title={redo ? `Ctrl Y: reverts your undo #${redo.sequence}` : 'Nothing to redo'}>
                            Redo{redo ? ` #${redo.sequence}` : ''}</button>
                    </>
                ) : null}
                <button type="button" className={css.button} onClick={() => actions.loadHistory()}>Read again</button>
            </div>
            {entries.length === 0 ? <div className={css.empty}>No changes recorded yet.</div> : null}
            {entries.map((entry) =>
            {
                const target = objectOf(entry);
                return (
                    <div key={entry.sequence} className={`${css.entry} ${entry.undone ? css.undone : ''} ${entry.notice?.length ? own.noticeEntry : ''}`} data-testid={`entry-${entry.sequence}`}>
                        <span className={css.seq}>#{entry.sequence}</span>
                        <span className={css.author} title={entry.author}>
                            {entry.author}
                            {entryTags(entry).map((tag) => <span key={tag} className={css.tag}>{tag}</span>)}
                        </span>
                        <span className={css.dim}>{entry.time ? entry.time.replace('T', ' ') : ''}</span>
                        <div className={css.changes}>
                            {entry.label ? <div><b>{entry.label}</b></div> : null}
                            {(entry.notice ?? []).map((line, index) => <div key={`n${index}`} className={own.notice}>{line}</div>)}
                            {entry.changes.slice(0, 4).map((change, index) => <div key={index} className={css.changeLine} title={change}>{change}</div>)}
                            {entry.changes.length > 4 ? <div className={css.dim}>… {entry.changes.length - 4} more</div> : null}
                            <div className={own.actions}>
                                {target ? <button type="button" className={own.link} onClick={() => actions.select(target, true)}>{target.id}</button> : null}
                                {entry.kind !== 'build' ? (
                                    <button type="button" className={ghost === entry.sequence ? own.ghostOn : css.button} data-testid={`ghost-${entry.sequence}`}
                                        title="Draw the map as it was before this entry, dashed over the plan and the 3D view (again: put it away)"
                                        onClick={() => actions.showGhost(ghost === entry.sequence ? null : entry.sequence)}>{ghost === entry.sequence ? 'hide as it was' : 'show as it was'}</button>
                                ) : null}
                                {author && !entry.undone && entry.kind !== 'build' ? (
                                    <button type="button" className={css.button} onClick={() => actions.revertEntry(entry.sequence)} data-testid={`revert-${entry.sequence}`}
                                        title="A new entry that puts back, object by object, what this entry changed (objects changed since are left alone and listed)">Revert this entry</button>
                                ) : null}
                            </div>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
