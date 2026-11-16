// The placing tools and the Wire stage's link on the plan (S5_BROWSER_EDITOR.md 3.18, part 2): Switch and Exit (a
// click on a wall), Chest, Start, Spawn, Monster, Item, Decoration (a floor, or a wall for one that hangs), Light,
// Sound and Placeholder (a click), the Select tool's handles of a placed thing (drag to move, the facing handle, the
// radius handle), and Link (`L`: a selected switch, plate or door, then clicks on the doors it moves). Every gesture
// is one transaction (an add without an id: the client's copy is drawn as a ghost until the core's id comes; a
// chest's or an exit's own event follows in the same history entry).
import type { FileTrees, JsonObject, JsonValue, Op, ViewLayoutResult } from '../../../schema/rpc/generated/rpc.ts';
import type { ToolName } from './stages.ts';
import type { Point } from './ops.ts';
import { allocatedId } from './ops.ts';
import { distance } from './geometry.ts';
import { blocksOf, handle, label, openingAt, roomAt, roomShapes, strokePath } from './tools.ts';
import { blockAt, objectBlocks, withIdOf } from './blocks.ts';
import { isObject, keysOf, segment } from './keys.ts';
import { pointInPolygon } from './geometry.ts';
import type { PlanTool, RoomShape, ToScreen, ToolHost } from './tools.ts';
import { degreesOf, facingOp, moveOp, nearestWall, placeList, placedAt, placedThings, radiusOp, slideOp, wallName, wallPoint } from './things.ts';
import type { Placed } from './things.ts';
import { linkChange, links, newEventOp } from './wiring.ts';

// A fine step for things (a chest need not sit on the room grid).
function snapThing(at: Point, grid: number, free: boolean): Point
{
    const step = free ? 1 : Math.min(16, grid);
    return [Math.round(at[0] / step) * step, Math.round(at[1] / step) * step];
}

// The wall a click is on: the room under it and its nearest wall when near enough, else any room's wall within reach.
function wallTarget(shapes: readonly RoomShape[], at: Point, reach: number): { room: RoomShape; edge: number; along: number; point: Point } | null
{
    const inside = roomAt(shapes, at);
    if (inside && !inside.ghost && !inside.path)
    {
        const near = nearestWall(inside.outline, at);
        if (near && near.distance <= reach)
        {
            return { room: inside, edge: near.edge, along: near.along, point: near.point };
        }
    }
    let best: { room: RoomShape; edge: number; along: number; point: Point; d: number } | null = null;
    for (const room of shapes)
    {
        if (room.ghost || room.path)
        {
            continue;
        }
        const near = nearestWall(room.outline, at);
        if (near && near.distance <= reach && (!best || near.distance < best.d))
        {
            best = { room, edge: near.edge, along: near.along, point: near.point, d: near.distance };
        }
    }
    return best;
}

