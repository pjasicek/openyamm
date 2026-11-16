// The outdoor tools on the plan (S5_BROWSER_EDITOR.md 3.18, the Outdoor table; W2): Select with the sketch's handles,
// the grid editor, the land words, the sculpt brush and its patches, the frame and rim, water, rivers, roads,
// districts and plots, buildings (a box, then parts inside it), every other structure by its kind's geometry, the
// ground brush, scatter, areas, actors and arrival points. The plan hands them map units; they work in cells and
// write sketch.yml (and the plan entries its words name) as one transaction per gesture.
import type { EditApplyResult, FileTrees, JsonObject, JsonValue, Op, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import type { ToolName } from './stages.ts';
import { DEFAULT_OUTDOOR } from './stages.ts';
import type { OutdoorOptions } from './stages.ts';
import { BaseTool, DrawingTool, handle, label, strokePath } from './toolbase.ts';
import type { PlanTool, ToScreen, ToolHost } from './toolbase.ts';
import { CELL, NODES, cellCentre, cellToLocal, cellToMap, extentOf, insideOrOn, mapToCell, nearestNode, roadStep, snapCell } from './cells.ts';
import { isObject, keyedAt, keysOf, segment } from './keys.ts';
import { LINE_KINDS, OUTLINE_KINDS, appendToSketch, insertPointOp, movePointsOps, partCells, removePointOp, shapeAt, sketchOf, sketchPatch, sketchShapes } from './sketch.ts';
import type { SketchShape } from './sketch.ts';
import { Stroke, paintDisc, rasterise, sculptMask, smoothed, strokeBlock, strokePatch, traceMask } from './strokes.ts';
import type { WrittenBlock } from './strokes.ts';
import { enteredBuilding } from '../plan/outdoorplan.ts';

// --- what every outdoor tool shares -------------------------------------------------------------------------------

export function isOutdoorFiles(files: FileTrees | undefined): boolean
{
    return files?.['project.yml']?.tree.kind === 'outdoor' || (Boolean(files?.['sketch.yml']) && !files?.['rooms.yml']);
}

function outdoorOptions(host: ToolHost): OutdoorOptions
{
    return host.options().outdoor ?? DEFAULT_OUTDOOR;
}

// The id the core gave the first object a gesture added to a file ("sketch.yml#thing:structure_3" -> thing:structure_3).
export function allocatedIn(result: EditApplyResult | null, file: string): string | null
{
    const entry = (result?.ids_allocated ?? []).find((made) => made.startsWith(`${file}#`));
    return entry ? entry.slice(entry.indexOf('#') + 1) : null;
}

// The key of the last item of a list of sketch.yml in an edit's answer (an item a gesture appended).
export function appendedSketchKey(result: EditApplyResult | null, pointer: string): string | null
{
    let node: JsonValue | undefined = result?.files['sketch.yml']?.tree;
    for (const part of pointer.split('/').slice(1))
    {
        node = isObject(node) ? node[part] : undefined;
    }
    if (!Array.isArray(node) || node.length === 0)
    {
        return null;
    }
    const name = pointer.slice(pointer.lastIndexOf('/') + 1);
    return keysOf(node, name, keyedAt({ file: 'sketch.yml' }, pointer))[node.length - 1];
}

// Items appended to one list of sketch.yml in one transaction (made, with what is above it, when missing).
export function appendManyToSketch(files: FileTrees | undefined, pointer: string, values: JsonValue[]): Op
{
    const first = appendToSketch(files, pointer, values[0]);
    if (first.op !== 'patch')
    {
        return first;
    }
    const step = first.patch[0];
    if (step.op === 'add' && step.path === `${pointer}/-`)
    {
        return sketchPatch(undefined, values.map((value) => ({ op: 'add', path: `${pointer}/-`, value })));
    }
    // The list is made: all of them in it (the value made carries the first; put the rest beside it).
    const made = structuredClone((step as { value: JsonValue }).value);
    let node: JsonValue = made;
    while (isObject(node))
    {
        node = Object.values(node)[0];
    }
    if (Array.isArray(node))
    {
        node.push(...values.slice(1));
    }
    return sketchPatch(undefined, [{ op: 'add', path: step.path, value: made }]);
}

// The plan space a cell point lies in: a district's space, else the map's first zone (the space the whole map is).
export function spaceAt(files: FileTrees | undefined, cell: Point): string
{
    const sketch = sketchOf(files);
    const districts = Array.isArray(sketch?.districts) ? sketch!.districts.filter(isObject) : [];
    for (const district of districts)
    {
        const polygon = Array.isArray(district.polygon) ? district.polygon as Point[] : [];
        if (polygon.length >= 3 && insideOrOn(cell, polygon) && typeof district.space === 'string')
        {
            return district.space;
        }
    }
    const spaces = files?.['plan.yml']?.tree.spaces;
    const zone = Array.isArray(spaces) ? spaces.filter(isObject).find((space) => space.kind === 'zone' || space.kind === 'wild' || space.kind === 'town') : undefined;
    return typeof zone?.id === 'string' ? zone.id : 'zone:land';
}

// The built land's height at a node in map units (view.layout's land), or null.
export function landHeight(host: ToolHost, node: Point): number | null
{
    const land = host.layout()?.land;
    if (!land)
    {
        return null;
    }
    const x = Math.min(land.size - 1, Math.max(0, Math.round(node[0])));
    const y = Math.min(land.size - 1, Math.max(0, Math.round(node[1])));
    return land.heights[y * land.size + x] * land.height_unit;
}

let serial = 0;
const mergeKeyOf = (what: string) => `${what} ${++serial} ${Date.now()}`;

// A tool that clicks points (cells) for a line or an outline: the indoor drawing tool, snapped to whole cells (half
// cells with Shift, or always with the options' half cells).
abstract class CellDrawingTool extends DrawingTool
{
    protected snap(at: Point, event: { shiftKey: boolean; altKey?: boolean }): Point
    {
        const step = event.shiftKey || outdoorOptions(this.host).halfCells ? 0.5 : 1;
        return cellToMap(snapCell(mapToCell(at), step));
    }

    protected cells(points: readonly Point[]): Point[]
    {
        return points.map((p) => mapToCell(p).map((value) => Math.round(value * 2) / 2) as Point);
    }

    protected options(): OutdoorOptions
    {
        return outdoorOptions(this.host);
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        super.draw(context, s);
        if (this.cursorAt)
        {
            const cell = mapToCell(this.cursorAt);
            label(context, s, [this.cursorAt[0], this.cursorAt[1] - 24 * this.host.unitsPerPixel()], `${cell[0]}, ${cell[1]}`, this.host.colour('text'), this.host.colour('surface'));
        }
    }
}

// --- the land words ---------------------------------------------------------------------------------------------

type LandWord = 'ridges' | 'cliffs' | 'terraces' | 'cuts' | 'rough' | 'peaks' | 'patches';

const LAND_LABELS: Record<LandWord, string> = {
    ridges: 'ridge', cliffs: 'cliff', terraces: 'terrace', cuts: 'cut', rough: 'rough ground', peaks: 'peaks', patches: 'sculpt patch',
};

class LandWordTool extends CellDrawingTool
{
    protected readonly closed: boolean;
    protected readonly boxes: boolean;
    protected readonly minimum: number;
    private readonly word: LandWord;

    constructor(host: ToolHost, word: LandWord)
    {
        super(host);
        this.word = word;
        this.closed = word !== 'ridges' && word !== 'cliffs';
        this.boxes = this.closed;
        this.minimum = this.closed ? 3 : 2;
    }

    protected describe(): string
    {
        return `${LAND_LABELS[this.word]}: ${this.points.length} points · ${this.closed ? 'drag a box, or click corners and Enter' : 'click its points, Enter'} · Esc cancels`;
    }

    protected finish(points: Point[]): void
    {
        const o = this.options();
        const cells = this.cells(points);
        let value: JsonObject;
        switch (this.word)
        {
        case 'ridges':
            value = { line: cells, height: o.height, ...(o.ridgeWidth > 1 ? { width: o.ridgeWidth } : {}), ...(o.ridgeSlope > 0 ? { slope: o.ridgeSlope } : {}) };
            break;
        case 'cliffs':
            value = { line: cells, drop: o.cliffDrop, down: o.cliffDown };
            break;
        case 'terraces':
            value = { polygon: cells, height: o.height, ...(o.terraceSlope > 0 ? { slope: o.terraceSlope } : {}) };
            break;
        case 'cuts':
            value = { polygon: cells, floor: o.height };
            break;
        case 'rough':
            value = { polygon: cells, amount: o.roughAmount };
            break;
        case 'peaks':
            value = { polygon: cells, count: o.peaksCount, height: [Math.min(o.peaksLow, o.peaksHigh), Math.max(o.peaksLow, o.peaksHigh)] };
            break;
        case 'patches':
        {
            const [width, depth] = extentOf(cells);
            const count = (sketchOf(this.host.files())?.heights as JsonObject | undefined)?.patches;
            if (width > 32 || depth > 32)
            {
                this.host.note(`A sculpt patch is at most 32 cells across each way (this one ${width} × ${depth}): draw a smaller one`);
                return;
            }
            if (Array.isArray(count) && count.length >= 16)
            {
                this.host.note('A map has at most 16 sculpt patches; mark the land made by hand (Project settings) to sculpt anywhere');
                return;
            }
            value = { polygon: cells };
            break;
        }
        }
        const pointer = `/heights/${this.word}`;
        void this.host.edit({ label: `new ${LAND_LABELS[this.word]}`, ops: [appendToSketch(this.host.files(), pointer, value)] }).then((result) =>
        {
            const key = appendedSketchKey(result, pointer);
            if (key)
            {
                this.host.select(`${pointer}/${segment(key)}`, 'sketch.yml');
            }
        });
    }
}

// A height point or a spire: a click on a whole cell.
class LandPointTool extends BaseTool
{
    private readonly word: 'points' | 'spires';

    constructor(host: ToolHost, word: 'points' | 'spires')
    {
        super(host);
        this.word = word;
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const o = outdoorOptions(this.host);
        const cell = nearestNode(mapToCell(at));
        const value: JsonObject = this.word === 'points' ? { at: cell, h: o.height } : { at: cell, height: o.height };
        const pointer = `/heights/${this.word}`;
        void this.host.edit({ label: `new ${this.word === 'points' ? 'height point' : 'spire'}`, ops: [appendToSketch(this.host.files(), pointer, value)] }).then((result) =>
        {
            const key = appendedSketchKey(result, pointer);
            if (key)
            {
                this.host.select(`${pointer}/${segment(key)}`, 'sketch.yml');
            }
        });
        return true;
    }

    move(at: Point): void
    {
        this.cursorAt = cellToMap(nearestNode(mapToCell(at)));
        this.host.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (this.cursorAt)
        {
            handle(context, s, this.cursorAt, this.host.colour('plan-select'), this.host.colour('surface'), 7);
            label(context, s, this.cursorAt, `${outdoorOptions(this.host).height}`, this.host.colour('text'), this.host.colour('surface'));
        }
    }
}

// --- the grid editor ------------------------------------------------------------------------------------------------

interface GridShape
{
    step: number;
    unit: number;
    rows: number[][];
}

export function gridOf(files: FileTrees | undefined): GridShape | null
{
    const grid = (sketchOf(files)?.heights as JsonObject | undefined)?.grid;
    if (!isObject(grid) || !Array.isArray(grid.rows) || typeof grid.step !== 'number')
    {
        return null;
    }
    return { step: grid.step, unit: typeof grid.unit === 'number' ? grid.unit : 64, rows: grid.rows.map((row) => (Array.isArray(row) ? row.map(Number) : [])) };
}

// Where spot (i across, j down) stands, in cells: the middle of its block of step x step cells.
export function spotCell(grid: { step: number }, i: number, j: number): Point
{
    return [grid.step * i + grid.step / 2, grid.step * j + grid.step / 2];
}

// The spots' new values as one patch: a test of each old value and its replacement (rows are positions).
export function spotOps(grid: GridShape, values: Map<string, number>): Op | null
{
    const steps: PatchStep[] = [];
    for (const [where, value] of values)
    {
        const [j, i] = where.split(',').map(Number);
        if (grid.rows[j]?.[i] === undefined || grid.rows[j][i] === value)
        {
            continue;
        }
        steps.push({ op: 'test', path: `/heights/grid/rows/${j}/${i}`, value: grid.rows[j][i] }, { op: 'replace', path: `/heights/grid/rows/${j}/${i}`, value });
    }
    return steps.length > 0 ? sketchPatch(undefined, steps) : null;
}

// Each spot height a handle with its number; a click or a drag paints the options' height over the spots it
// passes; PgUp and PgDn raise and lower the spot under the cursor by one unit of the grid; Alt click takes a spot's
// height into the options.
class SpotsTool extends BaseTool
{
    private hovered: [number, number] | null = null;
    private painting: Map<string, number> | null = null;

    private grid(): GridShape | null
    {
        return gridOf(this.host.files());
    }

    private spotNear(at: Point): [number, number] | null
    {
        const grid = this.grid();
        if (!grid)
        {
            return null;
        }
        const cell = mapToCell(at);
        const i = Math.round((cell[0] - grid.step / 2) / grid.step);
        const j = Math.round((cell[1] - grid.step / 2) / grid.step);
        if (j < 0 || j >= grid.rows.length || i < 0 || i >= (grid.rows[j]?.length ?? 0))
        {
            return null;
        }
        const spot = spotCell(grid, i, j);
        return Math.hypot(spot[0] - cell[0], spot[1] - cell[1]) * CELL <= Math.max(this.reach(14), grid.step * CELL * 0.35) ? [i, j] : null;
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const grid = this.grid();
        if (!grid)
        {
            const files = this.host.files();
            void this.host.edit({ label: 'a grid of spot heights', ops: [sketchPatch(undefined, [{ op: 'add', path: (sketchOf(files)?.heights ? '/heights/grid' : '/heights'),
                value: sketchOf(files)?.heights ? { step: 16, unit: 64, rows: Array.from({ length: 8 }, () => Array(8).fill(4)) }
                    : { grid: { step: 16, unit: 64, rows: Array.from({ length: 8 }, () => Array(8).fill(4)) } } }])] });
            return true;
        }
        const spot = this.spotNear(at);
        if (!spot)
        {
            return true;
        }
        if (event.altKey)
        {
            this.host.setOptions?.({ outdoor: { ...outdoorOptions(this.host), spotHeight: grid.rows[spot[1]][spot[0]] * grid.unit } });
            this.host.hint(`spot ${spot[0]}, ${spot[1]}: ${grid.rows[spot[1]][spot[0]] * grid.unit} taken as the paint height`);
            return true;
        }
        this.painting = new Map();
        this.paint(spot, grid);
        return true;
    }

    private paint(spot: [number, number], grid: GridShape): void
    {
        const value = Math.round(outdoorOptions(this.host).spotHeight / grid.unit);
        this.painting?.set(`${spot[1]},${spot[0]}`, value);
        this.host.redraw();
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        const spot = this.spotNear(at);
        const grid = this.grid();
        if (pressed && this.painting && spot && grid)
        {
            this.paint(spot, grid);
        }
        if (JSON.stringify(spot) !== JSON.stringify(this.hovered))
        {
            this.hovered = spot;
            this.host.hint(spot && grid ? `spot ${spot[0]}, ${spot[1]}: ${grid.rows[spot[1]][spot[0]] * grid.unit} · click or drag paints ${outdoorOptions(this.host).spotHeight} · PgUp/PgDn ±${grid.unit} · Alt click takes it`
                : 'spot heights: hover one; click or drag paints the options\' height');
            this.host.redraw();
        }
    }

    up(): void
    {
        const painting = this.painting;
        this.painting = null;
        const grid = this.grid();
        if (!painting || !grid)
        {
            return;
        }
        const op = spotOps(grid, painting);
        if (op)
        {
            void this.host.edit({ label: `spot heights (${painting.size})`, ops: [op] });
        }
        this.host.redraw();
    }

    key(event: KeyboardEvent): boolean
    {
        if ((event.code !== 'PageUp' && event.code !== 'PageDown') || !this.hovered)
        {
            return false;
        }
        const grid = this.grid();
        if (!grid)
        {
            return false;
        }
        const [i, j] = this.hovered;
        const value = grid.rows[j][i] + (event.code === 'PageUp' ? 1 : -1);
        if (value < 0)
        {
            this.host.note('A spot height cannot go below 0');
            return true;
        }
        const op = spotOps(grid, new Map([[`${j},${i}`, value]]));
        if (op)
        {
            void this.host.edit({ label: `spot ${i}, ${j}`, mergeKey: `spot ${i} ${j}`, ops: [op] });
            this.host.hint(`spot ${i}, ${j}: ${value * grid.unit}`);
        }
        return true;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const grid = this.grid();
        if (!grid)
        {
            return;
        }
        const accent = this.host.colour('plan-select');
        const surface = this.host.colour('surface');
        const text = this.host.colour('text');
        context.font = '600 11px ui-monospace, monospace';
        grid.rows.forEach((row, j) => row.forEach((written, i) =>
        {
            const value = this.painting?.get(`${j},${i}`) ?? written;
            const at = cellToMap(spotCell(grid, i, j));
            const [x, y] = s(at[0], at[1]);
            const hovered = this.hovered?.[0] === i && this.hovered?.[1] === j;
            const changed = value !== written;
            context.fillStyle = changed ? this.host.colour('warn') : surface;
            context.strokeStyle = hovered ? this.host.colour('plan-hover') : accent;
            context.lineWidth = hovered ? 2.5 : 1.5;
            const textWidth = context.measureText(String(value * grid.unit)).width;
            context.fillRect(x - textWidth / 2 - 5, y - 9, textWidth + 10, 18);
            context.strokeRect(x - textWidth / 2 - 5, y - 9, textWidth + 10, 18);
            context.fillStyle = changed ? surface : text;
            context.fillText(String(value * grid.unit), x - textWidth / 2, y + 4);
        }));
    }

    cursor(): string
    {
        return this.hovered ? 'pointer' : 'crosshair';
    }
}

// --- the sculpt brush -------------------------------------------------------------------------------------------

function patchesOf(files: FileTrees | undefined): Point[][]
{
    const heights = sketchOf(files)?.heights;
    const patches = isObject(heights) && Array.isArray(heights.patches) ? heights.patches.filter(isObject) : [];
    return patches.map((patch) => (Array.isArray(patch.polygon) ? patch.polygon as Point[] : []));
}

function handMade(files: FileTrees | undefined): boolean
{
    const heights = sketchOf(files)?.heights;
    return isObject(heights) && heights.hand_made === true;
}

// The built land in map units, node by node (for the preview).
function builtHeights(host: ToolHost): Float32Array | null
{
    const land = host.layout()?.land;
    if (!land || land.size !== NODES)
    {
        return null;
    }
    return Float32Array.from(land.heights, (value) => value * land.height_unit);
}

// Raise, lower, smooth and flatten (the options' mode, radius in cells, strength in map units a dab). Previewed while
// the pointer moves (the plan tints the nodes, the 3D view moves its land) and written once on pointer-up: raise
// and lower as a block of heights.strokes, smooth as a heights.smooth outline, flatten as a terrace at the height
// under the first press. On land the sketch describes only inside a sculpt patch; anywhere on land made by hand.
class SculptTool extends BaseTool
{
    private stroke: Stroke | null = null;
    private base: Float32Array | null = null;
    private flatHeight: Promise<number | null> | null = null;
    private flatKnown: number | null = null;
    private lastPreview = 0;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const files = this.host.files();
        const o = outdoorOptions(this.host);
        const allowed = sculptMask(patchesOf(files), handMade(files));
        const node = nearestNode(mapToCell(at));
        if (!allowed[node[1] * NODES + node[0]])
        {
            this.host.note(handMade(files) ? 'Nothing to sculpt there' : 'The brush works inside a sculpt patch on land the sketch describes: draw one (Patch tool), or mark the land made by hand in the project settings');
            return true;
        }
        this.stroke = new Stroke(o.brushMode, o.brushRadius, o.brushStrength, allowed);
        this.base = builtHeights(this.host);
        this.flatKnown = null;
        if (o.brushMode === 'flatten')
        {
            // The height under the first press, from the built land (view.terrain_query).
            const cell = mapToCell(at);
            this.flatHeight = (this.host.terrainHeights?.([cell]) ?? Promise.resolve(null)).then((heights) =>
            {
                const value = heights?.[0] ?? landHeight(this.host, node);
                this.flatKnown = value;
                return value;
            });
        }
        this.stroke.to(mapToCell(at));
        this.preview();
        return true;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        if (pressed && this.stroke)
        {
            this.stroke.to(mapToCell(at));
            const now = performance.now();
            // The 3D land at most every 50 ms (the plan's tint every move).
            if (now - this.lastPreview > 50)
            {
                this.lastPreview = now;
                this.preview();
            }
        }
        this.host.redraw();
    }

    // The difference the stroke makes, node by node, in map units.
    private difference(): Float32Array | null
    {
        const stroke = this.stroke;
        if (!stroke)
        {
            return null;
        }
        if (stroke.mode === 'raise' || stroke.mode === 'lower')
        {
            return stroke.delta;
        }
        if (!this.base)
        {
            return null;
        }
        const out = new Float32Array(NODES * NODES);
        if (stroke.mode === 'smooth')
        {
            const after = smoothed(this.base, stroke.covered, 1, 2);
            for (let index = 0; index < out.length; ++index)
            {
                out[index] = after[index] - this.base[index];
            }
            return out;
        }
        if (this.flatKnown !== null)
        {
            for (let index = 0; index < out.length; ++index)
            {
                out[index] = stroke.covered[index] ? this.flatKnown - this.base[index] : 0;
            }
        }
        return out;
    }

    private preview(): void
    {
        this.host.landPreview?.(this.difference());
    }

    up(): void
    {
        const stroke = this.stroke;
        this.stroke = null;
        this.host.redraw();
        if (!stroke || stroke.empty())
        {
            this.host.landPreview?.(null);
            return;
        }
        this.preview();
        const files = this.host.files();
        const heights = sketchOf(files)?.heights as JsonObject | undefined;
        const refused = (result: EditApplyResult | null) =>
        {
            if (!result)
            {
                this.host.landPreview?.(null);
            }
        };
        if (stroke.mode === 'raise' || stroke.mode === 'lower')
        {
            const block = strokeBlock(stroke.delta);
            if (!block)
            {
                this.host.note('The stroke moved no node by half a step (16): stronger, or more passes');
                this.host.landPreview?.(null);
                return;
            }
            const steps = strokePatch(block, Array.isArray(heights?.strokes) ? heights!.strokes as unknown as WrittenBlock[] : undefined);
            if (steps.length === 0)
            {
                this.host.landPreview?.(null);
                return;
            }
            void this.host.edit({ label: `${stroke.mode} stroke`, ops: [sketchPatch(undefined, steps)] }).then(refused);
            return;
        }
        const outlines = traceMask(stroke.covered, NODES, NODES, -0.5);
        if (outlines.length === 0)
        {
            this.host.landPreview?.(null);
            return;
        }
        if (stroke.mode === 'smooth')
        {
            void this.host.edit({ label: 'smooth stroke', ops: [appendManyToSketch(files, '/heights/smooth', outlines.map((polygon) => ({ polygon })))] }).then(refused);
            return;
        }
        void (this.flatHeight ?? Promise.resolve(null)).then((height) =>
        {
            if (height === null)
            {
                this.host.note('The height under the press is not known (no built land yet)');
                this.host.landPreview?.(null);
                return;
            }
            const level = Math.max(0, Math.min(8160, Math.round(height)));
            void this.host.edit({ label: `flatten at ${level}`, ops: [appendManyToSketch(files, '/heights/terraces', outlines.map((polygon) => ({ polygon, height: level })))] }).then(refused);
        });
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const o = outdoorOptions(this.host);
        if (this.cursorAt)
        {
            const [x, y] = s(this.cursorAt[0], this.cursorAt[1]);
            const r = Math.abs(s(o.brushRadius * CELL, 0)[0] - s(0, 0)[0]);
            context.strokeStyle = this.host.colour('plan-select');
            context.lineWidth = 1.5;
            context.beginPath();
            context.arc(x, y, r, 0, Math.PI * 2);
            context.stroke();
            label(context, s, this.cursorAt, `${o.brushMode} r${o.brushRadius}`, this.host.colour('text'), this.host.colour('surface'));
        }
        const stroke = this.stroke;
        const difference = stroke ? this.difference() : null;
        if (!stroke)
        {
            return;
        }
        const size = Math.max(2, Math.abs(s(CELL, 0)[0] - s(0, 0)[0]));
        const up = this.host.colour('warn');
        const down = this.host.colour('plan-water');
        for (let index = 0; index < stroke.covered.length; ++index)
        {
            if (!stroke.covered[index])
            {
                continue;
            }
            const value = difference?.[index] ?? 0;
            const [x, y] = s(...cellToMap([index % NODES, Math.floor(index / NODES)]));
            context.fillStyle = value < 0 ? down : up;
            context.globalAlpha = Math.min(0.8, 0.2 + Math.abs(value) / 256);
            context.fillRect(x - size / 2, y - size / 2, size, size);
        }
        context.globalAlpha = 1;
    }
}

