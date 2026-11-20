// The 3D view's travel scrubber (S5_BROWSER_EDITOR.md 3.5, 3.18; S5b2): with a door, lift or mover selected, a slider
// over the view moves it through its travel on the client (viewport/travel.ts; no core call per frame). Let go, it
// returns to the state the map starts in, unless "hold" keeps the pose as a view (never written).
import { useEffect, useMemo, useRef, useState } from 'react';
import type { Viewport } from '../viewport/Viewport.ts';
import { shareText, travelOf, travelSize, travelWords } from '../viewport/travel.ts';
import { useS } from './context.ts';
import css from './Scrubber.module.css';

export function TravelScrubber({ viewport }: { viewport: Viewport | null })
{
    const selection = useS((s) => s.selection?.id ?? null);
    const layout = useS((s) => (s.layout.state === 'ready' ? s.layout.value : null));
    const meshReady = useS((s) => s.mesh.state === 'ready');
    const walking = useS((s) => s.walk.state !== 'off');
    const travel = useMemo(() => travelOf(layout, selection), [layout, selection]);
    const rest = travel?.startsOpen ? 1 : 0;
    const [share, setShare] = useState(rest);
    const [hold, setHold] = useState(false);
    const [playing, setPlaying] = useState(false);
    const frame = useRef(0);

    // A new selection rests where the map starts it.
    useEffect(() =>
    {
        setShare(rest);
        setPlaying(false);
    }, [travel?.id, rest]);
    useEffect(() =>
    {
        viewport?.setTravel(travel && meshReady && !walking ? travel : null, share);
    }, [viewport, travel, share, meshReady, walking]);
    useEffect(() => () => viewport?.setTravel(null, 0), [viewport]);
    // Play: through the travel and back in three seconds, then at rest again.
    useEffect(() =>
    {
        if (!playing)
        {
            return;
        }
        const start = performance.now();
        const step = (now: number) =>
        {
            const phase = (now - start) / 3000;
            if (phase >= 1)
            {
                setShare(rest);
                setPlaying(false);
                return;
            }
            const there = phase < 0.5 ? phase * 2 : 2 - phase * 2;
            setShare(rest === 1 ? 1 - there : there);
            frame.current = requestAnimationFrame(step);
        };
        frame.current = requestAnimationFrame(step);
        return () => cancelAnimationFrame(frame.current);
    }, [playing, rest]);

    if (!travel || walking || !meshReady)
    {
        return null;
    }
    const [low, high] = travelWords(travel);
    const letGo = () =>
    {
        if (!hold)
        {
            setShare(rest);
        }
    };
    return (
        <div className={css.scrubber} data-testid="travel-scrubber" onPointerDown={(event) => event.stopPropagation()}>
            <span className={css.name} title={`${travel.id}: ${travelSize(travel)}; the map starts it ${rest ? high : low}`}>
                {travel.id} <span className={css.dim}>{travelSize(travel)}</span>
            </span>
            <span className={css.end}>{low}</span>
            <input type="range" className={css.range} min={0} max={1000} step={1} value={Math.round(share * 1000)} data-testid="travel-range"
                aria-label={`Travel of ${travel.id}`}
                onChange={(event) => { setPlaying(false); setShare(Number(event.target.value) / 1000); }}
                onPointerUp={letGo} onKeyUp={letGo} onBlur={letGo} />
            <span className={css.end}>{high}</span>
            <span className={css.share} data-testid="travel-share" title={`the map starts it ${rest ? high : low}`}>{shareText(travel, share)}</span>
            <button type="button" className={css.button} onClick={() => setPlaying(!playing)} title="Through its travel and back">{playing ? 'stop' : 'play'}</button>
            <label className={css.hold} title="Keep the pose when let go (a view only: nothing is written)">
                <input type="checkbox" checked={hold} onChange={(event) => { setHold(event.target.checked); if (!event.target.checked) setShare(rest); }} /> hold
            </label>
        </div>
    );
}