// The mark of a kind of thing (the tools' ghosts and the things the layout does not draw yet).
export function drawMark(context: CanvasRenderingContext2D, x: number, y: number, list: string, colour: string, ghost: boolean): void
{
    const r = 5;
    context.strokeStyle = colour;
    context.fillStyle = colour;
    context.lineWidth = 1.5;
    context.globalAlpha = ghost ? 0.55 : 1;
    context.setLineDash(ghost ? [2, 2] : []);
    context.beginPath();
    switch (list)
    {
    case 'switches':
        context.rect(x - 3, y - 6, 6, 12);
        context.stroke();
        context.beginPath();
        context.moveTo(x, y - 2);
        context.lineTo(x + 6, y - 9);
        context.stroke();
        break;
    case 'exits':
        context.rect(x - 6, y - 6, 12, 12);
        context.stroke();
        context.beginPath();
        context.moveTo(x - 3, y);
        context.lineTo(x + 4, y);
        context.lineTo(x + 1, y - 3);
        context.moveTo(x + 4, y);
        context.lineTo(x + 1, y + 3);
        context.stroke();
        break;
    case 'chests':
        context.rect(x - r, y - r * 0.7, r * 2, r * 1.4);
        context.fill();
        break;
    case 'monsters':
        context.arc(x, y, r + 1, 0, Math.PI * 2);
        context.stroke();
        break;
    case 'items':
        context.moveTo(x, y - r);
        context.lineTo(x + r, y);
        context.lineTo(x, y + r);
        context.lineTo(x - r, y);
        context.closePath();
        context.fill();
        break;
    case 'lights':
        for (let i = 0; i < 4; ++i)
        {
            const a = (i * Math.PI) / 4;
            context.moveTo(x - Math.cos(a) * r, y - Math.sin(a) * r);
            context.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r);
        }
        context.stroke();
        break;
    case 'spawns':
        context.moveTo(x - r, y - r);
        context.lineTo(x + r, y + r);
        context.moveTo(x + r, y - r);
        context.lineTo(x - r, y + r);
        context.stroke();
        break;
    case 'sounds':
        context.arc(x, y, 3, 0, Math.PI * 2);
        context.fill();
        context.beginPath();
        context.arc(x, y, 7, -0.7, 0.7);
        context.stroke();
        break;
    case 'placeholders':
        context.rect(x - r, y - r, r * 2, r * 2);
        context.stroke();
        context.beginPath();
        context.moveTo(x - r, y - r);
        context.lineTo(x + r, y + r);
        context.stroke();
        break;
    case 'start':
        context.moveTo(x + 9, y);
        context.lineTo(x - 6, y - 6);
        context.lineTo(x - 6, y + 6);
        context.closePath();
        context.fill();
        break;
    default:
        context.arc(x, y, r * 0.7, 0, Math.PI * 2);
        context.fill();
        break;
    }
    context.setLineDash([]);
    context.globalAlpha = 1;
}

// A platform of rooms.yml under a point, for a switch on a block: the platform's room, its address and pointer, its id
// when it has one, and the side nearest the point (by compass, or the outline's edge number) with the place along it.
interface BlockTarget
{
    room: RoomShape;
    address: string;
    pointer: string;
    id?: string;
    outline: Point[];
    side: string | number;
    along: number;
}

const SHORT_SIDES: Record<string, string> = { east: 'e', north: 'n', west: 'w', south: 's' };

function shortSide(side: string | number): string | number
{
    return typeof side === 'string' ? SHORT_SIDES[side] ?? side : side;
}

function blockTarget(shapes: readonly RoomShape[], at: Point): BlockTarget | null
{
    const room = roomAt(shapes, at);
    if (!room || room.ghost)
    {
        return null;
    }
    const platforms = Array.isArray(room.room.platforms) ? room.room.platforms : [];
    const keys = keysOf(platforms, 'platforms');
    for (const block of blocksOf(room.room))
    {
        if (block.list !== 'platforms' || !pointInPolygon(at, block.outline))
        {
            continue;
        }
        const item = platforms[keys.indexOf(block.key)];
        const near = nearestWall(block.outline, at);
        return { room, address: block.address, pointer: `/platforms/${segment(block.key)}`, ...(isObject(item) && typeof item.id === 'string' ? { id: item.id } : {}),
            outline: block.outline, side: near ? shortSide(wallName(block.outline, near.edge)) : 's', along: near?.along ?? 0.5 };
    }
    return null;
}

// --- placing tools ---------------------------------------------------------------------------------------------------

const TOOL_LIST: Partial<Record<ToolName, string>> = {
    switch: 'switches', exit: 'exits', chest: 'chests', start: 'start', spawn: 'spawns', monster: 'monsters', item: 'items',
    decoration: 'decorations', light: 'lights', sound: 'sounds', placeholder: 'placeholders',
};

// A number written as a number, else the text (monster and item names or numbers).
function numberOrName(text: string): JsonValue
{
    return /^\d+$/.test(text.trim()) ? Number(text.trim()) : text.trim();
}

let placeSerial = 0;

export class PlaceTool implements PlanTool
{
    private readonly host: ToolHost;
    private readonly name: ToolName;
    private readonly list: string;
    private cursorAt: Point | null = null;
    private wall: ReturnType<typeof wallTarget> = null;
    // A switch on a block (a platform of rooms.yml: a post, a console): the platform under the pointer.
    private block: BlockTarget | null = null;

    constructor(host: ToolHost, name: ToolName)
    {
        this.host = host;
        this.name = name;
        this.list = TOOL_LIST[name] ?? 'decorations';
    }

