// The scorecard, the jobs and the pictures (S5_BROWSER_EDITOR.md 3.10, 3.11, 3.15; S5a5). The scorecard is one card per
// check of the project, from the newest finished job of each kind; it says which revision a result belongs to and
// greys one of an older revision. The background checks fill it by themselves when the project opens and after each
// change; the rest run on request. Jobs lists every job with its state, last line and a cancel. Pictures shows the
// game's pictures of the jobs (pins tours, building shots) grouped by job, full size on a click.
import { useEffect, useMemo, useState } from 'react';
import type { BuildingShotsJobResult, Job, LightingBakeJobResult, PinsTourJobResult } from '../../../schema/rpc/generated/rpc.ts';
import { KIND_TITLES, latestJobs, scorecardKinds, scoreLine } from '../model/scorecard.ts';
import type { JobKind, KindResults, ScoreLine } from '../model/scorecard.ts';
import { NONE } from '../state/store.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Checks.module.css';

const card = (files: Record<string, { tree?: unknown } | undefined> | undefined) =>
    (files?.['project.yml']?.tree ?? {}) as Record<string, unknown>;

export function ScorecardPanel()
{
    const actions = useActions();
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const jobsState = useS((s) => s.jobs);
    const results = useS((s) => s.jobResults);
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const python = useS((s) => s.python);
    const info = card(files);
    const kind = String(info.kind ?? 'indoor');
    const stats = (info.map_stats ?? {}) as Record<string, unknown>;
    const original = typeof stats.reference === 'string' ? stats.reference : typeof info.base === 'string' ? info.base : '';
    const lines = useMemo<ScoreLine[]>(() => scorecardKinds(kind, Boolean(original)).map((kindOf) =>
    {
        const { done, pending } = latestJobs(jobs, kindOf, revision);
        const result = done ? (results[done.id] as KindResults[typeof kindOf] | undefined) ?? null : null;
        return scoreLine(kindOf, done, pending, result, revision);
    }), [jobs, results, revision, kind, original]);
    const [otherOriginal, setOtherOriginal] = useState('');
    if (jobsState.state === 'loading' || jobsState.state === 'idle')
    {
        return <div className={css.empty}>Reading the jobs…</div>;
    }
    if (jobsState.state === 'error')
    {
        return <div className={css.empty}><span className={css.v_bad}>The jobs could not be read: {jobsState.message}</span></div>;
    }
    const running = jobs.filter((job) => job.state === 'running' || job.state === 'queued').length;
    return (
        <div className={css.panel} data-testid="scorecard">
            <div className={css.toolbar}>
                <span>{original ? <>a rebuild of <b>{original}</b></> : kind === 'outdoor' ? 'a new outdoor map' : 'a new map'}</span>
                <span className={css.dim}>revision {revision?.slice(0, 8)}</span>
                {running > 0 ? <span className={css.badgeRun}>{running} running or waiting</span> : null}
                <span className={css.spacer} />
                {!original ? (
                    <>
                        <input className={css.input} placeholder="6d01.blv" value={otherOriginal} onChange={(event) => setOtherOriginal(event.target.value)}
                            aria-label="Original map to compare with" />
                        <button type="button" className={css.button} disabled={!/^[A-Za-z0-9_-]+\.(blv|odm)$/.test(otherOriginal)}
                            onClick={() => actions.startJob('compare', { original: otherOriginal })}>Compare with it</button>
                    </>
                ) : null}
                <button type="button" className={css.button} onClick={() => actions.startJob('checks')}>Check again</button>
                <button type="button" className={css.button} onClick={() => actions.startJob('playtest', { runs: 4 })}
                    title="The project's playtest.yml in the game, four times">Playtest ×4</button>
                {kind === 'outdoor' && original ? (
                    <button type="button" className={css.button} disabled={!python} onClick={() => actions.startJob('building_shots')}
                        title="Every building beside the original's in the game (calibration/building_shots.py; about 35 minutes)">Building shots</button>
                ) : null}
            </div>
            <div className={css.scroll}>
                {lines.map((line) => <ScoreCard key={line.kind} line={line} python={python} />)}
            </div>
        </div>
    );
}

