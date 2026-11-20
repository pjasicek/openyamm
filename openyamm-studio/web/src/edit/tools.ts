// The indoor tools on the plan (S5_BROWSER_EDITOR.md 3.18, part 1): Select (handles of the selection), Room,
// Corridor, Opening, Door, Stairs, and inside a selected room Level, Platform and Pillar. Framework-free: the plan
// view hands them pointer events in map units and draws what they draw (their ghost) over the plan; every gesture
// ends in one transaction (ToolHost.edit). Nothing here waits for the core to redraw.
import type { FileTrees, JsonObject, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import type { ToolName } from './stages.ts';
import { PLACING_TOOLS } from './stages.ts';
import { LinkTool, PlaceTool, ThingHandles } from './placing.ts';
import { BoxBlockTool, FlightTool, FloorTool, HeightPointsTool, LadderTool, RoomLineTool } from './blocks.ts';
import { GoalTool, PlanLinkTool, SpaceTool, spaceBox, spacePlaces } from './plantools.ts';
import { isOutdoorFiles, makeOutdoorTool } from './outdoortools.ts';
import { degreesTo, grabsShape, objectShape, roomLineShape, shapeGestureOp } from './handles.ts';
import type { EditShape } from './handles.ts';
import { KEYED_LISTS, isObject, keysOf, resolvePointer, splitAddress } from './keys.ts';
import type { Point } from './ops.ts';
import {
    allocatedId, appendItemOp, appendedKey, doorOp, heightStepOp, insertPointOp, movePointsOp, needsStart, roomById, startOp,
} from './ops.ts';
import {
    box, counterClockwise, distance, nearCorner, nearEdge, openingPlace, pathBand, pointInPolygon, selfCrossing, slopeToward,
} from './geometry.ts';
import type { OpeningPlace } from './geometry.ts';

export type { ToScreen, ToolHost, PlanTool, RoomShape } from './toolbase.ts';
export { BaseTool, DrawingTool, handle, hostRoom, label, points, roomAt, roomShapes, strokePath } from './toolbase.ts';
import { BaseTool, DrawingTool, handle, hostRoom, label, points, roomAt, roomShapes, strokePath } from './toolbase.ts';
import type { PlanTool, RoomShape, ToScreen, ToolHost } from './toolbase.ts';

// Each new object gets a merge key of its own, so the start set after the first room folds into the room's entry.
let gestureSerial = 0;

class RoomTool extends DrawingTool
{
    protected readonly closed = true;

    protected describe(): string
    {
        return `room: ${this.points.length} corners · click the first corner or Enter to finish · Backspace takes one back · Esc cancels · Shift any angle`;
    }

    protected finish(outline: Point[]): void
    {
        const options = this.host.options();
        const files = this.host.files();
        const startNeeded = files ? needsStart(files) : false;
        const mergeKey = `new room ${++gestureSerial} ${Date.now()}`;
        // A room drawn for a plan space of the Checklist realises it; so does one drawn over a planned space's bubble.
        const xs = outline.map((p) => p[0]);
        const ys = outline.map((p) => p[1]);
        const middle: Point = [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
        const over = options.space ? null : spacePlaces(files, this.host.layout()).find((place) => !place.room && pointInPolygon(place.at, outline)
            || (!place.room && pointInPolygon(middle, spaceBox(place))));
        const realises = options.space || over?.id || '';
        const space: JsonObject = realises ? { space: realises } : {};
        if (options.space)
        {
            this.host.setOptions?.({ space: '' });
        }
        void this.host.edit({ label: 'new room', mergeKey, ops: [{ op: 'add', to: 'rooms', value: {
            outline: counterClockwise(outline), floor: options.floor, ceiling: options.ceiling, ...space } }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated, 'rooms');
            if (!id)
            {
                return;
            }
            this.host.select(id);
            if (startNeeded)
            {
                void this.host.edit({ label: 'party start', mergeKey, ops: [startOp(id)] });
            }
        });
    }
}

class CorridorTool extends DrawingTool
{
    protected readonly closed = false;
    protected readonly minimum = 2;

    protected describe(): string
    {
        return `corridor: ${this.points.length} points · Enter finishes · Backspace takes one back · Esc cancels · width ${this.host.options().width}`;
    }

    protected drawBody(context: CanvasRenderingContext2D, s: ToScreen, line: Point[]): void
    {
        context.fillStyle = this.host.colour('plan-select');
        context.globalAlpha = 0.14;
        for (const quad of pathBand(line, this.host.options().width))
        {
            strokePath(context, s, quad, true);
            context.fill();
        }
        context.globalAlpha = 1;
    }

    protected finish(path: Point[]): void
    {
        const options = this.host.options();
        const files = this.host.files();
        const startNeeded = files ? needsStart(files) : false;
        const mergeKey = `new corridor ${++gestureSerial} ${Date.now()}`;
        // Drawn through a planned space's bubble (a corridor of the plan): it realises it.
        // A planned corridor first, then any planned space the path's middle point lies in.
        const open = options.space ? [] : spacePlaces(files, this.host.layout()).filter((place) => !place.room);
        const middlePoint = path[Math.floor(path.length / 2)];
        const over = open.find((place) => place.kind === 'corridor' && path.some((p) => pointInPolygon(p, spaceBox(place))))
            ?? open.find((place) => pointInPolygon(middlePoint, spaceBox(place)));
        const realises = options.space || over?.id || '';
        if (options.space)
        {
            this.host.setOptions?.({ space: '' });
        }
        void this.host.edit({ label: 'new corridor', mergeKey, ops: [{ op: 'add', to: 'rooms', value: {
            path, width: options.width, floor: options.floor, ceiling: options.ceiling, ...(realises ? { space: realises } : {}) } }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated, 'rooms');
            if (id)
            {
                this.host.select(id);
                if (startNeeded)
                {
                    void this.host.edit({ label: 'party start', mergeKey, ops: [startOp(id)] });
                }
            }
        });
    }
}

class BlockTool extends DrawingTool
{
    protected readonly closed = true;
    protected readonly boxes = true;
    private readonly kind: 'level' | 'platform' | 'pillar';

    constructor(host: ToolHost, kind: 'level' | 'platform' | 'pillar')
    {
        super(host);
        this.kind = kind;
    }

    protected describe(): string
    {
        return `${this.kind}: drag a box, or click corners and Enter · inside the selected room · Esc cancels`;
    }

    protected finish(outline: Point[], asBox: boolean): void
    {
        const shapes = this.shapes();
        const room = hostRoom(this.host, shapes, outline[0]);
        if (!room || room.ghost)
        {
            this.host.note(`Select a room first (or draw the ${this.kind} inside one)`);
            return;
        }
        if (!outline.every((p) => pointInPolygon(p, room.outline) || room.outline.some((q) => distance(p, q) < 1)
            || nearEdge(room.outline, p, 1, true)))
        {
            this.host.note(`The ${this.kind} must lie inside ${room.id}`);
            return;
        }
        const options = this.host.options();
        const ccw = counterClockwise(outline);
        const made = box(ccw[0], ccw[2]);
        let value: JsonObject;
        const list = this.kind === 'level' ? 'levels' : this.kind === 'platform' ? 'platforms' : 'pillars';
        if (this.kind === 'level')
        {
            value = { outline: ccw, floor: Number(room.room.floor) + options.levelRise };
        }
        else if (asBox && made)
        {
            value = { at: made.at, size: made.size, ...(this.kind === 'platform' ? { rise: options.platformRise } : {}) };
        }
        else
        {
            value = { outline: ccw, ...(this.kind === 'platform' ? { rise: options.platformRise } : {}) };
        }
        void this.host.edit({ label: `new ${this.kind} in ${room.id}`, ops: [appendItemOp(room.id, room.room, list, value)] }).then((result) =>
        {
            const after = result?.files['rooms.yml']?.tree.rooms;
            const object = Array.isArray(after) ? (after as JsonObject[]).find((entry) => entry.id === room.id) : undefined;
            const key = appendedKey(object, list);
            if (key)
            {
                this.host.select(`${room.id}/${list}/${key}`);
            }
        });
    }
}

class OpeningTool extends BaseTool
{
    private start: { at: Point; room: RoomShape } | null = null;
    private place: OpeningPlace | { reason: string } | null = null;
    private target: RoomShape | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const room = roomAt(this.shapes(), at);
        if (!room || room.ghost)
        {
            this.host.note('Start the drag inside a room and end it in the room next to it');
            return true;
        }
        this.start = { at, room };
        this.cursorAt = at;
        this.host.hint(`opening from ${room.id}: drag into the next room`);
        return true;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        if (!pressed || !this.start)
        {
            return;
        }
        const shapes = this.shapes();
        const room = roomAt(shapes, at);
        this.target = room && room.id !== this.start.room.id ? room : null;
        this.place = this.target ? openingPlace(this.start.room.outline, this.target.outline, this.start.at, at, this.host.options().openingWidth) : null;
        this.host.hint(this.place && 'reason' in this.place ? this.place.reason
            : this.target ? `opening ${this.start.room.id} → ${this.target.id}: release to make it` : `opening from ${this.start.room.id}: drag into the next room`);
        this.host.redraw();
    }

    up(at: Point): void
    {
        const start = this.start;
        const place = this.place;
        const target = this.target;
        this.start = null;
        this.place = null;
        this.target = null;
        this.host.hint(null);
        this.host.redraw();
        if (!start || !target)
        {
            return;
        }
        if (!place || 'reason' in place)
        {
            this.host.note(place?.reason ?? 'No opening there');
            return;
        }
        void at;
        const options = this.host.options();
        const value: JsonObject = { from: start.room.id, to: target.id, along: place.along, width: place.width, height: options.openingHeight,
            ...(place.from_wall !== undefined ? { from_wall: place.from_wall, to_wall: place.to_wall! } : {}) };
        void this.host.edit({ label: `opening ${start.room.id} → ${target.id}`, ops: [{ op: 'add', to: 'openings', file: 'rooms.yml', value }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                this.host.select(id);
            }
        });
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (!this.start || !this.cursorAt)
        {
            return;
        }
        const bad = this.place && 'reason' in this.place;
        strokePath(context, s, [this.start.at, this.cursorAt], false);
        context.strokeStyle = this.host.colour(bad ? 'bad' : 'plan-opening');
        context.lineWidth = 1.5;
        context.setLineDash([5, 4]);
        context.stroke();
        context.setLineDash([]);
        if (this.place && !('reason' in this.place))
        {
            strokePath(context, s, this.place.shared, false);
            context.strokeStyle = this.host.colour('plan-opening');
            context.globalAlpha = 0.45;
            context.lineWidth = 3;
            context.stroke();
            context.globalAlpha = 1;
            strokePath(context, s, [this.place.a, this.place.b], false);
            context.lineWidth = 7;
            context.stroke();
            label(context, s, this.place.b, `width ${this.place.width} · along ${this.place.along}`, this.host.colour('text'), this.host.colour('surface'));
        }
    }
}

// An opening on the plan from the core's layout (its two ends in the `from` room's wall).
export function openingAt(layout: ViewLayoutResult | null, at: Point, reach: number): string | null
{
    let best: { id: string; d: number } | null = null;
    for (const opening of layout?.openings ?? [])
    {
        if (!opening.a || !opening.b)
        {
            continue;
        }
        const near = nearEdge([opening.a, opening.b], at, reach, false) ?? (distance(opening.a, at) <= reach || distance(opening.b, at) <= reach ? { edge: 0, point: at } : null);
        if (near)
        {
            const d = distance(near.point, at);
            if (!best || d < best.d)
            {
                best = { id: opening.id, d };
            }
        }
    }
    return best?.id ?? null;
}

class DoorTool extends BaseTool
{
    private hovered: string | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        // The opening's line lies in the `from` room's wall; the gap to the other room counts too.
        const opening = openingAt(this.host.layout(), at, this.reach(10) + 64);
        if (!opening)
        {
            this.host.note('Click an opening (the teal marks between rooms) to put a door in it');
            return true;
        }
        const doors = this.host.files()?.['objects.yml']?.tree.doors;
        const existing = Array.isArray(doors) ? (doors as JsonObject[]).find((door) => door.opening === opening) : undefined;
        if (existing)
        {
            this.host.select(String(existing.id));
            this.host.note(`${opening} has a door already (${existing.id}): selected`);
            return true;
        }
        const preset = this.host.options().door;
        void this.host.edit({ label: `door in ${opening}`, ops: [doorOp(opening, preset)] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (id)
            {
                this.host.select(id);
            }
        });
        return true;
    }

    move(at: Point): void
    {
        const hovered = openingAt(this.host.layout(), at, this.reach(10) + 64);
        if (hovered !== this.hovered)
        {
            this.hovered = hovered;
            this.host.hint(hovered ? `click: a door in ${hovered}` : 'click an opening to put a door in it');
            this.host.redraw();
        }
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const opening = this.hovered ? this.host.layout()?.openings.find((entry) => entry.id === this.hovered) : undefined;
        if (opening?.a && opening.b)
        {
            strokePath(context, s, [opening.a, opening.b], false);
            context.strokeStyle = this.host.colour('plan-door');
            context.lineWidth = 8;
            context.globalAlpha = 0.6;
            context.stroke();
            context.globalAlpha = 1;
        }
    }

    cursor(): string
    {
        return this.hovered ? 'pointer' : 'crosshair';
    }
}

