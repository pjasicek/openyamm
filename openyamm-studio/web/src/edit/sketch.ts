// The sketch's words as the plan draws and picks them (S5_BROWSER_EDITOR.md 3.18, the Outdoor table): every word with a
// place (a point, a line, an outline, a box, a circle) read from sketch.yml as the client has it, with its address
// (a top-level id, a building's part below it, or a word without an id by its pointer in the file) and where its
// geometry lies, so the Select tool's handles can patch it. All in cells.
import type { FileTrees, JsonObject, JsonValue, Op, PatchStep } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from './ops.ts';
import { isObject, keyedAt, keysOf, placeOfPointer, segment, walkPointer } from './keys.ts';
import { CELL, MAP_CELLS, insideOrOn } from './cells.ts';

export type SketchLayer = 'frame' | 'land' | 'patch' | 'water' | 'road' | 'district' | 'ground' | 'structure' | 'part' | 'scatter' | 'area' | 'actor'
    | 'point';

export type SketchGeom = 'point' | 'polyline' | 'polygon' | 'box' | 'circle';

export interface SketchShape
{
    // What the plan selects: a top-level id (thing:hall), a building's part (thing:hall/parts/main) or a word without
    // an id by its pointer in sketch.yml (/heights/ridges/ridge2).
    address: string;
    layer: SketchLayer;
    // The list the word is in (ridges, bodies, structures) and, for a structure, its kind.
    word: string;
    kind?: string;
    geom: SketchGeom;
    // The geometry in cells: a point, a line's or an outline's points, a box's four corners (north-west first,
    // clockwise on the screen), a circle's middle.
    cells: Point[];
    radius?: number;
    label?: string;
    // Where the geometry is written: the id the patch names (none: a pointer in the file) and the pointer of the
    // list of points (`points`), of the point (`point`), of the box's `at` and `size` (`box`, in cells; `local` for a
    // building's part in map units from its plot's corner) or of a circle's object (`circle`).
    edit?: { id?: string; base: string; kind: 'points' | 'point' | 'box' | 'circle'; closed?: boolean; origin?: Point; local?: boolean };
    ghost?: boolean;
}

const pts = (value: JsonValue | undefined): Point[] => (Array.isArray(value)
    ? value.filter((p): p is number[] => Array.isArray(p) && typeof p[0] === 'number' && typeof p[1] === 'number').map((p) => [p[0], p[1]] as Point) : []);
const pt = (value: JsonValue | undefined): Point | null => pts(Array.isArray(value) ? [value] : undefined)[0] ?? null;

export function sketchOf(files: FileTrees | undefined): JsonObject | undefined
{
    return files?.['sketch.yml']?.tree;
}

// The keyed items of a list at a place of sketch.yml with their keys.
function keyed(list: JsonValue | undefined, place: string): { item: JsonObject; key: string }[]
{
    if (!Array.isArray(list))
    {
        return [];
    }
    const name = place.slice(place.lastIndexOf('/') + 1);
    const keys = keysOf(list, name, keyedAt({ file: 'sketch.yml' }, place));
    return list.map((item, index) => ({ item, key: keys[index] })).filter((entry): entry is { item: JsonObject; key: string } => isObject(entry.item));
}

function boxCorners(at: Point, size: Point): Point[]
{
    return [at, [at[0] + size[0], at[1]], [at[0] + size[0], at[1] + size[1]], [at[0], at[1] + size[1]]];
}

// A building part's box in cells (box parts; an outline part's points; a round part's corners), from its plot's
// corner `at` (cells) and the plot's size (cells): a part without `at` and `size` is the whole plot.
export function partCells(part: JsonObject, at: Point, plot: Point): { geom: SketchGeom; cells: Point[]; radius?: number }
{
    const shape = typeof part.shape === 'string' ? part.shape : 'box';
    const local = (p: Point): Point => [at[0] + p[0] / CELL, at[1] + p[1] / CELL];
    if (shape === 'outline')
    {
        return { geom: 'polygon', cells: pts(part.outline).map(local) };
    }
    if (shape === 'round')
    {
        const middle = pt(part.at) ? local(pt(part.at)!) : [at[0] + plot[0] / 2, at[1] + plot[1] / 2] as Point;
        return { geom: 'circle', cells: [middle], radius: Number(part.radius ?? 128) / CELL };
    }
    const corner = pt(part.at) ?? [0, 0];
    const size = pt(part.size) ?? [plot[0] * CELL, plot[1] * CELL];
    return { geom: 'box', cells: boxCorners(local(corner), [size[0] / CELL, size[1] / CELL]) };
}