// --- the frame and the rim ------------------------------------------------------------------------------------------

// Drag the square the party can walk.
class FrameTool extends CellDrawingTool
{
    protected readonly closed = true;
    protected readonly boxes = true;

    protected describe(): string
    {
        return 'the playable square: drag it (whole cells)';
    }

    protected finish(points: Point[], asBox: boolean): void
    {
        if (!asBox)
        {
            this.host.note('Drag a box for the playable square');
            return;
        }
        const cells = this.cells(points).map((p) => [Math.round(p[0]), Math.round(p[1])] as Point);
        const xs = cells.map((p) => p[0]);
        const ys = cells.map((p) => p[1]);
        const value = [Math.min(...xs), Math.min(...ys), Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys)];
        void this.host.edit({ label: 'the playable square', ops: [{ op: 'set_value', file: 'sketch.yml', path: 'frame.playable', value }] }).then(() =>
            this.host.select('/frame/playable', 'sketch.yml'));
    }
}

// Drag along a side of the map: a stretch of rim there (the options' form and height).
class RimTool extends BaseTool
{
    private from: Point | null = null;

    private static sideOf(cell: Point): 'north' | 'east' | 'south' | 'west'
    {
        const distances: [string, number][] = [['north', cell[1]], ['south', 128 - cell[1]], ['west', cell[0]], ['east', 128 - cell[0]]];
        distances.sort((a, b) => a[1] - b[1]);
        return distances[0][0] as 'north' | 'east' | 'south' | 'west';
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        this.from = mapToCell(at);
        this.cursorAt = at;
        return true;
    }