class StairsTool extends BaseTool
{
    private start: { at: Point; room: RoomShape } | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const room = roomAt(this.shapes(), at);
        if (!room || room.ghost)
        {
            this.host.note('Drag across a room, from its low side to its high side');
            return true;
        }
        this.start = { at, room };
        this.cursorAt = at;
        return true;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        if (pressed && this.start)
        {
            const toward = slopeToward(this.start.room.outline, this.start.at, at);
            this.host.hint(`stairs in ${this.start.room.id}: rising ${this.host.options().rise} toward ${toward ?? '…'}`);
            this.host.redraw();
        }
    }

    up(at: Point): void
    {
        const start = this.start;
        this.start = null;
        this.host.hint(null);
        this.host.redraw();
        if (!start || distance(start.at, at) < this.reach(12))
        {
            return;
        }
        const options = this.host.options();
        const room = start.room;
        const floor = Number(room.room.floor);
        const slope: JsonObject = { to: floor + options.rise, ...(options.steps > 0 ? { steps: options.steps } : {}) };
        if (!room.path)
        {
            const toward = slopeToward(room.outline, start.at, at);
            if (toward === null)
            {
                return;
            }
            slope.toward = toward;
        }
        void this.host.edit({ label: `stairs in ${room.id}`, ops: [{ op: 'patch', id: room.id, file: 'rooms.yml', patch: [{ op: 'add', path: '/slope', value: slope }] }] });
        this.host.select(room.id);
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (!this.start || !this.cursorAt)
        {
            return;
        }
        const [ax, ay] = s(this.start.at[0], this.start.at[1]);
        const [bx, by] = s(this.cursorAt[0], this.cursorAt[1]);
        const angle = Math.atan2(by - ay, bx - ax);
        context.strokeStyle = this.host.colour('plan-select');
        context.lineWidth = 3;
        context.beginPath();
        context.moveTo(ax, ay);
        context.lineTo(bx, by);
        context.lineTo(bx - Math.cos(angle - 0.4) * 14, by - Math.sin(angle - 0.4) * 14);
        context.moveTo(bx, by);
        context.lineTo(bx - Math.cos(angle + 0.4) * 14, by - Math.sin(angle + 0.4) * 14);
        context.stroke();
        label(context, s, this.cursorAt, `+${this.host.options().rise}`, this.host.colour('text'), this.host.colour('surface'));
    }
}

