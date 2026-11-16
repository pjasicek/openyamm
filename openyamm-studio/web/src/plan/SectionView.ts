// The plan's section view (S5_BROWSER_EDITOR.md 3.4; the design page's mock-nl-lift; S5b2): a side view of what a
// vertical cut crosses (plan/section.ts), rooms stacked by height with their floors, ceilings, floor parts, ceiling
// levels, and lifts and movers with their travel. Framework-free Canvas2D, read only: a click selects what it hits.
// Also the cut's line over the plan (SectionCut), drawn by a drag when armed.
import type { SectionLine, SectionSpan } from './section.ts';
import { sectionRange, spanAt } from './section.ts';
import type { PlanOverlay } from './PlanView.ts';

type ToScreen = (x: number, y: number) => [number, number];

const LEFT = 58;
const RIGHT = 14;
const TOP = 26;
const BOTTOM = 22;

export class SectionView
{
    private readonly canvas: HTMLCanvasElement;
    private readonly context: CanvasRenderingContext2D;
    private readonly observer: ResizeObserver;
    private spans: SectionSpan[] = [];
    private selection: string | null = null;
    private caption = '';
    private frame = { s0: 0, s1: 1, low: 0, high: 1 };
    private readonly onPick: (id: string | null) => void;

    constructor(root: HTMLElement, onPick: (id: string | null) => void)
    {
        this.onPick = onPick;
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'oy-section-canvas';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.display = 'block';
        root.append(this.canvas);
        this.context = this.canvas.getContext('2d')!;
        this.observer = new ResizeObserver(() => this.draw());
        this.observer.observe(root);
        this.canvas.addEventListener('click', this.onClick);
    }

    dispose(): void
    {
        this.observer.disconnect();
        this.canvas.remove();
    }

    set(spans: SectionSpan[], selection: string | null, caption: string): void
    {
        this.spans = spans;
        this.selection = selection;
        this.caption = caption;
        this.draw();
    }

    // The screen point of a section point (along the cut, height), in CSS pixels of the canvas (scripted runs).
    screenOf(along: number, height: number): [number, number]
    {
        const rect = this.canvas.getBoundingClientRect();
        const [x, y] = this.toScreen()(along, height);
        return [rect.left + x, rect.top + y];
    }

    private toScreen(): ToScreen
    {
        const width = Math.max(1, this.canvas.clientWidth - LEFT - RIGHT);
        const height = Math.max(1, this.canvas.clientHeight - TOP - BOTTOM);
        const { s0, s1, low, high } = this.frame;
        // One scale for both axes where it fits (a true side view), else each axis its own.
        const scaleX = width / Math.max(1, s1 - s0);
        const scaleY = height / Math.max(1, high - low);
        const scale = Math.min(scaleX, scaleY);
        const sx = scaleX / scale > 4 ? scaleX : scale;
        const sy = scaleY / scale > 4 ? scaleY : scale;
        const offsetX = LEFT + (width - (s1 - s0) * sx) / 2;
        const offsetY = TOP + (height - (high - low) * sy) / 2;
        return (along, z) => [offsetX + (along - s0) * sx, offsetY + (high - z) * sy];
    }

    private colour(name: string, fallback: string): string
    {
        return getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim() || fallback;
    }