// The structures' kinds whose place is a line, an outline (in cells), or a box of `size` in cells (buildings).
export const LINE_KINDS = ['wall', 'fence', 'waterfall', 'barrier', 'bridge', 'stairs', 'arch', 'walkway', 'arcade'];
export const OUTLINE_KINDS = ['deck'];

// Every word of the sketch with a place, in drawing order (land first, people last).
export function sketchShapes(files: FileTrees | undefined): SketchShape[]
{
    const sketch = sketchOf(files);
    if (!sketch)
    {
        return [];
    }
    const out: SketchShape[] = [];
    const frame = isObject(sketch.frame) ? sketch.frame : undefined;
    const playable = Array.isArray(frame?.playable) ? frame!.playable as number[] : null;
    if (playable && playable.length === 4)
    {
        out.push({ address: '/frame/playable', layer: 'frame', word: 'playable', geom: 'box', cells: boxCorners([playable[0], playable[1]], [playable[2], playable[3]]),
            label: 'playable', edit: { base: '/frame/playable', kind: 'box' } });
    }
    const heights = isObject(sketch.heights) ? sketch.heights : {};
    const list = (name: string, layer: SketchLayer, field: 'line' | 'polygon' | 'at', label: (item: JsonObject) => string, base = `/heights/${name}`,
        from: JsonValue | undefined = heights[name]) =>
    {
        for (const { item, key } of keyed(from, base))
        {
            const address = `${base}/${segment(key)}`;
            if (field === 'at')
            {
                const at = pt(item.at);
                if (at)
                {
                    out.push({ address, layer, word: name, geom: 'point', cells: [at], label: label(item), edit: { base: `${address}/at`, kind: 'point' } });
                }
                continue;
            }
            const points = pts(item[field]);
            if (points.length >= 2)
            {
                const closed = field === 'polygon' || item.closed === true;
                out.push({ address, layer, word: name, geom: closed ? 'polygon' : 'polyline', cells: points, label: label(item),
                    edit: { base: `${address}/${field}`, kind: 'points', closed } });
            }
        }
    };
    list('patches', 'patch', 'polygon', () => 'sculpt patch');
    list('terraces', 'land', 'polygon', (item) => `terrace ${String(item.height ?? '')}`);
    list('cuts', 'land', 'polygon', (item) => `cut ${String(item.floor ?? '')}`);
    list('rough', 'land', 'polygon', (item) => `rough ±${String(item.amount ?? '')}`);
    list('peaks', 'land', 'polygon', (item) => `${String(item.count ?? '')} peaks`);
    list('smooth', 'land', 'polygon', () => 'smoothed');
    list('bands', 'land', 'polygon', (item) => `band ${String(item.band ?? '')}`);
    list('ridges', 'land', 'line', (item) => `ridge ${Array.isArray(item.height) ? item.height.join('→') : String(item.height ?? '')}`);
    list('cliffs', 'land', 'line', (item) => `cliff ${String(item.drop ?? '')}`);
    list('points', 'land', 'at', (item) => `${String(item.h ?? '')}`);
    list('spires', 'land', 'at', (item) => `spire ${String(item.height ?? '')}`);
    for (const { item, key } of keyed(heights.strokes, '/heights/strokes'))
    {
        const at = pt(item.at);
        const rows = Array.isArray(item.rows) ? item.rows : [];
        const width = Math.max(0, ...rows.map((row) => (Array.isArray(row) ? row.length : 0)));
        if (at && rows.length > 0 && width > 0)
        {
            // A stroke block covers its nodes' half cells.
            out.push({ address: `/heights/strokes/${segment(key)}`, layer: 'patch', word: 'strokes', geom: 'box',
                cells: boxCorners([at[0] - 0.5, at[1] - 0.5], [width, rows.length]), label: 'stroke' });
        }
    }
    for (const { item, key } of keyed(frame?.rim, '/frame/rim'))
    {
        const span = Array.isArray(item.span) ? item.span as number[] : [0, MAP_CELLS];
        const side = String(item.side ?? 'north');
        const [a, b] = [Number(span[0] ?? 0), Number(span[1] ?? MAP_CELLS)];
        const end = MAP_CELLS;
        const line: Point[] = side === 'north' ? [[a, 0], [b, 0]] : side === 'south' ? [[a, end], [b, end]] : side === 'west' ? [[0, a], [0, b]] : [[end, a], [end, b]];
        out.push({ address: `/frame/rim/${segment(key)}`, layer: 'frame', word: 'rim', geom: 'polyline', cells: line, label: `rim ${String(item.form ?? 'level')}` });
    }
    const water = isObject(sketch.water) ? sketch.water : {};
    for (const { item, key } of keyed(water.bodies, '/water/bodies'))
    {
        const polygon = pts(item.polygon);
        if (polygon.length >= 3)
        {
            const address = `/water/bodies/${segment(key)}`;
            out.push({ address, layer: 'water', word: 'bodies', geom: 'polygon', cells: polygon, label: `${String(item.kind ?? 'water')} ${String(item.level ?? '')}`,
                edit: { base: `${address}/polygon`, kind: 'points', closed: true } });
        }
    }
    for (const { item, key } of keyed(water.rivers, '/water/rivers'))
    {
        const line = pts(item.line);
        if (line.length >= 2)
        {
            const address = `/water/rivers/${segment(key)}`;
            out.push({ address, layer: 'water', word: 'rivers', geom: 'polyline', cells: line, label: 'river', edit: { base: `${address}/line`, kind: 'points' } });
        }
    }
    for (const { item, key } of keyed(sketch.ground, '/ground'))
    {
        const polygon = pts(item.polygon);
        const line = pts(item.line);
        const address = `/ground/${segment(key)}`;
        if (polygon.length >= 3)
        {
            out.push({ address, layer: 'ground', word: 'ground', kind: String(item.material ?? ''), geom: 'polygon', cells: polygon, label: String(item.material ?? ''),
                edit: { base: `${address}/polygon`, kind: 'points', closed: true } });
        }
        else if (line.length >= 2)
        {
            out.push({ address, layer: 'ground', word: 'ground', kind: String(item.material ?? ''), geom: 'polyline', cells: line, label: String(item.material ?? ''),
                edit: { base: `${address}/line`, kind: 'points' } });
        }
    }
    for (const { item, key } of keyed(sketch.districts, '/districts'))
    {
        const polygon = pts(item.polygon);
        const address = `/districts/${segment(key)}`;
        if (polygon.length >= 3)
        {
            out.push({ address, layer: 'district', word: 'districts', geom: 'polygon', cells: polygon, label: String(item.space ?? 'district'),
                edit: { base: `${address}/polygon`, kind: 'points', closed: true } });
        }
        for (const { item: plot, key: plotKey } of keyed(item.plots, '/districts/*/plots'))
        {
            const at = pt(plot.at);
            if (at)
            {
                const plotAddress = `${address}/plots/${segment(plotKey)}`;
                out.push({ address: plotAddress, layer: 'district', word: 'plots', geom: 'point', cells: [at], label: `${String(plot.building ?? 'plot')} ${String(plot.facing ?? '')}`,
                    edit: { base: `${plotAddress}/at`, kind: 'point' } });
            }
        }
    }
    for (const { item, key } of keyed(sketch.roads, '/roads'))
    {
        const line = pts(item.line);
        if (line.length >= 2)
        {
            const address = `/roads/${segment(key)}`;
            out.push({ address, layer: 'road', word: 'roads', geom: 'polyline', cells: line, label: `${String(item.width ?? 'road')}`,
                edit: { base: `${address}/line`, kind: 'points' } });
        }
    }
    const idList = (name: string) => (Array.isArray(sketch[name]) ? (sketch[name] as JsonValue[]).filter(isObject) : []);
    for (const area of idList('areas'))
    {
        const id = String(area.id ?? '');
        const polygon = pts(area.polygon);
        const circle = isObject(area.circle) ? area.circle : null;
        if (polygon.length >= 3)
        {
            out.push({ address: id, layer: 'area', word: 'areas', kind: String(area.kind ?? 'encounter'), geom: 'polygon', cells: polygon, label: id,
                edit: { id, base: '/polygon', kind: 'points', closed: true } });
        }
        else if (circle && pt(circle.at))
        {
            out.push({ address: id, layer: 'area', word: 'areas', kind: String(area.kind ?? 'encounter'), geom: 'circle', cells: [pt(circle.at)!], radius: Number(circle.r ?? 1),
                label: id, edit: { id, base: '/circle', kind: 'circle' } });
        }
    }
    for (const scatter of idList('scatter'))
    {
        const id = String(scatter.id ?? '');
        const polygon = pts(scatter.polygon);
        const line = pts(scatter.line);
        const label = `${String(scatter.decoration ?? 'mixed')} ×${String(scatter.count ?? '')}`;
        if (polygon.length >= 3)
        {
            out.push({ address: id, layer: 'scatter', word: 'scatter', geom: 'polygon', cells: polygon, label, edit: { id, base: '/polygon', kind: 'points', closed: true } });
        }
        else if (line.length >= 2)
        {
            out.push({ address: id, layer: 'scatter', word: 'scatter', geom: scatter.closed === true ? 'polygon' : 'polyline', cells: line, label,
                edit: { id, base: '/line', kind: 'points', closed: scatter.closed === true } });
        }
    }
    for (const structure of idList('structures'))
    {
        const id = String(structure.id ?? '');
        const kind = String(structure.kind ?? '');
        const at = pt(structure.at);
        const size = pt(structure.size);
        const line = pts(structure.line);
        const outline = pts(structure.outline);
        const ghost = structure.__ghost === true;
        if (kind === 'building' && at)
        {
            const plot: Point = size ?? [2, 2];
            out.push({ address: id, layer: 'structure', word: 'structures', kind, geom: 'box', cells: boxCorners(at, plot), label: String(structure.title ?? id), ghost,
                edit: { id, base: '', kind: 'box' } });
            if (Array.isArray(structure.parts))
            {
                for (const { item: part, key } of keyed(structure.parts, '/structures/*/parts'))
                {
                    const shape = partCells(part, at, plot);
                    const address = `${id}/parts/${segment(key)}`;
                    out.push({ address, layer: 'part', word: 'parts', kind: String(part.shape ?? 'box'), geom: shape.geom, cells: shape.cells, ...(shape.radius ? { radius: shape.radius } : {}),
                        label: `${key}${part.roof ? ` · ${String(part.roof)}` : ''}`,
                        ...(shape.geom === 'box' ? { edit: { id, base: `/parts/${segment(key)}`, kind: 'box' as const, origin: at, local: true } } : {}) });
                }
            }
            continue;
        }
        if (LINE_KINDS.includes(kind) && line.length >= 2)
        {
            out.push({ address: id, layer: 'structure', word: 'structures', kind, geom: structure.closed === true ? 'polygon' : 'polyline', cells: line, label: `${kind} ${id}`, ghost,
                edit: { id, base: '/line', kind: 'points', closed: structure.closed === true } });
            continue;
        }
        if (OUTLINE_KINDS.includes(kind) && outline.length >= 3)
        {
            out.push({ address: id, layer: 'structure', word: 'structures', kind, geom: 'polygon', cells: outline, label: `${kind} ${id}`, ghost,
                edit: { id, base: '/outline', kind: 'points', closed: true } });
            continue;
        }
        if (at)
        {
            out.push({ address: id, layer: 'structure', word: 'structures', kind, geom: 'point', cells: [at], label: `${kind} ${id}`, ghost, edit: { id, base: '/at', kind: 'point' } });
        }
    }
    for (const actor of idList('actors'))
    {
        const at = pt(actor.at);
        if (at)
        {
            const id = String(actor.id ?? '');
            out.push({ address: id, layer: 'actor', word: 'actors', geom: 'point', cells: [at], label: `${String(actor.monster ?? '')}${Number(actor.count ?? 1) > 1 ? ` ×${String(actor.count)}` : ''}`,
                ghost: actor.__ghost === true, edit: { id, base: '/at', kind: 'point' } });
        }
    }
    for (const point of idList('points'))
    {
        const at = pt(point.at);
        if (at)
        {
            const id = String(point.id ?? '');
            out.push({ address: id, layer: 'point', word: 'points', geom: 'point', cells: [at], label: id, edit: { id, base: '/at', kind: 'point' } });
        }
    }
    return out;
}