// --- Select: the selection's handles ---------------------------------------------------------------------------------

// What of the selection the handles change: a list of points (a room's outline or path, a level's or block's
// outline), a box (a block's `at` and `size`), and since S5b2 the blocks of objects.yml and the lines of a room
// (edit/handles.ts).
export type { EditShape } from './handles.ts';

export function editShape(files: FileTrees | undefined, address: string | null): EditShape | null
{
    if (!files || !address)
    {
        return null;
    }
    const { id, pointer } = splitAddress(address);
    const room = roomById(files, id);
    if (!room)
    {
        // A lift, mover, plate or ladder of objects.yml (S5b2).
        return objectShape(files, id);
    }
    const target = pointer ? resolvePointer(room, pointer) : room;
    if (!isObject(target))
    {
        return null;
    }
    if (points(target.outline).length >= 3)
    {
        // A part of the room (a level, a ceiling level) moves whole by a drag inside it; the room itself does not.
        return { id, base: `${pointer}/outline`, kind: 'polygon', points: points(target.outline), ...(pointer ? { movable: true } : {}) };
    }
    if (pointer)
    {
        // A parapet's or beam's path, a flight's ends (S5b2).
        const line = roomLineShape(files, address);
        if (line)
        {
            return line;
        }
    }
    if (!pointer && points(target.path).length >= 2)
    {
        return { id, base: '/path', kind: 'polyline', points: points(target.path) };
    }
    const at = points([target.at])[0];
    const size = points([target.size])[0];
    if (pointer && at && size)
    {
        const [w, h] = size;
        return { id, base: pointer, kind: 'box', at, size, points: [[at[0] - w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] + h / 2], [at[0] - w / 2, at[1] + h / 2]] };
    }
    return null;
}

