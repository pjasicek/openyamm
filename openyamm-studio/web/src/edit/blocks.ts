// Part two's indoor tools (S5_BROWSER_EDITOR.md 3.18): the blocks of objects.yml that move or mark a floor (Lift,
// Mover, Plate: "draw the block"; Floor: a click turns a floor to lava or water; Ladder: a drag up onto what it climbs)
// and the per-word tools inside a room (Height points, Flight, Parapet, Beam, Ceiling level). Each gesture is one
// transaction; an id the core must give first (a level or platform a floor names) comes in a first transaction of
// the same history entry (merge_key). The plan draws these blocks from the files (drawBlocks).
import type { FileTrees, JsonObject, JsonValue, Op, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import { allocatedId, appendItemOp, appendedKey } from './ops.ts';
import { isObject, keysOf, segment } from './keys.ts';
import { box, counterClockwise, distance, nearestOnSegment, pointInPolygon } from './geometry.ts';
import {
    BaseTool, DrawingTool, handle, hostRoom, label, points as pointsOf, roomAt, roomShapes, strokePath,
} from './toolbase.ts';
import type { RoomShape, ToScreen, ToolHost } from './toolbase.ts';
import { blocksOf } from './tools.ts';

let serial = 0;

function list(files: FileTrees | undefined, name: string): JsonObject[]
{
    const value = files?.['objects.yml']?.tree[name];
    return Array.isArray(value) ? value.filter(isObject) : [];
}

function rectangle(at: Point, size: Point): Point[]
{
    const [w, h] = size;
    return [[at[0] - w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] + h / 2], [at[0] - w / 2, at[1] + h / 2]];
}

// --- the blocks of objects.yml on the plan ---------------------------------------------------------------------------

export interface ObjectBlock
{
    id: string;
    list: 'lifts' | 'movers' | 'plates' | 'ladders';
    room: string;
    outline: Point[];
    // A ladder: its foot and the way the climber looks; a leaning ladder's top on the plan (S6 L).
    at?: Point;
    facing?: number;
    top?: Point;
    // Floors of objects.yml naming it (lava, water).
    floor?: string;
}

// Where a block stands as the files say it (`at` and `size`, an outline, or `offset` from the room's middle).
export function objectBlocks(files: FileTrees | undefined, layout: ViewLayoutResult | null): ObjectBlock[]
{
    if (!files)
    {
        return [];
    }
    const shapes = new Map(roomShapes(files, layout).map((shape) => [shape.id, shape]));
    const floors = new Map(list(files, 'floors').map((floor) => [String(floor.of), String(floor.kind)]));
    const out: ObjectBlock[] = [];
    for (const name of ['lifts', 'movers', 'plates'] as const)
    {
        for (const item of list(files, name))
        {
            const id = String(item.id ?? '');
            const room = String(item.room ?? '');
            let outline = pointsOf(item.outline);
            if (outline.length < 3)
            {
                const size = pointsOf([item.size])[0] ?? [64, 64];
                let at = pointsOf([item.at])[0];
                if (!at)
                {
                    const shape = shapes.get(room);
                    const xs = shape?.outline.map((p) => p[0]) ?? [0];
                    const ys = shape?.outline.map((p) => p[1]) ?? [0];
                    const middle: Point = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
                    const offset = pointsOf([item.offset])[0] ?? [0, 0];
                    at = [middle[0] + offset[0], middle[1] + offset[1]];
                }
                outline = rectangle(at, size);
            }
            out.push({ id, list: name, room, outline, ...(floors.has(id) ? { floor: floors.get(id) } : {}) });
        }
    }
    for (const item of list(files, 'ladders'))
    {
        const at = pointsOf([item.at])[0];
        if (!at)
        {
            continue;
        }
        const facing = typeof item.facing === 'number' ? item.facing : 0;
        const width = typeof item.width === 'number' ? item.width : 96;
        const a = (facing * Math.PI) / 180;
        const along: Point = [-Math.sin(a) * width / 2, Math.cos(a) * width / 2];
        const back: Point = [-Math.cos(a) * 16, -Math.sin(a) * 16];
        const top = pointsOf([item.top_at])[0];
        if (top && Math.hypot(top[0] - at[0], top[1] - at[1]) > 1)
        {
            // Leaning: the strip from the foot to the top, as it stands over the plan.
            out.push({ id: String(item.id ?? ''), list: 'ladders', room: String(item.room ?? ''), at, facing, top,
                outline: [[at[0] - along[0], at[1] - along[1]], [at[0] + along[0], at[1] + along[1]],
                    [top[0] + along[0], top[1] + along[1]], [top[0] - along[0], top[1] - along[1]]] });
            continue;
        }
        out.push({ id: String(item.id ?? ''), list: 'ladders', room: String(item.room ?? ''), at, facing,
            outline: [[at[0] - along[0], at[1] - along[1]], [at[0] + along[0], at[1] + along[1]],
                [at[0] + along[0] + back[0], at[1] + along[1] + back[1]], [at[0] - along[0] + back[0], at[1] - along[1] + back[1]]] });
    }
    return out;
}