    draw(): void
    {
        const ratio = window.devicePixelRatio || 1;
        const width = Math.max(1, this.canvas.clientWidth);
        const height = Math.max(1, this.canvas.clientHeight);
        if (this.canvas.width !== Math.round(width * ratio) || this.canvas.height !== Math.round(height * ratio))
        {
            this.canvas.width = Math.round(width * ratio);
            this.canvas.height = Math.round(height * ratio);
        }
        const context = this.context;
        context.setTransform(ratio, 0, 0, ratio, 0, 0);
        context.fillStyle = this.colour('canvas', '#16181c');
        context.fillRect(0, 0, width, height);
        const text = this.colour('text', '#e6e8eb');
        const dim = this.colour('text-dim', '#8d96a3');
        const edge = this.colour('plan-room-edge', '#8d96a3');
        const select = this.colour('plan-select', '#4a90e2');
        const room = this.colour('plan-room-low', '#2a2e36');
        const raised = this.colour('plan-room-high', '#3a3e47');
        const lift = '#d29a49';
        const mover = this.colour('plan-door', '#cc6666');
        context.font = '600 11px ui-sans-serif, system-ui, sans-serif';
        if (this.spans.length === 0)
        {
            context.fillStyle = dim;
            context.fillText(this.caption || 'The cut crosses nothing built: draw it across rooms', LEFT, TOP + 20);
            return;
        }
        const range = sectionRange(this.spans);
        const pad = Math.max(48, (range.high - range.low) * 0.08);
        this.frame = { s0: Math.min(...this.spans.map((span) => span.from)) - 64, s1: Math.max(...this.spans.map((span) => span.to)) + 64,
            low: range.low - pad, high: range.high + pad };
        const s = this.toScreen();
        // The heights of the floors: dashed across, with their numbers on the scale.
        context.font = '10px ui-monospace, monospace';
        context.strokeStyle = this.colour('plan-grid', '#2b313b');
        context.lineWidth = 1;
        let lastLabel = Infinity;
        for (const floor of [...range.floors].reverse())
        {
            const [, y] = s(0, floor);
            context.setLineDash([2, 3]);
            context.beginPath();
            context.moveTo(LEFT - 4, y);
            context.lineTo(width - RIGHT, y);
            context.stroke();
            context.setLineDash([]);
            if (Math.abs(y - lastLabel) >= 11)
            {
                context.fillStyle = dim;
                context.fillText(String(floor), 6, y + 3);
                lastLabel = y;
            }
        }
        const quad = (span: SectionSpan, bottom: [number, number], top: [number, number]) =>
        {
            const [x0, y0] = s(span.from, bottom[0]);
            const [x1, y1] = s(span.to, bottom[1]);
            const [x2, y2] = s(span.to, top[1]);
            const [x3, y3] = s(span.from, top[0]);
            context.beginPath();
            context.moveTo(x0, y0);
            context.lineTo(x1, y1);
            context.lineTo(x2, y2);
            context.lineTo(x3, y3);
            context.closePath();
        };
        // Rooms: the space between floor and ceiling, the floor drawn heavy.
        for (const span of this.spans.filter((entry) => entry.kind === 'room'))
        {
            const chosen = span.id === this.selection;
            quad(span, [span.floor, span.floorTo], [span.ceiling ?? span.floor, span.ceilingTo ?? span.floorTo]);
            context.fillStyle = chosen ? select : raised;
            context.globalAlpha = chosen ? 0.25 : 0.55;
            context.fill();
            context.globalAlpha = 1;
            context.strokeStyle = chosen ? select : edge;
            context.lineWidth = chosen ? 2.5 : 1;
            context.stroke();
            const [fx0, fy0] = s(span.from, span.floor);
            const [fx1, fy1] = s(span.to, span.floorTo);
            context.beginPath();
            context.moveTo(fx0, fy0);
            context.lineTo(fx1, fy1);
            context.strokeStyle = chosen ? select : text;
            context.lineWidth = 3;
            context.stroke();
        }
        // Floor parts at other heights (raised: solid down to the room's floor; sunken: hatched), ceiling levels.
        for (const span of this.spans.filter((entry) => entry.kind === 'level' || entry.kind === 'ceiling'))
        {
            quad(span, [span.ceiling!, span.ceilingTo!], [span.floor, span.floorTo]);
            if (span.kind === 'level')
            {
                context.fillStyle = span.floor >= (span.ceiling ?? 0) ? raised : this.colour('canvas', '#16181c');
                context.fill();
                const [x0, y0] = s(span.from, span.floor);
                const [x1] = s(span.to, span.floor);
                context.beginPath();
                context.moveTo(x0, y0);
                context.lineTo(x1, y0);
                context.strokeStyle = span.id === this.selection ? select : text;
                context.lineWidth = 3;
                context.stroke();
            }
            else
            {
                context.fillStyle = room;
                context.fill();
                context.setLineDash([3, 3]);
                context.strokeStyle = edge;
                context.lineWidth = 1;
                context.stroke();
                context.setLineDash([]);
            }
        }
        // Lifts and movers: the block where the map starts it, the travel dashed, an arrow and the distance.
        for (const span of this.spans.filter((entry) => entry.kind === 'lift' || entry.kind === 'mover' || entry.kind === 'plate'))
        {
            const chosen = span.id === this.selection;
            const tone = span.kind === 'lift' ? lift : span.kind === 'mover' ? mover : this.colour('warn', '#a35b00');
            const thickness = span.thickness ?? 8;
            const travel = span.travel ?? 0;
            const base = span.floor + (span.startsUp ? travel : 0);
            const [bottom, top] = span.kind === 'lift' ? [base - thickness, base] : [base, base + thickness];
            const [x0, y0] = s(span.from, top);
            const [x1, y1] = s(span.to, bottom);
            if (travel > 0)
            {
                const [, ty] = s(0, span.floor + travel + (span.kind === 'lift' ? 0 : thickness));
                const [, by] = s(0, span.kind === 'lift' ? span.floor - thickness : span.floor);
                context.fillStyle = tone;
                context.globalAlpha = 0.1;
                context.fillRect(x0, ty, x1 - x0, by - ty);
                context.globalAlpha = 1;
                context.setLineDash([4, 3]);
                context.strokeStyle = tone;
                context.lineWidth = 1;
                context.strokeRect(x0, ty, x1 - x0, by - ty);
                context.setLineDash([]);
                // The arrow from the start to the end.
                const ax = x1 + 8;
                const [, from] = s(0, span.floor);
                const [, to] = s(0, span.floor + travel);
                context.beginPath();
                context.moveTo(ax, from);
                context.lineTo(ax, to);
                context.lineTo(ax - 4, to + 7);
                context.moveTo(ax, to);
                context.lineTo(ax + 4, to + 7);
                context.strokeStyle = '#f2c14e';
                context.lineWidth = 1.5;
                context.stroke();
                context.fillStyle = '#f2d9a8';
                context.font = '600 11px ui-sans-serif, system-ui, sans-serif';
                context.fillText(String(travel), ax + 6, (from + to) / 2 + 4);
            }
            context.fillStyle = tone;
            context.fillRect(x0, y0, x1 - x0, Math.max(3, y1 - y0));
            context.strokeStyle = chosen ? select : tone;
            context.lineWidth = chosen ? 2.5 : 1;
            context.strokeRect(x0, y0, x1 - x0, Math.max(3, y1 - y0));
        }
        // Names: each room once, over its widest stretch.
        context.font = '600 11px ui-sans-serif, system-ui, sans-serif';
        const named = new Set<string>();
        for (const span of [...this.spans].sort((x, y) => (y.to - y.from) - (x.to - x.from)))
        {
            if (span.kind === 'level' || span.kind === 'ceiling' || named.has(span.id))
            {
                continue;
            }
            const [x0] = s(span.from, 0);
            const [x1] = s(span.to, 0);
            const label = span.id.replace(/^[a-z]+:/, '');
            if (x1 - x0 < context.measureText(label).width + 8)
            {
                continue;
            }
            named.add(span.id);
            const top = span.kind === 'room' ? Math.max(span.ceiling ?? span.floor, span.ceilingTo ?? span.floorTo)
                : span.floor + (span.travel ?? 0) + (span.thickness ?? 0) + 24;
            const [, y] = s(0, top);
            context.fillStyle = span.id === this.selection ? select : dim;
            context.fillText(label, x0 + 4, y - 4);
        }
        // The distance scale and the caption.
        context.fillStyle = dim;
        context.font = '10px ui-monospace, monospace';
        const [ax] = s(0, range.low);
        const [bx] = s(Math.max(...this.spans.map((span) => span.to)), range.low);
        context.fillText('A', ax - 3, height - 6);
        context.fillText('B', bx - 3, height - 6);
        context.font = '600 11px ui-sans-serif, system-ui, sans-serif';
        context.fillStyle = text;
        context.fillText(this.caption, LEFT, 16);
    }