type Drag =
    | { kind: 'corner'; shape: EditShape; index: number; start: Point; now: Point }
    | { kind: 'edge'; shape: EditShape; index: number; start: Point; now: Point }
    | { kind: 'box'; shape: EditShape; corner: number; start: Point; now: Point }
    | { kind: 'move'; shape: EditShape; start: Point; now: Point }
    | { kind: 'facing'; shape: EditShape; start: Point; now: Point };

// A point shape's facing handle (a ladder): `pixels` along its facing.
function facingHandleOf(shape: EditShape, unitsPerPixel: number, pixels = 34): Point | null
{
    if (shape.kind !== 'point' || shape.facing === undefined)
    {
        return null;
    }
    const a = (shape.facing * Math.PI) / 180;
    return [shape.points[0][0] + Math.cos(a) * pixels * unitsPerPixel, shape.points[0][1] + Math.sin(a) * pixels * unitsPerPixel];
}

// S5b2: the press on a shape of handles.ts that the room handles do not take (a ladder's point and facing, a block or
// line moved whole).
function pressS5b2(shape: EditShape, at: Point, reach: number, unitsPerPixel: number): Drag | null
{
    const facing = facingHandleOf(shape, unitsPerPixel);
    if (facing && distance(facing, at) <= reach)
    {
        return { kind: 'facing', shape, start: at, now: at };
    }
    if (shape.kind === 'point' && distance(shape.points[0], at) <= reach * 1.5)
    {
        return { kind: 'move', shape, start: at, now: at };
    }
    return shape.kind !== 'box' && grabsShape(shape, at, reach * 0.7) ? { kind: 'move', shape, start: at, now: at } : null;
}