    private reach(pixels: number): number
    {
        return pixels * this.host.unitsPerPixel();
    }

    // Whether the tool puts its thing on a wall here: switches (unless on a block) and exits always, a decoration near
    // a wall.
    private wantsWall(): boolean
    {
        return (this.name === 'switch' && !this.block) || this.name === 'exit' || (this.name === 'decoration' && this.wall !== null);
    }

    private aim(at: Point, event: { altKey: boolean }): void
    {
        const shapes = roomShapes(this.host.files(), this.host.layout());
        this.block = this.name === 'switch' ? blockTarget(shapes, at) : null;
        const reach = this.name === 'decoration' ? this.reach(10) : Math.max(this.reach(16), 96);
        this.wall = this.name === 'switch' || this.name === 'exit' || this.name === 'decoration' ? wallTarget(shapes, at, reach) : null;
        this.cursorAt = snapThing(at, this.host.options().grid, event.altKey || !this.host.options().snap);
    }

    // The thing's words from the options, or the reason it cannot be made yet.
    private value(room: string, at: Point): { value: JsonObject } | { reason: string }
    {
        const o = this.host.options();
        switch (this.name)
        {
        case 'chest':
            return { value: { room, at, kind: o.chestKind } };
        case 'spawn':
            return { value: { room, at, slot: o.spawnSlot, ...(o.spawnTier !== 'a' ? { tier: o.spawnTier } : {}), radius: o.spawnRadius } };
        case 'monster':
            return o.monster.trim() ? { value: { room, at, monster: numberOrName(o.monster) } } : { reason: 'Name the monster in the options first (its number or name in monster_data.txt)' };
        case 'item':
            return o.item.trim() ? { value: { room, at, item: numberOrName(o.item) } } : { reason: 'Name the item in the options first (its number or name in items.txt)' };
        case 'decoration':
            return o.decoration.trim() ? { value: { room, at, decoration: o.decoration.trim() } } : { reason: 'Pick a decoration in the options or drag one from the Library' };
        case 'light':
            return { value: { room, at, radius: o.lightRadius, ...(o.lightHeight > 0 ? { height: o.lightHeight } : {}) } };
        case 'sound':
            return o.sound.trim() ? { value: { room, at, sound: o.sound.trim(), radius: o.soundRadius } } : { reason: 'Name the sound file in the options first (a sound of the world\'s audio)' };
        case 'placeholder':
            return { value: { room, at, stands_for: o.standsFor.trim() || 'a thing to be made here' } };
        default:
            return { reason: 'not a placing tool' };
        }
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        this.aim(at, event);
        const files = this.host.files();
        if (!files)
        {
            return true;
        }
        const o = this.host.options();
        const mergeKey = `place ${this.name} ${++placeSerial} ${Date.now()}`;
        if (this.name === 'switch' && this.block)
        {
            // On the block's top (a plate) or on its side nearest the click (a lever, a button): the block needs an id,
            // which the core gives it first when it has none.
            const block = this.block;
            const top = o.switchKind === 'plate';
            const words: JsonObject = top ? { side: 'top', at: [Math.round(this.cursorAt![0]), Math.round(this.cursorAt![1])], size: [32, 32] }
                : { side: block.side, along: block.along, ...(o.switchHeight > 0 ? { height: o.switchHeight } : {}) };
            withIdOf(this.host, { ...(block.id ? { id: block.id } : {}), room: block.room, pointer: block.pointer }, `new switch on ${block.id ?? block.address}`, mergeKey,
                (id) => [{ op: 'add', to: 'switches', file: 'objects.yml', value: { room: block.room.id, block: id, kind: o.switchKind, ...words } }], 'switches');
            return true;
        }
        if (this.wantsWall())
        {
            const wall = this.wall;
            if (!wall)
            {
                this.host.note(this.name === 'switch' ? 'Click on a wall of a room: the switch goes on it' : 'Click on a wall of a room: the exit is a door face on it');
                return true;
            }
            const name = wallName(wall.room.outline, wall.edge);
            let value: JsonObject;
            if (this.name === 'switch')
            {
                value = { room: wall.room.id, wall: name, along: wall.along, kind: o.switchKind, ...(o.switchHeight > 0 ? { height: o.switchHeight } : {}) };
            }
            else if (this.name === 'exit')
            {
                if (!o.exitTo)
                {
                    this.host.note('Pick where the exit leads in the options (a neighbour of the map card; make one there)');
                    return true;
                }
                value = { room: wall.room.id, wall: name, along: wall.along, to: o.exitTo };
            }
            else
            {
                if (!o.decoration.trim())
                {
                    this.host.note('Pick a decoration in the options or drag one from the Library');
                    return true;
                }
                value = { room: wall.room.id, wall: name, along: wall.along, height: o.wallHeight, decoration: o.decoration.trim() };
            }
            this.add(value, mergeKey);
            return true;
        }
        const shapes = roomShapes(files, this.host.layout());
        const room = roomAt(shapes, this.cursorAt!);
        if (!room || room.ghost)
        {
            this.host.note('Click inside a room');
            return true;
        }
        if (this.name === 'start')
        {
            const old = files['objects.yml']?.tree.start;
            const kept: JsonObject = typeof old === 'object' && old !== null && !Array.isArray(old) ? { ...old } : {};
            delete kept.at;
            delete kept.offset;
            delete kept.floor_height;
            void this.host.edit({ label: 'party start', ops: [{ op: 'set_value', file: 'objects.yml', path: 'start', value: { ...kept, room: room.id, at: this.cursorAt! } }] })
                .then((result) => result && this.host.select('start'));
            return true;
        }
        const made = this.value(room.id, this.cursorAt!);
        if ('reason' in made)
        {
            this.host.note(made.reason);
            return true;
        }
        this.add(made.value, mergeKey);
        return true;
    }

