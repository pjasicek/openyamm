// Plain geometry for the plan view (no DOM): the view transform, hit tests, height bands. Map units, x east,
// y north; the screen has y down, so north is up.

export type Point = [number, number];

export interface Bounds
{
    minX: number;
    minY: number;
    maxX: number;
    maxY: number;
}

export function emptyBounds(): Bounds
{
    return { minX: Infinity, minY: Infinity, maxX: -Infinity, maxY: -Infinity };
}

export function extend(bounds: Bounds, point: readonly number[]): Bounds
{
    bounds.minX = Math.min(bounds.minX, point[0]);
    bounds.minY = Math.min(bounds.minY, point[1]);
    bounds.maxX = Math.max(bounds.maxX, point[0]);
    bounds.maxY = Math.max(bounds.maxY, point[1]);
    return bounds;
}

export function isEmpty(bounds: Bounds): boolean
{
    return !(bounds.maxX >= bounds.minX && bounds.maxY >= bounds.minY);
}

// World to screen: screen = (x - cx) * scale + w/2, (cy - y) * scale + h/2.
export interface ViewTransform
{
    cx: number;
    cy: number;
    scale: number;
    width: number;
    height: number;
}

export function toScreen(view: ViewTransform, x: number, y: number): Point
{
    return [(x - view.cx) * view.scale + view.width / 2, (view.cy - y) * view.scale + view.height / 2];
}

export function toWorld(view: ViewTransform, sx: number, sy: number): Point
{
    return [(sx - view.width / 2) / view.scale + view.cx, view.cy - (sy - view.height / 2) / view.scale];
}

// The transform that shows `bounds` with a margin of `margin` pixels.
export function fit(bounds: Bounds, width: number, height: number, margin = 24): ViewTransform
{
    if (isEmpty(bounds))
    {
        return { cx: 0, cy: 0, scale: 0.05, width, height };
    }
    const w = Math.max(1, bounds.maxX - bounds.minX);
    const h = Math.max(1, bounds.maxY - bounds.minY);
    const scale = Math.min((width - 2 * margin) / w, (height - 2 * margin) / h);
    return { cx: (bounds.minX + bounds.maxX) / 2, cy: (bounds.minY + bounds.maxY) / 2, scale: Math.max(scale, 1e-4), width, height };
}

// Zoom about a screen point, keeping the world point under it in place.
export function zoomAt(view: ViewTransform, sx: number, sy: number, factor: number): ViewTransform
{
    const [wx, wy] = toWorld(view, sx, sy);
    const scale = Math.min(50, Math.max(1e-4, view.scale * factor));
    return {
        ...view,
        scale,
        cx: wx - (sx - view.width / 2) / scale,
        cy: wy + (sy - view.height / 2) / scale,
    };
}

export function pointInPolygon(point: readonly number[], polygon: readonly (readonly number[])[]): boolean
{
    let inside = false;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++)
    {
        const [xi, yi] = polygon[i];
        const [xj, yj] = polygon[j];
        if ((yi > point[1]) !== (yj > point[1]) && point[0] < ((xj - xi) * (point[1] - yi)) / (yj - yi) + xi)
        {
            inside = !inside;
        }
    }
    return inside;
}

export function distanceToSegment(p: readonly number[], a: readonly number[], b: readonly number[]): number
{
    const dx = b[0] - a[0];
    const dy = b[1] - a[1];
    const length2 = dx * dx + dy * dy;
    const t = length2 === 0 ? 0 : Math.max(0, Math.min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / length2));
    return Math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy));
}

export function polygonArea(polygon: readonly (readonly number[])[]): number
{
    let area = 0;
    for (let i = 0, j = polygon.length - 1; i < polygon.length; j = i++)
    {
        area += (polygon[j][0] + polygon[i][0]) * (polygon[j][1] - polygon[i][1]);
    }
    return Math.abs(area / 2);
}

export function centroid(polygon: readonly (readonly number[])[]): Point
{
    let x = 0;
    let y = 0;
    for (const point of polygon)
    {
        x += point[0];
        y += point[1];
    }
    return [x / Math.max(1, polygon.length), y / Math.max(1, polygon.length)];
}

// Height bands from the floors when the plan names none: floors sorted, a new band where the next floor is more
// than `gap` above the last (S5_BROWSER_EDITOR.md 3.4). Returns each band's [low, high].
export function floorClusters(floors: number[], gap = 384): [number, number][]
{
    const sorted = [...floors].sort((a, b) => a - b);
    const bands: [number, number][] = [];
    for (const floor of sorted)
    {
        const last = bands[bands.length - 1];
        if (last && floor - last[1] <= gap)
        {
            last[1] = floor;
        }
        else
        {
            bands.push([floor, floor]);
        }
    }
    return bands;
}

// An outdoor cell (x east, y south from the north-west corner; `size` cells of `cell` units) to map units.
export function cellToWorld(cx: number, cy: number, size: number, cell: number): Point
{
    return [(cx - size / 2) * cell, (size / 2 - cy) * cell];
}

// Hillshade of a height grid (row by row from the north): 0..1 per cell, light from the north-west.
export function hillshade(heights: readonly number[], size: number, unit: number, cell: number): Float32Array
{
    const out = new Float32Array(size * size);
    const at = (x: number, y: number) => heights[Math.min(size - 1, Math.max(0, y)) * size + Math.min(size - 1, Math.max(0, x))] * unit;
    for (let y = 0; y < size; ++y)
    {
        for (let x = 0; x < size; ++x)
        {
            const dx = (at(x + 1, y) - at(x - 1, y)) / (2 * cell);
            const dy = (at(x, y + 1) - at(x, y - 1)) / (2 * cell);
            // Normal (-dx, dy, 1) in (east, north, up) with y south in the grid; light from north-west, above.
            const nx = -dx;
            const ny = dy;
            const length = Math.hypot(nx, ny, 1);
            const light = (-0.5 * nx + 0.5 * ny + 0.707) / length;
            out[y * size + x] = Math.max(0, Math.min(1, light));
        }
    }
    return out;
}