    move(at: Point): void
    {
        this.cursorAt = at;
        this.host.redraw();
    }

    up(at: Point): void
    {
        const from = this.from;
        this.from = null;
        if (!from)
        {
            return;
        }
        const to = mapToCell(at);
        const side = RimTool.sideOf(from);
        const along = side === 'north' || side === 'south' ? [from[0], to[0]] : [from[1], to[1]];
        const span = [Math.max(0, Math.round(Math.min(...along))), Math.min(128, Math.round(Math.max(...along)))];
        if (span[1] - span[0] < 2)
        {
            this.host.note('Drag along a side of the map, near its edge: the stretch of rim the drag covers');
            return;
        }
        const o = outdoorOptions(this.host);
        const value: JsonObject = { side, span, form: o.rimForm, ...(o.rimForm === 'level' ? { height: o.height } : { height: [Math.min(o.peaksLow, o.peaksHigh), Math.max(o.peaksLow, o.peaksHigh)] }) };
        void this.host.edit({ label: `rim on the ${side}`, ops: [appendToSketch(this.host.files(), '/frame/rim', value)] }).then((result) =>
        {
            const key = appendedSketchKey(result, '/frame/rim');
            if (key)
            {
                this.host.select(`/frame/rim/${segment(key)}`, 'sketch.yml');
            }
        });
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (!this.from || !this.cursorAt)
        {
            return;
        }
        strokePath(context, s, [cellToMap(this.from), this.cursorAt], false);
        context.strokeStyle = this.host.colour('plan-select');
        context.lineWidth = 6;
        context.globalAlpha = 0.6;
        context.stroke();
        context.globalAlpha = 1;
        label(context, s, this.cursorAt, `rim: ${RimTool.sideOf(this.from)}`, this.host.colour('text'), this.host.colour('surface'));
    }
}

// --- water, rivers, roads, districts, plots ---------------------------------------------------------------------

// A plan entry first (the word names it), then the sketch's word, folded into one history entry.
async function withPlanEntry(host: ToolHost, label: string, add: Op, then: (id: string) => Op): Promise<{ id: string; result: EditApplyResult | null } | null>
{
    const mergeKey = mergeKeyOf(label);
    const made = await host.edit({ label, mergeKey, ops: [add] });
    const id = allocatedIn(made, 'plan.yml');
    if (!id)
    {
        return null;
    }
    const result = await host.edit({ label, mergeKey, ops: [then(id)] });
    return { id, result };
}

class WaterTool extends CellDrawingTool
{
    protected readonly closed: boolean;
    protected readonly boxes: boolean;
    protected readonly minimum: number;
    private readonly river: boolean;

    constructor(host: ToolHost, river: boolean)
    {
        super(host);
        this.river = river;
        this.closed = !river;
        this.boxes = !river;
        this.minimum = river ? 2 : 3;
    }

    protected describe(): string
    {
        return this.river ? `river: ${this.points.length} points of its middle line, from the source down · Enter` : `water: ${this.points.length} corners · drag a box, or click corners and Enter`;
    }