    private add(value: JsonObject, mergeKey: string): void
    {
        const o = this.host.options();
        const list = this.list;
        void this.host.edit({ label: `new ${placeList(list)?.noun ?? list} in ${String(value.room)}`, mergeKey, ops: [{ op: 'add', to: list, file: 'objects.yml', value }] }).then((result) =>
        {
            const id = allocatedId(result?.ids_allocated);
            if (!id)
            {
                return;
            }
            this.host.select(id);
            // A chest opens and an exit leads out by an event of their own (presets chest and exit).
            if (o.withEvent && (list === 'chests' || list === 'exits'))
            {
                void this.host.edit({ label: `the event of ${id}`, mergeKey, ops: [newEventOp(this.host.files(), list === 'chests' ? 'chest' : 'exit', id)] });
            }
        });
    }

    move(at: Point, event: PointerEvent): void
    {
        this.aim(at, event);
        const wall = this.wall;
        if (this.block)
        {
            this.host.hint(`switch on ${this.block.id ?? this.block.address}: ${this.host.options().switchKind === 'plate' ? 'its top' : `side ${String(this.block.side)}`} · click to place`);
            this.host.redraw();
            return;
        }
        this.host.hint(this.wantsWall()
            ? (wall ? `${this.name} on wall ${wallName(wall.room.outline, wall.edge)} of ${wall.room.id}, ${Math.round(wall.along * 100)} % along: click to place` : `${this.name}: point at a wall`)
            : `${this.name}: click inside a room · Alt: no snapping · Esc: Select`);
        this.host.redraw();
    }

    up(): void
    {
        // A placing tool acts on the press.
    }

    doubleClick(): boolean
    {
        return false;
    }

