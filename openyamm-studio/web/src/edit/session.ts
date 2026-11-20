// Autosave (S5_BROWSER_EDITOR.md 2.5, 2.7 "Autosave is the model"): every gesture is one edit.apply. The client
// applies its own copy of the operations at once (the plan redraws without waiting), sends the gestures one at a
// time against the revision the core last answered (rebase: true, as a person: author user, allow_errors), and
// replaces its copy with the core's files from each answer. A refusal drops that gesture from the copy, with the
// core's reason. Undo, redo and revert are the core's revert entries (edit.undo, edit.redo, edit.revert).
import type { EditApplyResult, EditUndoResult, FileTrees, Issue, Op } from '../../../schema/rpc/generated/rpc.ts';
import { RpcCallError } from '../rpc/client.ts';
import type { StudioClient } from '../rpc/client.ts';
import type { Store } from '../state/store.ts';
import { LocalOpError, applyOpsLocally, idsOf } from './ops.ts';

export interface Gesture
{
    ops: Op[];
    label: string;
    // Repeated edits fold into one history entry (a drag, PgUp pressed ten times): 2.6 item 6.
    mergeKey?: string;
}

interface Queued extends Gesture
{
    resolve: (result: EditApplyResult | null) => void;
}

export interface SessionHooks
{
    // After the core wrote something (or the queue ran dry): the views, the history and the checks again; with
    // `reload`, the whole project (a gesture refused because others changed the same objects).
    committed(key: string, reload: boolean): void;
    note(text: string): void;
}

function reasonOf(error: unknown): string
{
    if (error instanceof RpcCallError)
    {
        const data = error.data as { reason?: string; new_issues?: Issue[] } | undefined;
        if (data?.new_issues?.length)
        {
            return data.new_issues.map((issue) => issue.message).join('; ');
        }
        return error.message;
    }
    return error instanceof Error ? error.message : String(error);
}

export class EditSession
{
    private readonly client: StudioClient;
    private readonly store: Store;
    private readonly hooks: SessionHooks;
    private queue: Queued[] = [];
    private sending = false;
    // What the core last answered: its files and revision. The store shows these plus the queued gestures.
    private confirmed: { key: string; files: FileTrees; revision: string } | null = null;
    private reload = false;

    constructor(client: StudioClient, store: Store, hooks: SessionHooks)
    {
        this.client = client;
        this.store = store;
        this.hooks = hooks;
    }

    get busy(): boolean
    {
        return this.sending || this.queue.length > 0;
    }

    // One gesture: shown at once, written in order. Resolves with the core's answer, or null when refused.
    apply(gesture: Gesture): Promise<EditApplyResult | null>
    {
        const state = this.store.getState();
        if (!state.projectKey || state.project.state !== 'ready')
        {
            return Promise.resolve(null);
        }
        if (!this.busy || this.confirmed?.key !== state.projectKey)
        {
            this.confirmed = { key: state.projectKey, files: state.project.value.files, revision: state.project.value.revision };
        }
        return new Promise((resolve) =>
        {
            this.queue.push({ ...gesture, resolve });
            this.show();
            void this.pump();
        });
    }

    // The store's project: the confirmed files with every queued gesture applied on the client.
    private show(): void
    {
        const state = this.store.getState();
        if (!this.confirmed || state.projectKey !== this.confirmed.key || state.project.state !== 'ready')
        {
            return;
        }
        let files = this.confirmed.files;
        for (const gesture of this.queue)
        {
            try
            {
                files = applyOpsLocally(files, gesture.ops);
            }
            catch (error)
            {
                // The client cannot show this one (a rename): it shows after the core's answer.
                if (!(error instanceof LocalOpError))
                {
                    throw error;
                }
            }
        }
        this.store.setState({
            project: { state: 'ready', value: { ...state.project.value, files, ids: idsOf(files), revision: this.confirmed.revision } },
            edits: { ...state.edits, pending: this.queue.length },
        });
    }

    private async pump(): Promise<void>
    {
        if (this.sending)
        {
            return;
        }
        this.sending = true;
        try
        {
            while (this.queue.length > 0 && this.confirmed)
            {
                const gesture = this.queue[0];
                const key = this.confirmed.key;
                let result: EditApplyResult | null = null;
                try
                {
                    result = await this.client.call('edit.apply', {
                        project: key, ops: gesture.ops, expect_revision: this.confirmed.revision, rebase: true,
                        allow_errors: true, author: 'user', label: gesture.label, ...(gesture.mergeKey ? { merge_key: gesture.mergeKey } : {}),
                    });
                }
                catch (error)
                {
                    this.refused(gesture, reasonOf(error), error instanceof RpcCallError && error.kind === 'stale_revision');
                }
                this.queue.shift();
                if (result && this.confirmed?.key === key)
                {
                    this.accepted(gesture, result);
                }
                this.show();
                gesture.resolve(result);
            }
        }
        finally
        {
            this.sending = false;
            const key = this.confirmed?.key;
            this.store.setState((s) => ({ edits: { ...s.edits, pending: 0 } }));
            if (key)
            {
                this.hooks.committed(key, this.reload);
            }
            this.reload = false;
        }
    }