export function blockAt(blocks: readonly ObjectBlock[], at: Point): ObjectBlock | null
{
    let best: ObjectBlock | null = null;
    for (const block of blocks)
    {
        if (pointInPolygon(at, block.outline))
        {
            best = block;
        }
    }
    return best;
}

export function drawBlocks(context: CanvasRenderingContext2D, s: ToScreen, files: FileTrees, layout: ViewLayoutResult | null,
    colour: (name: string) => string, selection: string | null, hover: string | null): void
{
    const shapes = roomShapes(files, layout);
    context.save();
    for (const block of objectBlocks(files, layout))
    {
        const marked = block.id === selection ? colour('plan-select') : block.id === hover ? colour('plan-hover') : null;
        strokePath(context, s, block.outline, true);
        const tone = block.list === 'lifts' ? colour('plan-link') : block.list === 'movers' ? colour('plan-door')
            : block.list === 'plates' ? colour('warn') : colour('plan-thing');
        context.fillStyle = block.floor === 'lava' ? '#d4532a' : block.floor ? '#3a7bd5' : tone;
        context.globalAlpha = block.floor ? 0.45 : 0.22;
        context.fill();
        context.globalAlpha = 1;
        context.strokeStyle = marked ?? tone;
        context.lineWidth = marked ? 2.5 : 1.5;
        context.setLineDash(block.list === 'movers' ? [6, 3] : []);
        context.stroke();
        context.setLineDash([]);
        const xs = block.outline.map((p) => p[0]);
        const ys = block.outline.map((p) => p[1]);
        const [x, y] = s((Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2);
        context.font = '600 10px ui-monospace, monospace';
        context.fillStyle = marked ?? colour('text');
        const tag = block.list === 'lifts' ? 'LIFT' : block.list === 'movers' ? 'MOVER' : block.list === 'plates' ? 'PLATE' : 'LADDER';
        context.fillText(tag, x - context.measureText(tag).width / 2, y + 3);
    }
    // Floors of rooms, levels and platforms (lava, water): a tint over them.
    for (const floor of list(files, 'floors'))
    {
        const of = String(floor.of ?? '');
        let outline: Point[] | undefined = shapes.find((shape) => shape.id === of)?.outline;
        if (!outline)
        {
            for (const shape of shapes)
            {
                for (const item of [...(Array.isArray(shape.room.levels) ? shape.room.levels : []), ...(Array.isArray(shape.room.platforms) ? shape.room.platforms : [])])
                {
                    if (isObject(item) && item.id === of)
                    {
                        outline = blocksOf(shape.room).find((block) => block.address.endsWith(`/${String(item.key ?? '')}`))?.outline
                            ?? pointsOf(item.outline);
                    }
                }
            }
        }
        if (outline && outline.length >= 3)
        {
            strokePath(context, s, outline, true);
            context.fillStyle = floor.kind === 'lava' ? '#d4532a' : '#3a7bd5';
            context.globalAlpha = 0.35;
            context.fill();
            context.globalAlpha = 1;
        }
    }
    context.restore();
}

// --- box tools: lift, mover, plate, ceiling level ------------------------------------------------------------------

type BoxKind = 'lift' | 'mover' | 'plate' | 'ceiling';

export class BoxBlockTool extends DrawingTool
{
    protected readonly closed = true;
    protected readonly boxes = true;
    private readonly kind: BoxKind;

    constructor(host: ToolHost, kind: BoxKind)
    {
        super(host);
        this.kind = kind;
    }

    protected describe(): string
    {
        return `${this.kind === 'ceiling' ? 'ceiling level' : this.kind}: drag a box${this.kind === 'mover' || this.kind === 'ceiling' ? ', or click corners and Enter' : ''} inside a room · Esc cancels`;
    }

    protected finish(outline: Point[], asBox: boolean): void
    {
        const shapes = this.shapes();
        const room = this.kind === 'ceiling' ? hostRoom(this.host, shapes, outline[0]) : roomAt(shapes, outline[0]) ?? hostRoom(this.host, shapes, outline[0]);
        if (!room || room.ghost)
        {
            this.host.note(`Draw the ${this.kind} inside a room`);
            return;
        }
        if (!outline.every((p) => pointInPolygon(p, room.outline) || room.outline.some((q) => distance(p, q) < 1)))
        {
            this.host.note(`The ${this.kind} must lie inside ${room.id}`);
            return;
        }
        const o = this.host.options();
        const ccw = counterClockwise(outline);
        const xs = ccw.map((p) => p[0]);
        const ys = ccw.map((p) => p[1]);
        const made = box([Math.min(...xs), Math.min(...ys)], [Math.max(...xs), Math.max(...ys)]);
        if (!made)
        {
            return;
        }
        if (this.kind === 'ceiling')
        {
            const value: JsonObject = { outline: ccw, ceiling: Number(room.room.ceiling) + o.ceilingRise };
            void this.host.edit({ label: `new ceiling level in ${room.id}`, ops: [appendItemOp(room.id, room.room, 'ceiling_levels', value)] }).then((result) =>
            {
                const after = (result?.files['rooms.yml']?.tree.rooms as JsonObject[] | undefined)?.find((entry) => entry.id === room.id);
                const key = appendedKey(after, 'ceiling_levels');
                if (key)
                {
                    this.host.select(`${room.id}/ceiling_levels/${key}`);
                }
            });
            return;
        }
        let value: JsonObject;
        let to: string;
        if (this.kind === 'lift')
        {
            to = 'lifts';
            value = { room: room.id, at: made.at, size: made.size, travel: o.liftTravel };
        }
        else if (this.kind === 'mover')
        {
            to = 'movers';
            const shape: JsonObject = asBox ? { at: made.at, size: made.size } : { outline: ccw };
            value = { room: room.id, ...shape, height: o.moverHeight, travel: [o.moverTravelX, o.moverTravelY, o.moverTravelZ] };
        }
        else
        {
            to = 'plates';
            value = { room: room.id, at: made.at, size: made.size, ...(o.plateRise > 0 ? { rise: o.plateRise } : {}) };
        }
        void this.host.edit({ label: `new ${this.kind} in ${room.id}`, ops: [{ op: 'add', to, file: 'objects.yml', value }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                this.host.select(id, 'objects.yml');
            }
        });
    }
}

// --- floors that burn or are wet -----------------------------------------------------------------------------------

// The floor under a point, the highest first: a plate, a platform's top, a level, the room's floor.
interface FloorHit
{
    kind: 'plate' | 'platform' | 'level' | 'room';
    room: RoomShape;
    height: number;
    outline: Point[];
    // What floors.of and an event's source name: the object's id (none yet for a level or platform without one).
    id?: string;
    // A level's or platform's place in its room: /levels/<key>.
    pointer?: string;
}

function floorsAt(files: FileTrees | undefined, layout: ViewLayoutResult | null, at: Point): FloorHit[]
{
    const shapes = roomShapes(files, layout);
    const room = roomAt(shapes, at);
    if (!room || room.ghost)
    {
        return [];
    }
    const floor = Number(room.room.floor);
    const hits: FloorHit[] = [{ kind: 'room', room, height: floor, outline: room.outline, id: room.id }];
    for (const name of ['levels', 'platforms'] as const)
    {
        const items = room.room[name];
        if (!Array.isArray(items))
        {
            continue;
        }
        const keys = keysOf(items, name);
        const blocks = blocksOf(room.room);
        items.forEach((item, index) =>
        {
            if (!isObject(item))
            {
                return;
            }
            const outline = blocks.find((block) => block.list === name && block.key === keys[index])?.outline ?? [];
            if (outline.length >= 3 && pointInPolygon(at, outline))
            {
                const height = name === 'levels' ? Number(item.floor) : floor + Number(item.base ?? 0) + Number(item.rise ?? 0);
                hits.push({ kind: name === 'levels' ? 'level' : 'platform', room, height, outline,
                    ...(typeof item.id === 'string' ? { id: item.id } : {}), pointer: `/${name}/${segment(keys[index])}` });
            }
        });
    }
    for (const block of objectBlocks(files, layout))
    {
        if (block.list === 'plates' && block.room === room.id && pointInPolygon(at, block.outline))
        {
            hits.push({ kind: 'plate', room, height: floor, outline: block.outline, id: block.id });
        }
    }
    // The most particular last: the room, its levels, its platforms (standing on them), a plate.
    const rank = { room: 0, level: 1, platform: 2, plate: 3 };
    return hits.sort((a, b) => rank[a.kind] - rank[b.kind] || a.height - b.height);
}

// The floor at a point (a ladder's foot and top, a flight's ends): a platform's top, else a level's floor (raised or
// sunken), else the room's.
export function floorHeightAt(files: FileTrees | undefined, layout: ViewLayoutResult | null, at: Point): number | null
{
    const hits = floorsAt(files, layout, at).filter((hit) => hit.kind !== 'plate');
    return hits.length > 0 ? hits[hits.length - 1].height : null;
}

// A level or platform without an id gets one from the core (op name); `then` follows with the id in the same entry.
export function withIdOf(host: ToolHost, hit: { id?: string; room: RoomShape; pointer?: string }, label: string, mergeKey: string,
    then: (id: string) => Op[], selectList?: string): void
{
    // What the second step made is selected (a floor, a switch).
    const finish = (ops: Op[]) => void host.edit({ label, mergeKey, ops }).then((result) =>
    {
        const made = selectList ? allocatedId(result?.ids_allocated, selectList) : null;
        if (made)
        {
            host.select(made, 'objects.yml');
        }
    });
    if (hit.id)
    {
        finish(then(hit.id));
        return;
    }
    void host.edit({ label: `${label}: an id for ${hit.room.id}${hit.pointer}`, mergeKey, ops: [{ op: 'name', id: hit.room.id, file: 'rooms.yml', path: hit.pointer! }] })
        .then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                finish(then(id));
            }
        });
}