    key(event: KeyboardEvent): boolean
    {
        if (event.code === 'Escape')
        {
            this.host.setTool?.('select');
            return true;
        }
        return false;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const accent = this.host.colour('plan-select');
        if (this.block && this.cursorAt)
        {
            strokePath(context, s, this.block.outline, true);
            context.strokeStyle = accent;
            context.lineWidth = 3;
            context.stroke();
            const [x, y] = s(this.cursorAt[0], this.cursorAt[1]);
            drawMark(context, x, y, 'switches', accent, true);
            return;
        }
        if (this.wantsWall() && this.wall)
        {
            const outline = this.wall.room.outline;
            strokePath(context, s, [outline[this.wall.edge], outline[(this.wall.edge + 1) % outline.length]], false);
            context.strokeStyle = accent;
            context.lineWidth = 4;
            context.globalAlpha = 0.5;
            context.stroke();
            context.globalAlpha = 1;
            const [x, y] = s(this.wall.point[0], this.wall.point[1]);
            drawMark(context, x, y, this.list, accent, true);
            return;
        }
        if (this.cursorAt && !this.wantsWall())
        {
            const [x, y] = s(this.cursorAt[0], this.cursorAt[1]);
            drawMark(context, x, y, this.list, accent, true);
            const o = this.host.options();
            const radius = this.name === 'light' ? o.lightRadius : this.name === 'spawn' ? o.spawnRadius : this.name === 'sound' ? o.soundRadius : 0;
            if (radius > 0)
            {
                const [ex] = s(this.cursorAt[0] + radius, this.cursorAt[1]);
                context.beginPath();
                context.setLineDash([3, 4]);
                context.arc(x, y, Math.abs(ex - x), 0, Math.PI * 2);
                context.strokeStyle = accent;
                context.lineWidth = 1;
                context.stroke();
                context.setLineDash([]);
            }
        }
    }

    cursor(): string
    {
        return 'crosshair';
    }
}

// --- the Select tool's handles of a placed thing ---------------------------------------------------------------------

type ThingDrag =
    | { kind: 'move'; thing: Placed; start: Point; now: Point; moved: boolean }
    | { kind: 'facing'; thing: Placed; now: Point }
    | { kind: 'radius'; thing: Placed; now: Point };

// How far from the thing (pixels) its facing handle stands.
const FACING_HANDLE = 30;

export class ThingHandles
{
    private readonly host: ToolHost;
    private drag: ThingDrag | null = null;

    constructor(host: ToolHost)
    {
        this.host = host;
    }

    active(): boolean
    {
        return this.drag !== null;
    }

    private things(): Placed[]
    {
        return placedThings(this.host.files(), this.host.layout());
    }

    private selected(things: readonly Placed[]): Placed | null
    {
        const address = this.host.selection();
        return address ? things.find((thing) => thing.address === address) ?? null : null;
    }

    private facingHandle(thing: Placed): Point | null
    {
        const list = placeList(thing.list);
        if (thing.list !== 'start' && !list?.facing)
        {
            return null;
        }
        const angle = ((thing.facing ?? 0) * Math.PI) / 180;
        const d = FACING_HANDLE * this.host.unitsPerPixel();
        return [thing.at[0] + Math.cos(angle) * d, thing.at[1] + Math.sin(angle) * d];
    }

    private radiusHandle(thing: Placed): Point | null
    {
        if (!placeList(thing.list)?.radius)
        {
            return null;
        }
        const radius = thing.radius ?? (thing.list === 'spawns' ? 128 : thing.list === 'lights' ? 0 : 0);
        return radius > 0 ? [thing.at[0] + radius, thing.at[1]] : null;
    }

    down(at: Point, event: PointerEvent): boolean
    {
        void event;
        const things = this.things();
        const reach = 9 * this.host.unitsPerPixel();
        const selected = this.selected(things);
        if (selected && !selected.ghost)
        {
            const facing = this.facingHandle(selected);
            if (facing && distance(facing, at) <= reach)
            {
                this.drag = { kind: 'facing', thing: selected, now: at };
                return true;
            }
            const radius = this.radiusHandle(selected);
            if (radius && distance(radius, at) <= reach)
            {
                this.drag = { kind: 'radius', thing: selected, now: at };
                return true;
            }
        }
        const hit = placedAt(things, at, reach);
        if (!hit || hit.ghost)
        {
            return false;
        }
        if (hit.address !== this.host.selection())
        {
            this.host.select(hit.address);
        }
        this.drag = { kind: 'move', thing: hit, start: at, now: hit.at, moved: false };
        return true;
    }

    // Where a dragged thing would go: a point (snapped), or for a thing on a wall the nearest place on its room's walls.
    private target(drag: Extract<ThingDrag, { kind: 'move' }>): { at: Point; wall?: { name: string | number; along: number } }
    {
        const thing = drag.thing;
        if (thing.wall && thing.room)
        {
            const room = roomShapes(this.host.files(), this.host.layout()).find((shape) => shape.id === thing.room);
            const near = room ? nearestWall(room.outline, drag.now) : null;
            if (room && near)
            {
                return { at: wallPoint(room.outline, near.edge, near.along), wall: { name: wallName(room.outline, near.edge), along: near.along } };
            }
        }
        return { at: drag.now };
    }