class SelectTool extends BaseTool
{
    private drag: Drag | null = null;
    // A part grabbed to move and let go where it was: the plan picks through it (S5b2).
    private unmoved = false;
    // The placed things' handles (part 2): a thing dragged, turned by its facing handle, its radius changed.
    private readonly things: ThingHandles;

    constructor(host: ToolHost)
    {
        super(host);
        this.things = new ThingHandles(host);
    }

    private shape(): EditShape | null
    {
        return editShape(this.host.files(), this.host.selection());
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        if (this.things.down(at, event))
        {
            return true;
        }
        const shape = this.shape();
        if (!shape)
        {
            return false;
        }
        if (shape.kind === 'point')
        {
            this.drag = pressS5b2(shape, at, this.reach(8), this.host.unitsPerPixel());
            return this.drag !== null;
        }
        const corner = nearCorner(shape.points, at, this.reach(8));
        if (corner >= 0)
        {
            this.drag = shape.kind === 'box' ? { kind: 'box', shape, corner, start: at, now: at } : { kind: 'corner', shape, index: corner, start: shape.points[corner], now: shape.points[corner] };
            return true;
        }
        if (shape.kind === 'polygon')
        {
            const edge = nearEdge(shape.points, at, this.reach(6), true);
            if (edge)
            {
                this.drag = { kind: 'edge', shape, index: edge.edge, start: at, now: at };
                return true;
            }
        }
        if (shape.kind === 'box' && pointInPolygon(at, shape.points))
        {
            this.drag = { kind: 'move', shape, start: at, now: at };
            return true;
        }
        this.drag = pressS5b2(shape, at, this.reach(8), this.host.unitsPerPixel());
        return this.drag !== null;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        if (this.things.active())
        {
            this.things.move(at, event);
            return;
        }
        if (!pressed || !this.drag)
        {
            return;
        }
        const drag = this.drag;
        const options = this.host.options();
        if (drag.kind === 'corner')
        {
            // A corner snaps to the grid and to other rooms' corners and walls (Shift or Alt: free).
            drag.now = this.snap(at, event, null, drag.shape.id);
        }
        else if (drag.kind === 'facing')
        {
            drag.now = at;
            this.host.hint(`${drag.shape.id}: facing ${degreesTo(drag.shape.points[0], at, event.shiftKey ? 1 : 15)}°`);
        }
        else
        {
            const dx = at[0] - drag.start[0];
            const dy = at[1] - drag.start[1];
            const grid = options.snap && !event.altKey ? options.grid : 1;
            drag.now = [drag.start[0] + Math.round(dx / grid) * grid, drag.start[1] + Math.round(dy / grid) * grid];
        }
        this.host.redraw();
    }

