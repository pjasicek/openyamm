// The drawer (S5_BROWSER_EDITOR.md 3.10): Issues (by severity, errors first), Scorecard, Jobs and Pictures (Checks.tsx,
// S5a5), Pins (open first, with threads: Pins.tsx), History (History.tsx), Outline (every object by file and list),
// Library (Library.tsx) and Checklist (Checklist.tsx), S5b1 part 2. Long lists through one virtualiser (TanStack Virtual, 4.16).
import { useMemo, useRef } from 'react';
import { Tabs } from '@base-ui/react/tabs';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { IdPlace, Issue } from '../../../schema/rpc/generated/rpc.ts';
import { issueObject } from '../model/objects.ts';
import { knownIssues, NONE } from '../state/store.ts';
import type { DrawerTab } from '../state/store.ts';
import { PinsPanel } from './Pins.tsx';
import { HistoryPanel } from './History.tsx';
import { JobsPanel, PicturesPanel, ScorecardPanel } from './Checks.tsx';
import { LibraryPanel } from './Library.tsx';
import { ChecklistPanel } from './Checklist.tsx';
import { CinematicsPanel, OverlayPanel } from './S6Panels.tsx';
import { latestJobs } from '../model/scorecard.ts';
import { useActions, useS, useStudioContext } from './context.ts';
import css from './Drawer.module.css';

const SEVERITY_ORDER = ['error', 'warning', 'note'] as const;

export function Drawer()
{
    const { store } = useStudioContext();
    const tab = useS((s) => s.drawerTab);
    const issues = useS((s) => knownIssues(s));
    const pins = useS((s) => (s.pins.state === 'ready' ? s.pins.value.pins : NONE));
    const errors = issues.filter((issue) => issue.severity === 'error').length;
    // Pins that wait for someone: open, claimed, and resolved ones the person has not accepted yet.
    const open = pins.filter((pin) => !pin.status || pin.status === 'open' || pin.status === 'claimed' || pin.status === 'resolved').length;
    const historyCount = useS((s) => (s.history.state === 'ready' ? s.history.value.count : null));
    const jobs = useS((s) => (s.jobs.state === 'ready' ? s.jobs.value : NONE));
    const active = jobs.filter((job) => job.state === 'queued' || job.state === 'running').length;
    const pictures = jobs.filter((job) => job.state === 'done').reduce((sum, job) => sum + job.pictures.length, 0);
    // A string, not an object: a selector must give the same value for the same state.
    const compareText = useS((s) =>
    {
        const { done } = latestJobs(s.jobs.state === 'ready' ? s.jobs.value : NONE, 'compare', null);
        const result = done ? (s.jobResults[done.id] as { score?: number; band?: { within: boolean } } | undefined) : undefined;
        return result?.score !== undefined ? `${result.band?.within === true ? '+' : '-'}${(result.score * 100).toFixed(1)} %` : '';
    });
    const compareFigure = compareText ? { text: compareText.slice(1), good: compareText.startsWith('+') } : null;
    return (
        <Tabs.Root className={css.drawer} value={tab} onValueChange={(value) => store.setState({ drawerTab: value as DrawerTab })}>
            <Tabs.List className={css.tabs}>
                <Tabs.Tab className={css.tab} value="issues">
                    Issues <span className={errors > 0 ? css.countBad : css.count}>{issues.length}</span>
                </Tabs.Tab>
                <Tabs.Tab className={css.tab} value="scorecard" data-testid="tab-scorecard">Scorecard{compareFigure ? <span className={compareFigure.good ? css.count : css.countBad}>{compareFigure.text}</span> : null}</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="pins">Pins <span className={open > 0 ? css.countWarn : css.count}>{open}</span></Tabs.Tab>
                <Tabs.Tab className={css.tab} value="history">History{historyCount !== null ? <span className={css.count}>{historyCount}</span> : null}</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="jobs" data-testid="tab-jobs">Jobs{active > 0 ? <span className={css.countWarn}>{active}</span> : null}</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="pictures" data-testid="tab-pictures">Pictures{pictures > 0 ? <span className={css.count}>{pictures}</span> : null}</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="outline">Outline</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="library" data-testid="tab-library">Library</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="checklist" data-testid="tab-checklist">Checklist</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="cinematics" data-testid="tab-cinematics">Cinematics</Tabs.Tab>
                <Tabs.Tab className={css.tab} value="overlay" data-testid="tab-overlay">Overlay</Tabs.Tab>
            </Tabs.List>
            <Tabs.Panel className={css.panel} value="issues"><IssuesPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="scorecard"><ScorecardPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="pins"><PinsPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="history"><HistoryPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="jobs"><JobsPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="pictures"><PicturesPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="outline"><OutlinePanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="library"><LibraryPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="checklist"><ChecklistPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="cinematics"><CinematicsPanel /></Tabs.Panel>
            <Tabs.Panel className={css.panel} value="overlay"><OverlayPanel /></Tabs.Panel>
        </Tabs.Root>
    );
}

type IssueRow = { kind: 'head'; severity: string; count: number } | { kind: 'issue'; issue: Issue };

