// The base of the plan's tools (S5_BROWSER_EDITOR.md 3.18): what a tool asks of the app, the files' rooms as the tools
// measure against, the drawing helpers, the base classes (a tool that takes clicks; one that draws an outline, a line
// or a box), and the room a block tool draws in. Kept apart from the tools themselves so every tool module can extend
// them (tools.ts, blocks.ts, plantools.ts).
import type { EditApplyResult, FileTrees, JsonObject, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import type { Gesture } from './session.ts';
import type { ToolName, ToolOptions } from './stages.ts';
import { splitAddress } from './keys.ts';
import type { Point } from './ops.ts';
import { GHOST, roomsOf } from './ops.ts';
import { box, distance, pathBand, pointInPolygon, selfCrossing, snapPoint } from './geometry.ts';
import type { Outline } from './geometry.ts';

export type ToScreen = (x: number, y: number) => [number, number];

// What a tool asks of the app.
export interface ToolHost
{
    files(): FileTrees | undefined;
    layout(): ViewLayoutResult | null;
    options(): ToolOptions;
    // The selection as an address (room:hall, room:hall/pillars/pillar2), or null.
    selection(): string | null;
    // `file` where the address alone does not say it (a plan space may share its id with its room).
    select(address: string | null, file?: string): void;
    edit(gesture: Gesture): Promise<EditApplyResult | null>;
    hint(text: string | null): void;
    note(text: string): void;
    redraw(): void;
    // Map units per screen pixel (for "near" in pixels).
    unitsPerPixel(): number;
    colour(name: string): string;
    // Another tool (the link tool ends in Select) and a change of the options (a space realised).
    setTool?(name: ToolName): void;
    setOptions?(change: Partial<ToolOptions>): void;
    // Outdoors (S5b2): the sculpt brush's preview in the 3D view (map units node by node over the land it has; null
    // puts the land back) and the built land's heights at cell points (view.terrain_query).
    landPreview?(delta: Float32Array | null): void;
    terrainHeights?(cells: Point[]): Promise<number[] | null>;
}

// What the plan view calls on the active tool. `down` returns whether the tool takes the press (else the plan pans
// or picks as in Review mode).
export interface PlanTool
{
    down(at: Point, event: PointerEvent): boolean;
    move(at: Point, event: PointerEvent, pressed: boolean): void;
    up(at: Point, event: PointerEvent): void;
    doubleClick(at: Point, event: MouseEvent): boolean;
    key(event: KeyboardEvent): boolean;
    draw(context: CanvasRenderingContext2D, s: ToScreen): void;
    cursor(): string;
    // After `up`: the press was a click the tool did not use (a part grabbed to move, not moved), so the plan picks
    // what lies there as in Review mode (S5b2).
    passClick?(): boolean;
}

// --- shapes of the files' rooms ------------------------------------------------------------------------------------

export interface RoomShape
{
    id: string;
    room: JsonObject;
    // The outline the tools measure against: the file's, else (a corridor) the built one, else the path's band.
    outline: Point[];
    path?: Point[];
    width?: number;
    ghost: boolean;
}

export function points(value: unknown): Point[]
{
    return Array.isArray(value) ? value.filter((p): p is Point => Array.isArray(p) && typeof p[0] === 'number' && typeof p[1] === 'number').map((p) => [p[0], p[1]]) : [];
}

export function roomShapes(files: FileTrees | undefined, layout: ViewLayoutResult | null): RoomShape[]
{
    if (!files)
    {
        return [];
    }
    const built = new Map((layout?.rooms ?? []).map((room) => [room.id, room.outline as Point[]]));
    return roomsOf(files).map((room) =>
    {
        const id = typeof room.id === 'string' ? room.id : '';
        const outline = points(room.outline);
        const path = points(room.path);
        const width = typeof room.width === 'number' ? room.width : 256;
        let shape = outline;
        if (shape.length < 3)
        {
            shape = built.get(id) ?? [];
        }
        if (shape.length < 3 && path.length >= 2)
        {
            // A rough hull of the band for hit tests until the core's layout answers.
            shape = pathBand(path, width).flat();
        }
        return { id, room, outline: shape, ...(path.length >= 2 ? { path, width } : {}), ghost: room[GHOST] === true };
    });
}

export function roomAt(shapes: readonly RoomShape[], at: Point): RoomShape | null
{
    let best: RoomShape | null = null;
    for (const shape of shapes)
    {
        const inside = shape.path
            ? pathBand(shape.path, shape.width ?? 256).some((quad) => pointInPolygon(at, quad))
            : pointInPolygon(at, shape.outline);
        if (inside && (!best || Number(shape.room.floor) > Number(best.room.floor)))
        {
            best = shape;
        }
    }
    return best;
}

// --- drawing helpers -----------------------------------------------------------------------------------------------

export function strokePath(context: CanvasRenderingContext2D, s: ToScreen, pts: readonly (readonly number[])[], closed: boolean): void
{
    context.beginPath();
    pts.forEach((p, i) =>
    {
        const [x, y] = s(p[0], p[1]);
        if (i === 0)
        {
            context.moveTo(x, y);
        }
        else
        {
            context.lineTo(x, y);
        }
    });
    if (closed)
    {
        context.closePath();
    }
}

export function handle(context: CanvasRenderingContext2D, s: ToScreen, p: readonly number[], colour: string, fill: string, size = 7): void
{
    const [x, y] = s(p[0], p[1]);
    context.fillStyle = fill;
    context.strokeStyle = colour;
    context.lineWidth = 1.5;
    context.fillRect(x - size / 2, y - size / 2, size, size);
    context.strokeRect(x - size / 2, y - size / 2, size, size);
}

export function label(context: CanvasRenderingContext2D, s: ToScreen, p: readonly number[], text: string, colour: string, background: string): void
{
    const [x, y] = s(p[0], p[1]);
    context.font = '600 11px ui-monospace, monospace';
    const width = context.measureText(text).width;
    context.fillStyle = background;
    context.fillRect(x + 8, y - 18, width + 8, 15);
    context.fillStyle = colour;
    context.fillText(text, x + 12, y - 7);
}

// --- the tools -----------------------------------------------------------------------------------------------------

export abstract class BaseTool implements PlanTool
{
    protected readonly host: ToolHost;
    // The pointer's last snapped place, for the ghost.
    protected cursorAt: Point | null = null;

    constructor(host: ToolHost)
    {
        this.host = host;
    }

    abstract down(at: Point, event: PointerEvent): boolean;

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void at;
        void event;
        void pressed;
    }

    up(at: Point, event: PointerEvent): void
    {
        void at;
        void event;
    }

    doubleClick(at: Point, event: MouseEvent): boolean
    {
        void at;
        void event;
        return false;
    }

    key(event: KeyboardEvent): boolean
    {
        void event;
        return false;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        void context;
        void s;
    }

    cursor(): string
    {
        return 'crosshair';
    }

    protected shapes(): RoomShape[]
    {
        return roomShapes(this.host.files(), this.host.layout());
    }

    protected reach(pixels = 9): number
    {
        return pixels * this.host.unitsPerPixel();
    }

    protected snap(at: Point, event: { shiftKey: boolean; altKey?: boolean }, previous: Point | null, exclude?: string): Point
    {
        const options = this.host.options();
        if (!options.snap || event.altKey)
        {
            return [Math.round(at[0]), Math.round(at[1])];
        }
        const outlines: Outline[] = this.shapes().filter((shape) => shape.id !== exclude).map((shape) => shape.outline);
        return snapPoint(at, { grid: options.grid, previous, free: event.shiftKey, outlines, reach: this.reach() }).point;
    }
}