    // The points as the drag leaves them.
    private dragged(drag: Drag): Point[]
    {
        const pts = drag.shape.points.map((p) => [p[0], p[1]] as Point);
        const dx = drag.now[0] - drag.start[0];
        const dy = drag.now[1] - drag.start[1];
        if (drag.kind === 'corner')
        {
            pts[drag.index] = drag.now;
        }
        else if (drag.kind === 'edge')
        {
            // The edge moves square to itself.
            const a = pts[drag.index];
            const b = pts[(drag.index + 1) % pts.length];
            const length = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
            const nx = -(b[1] - a[1]) / length;
            const ny = (b[0] - a[0]) / length;
            const along = dx * nx + dy * ny;
            const mx = Math.round(nx * along);
            const my = Math.round(ny * along);
            pts[drag.index] = [a[0] + mx, a[1] + my];
            pts[(drag.index + 1) % pts.length] = [b[0] + mx, b[1] + my];
        }
        else if (drag.kind === 'move')
        {
            return pts.map((p) => [p[0] + dx, p[1] + dy]);
        }
        else if (drag.kind === 'facing')
        {
            return pts;
        }
        else
        {
            const opposite = pts[(drag.corner + 2) % 4];
            const corner: Point = [pts[drag.corner][0] + dx, pts[drag.corner][1] + dy];
            return box(opposite, corner)?.outline ?? pts;
        }
        return pts;
    }

    up(at: Point, event: PointerEvent): void
    {
        if (this.things.active())
        {
            this.things.up(at, event);
            return;
        }
        const drag = this.drag;
        this.drag = null;
        if (!drag || (drag.now[0] === drag.start[0] && drag.now[1] === drag.start[1]))
        {
            this.unmoved = drag?.kind === 'move';
            this.host.redraw();
            return;
        }
        const shape = drag.shape;
        const after = this.dragged(drag);
        const what = shape.base.startsWith('/') && shape.base !== '/outline' && shape.base !== '/path' ? `${shape.id}${shape.base.replace(/\/(outline|path)$/, '')}` : shape.id;
        if (shape.file || shape.kind === 'point' || shape.kind === 'ends' || drag.kind === 'facing' || (drag.kind === 'move' && shape.kind !== 'box'))
        {
            // S5b2: the blocks of objects.yml, ladders, lines and parts moved whole (edit/handles.ts).
            this.host.hint(null);
            if (shape.kind === 'polygon' && selfCrossing(after))
            {
                this.host.note('That would make the outline cross itself: not changed');
                this.host.redraw();
                return;
            }
            const facing = drag.kind === 'facing' ? degreesTo(shape.points[0], drag.now, event.shiftKey ? 1 : 15) : undefined;
            const op = shapeGestureOp(shape, after, drag.kind, facing);
            const verb = drag.kind === 'facing' ? 'turn' : drag.kind === 'move' ? 'move' : drag.kind === 'box' ? 'size' : drag.kind === 'edge' ? 'move side of' : 'move end of';
            if (op)
            {
                void this.host.edit({ label: `${verb} ${what}`, mergeKey: `drag ${what} ${drag.kind}`, ops: [op] });
            }
            this.host.redraw();
            return;
        }
        if (shape.kind === 'box')
        {
            const made = box(after[0], after[2]);
            if (!made)
            {
                return;
            }
            void this.host.edit({ label: `${drag.kind === 'move' ? 'move' : 'size'} ${what}`, mergeKey: `drag ${what}`, ops: [{ op: 'patch', id: shape.id, file: 'rooms.yml', patch: [
                { op: 'test', path: `${shape.base}/at`, value: shape.at! },
                { op: 'replace', path: `${shape.base}/at`, value: made.at },
                { op: 'test', path: `${shape.base}/size`, value: shape.size! },
                { op: 'replace', path: `${shape.base}/size`, value: made.size },
            ] }] });
            return;
        }
        if (shape.kind === 'polygon' && selfCrossing(after))
        {
            this.host.note('That would make the outline cross itself: not changed');
            this.host.redraw();
            return;
        }
        const moves = after.map((to, index) => ({ index, from: shape.points[index], to })).filter((move) => move.to[0] !== move.from[0] || move.to[1] !== move.from[1]);
        void this.host.edit({ label: `${drag.kind === 'edge' ? 'move wall of' : 'move corner of'} ${what}`, mergeKey: `drag ${what} ${shape.base}`, ops: [movePointsOp(shape.id, shape.base, moves)] });
    }

    passClick(): boolean
    {
        const unmoved = this.unmoved;
        this.unmoved = false;
        return unmoved;
    }