// What lies under a cell point: points and plots first, then lines, then outlines and boxes (the smallest first).
// `reach` is in cells. With a building entered (`building`: its id), its parts come first.
export function shapeAt(shapes: readonly SketchShape[], at: Point, reach: number, building: string | null = null, layers?: ReadonlySet<SketchLayer>): SketchShape | null
{
    const usable = shapes.filter((shape) => (!layers || layers.has(shape.layer)) && (shape.layer !== 'part' || (building && shape.address.startsWith(`${building}/`))));
    let best: { shape: SketchShape; d: number } | null = null;
    for (const shape of usable)
    {
        if (shape.geom !== 'point')
        {
            continue;
        }
        const d = Math.hypot(shape.cells[0][0] - at[0], shape.cells[0][1] - at[1]);
        if (d <= reach && (!best || d < best.d))
        {
            best = { shape, d };
        }
    }
    if (best)
    {
        return best.shape;
    }
    if (building)
    {
        const part = smallestContaining(usable.filter((shape) => shape.layer === 'part'), at);
        if (part)
        {
            return part;
        }
    }
    for (const shape of usable)
    {
        if (shape.geom === 'polyline')
        {
            for (let i = 0; i + 1 < shape.cells.length; ++i)
            {
                const d = segmentDistance(at, shape.cells[i], shape.cells[i + 1]);
                if (d <= reach && (!best || d < best.d))
                {
                    best = { shape, d };
                }
            }
        }
    }
    if (best)
    {
        return best.shape;
    }
    return smallestContaining(usable.filter((shape) => shape.layer !== 'part' && shape.layer !== 'ground' && shape.address !== '/frame/playable'), at)
        ?? smallestContaining(usable.filter((shape) => shape.layer === 'ground'), at);
}

