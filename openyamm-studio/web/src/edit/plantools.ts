// The Plan stage's tools (S5_BROWSER_EDITOR.md 3.18 "plan": "Plan stage: bubbles and links on an empty plan; drag
// bubbles; inspector"): Space (a click makes a planned space at that place, a drag moves its bubble), Plan link (a drag
// from one space to another) and Goal (a click on a space). A space without a room stands where its `at` says, as a
// dashed box of its extent or size class; a space a room realises stands on its room. Every gesture is one
// transaction; ids are the core's.
import type { FileTrees, JsonObject, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import { allocatedId } from './ops.ts';
import { isObject } from './keys.ts';
import { distance, pointInPolygon } from './geometry.ts';
import { BaseTool, label, roomShapes, strokePath } from './toolbase.ts';
import type { ToScreen } from './toolbase.ts';

// The side of a square of a size class's floor area (S5 common.schema.json size_class).
const SIZE_SIDE: Record<string, number> = { XS: 320, S: 560, M: 1000, L: 1500, XL: 2000 };

export interface SpacePlace
{
    id: string;
    name: string;
    kind: string;
    at: Point;
    // The box drawn for it: [width, depth].
    size: Point;
    // The room that realises it, or null (a ghost).
    room: string | null;
    // Placed by `at` (true) or put in the row under the map because it has neither a room nor `at`.
    placed: boolean;
    goals: string[];
}

function listOf(files: FileTrees | undefined, file: keyof FileTrees, name: string): JsonObject[]
{
    const value = files?.[file]?.tree[name];
    return Array.isArray(value) ? value.filter(isObject) : [];
}

function centre(outline: readonly Point[]): Point
{
    const xs = outline.map((p) => p[0]);
    const ys = outline.map((p) => p[1]);
    return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
}

// Where every space of plan.yml stands on the plan.
export function spacePlaces(files: FileTrees | undefined, layout: ViewLayoutResult | null): SpacePlace[]
{
    const spaces = listOf(files, 'plan.yml', 'spaces');
    if (spaces.length === 0)
    {
        return [];
    }
    const shapes = roomShapes(files, layout).filter((shape) => !shape.ghost && shape.outline.length >= 3);
    const realisedBy = new Map<string, Point[]>();
    for (const shape of shapes)
    {
        realisedBy.set(typeof shape.room.space === 'string' ? shape.room.space : shape.id, shape.outline);
    }
    const goals = listOf(files, 'plan.yml', 'goals');
    let bottom = 0;
    let left = 0;
    for (const shape of shapes)
    {
        for (const p of shape.outline)
        {
            bottom = Math.min(bottom, p[1]);
            left = Math.min(left, p[0]);
        }
    }
    let row = 0;
    return spaces.map((space) =>
    {
        const id = String(space.id ?? '');
        const extent = Array.isArray(space.extent) && typeof space.extent[0] === 'number' && typeof space.extent[1] === 'number'
            ? [space.extent[0], space.extent[1]] as Point : null;
        const side = SIZE_SIDE[String(space.size ?? 'M')] ?? 1000;
        const size: Point = extent ?? [side, side];
        const room = realisedBy.get(id);
        const own = Array.isArray(space.at) && typeof space.at[0] === 'number' && typeof space.at[1] === 'number' ? [space.at[0], space.at[1]] as Point : null;
        let at: Point;
        let placed = true;
        if (room)
        {
            at = centre(room);
        }
        else if (own)
        {
            at = own;
        }
        else
        {
            at = [left + row * 1200 + 500, bottom - 900];
            row += 1;
            placed = false;
        }
        const roomId = room ? shapes.find((shape) => shape.outline === room)?.id ?? null : null;
        return { id, name: String(space.name ?? ''), kind: String(space.kind ?? 'room'), at, size, room: roomId, placed,
            goals: goals.filter((goal) => goal.space === id).map((goal) => `${String(goal.kind ?? 'reach')}${goal.what ? ` ${String(goal.what)}` : ''}`) };
    });
}

export function spaceBox(place: SpacePlace): Point[]
{
    const [w, d] = place.size;
    const [x, y] = place.at;
    return [[x - w / 2, y - d / 2], [x + w / 2, y - d / 2], [x + w / 2, y + d / 2], [x - w / 2, y + d / 2]];
}

// The space under a point: a bubble's middle within reach, else a ghost's box.
export function spaceAt(places: readonly SpacePlace[], at: Point, reach: number): SpacePlace | null
{
    let best: SpacePlace | null = null;
    let bestDistance = Infinity;
    for (const place of places)
    {
        const d = distance(place.at, at);
        if (d <= Math.max(reach, 40) && d < bestDistance)
        {
            best = place;
            bestDistance = d;
        }
    }
    if (best)
    {
        return best;
    }
    for (const place of places)
    {
        if (!place.room && pointInPolygon(at, spaceBox(place)))
        {
            return place;
        }
    }
    return null;
}

// The plan's links between the places of their spaces.
export function planLinks(files: FileTrees | undefined): { id: string; from: string; to: string; kind: string; locked: boolean }[]
{
    return listOf(files, 'plan.yml', 'links').map((link) => ({ id: String(link.id ?? ''), from: String(link.from ?? ''), to: String(link.to ?? ''),
        kind: String(link.kind ?? 'open'), locked: link.condition !== undefined }));
}

// The plan's bubbles, links and goals over the plan (Author mode): ghosts dashed, the selection marked.
export function drawPlanBubbles(context: CanvasRenderingContext2D, s: ToScreen, files: FileTrees, layout: ViewLayoutResult | null,
    colour: (name: string) => string, selection: string | null, full: boolean): void
{
    const places = spacePlaces(files, layout);
    if (places.length === 0)
    {
        return;
    }
    const byId = new Map(places.map((place) => [place.id, place]));
    const link = colour('plan-link');
    const select = colour('plan-select');
    const text = colour('text');
    const surface = colour('surface');
    context.save();
    if (full)
    {
        for (const entry of planLinks(files))
        {
            const from = byId.get(entry.from);
            const to = byId.get(entry.to);
            if (!from || !to)
            {
                continue;
            }
            strokePath(context, s, [from.at, to.at], false);
            context.strokeStyle = entry.id === selection ? select : link;
            context.lineWidth = entry.id === selection ? 4 : 2.5;
            context.setLineDash(entry.locked ? [8, 4] : []);
            context.stroke();
            context.setLineDash([]);
            const middle: Point = [(from.at[0] + to.at[0]) / 2, (from.at[1] + to.at[1]) / 2];
            label(context, s, middle, `${entry.kind}${entry.locked ? ' 🔒' : ''}`, text, surface);
        }
    }
    for (const place of places)
    {
        const selected = place.id === selection;
        if (!place.room)
        {
            strokePath(context, s, spaceBox(place), true);
            context.fillStyle = select;
            context.globalAlpha = 0.07;
            context.fill();
            context.globalAlpha = 1;
            context.strokeStyle = selected ? select : colour('plan-room-edge');
            context.lineWidth = selected ? 2.5 : 1.5;
            context.setLineDash([7, 5]);
            context.stroke();
            context.setLineDash([]);
        }
        if (!full && place.room)
        {
            continue;
        }
        const [x, y] = s(place.at[0], place.at[1]);
        const name = place.name || place.id.replace(/^[a-z_]+:/, '');
        context.font = '600 12px ui-sans-serif, system-ui, sans-serif';
        const width = Math.max(56, context.measureText(name).width + 22);
        context.beginPath();
        context.ellipse(x, y, width / 2, 15, 0, 0, Math.PI * 2);
        context.fillStyle = surface;
        context.globalAlpha = place.room ? 0.92 : 0.8;
        context.fill();
        context.globalAlpha = 1;
        context.strokeStyle = selected ? select : place.room ? colour('good') : link;
        context.lineWidth = selected ? 3 : 2;
        context.setLineDash(place.room ? [] : [4, 3]);
        context.stroke();
        context.setLineDash([]);
        context.fillStyle = text;
        context.textAlign = 'center';
        context.fillText(name, x, y + 4);
        context.textAlign = 'start';
        if (place.goals.length > 0)
        {
            context.fillStyle = colour('warn');
            context.font = '600 11px ui-sans-serif, system-ui, sans-serif';
            context.fillText(`★ ${place.goals.join(' · ')}`, x - width / 2, y + 30);
        }
    }
    context.restore();
}

let serial = 0;

// Space: a click on an empty place makes a space there; a drag of a bubble without a room moves it.
export class SpaceTool extends BaseTool
{
    private drag: { place: SpacePlace; now: Point } | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const places = spacePlaces(this.host.files(), this.host.layout());
        const hit = spaceAt(places, at, this.reach(16));
        if (hit)
        {
            this.host.select(hit.id, 'plan.yml');
            if (!hit.room)
            {
                this.drag = { place: hit, now: hit.at };
            }
            return true;
        }
        const o = this.host.options();
        const point: Point = [Math.round(at[0] / 64) * 64, Math.round(at[1] / 64) * 64];
        const value: JsonObject = { kind: o.spaceKind, size: o.spaceSize, at: point };
        void this.host.edit({ label: `new space (${o.spaceKind}, ${o.spaceSize})`, mergeKey: `new space ${++serial} ${Date.now()}`,
            ops: [{ op: 'add', to: 'spaces', file: 'plan.yml', value }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                this.host.select(id, 'plan.yml');
            }
        });
        return true;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        if (pressed && this.drag)
        {
            this.drag.now = [Math.round(at[0] / 32) * 32, Math.round(at[1] / 32) * 32];
            this.host.hint(`${this.drag.place.id}: ${this.drag.now.join(', ')}`);
        }
        else
        {
            const hit = spaceAt(spacePlaces(this.host.files(), this.host.layout()), at, this.reach(16));
            this.host.hint(hit ? `${hit.id}${hit.room ? ` (the room ${hit.room})` : ''}: click selects, drag moves` : 'click: a new space here');
        }
        this.host.redraw();
    }

    up(): void
    {
        const drag = this.drag;
        this.drag = null;
        this.host.hint(null);
        if (!drag || distance(drag.now, drag.place.at) < 1)
        {
            this.host.redraw();
            return;
        }
        void this.host.edit({ label: `move ${drag.place.id}`, mergeKey: `move ${drag.place.id}`,
            ops: [{ op: 'patch', id: drag.place.id, file: 'plan.yml', patch: [{ op: 'add', path: '/at', value: drag.now }] }] });
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (this.drag)
        {
            const place = { ...this.drag.place, at: this.drag.now };
            strokePath(context, s, spaceBox(place), true);
            context.strokeStyle = this.host.colour('plan-select');
            context.lineWidth = 2;
            context.setLineDash([6, 4]);
            context.stroke();
            context.setLineDash([]);
        }
        else if (this.cursorAt)
        {
            const o = this.host.options();
            const side = SIZE_SIDE[o.spaceSize] ?? 1000;
            const ghost = { id: '', name: '', kind: o.spaceKind, at: this.cursorAt, size: [side, side] as Point, room: null, placed: true, goals: [] };
            if (!spaceAt(spacePlaces(this.host.files(), this.host.layout()), this.cursorAt, this.reach(16)))
            {
                strokePath(context, s, spaceBox(ghost), true);
                context.strokeStyle = this.host.colour('plan-select');
                context.globalAlpha = 0.5;
                context.setLineDash([3, 4]);
                context.lineWidth = 1;
                context.stroke();
                context.setLineDash([]);
                context.globalAlpha = 1;
            }
        }
    }

    cursor(): string
    {
        return this.drag ? 'grabbing' : 'crosshair';
    }
}