    protected finish(points: Point[]): void
    {
        const o = this.options();
        const cells = this.cells(points).map((p) => [Math.round(p[0]), Math.round(p[1])] as Point);
        // The surface: the options' level, else a step under the lowest land on the outline.
        const lowest = Math.min(...cells.map((cell) => landHeight(this.host, nearestNode(cell)) ?? 256));
        const level = o.waterLevel > 0 ? o.waterLevel : Math.max(0, Math.floor(lowest / 32) * 32 - 32);
        const name = this.river ? 'River' : o.waterKind === 'pond' ? 'Pond' : o.waterKind === 'lake' ? 'Lake' : o.waterKind === 'sea' ? 'Sea' : 'Inlet';
        const pointer = this.river ? '/water/rivers' : '/water/bodies';
        void withPlanEntry(this.host, `new ${name.toLowerCase()}`, { op: 'add', to: 'spaces', file: 'plan.yml', value: { kind: 'water', name } }, (id) =>
            appendToSketch(this.host.files(), pointer, this.river ? { id, line: cells, ...(o.riverWidth !== 1 ? { width_cells: o.riverWidth } : {}), level }
                : { id, kind: o.waterKind, level, polygon: cells, ...(o.tileSet ? { tile_set: o.tileSet } : {}) })).then((made) =>
        {
            if (made?.result)
            {
                this.host.select(`${pointer}/${segment(made.id)}`, 'sketch.yml');
            }
        });
    }
}

// Click cells: the road steps square or at 45 degrees from each point to the next (cell centres); Enter makes it,
// with its plan link (a road between the spaces at its two ends).
class RoadTool extends BaseTool
{
    private line: Point[] = [];

    private next(at: Point): Point
    {
        const cell = cellCentre(mapToCell(at));
        const last = this.line.at(-1);
        return last && outdoorOptions(this.host).roadSteps ? roadStep(last, cell) : cell;
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const point = this.next(at);
        const last = this.line.at(-1);
        if (!last || last[0] !== point[0] || last[1] !== point[1])
        {
            this.line.push(point);
        }
        this.host.hint(`road: ${this.line.length} points · Enter makes it · Backspace takes one back · Esc cancels · Alt: any angle`);
        this.host.redraw();
        return true;
    }

    move(at: Point, event: PointerEvent): void
    {
        this.cursorAt = event.altKey ? cellToMap(cellCentre(mapToCell(at))) : cellToMap(this.next(at));
        this.host.redraw();
    }

    key(event: KeyboardEvent): boolean
    {
        if (event.code === 'Escape' && this.line.length > 0)
        {
            this.line = [];
            this.host.hint(null);
            return true;
        }
        if (event.code === 'Backspace' && this.line.length > 0)
        {
            this.line.pop();
            return true;
        }
        if (event.code !== 'Enter' || this.line.length === 0)
        {
            return false;
        }
        const line = this.line;
        this.line = [];
        this.host.hint(null);
        if (line.length < 2)
        {
            this.host.note('A road needs two points at least');
            return true;
        }
        const files = this.host.files();
        const o = outdoorOptions(this.host);
        const from = spaceAt(files, line[0]);
        const to = spaceAt(files, line[line.length - 1]);
        void withPlanEntry(this.host, 'new road', { op: 'add', to: 'links', file: 'plan.yml', value: { from, to, kind: 'road' } }, (id) =>
            appendToSketch(this.host.files(), '/roads', { link: id, line, width: o.roadWidth, ...(o.roadSurface ? { surface: o.roadSurface } : {}) })).then((made) =>
        {
            const key = appendedSketchKey(made?.result ?? null, '/roads');
            if (key)
            {
                this.host.select(`/roads/${segment(key)}`, 'sketch.yml');
            }
        });
        return true;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const line = [...this.line.map(cellToMap), ...(this.cursorAt && this.line.length > 0 ? [this.cursorAt] : [])];
        if (line.length > 0)
        {
            strokePath(context, s, line, false);
            context.strokeStyle = this.host.colour('plan-link');
            context.lineWidth = Math.max(3, Math.abs(s(CELL * 0.8, 0)[0] - s(0, 0)[0]));
            context.globalAlpha = 0.6;
            context.stroke();
            context.globalAlpha = 1;
            this.line.forEach((p) => handle(context, s, cellToMap(p), this.host.colour('plan-select'), this.host.colour('surface')));
        }
        if (this.cursorAt)
        {
            const cell = mapToCell(this.cursorAt);
            handle(context, s, this.cursorAt, this.host.colour('plan-select'), this.host.colour('surface'), 5);
            label(context, s, this.cursorAt, `${cell[0]}, ${cell[1]}`, this.host.colour('text'), this.host.colour('surface'));
        }
    }
}

// A district's outline for a plan space (the options' space, or a new district space).
class DistrictTool extends CellDrawingTool
{
    protected readonly closed = true;
    protected readonly boxes = true;

    protected describe(): string
    {
        return `district: ${this.points.length} corners · drag a box, or click corners and Enter`;
    }

    protected finish(points: Point[]): void
    {
        const o = this.options();
        const polygon = this.cells(points);
        const write = (space: string) => appendToSketch(this.host.files(), '/districts', { space, polygon });
        const after = (result: EditApplyResult | null) =>
        {
            const key = appendedSketchKey(result, '/districts');
            if (key)
            {
                this.host.select(`/districts/${segment(key)}`, 'sketch.yml');
            }
        };
        if (o.districtSpace)
        {
            void this.host.edit({ label: `district of ${o.districtSpace}`, ops: [write(o.districtSpace)] }).then(after);
            return;
        }
        void withPlanEntry(this.host, 'new district', { op: 'add', to: 'spaces', file: 'plan.yml', value: { kind: 'district', name: o.districtName || 'District' } }, write)
            .then((made) => after(made?.result ?? null));
    }
}

// The plan's buildings of a space ({id, type, footprint_cells}).
export function planBuildings(files: FileTrees | undefined, space?: string): { id: string; space: string; footprint: Point }[]
{
    const spaces = files?.['plan.yml']?.tree.spaces;
    const out: { id: string; space: string; footprint: Point }[] = [];
    for (const entry of Array.isArray(spaces) ? spaces.filter(isObject) : [])
    {
        if (space && entry.id !== space)
        {
            continue;
        }
        for (const building of Array.isArray(entry.buildings) ? entry.buildings.filter(isObject) : [])
        {
            const footprint = Array.isArray(building.footprint_cells) ? building.footprint_cells as number[] : [2, 2];
            if (typeof building.id === 'string')
            {
                out.push({ id: building.id, space: String(entry.id), footprint: [Number(footprint[0] ?? 2), Number(footprint[1] ?? 2)] });
            }
        }
    }
    return out;
}

// A click in a district: a plot for the options' plan building there, its north-west corner at the click.
class PlotTool extends BaseTool
{
    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const files = this.host.files();
        const cell = snapCell(mapToCell(at), 0.5);
        const districts = sketchShapes(files).filter((shape) => shape.word === 'districts' && insideOrOn(cell, shape.cells));
        const district = districts[0];
        if (!district)
        {
            this.host.note('Click inside a district (draw one with the District tool) to place a plot there');
            return true;
        }
        const o = outdoorOptions(this.host);
        const space = String(((sketchOf(files)?.districts as JsonValue[]) ?? []).filter(isObject).find((entry, index) =>
            `/districts/${segment(keysOf(sketchOf(files)!.districts as JsonValue[], 'districts', keyedAt({ file: 'sketch.yml' }, '/districts'))[index])}` === district.address && entry)?.space ?? '');
        const building = o.plotBuilding || planBuildings(files, space)[0]?.id;
        if (!building)
        {
            this.host.note(`The district's space (${space}) has no plan building: add one in the options (+ plan building)`);
            return true;
        }
        const pointer = `${district.address}/plots`;
        void this.host.edit({ label: `plot of ${building}`, ops: [appendToSketch(files, pointer, { building, at: cell, facing: o.plotFacing })] }).then((result) =>
        {
            const key = appendedSketchKey(result, pointer);
            if (key)
            {
                this.host.select(`${pointer}/${segment(key)}`, 'sketch.yml');
            }
        });
        return true;
    }

    move(at: Point): void
    {
        this.cursorAt = cellToMap(snapCell(mapToCell(at), 0.5));
        this.host.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (this.cursorAt)
        {
            const o = outdoorOptions(this.host);
            const building = planBuildings(this.host.files()).find((entry) => entry.id === o.plotBuilding);
            const [front, depth] = building?.footprint ?? [2, 2];
            const size: Point = o.plotFacing === 'n' || o.plotFacing === 's' ? [front, depth] : [depth, front];
            const cell = mapToCell(this.cursorAt);
            strokePath(context, s, [cell, [cell[0] + size[0], cell[1]], [cell[0] + size[0], cell[1] + size[1]], [cell[0], cell[1] + size[1]]].map(cellToMap), true);
            context.strokeStyle = this.host.colour('plan-select');
            context.setLineDash([5, 3]);
            context.lineWidth = 1.5;
            context.stroke();
            context.setLineDash([]);
        }
    }
}

// --- buildings and structures -----------------------------------------------------------------------------------

// Drag a box on the plan: a building on that ground with its first part (the world's ordinary house). With a
// building selected (or one of its parts), a box inside its plot is a new part of it.
class BuildingTool extends CellDrawingTool
{
    protected readonly closed = true;
    protected readonly boxes = true;

    protected describe(): string
    {
        return 'building: drag a box (whole cells; with a building selected, a box inside it is a new part)';
    }

    protected snap(at: Point, event: { shiftKey: boolean; altKey?: boolean }): Point
    {
        const files = this.host.files();
        const building = this.selectedBuilding(files);
        if (building)
        {
            // Inside a building: parts on a grid of a quarter cell (128, a bay).
            return cellToMap(snapCell(mapToCell(at), event.shiftKey ? 1 / 16 : 0.25));
        }
        return super.snap(at, event);
    }

    private selectedBuilding(files: FileTrees | undefined): JsonObject | null
    {
        const selection = this.host.selection();
        const id = selection && !selection.startsWith('/') ? selection.split('/')[0] : null;
        const structures = sketchOf(files)?.structures;
        const found = id && Array.isArray(structures) ? structures.filter(isObject).find((entry) => entry.id === id && entry.kind === 'building') : undefined;
        return found ?? null;
    }

