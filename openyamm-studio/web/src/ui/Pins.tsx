// The Pins panel (S5_BROWSER_EDITOR.md 3.13; S5a3): the project's pins, open first, each with its picture, its object
// and its thread; a new pin made with P in the plan or the 3D view (the object under the pointer, the camera, the
// view's picture); claim, reply, resolve, accept, reopen and decline through the request list, as the user. Agents
// answer the same pins through MCP or `oymap pins`; the host's notices bring their answers here at once.
import { useEffect, useMemo, useRef, useState } from 'react';
import type { Job, Pin, PinsTourJobResult } from '../../../schema/rpc/generated/rpc.ts';
import { latestJobs } from '../model/scorecard.ts';
import { actionsFor, isClosed, needsText, pinPlace, sortPins, statusOf } from '../model/pins.ts';
import type { PinAction } from '../model/pins.ts';
import { NONE } from '../state/store.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Pins.module.css';

const ACTION_LABEL: Record<PinAction, string> = {
    claim: 'Claim', reply: 'Reply', resolve: 'Resolve', accept: 'Accept', reopen: 'Reopen', decline: 'Decline',
};

export function PinsPanel()
{
    const pins = useS((s) => s.pins);
    const draft = useS((s) => s.pinDraft);
    const filter = useS((s) => s.pinFilter);
    const selectedId = useS((s) => s.selectedPin);
    const all = pins.state === 'ready' ? pins.value.pins : NONE;
    const sorted = useMemo(() => sortPins(all), [all]);
    const shown = filter === 'all' ? sorted : sorted.filter((pin) => !isClosed(pin));
    const selected = sorted.find((pin) => pin.id === selectedId) ?? null;
    if (pins.state === 'loading' || pins.state === 'idle')
    {
        return <div className={css.empty}>Reading the pins…</div>;
    }
    if (pins.state === 'error')
    {
        return <div className={css.empty}><span className={css.bad}>The pins could not be read: {pins.message}</span></div>;
    }
    return (
        <div className={css.panel}>
            <div className={css.list} data-testid="pins-list">
                <PinsToolbar counter={pins.value.counter} total={sorted.length} shown={shown.length} />
                {draft ? <Composer /> : null}
                {shown.length === 0 && !draft ? (
                    <div className={css.empty}>
                        {sorted.length === 0 ? <>No pins. Press <kbd>P</kbd> over the plan or the 3D view, or pin a fault while playing (the game's console: <code>pin &lt;text&gt;</code>).</>
                            : 'No open pins.'}
                    </div>
                ) : null}
                {shown.map((pin) => <PinRow key={pin.id} pin={pin} selected={pin.id === selectedId} />)}
            </div>
            <div className={css.detail}>
                {selected ? <Thread key={selected.id} pin={selected} /> : <div className={css.empty}>Choose a pin to read its thread.</div>}
            </div>
        </div>
    );
}

function PinsToolbar({ counter, total, shown }: { counter: number; total: number; shown: number })
{
    const actions = useActions();
    const filter = useS((s) => s.pinFilter);
    const { store } = useStudioContext();
    return (
        <div className={css.toolbar}>
            <button type="button" className={filter === 'active' ? css.chipOn : css.chip} onClick={() => store.setState({ pinFilter: 'active' })}>Active</button>
            <button type="button" className={filter === 'all' ? css.chipOn : css.chip} onClick={() => store.setState({ pinFilter: 'all' })}>All {total}</button>
            <span className={css.dim}>{shown} shown · counter {counter}</span>
            <span className={css.spacer} />
            <TourButton />
            <button type="button" className={css.button} onClick={() => actions.startPin(store.getState().viewMode === 'plan' ? 'plan' : '3d')} title="P over the plan or the 3D view pins what is under the pointer">New pin (P)</button>
        </div>
    );
}

// `oymap pins tour` as a button (S5_BROWSER_EDITOR.md 3.13; S5a5): the game's own pictures at every open, claimed and
// resolved pin's pose, taken by the host's pins tour job on the project built and installed now; each pin's thread
// then shows its picture, to answer with.
function TourButton()
{
    const actions = useActions();
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const { pending } = latestJobs(jobs, 'pins_tour', revision);
    return (
        <button type="button" className={css.button} disabled={Boolean(pending)} onClick={() => actions.startJob('pins_tour')} data-testid="pins-tour"
            title="Build, install and take the game's own picture at every open, claimed and resolved pin's pose (a job: Jobs, Pictures)">
            {pending ? (pending.state === 'running' ? 'touring the pins…' : 'tour waiting…') : 'Tour pins in the game'}</button>
    );
}

// The newest pins tour's picture of a pin, with a reply or resolve that attaches it.
function TourPicture({ pin, text, onDone }: { pin: Pin; text: string; onDone: (error: string | null) => void })
{
    const actions = useActions();
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const results = useS((s) => s.jobResults);
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const tour: Job | null = jobs.find((job) => job.kind === 'pins_tour' && job.state === 'done' && job.has_result) ?? null;
    const result = tour ? (results[tour.id] as PinsTourJobResult | undefined) : undefined;
    const shot = result?.shots.find((entry) => entry.pin === pin.id && entry.picture);
    const [url, setUrl] = useState<string | null>(null);
    const [busy, setBusy] = useState(false);
    useEffect(() =>
    {
        let live = true;
        if (tour && shot?.picture)
        {
            void actions.jobFile(tour, shot.picture).then((found) => live && setUrl(found));
        }
        return () => { live = false; };
    }, [actions, tour, shot]);
    if (!tour || !shot?.picture)
    {
        return null;
    }
    const answer = async (action: 'reply' | 'resolve') =>
    {
        setBusy(true);
        onDone(await actions.answerWithPicture(pin, tour, shot.picture!, action, text));
        setBusy(false);
    };
    const resolvable = statusOf(pin) === 'open' || statusOf(pin) === 'claimed';
    return (
        <div className={css.pictureBox} data-testid="tour-picture">
            <div className={css.dim}>The game, rev {tour.revision.slice(0, 8)}{tour.revision !== revision ? ' (older revision)' : ''}</div>
            {url ? <img className={css.picture} src={url} alt={`${pin.id} in the game`} onClick={() => actions.openLightbox(url, `${pin.id} in the game · rev ${tour.revision.slice(0, 8)}`)} /> : null}
            <button type="button" className={css.link} disabled={busy} onClick={() => void answer('reply')}>Reply with it</button>
            {resolvable ? <button type="button" className={css.link} disabled={busy || !text.trim()} onClick={() => void answer('resolve')}
                title="Resolve with the words above and this picture">Resolve with it</button> : null}
        </div>
    );
}

function Composer()
{
    const actions = useActions();
    const draft = useS((s) => s.pinDraft)!;
    const [text, setText] = useState('');
    const field = useRef<HTMLTextAreaElement>(null);
    useEffect(() => field.current?.focus(), []);
    const target = draft.on ? `on ${draft.on}${draft.file ? ` (${draft.file})` : ''}` : draft.at ? `at [${draft.at.join(', ')}]` : 'nowhere';
    const send = () => void actions.submitPin(text);
    return (
        <div className={`${css.composer} ${draft.picture ? '' : css.composerBare}`} data-testid="pin-composer">
            {draft.picture ? <img className={css.composerPicture} src={draft.picture} alt="The view the pin is made in" /> : null}
            <div className={css.composerBody}>
                <div className={css.dim}>New pin {target}{draft.on && draft.at ? ` · at [${draft.at.join(', ')}]` : ''} · from the {draft.where === '3d' ? '3D view (its camera kept)' : 'plan'}</div>
                <textarea ref={field} className={css.text} value={text} placeholder="What is wrong, or what should change?"
                    onChange={(event) => setText(event.target.value)}
                    onKeyDown={(event) =>
                    {
                        if (event.key === 'Enter' && (event.ctrlKey || event.metaKey))
                        {
                            event.preventDefault();
                            send();
                        }
                        else if (event.key === 'Escape')
                        {
                            actions.cancelPin();
                        }
                    }} />
                {draft.error ? <div className={css.bad}>{draft.error}</div> : null}
                <div className={css.buttons}>
                    <button type="button" className={css.primary} disabled={!text.trim() || draft.sending || (!draft.on && !draft.at)} onClick={send}>{draft.sending ? 'Pinning…' : 'Pin (Ctrl Enter)'}</button>
                    <button type="button" className={css.button} onClick={() => actions.cancelPin()}>Cancel</button>
                </div>
            </div>
        </div>
    );
}

function PinRow({ pin, selected }: { pin: Pin; selected: boolean })
{
    const actions = useActions();
    const status = statusOf(pin);
    const place = pinPlace(pin);
    const replies = pin.replies?.length ?? 0;
    return (
        <div className={`${css.row} ${selected ? css.selected : ''}`} data-pin={pin.id} onClick={() => actions.selectPin(pin.id)}
            onDoubleClick={() => actions.goToPin(pin)}>
            <span className={css[`status_${status}`]}>{status}</span>
            <span className={css.rowText} title={pin.text}>{pin.text}</span>
            <span className={css.rowMeta}>
                {pin.on ?? (place ? `[${place.map((v) => Math.round(v)).join(', ')}]` : '')}
                {' · '}{pin.source === 'game' ? 'game' : pin.source === 'studio' ? 'studio' : pin.author ?? ''}
                {pin.picture ? ' · picture' : ''}
                {replies > 0 ? ` · ${replies} ${replies === 1 ? 'reply' : 'replies'}` : ''}
            </span>
        </div>
    );
}

function Picture({ relative, label }: { relative: string; label: string })
{
    const actions = useActions();
    const [url, setUrl] = useState<string | null | undefined>(undefined);
    const [large, setLarge] = useState(false);
    useEffect(() =>
    {
        let live = true;
        void actions.picture(relative).then((found) => live && setUrl(found));
        return () => { live = false; };
    }, [actions, relative]);
    if (url === undefined)
    {
        return <div className={css.pictureWait}>loading picture…</div>;
    }
    if (url === null)
    {
        return <div className={css.pictureMissing}>The picture is not on this machine ({relative}); go to the pin's pose instead.</div>;
    }
    return (
        <>
            <img className={css.picture} src={url} alt={label} title={`${label} (click to enlarge)`} onClick={() => setLarge(true)} />
            {large ? (
                <div className={css.lightbox} onClick={() => setLarge(false)} role="dialog" aria-label={label}>
                    <img src={url} alt={label} />
                </div>
            ) : null}
        </>
    );
}

function Thread({ pin }: { pin: Pin })
{
    const actions = useActions();
    const [text, setText] = useState('');
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const status = statusOf(pin);
    const available = actionsFor(pin, 'user');
    const place = pinPlace(pin);
    const run = async (action: PinAction | 'keep') =>
    {
        setBusy(true);
        setError(null);
        const refused = await actions.actOnPin(pin, action, text);
        setBusy(false);
        if (refused)
        {
            setError(refused);
        }
        else if (action !== 'keep')
        {
            setText('');
        }
    };
    return (
        <div className={css.thread} data-testid="pin-thread">
            <div className={css.threadHead}>
                <span className={css[`status_${status}`]}>{status}</span>
                <span className={css.pinId}>{pin.id}</span>
                <span className={css.dim}>{pin.author ?? ''}{pin.source ? ` in the ${pin.source}` : ''}{pin.created ? ` · ${pin.created.replace('T', ' ')}` : ''}</span>
                <span className={css.spacer} />
                <button type="button" className={css.primary} onClick={() => actions.goToPin(pin)} disabled={!pin.pose && !pin.on && !place}
                    title={pin.pose ? 'The 3D camera where the pin was made from' : 'Frame its object or place'}>Go to</button>
            </div>
            <div className={css.pinBody}>
                <div className={css.pinWords}>
                    <p className={css.pinText}>{pin.text}</p>
                    <div className={css.dim}>
                        {pin.on ? <>on <code>{pin.on}</code>{pin.file ? ` (${pin.file})` : ''}</> : null}
                        {place ? <> at [{place.map((v) => Math.round(v)).join(', ')}]</> : null}
                        {pin.map ? ` · ${pin.map}` : ''}
                        {pin.claimed_by ? ` · claimed by ${pin.claimed_by}` : ''}
                        {pin.revision ? ` · made at rev ${pin.revision.slice(0, 8)}` : ''}
                    </div>
                </div>
                {pin.picture ? (
                    <div className={css.pictureBox}>
                        <Picture relative={pin.picture} label={`${pin.id}: the view it was made in`} />
                        {!pin.keep ? <button type="button" className={css.link} onClick={() => void run('keep')} disabled={busy} title="Copy it into review/pictures/ (kept in git)">Keep picture</button>
                            : <span className={css.dim}>kept in git</span>}
                    </div>
                ) : null}
                <TourPicture pin={pin} text={text} onDone={(refused) => { setError(refused); if (!refused) setText(''); }} />
            </div>
            <ol className={css.replies}>
                {(pin.replies ?? []).map((reply, index) => (
                    <li key={index} className={css.reply}>
                        <div className={css.replyHead}>
                            <b>{reply.author}</b>
                            {reply.status ? <span className={css[`status_${reply.status}`]}> {reply.status}</span> : null}
                            <span className={css.dim}>{reply.created ? ` · ${reply.created.replace('T', ' ')}` : ''}{reply.revision ? ` · rev ${reply.revision.slice(0, 8)}` : ''}</span>
                        </div>
                        {reply.text ? <div className={css.replyText}>{reply.text}</div> : null}
                        {(reply.pictures ?? []).length > 0 ? (
                            <div className={css.replyPictures}>
                                {reply.pictures!.map((picture) => <Picture key={picture} relative={picture} label={`${pin.id}: ${reply.author}'s picture`} />)}
                            </div>
                        ) : null}
                    </li>
                ))}
            </ol>
            <div className={css.answer}>
                <textarea className={css.text} value={text} placeholder={status === 'resolved' ? 'Accept, or say why it is not right and reopen' : 'Reply, or say what was done (resolve) or why not (decline)'}
                    onChange={(event) => setText(event.target.value)} />
                <div className={css.buttons}>
                    {available.map((action) => (
                        <button key={action} type="button" className={action === 'accept' || action === 'reply' ? css.primary : css.button}
                            disabled={busy || (needsText(action) && !text.trim())} onClick={() => void run(action)}
                            data-action={action}>{ACTION_LABEL[action]}</button>
                    ))}
                </div>
                {error ? <div className={css.bad}>{error}</div> : null}
            </div>
        </div>
    );
}