// Click corners (or the points of a line); Enter, or a click on the first point, finishes; Backspace takes the last
// point back; Esc cancels. A drag from the first press makes a box when the tool takes boxes.
export abstract class DrawingTool extends BaseTool
{
    protected points: Point[] = [];
    private pressAt: Point | null = null;
    private boxing = false;
    protected abstract readonly closed: boolean;
    protected readonly boxes: boolean = false;
    protected readonly minimum: number = 3;

    protected abstract finish(points: Point[], asBox: boolean): void;

    protected abstract describe(): string;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const point = this.snap(at, event, this.points.at(-1) ?? null);
        if (this.points.length === 0 && this.boxes)
        {
            this.pressAt = point;
        }
        if (this.closed && this.points.length >= this.minimum && distance(point, this.points[0]) <= this.reach(10))
        {
            this.complete();
            return true;
        }
        if (this.points.length === 0 || distance(point, this.points.at(-1)!) > 0.5)
        {
            this.points.push(point);
        }
        this.cursorAt = point;
        this.host.hint(this.describe());
        this.host.redraw();
        return true;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        if (pressed && this.pressAt && this.points.length === 1)
        {
            const point = this.snap(at, { shiftKey: false, altKey: event.altKey }, null);
            if (distance(point, this.pressAt) > this.reach(6))
            {
                this.boxing = true;
            }
            this.cursorAt = point;
        }
        else
        {
            this.cursorAt = this.snap(at, event, this.points.at(-1) ?? null);
        }
        this.host.redraw();
    }

    up(at: Point, event: PointerEvent): void
    {
        if (this.boxing && this.pressAt)
        {
            const corner = this.snap(at, { shiftKey: false, altKey: event.altKey }, null);
            const made = box(this.pressAt, corner);
            this.boxing = false;
            this.pressAt = null;
            this.points = [];
            if (made)
            {
                this.finish(made.outline, true);
            }
            this.host.redraw();
            return;
        }
        this.pressAt = null;
    }

    key(event: KeyboardEvent): boolean
    {
        if (event.code === 'Enter' && this.points.length > 0)
        {
            this.complete();
            return true;
        }
        if (event.code === 'Escape' && this.points.length > 0)
        {
            this.cancel();
            return true;
        }
        if (event.code === 'Backspace' && this.points.length > 0)
        {
            this.points.pop();
            this.host.hint(this.points.length > 0 ? this.describe() : null);
            this.host.redraw();
            return true;
        }
        return false;
    }

    cancel(): void
    {
        this.points = [];
        this.boxing = false;
        this.pressAt = null;
        this.host.hint(null);
        this.host.redraw();
    }

    private complete(): void
    {
        const done = [...this.points];
        if (done.length < this.minimum)
        {
            this.host.note(`${this.closed ? 'An outline' : 'A line'} needs at least ${this.minimum} points (Esc cancels)`);
            return;
        }
        if (this.closed && selfCrossing(done))
        {
            this.host.note('The outline crosses itself: move or take back a corner (Backspace)');
            return;
        }
        this.points = [];
        this.host.hint(null);
        this.finish(done, false);
        this.host.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const accent = this.host.colour('plan-select');
        const surface = this.host.colour('surface');
        if (this.boxing && this.pressAt && this.cursorAt)
        {
            const made = box(this.pressAt, this.cursorAt);
            if (made)
            {
                strokePath(context, s, made.outline, true);
                context.fillStyle = accent;
                context.globalAlpha = 0.18;
                context.fill();
                context.globalAlpha = 1;
                context.strokeStyle = accent;
                context.setLineDash([6, 4]);
                context.lineWidth = 2;
                context.stroke();
                context.setLineDash([]);
                label(context, s, this.cursorAt, `${made.size[0]} × ${made.size[1]}`, this.host.colour('text'), surface);
            }
            return;
        }
        const line = this.cursorAt && this.points.length > 0 ? [...this.points, this.cursorAt] : this.points;
        if (line.length > 0)
        {
            this.drawBody(context, s, line);
            strokePath(context, s, line, false);
            context.strokeStyle = accent;
            context.lineWidth = 2;
            context.setLineDash([6, 4]);
            context.stroke();
            context.setLineDash([]);
            this.points.forEach((p, i) => handle(context, s, p, accent, i === 0 ? accent : surface, i === 0 ? 9 : 7));
        }
        if (this.cursorAt)
        {
            handle(context, s, this.cursorAt, accent, surface, 5);
            const last = this.points.at(-1);
            const text = last ? `${Math.round(distance(last, this.cursorAt))}` : `${this.cursorAt[0]}, ${this.cursorAt[1]}`;
            label(context, s, this.cursorAt, text, this.host.colour('text'), surface);
        }
    }

    // What the shape will be (a corridor's band, a room's fill).
    protected drawBody(context: CanvasRenderingContext2D, s: ToScreen, line: Point[]): void
    {
        if (this.closed && line.length >= 3)
        {
            strokePath(context, s, line, true);
            context.fillStyle = this.host.colour('plan-select');
            context.globalAlpha = 0.14;
            context.fill();
            context.globalAlpha = 1;
        }
    }
}

// The room a block tool draws in: the selected room, else the room under the first point.
export function hostRoom(host: ToolHost, shapes: RoomShape[], at: Point | null): RoomShape | null
{
    const selected = host.selection();
    if (selected)
    {
        const id = splitAddress(selected).id;
        const shape = shapes.find((entry) => entry.id === id);
        if (shape)
        {
            return shape;
        }
    }
    return at ? roomAt(shapes, at) : null;
}