    private readonly onClick = (event: MouseEvent) =>
    {
        if (this.spans.length === 0)
        {
            return;
        }
        const rect = this.canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        // The screen point back to (along, height) by the two axes' linear maps.
        const s = this.toScreen();
        const [x0, y0] = s(0, 0);
        const [x1, y1] = s(1000, 1000);
        const along = ((x - x0) / (x1 - x0)) * 1000;
        const z = ((y - y0) / (y1 - y0)) * 1000;
        const reach = Math.abs(6 / ((x1 - x0) / 1000));
        this.onPick(spanAt(this.spans, along, z, reach)?.id ?? null);
    };
}

// The cut's line over the plan: always drawn (A at its start, B at its end); armed, a drag on the plan draws it anew.
export class SectionCut implements PlanOverlay
{
    line: SectionLine | null = null;
    armed = false;
    private start: [number, number] | null = null;
    private now: [number, number] | null = null;
    private readonly onLine: (line: SectionLine) => void;
    private readonly redraw: () => void;

    constructor(onLine: (line: SectionLine) => void, redraw: () => void)
    {
        this.onLine = onLine;
        this.redraw = redraw;
    }

    private snap(at: [number, number]): [number, number]
    {
        return [Math.round(at[0] / 16) * 16, Math.round(at[1] / 16) * 16];
    }

    down(at: [number, number], event: PointerEvent): boolean
    {
        if (!this.armed || event.button !== 0)
        {
            return false;
        }
        this.start = this.snap(at);
        this.now = this.start;
        return true;
    }

    move(at: [number, number]): void
    {
        if (this.start)
        {
            this.now = this.snap(at);
            this.redraw();
        }
    }

    up(at: [number, number]): void
    {
        const start = this.start;
        this.start = null;
        this.now = null;
        const end = this.snap(at);
        if (start && Math.hypot(end[0] - start[0], end[1] - start[1]) >= 64)
        {
            this.armed = false;
            this.onLine({ a: start, b: end });
        }
        this.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const line = this.start && this.now ? { a: this.start, b: this.now } : this.line;
        if (!line)
        {
            return;
        }
        const [ax, ay] = s(line.a[0], line.a[1]);
        const [bx, by] = s(line.b[0], line.b[1]);
        context.save();
        context.strokeStyle = '#f2c14e';
        context.lineWidth = 2;
        context.setLineDash([8, 4]);
        context.beginPath();
        context.moveTo(ax, ay);
        context.lineTo(bx, by);
        context.stroke();
        context.setLineDash([]);
        context.fillStyle = '#f2c14e';
        context.font = '700 12px ui-sans-serif, system-ui, sans-serif';
        for (const [x, y, name] of [[ax, ay, 'A'], [bx, by, 'B']] as const)
        {
            context.beginPath();
            context.arc(x, y, 4, 0, Math.PI * 2);
            context.fill();
            context.fillText(name, x + 6, y - 6);
        }
        context.restore();
    }
}
