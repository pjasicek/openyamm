// The frame (S5_BROWSER_EDITOR.md 3.1; wireframe W1): title bar, the views, the inspector, the drawer, the status
// bar. Fixed layout first (4.3). Review mode: nothing edits.
import { TitleBar, StatusBar } from './Bars.tsx';
import { Views } from './Views.tsx';
import { Inspector } from './Inspector.tsx';
import { Drawer } from './Drawer.tsx';
import { Lightbox } from './Checks.tsx';
import { ProjectList } from './ProjectList.tsx';
import { useS, useStudioContext } from './context.ts';
import { HostedStart, PairedBanner } from '../hosted/HostedStart.tsx';
import { NONE } from '../state/store.ts';
import { AuthorBanners, StageBar, ToolRail } from './Author.tsx';
import css from './Frame.module.css';

export function App()
{
    const key = useS((s) => s.projectKey);
    // The hosted page (S5c) starts with the game's files and a project of the person's; paired, with the host's list.
    const mode = useStudioContext().controller?.client.mode ?? 'local';
    if (key)
    {
        return <Frame />;
    }
    return (
        <div className={css.listPage}>
            {mode === 'hosted' ? <HostedStart />
                : mode === 'paired' ? <div className={css.listColumn}><PairedBanner /><ProjectList /></div> : <ProjectList />}
            <StatusBar />
        </div>
    );
}

export function Frame()
{
    const project = useS((s) => s.project);
    const unreadable = useS((s) => s.unreadable);
    const tall = useS((s) => s.drawerTab === 'pins' || s.drawerTab === 'history' || s.drawerTab === 'scorecard' || s.drawerTab === 'pictures'
        || s.drawerTab === 'overlay' || s.drawerTab === 'cinematics');
    const author = useS((s) => s.mode === 'author');
    return (
        <div className={css.frame} data-author={author || undefined} style={tall ? { '--drawer-height': '340px' } as React.CSSProperties : undefined}>
            <div className={css.title}><TitleBar /></div>
            {author ? <div className={css.stages}><StageBar /></div> : null}
            {author ? <div className={css.rail}><ToolRail /></div> : null}
            {project.state === 'error' ? (
                <div className={css.failed}>The project could not be opened: {project.message}</div>
            ) : unreadable ? (
                <div className={css.failed} data-testid="unreadable">A file of the project does not parse; the views keep its last good state and nothing can change until it parses: {unreadable}</div>
            ) : null}
            <div className={css.views}>{author ? <AuthorBanners /> : null}<div className={css.viewsInner}><Views /><Notes /></div></div>
            <div className={css.inspector}><Inspector /></div>
            <div className={css.drawer}><Drawer /></div>
            <div className={css.status}><StatusBar /></div>
            <Lightbox />
        </div>
    );
}

// What changed lately (an agent's edit, a pin answered, an agent connecting), over the views for a few seconds.
function Notes()
{
    const notes = useS((s) => (s.notes.length > 0 ? s.notes : NONE));
    if (notes.length === 0)
    {
        return null;
    }
    return (
        <div className={css.notes} aria-live="polite" data-testid="notes">
            {notes.map((note) => <div key={note.id} className={css[`note_${note.kind}`]}>{note.text}</div>)}
        </div>
    );
}
