// The title bar and the status bar of the frame (S5_BROWSER_EDITOR.md 3.1).
import { ToggleGroup } from '@base-ui/react/toggle-group';
import { Toggle } from '@base-ui/react/toggle';
import { useActions, useS, useStudioContext } from './context.ts';
import { Search } from './Search.tsx';
import { ModeSwitch, ProjectSettings } from './Author.tsx';
import type { ViewMode } from '../state/store.ts';
import { walkStatus } from '../walk/input.ts';
import { HostedMenu } from '../hosted/HostedMenu.tsx';
import css from './Bars.module.css';

export function TitleBar()
{
    const { store } = useStudioContext();
    const actions = useActions();
    const key = useS((s) => s.projectKey);
    const name = useS((s) => (s.project.state === 'ready' ? String((s.project.value.files['project.yml']?.tree as Record<string, unknown> | undefined)?.name ?? '') : ''));
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : ''));
    const viewMode = useS((s) => s.viewMode);
    return (
        <header className={css.title}>
            <button type="button" className={css.brand} onClick={() => actions.closeProject()} title="All projects">Map Studio</button>
            <span className={css.project}>
                <span className={css.name}>{name || '…'}</span>
                <span className={css.key} title={key ?? ''}>{key}</span>
                {revision ? <span className={css.revision} title={revision}>rev {revision.slice(0, 6)}</span> : null}
            </span>
            <Search />
            <span className={css.spacer} />
            <HostedMenu />
            <ProjectSettings />
            <ModeSwitch />
            <ToggleGroup
                className={css.views}
                value={[viewMode]}
                onValueChange={(value) =>
                {
                    if (value.length === 0)
                    {
                        return;
                    }
                    if (value[0] === 'compare')
                    {
                        actions.enterCompare();
                        return;
                    }
                    store.setState({ viewMode: value[0] as ViewMode, maximised: null });
                }}
                aria-label="Views"
            >
                <Toggle value="plan" className={css.view}>Plan</Toggle>
                <Toggle value="split" className={css.view}>Split</Toggle>
                <Toggle value="3d" className={css.view}>3D</Toggle>
                <Toggle value="compare" className={css.view} title="The original beside the rebuild, cameras locked (a rebuild's map_stats.reference)" data-testid="view-compare">Compare</Toggle>
                <Toggle value="flow" className={css.view} title="The flow graph: what opens in which step, and the wiring" data-testid="view-flow">Flow</Toggle>
                <Toggle value="board" className={css.view} title="The switch board: events against the doors, lifts and levers they move, editable cell by cell" data-testid="view-board">Board</Toggle>
            </ToggleGroup>
        </header>
    );
}

export function StatusBar()
{
    const cursor = useS((s) => s.cursor);
    const hover = useS((s) => s.hover);
    const connection = useS((s) => s.connection);
    const revision = useS((s) => (s.project.state === 'ready' ? s.project.value.revision : ''));
    const layoutStale = useS((s) => s.layout.state === 'ready' && s.layout.value.stale);
    const note = useS((s) => s.textureNote);
    const unreadable = useS((s) => s.unreadable);
    const latest = useS((s) => s.notes.at(-1) ?? null);
    const clients = useS((s) => s.clients);
    const agents = clients.filter((client) => client.kind === 'mcp');
    const browsers = clients.filter((client) => client.kind === 'browser').length;
    const walk = useS((s) => s.walk);
    const hint = useS((s) => (s.mode === 'author' ? s.hint : null));
    const mode = useStudioContext().controller?.client.mode ?? 'local';
    const ok = mode === 'hosted' ? 'core ok (in this page)' : mode === 'paired' ? 'paired with the studio' : 'host ok';
    return (
        <footer className={css.status}>
            {walk.state === 'on' && walk.pose && walk.kind
                ? <span className={css.cell} data-testid="walk-status">{walkStatus(walk.pose, walk.kind)}</span>
                : <span className={css.cell}>{cursor ? `X ${cursor[0]}  Y ${cursor[1]}  Z ${cursor[2]}` : 'X —  Y —  Z —'}</span>}
            <span className={css.cell}>{hover?.owner ?? ''}</span>
            {hint ? <span className={css.hint} title={hint} data-testid="tool-hint">{hint}</span> : null}
            {layoutStale ? <span className={css.stale}>stale view</span> : null}
            {unreadable ? <span className={css.bad} title={unreadable}>a file does not parse: read only</span> : null}
            {latest ? <span className={css.change} title={latest.text} data-testid="latest-note">{latest.text}</span>
                : note ? <span className={css.note} title={note}>{note}</span> : null}
            <span className={css.spacer} />
            {clients.length > 0 ? (
                <span className={css.presence} title={clients.map((client) => `${client.name}${client.project ? ` (${client.project})` : ''}`).join('\n')} data-testid="presence">
                    {browsers} {browsers === 1 ? 'browser' : 'browsers'}{agents.length > 0 ? <> · <b>{agents.map((agent) => agent.name).join(', ')}</b></> : ' · no agent'}
                </span>
            ) : null}
            <span className={css.cell}>{revision ? `rev ${revision.slice(0, 8)}` : ''}</span>
            <span className={connection === 'open' ? css.ok : css.bad}>
                {connection === 'open' ? ok : connection === 'connecting' ? 'connecting…' : 'disconnected'}
            </span>
        </footer>
    );
}