    private accepted(gesture: Gesture, result: EditApplyResult): void
    {
        const confirmed = this.confirmed!;
        confirmed.files = { ...confirmed.files, ...result.files };
        confirmed.revision = result.revision_after;
        const state = this.store.getState();
        // The known issues move by the change's own delta at once (the full check follows when the queue is dry).
        const fixed = new Set(result.fixed_issues.map((issue) => JSON.stringify(issue)));
        const moved = (issues: Issue[]) => [...issues.filter((issue) => !fixed.has(JSON.stringify(issue))), ...result.new_issues];
        if (state.project.state === 'ready')
        {
            this.store.setState({ project: { state: 'ready', value: { ...state.project.value, issues: moved(state.project.value.issues),
                ...(result.hand_edited ? { hand_edited: result.hand_edited } : {}) } } });
        }
        if (state.validation.state === 'ready')
        {
            this.store.setState({ validation: { state: 'ready', value: { ...state.validation.value, issues: moved(state.validation.value.issues) } } });
        }
        this.store.setState((s) => ({ edits: { ...s.edits, saved: { revision: result.revision_after, at: Date.now(), label: gesture.label }, error: null } }));
        if (result.outside_notice?.length)
        {
            this.hooks.note(`Before this change: ${result.outside_notice.join(' ')}`);
        }
    }

    private refused(gesture: Gesture, reason: string, stale: boolean): void
    {
        this.store.setState((s) => ({ edits: { ...s.edits, error: { label: gesture.label, message: reason } } }));
        this.reload ||= stale;
        this.hooks.note(`Not written: ${gesture.label}: ${reason}${stale ? ' (someone changed the same objects; the project is read again)' : ''}`);
    }

    // Undo (Ctrl Z), redo (Ctrl Y) and "Revert this entry": each a new history entry (2.7). Waits for the queue.
    async revert(kind: 'undo' | 'redo' | 'revert', sequence?: number, force = false): Promise<EditUndoResult | null>
    {
        while (this.busy)
        {
            await new Promise((done) => setTimeout(done, 20));
        }
        const state = this.store.getState();
        const key = state.projectKey;
        if (!key || state.project.state !== 'ready')
        {
            return null;
        }
        this.confirmed = { key, files: state.project.value.files, revision: state.project.value.revision };
        this.sending = true;
        try
        {
            const common = { project: key, author: 'user', allow_errors: true, ...(force ? { force: true } : {}) };
            const result = kind === 'undo' ? await this.client.call('edit.undo', common)
                : kind === 'redo' ? await this.client.call('edit.redo', common)
                : await this.client.call('edit.revert', { ...common, sequence: sequence! });
            if (this.confirmed.key === key)
            {
                this.confirmed.files = { ...this.confirmed.files, ...result.files };
                this.confirmed.revision = result.revision;
                this.show();
                this.store.setState((s) => ({ edits: { ...s.edits,
                    saved: { revision: result.revision, at: Date.now(), label: `${kind} #${result.reverts}` }, error: null,
                    conflict: result.conflicts.length > 0 ? { kind, sequence: result.reverts, conflicts: result.conflicts } : null } }));
                if (result.changes.length === 0 && result.conflicts.length > 0)
                {
                    this.hooks.note(`Nothing ${kind === 'redo' ? 'redone' : 'undone'}: every object it changed was changed since (${result.conflicts.join(', ')})`);
                }
            }
            return result;
        }
        catch (error)
        {
            if (error instanceof RpcCallError && error.kind === 'nothing_to_undo')
            {
                this.hooks.note(kind === 'redo' ? 'Nothing of yours to redo.' : 'Nothing of yours to undo (an agent\'s changes are not undone by Ctrl Z: revert them in History).');
            }
            else
            {
                this.store.setState((s) => ({ edits: { ...s.edits, error: { label: kind, message: reasonOf(error) } } }));
                this.hooks.note(`${kind}: ${reasonOf(error)}`);
            }
            return null;
        }
        finally
        {
            this.sending = false;
            this.hooks.committed(key, false);
        }
    }

    // A project opened or read again: nothing of an earlier one stays.
    reset(): void
    {
        for (const gesture of this.queue)
        {
            gesture.resolve(null);
        }
        this.queue = [];
        this.confirmed = null;
    }
}