export class FloorTool extends BaseTool
{
    private hit: FloorHit | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const hits = floorsAt(this.host.files(), this.host.layout(), at);
        const hit = hits.at(-1);
        if (!hit)
        {
            this.host.note('Click a room\'s floor, a level, a platform or a plate');
            return true;
        }
        const kind = this.host.options().floorKind;
        const existing = list(this.host.files(), 'floors').find((floor) => hit.id !== undefined && floor.of === hit.id);
        if (existing)
        {
            void this.host.edit({ label: `${String(existing.id)} ${kind}`, ops: [{ op: 'set', id: String(existing.id), file: 'objects.yml', fields: { kind } }] });
            this.host.select(String(existing.id), 'objects.yml');
            return true;
        }
        const mergeKey = `floor ${++serial} ${Date.now()}`;
        withIdOf(this.host, hit, `${kind} floor of ${hit.id ?? hit.room.id + hit.pointer!}`, mergeKey,
            (id) => [{ op: 'add', to: 'floors', file: 'objects.yml', value: { of: id, kind } }], 'floors');
        return true;
    }

    move(at: Point): void
    {
        const hit = floorsAt(this.host.files(), this.host.layout(), at).at(-1) ?? null;
        if (hit?.outline !== this.hit?.outline)
        {
            this.hit = hit;
            this.host.hint(hit ? `click: ${hit.kind} ${hit.id ?? `${hit.room.id}${hit.pointer}`} becomes ${this.host.options().floorKind}` : 'click a floor');
            this.host.redraw();
        }
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (this.hit)
        {
            strokePath(context, s, this.hit.outline, true);
            context.fillStyle = this.host.options().floorKind === 'lava' ? '#d4532a' : '#3a7bd5';
            context.globalAlpha = 0.35;
            context.fill();
            context.globalAlpha = 1;
        }
    }
}