    move(at: Point, event: PointerEvent): void
    {
        const drag = this.drag;
        if (!drag)
        {
            return;
        }
        if (drag.kind === 'move')
        {
            const dx = at[0] - drag.start[0];
            const dy = at[1] - drag.start[1];
            if (Math.hypot(dx, dy) > 3 * this.host.unitsPerPixel())
            {
                drag.moved = true;
            }
            drag.now = snapThing([drag.thing.at[0] + dx, drag.thing.at[1] + dy], this.host.options().grid, event.altKey || !this.host.options().snap);
            const target = this.target(drag);
            this.host.hint(target.wall ? `${drag.thing.address}: wall ${target.wall.name}, ${Math.round(target.wall.along * 100)} % along` : `${drag.thing.address}: ${target.at.join(', ')}`);
        }
        else
        {
            drag.now = at;
            if (drag.kind === 'facing')
            {
                this.host.hint(`${drag.thing.address}: facing ${degreesOf(at[0] - drag.thing.at[0], at[1] - drag.thing.at[1], event.shiftKey ? 1 : 15)}°`);
            }
            else
            {
                this.host.hint(`${drag.thing.address}: radius ${Math.max(16, Math.round(distance(drag.thing.at, at) / 16) * 16)}`);
            }
        }
        this.host.redraw();
    }

    up(at: Point, event: PointerEvent): void
    {
        const drag = this.drag;
        this.drag = null;
        this.host.hint(null);
        if (!drag)
        {
            return;
        }
        const thing = drag.thing;
        let op: Op | null = null;
        let what = '';
        if (drag.kind === 'move')
        {
            if (!drag.moved)
            {
                this.host.redraw();
                return;
            }
            const target = this.target(drag);
            if (target.wall)
            {
                op = slideOp(thing, target.wall.name, target.wall.along);
                what = 'slide';
            }
            else
            {
                const room = roomAt(roomShapes(this.host.files(), this.host.layout()), target.at);
                if (!room && thing.list !== 'start')
                {
                    this.host.note(`${thing.address} must stay inside a room: not moved`);
                    this.host.redraw();
                    return;
                }
                op = moveOp(thing, target.at, room?.id);
                what = 'move';
            }
        }
        else if (drag.kind === 'facing')
        {
            op = facingOp(thing, degreesOf(at[0] - thing.at[0], at[1] - thing.at[1], event.shiftKey ? 1 : 15));
            what = 'turn';
        }
        else
        {
            op = radiusOp(thing, Math.max(16, Math.round(distance(thing.at, at) / 16) * 16));
            what = 'radius of';
        }
        if (op)
        {
            void this.host.edit({ label: `${what} ${thing.address}`, mergeKey: `${what} ${thing.address}`, ops: [op] });
        }
        this.host.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const accent = this.host.colour('plan-select');
        const surface = this.host.colour('surface');
        const things = this.things();
        const thing = this.drag?.thing ?? this.selected(things);
        if (!thing)
        {
            return;
        }
        let at = thing.at;
        if (this.drag?.kind === 'move' && this.drag.moved)
        {
            at = this.target(this.drag).at;
            const [x, y] = s(at[0], at[1]);
            drawMark(context, x, y, thing.list, accent, true);
            label(context, s, at, at.map((v) => Math.round(v)).join(', '), this.host.colour('text'), surface);
        }
        const [x, y] = s(at[0], at[1]);
        context.beginPath();
        context.arc(x, y, 10, 0, Math.PI * 2);
        context.strokeStyle = accent;
        context.lineWidth = 2;
        context.stroke();
        const facing = this.drag?.kind === 'facing' ? this.drag.now : this.facingHandle(thing);
        if (facing)
        {
            const angle = Math.atan2(facing[1] - thing.at[1], facing[0] - thing.at[0]);
            const d = FACING_HANDLE * this.host.unitsPerPixel();
            const tip: Point = [thing.at[0] + Math.cos(angle) * d, thing.at[1] + Math.sin(angle) * d];
            strokePath(context, s, [thing.at, tip], false);
            context.strokeStyle = accent;
            context.lineWidth = 2;
            context.stroke();
            const [tx, ty] = s(tip[0], tip[1]);
            context.beginPath();
            context.arc(tx, ty, 5, 0, Math.PI * 2);
            context.fillStyle = accent;
            context.fill();
        }
        const radius = this.drag?.kind === 'radius' ? distance(thing.at, this.drag.now) : this.radiusHandle(thing) ? (thing.radius ?? 128) : 0;
        if (radius > 0)
        {
            const [ex] = s(thing.at[0] + radius, thing.at[1]);
            context.beginPath();
            context.setLineDash([4, 4]);
            context.arc(x, y, Math.abs(ex - x), 0, Math.PI * 2);
            context.strokeStyle = accent;
            context.lineWidth = 1.5;
            context.stroke();
            context.setLineDash([]);
            handle(context, s, [thing.at[0] + radius, thing.at[1]], accent, surface);
        }
    }
}

