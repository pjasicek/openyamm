// A person's place in the shared history (S5_BROWSER_EDITOR.md 2.7), read off the log as the core does: Ctrl Z
// takes the author's latest entry that is neither an undo nor reverted already; Ctrl Y the author's latest undo not
// reverted yet, while the author made no other change since. Used to label and enable Undo and Redo; the core
// decides (edit.undo, edit.redo).
import type { HistoryEntry } from '../../../schema/rpc/generated/rpc.ts';

export function undoTarget(entries: readonly HistoryEntry[], author: string): HistoryEntry | null
{
    for (let i = entries.length - 1; i >= 0; --i)
    {
        const entry = entries[i];
        if (entry.author !== author)
        {
            continue;
        }
        if (entry.kind === 'revert' && entry.revert_kind === 'undo')
        {
            continue;
        }
        if (entry.undone)
        {
            continue;
        }
        if (entry.kind === 'transaction' || entry.kind === 'revert')
        {
            return entry;
        }
    }
    return null;
}

export function redoTarget(entries: readonly HistoryEntry[], author: string): HistoryEntry | null
{
    for (let i = entries.length - 1; i >= 0; --i)
    {
        const entry = entries[i];
        if (entry.author !== author)
        {
            continue;
        }
        if (entry.kind === 'revert' && entry.revert_kind === 'undo')
        {
            if (entry.undone)
            {
                // Redone already: an earlier undo of the chain may still be redone.
                continue;
            }
            return entry;
        }
        // A redo entry continues the chain (an undo after it may be redone); any other change ends it.
        if (entry.kind === 'revert' && entry.revert_kind === 'redo')
        {
            continue;
        }
        return null;
    }
    return null;
}

// The outside rewrite of a hand-edited project still in effect, with its notice (2.8 point 3): the newest outside
// entry with a notice that nothing has reverted.
export function openNotice(entries: readonly HistoryEntry[], dismissed: ReadonlySet<number>): HistoryEntry | null
{
    for (let i = entries.length - 1; i >= 0; --i)
    {
        const entry = entries[i];
        if (entry.notice && entry.notice.length > 0 && !entry.undone && !dismissed.has(entry.sequence))
        {
            return entry;
        }
    }
    return null;
}

// How an entry reads in the History list: what kind of entry, and what it reverts.
export function entryTags(entry: HistoryEntry): string[]
{
    const tags: string[] = [];
    if (entry.kind === 'outside')
    {
        tags.push('outside');
    }
    if (entry.kind === 'migration')
    {
        tags.push('migration');
    }
    if (entry.kind === 'revert')
    {
        tags.push(`${entry.revert_kind ?? 'revert'} of #${entry.reverts ?? '?'}`);
    }
    if (entry.merged && entry.merged > 1)
    {
        tags.push(`${entry.merged} edits`);
    }
    if (entry.undone)
    {
        tags.push('reverted');
    }
    return tags;
}