// --- ladders ------------------------------------------------------------------------------------------------------

// Where a drag from `from` up to `to` crosses the edge of what it climbs (the outline holding `to`).
function crossing(outline: readonly Point[], from: Point, to: Point): Point | null
{
    let best: { point: Point; t: number } | null = null;
    for (let i = 0; i < outline.length; ++i)
    {
        const a = outline[i];
        const b = outline[(i + 1) % outline.length];
        const d1: Point = [to[0] - from[0], to[1] - from[1]];
        const d2: Point = [b[0] - a[0], b[1] - a[1]];
        const denominator = d1[0] * d2[1] - d1[1] * d2[0];
        if (Math.abs(denominator) < 1e-9)
        {
            continue;
        }
        const t = ((a[0] - from[0]) * d2[1] - (a[1] - from[1]) * d2[0]) / denominator;
        const u = ((a[0] - from[0]) * d1[1] - (a[1] - from[1]) * d1[0]) / denominator;
        if (t >= 0 && t <= 1 && u >= 0 && u <= 1 && (!best || t < best.t))
        {
            best = { point: [from[0] + d1[0] * t, from[1] + d1[1] * t], t };
        }
    }
    return best?.point ?? null;
}

export class LadderTool extends BaseTool
{
    private start: Point | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        if (floorHeightAt(this.host.files(), this.host.layout(), at) === null)
        {
            this.host.note('Start the drag where the ladder\'s foot stands, inside a room');
            return true;
        }
        this.start = at;
        this.cursorAt = at;
        return true;
    }

    // The ladder a drag makes, or why not.
    private ladder(from: Point, to: Point): { value: JsonObject } | { reason: string }
    {
        const files = this.host.files();
        const layout = this.host.layout();
        const low = floorsAt(files, layout, from).filter((hit) => hit.kind !== 'plate');
        const high = floorsAt(files, layout, to).filter((hit) => hit.kind !== 'plate');
        if (low.length === 0 || high.length === 0)
        {
            return { reason: 'Drag from the foot inside a room up onto a floor' };
        }
        const foot = low[low.length - 1];
        const top = high[high.length - 1];
        const option = this.host.options().ladderHeight;
        const climb = top.height - foot.height;
        if (climb < 32 && option < 32)
        {
            return { reason: `the floor there is not higher (${foot.height} to ${top.height}): drag onto a level, a platform or a higher room` };
        }
        const edge = crossing(top.outline, from, to) ?? from;
        const facing = Math.round(((Math.atan2(to[1] - from[1], to[0] - from[0]) * 180) / Math.PI + 360) % 360);
        const back = 2;
        const a = (facing * Math.PI) / 180;
        const at: Point = [Math.round(edge[0] - Math.cos(a) * back), Math.round(edge[1] - Math.sin(a) * back)];
        return { value: { room: foot.room.id, at, facing, height: climb >= 32 ? climb : option } };
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        if (pressed && this.start)
        {
            const made = this.ladder(this.start, at);
            this.host.hint('reason' in made ? made.reason : `ladder in ${String(made.value.room)}: ${String(made.value.height)} high, facing ${String(made.value.facing)}°: release`);
            this.host.redraw();
        }
    }

    up(at: Point): void
    {
        const start = this.start;
        this.start = null;
        this.host.hint(null);
        this.host.redraw();
        if (!start || distance(start, at) < this.reach(10))
        {
            return;
        }
        const made = this.ladder(start, at);
        if ('reason' in made)
        {
            this.host.note(made.reason);
            return;
        }
        void this.host.edit({ label: `new ladder in ${String(made.value.room)}`, ops: [{ op: 'add', to: 'ladders', file: 'objects.yml', value: made.value }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                this.host.select(id, 'objects.yml');
            }
        });
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (!this.start || !this.cursorAt)
        {
            return;
        }
        strokePath(context, s, [this.start, this.cursorAt], false);
        context.strokeStyle = this.host.colour('plan-select');
        context.lineWidth = 3;
        context.setLineDash([2, 5]);
        context.stroke();
        context.setLineDash([]);
        const made = this.ladder(this.start, this.cursorAt);
        if (!('reason' in made))
        {
            handle(context, s, made.value.at as number[], this.host.colour('plan-select'), this.host.colour('surface'), 9);
            label(context, s, made.value.at as number[], `↑ ${String(made.value.height)}`, this.host.colour('text'), this.host.colour('surface'));
        }
    }
}