    doubleClick(at: Point): boolean
    {
        const shape = this.shape();
        if (!shape || shape.kind === 'box' || shape.kind === 'point' || shape.kind === 'ends')
        {
            return false;
        }
        const edge = nearEdge(shape.points, at, this.reach(8), shape.kind === 'polygon');
        if (!edge)
        {
            return false;
        }
        const options = this.host.options();
        const point: Point = options.snap ? [Math.round(edge.point[0] / 8) * 8, Math.round(edge.point[1] / 8) * 8] : [Math.round(edge.point[0]), Math.round(edge.point[1])];
        void this.host.edit({ label: `new corner of ${shape.id}`, ops: [insertPointOp(shape.id, shape.base, shape.points, edge.edge, point, shape.file)] });
        return true;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        this.things.draw(context, s);
        const shape = this.drag?.shape ?? this.shape();
        if (!shape)
        {
            return;
        }
        const pts = this.drag ? this.dragged(this.drag) : shape.points;
        const accent = this.host.colour('plan-select');
        const surface = this.host.colour('surface');
        if (this.drag)
        {
            strokePath(context, s, pts, shape.kind === 'polygon' || shape.kind === 'box');
            context.strokeStyle = accent;
            context.lineWidth = 2;
            context.setLineDash([6, 4]);
            context.stroke();
            context.setLineDash([]);
        }
        pts.forEach((p) => handle(context, s, p, accent, surface));
        // A ladder's facing handle (S5b2).
        const facing = this.drag?.kind === 'facing' ? this.drag.now : facingHandleOf({ ...shape, points: pts }, this.host.unitsPerPixel());
        if (shape.kind === 'point' && facing)
        {
            strokePath(context, s, [pts[0], facing], false);
            context.strokeStyle = accent;
            context.lineWidth = 2;
            context.stroke();
            const [fx, fy] = s(facing[0], facing[1]);
            context.beginPath();
            context.arc(fx, fy, 5, 0, Math.PI * 2);
            context.fillStyle = accent;
            context.fill();
        }
        if (shape.kind === 'polygon')
        {
            for (let i = 0; i < pts.length; ++i)
            {
                const a = pts[i];
                const b = pts[(i + 1) % pts.length];
                const [x, y] = s((a[0] + b[0]) / 2, (a[1] + b[1]) / 2);
                context.beginPath();
                context.arc(x, y, 3, 0, Math.PI * 2);
                context.fillStyle = accent;
                context.fill();
            }
        }
        if (this.drag && this.drag.kind === 'corner')
        {
            label(context, s, this.drag.now, `${this.drag.now[0]}, ${this.drag.now[1]}`, this.host.colour('text'), surface);
        }
    }

    cursor(): string
    {
        return this.drag || this.things.active() ? 'grabbing' : 'default';
    }
}

// --- the active tool, with the keys every tool shares ------------------------------------------------------------

export class ToolController implements PlanTool
{
    private readonly host: ToolHost;
    private active: PlanTool;
    name: ToolName = 'select';
    private pointer: Point | null = null;

    constructor(host: ToolHost)
    {
        this.host = host;
        this.active = isOutdoorFiles(host.files()) ? makeOutdoorTool(host, 'select')! : new SelectTool(host);
        this.outdoor = isOutdoorFiles(host.files());
    }

    // The project's kind the active tool is for (an outdoor project's tools are its own: S5b2).
    private outdoor = false;

    setTool(name: ToolName): void
    {
        const outdoor = isOutdoorFiles(this.host.files());
        if (name === this.name && outdoor === this.outdoor)
        {
            return;
        }
        this.name = name;
        this.outdoor = outdoor;
        this.active = makeTool(this.host, name);
        this.host.hint(null);
        this.host.redraw();
    }

    down(at: Point, event: PointerEvent): boolean
    {
        return this.active.down(at, event);
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        this.pointer = at;
        this.active.move(at, event, pressed);
    }

    up(at: Point, event: PointerEvent): void
    {
        this.active.up(at, event);
    }

    passClick(): boolean
    {
        return this.active.passClick?.() ?? false;
    }

    doubleClick(at: Point, event: MouseEvent): boolean
    {
        return this.active.doubleClick(at, event);
    }