function ScoreCard({ line, python }: { line: ScoreLine; python: boolean })
{
    const actions = useActions();
    const [open, setOpen] = useState(line.verdict === 'bad');
    const pythonKind = line.kind === 'scale_bands' || line.kind === 'town_feel' || line.kind === 'building_shots';
    const shown = open ? line.details : line.details.slice(0, 4);
    const compare = line.kind === 'compare' && line.job;
    return (
        <div className={`${css.card} ${line.stale ? css.stale : ''}`} data-kind={line.kind} data-verdict={line.verdict}>
            <div className={css.cardHead}>
                <span className={css[`dot_${line.verdict}`]} />
                <span className={css.cardTitle}>{line.title}</span>
                <span className={`${css.figure} ${css[`v_${line.verdict}`]}`}>{line.figure}</span>
                {line.kind === 'compare' && line.job && line.verdict !== 'none' ? <ScoreBar share={Number.parseFloat(line.figure) / 100} good={line.verdict === 'good'} /> : null}
                {line.job ? <span className={line.stale ? css.badgeStale : css.badge} title={line.job.revision}>
                    {line.stale ? `older revision ${line.job.revision.slice(0, 6)}` : `rev ${line.job.revision.slice(0, 6)}`} · {line.job.seconds ?? '–'} s</span> : null}
                {line.pending ? <span className={css.badgeRun}>{line.pending.state === 'running' ? 'running…' : 'waiting…'}</span> : null}
                <span className={css.spacer} />
                {compare ? <button type="button" className={css.button} onClick={() => actions.enterCompare()}>Compare view</button> : null}
                <button type="button" className={css.button} disabled={(pythonKind && !python) || Boolean(line.pending)}
                    onClick={() => actions.startJob(line.kind, line.kind === 'playtest' ? { runs: 4 } : {})}>{line.job ? 'Run again' : 'Run'}</button>
            </div>
            {shown.length > 0 ? (
                <ul className={css.details}>
                    {shown.map((detail, index) => (
                        <li key={index}>
                            <span className={css[`dot_${detail.verdict}`]} />
                            <span className={css.detailText}>{detail.text}</span>
                            {detail.id ? <button type="button" className={css.link} onClick={() => actions.select({ id: detail.id! }, true)}>{detail.id}</button> : null}
                            {detail.at ? <button type="button" className={css.link} onClick={() => actions.goToPlace(detail.at!)}>go</button> : null}
                        </li>
                    ))}
                </ul>
            ) : null}
            {line.details.length > 4 ? <button type="button" className={css.more} onClick={() => setOpen(!open)}>{open ? 'fewer' : `${line.details.length - 4} more`}</button> : null}
        </div>
    );
}

function ScoreBar({ share, good }: { share: number; good: boolean })
{
    return <span className={css.bar}><span className={good ? css.barFill : css.barFillWarn} style={{ width: `${Math.max(0, Math.min(1, share)) * 100}%` }} /></span>;
}

const STATE_GLYPH: Record<Job['state'], string> = { queued: '…', running: '▶', done: '✓', failed: '✗', cancelled: '–' };

export function JobsPanel()
{
    const actions = useActions();
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const python = useS((s) => s.python);
    const kind = useS((s) => String(card(s.project.state === 'ready' ? s.project.value.files : undefined).kind ?? 'indoor'));
    const overlay = useS((s) => Boolean(card(s.project.state === 'ready' ? s.project.value.files : undefined).base));
    const start: { kind: JobKind; label: string; python?: boolean }[] = [
        { kind: 'checks', label: 'Checks' },
        { kind: 'compare', label: 'Compare' },
        ...(kind === 'outdoor' ? [{ kind: 'town_feel' as const, label: 'Town feel', python: true }]
            : [{ kind: 'scale_bands' as const, label: 'Scale bands', python: true }]),
        { kind: 'pins_tour', label: 'Pins tour' },
        { kind: 'playtest', label: 'Playtest' },
        // S6: the repository's Cycles bake (Blender and the game, local only); the base map's bake stays an overlay's.
        ...(overlay ? [] : [{ kind: 'lighting_bake' as const, label: 'Bake lighting' }]),
    ];
    return (
        <div className={css.panel} data-testid="jobs">
            <div className={css.toolbar}>
                <span className={css.dim}>{jobs.length} jobs · lane J (checks, compare) and processes (Python, the game), one at a time each</span>
                <span className={css.spacer} />
                {start.map((entry) => (
                    <button key={entry.kind} type="button" className={css.button} disabled={entry.python && !python}
                        onClick={() => actions.startJob(entry.kind, entry.kind === 'playtest' ? { runs: 4 } : {})}>{entry.label}</button>
                ))}
            </div>
            <div className={css.scroll}>
                {jobs.length === 0 ? <div className={css.empty}>No jobs yet: the background checks start when the project opens.</div> : null}
                {jobs.map((job) => (
                    <div key={job.id} className={css.job} data-state={job.state}>
                        <span className={css[`state_${job.state}`]} title={job.state}>{STATE_GLYPH[job.state]}</span>
                        <span>{job.title}{job.background ? <span className={css.dim}> · background</span> : null}</span>
                        <span className={`${css.mono} ${job.revision === revision ? '' : css.dim}`} title={job.revision}>rev {job.revision.slice(0, 6)}</span>
                        <span className={css.dim}>{job.seconds !== null ? `${job.seconds} s` : job.state}</span>
                        <span className={css.jobLine} title={job.progress.join('\n')}>{job.line || job.error || ''}</span>
                        {job.state === 'queued' || job.state === 'running'
                            ? <button type="button" className={css.button} onClick={() => actions.cancelJob(job.id)}>Cancel</button>
                            : <span />}
                    </div>
                ))}
            </div>
        </div>
    );
}