// --- the link (W3) ---------------------------------------------------------------------------------------------------

// Where an id is on the plan: a placed thing, a door in its opening, an opening.
export function objectPlace(files: FileTrees | undefined, layout: ViewLayoutResult | null, id: string, things?: readonly Placed[]): Point | null
{
    const placed = (things ?? placedThings(files, layout)).find((thing) => thing.address === id);
    if (placed)
    {
        return placed.at;
    }
    // A lift, a mover, a plate: the middle of its block.
    const block = objectBlocks(files, layout).find((entry) => entry.id === id);
    if (block)
    {
        const xs = block.outline.map((p) => p[0]);
        const ys = block.outline.map((p) => p[1]);
        return [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2];
    }
    let opening = id;
    if (id.startsWith('door:'))
    {
        const door = layout?.doors.find((entry) => entry.id === id);
        const doors = files?.['objects.yml']?.tree.doors;
        const written = Array.isArray(doors) ? (doors as JsonObject[]).find((entry) => entry.id === id) : undefined;
        opening = door?.opening ?? (typeof written?.opening === 'string' ? written.opening : '');
    }
    const found = layout?.openings.find((entry) => entry.id === opening);
    if (found?.a && found.b)
    {
        return [(found.a[0] + found.b[0]) / 2, (found.a[1] + found.b[1]) / 2];
    }
    return null;
}

// What a click links to: a door (by its opening on the plan) or a switch (a lever thrown by another).
function linkTarget(host: ToolHost, at: Point): string | null
{
    const layout = host.layout();
    const reach = 10 * host.unitsPerPixel();
    const switches = placedThings(host.files(), layout).filter((thing) => thing.list === 'switches');
    const lever = placedAt(switches, at, reach);
    if (lever)
    {
        return lever.address;
    }
    const opening = openingAt(layout, at, reach + 48);
    if (!opening)
    {
        // A lift or a mover the event raises or moves.
        const block = blockAt(objectBlocks(host.files(), layout).filter((entry) => entry.list === 'lifts' || entry.list === 'movers'), at);
        return block ? block.id : null;
    }
    const door = layout?.doors.find((entry) => entry.opening === opening);
    if (door)
    {
        return door.id;
    }
    const doors = host.files()?.['objects.yml']?.tree.doors;
    const written = Array.isArray(doors) ? (doors as JsonObject[]).find((entry) => entry.opening === opening) : undefined;
    return written ? String(written.id) : null;
}

const LINKABLE = ['switch:', 'plate:', 'door:', 'lift:', 'mover:', 'chest:', 'exit:', 'deco:', 'decoration:'];

export class LinkTool implements PlanTool
{
    private readonly host: ToolHost;
    private readonly source: string | null;
    private cursorAt: Point | null = null;
    private hovered: string | null = null;