    protected finish(points: Point[], asBox: boolean): void
    {
        const files = this.host.files();
        const cells = mapPointsToCells(points);
        const xs = cells.map((p) => p[0]);
        const ys = cells.map((p) => p[1]);
        const corner: Point = [Math.min(...xs), Math.min(...ys)];
        const size: Point = [Math.max(...xs) - corner[0], Math.max(...ys) - corner[1]];
        if (!asBox)
        {
            this.host.note('Drag a box for a building');
            return;
        }
        const o = this.options();
        const building = this.selectedBuilding(files);
        const at = building && Array.isArray(building.at) ? building.at as Point : null;
        const plot = building && Array.isArray(building.size) ? building.size as Point : [2, 2];
        if (building && at && corner[0] >= at[0] - 1e-6 && corner[1] >= at[1] - 1e-6 && corner[0] + size[0] <= at[0] + plot[0] + 1e-6 && corner[1] + size[1] <= at[1] + plot[1] + 1e-6)
        {
            const id = String(building.id);
            const local = cellToLocal(at, corner);
            const value = { at: local, size: [Math.round(size[0] * CELL), Math.round(size[1] * CELL)], roof: o.roof };
            const parts = Array.isArray(building.parts) ? building.parts : null;
            void this.host.edit({ label: `new part of ${id}`, ops: [sketchPatch(id, parts ? [{ op: 'add', path: '/parts/-', value }] : [{ op: 'add', path: '/parts', value: [{ id: 'main' }, value] }])] })
                .then((result) =>
                {
                    const after = result?.files['sketch.yml']?.tree.structures;
                    const made = Array.isArray(after) ? after.filter(isObject).find((entry) => entry.id === id) : undefined;
                    const list = made && Array.isArray(made.parts) ? made.parts : [];
                    if (list.length > 0)
                    {
                        const key = keysOf(list, 'parts', { field: 'id', prefix: 'part' })[list.length - 1];
                        this.host.select(`${id}/parts/${segment(key)}`, 'sketch.yml');
                    }
                });
            return;
        }
        if (size[0] < 1 || size[1] < 1)
        {
            this.host.note('A building stands on at least one cell each way');
            return;
        }
        const ground: Point = [Math.round(size[0]), Math.round(size[1])];
        const value: JsonObject = { kind: 'building', at: [Math.round(corner[0]), Math.round(corner[1])], size: ground, facing: o.facing,
            parts: [{ id: 'main', roof: o.roof, ...(o.roofPitch > 0 ? { roof_pitch: o.roofPitch } : {}) }], ...(o.kit ? { kit: o.kit } : {}) };
        void this.host.edit({ label: 'new building', ops: [{ op: 'add', to: 'structures', file: 'sketch.yml', value }] }).then((result) =>
        {
            const id = allocatedIn(result, 'sketch.yml');
            if (id)
            {
                this.host.select(id, 'sketch.yml');
            }
        });
    }
}

function mapPointsToCells(points: readonly Point[]): Point[]
{
    return points.map((p) => mapToCell(p).map((value) => Math.round(value * 16) / 16) as Point);
}

// Every other structure (S5_BROWSER_EDITOR.md 3.18 "Generic"): the options' kind placed by its geometry: a click for
// the things that stand at a point, points and Enter for those along a line, an outline for a deck. The inspector
// holds the rest of its words.
class StructureTool extends CellDrawingTool
{
    protected closed: boolean = false;
    protected minimum: number = 2;

    private kind(): string
    {
        return this.options().structureKind;
    }

    private geometry(): 'at' | 'line' | 'outline'
    {
        const kind = this.kind();
        return LINE_KINDS.includes(kind) ? 'line' : OUTLINE_KINDS.includes(kind) ? 'outline' : 'at';
    }

    protected describe(): string
    {
        return `${this.kind()}: ${this.geometry() === 'at' ? 'click where it stands' : `${this.points.length} points · Enter`}`;
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (this.geometry() !== 'at')
        {
            this.closed = this.geometry() === 'outline';
            this.minimum = this.geometry() === 'outline' ? 3 : 2;
            return super.down(at, event);
        }
        if (event.button !== 0)
        {
            return false;
        }
        this.finish([this.snap(at, event)]);
        return true;
    }

    protected finish(points: Point[]): void
    {
        const kind = this.kind();
        const cells = this.cells(points);
        const geometry = this.geometry();
        const value: JsonObject = { kind, ...(geometry === 'at' ? { at: cells[0] } : geometry === 'line' ? { line: cells } : { outline: cells }),
            ...(kind === 'decoration' ? { decoration: this.options().decoration } : {}) };
        void this.host.edit({ label: `new ${kind}`, ops: [{ op: 'add', to: 'structures', file: 'sketch.yml', value }] }).then((result) =>
        {
            const id = allocatedIn(result, 'sketch.yml');
            if (id)
            {
                this.host.select(id, 'sketch.yml');
            }
        });
    }
}

// --- the ground brush -------------------------------------------------------------------------------------------

// The world's first kind of land: what the whole map is laid with when the sketch has no zone.
export const FIRST_KIND = 'grass';

// The zones of the sketch whose places are outlines (zones by line or by steepness are left to the inspector).
function paintedZones(files: FileTrees | undefined): { key: string; material: string; polygon: Point[]; index: number }[]
{
    const ground = sketchOf(files)?.ground;
    if (!Array.isArray(ground))
    {
        return [];
    }
    const keys = keysOf(ground, 'ground', keyedAt({ file: 'sketch.yml' }, '/ground'));
    return ground.map((zone, index) => ({ zone, index })).filter(({ zone }) => isObject(zone) && Array.isArray(zone.polygon) && zone.steeper_than === undefined)
        .map(({ zone, index }) => ({ key: keys[index], material: String((zone as JsonObject).material ?? ''), polygon: (zone as JsonObject).polygon as Point[], index }));
}

// The operations of a ground stroke: the painted cells become `material`, every other outlined kind loses them; each
// kind that changed gets its zones' outlines traced again (polygons replaced, added or removed by key). A sketch
// without zones first gets the world's first kind over the whole map, so nothing but the stroke changes.
export function groundPatch(files: FileTrees | undefined, material: string, painted: Uint8Array, size = 128): { steps: PatchStep[]; kinds: string[] } | { refused: string }
{
    const ground = sketchOf(files)?.ground;
    const zones = paintedZones(files);
    const kinds = new Set(Array.isArray(ground) ? ground.filter(isObject).map((zone) => String(zone.material ?? '')) : []);
    if (!Array.isArray(ground) || ground.length === 0)
    {
        kinds.add(FIRST_KIND);
    }
    kinds.add(material);
    const drawn = [...kinds].filter((kind) => kind !== 'dirt' && kind !== 'soil');
    if (drawn.length > 2)
    {
        return { refused: `A classic outdoor map holds dirt and two more kinds of land: this map has ${drawn.filter((kind) => kind !== material).join(' and ')} already` };
    }
    const masks = new Map<string, Uint8Array>();
    const maskOf = (kind: string) =>
    {
        let mask = masks.get(kind);
        if (!mask)
        {
            mask = new Uint8Array(size * size);
            masks.set(kind, mask);
        }
        return mask;
    };
    const base = !Array.isArray(ground) || ground.length === 0;
    if (base)
    {
        maskOf(FIRST_KIND).fill(1);
    }
    for (const zone of zones)
    {
        rasterise(zone.polygon, maskOf(zone.material), size);
    }
    const before = new Map([...masks].map(([kind, mask]) => [kind, Uint8Array.from(mask)]));
    const target = maskOf(material);
    for (let index = 0; index < painted.length; ++index)
    {
        if (!painted[index])
        {
            continue;
        }
        target[index] = 1;
        for (const [kind, mask] of masks)
        {
            if (kind !== material && !(base && kind === FIRST_KIND))
            {
                mask[index] = 0;
            }
        }
    }
    const changed = [...masks.keys()].filter((kind) => base || !before.has(kind) || before.get(kind)!.some((value, index) => value !== masks.get(kind)![index]));
    if (base)
    {
        const whole = { material: FIRST_KIND, polygon: [[0, 0], [128, 0], [128, 128], [0, 128]] };
        const painted = traceMask(target, size, size).map((polygon) => ({ material, polygon }));
        return { steps: [{ op: 'add', path: '/ground', value: [whole, ...painted] }], kinds: [FIRST_KIND, material] };
    }
    const steps: PatchStep[] = [];
    const removed: string[] = [];
    for (const kind of changed)
    {
        const polygons = traceMask(masks.get(kind)!, size, size);
        const own = zones.filter((zone) => zone.material === kind);
        polygons.forEach((polygon, index) =>
        {
            if (index < own.length)
            {
                if (JSON.stringify(own[index].polygon) !== JSON.stringify(polygon))
                {
                    steps.push({ op: 'replace', path: `/ground/${segment(own[index].key)}/polygon`, value: polygon });
                }
            }
            else
            {
                steps.push({ op: 'add', path: '/ground/-', value: { material: kind, polygon } });
            }
        });
        own.slice(polygons.length).forEach((zone) => removed.push(zone.key));
    }
    for (const key of removed)
    {
        steps.push({ op: 'remove', path: `/ground/${segment(key)}` });
    }
    return { steps, kinds: changed };
}

