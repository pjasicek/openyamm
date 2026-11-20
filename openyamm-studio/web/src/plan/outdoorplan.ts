// Author mode's drawing of an outdoor project's sketch over the land (S5_BROWSER_EDITOR.md 3.18): every word with a
// place, by layer, from the client's own copy of sketch.yml, so a gesture shows at once; the selection and hover
// marked; a building's parts drawn when one of them is selected (the building entered). Picking maps a map point
// back to the word's address.
import type { FileTrees } from '../../../schema/rpc/generated/rpc.ts';
import type { Point } from '../edit/ops.ts';
import { cellToMap, mapToCell } from '../edit/cells.ts';
import { shapeAt, sketchShapes } from '../edit/sketch.ts';
import type { SketchLayer, SketchShape } from '../edit/sketch.ts';

export type ToScreen = (x: number, y: number) => [number, number];

// The building entered: the id of the selected building's part's building (thing:hall/parts/main -> thing:hall),
// or of the building itself.
export function enteredBuilding(files: FileTrees | undefined, selection: string | null): string | null
{
    if (!selection || selection.startsWith('/'))
    {
        return null;
    }
    const slash = selection.indexOf('/');
    const id = slash < 0 ? selection : selection.slice(0, slash);
    const structures = files?.['sketch.yml']?.tree.structures;
    const found = Array.isArray(structures) ? structures.find((item) => typeof item === 'object' && item !== null && !Array.isArray(item) && item.id === id) : undefined;
    return found && typeof found === 'object' && !Array.isArray(found) && found.kind === 'building' && slash > 0 ? id : null;
}

const LAYER_COLOURS: Record<SketchLayer, string> = {
    frame: 'plan-room-edge', land: 'geom', patch: 'warn', water: 'plan-water', road: 'plan-link', district: 'plan-opening', ground: 'plan-land-high',
    structure: 'plan-model', part: 'plan-model', scatter: 'good', area: 'plan-door', actor: 'plan-thing', point: 'plan-start',
};

// The colours of the tokens, read once per draw.
export function tokenColours(): (name: string) => string
{
    const style = getComputedStyle(document.documentElement);
    const cache = new Map<string, string>();
    return (name) =>
    {
        let value = cache.get(name);
        if (value === undefined)
        {
            value = style.getPropertyValue(`--${name}`).trim() || '#888888';
            cache.set(name, value);
        }
        return value;
    };
}

