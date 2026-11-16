// The plan's section view (S5_BROWSER_EDITOR.md 3.4; the design page's mock-nl-lift; S5b2): a panel over the plan's
// foot showing a side cut through the map, along a line drawn on the plan ("Draw a cut") or along the selected room's
// long axis, with floors, ceilings, floor parts, ceiling levels and lifts with their travel stacked by height. Read only;
// a click in it selects what it hits.
import { useEffect, useMemo, useRef, useState } from 'react';
import type { PlanView } from '../plan/PlanView.ts';
import { SectionCut, SectionView } from '../plan/SectionView.ts';
import type { SectionLine } from '../plan/section.ts';
import { longAxis, sectionRange, sectionSpans } from '../plan/section.ts';
import { objectBlocks } from '../edit/blocks.ts';
import { roomShapes } from '../edit/toolbase.ts';
import { probe } from '../app/controller.ts';
import { useActions, useS } from './context.ts';
import css from './Section.module.css';

export function SectionPanel({ plan }: { plan: PlanView | null })
{
    const actions = useActions();
    const layout = useS((s) => (s.layout.state === 'ready' ? s.layout.value : null));
    const files = useS((s) => (s.project.state === 'ready' ? s.project.value.files : undefined));
    const selection = useS((s) => s.selection?.id ?? null);
    const [open, setOpen] = useState(false);
    const [drawn, setDrawn] = useState<SectionLine | null>(null);
    const [armed, setArmed] = useState(false);
    const host = useRef<HTMLDivElement>(null);
    const [view, setView] = useState<SectionView | null>(null);

    // The cut: the one drawn, else along the long axis of the selection's room (a block's room for a lift or a
    // room's part), else none.
    const along = useMemo<SectionLine | null>(() =>
    {
        if (drawn || !selection)
        {
            return null;
        }
        const id = selection.split('/')[0];
        const block = objectBlocks(files, layout).find((entry) => entry.id === id);
        const roomId = block ? block.room : id;
        const outline = layout?.rooms.find((room) => room.id === roomId)?.outline
            ?? roomShapes(files, layout).find((shape) => shape.id === roomId)?.outline;
        return outline && outline.length >= 3 ? longAxis(outline) : null;
    }, [drawn, selection, files, layout]);
    const line = drawn ?? along;
    const spans = useMemo(() => (line && open ? sectionSpans(layout, files, line) : []), [line, open, layout, files]);
    const cut = useMemo(() => new SectionCut((made) => { setDrawn(made); setArmed(false); }, () => plan?.redraw()), [plan]);

    useEffect(() =>
    {
        cut.line = open ? line : null;
        cut.armed = open && armed;
        plan?.setOverlay(open ? cut : null);
        plan?.redraw();
    }, [plan, cut, open, line, armed]);
    useEffect(() => () => plan?.setOverlay(null), [plan]);
    useEffect(() =>
    {
        if (!open || !host.current)
        {
            return;
        }
        const made = new SectionView(host.current, (id) =>
        {
            actions.select(id ? { id, file: id.startsWith('room:') ? 'rooms.yml' : 'objects.yml' } : null);
        });
        setView(made);
        (probe() as { section?: unknown }).section = made;
        return () =>
        {
            made.dispose();
            setView(null);
        };
    }, [open, actions]);
    useEffect(() =>
    {
        if (!view)
        {
            return;
        }
        const range = sectionRange(spans);
        const name = drawn ? 'the cut drawn' : selection ? `along ${selection.split('/')[0]}` : '';
        const caption = !line ? 'Select a room, or draw a cut across the plan'
            : `Section A–B ${name} · ${Math.round(Math.hypot(line.b[0] - line.a[0], line.b[1] - line.a[1]))} long · floors ${range.floors.join(', ') || '–'}`;
        view.set(spans, selection, caption);
    }, [view, spans, selection, line, drawn]);

    if (!open)
    {
        return (
            <button type="button" className={css.toggle} data-testid="section-toggle" onClick={() => setOpen(true)}
                title="A side section through the map: floors stacked by height, lifts with their travel">Section</button>
        );
    }
    return (
        <div className={css.panel} data-testid="section-panel" onPointerDown={(event) => event.stopPropagation()}>
            <div className={css.bar}>
                <span className={css.label}>Section</span>
                <button type="button" className={armed ? css.on : css.button} data-testid="section-draw" onClick={() => setArmed(!armed)}
                    title="Drag a line across the plan: the section follows it">{armed ? 'drag on the plan…' : 'Draw a cut'}</button>
                <button type="button" className={css.button} disabled={!drawn} data-testid="section-along" onClick={() => setDrawn(null)}
                    title="Back to the selected room's long axis">Along the selection</button>
                <span className={css.spacer} />
                <span className={css.dim}>{spans.length > 0 ? `${new Set(spans.map((span) => span.id)).size} objects crossed · click one to select it` : ''}</span>
                <button type="button" className={css.button} data-testid="section-close" onClick={() => { setOpen(false); setArmed(false); }}>Close</button>
            </div>
            <div ref={host} className={css.canvas} data-testid="section-canvas" />
        </div>
    );
}