// The pictures of the jobs: the pins tours' and building shots', grouped by job, newest first.
export function PicturesPanel()
{
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const results = useS((s) => s.jobResults);
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : null));
    const withPictures = jobs.filter((job) => job.state === 'done' && job.pictures.length > 0);
    if (withPictures.length === 0)
    {
        return <div className={css.empty}>No pictures yet. A pins tour (Pins: “Tour pins in the game”) or building shots take the game's own pictures; they show here by job and revision.</div>;
    }
    return (
        <div className={css.scroll} data-testid="pictures">
            {withPictures.map((job) => <ContactSheet key={job.id} job={job} result={results[job.id]} current={job.revision === revision} />)}
        </div>
    );
}

function ContactSheet({ job, result, current }: { job: Job; result: unknown; current: boolean })
{
    const captions = useMemo(() =>
    {
        const out = new Map<string, string>();
        if (job.kind === 'pins_tour' && result)
        {
            for (const shot of (result as PinsTourJobResult).shots)
            {
                if (shot.picture)
                {
                    out.set(shot.picture, shot.pin);
                }
            }
        }
        if (job.kind === 'lighting_bake' && result)
        {
            const bake = result as LightingBakeJobResult;
            if (bake.before)
            {
                out.set(bake.before, 'the game, before the bake');
            }
            if (bake.after)
            {
                out.set(bake.after, 'the game, with the bake');
            }
            bake.pages.forEach((page, index) => out.set(page.picture, `lightmap page ${index} (${page.width} × ${page.height})`));
        }
        if (job.kind === 'building_shots' && result)
        {
            for (const building of (result as BuildingShotsJobResult).buildings)
            {
                building.pictures.forEach((picture) => out.set(picture, `${building.id} ${picture.split('/').pop()?.replace(/\.jpg$/, '')}`));
            }
        }
        return out;
    }, [job, result]);
    return (
        <div className={`${css.sheet} ${current ? '' : css.stale}`}>
            <div className={css.sheetHead}>
                {job.title}
                <span className={css.dim}>{job.pictures.length} pictures · {new Date(job.finished ?? job.created).toLocaleString()}</span>
                <span className={current ? css.badge : css.badgeStale}>{current ? 'this revision' : `older revision ${job.revision.slice(0, 6)}`}</span>
            </div>
            <div className={css.thumbs}>
                {job.pictures.slice(0, 120).map((picture) => <Thumb key={picture} job={job} relative={picture} caption={captions.get(picture) ?? picture} />)}
            </div>
        </div>
    );
}

export function Thumb({ job, relative, caption }: { job: Job; relative: string; caption: string })
{
    const actions = useActions();
    const [url, setUrl] = useState<string | null>(null);
    useEffect(() =>
    {
        let live = true;
        void actions.jobFile(job, relative).then((found) => live && setUrl(found));
        return () =>
        {
            live = false;
        };
    }, [actions, job, relative]);
    return (
        <button type="button" className={css.thumb} onClick={() => url && actions.openLightbox(url, `${caption} · ${job.title} · rev ${job.revision.slice(0, 8)}`)}>
            {url ? <img src={url} alt={caption} /> : <img alt="" />}
            <span>{caption}</span>
        </button>
    );
}

export function Lightbox()
{
    const { store } = useStudioContext();
    const lightbox = useS((s) => s.lightbox);
    useEffect(() =>
    {
        const onKey = (event: KeyboardEvent) =>
        {
            if (event.code === 'Escape' && store.getState().lightbox)
            {
                event.stopPropagation();
                store.setState({ lightbox: null });
            }
        };
        window.addEventListener('keydown', onKey, true);
        return () => window.removeEventListener('keydown', onKey, true);
    }, [store]);
    if (!lightbox)
    {
        return null;
    }
    return (
        <figure className={css.lightbox} onClick={() => store.setState({ lightbox: null })} data-testid="lightbox">
            <img src={lightbox.url} alt={lightbox.caption} />
            <figcaption>{lightbox.caption}</figcaption>
        </figure>
    );
}

export { KIND_TITLES };