class GroundTool extends BaseTool
{
    private painted: Uint8Array | null = null;

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        this.painted = new Uint8Array(128 * 128);
        this.paint(at);
        return true;
    }

    private paint(at: Point): void
    {
        paintDisc(this.painted!, 128, mapToCell(at), outdoorOptions(this.host).groundRadius, 1);
        this.host.redraw();
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        void event;
        this.cursorAt = at;
        if (pressed && this.painted)
        {
            this.paint(at);
        }
        this.host.redraw();
    }

    up(): void
    {
        const painted = this.painted;
        this.painted = null;
        if (!painted)
        {
            return;
        }
        const material = outdoorOptions(this.host).groundMaterial;
        const made = groundPatch(this.host.files(), material, painted);
        if ('refused' in made)
        {
            this.host.note(made.refused);
            this.host.redraw();
            return;
        }
        if (made.steps.length > 0)
        {
            void this.host.edit({ label: `ground: ${material}`, ops: [sketchPatch(undefined, made.steps)] });
        }
        this.host.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const o = outdoorOptions(this.host);
        if (this.cursorAt)
        {
            const [x, y] = s(this.cursorAt[0], this.cursorAt[1]);
            context.strokeStyle = this.host.colour('plan-select');
            context.lineWidth = 1.5;
            context.beginPath();
            context.arc(x, y, Math.abs(s(o.groundRadius * CELL, 0)[0] - s(0, 0)[0]), 0, Math.PI * 2);
            context.stroke();
            label(context, s, this.cursorAt, o.groundMaterial, this.host.colour('text'), this.host.colour('surface'));
        }
        if (this.painted)
        {
            context.fillStyle = this.host.colour('plan-select');
            context.globalAlpha = 0.35;
            for (let index = 0; index < this.painted.length; ++index)
            {
                if (this.painted[index])
                {
                    const x0 = index % 128;
                    const y0 = Math.floor(index / 128);
                    const [ax, ay] = s(...cellToMap([x0, y0]));
                    const [bx, by] = s(...cellToMap([x0 + 1, y0 + 1]));
                    context.fillRect(ax, ay, bx - ax, by - ay);
                }
            }
            context.globalAlpha = 1;
        }
    }
}

// --- scatter, areas, actors, points ---------------------------------------------------------------------------

class ScatterTool extends CellDrawingTool
{
    protected closed: boolean = true;
    protected boxes: boolean = true;
    protected minimum: number = 3;

    down(at: Point, event: PointerEvent): boolean
    {
        const line = this.options().scatterLine;
        this.closed = !line;
        this.boxes = !line;
        this.minimum = line ? 2 : 3;
        return super.down(at, event);
    }

    protected describe(): string
    {
        return `scatter of ${this.options().decoration}: ${this.points.length} points · ${this.closed ? 'drag a box, or click corners and Enter' : 'a row: click its points, Enter'}`;
    }

    protected finish(points: Point[]): void
    {
        const o = this.options();
        const cells = this.cells(points);
        // A row stands evenly along its line: no spacing (the core refuses it there).
        const value: JsonObject = { decoration: o.decoration, count: o.scatterCount, ...(o.scatterSpacing > 0 && !o.scatterLine ? { spacing: o.scatterSpacing } : {}),
            ...(o.scatterLine ? { line: cells } : { polygon: cells }) };
        void this.host.edit({ label: `scatter of ${o.decoration}`, ops: [{ op: 'add', to: 'scatter', file: 'sketch.yml', value }] }).then((result) =>
        {
            const id = allocatedIn(result, 'sketch.yml');
            if (id)
            {
                this.host.select(id, 'sketch.yml');
            }
        });
    }
}

// The plan's populations ids (the encounter areas' names).
export function populations(files: FileTrees | undefined): string[]
{
    const spaces = files?.['plan.yml']?.tree.spaces;
    const out: string[] = [];
    for (const space of Array.isArray(spaces) ? spaces.filter(isObject) : [])
    {
        for (const population of Array.isArray(space.population) ? space.population.filter(isObject) : [])
        {
            if (typeof population.id === 'string')
            {
                out.push(population.id);
            }
        }
    }
    return out;
}

// An area: drag a circle (from its middle), or click an outline's corners and Enter. An encounter area names a
// plan population: the options' one, else a new one in the space it lies in (named from the options).
class AreaTool extends CellDrawingTool
{
    protected readonly closed = true;
    private circle: { at: Point; r: number } | null = null;

    protected describe(): string
    {
        return `${this.options().areaKind} area: ${this.points.length} corners · click corners and Enter, or (circle in the options) drag from its middle`;
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (this.options().areaCircle && event.button === 0)
        {
            this.circle = { at: snapCell(mapToCell(at), 0.5), r: 0 };
            return true;
        }
        return super.down(at, event);
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        if (this.circle && pressed)
        {
            const cell = mapToCell(at);
            this.circle.r = Math.max(1, Math.round(Math.hypot(cell[0] - this.circle.at[0], cell[1] - this.circle.at[1])));
            this.host.redraw();
            return;
        }
        super.move(at, event, pressed);
    }

    up(at: Point, event: PointerEvent): void
    {
        if (this.circle)
        {
            const circle = this.circle;
            this.circle = null;
            if (circle.r >= 1)
            {
                this.write({ circle: { at: circle.at, r: circle.r } }, circle.at);
            }
            return;
        }
        super.up(at, event);
    }

    protected finish(points: Point[]): void
    {
        const polygon = this.cells(points);
        this.write({ polygon }, polygon[0]);
    }

    private write(place: JsonObject, at: Point): void
    {
        const o = this.options();
        const files = this.host.files();
        const value = (id: string): Op => ({ op: 'add', to: 'areas', file: 'sketch.yml', value: { id, kind: o.areaKind, ...place,
            ...(o.areaKind === 'encounter' || o.areaKind === 'items' ? { count: o.areaCount } : {}), ...(o.areaKind === 'encounter' ? { slot: o.areaSlot } : {}) } });
        const select = () => this.host.select(this.lastArea(), 'sketch.yml');
        if (o.areaKind !== 'encounter' && o.areaKind !== 'items')
        {
            void this.host.edit({ label: `${o.areaKind} area`, ops: [value(spaceAt(files, at))] }).then(select);
            return;
        }
        const known = populations(files);
        if (o.areaPopulation && known.includes(o.areaPopulation))
        {
            void this.host.edit({ label: `encounter area of ${o.areaPopulation}`, ops: [value(o.areaPopulation)] }).then(select);
            return;
        }
        // A population named by the person (the options' name), numbered when the name is taken.
        const base = `pop:${(o.areaPopulation || 'monsters').replace(/^pop:/, '').replace(/[^a-z0-9_]/g, '_') || 'monsters'}`;
        let id = base;
        for (let n = 2; known.includes(id); ++n)
        {
            id = `${base}_${n}`;
        }
        const space = spaceAt(files, at);
        const spaces = files?.['plan.yml']?.tree.spaces;
        const entry = Array.isArray(spaces) ? spaces.filter(isObject).find((item) => item.id === space) : undefined;
        const add: PatchStep = Array.isArray(entry?.population) ? { op: 'add', path: '/population/-', value: { id, slot: o.areaSlot } }
            : { op: 'add', path: '/population', value: [{ id, slot: o.areaSlot }] };
        const mergeKey = mergeKeyOf('area');
        void this.host.edit({ label: `encounter area of ${id}`, mergeKey, ops: [{ op: 'patch', id: space, file: 'plan.yml', patch: [add] }] }).then((made) =>
        {
            if (made)
            {
                void this.host.edit({ label: `encounter area of ${id}`, mergeKey, ops: [value(id)] }).then(select);
            }
        });
    }

    private lastArea(): string
    {
        const areas = sketchOf(this.host.files())?.areas;
        const last = Array.isArray(areas) ? areas.filter(isObject).at(-1) : undefined;
        return String(last?.id ?? '');
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (this.circle)
        {
            const [x, y] = s(...cellToMap(this.circle.at));
            context.beginPath();
            context.arc(x, y, Math.abs(s(this.circle.r * CELL, 0)[0] - s(0, 0)[0]), 0, Math.PI * 2);
            context.strokeStyle = this.host.colour('plan-select');
            context.setLineDash([6, 4]);
            context.lineWidth = 2;
            context.stroke();
            context.setLineDash([]);
            label(context, s, cellToMap(this.circle.at), `r ${this.circle.r}`, this.host.colour('text'), this.host.colour('surface'));
            return;
        }
        super.draw(context, s);
    }
}

// A click: the options' monster standing there from the start (count, hostile).
class ActorTool extends BaseTool
{
    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const o = outdoorOptions(this.host);
        if (!o.monster.trim())
        {
            this.host.note('Name the monster in the options (or drop one from the Library)');
            return true;
        }
        const value: JsonObject = { monster: o.monster.trim(), at: snapCell(mapToCell(at), 0.5), ...(o.actorCount > 1 ? { count: o.actorCount } : {}),
            ...(o.actorHostile ? { hostile: true } : {}) };
        void this.host.edit({ label: `${o.monster} placed`, ops: [{ op: 'add', to: 'actors', file: 'sketch.yml', value }] }).then((result) =>
        {
            const id = allocatedIn(result, 'sketch.yml');
            if (id)
            {
                this.host.select(id, 'sketch.yml');
            }
        });
        return true;
    }

    move(at: Point): void
    {
        this.cursorAt = cellToMap(snapCell(mapToCell(at), 0.5));
        this.host.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (this.cursorAt)
        {
            handle(context, s, this.cursorAt, this.host.colour('plan-select'), this.host.colour('surface'), 7);
            label(context, s, this.cursorAt, outdoorOptions(this.host).monster || 'a monster', this.host.colour('text'), this.host.colour('surface'));
        }
    }
}

// A click: a point of the plan (an arrival point, a landmark) where it stands, made in the plan with it.
class ArrivalTool extends BaseTool
{
    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const o = outdoorOptions(this.host);
        const files = this.host.files();
        const cell = nearestNode(mapToCell(at));
        const space = spaceAt(files, cell);
        const add: Op = o.pointKind === 'landmark' ? { op: 'add', to: 'landmarks', file: 'plan.yml', value: { space } }
            : { op: 'add', to: 'entrances', file: 'plan.yml', value: { space, kind: 'arrival', facing: o.pointFacing } };
        void withPlanEntry(this.host, `new ${o.pointKind === 'landmark' ? 'landmark' : 'arrival point'}`, add, (id) =>
            ({ op: 'add', to: 'points', file: 'sketch.yml', value: { id, at: cell, ...(o.pointKind === 'landmark' ? {} : { facing: o.pointFacing }) } })).then((made) =>
        {
            if (made?.result)
            {
                this.host.select(made.id, 'sketch.yml');
            }
        });
        return true;
    }

    move(at: Point): void
    {
        this.cursorAt = cellToMap(nearestNode(mapToCell(at)));
        this.host.redraw();
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        if (this.cursorAt)
        {
            handle(context, s, this.cursorAt, this.host.colour('plan-start'), this.host.colour('surface'), 8);
        }
    }
}