    constructor(host: ToolHost)
    {
        this.host = host;
        const selected = host.selection();
        this.source = selected && LINKABLE.some((prefix) => selected.startsWith(prefix)) ? selected : null;
        if (!this.source)
        {
            // The tool controller is still choosing this tool: the way back comes after it.
            queueMicrotask(() =>
            {
                host.note('Select a switch, a plate or a door first, then press L and click what it moves');
                host.setTool?.('select');
            });
        }
        else
        {
            host.hint(`link from ${this.source}: click the doors it moves (${host.options().linkVerb}); a linked one again unlinks it · Esc ends`);
        }
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0 || !this.source)
        {
            return false;
        }
        const target = linkTarget(this.host, at);
        if (!target)
        {
            this.host.note('Click a door (its opening on the plan) or a lever to link it');
            return true;
        }
        const change = linkChange(this.host.files(), this.source, target, this.host.options().linkVerb);
        if (change)
        {
            void this.host.edit({ label: change.label, ops: change.ops });
        }
        return true;
    }

    move(at: Point): void
    {
        this.cursorAt = at;
        const hovered = this.source ? linkTarget(this.host, at) : null;
        if (hovered !== this.hovered)
        {
            this.hovered = hovered;
            this.host.hint(hovered ? `click: ${this.source} ${this.host.options().linkVerb} ${hovered}` : `link from ${this.source}: click the doors it moves · Esc ends`);
        }
        this.host.redraw();
    }

    up(): void
    {
        // The link is made on the press.
    }

    doubleClick(): boolean
    {
        return false;
    }

    key(event: KeyboardEvent): boolean
    {
        if (event.code === 'Escape' || event.code === 'Enter')
        {
            this.host.hint(null);
            this.host.setTool?.('select');
            return true;
        }
        return false;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (!this.source)
        {
            return;
        }
        const files = this.host.files();
        const layout = this.host.layout();
        const from = objectPlace(files, layout, this.source);
        const colour = this.host.colour('plan-link');
        if (!from)
        {
            return;
        }
        for (const link of links(files).filter((entry) => entry.source === this.source))
        {
            const to = objectPlace(files, layout, link.target);
            if (to)
            {
                strokePath(context, s, [from, to], false);
                context.strokeStyle = colour;
                context.lineWidth = 3;
                context.setLineDash([7, 4]);
                context.stroke();
                context.setLineDash([]);
            }
        }
        const end = this.hovered ? objectPlace(files, layout, this.hovered) ?? this.cursorAt : this.cursorAt;
        if (end)
        {
            strokePath(context, s, [from, end], false);
            context.strokeStyle = colour;
            context.lineWidth = 2;
            context.setLineDash([3, 3]);
            context.stroke();
            context.setLineDash([]);
            if (this.hovered)
            {
                const [x, y] = s(end[0], end[1]);
                context.beginPath();
                context.arc(x, y, 9, 0, Math.PI * 2);
                context.strokeStyle = colour;
                context.lineWidth = 2.5;
                context.stroke();
            }
        }
        const [x, y] = s(from[0], from[1]);
        context.beginPath();
        context.arc(x, y, 8, 0, Math.PI * 2);
        context.fillStyle = colour;
        context.globalAlpha = 0.35;
        context.fill();
        context.globalAlpha = 1;
    }

    cursor(): string
    {
        return this.hovered ? 'alias' : 'crosshair';
    }
}

// The wiring on the plan (Author mode): each event's source to what it moves, dashed gold (W3: "Connections are
// visible").
export function drawWiring(context: CanvasRenderingContext2D, s: ToScreen, files: FileTrees, layout: ViewLayoutResult | null, colour: string, things: readonly Placed[]): void
{
    context.save();
    for (const link of links(files))
    {
        const from = objectPlace(files, layout, link.source, things);
        const to = objectPlace(files, layout, link.target, things);
        if (!from || !to)
        {
            continue;
        }
        strokePath(context, s, [from, to], false);
        context.strokeStyle = colour;
        context.lineWidth = 1.5;
        context.globalAlpha = 0.85;
        context.setLineDash([6, 4]);
        context.stroke();
        const [tx, ty] = s(to[0], to[1]);
        const [fx, fy] = s(from[0], from[1]);
        const angle = Math.atan2(ty - fy, tx - fx);
        context.setLineDash([]);
        context.beginPath();
        context.moveTo(tx, ty);
        context.lineTo(tx - Math.cos(angle - 0.4) * 9, ty - Math.sin(angle - 0.4) * 9);
        context.lineTo(tx - Math.cos(angle + 0.4) * 9, ty - Math.sin(angle + 0.4) * 9);
        context.closePath();
        context.fillStyle = colour;
        context.fill();
    }
    context.restore();
}