// --- flights of steps ------------------------------------------------------------------------------------------------

export class FlightTool extends BaseTool
{
    private start: Point | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const room = roomAt(this.shapes(), at);
        if (!room || room.ghost)
        {
            this.host.note('Drag inside a room from the lower floor to the higher one');
            return true;
        }
        this.start = this.snapFine(at);
        this.cursorAt = this.start;
        return true;
    }

    private snapFine(at: Point): Point
    {
        return [Math.round(at[0] / 16) * 16, Math.round(at[1] / 16) * 16];
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = this.snapFine(at);
        if (pressed && this.start)
        {
            const files = this.host.files();
            const layout = this.host.layout();
            const low = floorHeightAt(files, layout, this.start);
            const high = floorHeightAt(files, layout, this.cursorAt);
            this.host.hint(`flight from ${low ?? '?'} to ${high ?? '?'}: release`);
            this.host.redraw();
        }
    }

    up(at: Point): void
    {
        const start = this.start;
        this.start = null;
        this.host.hint(null);
        this.host.redraw();
        const end = this.snapFine(at);
        if (!start || distance(start, end) < 32)
        {
            return;
        }
        const room = roomAt(this.shapes(), start);
        if (!room)
        {
            return;
        }
        const files = this.host.files();
        const layout = this.host.layout();
        const low = floorHeightAt(files, layout, start);
        const high = floorHeightAt(files, layout, end);
        if (low === null || high === null || high <= low)
        {
            this.host.note(`A flight climbs: from a lower floor (${low ?? 'none'}) to a higher one (${high ?? 'none'})`);
            return;
        }
        void this.host.edit({ label: `new flight in ${room.id}`, ops: [appendItemOp(room.id, room.room, 'flights', { from: start, to: end })] }).then((result) =>
        {
            const after = (result?.files['rooms.yml']?.tree.rooms as JsonObject[] | undefined)?.find((entry) => entry.id === room.id);
            const key = appendedKey(after, 'flights');
            if (key)
            {
                this.host.select(`${room.id}/flights/${key}`);
            }
        });
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (!this.start || !this.cursorAt)
        {
            return;
        }
        const [ax, ay] = s(this.start[0], this.start[1]);
        const [bx, by] = s(this.cursorAt[0], this.cursorAt[1]);
        const length = Math.hypot(bx - ax, by - ay) || 1;
        const nx = -(by - ay) / length * 10;
        const ny = (bx - ax) / length * 10;
        context.strokeStyle = this.host.colour('plan-select');
        context.lineWidth = 1.5;
        for (let i = 0; i <= 6; ++i)
        {
            const t = i / 6;
            const x = ax + (bx - ax) * t;
            const y = ay + (by - ay) * t;
            context.beginPath();
            context.moveTo(x - nx, y - ny);
            context.lineTo(x + nx, y + ny);
            context.stroke();
        }
    }
}