function smallestContaining(shapes: readonly SketchShape[], at: Point): SketchShape | null
{
    let best: { shape: SketchShape; area: number } | null = null;
    for (const shape of shapes)
    {
        let inside = false;
        let size = 0;
        if (shape.geom === 'circle')
        {
            inside = Math.hypot(shape.cells[0][0] - at[0], shape.cells[0][1] - at[1]) <= (shape.radius ?? 0);
            size = Math.PI * (shape.radius ?? 0) ** 2;
        }
        else if (shape.geom === 'polygon' || shape.geom === 'box')
        {
            inside = insideOrOn(at, shape.cells);
            size = Math.abs(polygonArea(shape.cells));
        }
        if (inside && (!best || size < best.area))
        {
            best = { shape, area: size };
        }
    }
    return best?.shape ?? null;
}

export function polygonArea(points: readonly Point[]): number
{
    let sum = 0;
    for (let i = 0; i < points.length; ++i)
    {
        const a = points[i];
        const b = points[(i + 1) % points.length];
        sum += a[0] * b[1] - b[0] * a[1];
    }
    return sum / 2;
}

export function segmentDistance(p: readonly number[], a: readonly number[], b: readonly number[]): number
{
    const ex = b[0] - a[0];
    const ey = b[1] - a[1];
    const length = ex * ex + ey * ey;
    const t = length > 0 ? Math.max(0, Math.min(1, ((p[0] - a[0]) * ex + (p[1] - a[1]) * ey) / length)) : 0;
    return Math.hypot(a[0] + ex * t - p[0], a[1] + ey * t - p[1]);
}

