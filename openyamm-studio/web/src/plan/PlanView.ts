// The plan view (S5_BROWSER_EDITOR.md 3.4, 4.5): own Canvas2D for the bulk and an SVG layer for labels and the
// selection's handles. Framework-free: React mounts it and feeds it data; it calls back on hover and pick. All
// colours are read from the design tokens at draw time.
import type { Pin, ViewLayoutResult, ViewRoom, ViewThing } from '../../../schema/rpc/generated/rpc.ts';
import { pinPlace } from '../model/pins.ts';
export { pinPlace } from '../model/pins.ts';
import type { PlanHeat } from '../model/compare.ts';
import { heatColour } from '../model/scorecard.ts';
import {
    cellToWorld, distanceToSegment, emptyBounds, extend, fit, floorClusters, hillshade, isEmpty, pointInPolygon,
    polygonArea, toScreen, toWorld, zoomAt,
} from './geometry.ts';
import type { Bounds, ViewTransform } from './geometry.ts';
import type { FileTrees, JsonObject } from '../../../schema/rpc/generated/rpc.ts';
import type { PlanTool } from '../edit/tools.ts';
import { blocksOf, roomShapes } from '../edit/tools.ts';
import { placedAt, placedThings } from '../edit/things.ts';
import { drawMark, drawWiring } from '../edit/placing.ts';
import { blockAt, drawBlocks, drawRoomLines, objectBlocks } from '../edit/blocks.ts';
import { ceilingLevelAt, roomLineAt } from '../edit/handles.ts';
import { landChange, landChangePixels } from './ghost.ts';
import type { ViewLand } from '../../../schema/rpc/generated/rpc.ts';
import { drawPlanBubbles, planLinks, spaceAt, spacePlaces } from '../edit/plantools.ts';
import { pathBand, towardEdge } from '../edit/geometry.ts';
import type { ViewOpening } from '../../../schema/rpc/generated/rpc.ts';
import { drawSketch, sketchHit, tokenColours } from './outdoorplan.ts';

// Author mode's drawing of the files themselves (S5_BROWSER_EDITOR.md 3.4: "the project's room outlines and paths
// as drawn (from the files), the built sectors' floors under them"): the client's own copy, so a gesture shows at
// once; rooms the core has not built yet (ghosts) and rooms a view build left out (skipped) are hatched.
export interface PlanSource
{
    files: FileTrees;
    // The selection's address (room:hall, room:hall/pillars/pillar2).
    selection: string | null;
    // The Plan stage: the plan's bubbles, links and goals drawn in full and picked first.
    planStage?: boolean;
    // An outdoor project (S5b2): the sketch's words drawn over the land and picked (plan/outdoorplan.ts).
    outdoor?: boolean;
}

// An empty indoor layout: a project with no view yet (new, or with errors before any view was made).
const NO_LAYOUT: ViewLayoutResult = { revision: '', view_revision: '', stale: false, kind: 'indoor', world: '',
    bounds: { min: [-1024, -1024, 0], max: [1024, 1024, 0] }, rooms: [], openings: [], doors: [], lifts: [], things: [] };

// Something drawn over the plan above the tool that may take the pointer first (S5b2: the section's cut).
export interface PlanOverlay
{
    draw(context: CanvasRenderingContext2D, s: (x: number, y: number) => [number, number]): void;
    down?(at: [number, number], event: PointerEvent): boolean;
    move?(at: [number, number], event: PointerEvent): void;
    up?(at: [number, number], event: PointerEvent): void;
}

export interface PlanCallbacks
{
    onHover(owner: string | null, world: [number, number] | null): void;
    onPick(owner: string | null): void;
}

export interface PlanBand
{
    label: string;
    // The rooms in the band.
    rooms: Set<string>;
}

type Colour = [number, number, number];

const SVG_NS = 'http://www.w3.org/2000/svg';

function parseColour(text: string): Colour
{
    const hex = text.trim().replace('#', '');
    if (hex.length === 6)
    {
        return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16)];
    }
    return [128, 128, 128];
}