// --- lines inside a room: parapets and beams ----------------------------------------------------------------------

export class RoomLineTool extends DrawingTool
{
    protected readonly closed = false;
    protected readonly minimum = 2;
    private readonly kind: 'parapet' | 'beam';

    constructor(host: ToolHost, kind: 'parapet' | 'beam')
    {
        super(host);
        this.kind = kind;
    }

    protected describe(): string
    {
        return `${this.kind}: ${this.points.length} points · Enter finishes · Backspace takes one back · Esc cancels`;
    }

    protected finish(path: Point[]): void
    {
        const shapes = this.shapes();
        const room = roomAt(shapes, path[0]) ?? hostRoom(this.host, shapes, path[0]);
        if (!room || room.ghost)
        {
            this.host.note(`Draw the ${this.kind} inside a room`);
            return;
        }
        const o = this.host.options();
        let value: JsonObject;
        const listName = this.kind === 'parapet' ? 'parapets' : 'beams';
        if (this.kind === 'parapet')
        {
            value = { path, height: o.parapetHeight };
        }
        else
        {
            const bottom = o.beamBottom > 0 ? Number(room.room.floor) + o.beamBottom : Number(room.room.ceiling) - o.beamDepth - 32;
            value = { path, width: o.beamWidth, depth: o.beamDepth, bottom };
        }
        void this.host.edit({ label: `new ${this.kind} in ${room.id}`, ops: [appendItemOp(room.id, room.room, listName, value)] }).then((result) =>
        {
            const after = (result?.files['rooms.yml']?.tree.rooms as JsonObject[] | undefined)?.find((entry) => entry.id === room.id);
            const key = appendedKey(after, listName);
            if (key)
            {
                this.host.select(`${room.id}/${listName}/${key}`);
            }
        });
    }
}