// Plan link: a drag from one space to another.
export class PlanLinkTool extends BaseTool
{
    private from: SpacePlace | null = null;
    private over: SpacePlace | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        this.from = spaceAt(spacePlaces(this.host.files(), this.host.layout()), at, this.reach(16));
        if (!this.from)
        {
            this.host.note('Start the drag on a space (its bubble) and end it on another');
        }
        this.cursorAt = at;
        return true;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        const over = spaceAt(spacePlaces(this.host.files(), this.host.layout()), at, this.reach(16));
        this.over = over && over.id !== this.from?.id ? over : null;
        if (pressed && this.from)
        {
            this.host.hint(this.over ? `${this.from.id} → ${this.over.id} (${this.host.options().planLinkKind}): release to link` : `from ${this.from.id}: drag onto another space`);
        }
        this.host.redraw();
    }

    up(): void
    {
        const from = this.from;
        const to = this.over;
        this.from = null;
        this.over = null;
        this.host.hint(null);
        this.host.redraw();
        if (!from || !to)
        {
            return;
        }
        const kind = this.host.options().planLinkKind;
        void this.host.edit({ label: `link ${from.id} → ${to.id}`, ops: [{ op: 'add', to: 'links', file: 'plan.yml', value: { from: from.id, to: to.id, kind } }] })
            .then((result) =>
            {
                const id = allocatedId(result?.ids_allocated);
                if (id)
                {
                    this.host.select(id, 'plan.yml');
                }
            });
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (!this.from || !this.cursorAt)
        {
            return;
        }
        strokePath(context, s, [this.from.at, this.over?.at ?? this.cursorAt], false);
        context.strokeStyle = this.host.colour('plan-link');
        context.lineWidth = 3;
        context.setLineDash([6, 4]);
        context.stroke();
        context.setLineDash([]);
    }
}

// Goal: a click on a space.
export class GoalTool extends BaseTool
{
    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const space = spaceAt(spacePlaces(this.host.files(), this.host.layout()), at, this.reach(16));
        if (!space)
        {
            this.host.note('Click a space (its bubble) to set a goal there');
            return true;
        }
        const o = this.host.options();
        const value: JsonObject = { space: space.id, kind: o.goalKind, ...(o.goalWhat.trim() ? { what: o.goalWhat.trim() } : {}) };
        void this.host.edit({ label: `goal: ${o.goalKind} in ${space.id}`, ops: [{ op: 'add', to: 'goals', file: 'plan.yml', value }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                this.host.select(id, 'plan.yml');
            }
        });
        return true;
    }

    move(at: Point): void
    {
        const space = spaceAt(spacePlaces(this.host.files(), this.host.layout()), at, this.reach(16));
        this.host.hint(space ? `click: ${this.host.options().goalKind} ${this.host.options().goalWhat} in ${space.id}` : 'click a space');
    }
}