// --- operations of the sketch's words ---------------------------------------------------------------------------

// A patch of sketch.yml: of a top-level object by its id, or of the file by pointers.
export function sketchPatch(id: string | undefined, steps: PatchStep[]): Op
{
    return id ? { op: 'patch', id, file: 'sketch.yml', patch: steps } : { op: 'patch', file: 'sketch.yml', patch: steps };
}

// An item appended to a list of sketch.yml at a pointer (/heights/ridges, /water/bodies): `/-` when the list is
// there, else the list made with it, and the object above it made when missing (`heights`, `water`).
export function appendToSketch(files: FileTrees | undefined, pointer: string, value: JsonValue): Op
{
    const sketch = sketchOf(files) ?? {};
    const parts = pointer.split('/').slice(1);
    let node: JsonValue | undefined = sketch;
    for (let i = 0; i < parts.length; ++i)
    {
        // A list's item by its key or id (/districts/district1/plots), else an object's property.
        const next: JsonValue | undefined = Array.isArray(node) ? walkPointer(node, `/${parts[i]}`, { file: 'sketch.yml', base: placeOfPointer(`/${parts.slice(0, i).join('/')}`, { file: 'sketch.yml' }) }).node
            : isObject(node) ? node[parts[i]] : undefined;
        if (next === undefined && Array.isArray(node))
        {
            throw new Error(`no ${parts[i]} in ${parts.slice(0, i).join('/')}`);
        }
        if (next === undefined)
        {
            // Made from here down: the first missing step carries the rest.
            let made: JsonValue = [value];
            for (let j = parts.length - 1; j > i; --j)
            {
                made = { [parts[j]]: made };
            }
            return sketchPatch(undefined, [{ op: 'add', path: `/${parts.slice(0, i + 1).join('/')}`, value: made }]);
        }
        node = next;
    }
    return sketchPatch(undefined, [{ op: 'add', path: `${pointer}/-`, value }]);
}