// The lines of a room's parapets and beams and its flights, for the plan (Author mode).
export function drawRoomLines(context: CanvasRenderingContext2D, s: ToScreen, room: JsonObject, colour: (name: string) => string, selection: string | null): void
{
    const id = String(room.id ?? '');
    for (const [name, dash, width] of [['parapets', [], 4], ['beams', [8, 4], 6]] as const)
    {
        const items = room[name];
        if (!Array.isArray(items))
        {
            continue;
        }
        const keys = keysOf(items, name);
        items.forEach((item, index) =>
        {
            const path = isObject(item) ? pointsOf(item.path) : [];
            if (path.length < 2)
            {
                return;
            }
            strokePath(context, s, path, false);
            context.strokeStyle = selection === `${id}/${name}/${keys[index]}` ? colour('plan-select') : colour(name === 'beams' ? 'plan-faint' : 'plan-room-edge');
            context.lineWidth = width;
            context.globalAlpha = 0.8;
            context.setLineDash([...dash]);
            context.stroke();
            context.setLineDash([]);
            context.globalAlpha = 1;
        });
    }
    // Ceiling levels: dotted, the raised ceiling's height at their middle.
    const ceilings = room.ceiling_levels;
    if (Array.isArray(ceilings))
    {
        const keys = keysOf(ceilings, 'ceiling_levels');
        ceilings.forEach((item, index) =>
        {
            const outline = isObject(item) ? pointsOf(item.outline) : [];
            if (outline.length < 3)
            {
                return;
            }
            strokePath(context, s, outline, true);
            context.strokeStyle = selection === `${id}/ceiling_levels/${keys[index]}` ? colour('plan-select') : colour('plan-hover');
            context.lineWidth = 1.5;
            context.setLineDash([2, 3]);
            context.stroke();
            context.setLineDash([]);
            const xs = outline.map((p) => p[0]);
            const ys = outline.map((p) => p[1]);
            const [x, y] = s((Math.min(...xs) + Math.max(...xs)) / 2, Math.max(...ys));
            context.font = '10px ui-monospace, monospace';
            context.fillStyle = colour('plan-hover');
            context.fillText(`ceiling ${String((item as JsonObject).ceiling)}`, x - 30, y + 12);
        });
    }
    const flights = room.flights;
    if (Array.isArray(flights))
    {
        const flightKeys = keysOf(flights, 'flights');
        for (const [flightIndex, flight] of flights.entries())
        {
            const from = isObject(flight) ? pointsOf([flight.from])[0] : undefined;
            const to = isObject(flight) ? pointsOf([flight.to])[0] : undefined;
            if (!from || !to)
            {
                continue;
            }
            const [ax, ay] = s(from[0], from[1]);
            const [bx, by] = s(to[0], to[1]);
            const length = Math.hypot(bx - ax, by - ay) || 1;
            const nx = -(by - ay) / length * 8;
            const ny = (bx - ax) / length * 8;
            const chosen = selection === `${id}/flights/${flightKeys[flightIndex]}`;
            context.strokeStyle = chosen ? colour('plan-select') : colour('plan-room-edge');
            context.lineWidth = chosen ? 2 : 1;
            const steps = Math.max(3, Math.round(length / 10));
            for (let i = 0; i <= steps; ++i)
            {
                const x = ax + (bx - ax) * (i / steps);
                const y = ay + (by - ay) * (i / steps);
                context.beginPath();
                context.moveTo(x - nx, y - ny);
                context.lineTo(x + nx, y + ny);
                context.stroke();
            }
        }
    }
    for (const which of ['floor_points', 'ceiling_points'] as const)
    {
        const pts = room[which];
        if (!Array.isArray(pts))
        {
            continue;
        }
        for (const p of pts)
        {
            if (Array.isArray(p) && typeof p[0] === 'number' && typeof p[1] === 'number')
            {
                const [x, y] = s(p[0], p[1]);
                context.beginPath();
                if (which === 'floor_points')
                {
                    context.arc(x, y, 4, 0, Math.PI * 2);
                }
                else
                {
                    context.rect(x - 4, y - 4, 8, 8);
                }
                context.fillStyle = colour(which === 'floor_points' ? 'plan-link' : 'plan-hover');
                context.fill();
                context.font = '10px ui-monospace, monospace';
                context.fillText(String(p[2]), x + 6, y - 4);
            }
        }
    }
}

// --- height points ---------------------------------------------------------------------------------------------------

export class HeightPointsTool extends BaseTool
{
    private drag: { room: RoomShape; index: number; from: number[]; now: Point } | null = null;

    private which(): 'floor_points' | 'ceiling_points'
    {
        return this.host.options().pointsOn === 'ceiling' ? 'ceiling_points' : 'floor_points';
    }

    private room(at: Point): RoomShape | null
    {
        const shapes = this.shapes();
        const room = roomAt(shapes, at) ?? hostRoom(this.host, shapes, at);
        return room && !room.ghost && !room.path ? room : null;
    }

    private pointsOf(room: RoomShape): number[][]
    {
        const value = room.room[this.which()];
        return Array.isArray(value) ? value.filter((p): p is number[] => Array.isArray(p) && p.length >= 3).map((p) => p as number[]) : [];
    }

    private near(room: RoomShape, at: Point): number
    {
        const pts = this.pointsOf(room);
        let best = -1;
        let bestDistance = this.reach(9);
        pts.forEach((p, index) =>
        {
            const d = distance(p, at);
            if (d <= bestDistance)
            {
                best = index;
                bestDistance = d;
            }
        });
        return best;
    }