function path(context: CanvasRenderingContext2D, s: ToScreen, cells: readonly Point[], closed: boolean): void
{
    context.beginPath();
    cells.forEach((cell, index) =>
    {
        const [mx, my] = cellToMap(cell);
        const [x, y] = s(mx, my);
        if (index === 0)
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

export interface SketchDrawing
{
    files: FileTrees;
    selection: string | null;
    hover: string | null;
    // Layers drawn faint (the current stage's are drawn in full).
    faint?: ReadonlySet<SketchLayer>;
}

// The sketch over the land.
export function drawSketch(context: CanvasRenderingContext2D, s: ToScreen, drawing: SketchDrawing, colour: (name: string) => string): void
{
    const shapes = sketchShapes(drawing.files);
    const building = enteredBuilding(drawing.files, drawing.selection);
    const cellPixels = Math.abs(s(512, 0)[0] - s(0, 0)[0]);
    context.save();
    context.lineJoin = 'round';
    for (const shape of shapes)
    {
        if (shape.layer === 'part' && shape.address.split('/')[0] !== building && drawing.selection?.split('/')[0] !== shape.address.split('/')[0])
        {
            continue;
        }
        const selected = drawing.selection === shape.address;
        const hovered = drawing.hover === shape.address;
        const base = colour(LAYER_COLOURS[shape.layer]);
        const stroke = selected ? colour('plan-select') : hovered ? colour('plan-hover') : base;
        context.globalAlpha = drawing.faint?.has(shape.layer) && !selected ? 0.45 : 1;
        context.setLineDash(shape.ghost ? [5, 3] : []);
        switch (shape.geom)
        {
        case 'polygon':
        case 'box':
        {
            path(context, s, shape.cells, true);
            const fill = shape.layer === 'water' ? 0.45 : shape.layer === 'ground' ? 0.18 : shape.layer === 'structure' || shape.layer === 'part' ? 0.5
                : shape.layer === 'frame' || shape.layer === 'district' ? 0 : 0.14;
            if (fill > 0)
            {
                context.fillStyle = shape.layer === 'ground' ? groundColour(shape.kind ?? '', colour) : base;
                const alpha = context.globalAlpha;
                context.globalAlpha = alpha * fill;
                context.fill();
                context.globalAlpha = alpha;
            }
            context.strokeStyle = stroke;
            context.lineWidth = selected ? 2.5 : shape.layer === 'patch' || shape.layer === 'frame' ? 1.5 : 1.2;
            if (shape.layer === 'patch' || shape.layer === 'area' || shape.layer === 'frame')
            {
                context.setLineDash([6, 4]);
            }
            context.stroke();
            context.setLineDash([]);
            break;
        }
        case 'polyline':
        {
            path(context, s, shape.cells, false);
            context.strokeStyle = stroke;
            // A road as wide as it is (lane half a cell, road one, high road two).
            const width = shape.layer === 'road' ? Math.max(3, cellPixels * 0.8) : shape.layer === 'land' ? 3 : shape.layer === 'water' ? Math.max(3, cellPixels) : 2;
            context.lineWidth = selected ? width + 2 : width;
            context.globalAlpha *= shape.layer === 'road' || shape.layer === 'water' ? 0.75 : 1;
            context.stroke();
            if (shape.word === 'cliffs')
            {
                // The cliff's low side: ticks to the right of its line.
                ticks(context, s, shape.cells, stroke);
            }
            break;
        }
        case 'point':
        {
            const [mx, my] = cellToMap(shape.cells[0]);
            const [x, y] = s(mx, my);
            context.fillStyle = stroke;
            context.strokeStyle = stroke;
            context.lineWidth = 1.5;
            context.beginPath();
            if (shape.layer === 'structure')
            {
                context.rect(x - 5, y - 5, 10, 10);
                context.globalAlpha *= 0.85;
                context.fill();
            }
            else if (shape.layer === 'actor')
            {
                context.arc(x, y, 5, 0, Math.PI * 2);
                context.stroke();
                context.beginPath();
                context.arc(x, y, 1.8, 0, Math.PI * 2);
                context.fill();
            }
            else if (shape.layer === 'point')
            {
                context.moveTo(x, y - 7);
                context.lineTo(x + 6, y + 5);
                context.lineTo(x - 6, y + 5);
                context.closePath();
                context.fill();
            }
            else if (shape.word === 'plots')
            {
                context.rect(x - 4, y - 4, 8, 8);
                context.stroke();
            }
            else
            {
                // Height points and spires: a cross with the height.
                context.moveTo(x - 4, y - 4);
                context.lineTo(x + 4, y + 4);
                context.moveTo(x + 4, y - 4);
                context.lineTo(x - 4, y + 4);
                context.stroke();
            }
            break;
        }
        case 'circle':
        {
            const [mx, my] = cellToMap(shape.cells[0]);
            const [x, y] = s(mx, my);
            context.beginPath();
            context.arc(x, y, (shape.radius ?? 1) * cellPixels, 0, Math.PI * 2);
            context.fillStyle = base;
            const alpha = context.globalAlpha;
            context.globalAlpha = alpha * 0.14;
            context.fill();
            context.globalAlpha = alpha;
            context.strokeStyle = stroke;
            context.lineWidth = selected ? 2.5 : 1.2;
            context.setLineDash([6, 4]);
            context.stroke();
            context.setLineDash([]);
            break;
        }
        }
        context.globalAlpha = 1;
        if ((selected || hovered || shape.layer === 'point' || shape.layer === 'land' && shape.geom === 'point') && shape.label && cellPixels > 2)
        {
            labelAt(context, s, shape, colour);
        }
    }
    context.restore();
}

// The world's kinds of land as plan colours (a hint of the tile, not the tile).
function groundColour(material: string, colour: (name: string) => string): string
{
    const known: Record<string, string> = { grass: '#5e9a3c', grass_meadow: '#5e9a3c', sand: '#d9c27a', sand_ripples: '#d9c27a', snow: '#eef2f5', swamp: '#5b6b3a',
        volcanic: '#5a4a46', cracked: '#a08a6a', tropical: '#4fa36a', cobble: '#9a948a', rock: '#8a8a8a', desert: '#d8b878', dirt: '#8a6d4a', soil: '#8a6d4a',
        wasteland: '#8f8263', redrock: '#a8603e' };
    return known[material] ?? colour('plan-land-high');
}

function ticks(context: CanvasRenderingContext2D, s: ToScreen, cells: readonly Point[], stroke: string): void
{
    context.strokeStyle = stroke;
    context.lineWidth = 1.5;
    for (let i = 0; i + 1 < cells.length; ++i)
    {
        const [ax, ay] = s(...cellToMap(cells[i]));
        const [bx, by] = s(...cellToMap(cells[i + 1]));
        const length = Math.hypot(bx - ax, by - ay) || 1;
        // Right of the line seen walking it on the screen.
        const nx = -(by - ay) / length;
        const ny = (bx - ax) / length;
        for (let t = 0.1; t < 1; t += Math.max(0.1, 14 / length))
        {
            const x = ax + (bx - ax) * t;
            const y = ay + (by - ay) * t;
            context.beginPath();
            context.moveTo(x, y);
            context.lineTo(x - nx * 7, y - ny * 7);
            context.stroke();
        }
    }
}

function labelAt(context: CanvasRenderingContext2D, s: ToScreen, shape: SketchShape, colour: (name: string) => string): void
{
    const xs = shape.cells.map((cell) => cell[0]);
    const ys = shape.cells.map((cell) => cell[1]);
    const at: Point = shape.geom === 'point' || shape.geom === 'circle' ? shape.cells[0] : [(Math.min(...xs) + Math.max(...xs)) / 2, Math.min(...ys)];
    const [x, y] = s(...cellToMap(at));
    context.font = '600 11px ui-monospace, monospace';
    const text = shape.label!;
    const width = context.measureText(text).width;
    context.fillStyle = colour('surface');
    context.globalAlpha = 0.85;
    context.fillRect(x + 7, y - 17, width + 8, 15);
    context.globalAlpha = 1;
    context.fillStyle = colour('text');
    context.fillText(text, x + 11, y - 6);
}

// What the plan picks at a map point (Author mode, outdoors): the word's address there, or null.
export function sketchHit(files: FileTrees, selection: string | null, x: number, y: number, reachUnits: number): string | null
{
    const shape = shapeAt(sketchShapes(files), mapToCell([x, y]), reachUnits / 512, enteredBuilding(files, selection) ?? (selection && !selection.startsWith('/') && !selection.includes('/') ? selection : null));
    return shape ? shape.address : null;
}