// --- Select: the sketch's handles ---------------------------------------------------------------------------------

type OutdoorDrag =
    | { kind: 'vertex'; shape: SketchShape; index: number; now: Point }
    | { kind: 'move'; shape: SketchShape; start: Point; now: Point }
    | { kind: 'corner'; shape: SketchShape; index: number; now: Point };

const snapHalf = (cell: Point): Point => snapCell(cell, 0.5);

// Select outdoors: a click selects a word (the plan picks it); the selection's handles drag its points, a box's
// corners, the whole of it from inside; a double click on an edge adds a point, on a building enters it (its first
// part selected); Alt click on a point takes it out; PgUp and PgDn change a height under the cursor (a height point,
// a spire, a terrace, a ridge, a road's bed at a point).
class OutdoorSelectTool extends BaseTool
{
    private drag: OutdoorDrag | null = null;

    private selected(): SketchShape | null
    {
        const selection = this.host.selection();
        return selection ? sketchShapes(this.host.files()).find((shape) => shape.address === selection) ?? null : null;
    }

    down(at: Point, event: PointerEvent): boolean
    {
        if (event.button !== 0)
        {
            return false;
        }
        const shape = this.selected();
        if (!shape?.edit)
        {
            return false;
        }
        const cell = mapToCell(at);
        const reach = this.reach(9) / CELL;
        if (shape.edit.kind === 'points' || shape.edit.kind === 'box')
        {
            const index = shape.cells.findIndex((p) => Math.hypot(p[0] - cell[0], p[1] - cell[1]) <= reach);
            if (index >= 0)
            {
                if (event.altKey && shape.edit.kind === 'points')
                {
                    const op = removePointOp(shape, index);
                    if (op)
                    {
                        void this.host.edit({ label: `point taken out of ${shape.address}`, ops: [op] });
                    }
                    else
                    {
                        this.host.note('A line keeps two points, an outline three');
                    }
                    return true;
                }
                this.drag = shape.edit.kind === 'box' ? { kind: 'corner', shape, index, now: shape.cells[index] } : { kind: 'vertex', shape, index, now: shape.cells[index] };
                return true;
            }
        }
        const inside = shape.geom === 'point' ? Math.hypot(shape.cells[0][0] - cell[0], shape.cells[0][1] - cell[1]) <= reach * 1.5
            : shape.geom === 'circle' ? Math.hypot(shape.cells[0][0] - cell[0], shape.cells[0][1] - cell[1]) <= (shape.radius ?? 0)
                : shape.geom === 'polygon' || shape.geom === 'box' ? insideOrOn(cell, shape.cells) : false;
        if (inside && shape.address !== '/frame/playable')
        {
            this.drag = { kind: 'move', shape, start: snapHalf(cell), now: snapHalf(cell) };
            return true;
        }
        return false;
    }

    move(at: Point, event: PointerEvent, pressed: boolean): void
    {
        this.cursorAt = at;
        if (!pressed || !this.drag)
        {
            return;
        }
        const cell = mapToCell(at);
        const fine = event.shiftKey || this.drag.shape.edit?.local ? 1 / 16 : 0.5;
        this.drag.now = snapCell(cell, this.drag.shape.layer === 'road' ? 1 : fine);
        if (this.drag.shape.layer === 'road')
        {
            this.drag.now = cellCentre(cell);
        }
        this.host.redraw();
    }

    // The points as the drag leaves them.
    private dragged(drag: OutdoorDrag): Point[]
    {
        const cells = drag.shape.cells.map((p) => [p[0], p[1]] as Point);
        if (drag.kind === 'vertex')
        {
            cells[drag.index] = drag.now;
            return cells;
        }
        if (drag.kind === 'corner')
        {
            const opposite = cells[(drag.index + 2) % 4];
            const x0 = Math.min(opposite[0], drag.now[0]);
            const x1 = Math.max(opposite[0], drag.now[0]);
            const y0 = Math.min(opposite[1], drag.now[1]);
            const y1 = Math.max(opposite[1], drag.now[1]);
            return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]];
        }
        const dx = drag.now[0] - drag.start[0];
        const dy = drag.now[1] - drag.start[1];
        return cells.map((p) => [p[0] + dx, p[1] + dy]);
    }

    up(): void
    {
        const drag = this.drag;
        this.drag = null;
        this.host.redraw();
        if (!drag)
        {
            return;
        }
        const after = this.dragged(drag);
        const edit = drag.shape.edit!;
        const what = drag.shape.address;
        const label = `${drag.kind === 'move' ? 'move' : drag.kind === 'corner' ? 'size' : 'move a point of'} ${what}`;
        if (JSON.stringify(after) === JSON.stringify(drag.shape.cells))
        {
            return;
        }
        let op: Op | null = null;
        switch (edit.kind)
        {
        case 'points':
        {
            const moves = after.map((to, index) => ({ index, from: drag.shape.cells[index], to })).filter((move) => move.to[0] !== move.from[0] || move.to[1] !== move.from[1]);
            op = movePointsOps(drag.shape, moves);
            break;
        }
        case 'point':
        case 'circle':
        {
            const base = edit.kind === 'circle' ? `${edit.base}/at` : edit.base;
            op = sketchPatch(edit.id, [{ op: 'replace', path: base, value: after[0] }]);
            break;
        }
        case 'box':
        {
            const x0 = after[0][0];
            const y0 = after[0][1];
            const size: Point = [after[2][0] - x0, after[2][1] - y0];
            if (what === '/frame/playable')
            {
                op = { op: 'set_value', file: 'sketch.yml', path: 'frame.playable', value: [Math.round(x0), Math.round(y0), Math.round(size[0]), Math.round(size[1])] };
            }
            else if (edit.local && edit.origin)
            {
                const local = cellToLocal(edit.origin, [x0, y0]);
                const localSize = [Math.max(32, Math.round(size[0] * CELL)), Math.max(32, Math.round(size[1] * CELL))];
                op = sketchPatch(edit.id, [{ op: 'add', path: `${edit.base}/at`, value: local }, ...(drag.kind === 'corner' ? [{ op: 'add' as const, path: `${edit.base}/size`, value: localSize }] : [])]);
            }
            else
            {
                const at = [Math.round(x0 * 2) / 2, Math.round(y0 * 2) / 2];
                const ground = [Math.max(1, Math.round(size[0])), Math.max(1, Math.round(size[1]))];
                op = sketchPatch(edit.id, [{ op: 'replace', path: `${edit.base}/at`, value: at }, ...(drag.kind === 'corner' ? [{ op: 'replace' as const, path: `${edit.base}/size`, value: ground }] : [])]);
            }
            break;
        }
        }
        if (op)
        {
            void this.host.edit({ label, mergeKey: `drag ${what}`, ops: [op] });
        }
    }

    doubleClick(at: Point): boolean
    {
        const files = this.host.files();
        const cell = mapToCell(at);
        const shape = this.selected();
        if (shape?.edit?.kind === 'points')
        {
            const reach = this.reach(8) / CELL;
            for (let i = 0; i + 1 < shape.cells.length + (shape.geom === 'polygon' ? 1 : 0); ++i)
            {
                const a = shape.cells[i];
                const b = shape.cells[(i + 1) % shape.cells.length];
                const ex = b[0] - a[0];
                const ey = b[1] - a[1];
                const length = ex * ex + ey * ey;
                const t = length > 0 ? Math.max(0, Math.min(1, ((cell[0] - a[0]) * ex + (cell[1] - a[1]) * ey) / length)) : 0;
                const near: Point = [a[0] + ex * t, a[1] + ey * t];
                if (Math.hypot(near[0] - cell[0], near[1] - cell[1]) <= reach && t > 0.05 && t < 0.95)
                {
                    const op = insertPointOp(shape, i, snapHalf(near));
                    if (op)
                    {
                        void this.host.edit({ label: `new point of ${shape.address}`, ops: [op] });
                    }
                    return true;
                }
            }
        }
        // A building entered: its first part selected.
        const building = shapeAt(sketchShapes(files), cell, this.reach(8) / CELL, enteredBuilding(files, this.host.selection()));
        const id = building?.layer === 'structure' && building.kind === 'building' ? building.address : building?.layer === 'part' ? building.address.split('/')[0] : null;
        if (id)
        {
            const structure = (sketchOf(files)?.structures as JsonValue[] | undefined)?.filter(isObject).find((entry) => entry.id === id);
            const parts = structure && Array.isArray(structure.parts) ? structure.parts : [];
            if (parts.length === 0)
            {
                // The ordinary house has no parts written: its one part is the whole plot, made so it can be edited.
                void this.host.edit({ label: `the parts of ${id}`, ops: [sketchPatch(id, [{ op: 'add', path: '/parts', value: [{ id: 'main' }] }])] })
                    .then((result) => result && this.host.select(`${id}/parts/main`, 'sketch.yml'));
                return true;
            }
            const key = keysOf(parts, 'parts', { field: 'id', prefix: 'part' })[0];
            this.host.select(building?.layer === 'part' ? building.address : `${id}/parts/${segment(key)}`, 'sketch.yml');
            this.host.hint(`inside ${id}: click a part to select it, drag its corners; Building (U) drags a new part; the wall bays in the inspector`);
            return true;
        }
        return false;
    }

    key(event: KeyboardEvent): boolean
    {
        if ((event.code !== 'PageUp' && event.code !== 'PageDown') || !this.cursorAt)
        {
            return false;
        }
        const files = this.host.files();
        const shape = this.selected();
        if (!shape)
        {
            return false;
        }
        const o = outdoorOptions(this.host);
        const step = (event.code === 'PageUp' ? 1 : -1) * o.heightStep;
        const cell = mapToCell(this.cursorAt);
        const object = resolveShape(files, shape);
        if (!object)
        {
            return false;
        }
        const id = shape.edit?.id;
        const base = id ? '' : shape.address;
        const set = (field: string, value: JsonValue, old: JsonValue | undefined) => sketchPatch(id, [
            ...(old !== undefined ? [{ op: 'test' as const, path: `${base}/${field}`, value: old }] : []),
            { op: old !== undefined ? 'replace' as const : 'add' as const, path: `${base}/${field}`, value }]);
        let op: Op | null = null;
        let said = '';
        if (shape.word === 'roads')
        {
            // The bed at the road's point nearest the cursor: written for every point from the built land first.
            const index = nearestIndex(shape.cells, cell);
            const bed = Array.isArray(object.bed) && object.bed.length === shape.cells.length ? (object.bed as number[]).map(Number)
                : shape.cells.map((p) => Math.round((landHeight(this.host, nearestNode(p)) ?? 0) / 32) * 32);
            const next = [...bed];
            next[index] = Math.max(0, next[index] + step);
            op = set('bed', next, object.bed);
            said = `bed at point ${index}: ${next[index]}`;
        }
        else if (shape.word === 'points' && shape.layer === 'land')
        {
            const value = Number(object.h ?? 0) + step;
            op = set('h', value, object.h);
            said = `height ${value}`;
        }
        else if (['spires', 'terraces', 'ridges'].includes(shape.word) && typeof object.height === 'number')
        {
            const value = Math.max(0, Math.min(8160, object.height + step));
            op = set('height', value, object.height);
            said = `height ${value}`;
        }
        else if (shape.word === 'cuts' && typeof object.floor === 'number')
        {
            const value = Math.max(0, object.floor + step);
            op = set('floor', value, object.floor);
            said = `floor ${value}`;
        }
        if (!op)
        {
            return false;
        }
        void this.host.edit({ label: `${shape.address}: ${said}`, mergeKey: `height ${shape.address}`, ops: [op] });
        this.host.hint(`${shape.address}: ${said}`);
        return true;
    }

    draw(context: CanvasRenderingContext2D, s: ToScreen): void
    {
        const shape = this.drag?.shape ?? this.selected();
        if (!shape?.edit)
        {
            return;
        }
        const cells = this.drag ? this.dragged(this.drag) : shape.cells;
        const accent = this.host.colour('plan-select');
        const surface = this.host.colour('surface');
        if (this.drag)
        {
            strokePath(context, s, cells.map(cellToMap), shape.geom !== 'polyline' && shape.geom !== 'point');
            context.strokeStyle = accent;
            context.lineWidth = 2;
            context.setLineDash([6, 4]);
            context.stroke();
            context.setLineDash([]);
            const now = this.drag.now;
            label(context, s, cellToMap(now), `${now[0]}, ${now[1]}`, this.host.colour('text'), surface);
        }
        if (shape.edit.kind === 'points' || shape.edit.kind === 'box' || shape.edit.kind === 'point')
        {
            cells.forEach((p) => handle(context, s, cellToMap(p), accent, surface));
        }
    }

    cursor(): string
    {
        return this.drag ? 'grabbing' : 'default';
    }
}