// Points of a shape moved: each with a test of the old point (the points of a line or an outline are positions).
export function movePointsOps(shape: SketchShape, moves: { index: number; from: Point; to: Point }[]): Op | null
{
    if (!shape.edit || shape.edit.kind !== 'points')
    {
        return null;
    }
    const steps: PatchStep[] = [];
    for (const move of moves)
    {
        steps.push({ op: 'test', path: `${shape.edit.base}/${move.index}`, value: move.from }, { op: 'replace', path: `${shape.edit.base}/${move.index}`, value: move.to });
    }
    return sketchPatch(shape.edit.id, steps);
}

// A point inserted after `index`, or the point at `index` taken out (a line keeps two, an outline three).
export function insertPointOp(shape: SketchShape, index: number, point: Point): Op | null
{
    if (!shape.edit || shape.edit.kind !== 'points')
    {
        return null;
    }
    return sketchPatch(shape.edit.id, [{ op: 'test', path: `${shape.edit.base}/${index}`, value: shape.cells[index] },
        { op: 'add', path: `${shape.edit.base}/${index + 1}`, value: point }]);
}

export function removePointOp(shape: SketchShape, index: number): Op | null
{
    if (!shape.edit || shape.edit.kind !== 'points' || shape.cells.length <= (shape.geom === 'polygon' ? 3 : 2))
    {
        return null;
    }
    return sketchPatch(shape.edit.id, [{ op: 'test', path: `${shape.edit.base}/${index}`, value: shape.cells[index] },
        { op: 'remove', path: `${shape.edit.base}/${index}` }]);
}