export function IssuesPanel()
{
    const actions = useActions();
    const issues = useS((s) => knownIssues(s));
    const validation = useS((s) => s.validation);
    const projectState = useS((s) => s.project.state);
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const author = useS((s) => s.mode === 'author');
    // Objects the last view build left out (2.4.2): listed first, with the core's note on each.
    const skipped = useS((s) => (s.layout.state === 'ready' ? s.layout.value.skipped_issues ?? NONE : NONE));
    const rows = useMemo<IssueRow[]>(() =>
    {
        const out: IssueRow[] = [];
        if (skipped.length > 0)
        {
            out.push({ kind: 'head', severity: 'skipped', count: skipped.length });
            skipped.forEach((issue) => out.push({ kind: 'issue', issue }));
        }
        for (const severity of SEVERITY_ORDER)
        {
            const group = issues.filter((issue) => issue.severity === severity);
            if (group.length > 0)
            {
                out.push({ kind: 'head', severity, count: group.length });
                group.forEach((issue) => out.push({ kind: 'issue', issue }));
            }
        }
        return out;
    }, [issues, skipped]);
    const scroller = useRef<HTMLDivElement>(null);
    const virtual = useVirtualizer({ count: rows.length, getScrollElement: () => scroller.current, estimateSize: () => 24, overscan: 12 });

    const state = validation.state === 'loading' ? <span className={css.checking}>checking…</span>
        : validation.state === 'error' ? <span className={css.bad}>the check failed: {validation.message}</span>
        : validation.state === 'ready' ? <span className={css.dim}>{validation.value.with_assets ? 'checked with the asset root' : 'checked without assets'}{validation.value.notes.length ? ` · ${validation.value.notes.join(' ')}` : ''}</span>
        : null;
    if (projectState === 'loading')
    {
        return <div className={css.empty}>Opening…</div>;
    }
    return (
        <div className={css.column}>
            <div className={css.toolbar}>
                {SEVERITY_ORDER.map((severity) => (
                    <span key={severity} className={css[`sev_${severity}`]}>{issues.filter((issue) => issue.severity === severity).length} {severity}s</span>
                ))}
                {state}
                <span className={css.spacer} />
                <button type="button" className={css.button} onClick={() => actions.revalidate()} disabled={validation.state === 'loading'}>Check again</button>
            </div>
            {rows.length === 0 ? (
                <div className={css.empty}>{validation.state === 'ready' ? 'No issues.' : validation.state === 'loading' ? 'No issues in the files; the full check is running.' : 'No issues known.'}</div>
            ) : (
                <div ref={scroller} className={css.scroll}>
                    <div className={css.sizer} style={{ height: virtual.getTotalSize() }}>
                        {virtual.getVirtualItems().map((item) =>
                        {
                            const row = rows[item.index];
                            const top = { transform: `translateY(${item.start}px)` };
                            if (row.kind === 'head')
                            {
                                return <div key={item.key} className={`${css.row} ${css.head}`} style={top}><span className={css[`sev_${row.severity}`]}>{row.severity}</span> {row.count}</div>;
                            }
                            const target = issueObject(files, row.issue);
                            return (
                                <div key={item.key} className={css.row} style={top}>
                                    <span className={css[`dot_${row.issue.severity}`]} aria-label={row.issue.severity} />
                                    <span className={css.code}>{row.issue.code}</span>
                                    <span className={css.where}>{row.issue.file}{row.issue.path ? `: ${row.issue.path}` : ''}</span>
                                    <span className={css.message} title={row.issue.message}>{row.issue.message}</span>
                                    {target ? <button type="button" className={css.link} onClick={() => actions.select(target, true)}>{target.id}</button> : null}
                                    {author ? (row.issue.fixes ?? []).map((fix, index) => (
                                        <button key={index} type="button" className={css.fix} title={`Fix: ${fix.label} (one change, undone with Ctrl Z)`}
                                            data-testid={`fix-${item.index}-${index}`}
                                            onClick={() => void actions.edit({ label: `fix: ${fix.label}`, ops: fix.ops }).then(() => actions.revalidate())}>{fix.label}</button>
                                    )) : null}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}

type OutlineRow = { kind: 'head'; label: string } | { kind: 'id'; place: IdPlace };

export function OutlinePanel()
{
    const actions = useActions();
    const ids = useS((s) => (s.project.state === 'ready' ? s.project.value.ids : NONE));
    const selection = useS((s) => s.selection);
    const rows = useMemo<OutlineRow[]>(() =>
    {
        const out: OutlineRow[] = [];
        let last = '';
        for (const place of ids)
        {
            const label = `${place.file} · ${place.list}`;
            if (label !== last)
            {
                out.push({ kind: 'head', label });
                last = label;
            }
            out.push({ kind: 'id', place });
        }
        return out;
    }, [ids]);
    const scroller = useRef<HTMLDivElement>(null);
    const virtual = useVirtualizer({ count: rows.length, getScrollElement: () => scroller.current, estimateSize: () => 22, overscan: 16 });
    if (rows.length === 0)
    {
        return <div className={css.empty}>No objects.</div>;
    }
    return (
        <div ref={scroller} className={css.scroll}>
            <div className={css.sizer} style={{ height: virtual.getTotalSize() }}>
                {virtual.getVirtualItems().map((item) =>
                {
                    const row = rows[item.index];
                    const top = { transform: `translateY(${item.start}px)` };
                    if (row.kind === 'head')
                    {
                        return <div key={item.key} className={`${css.row} ${css.head}`} style={top}>{row.label}</div>;
                    }
                    const selected = selection?.id === row.place.id && (!selection.file || selection.file === row.place.file);
                    return (
                        <div key={item.key} className={`${css.row} ${selected ? css.selected : ''}`} style={top}
                            onClick={() => actions.select({ id: row.place.id, file: row.place.file })}
                            onDoubleClick={() => actions.select({ id: row.place.id, file: row.place.file }, true)}>
                            <span className={css.outlineId}>{row.place.id}</span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