function mix(a: Colour, b: Colour, t: number): string
{
    const c = a.map((value, index) => Math.round(value + (b[index] - value) * t));
    return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

// Bands for the tabs: the plan's height_bands (rooms by the spaces each lists) when it has them, else the floors'
// clusters.
export function planBands(layout: ViewLayoutResult, planTree: Record<string, unknown> | undefined, roomSpaces: Map<string, string>): PlanBand[]
{
    const named = Array.isArray(planTree?.height_bands) ? (planTree!.height_bands as Record<string, unknown>[]) : [];
    if (named.length > 1)
    {
        const bands: PlanBand[] = named.map((band) => ({ label: String(band.id ?? '').replace(/^[a-z]+:/, ''), rooms: new Set<string>() }));
        named.forEach((band, index) =>
        {
            const spaces = new Set<string>([...(Array.isArray(band.spaces) ? band.spaces : []), ...(Array.isArray(band.partly) ? band.partly : [])].map(String));
            for (const room of layout.rooms)
            {
                if (spaces.has(roomSpaces.get(room.id) ?? room.id))
                {
                    bands[index].rooms.add(room.id);
                }
            }
        });
        if (bands.some((band) => band.rooms.size > 0))
        {
            return bands.filter((band) => band.rooms.size > 0);
        }
    }
    const clusters = floorClusters(layout.rooms.map((room) => room.floor));
    if (clusters.length < 2)
    {
        return [];
    }
    return clusters.map(([low, high]) => ({
        label: low === high ? `${low}` : `${low}…${high}`,
        rooms: new Set(layout.rooms.filter((room) => room.floor >= low && room.floor <= high).map((room) => room.id)),
    }));
}

export class PlanView
{
    private readonly root: HTMLElement;
    private readonly canvas: HTMLCanvasElement;
    private readonly svg: SVGSVGElement;
    private readonly context: CanvasRenderingContext2D;
    private readonly callbacks: PlanCallbacks;
    private layout: ViewLayoutResult | null = null;
    private pins: Pin[] = [];
    private band: PlanBand | null = null;
    private selection: string | null = null;
    private hover: string | null = null;
    private view: ViewTransform | null = null;
    private landImage: HTMLCanvasElement | null = null;
    private dragging: { x: number; y: number; view: ViewTransform; moved: boolean } | null = null;
    private spaceDown = false;
    // A draw is wanted (dirty) and one is asked of the next animation frame (scheduled).
    private dirty = false;
    private scheduled = false;
    private readonly resizeObserver: ResizeObserver;
    private stale = false;
    // Until the person pans or zooms, the view keeps the whole map framed (also through resizes).
    private autoFit = true;
    lastDrawMs = 0;
    contextRestores = 0;
    private tool: PlanTool | null = null;
    private toolPressed = false;
    private overlay: PlanOverlay | null = null;
    private overlayPressed = false;
    private source: PlanSource | null = null;
    // The last place of every opening, for one a view build left out (2.4.2): drawn there, stale.
    private lastOpenings = new Map<string, ViewOpening>();
    private staleOpenings: ViewOpening[] = [];
    // History's "show as it was": an earlier state's rooms drawn dashed over the current, with its entry.
    private ghost: { sequence: number; rooms: readonly { outline: readonly (readonly number[])[] }[]; land?: ViewLand } | null = null;
    // Outdoors (S5b2): the land changed since the ghost's state, as an image over the land.
    private ghostLand: { image: HTMLCanvasElement; changed: number } | null = null;

    constructor(root: HTMLElement, callbacks: PlanCallbacks)
    {
        this.root = root;
        this.callbacks = callbacks;
        this.canvas = document.createElement('canvas');
        this.canvas.className = 'oy-plan-canvas';
        this.svg = document.createElementNS(SVG_NS, 'svg');
        this.svg.setAttribute('class', 'oy-plan-svg');
        root.append(this.canvas, this.svg);
        const context = this.canvas.getContext('2d');
        if (!context)
        {
            throw new Error('no 2D canvas');
        }
        this.context = context;
        this.resizeObserver = new ResizeObserver(() => this.resize());
        this.resizeObserver.observe(root);
        this.canvas.addEventListener('wheel', this.onWheel, { passive: false });
        this.canvas.addEventListener('pointerdown', this.onPointerDown);
        this.canvas.addEventListener('pointermove', this.onPointerMove);
        this.canvas.addEventListener('pointerup', this.onPointerUp);
        this.canvas.addEventListener('pointerleave', () => { this.setHoverInternal(null, null); });
        this.canvas.addEventListener('dblclick', this.onDoubleClick);
        // In the capture phase: the tool's keys come before the app's own listeners.
        window.addEventListener('keydown', this.onKey, true);
        window.addEventListener('keyup', this.onKey, true);
        // A 2D canvas drawn on the GPU loses its pixels when the GPU process restarts (as when a WebGL context is
        // lost in a fresh headless Chrome): draw it again.
        this.canvas.addEventListener('contextrestored', () =>
        {
            this.contextRestores += 1;
            this.request();
        });
        this.resize();
    }

    dispose(): void
    {
        this.resizeObserver.disconnect();
        window.removeEventListener('keydown', this.onKey, true);
        window.removeEventListener('keyup', this.onKey, true);
        this.canvas.remove();
        this.svg.remove();
    }

    setLayout(layout: ViewLayoutResult | null): void
    {
        // A new map is framed; a view the person moved (or is drawing in) stays put, also through a layout that
        // could not be made in between (an edit that broke the project for a moment).
        const first = layout !== null && (!this.view || (this.layout === null ? this.autoFit
            : this.layout.view_revision === undefined || layout.kind !== this.layout.kind));
        this.layout = layout;
        this.stale = layout?.stale ?? false;
        if (layout)
        {
            const skipped = new Set(layout.skipped ?? []);
            this.staleOpenings = [...skipped].map((id) => this.lastOpenings.get(id)).filter((opening): opening is ViewOpening => !!opening);
            for (const opening of layout.openings)
            {
                this.lastOpenings.set(opening.id, opening);
            }
        }
        this.landImage = layout?.land ? this.makeLand(layout) : null;
        if (first || !this.view)
        {
            this.frameAll();
        }
        this.request();
    }

    private selectedPin: string | null = null;

    setGhost(ghost: { sequence: number; rooms: readonly { outline: readonly (readonly number[])[] }[]; land?: ViewLand } | null): void
    {
        this.ghost = ghost;
        this.ghostLand = null;
        this.request();
    }

    // The overlay over the plan (the section's cut), or null.
    setOverlay(overlay: PlanOverlay | null): void
    {
        this.overlay = overlay;
        this.overlayPressed = false;
        this.request();
    }

    // Author mode: the active tool takes the pointer and its keys first (null: Review mode, pan and pick only).
    setTool(tool: PlanTool | null): void
    {
        this.tool = tool;
        this.toolPressed = false;
        this.canvas.style.cursor = tool ? tool.cursor() : '';
        this.request();
    }

    // Author mode: the files as drawn (null in Review mode).
    setSource(source: PlanSource | null): void
    {
        const first = !this.source && source && (!this.layout || this.layout.rooms.length === 0);
        this.source = source;
        if (first && this.autoFit)
        {
            this.frameAll();
        }
        this.request();
    }

    // Map units per screen pixel, and the screen point of a world point (scripted runs drive tools by these).
    unitsPerPixel(): number
    {
        return 1 / (this.view?.scale ?? 1);
    }

    screenOf(x: number, y: number): [number, number] | null
    {
        if (!this.view)
        {
            return null;
        }
        const rect = this.canvas.getBoundingClientRect();
        const [sx, sy] = toScreen(this.view, x, y);
        return [rect.left + sx, rect.top + sy];
    }

    // The map point under a page point (a drop from the Library), or null outside the plan.
    worldAt(clientX: number, clientY: number): [number, number] | null
    {
        if (!this.view)
        {
            return null;
        }
        const rect = this.canvas.getBoundingClientRect();
        if (clientX < rect.left || clientY < rect.top || clientX > rect.right || clientY > rect.bottom)
        {
            return null;
        }
        return toWorld(this.view, clientX - rect.left, clientY - rect.top);
    }

    redraw(): void
    {
        this.request();
    }

    setSelectedPin(id: string | null): void
    {
        this.selectedPin = id;
        this.request();
    }

    // The plan as a PNG data URL (a pin made on the plan).
    capture(): string
    {
        this.drawNow();
        return this.canvas.toDataURL('image/png');
    }

    // The world point under the pointer, with the floor of the room there (or 0), and the object there.
    pointerTarget(): { owner: string | null; at: [number, number, number] } | null
    {
        if (!this.pointerWorld || !this.layout)
        {
            return null;
        }
        const [x, y] = this.pointerWorld;
        let floor = 0;
        for (const room of this.layout.rooms ?? [])
        {
            if (pointInOutline(room.outline, x, y))
            {
                floor = room.floor;
                break;
            }
        }
        const owner = this.hitTest(x, y, this.view?.scale ?? 1);
        return { owner: owner && !owner.startsWith('pin:') ? owner : null, at: [Math.round(x), Math.round(y), Math.round(floor)] };
    }

    setPins(pins: Pin[]): void
    {
        this.pins = pins;
        this.request();
    }

    private heat: PlanHeat | null = null;

    // The compare's heat over the plan (S5_BROWSER_EDITOR.md 3.4 overlays, 3.14): every stand point's or block's square
    // by its score, the floor one map lacks, the worst places numbered; null: none.
    setHeat(heat: PlanHeat | null): void
    {
        this.heat = heat;
        this.request();
    }

    setBand(band: PlanBand | null): void
    {
        this.band = band;
        this.request();
    }

    setSelection(id: string | null): void
    {
        this.selection = id;
        this.request();
    }

    setHover(id: string | null): void
    {
        if (id !== this.hover)
        {
            this.hover = id;
            this.request();
        }
    }

    // Frames the whole layout.
    frameAll(): void
    {
        this.autoFit = true;
        const bounds = this.layoutBounds();
        this.view = fit(bounds, this.canvas.clientWidth || 1, this.canvas.clientHeight || 1);
        this.request();
    }

    // Frames one object (room, opening, thing, model) or a point.
    frameObject(id: string | null, at?: [number, number, number]): void
    {
        const bounds = emptyBounds();
        if (at)
        {
            extend(bounds, [at[0] - 768, at[1] - 768]);
            extend(bounds, [at[0] + 768, at[1] + 768]);
        }
        else if (id)
        {
            this.objectBounds(id, bounds);
        }
        if (isEmpty(bounds))
        {
            return;
        }
        this.autoFit = false;
        const pad = Math.max(256, (bounds.maxX - bounds.minX) * 0.6, (bounds.maxY - bounds.minY) * 0.6);
        extend(bounds, [bounds.minX - pad, bounds.minY - pad]);
        extend(bounds, [bounds.maxX + pad, bounds.maxY + pad]);
        this.view = fit(bounds, this.canvas.clientWidth || 1, this.canvas.clientHeight || 1);
        this.request();
    }

    // Frames a box of the map (scripted runs and "frame the drawing").
    frameBounds(minX: number, minY: number, maxX: number, maxY: number): void
    {
        const bounds = emptyBounds();
        extend(bounds, [minX, minY]);
        extend(bounds, [maxX, maxY]);
        this.autoFit = false;
        this.view = fit(bounds, this.canvas.clientWidth || 1, this.canvas.clientHeight || 1);
        this.request();
    }

    // Draws now (the screenshot run measures it).
    drawNow(): number
    {
        this.dirty = false;
        const start = performance.now();
        this.draw();
        this.lastDrawMs = performance.now() - start;
        return this.lastDrawMs;
    }

    // What lies under a world point: things first, then doors and openings, then rooms (the highest floor of the
    // band, the smallest), then outdoor models.
    hitTest(x: number, y: number, pixelsPerUnit: number): string | null
    {
        const layout = this.layout ?? (this.source ? NO_LAYOUT : null);
        if (!layout)
        {
            return null;
        }
        const near = 8 / pixelsPerUnit;
        if (this.source?.outdoor)
        {
            const word = sketchHit(this.source.files, this.source.selection, x, y, near);
            if (word)
            {
                return `sketch.yml#${word}`;
            }
        }
        if (this.source?.planStage && !this.source.outdoor)
        {
            // The Plan stage: a bubble (by its file: a space may share its id with its room), then a link.
            const places = spacePlaces(this.source.files, this.layout);
            const space = spaceAt(places, [x, y], near * 2);
            if (space)
            {
                return `plan.yml#${space.id}`;
            }
            const byId = new Map(places.map((place) => [place.id, place]));
            for (const link of planLinks(this.source.files))
            {
                const from = byId.get(link.from);
                const to = byId.get(link.to);
                if (from && to && distanceToSegment([x, y], from.at, to.at) <= near)
                {
                    return `plan.yml#${link.id}`;
                }
            }
        }
        if (this.source)
        {
            // Author mode: the files' things (switches and exits too, and things not built yet).
            const placed = placedAt(placedThings(this.source.files, this.layout), [x, y], near);
            if (placed && !placed.ghost)
            {
                return placed.address;
            }
            // A ladder by its id (the layout names its marker by the scene's name: S5b2's handles select it).
            const ladders = objectBlocks(this.source.files, this.layout).filter((block) => block.list === 'ladders');
            const ladder = blockAt(ladders, [x, y])
                ?? ladders.find((block) => block.at && Math.hypot(block.at[0] - x, block.at[1] - y) <= near * 1.5);
            if (ladder)
            {
                return ladder.id;
            }
        }
        let best: { id: string; distance: number } | null = null;
        for (const thing of layout.things)
        {
            const distance = Math.hypot(thing.at[0] - x, thing.at[1] - y);
            if (distance <= Math.max(near, thing.radius ?? 0) && (!best || distance < best.distance))
            {
                best = { id: thing.id, distance };
            }
        }
        for (const pin of this.pins)
        {
            const place = pinPlace(pin);
            if (place && Math.hypot(place[0] - x, place[1] - y) <= near && (!best || Math.hypot(place[0] - x, place[1] - y) < best.distance))
            {
                best = { id: pin.id, distance: Math.hypot(place[0] - x, place[1] - y) };
            }
        }
        if (best)
        {
            return best.id;
        }
        const doorOf = new Map(layout.doors.map((door) => [door.opening, door.id]));
        for (const opening of layout.openings)
        {
            if (opening.a && opening.b && distanceToSegment([x, y], opening.a, opening.b) <= near * 0.75)
            {
                return doorOf.get(opening.id) ?? opening.id;
            }
        }
        if (this.source)
        {
            // Author mode: a room's lines (parapets, beams, flights: S5b2), blocks of the room under the point (the
            // smallest first), then the files' rooms.
            const line = roomLineAt(this.source.files, [x, y], near * 0.75);
            if (line)
            {
                return line;
            }
            const shapes = roomShapes(this.source.files, this.layout);
            let block: { address: string; area: number } | null = null;
            for (const shape of shapes)
            {
                for (const candidate of blocksOf(shape.room as JsonObject))
                {
                    const area = Math.abs(polygonArea(candidate.outline));
                    if (pointInPolygon([x, y], candidate.outline) && (!block || area < block.area))
                    {
                        block = { address: candidate.address, area };
                    }
                }
            }
            if (block)
            {
                return block.address;
            }
            const moving = blockAt(objectBlocks(this.source.files, this.layout), [x, y]);
            if (moving)
            {
                return moving.id;
            }
            const raised = ceilingLevelAt(this.source.files, [x, y]);
            if (raised)
            {
                return raised;
            }
            for (const shape of shapes)
            {
                if (shape.id && !shape.ghost && !layout.rooms.some((room) => room.id === shape.id) && pointInPolygon([x, y], shape.outline))
                {
                    return shape.id;
                }
            }
        }
        let room: ViewRoom | null = null;
        for (const candidate of layout.rooms)
        {
            if (this.band && !this.band.rooms.has(candidate.id))
            {
                continue;
            }
            if (pointInPolygon([x, y], candidate.outline)
                && (!room || candidate.floor > room.floor || (candidate.floor === room.floor && polygonArea(candidate.outline) < polygonArea(room.outline))))
            {
                room = candidate;
            }
        }
        if (room)
        {
            return room.id;
        }
        for (const model of layout.models ?? [])
        {
            if (x >= model.min[0] && x <= model.max[0] && y >= model.min[1] && y <= model.max[1])
            {
                return model.id;
            }
        }
        return null;
    }

    private request(): void
    {
        this.dirty = true;
        if (this.scheduled)
        {
            return;
        }
        this.scheduled = true;
        requestAnimationFrame(() =>
        {
            this.scheduled = false;
            if (this.dirty)
            {
                this.drawNow();
            }
        });
    }

    private resize(): void
    {
        const width = Math.max(1, this.root.clientWidth);
        const height = Math.max(1, this.root.clientHeight);
        const ratio = window.devicePixelRatio || 1;
        // Setting a canvas's size clears it, even to the same size.
        if (this.canvas.width !== Math.round(width * ratio) || this.canvas.height !== Math.round(height * ratio))
        {
            this.canvas.width = Math.round(width * ratio);
            this.canvas.height = Math.round(height * ratio);
        }
        this.canvas.style.width = `${width}px`;
        this.canvas.style.height = `${height}px`;
        this.svg.setAttribute('width', String(width));
        this.svg.setAttribute('height', String(height));
        if (this.layout && (this.autoFit || !this.view))
        {
            this.frameAll();
        }
        else if (this.view)
        {
            this.view = { ...this.view, width, height };
        }
        this.request();
    }

    private layoutBounds(): Bounds
    {
        const bounds = emptyBounds();
        const layout = this.layout ?? (this.source ? NO_LAYOUT : null);
        if (!layout)
        {
            return bounds;
        }
        if (!layout.land && this.source?.outdoor)
        {
            extend(bounds, [-32768, -32768]);
            extend(bounds, [32768, 32768]);
            return bounds;
        }
        if (layout.land)
        {
            const half = (layout.land.size / 2) * layout.land.cell;
            extend(bounds, [-half, -half]);
            extend(bounds, [half, half]);
            return bounds;
        }
        for (const room of layout.rooms)
        {
            room.outline.forEach((point) => extend(bounds, point));
        }
        for (const shape of roomShapes(this.source?.files, null))
        {
            shape.outline.forEach((point) => extend(bounds, point));
        }
        if (isEmpty(bounds))
        {
            extend(bounds, [layout.bounds.min[0], layout.bounds.min[1]]);
            extend(bounds, [layout.bounds.max[0], layout.bounds.max[1]]);
        }
        return bounds;
    }

    private objectBounds(id: string, bounds: Bounds): void
    {
        const layout = this.layout;
        if (!layout)
        {
            return;
        }
        layout.rooms.filter((room) => room.id === id).forEach((room) => room.outline.forEach((point) => extend(bounds, point)));
        layout.things.filter((thing) => thing.id === id).forEach((thing) =>
        {
            extend(bounds, [thing.at[0] - 128, thing.at[1] - 128]);
            extend(bounds, [thing.at[0] + 128, thing.at[1] + 128]);
        });
        const opening = layout.openings.find((o) => o.id === id || layout.doors.some((door) => door.id === id && door.opening === o.id));
        if (opening)
        {
            [opening.a, opening.b, ...(opening.outline ?? [])].forEach((point) => point && extend(bounds, point));
        }
        (layout.models ?? []).filter((model) => model.id === id).forEach((model) =>
        {
            extend(bounds, model.min);
            extend(bounds, model.max);
        });
    }

    private colours(): Record<string, string>
    {
        const style = getComputedStyle(document.documentElement);
        const names = ['canvas', 'plan-grid', 'plan-room-low', 'plan-room-high', 'plan-room-edge', 'plan-faint', 'plan-opening',
            'plan-door', 'plan-thing', 'plan-start', 'plan-pin', 'plan-select', 'plan-hover', 'plan-model', 'plan-water',
            'warn', 'good', 'text-dim', 'plan-link',
            'plan-land-low', 'plan-land-high', 'text', 'surface'];
        const out: Record<string, string> = {};
        for (const name of names)
        {
            out[name] = style.getPropertyValue(`--${name}`).trim() || '#888888';
        }
        return out;
    }

    private makeLand(layout: ViewLayoutResult): HTMLCanvasElement
    {
        const land = layout.land!;
        const colours = this.colours();
        const low = parseColour(colours['plan-land-low']);
        const high = parseColour(colours['plan-land-high']);
        const water = parseColour(colours['plan-water']);
        const canvas = document.createElement('canvas');
        canvas.width = land.size;
        canvas.height = land.size;
        const context = canvas.getContext('2d')!;
        const image = context.createImageData(land.size, land.size);
        const shade = hillshade(land.heights, land.size, land.height_unit, land.cell);
        let minHeight = Infinity;
        let maxHeight = -Infinity;
        for (const height of land.heights)
        {
            minHeight = Math.min(minHeight, height);
            maxHeight = Math.max(maxHeight, height);
        }
        for (let index = 0; index < land.size * land.size; ++index)
        {
            const t = maxHeight > minHeight ? (land.heights[index] - minHeight) / (maxHeight - minHeight) : 0;
            const base: Colour = land.water[index] ? water : low.map((value, c) => value + (high[c] - value) * t) as Colour;
            const light = land.water[index] ? 1 : 0.55 + 0.65 * shade[index];
            image.data[index * 4] = Math.min(255, base[0] * light);
            image.data[index * 4 + 1] = Math.min(255, base[1] * light);
            image.data[index * 4 + 2] = Math.min(255, base[2] * light);
            image.data[index * 4 + 3] = 255;
        }
        context.putImageData(image, 0, 0);
        return canvas;
    }

    private draw(): void
    {
        const canvas = this.canvas;
        const context = this.context;
        const ratio = window.devicePixelRatio || 1;
        const colours = this.colours();
        context.setTransform(ratio, 0, 0, ratio, 0, 0);
        context.fillStyle = colours.canvas;
        context.fillRect(0, 0, canvas.width, canvas.height);
        const layout = this.layout ?? (this.source ? NO_LAYOUT : null);
        if (!this.view && layout)
        {
            this.view = fit(this.layoutBounds(), this.canvas.clientWidth || 1, this.canvas.clientHeight || 1);
        }
        const view = this.view;
        this.svg.replaceChildren();
        if (!layout || !view)
        {
            return;
        }
        const s = (x: number, y: number) => toScreen(view, x, y);
        this.drawGrid(context, view, colours['plan-grid']);

        if (layout.land && this.landImage)
        {
            const half = (layout.land.size / 2) * layout.land.cell;
            const [x0, y0] = s(-half, half);
            const [x1, y1] = s(half, -half);
            context.imageSmoothingEnabled = false;
            context.drawImage(this.landImage, x0, y0, x1 - x0, y1 - y0);
            void cellToWorld;
        }
        for (const model of layout.models ?? [])
        {
            const [x0, y0] = s(model.min[0], model.max[1]);
            const [x1, y1] = s(model.max[0], model.min[1]);
            const highlighted = model.id === this.selection ? colours['plan-select'] : model.id === this.hover ? colours['plan-hover'] : null;
            context.fillStyle = colours['plan-model'];
            context.globalAlpha = 0.55;
            context.fillRect(x0, y0, x1 - x0, y1 - y0);
            context.globalAlpha = 1;
            context.strokeStyle = highlighted ?? colours['plan-room-edge'];
            context.lineWidth = highlighted ? 2.5 : 1;
            context.strokeRect(x0, y0, x1 - x0, y1 - y0);
        }

        // Rooms: fill by floor height, faint outside the band; the selection and hover drawn last.
        const floors = layout.rooms.length > 0 ? layout.rooms.map((room) => room.floor) : [0];
        const low = Math.min(...floors);
        const high = Math.max(...floors);
        const lowColour = parseColour(colours['plan-room-low']);
        const highColour = parseColour(colours['plan-room-high']);
        const ordered = [...layout.rooms].sort((a, b) => a.floor - b.floor);
        const path = (outline: readonly (readonly number[])[]) =>
        {
            context.beginPath();
            outline.forEach((point, index) =>
            {
                const [x, y] = s(point[0], point[1]);
                if (index === 0)
                {
                    context.moveTo(x, y);
                }
                else
                {
                    context.lineTo(x, y);
                }
            });
            context.closePath();
        };
        for (const room of ordered)
        {
            const inBand = !this.band || this.band.rooms.has(room.id);
            path(room.outline);
            context.fillStyle = inBand ? mix(lowColour, highColour, high > low ? (room.floor - low) / (high - low) : 0.5) : colours['plan-faint'];
            context.globalAlpha = inBand ? 1 : 0.5;
            context.fill();
            context.globalAlpha = inBand ? 1 : 0.35;
            context.strokeStyle = colours['plan-room-edge'];
            context.lineWidth = 1;
            context.stroke();
            if (inBand && room.levels)
            {
                for (const level of room.levels)
                {
                    path(level.outline);
                    context.fillStyle = mix(lowColour, highColour, high > low ? (level.height - low) / (high - low) : 0.5);
                    context.fill();
                    context.setLineDash([3, 3]);
                    context.stroke();
                    context.setLineDash([]);
                }
            }
            context.globalAlpha = 1;
        }

        // Openings teal, doors red.
        const doorOf = new Map(layout.doors.map((door) => [door.opening, door.id]));
        for (const opening of layout.openings)
        {
            const door = doorOf.get(opening.id);
            const marked = opening.id === this.selection || door === this.selection ? colours['plan-select']
                : opening.id === this.hover || door === this.hover ? colours['plan-hover'] : null;
            if (opening.a && opening.b)
            {
                const [ax, ay] = s(opening.a[0], opening.a[1]);
                const [bx, by] = s(opening.b[0], opening.b[1]);
                context.strokeStyle = marked ?? colours['plan-opening'];
                context.lineWidth = marked ? 5 : 3;
                context.beginPath();
                context.moveTo(ax, ay);
                context.lineTo(bx, by);
                context.stroke();
                if (door)
                {
                    const mx = (ax + bx) / 2;
                    const my = (ay + by) / 2;
                    const length = Math.hypot(bx - ax, by - ay) || 1;
                    const nx = -(by - ay) / length;
                    const ny = (bx - ax) / length;
                    context.strokeStyle = marked ?? colours['plan-door'];
                    context.lineWidth = 3;
                    context.beginPath();
                    context.moveTo(mx - nx * 4 - (bx - ax) * 0.3, my - ny * 4 - (by - ay) * 0.3);
                    context.lineTo(mx - nx * 4 + (bx - ax) * 0.3, my - ny * 4 + (by - ay) * 0.3);
                    context.stroke();
                }
            }
            else if (opening.outline)
            {
                path(opening.outline);
                context.strokeStyle = marked ?? colours['plan-opening'];
                context.lineWidth = 2;
                context.setLineDash([4, 2]);
                context.stroke();
                context.setLineDash([]);
            }
        }

        // The selected and hovered rooms on top.
        for (const [id, colour, width] of [[this.hover, colours['plan-hover'], 2], [this.selection, colours['plan-select'], 3]] as const)
        {
            const room = id ? layout.rooms.find((candidate) => candidate.id === id) : undefined;
            if (room)
            {
                path(room.outline);
                context.strokeStyle = colour;
                context.lineWidth = width;
                context.stroke();
            }
        }

        if (this.source?.outdoor)
        {
            drawSketch(context, s, { files: this.source.files, selection: this.source.selection, hover: this.pointerOwner }, tokenColours());
        }
        else if (this.source)
        {
            const colour = (name: string) => colours[name] ?? '#888888';
            this.drawSource(context, layout, s, colours);
            drawBlocks(context, s, this.source.files, this.layout, colour, this.source.selection, this.hover);
            this.drawStaleOpenings(context, s, colours);
            this.drawPlaced(context, layout, s, colours);
            drawPlanBubbles(context, s, this.source.files, this.layout, colour, this.source.selection, this.source.planStage === true);
        }

        if (this.heat)
        {
            this.drawHeat(context, this.heat, s, colours);
        }

        // Things by kind.
        for (const thing of layout.things)
        {
            this.drawThing(context, thing, s, colours);
        }
        if (layout.start)
        {
            const [x, y] = s(layout.start.at[0], layout.start.at[1]);
            const angle = (layout.start.facing * Math.PI) / 180;
            context.fillStyle = colours['plan-start'];
            context.beginPath();
            context.moveTo(x + Math.cos(angle) * 11, y - Math.sin(angle) * 11);
            context.lineTo(x + Math.cos(angle + 2.5) * 7, y - Math.sin(angle + 2.5) * 7);
            context.lineTo(x + Math.cos(angle - 2.5) * 7, y - Math.sin(angle - 2.5) * 7);
            context.closePath();
            context.fill();
        }
        for (const pin of this.pins)
        {
            const place = pinPlace(pin);
            if (!place)
            {
                continue;
            }
            const [x, y] = s(place[0], place[1]);
            const status = pin.status ?? 'open';
            const selected = pin.id === this.selectedPin;
            context.globalAlpha = status === 'accepted' || status === 'declined' ? 0.45 : 1;
            context.fillStyle = status === 'claimed' ? colours.warn : status === 'resolved' ? colours.good
                : status === 'open' ? colours['plan-pin'] : colours['text-dim'];
            context.strokeStyle = selected ? colours['plan-select'] : colours.surface;
            context.lineWidth = selected ? 3 : 1.5;
            context.beginPath();
            context.arc(x, y - 9, selected ? 8 : 6, 0, Math.PI * 2);
            context.fill();
            context.stroke();
            context.beginPath();
            context.moveTo(x - 3, y - 5);
            context.lineTo(x, y);
            context.lineTo(x + 3, y - 5);
            context.fill();
            context.globalAlpha = 1;
        }

        if (this.ghost)
        {
            context.save();
            context.strokeStyle = '#e0a020';
            context.lineWidth = 2;
            context.setLineDash([6, 4]);
            for (const room of this.ghost.rooms)
            {
                path(room.outline);
                context.stroke();
            }
            context.setLineDash([]);
            const land = this.drawGhostLand(context, layout, s);
            context.font = '600 12px ui-sans-serif, system-ui, sans-serif';
            context.fillStyle = '#e0a020';
            context.fillText(`as it was before #${this.ghost.sequence} (dashed)${land}`, 12, 20);
            context.restore();
        }

        if (this.tool)
        {
            context.save();
            this.tool.draw(context, s);
            context.restore();
        }
        this.overlay?.draw(context, s);

        this.drawLabels(layout, view);
    }

    // Outdoors (S5b2): the land changed since the ghost's state, tinted over the land (risen amber, sunk blue); the
    // words for the caption.
    private drawGhostLand(context: CanvasRenderingContext2D, layout: ViewLayoutResult, s: (x: number, y: number) => [number, number]): string
    {
        const then = this.ghost?.land;
        if (!then || !layout.land)
        {
            return '';
        }
        if (!this.ghostLand)
        {
            const change = landChange(then, layout.land);
            if (!change)
            {
                return '';
            }
            const image = document.createElement('canvas');
            image.width = change.size;
            image.height = change.size;
            const pixels = new ImageData(change.size, change.size);
            pixels.data.set(landChangePixels(change));
            image.getContext('2d')!.putImageData(pixels, 0, 0);
            this.ghostLand = { image, changed: change.changed };
        }
        const half = (layout.land.size / 2) * layout.land.cell;
        const [x0, y0] = s(-half, half);
        const [x1, y1] = s(half, -half);
        context.imageSmoothingEnabled = false;
        context.drawImage(this.ghostLand.image, x0, y0, x1 - x0, y1 - y0);
        return this.ghostLand.changed > 0 ? `; land changed since: ${this.ghostLand.changed} cells (amber risen, blue sunk)` : '; the land is as it was';
    }

    // The files' rooms over the built ones (author mode): outlines and corridors as drawn, rooms not built (a ghost
    // waiting for the core, a room the view build skipped) hatched, the blocks inside rooms, the selected block.
    private drawSource(context: CanvasRenderingContext2D, layout: ViewLayoutResult, s: (x: number, y: number) => [number, number],
        colours: Record<string, string>): void
    {
        const built = new Set(layout.rooms.map((room) => room.id));
        const skipped = new Set(layout.skipped ?? []);
        const shapes = roomShapes(this.source!.files, this.layout);
        const hatch = this.hatch(colours.warn);
        const ghostHatch = this.hatch(colours['plan-select']);
        const path = (outline: readonly (readonly number[])[]) =>
        {
            context.beginPath();
            outline.forEach((point, index) =>
            {
                const [x, y] = s(point[0], point[1]);
                if (index === 0)
                {
                    context.moveTo(x, y);
                }
                else
                {
                    context.lineTo(x, y);
                }
            });
            context.closePath();
        };
        for (const shape of shapes)
        {
            const missing = shape.ghost || !built.has(shape.id) || skipped.has(shape.id);
            const pieces = shape.path ? pathBand(shape.path, shape.width ?? 256) : [shape.outline];
            for (const piece of pieces)
            {
                if (piece.length < 3)
                {
                    continue;
                }
                path(piece);
                if (missing)
                {
                    context.fillStyle = (shape.ghost ? ghostHatch : hatch) ?? colours['plan-faint'];
                    context.fill();
                }
                if (!shape.path)
                {
                    context.strokeStyle = missing ? (shape.ghost ? colours['plan-select'] : colours.warn) : colours['plan-room-edge'];
                    context.lineWidth = 1.5;
                    context.setLineDash(missing ? [5, 3] : []);
                    context.stroke();
                    context.setLineDash([]);
                }
            }
            if (shape.path)
            {
                context.beginPath();
                shape.path.forEach((point, index) =>
                {
                    const [x, y] = s(point[0], point[1]);
                    if (index === 0)
                    {
                        context.moveTo(x, y);
                    }
                    else
                    {
                        context.lineTo(x, y);
                    }
                });
                context.strokeStyle = missing ? colours.warn : colours['plan-room-edge'];
                context.lineWidth = 1;
                context.setLineDash([2, 4]);
                context.stroke();
                context.setLineDash([]);
            }
            // A floor that rises: an arrow toward the wall it climbs to, with the rise.
            const slope = shape.room.slope as { to?: number; toward?: unknown } | undefined;
            const edge = slope && !shape.path ? towardEdge(shape.outline, slope.toward) : -1;
            if (slope && edge >= 0)
            {
                const centre = shape.outline.reduce((sum, p) => [sum[0] + p[0] / shape.outline.length, sum[1] + p[1] / shape.outline.length], [0, 0]);
                const a = shape.outline[edge];
                const b = shape.outline[(edge + 1) % shape.outline.length];
                const [cx, cy] = s(centre[0], centre[1]);
                const [tx, ty] = s((a[0] + b[0]) / 2 * 0.8 + centre[0] * 0.2, (a[1] + b[1]) / 2 * 0.8 + centre[1] * 0.2);
                const angle = Math.atan2(ty - cy, tx - cx);
                context.strokeStyle = colours['plan-room-edge'];
                context.fillStyle = colours['plan-room-edge'];
                context.lineWidth = 2;
                context.beginPath();
                context.moveTo(cx, cy);
                context.lineTo(tx, ty);
                context.stroke();
                context.beginPath();
                context.moveTo(tx, ty);
                context.lineTo(tx - Math.cos(angle - 0.45) * 10, ty - Math.sin(angle - 0.45) * 10);
                context.lineTo(tx - Math.cos(angle + 0.45) * 10, ty - Math.sin(angle + 0.45) * 10);
                context.closePath();
                context.fill();
                const rise = Number(slope.to) - Number(shape.room.floor);
                context.font = '600 11px ui-monospace, monospace';
                context.fillText(`${rise >= 0 ? '+' : ''}${rise}${(shape.room.slope as { steps?: number }).steps ? ` · ${(shape.room.slope as { steps?: number }).steps} steps` : ''}`, cx + 6, cy - 6);
            }
            // Parapets, beams, flights and height points.
            drawRoomLines(context, s, shape.room, (name) => colours[name] ?? '#888888', this.source!.selection);
            // Blocks inside the room: pillars solid, platforms crossed, levels dashed.
            for (const block of blocksOf(shape.room))
            {
                const selected = this.source!.selection === block.address;
                const hovered = this.hover === block.address;
                path(block.outline);
                if (block.list === 'pillars')
                {
                    context.fillStyle = colours['plan-room-edge'];
                    context.globalAlpha = 0.75;
                    context.fill();
                    context.globalAlpha = 1;
                }
                context.strokeStyle = selected ? colours['plan-select'] : hovered ? colours['plan-hover'] : colours['plan-room-edge'];
                context.lineWidth = selected ? 2.5 : 1;
                context.setLineDash(block.list === 'levels' ? [4, 3] : []);
                context.stroke();
                context.setLineDash([]);
                if (block.list === 'platforms')
                {
                    const [x0, y0] = s(block.outline[0][0], block.outline[0][1]);
                    const [x2, y2] = s(block.outline[2][0], block.outline[2][1]);
                    context.beginPath();
                    context.moveTo(x0, y0);
                    context.lineTo(x2, y2);
                    context.stroke();
                }
            }
        }
    }

    // Author mode's things from the files: those the core's layout does not draw (switches, exits, ghosts, things
    // added since the last view), and the wiring's links.
    private drawPlaced(context: CanvasRenderingContext2D, layout: ViewLayoutResult, s: (x: number, y: number) => [number, number],
        colours: Record<string, string>): void
    {
        const things = placedThings(this.source!.files, this.layout);
        const built = new Set(layout.things.map((thing) => thing.id));
        drawWiring(context, s, this.source!.files, this.layout, colours['plan-link'], things);
        for (const thing of things)
        {
            if (thing.list === 'start' ? Boolean(layout.start) && !thing.ghost : built.has(thing.address) && !thing.ghost)
            {
                continue;
            }
            const [x, y] = s(thing.at[0], thing.at[1]);
            const marked = thing.address === this.selection ? colours['plan-select'] : thing.address === this.hover ? colours['plan-hover'] : null;
            drawMark(context, x, y, thing.list, marked ?? (thing.list === 'start' ? colours['plan-start'] : colours['plan-thing']), thing.ghost);
        }
    }

    private drawStaleOpenings(context: CanvasRenderingContext2D, s: (x: number, y: number) => [number, number], colours: Record<string, string>): void
    {
        for (const opening of this.staleOpenings)
        {
            if (!opening.a || !opening.b)
            {
                continue;
            }
            const [ax, ay] = s(opening.a[0], opening.a[1]);
            const [bx, by] = s(opening.b[0], opening.b[1]);
            context.strokeStyle = colours.warn;
            context.lineWidth = 3;
            context.setLineDash([3, 3]);
            context.beginPath();
            context.moveTo(ax, ay);
            context.lineTo(bx, by);
            context.stroke();
            context.setLineDash([]);
        }
    }

    private hatchCache = new Map<string, CanvasPattern | null>();

    private hatch(colour: string): CanvasPattern | null
    {
        let pattern = this.hatchCache.get(colour);
        if (pattern === undefined)
        {
            const tile = document.createElement('canvas');
            tile.width = 8;
            tile.height = 8;
            const context = tile.getContext('2d')!;
            context.strokeStyle = colour;
            context.globalAlpha = 0.55;
            context.lineWidth = 1.5;
            context.beginPath();
            context.moveTo(0, 8);
            context.lineTo(8, 0);
            context.stroke();
            pattern = this.context.createPattern(tile, 'repeat');
            this.hatchCache.set(colour, pattern);
        }
        return pattern;
    }

    private drawHeat(context: CanvasRenderingContext2D, heat: PlanHeat, s: (x: number, y: number) => [number, number],
        colours: Record<string, string>): void
    {
        const half = heat.cell / 2;
        context.globalAlpha = 0.5;
        for (const point of heat.points)
        {
            const [x0, y0] = s(point[0] - half, point[1] + half);
            const [x1, y1] = s(point[0] + half, point[1] - half);
            const [r, g, b] = heatColour(point[2]);
            context.fillStyle = `rgb(${r}, ${g}, ${b})`;
            context.fillRect(x0, y0, Math.max(1, x1 - x0 - 1), Math.max(1, y1 - y0 - 1));
        }
        context.globalAlpha = 0.9;
        // Floor only the rebuild has: blue dots (as `oymap compare` draws them).
        context.fillStyle = 'rgb(70, 130, 255)';
        for (const point of heat.extra)
        {
            const [x, y] = s(point[0], point[1]);
            context.fillRect(x - 2, y - 2, 4, 4);
        }
        context.globalAlpha = 1;
        context.font = '600 11px var(--font-ui, sans-serif)';
        context.textAlign = 'center';
        context.textBaseline = 'middle';
        for (const place of heat.worst)
        {
            const [x, y] = s(place.at[0], place.at[1]);
            context.fillStyle = colours.surface;
            context.strokeStyle = colours.text;
            context.lineWidth = 1.5;
            context.beginPath();
            context.arc(x, y, 8, 0, Math.PI * 2);
            context.fill();
            context.stroke();
            context.fillStyle = colours.text;
            context.fillText(place.label, x, y + 0.5);
        }
        context.textAlign = 'start';
        context.textBaseline = 'alphabetic';
    }

    private drawGrid(context: CanvasRenderingContext2D, view: ViewTransform, colour: string): void
    {
        let step = 512;
        while (step * view.scale < 24)
        {
            step *= 2;
        }
        while (step * view.scale > 160 && step > 64)
        {
            step /= 2;
        }
        const [x0, y1] = toWorld(view, 0, 0);
        const [x1, y0] = toWorld(view, view.width, view.height);
        context.strokeStyle = colour;
        context.lineWidth = 1;
        context.beginPath();
        for (let x = Math.floor(x0 / step) * step; x <= x1; x += step)
        {
            const [sx] = toScreen(view, x, 0);
            context.moveTo(Math.round(sx) + 0.5, 0);
            context.lineTo(Math.round(sx) + 0.5, view.height);
        }
        for (let y = Math.floor(y0 / step) * step; y <= y1; y += step)
        {
            const [, sy] = toScreen(view, 0, y);
            context.moveTo(0, Math.round(sy) + 0.5);
            context.lineTo(view.width, Math.round(sy) + 0.5);
        }
        context.stroke();
    }

    private drawThing(context: CanvasRenderingContext2D, thing: ViewThing, s: (x: number, y: number) => [number, number], colours: Record<string, string>): void
    {
        const [x, y] = s(thing.at[0], thing.at[1]);
        const marked = thing.id === this.selection ? colours['plan-select'] : thing.id === this.hover ? colours['plan-hover'] : null;
        const r = marked ? 6 : 4;
        context.fillStyle = marked ?? colours['plan-thing'];
        context.strokeStyle = marked ?? colours['plan-thing'];
        context.lineWidth = 1.5;
        context.beginPath();
        switch (thing.kind)
        {
        case 'chest':
            context.rect(x - r, y - r * 0.7, r * 2, r * 1.4);
            context.fill();
            break;
        case 'monster':
            context.arc(x, y, r + 1, 0, Math.PI * 2);
            context.stroke();
            context.beginPath();
            context.arc(x, y, 1.5, 0, Math.PI * 2);
            context.fill();
            break;
        case 'item':
            context.moveTo(x, y - r);
            context.lineTo(x + r, y);
            context.lineTo(x, y + r);
            context.lineTo(x - r, y);
            context.closePath();
            context.fill();
            break;
        case 'light':
            for (let i = 0; i < 4; ++i)
            {
                const a = (i * Math.PI) / 4;
                context.moveTo(x - Math.cos(a) * r, y - Math.sin(a) * r);
                context.lineTo(x + Math.cos(a) * r, y + Math.sin(a) * r);
            }
            context.stroke();
            break;
        case 'spawn':
            context.moveTo(x - r, y - r);
            context.lineTo(x + r, y + r);
            context.moveTo(x + r, y - r);
            context.lineTo(x - r, y + r);
            context.stroke();
            if (thing.radius)
            {
                context.beginPath();
                context.setLineDash([2, 3]);
                const [ex] = s(thing.at[0] + thing.radius, thing.at[1]);
                context.arc(x, y, Math.abs(ex - x), 0, Math.PI * 2);
                context.stroke();
                context.setLineDash([]);
            }
            break;
        case 'switch':
        case 'exit':
            // At the middle of its face, as the core placed it (view.layout).
            drawMark(context, x, y, thing.kind === 'switch' ? 'switches' : 'exits', marked ?? colours['plan-thing'], false);
            break;
        default:
            context.arc(x, y, r * 0.6, 0, Math.PI * 2);
            context.fill();
            break;
        }
    }

    private drawLabels(layout: ViewLayoutResult, view: ViewTransform): void
    {
        const ids = [this.hover, this.selection].filter((id): id is string => !!id);
        for (const id of [...new Set(ids)])
        {
            const bounds = emptyBounds();
            this.objectBounds(id, bounds);
            if (isEmpty(bounds))
            {
                continue;
            }
            const [x, y] = toScreen(view, (bounds.minX + bounds.maxX) / 2, bounds.maxY);
            const text = document.createElementNS(SVG_NS, 'text');
            text.setAttribute('x', String(Math.round(x)));
            text.setAttribute('y', String(Math.round(y - 8)));
            text.setAttribute('class', id === this.selection ? 'oy-plan-label oy-plan-label-selected' : 'oy-plan-label');
            text.textContent = id;
            this.svg.append(text);
        }
        if (this.stale)
        {
            const text = document.createElementNS(SVG_NS, 'text');
            text.setAttribute('x', '12');
            text.setAttribute('y', String(view.height - 12));
            text.setAttribute('class', 'oy-plan-label oy-plan-stale');
            text.textContent = `stale: the plan of revision ${layout.view_revision.slice(0, 8)}`;
            this.svg.append(text);
        }
    }

    // Where the pointer was last over the plan (map units).
    private pointerWorld: [number, number] | null = null;

    // The whole address under the pointer (the store keeps top-level ids only; an outdoor word's hover needs all).
    private pointerOwner: string | null = null;

    private setHoverInternal(id: string | null, world: [number, number] | null): void
    {
        if (world)
        {
            this.pointerWorld = world;
        }
        const owner = id?.startsWith('sketch.yml#') ? id.slice('sketch.yml#'.length) : id;
        if (owner !== this.pointerOwner)
        {
            this.pointerOwner = owner;
            this.request();
        }
        this.setHover(id);
        this.callbacks.onHover(id, world);
    }

    private eventWorld(event: PointerEvent | WheelEvent): [number, number]
    {
        const rect = this.canvas.getBoundingClientRect();
        return toWorld(this.view!, event.clientX - rect.left, event.clientY - rect.top);
    }

    private readonly onWheel = (event: WheelEvent) =>
    {
        if (!this.view)
        {
            return;
        }
        event.preventDefault();
        this.autoFit = false;
        const rect = this.canvas.getBoundingClientRect();
        this.view = zoomAt(this.view, event.clientX - rect.left, event.clientY - rect.top, Math.exp(-event.deltaY * 0.0015));
        this.request();
    };

    private readonly onKey = (event: KeyboardEvent) =>
    {
        const typing = (event.target as HTMLElement | null)?.closest?.('input, textarea, select, .cm-editor, [contenteditable]');
        if (event.code === 'Space' && !typing)
        {
            this.spaceDown = event.type === 'keydown';
        }
        // The active tool's keys (Enter, Esc, Backspace, PgUp, PgDn) before the app's: a drawing's Esc cancels the
        // drawing, not the selection.
        if (event.type === 'keydown' && this.tool && !typing && !event.ctrlKey && !event.metaKey && this.tool.key(event))
        {
            event.preventDefault();
            event.stopImmediatePropagation();
            this.request();
        }
    };

    private readonly onDoubleClick = (event: MouseEvent) =>
    {
        if (this.tool && this.view)
        {
            const rect = this.canvas.getBoundingClientRect();
            const world = toWorld(this.view, event.clientX - rect.left, event.clientY - rect.top);
            if (this.tool.doubleClick(world, event))
            {
                event.preventDefault();
                this.request();
            }
        }
    };

    private readonly onPointerDown = (event: PointerEvent) =>
    {
        if (!this.view)
        {
            return;
        }
        this.canvas.setPointerCapture(event.pointerId);
        if (this.overlay?.down?.(this.eventWorld(event), event))
        {
            this.autoFit = false;
            this.overlayPressed = true;
            this.request();
            return;
        }
        if (this.tool && event.button === 0 && !this.spaceDown && this.tool.down(this.eventWorld(event), event))
        {
            // Drawing: the view no longer follows the map's bounds by itself.
            this.autoFit = false;
            this.toolPressed = true;
            this.canvas.style.cursor = this.tool.cursor();
            this.request();
            return;
        }
        this.dragging = { x: event.clientX, y: event.clientY, view: this.view, moved: event.button === 1 || this.spaceDown };
        if (event.button === 1)
        {
            event.preventDefault();
        }
    };

    private readonly onPointerMove = (event: PointerEvent) =>
    {
        if (!this.view)
        {
            return;
        }
        if (this.overlayPressed)
        {
            this.overlay?.move?.(this.eventWorld(event), event);
            this.request();
            return;
        }
        if (this.tool)
        {
            const world = this.eventWorld(event);
            this.pointerWorld = world;
            this.tool.move(world, event, this.toolPressed);
            this.canvas.style.cursor = this.tool.cursor();
            if (this.toolPressed)
            {
                this.callbacks.onHover(null, world);
                return;
            }
        }
        if (this.dragging)
        {
            const dx = event.clientX - this.dragging.x;
            const dy = event.clientY - this.dragging.y;
            if (this.dragging.moved || Math.hypot(dx, dy) > 4)
            {
                this.dragging.moved = true;
                this.autoFit = false;
                const start = this.dragging.view;
                this.view = { ...start, cx: start.cx - dx / start.scale, cy: start.cy + dy / start.scale };
                this.request();
                return;
            }
        }
        const world = this.eventWorld(event);
        this.setHoverInternal(this.hitTest(world[0], world[1], this.view.scale), world);
    };

    private readonly onPointerUp = (event: PointerEvent) =>
    {
        if (this.overlayPressed && this.view)
        {
            this.overlayPressed = false;
            this.overlay?.up?.(this.eventWorld(event), event);
            this.request();
            return;
        }
        if (this.toolPressed && this.tool && this.view)
        {
            this.toolPressed = false;
            const world = this.eventWorld(event);
            this.tool.up(world, event);
            this.canvas.style.cursor = this.tool.cursor();
            this.request();
            if (this.tool.passClick?.())
            {
                this.callbacks.onPick(this.hitTest(world[0], world[1], this.view.scale));
            }
            return;
        }
        const dragging = this.dragging;
        this.dragging = null;
        if (!this.view || !dragging || dragging.moved || event.button !== 0)
        {
            return;
        }
        const world = this.eventWorld(event);
        this.callbacks.onPick(this.hitTest(world[0], world[1], this.view.scale));
    };
}

function pointInOutline(outline: readonly (readonly number[])[], x: number, y: number): boolean
{
    let inside = false;
    for (let i = 0, j = outline.length - 1; i < outline.length; j = i++)
    {
        const [xi, yi] = outline[i];
        const [xj, yj] = outline[j];
        if ((yi > y) !== (yj > y) && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)
        {
            inside = !inside;
        }
    }
    return inside;
}