    key(event: KeyboardEvent): boolean
    {
        if (this.active.key(event))
        {
            return true;
        }
        // PgUp, PgDn: the floor under the cursor up or down by the grid; with Shift the ceiling (3.17).
        if ((event.code === 'PageUp' || event.code === 'PageDown') && this.pointer)
        {
            const room = roomAt(roomShapes(this.host.files(), this.host.layout()), this.pointer);
            if (!room || room.ghost)
            {
                return false;
            }
            const which = event.shiftKey ? 'ceiling' : 'floor';
            const step = (event.code === 'PageUp' ? 1 : -1) * this.host.options().grid;
            const op = heightStepOp(room.room, which, step);
            if (!op)
            {
                this.host.note(`${room.id}: the ${which} cannot pass the ${which === 'floor' ? 'ceiling' : 'floor'}`);
                return true;
            }
            void this.host.edit({ label: `${which} of ${room.id}`, mergeKey: `${which} ${room.id}`, ops: [op] });
            this.host.hint(`${room.id}: ${which} ${(op as { fields: Record<string, number> }).fields[which]}`);
            return true;
        }
        return false;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        this.active.draw(context, s);
    }

    cursor(): string
    {
        return this.active.cursor();
    }
}

export function makeTool(host: ToolHost, name: ToolName): PlanTool
{
    if (isOutdoorFiles(host.files()))
    {
        return makeOutdoorTool(host, name) ?? makeOutdoorTool(host, 'select')!;
    }
    switch (name)
    {
    case 'room':
        return new RoomTool(host);
    case 'corridor':
        return new CorridorTool(host);
    case 'opening':
        return new OpeningTool(host);
    case 'door':
        return new DoorTool(host);
    case 'stairs':
        return new StairsTool(host);
    case 'level':
    case 'platform':
    case 'pillar':
        return new BlockTool(host, name);
    case 'link':
        return new LinkTool(host);
    case 'space':
        return new SpaceTool(host);
    case 'planlink':
        return new PlanLinkTool(host);
    case 'goal':
        return new GoalTool(host);
    case 'lift':
    case 'mover':
    case 'plate':
    case 'ceiling':
        return new BoxBlockTool(host, name);
    case 'floor':
        return new FloorTool(host);
    case 'ladder':
        return new LadderTool(host);
    case 'points':
        return new HeightPointsTool(host);
    case 'flight':
        return new FlightTool(host);
    case 'parapet':
    case 'beam':
        return new RoomLineTool(host, name);
    default:
        return PLACING_TOOLS.includes(name) ? new PlaceTool(host, name) : new SelectTool(host);
    }
}

// The keyed sub-objects of a room the plan draws (pillars, platforms, levels), with their addresses.
export function blocksOf(room: JsonObject): { address: string; list: string; key: string; outline: Point[] }[]
{
    const out: { address: string; list: string; key: string; outline: Point[] }[] = [];
    for (const list of ['levels', 'platforms', 'pillars'])
    {
        const items = room[list];
        if (!Array.isArray(items) || !KEYED_LISTS[list])
        {
            continue;
        }
        const keys = keysOf(items, list);
        items.forEach((item, index) =>
        {
            if (!isObject(item))
            {
                return;
            }
            let outline = points(item.outline);
            if (outline.length < 3)
            {
                const at = points([item.at])[0];
                const size = points([item.size])[0];
                if (!at)
                {
                    return;
                }
                const [w, h] = size ?? [64, 64];
                outline = [[at[0] - w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] - h / 2], [at[0] + w / 2, at[1] + h / 2], [at[0] - w / 2, at[1] + h / 2]];
            }
            out.push({ address: `${String(room.id)}/${list}/${keys[index]}`, list, key: keys[index], outline });
        });
    }
    return out;
}

// How far a copy (Ctrl D) goes so that it lies beside the original, east of it: the object's width and two grid
// steps (a room's copy that overlapped it would stop the whole view).
export function besideOffset(files: FileTrees | undefined, address: string, grid: number): Point
{
    if (!files)
    {
        return [grid * 2, 0];
    }
    const { id, pointer } = splitAddress(address);
    const room = roomById(files, id);
    let outline: Point[] = [];
    if (room && !pointer)
    {
        outline = roomShapes(files, null).find((shape) => shape.id === id)?.outline ?? [];
    }
    else if (room)
    {
        outline = blocksOf(room).find((block) => block.address === address)?.outline ?? [];
    }
    if (outline.length === 0)
    {
        return [grid * 2, 0];
    }
    const xs = outline.map((p) => p[0]);
    return [Math.ceil((Math.max(...xs) - Math.min(...xs)) / grid) * grid + grid * (pointer ? 1 : 2), 0];
}