    // A point on the outline snaps onto it (a corner, else the wall), else to 16 inside.
    private place(room: RoomShape, at: Point): Point
    {
        for (const corner of room.outline)
        {
            if (distance(corner, at) <= this.reach(9))
            {
                return [corner[0], corner[1]];
            }
        }
        for (let i = 0; i < room.outline.length; ++i)
        {
            const near = nearestOnSegment(at, room.outline[i], room.outline[(i + 1) % room.outline.length]);
            if (near.distance <= this.reach(6))
            {
                return [Math.round(near.point[0]), Math.round(near.point[1])];
            }
        }
        return [Math.round(at[0] / 16) * 16, Math.round(at[1] / 16) * 16];
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const room = this.room(at);
        if (!room)
        {
            this.host.note('Click inside a room drawn by its outline (not a corridor)');
            return true;
        }
        const which = this.which();
        const index = this.near(room, at);
        if (index >= 0)
        {
            const point = this.pointsOf(room)[index];
            if (event.altKey)
            {
                const remaining = this.pointsOf(room).length;
                void this.host.edit({ label: `remove a ${which === 'floor_points' ? 'floor' : 'ceiling'} point of ${room.id}`, ops: [{ op: 'patch', id: room.id, file: 'rooms.yml',
                    patch: remaining > 1 ? [{ op: 'test', path: `/${which}/${index}`, value: point }, { op: 'remove', path: `/${which}/${index}` }]
                        : [{ op: 'remove', path: `/${which}` }] }] });
                return true;
            }
            this.drag = { room, index, from: point, now: [point[0], point[1]] };
            this.host.select(room.id);
            return true;
        }
        const o = this.host.options();
        const [x, y] = this.place(room, at);
        const height = (which === 'floor_points' ? Number(room.room.floor) : Number(room.room.ceiling)) + o.pointHeight;
        const value: JsonValue = [x, y, height];
        void this.host.edit({ label: `${which === 'floor_points' ? 'floor' : 'ceiling'} point in ${room.id}`, ops: [Array.isArray(room.room[which])
            ? { op: 'patch', id: room.id, file: 'rooms.yml', patch: [{ op: 'add', path: `/${which}/-`, value }] }
            : { op: 'patch', id: room.id, file: 'rooms.yml', patch: [{ op: 'add', path: `/${which}`, value: [value] }] }] });
        this.host.select(room.id);
        return true;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        if (pressed && this.drag)
        {
            this.drag.now = this.place(this.drag.room, at);
            this.host.redraw();
            return;
        }
        const room = this.room(at);
        const index = room ? this.near(room, at) : -1;
        this.host.hint(room ? index >= 0 ? `point ${index} of ${room.id} at ${this.pointsOf(room)[index][2]}: drag moves it, PgUp/PgDn raise or lower it by ${this.host.options().pointStep}, Alt click removes it`
            : `click: a ${this.which() === 'floor_points' ? 'floor' : 'ceiling'} point in ${room.id}` : 'click inside a room');
        this.host.redraw();
    }

    up(): void
    {
        const drag = this.drag;
        this.drag = null;
        if (!drag || (drag.now[0] === drag.from[0] && drag.now[1] === drag.from[1]))
        {
            return;
        }
        const which = this.which();
        void this.host.edit({ label: `move a point of ${drag.room.id}`, mergeKey: `points ${drag.room.id} ${drag.index}`, ops: [{ op: 'patch', id: drag.room.id, file: 'rooms.yml',
            patch: [{ op: 'test', path: `/${which}/${drag.index}`, value: drag.from }, { op: 'replace', path: `/${which}/${drag.index}`, value: [drag.now[0], drag.now[1], drag.from[2]] }] }] });
    }

    key(event: KeyboardEvent): boolean
    {
        if ((event.code !== 'PageUp' && event.code !== 'PageDown') || !this.cursorAt)
        {
            return false;
        }
        const room = this.room(this.cursorAt);
        const index = room ? this.near(room, this.cursorAt) : -1;
        if (!room || index < 0)
        {
            return false;
        }
        const which = this.which();
        const point = this.pointsOf(room)[index];
        const step = (event.code === 'PageUp' ? 1 : -1) * this.host.options().pointStep;
        void this.host.edit({ label: `height of a point of ${room.id}`, mergeKey: `point height ${room.id} ${index}`, ops: [{ op: 'patch', id: room.id, file: 'rooms.yml',
            patch: [{ op: 'test', path: `/${which}/${index}`, value: point }, { op: 'replace', path: `/${which}/${index}`, value: [point[0], point[1], point[2] + step] }] }] });
        this.host.hint(`point ${index} of ${room.id}: ${point[2] + step}`);
        return true;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const accent = this.host.colour('plan-select');
        const surface = this.host.colour('surface');
        const room = this.cursorAt ? this.room(this.cursorAt) : null;
        if (room)
        {
            strokePath(context, s, room.outline, true);
            context.strokeStyle = accent;
            context.globalAlpha = 0.4;
            context.lineWidth = 2;
            context.stroke();
            context.globalAlpha = 1;
            this.pointsOf(room).forEach((p) => handle(context, s, p, accent, surface, 8));
        }
        if (this.drag)
        {
            handle(context, s, this.drag.now, accent, accent, 9);
            label(context, s, this.drag.now, `${this.drag.now.join(', ')} · ${this.drag.from[2]}`, this.host.colour('text'), surface);
        }
        else if (this.cursorAt && room && this.near(room, this.cursorAt) < 0)
        {
            const p = this.place(room, this.cursorAt);
            const o = this.host.options();
            handle(context, s, p, accent, surface, 5);
            label(context, s, p, `${(o.pointsOn === 'ceiling' ? Number(room.room.ceiling) : Number(room.room.floor)) + o.pointHeight}`, this.host.colour('text'), surface);
        }
    }
}