// The object a shape's address names (a top-level object, or the word in the file).
export function resolveShape(files: FileTrees | undefined, shape: SketchShape): JsonObject | null
{
    const sketch = sketchOf(files);
    if (!sketch)
    {
        return null;
    }
    if (!shape.address.startsWith('/'))
    {
        const [id, ...rest] = shape.address.split('/');
        for (const list of ['structures', 'areas', 'scatter', 'actors', 'points', 'events'])
        {
            const found = Array.isArray(sketch[list]) ? (sketch[list] as JsonValue[]).filter(isObject).find((entry) => entry.id === id) : undefined;
            if (found)
            {
                if (rest.length === 2 && Array.isArray(found[rest[0]]))
                {
                    const items = found[rest[0]] as JsonValue[];
                    const index = keysOf(items, rest[0], keyedAt({ file: 'sketch.yml' }, `/${list}/*/${rest[0]}`)).indexOf(rest[1]);
                    return isObject(items[index]) ? items[index] as JsonObject : null;
                }
                return found;
            }
        }
        return null;
    }
    let node: JsonValue | undefined = sketch;
    let place = '';
    for (const part of shape.address.split('/').slice(1))
    {
        if (Array.isArray(node))
        {
            const keys = keysOf(node, place.slice(place.lastIndexOf('/') + 1), keyedAt({ file: 'sketch.yml' }, place));
            node = node[keys.indexOf(part)];
            place += '/*';
        }
        else
        {
            node = isObject(node) ? node[part] : undefined;
            place += `/${part}`;
        }
    }
    return isObject(node) ? node : null;
}

function nearestIndex(cells: readonly Point[], at: Point): number
{
    let best = 0;
    cells.forEach((p, index) =>
    {
        if (Math.hypot(p[0] - at[0], p[1] - at[1]) < Math.hypot(cells[best][0] - at[0], cells[best][1] - at[1]))
        {
            best = index;
        }
    });
    return best;
}

// --- the tools by name ----------------------------------------------------------------------------------------------

export function makeOutdoorTool(host: ToolHost, name: ToolName): PlanTool | null
{
    switch (name)
    {
    case 'select':
        return new OutdoorSelectTool(host);
    case 'spots':
        return new SpotsTool(host);
    case 'sculpt':
        return new SculptTool(host);
    case 'patch':
        return new LandWordTool(host, 'patches');
    case 'hpoint':
        return new LandPointTool(host, 'points');
    case 'spire':
        return new LandPointTool(host, 'spires');
    case 'ridge':
        return new LandWordTool(host, 'ridges');
    case 'cliff':
        return new LandWordTool(host, 'cliffs');
    case 'terrace':
        return new LandWordTool(host, 'terraces');
    case 'cut':
        return new LandWordTool(host, 'cuts');
    case 'rough':
        return new LandWordTool(host, 'rough');
    case 'peaks':
        return new LandWordTool(host, 'peaks');
    case 'frame':
        return new FrameTool(host);
    case 'rim':
        return new RimTool(host);
    case 'water':
        return new WaterTool(host, false);
    case 'river':
        return new WaterTool(host, true);
    case 'road':
        return new RoadTool(host);
    case 'district':
        return new DistrictTool(host);
    case 'plot':
        return new PlotTool(host);
    case 'building':
        return new BuildingTool(host);
    case 'structure':
        return new StructureTool(host);
    case 'ground':
        return new GroundTool(host);
    case 'scatter':
        return new ScatterTool(host);
    case 'area':
        return new AreaTool(host);
    case 'actor':
        return new ActorTool(host);
    case 'arrival':
        return new ArrivalTool(host);
    default:
        return null;
    }
}

// The building of a part (its plot's corner and size in cells) and the part's box in map units on its plot, for the
// wall bay strip.
export function partBox(files: FileTrees | undefined, address: string): { building: JsonObject; part: JsonObject; key: string; size: Point } | null
{
    const [id, list, key] = address.split('/');
    const structure = (sketchOf(files)?.structures as JsonValue[] | undefined)?.filter(isObject).find((entry) => entry.id === id);
    if (!structure || structure.kind !== 'building')
    {
        return null;
    }
    const parts = Array.isArray(structure.parts) ? structure.parts : [];
    const keys = keysOf(parts, 'parts', { field: 'id', prefix: 'part' });
    const partKey = list === 'parts' && key ? key : keys[0];
    const part = parts[keys.indexOf(partKey)];
    if (!isObject(part))
    {
        return null;
    }
    const plot: Point = Array.isArray(structure.size) ? [Number(structure.size[0]), Number(structure.size[1])] : [2, 2];
    const shape = partCells(part, [0, 0], plot);
    const xs = shape.cells.map((p) => p[0]);
    const ys = shape.cells.map((p) => p[1]);
    const size: Point = shape.geom === 'circle' ? [(shape.radius ?? 0) * 2 * CELL, (shape.radius ?? 0) * 2 * CELL]
        : [Math.round((Math.max(...xs) - Math.min(...xs)) * CELL), Math.round((Math.max(...ys) - Math.min(...ys)) * CELL)];
    return { building: structure, part, key: partKey, size };
}


// --- the Library dropped outdoors -------------------------------------------------------------------------------

// What a Library asset dropped on an outdoor plan or 3D view does (at: the map point): a decoration on a scatter
// becomes its decoration, elsewhere a decoration structure stands there (and the Scatter tool's decoration is set); a
// monster stands there as an actor; a texture on a building's part becomes its walls' texture role. Null: nothing
// to do there (with the reason).
export function outdoorDrop(files: FileTrees | undefined, kind: string, name: string, at: Point, selection: string | null):
    { ops: Op[]; label: string; options?: Partial<OutdoorOptions> } | { note: string }
{
    const cell = snapCell(mapToCell(at), 0.5);
    const under = shapeAt(sketchShapes(files), cell, 0.75, enteredBuilding(files, selection));
    if (kind === 'decoration')
    {
        if (under?.layer === 'scatter')
        {
            return { ops: [sketchPatch(under.address, [{ op: 'add', path: '/decoration', value: name }])], label: `${under.address} of ${name}`, options: { decoration: name } };
        }
        return { ops: [{ op: 'add', to: 'structures', file: 'sketch.yml', value: { kind: 'decoration', decoration: name, at: cell } }], label: `${name} placed`, options: { decoration: name } };
    }
    if (kind === 'monster')
    {
        return { ops: [{ op: 'add', to: 'actors', file: 'sketch.yml', value: { monster: name, at: cell } }], label: `${name} placed`, options: { monster: name } };
    }
    if (kind === 'texture' && under?.layer === 'part')
    {
        const [id, , key] = under.address.split('/');
        return { ops: [sketchPatch(id, [{ op: 'add', path: `/parts/${key}/textures`, value: { wall: name } }])], label: `${name} on the walls of ${under.address}` };
    }
    return { note: kind === 'texture' ? 'Drop a texture on a building\'s part (double-click the building first): it becomes its walls\' texture' : `A ${kind} is not placed outdoors` };
}
