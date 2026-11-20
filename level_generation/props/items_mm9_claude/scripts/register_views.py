"""Register each generated paint/mask view onto its exact guide silhouette before baking.

Imagegen keeps the content of a guide but not its exact size: views come back 5-35% larger or narrower, which the
bake's bounding-box gate rightly rejects. Asking imagegen for size-only corrections does not converge, so register
the artwork instead: a bounding-box affine fit, then a smooth multi-scale demons warp of the painted silhouette onto
the guide's. The warp is bounded and measured; a view passes only when the warped silhouette overlaps the guide's
(IoU) and its displacement stays small relative to the object, so a painting of a different shape is still rejected.

Every raw revision (paint_mask_raw_v*.png, 3x4 cells: paint rows 0-1, mask rows 2-3; or paint_raw_v*.png, 3x2 paint
cells for single-material designs) is tried per view and kind; the best passing candidate is written as
<kind>_<view>.png in the guide's 1024 frame, raw files stay unchanged. Designs with a 'surface_material' need no mask.
Usage: python3 register_views.py <design> [...]   -> codex_tex/<design>/registration.json"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(P / 'scripts'))
import material_masks as masks  # noqa: E402

DESIGNS = json.loads((P / 'designs.json').read_text())
VIEWS = ['front', 'back', 'left', 'right', 'top']
SIZE = 1024
MIN_IOU = 0.95
# A guide silhouette under this many pixels in its short dimension is an edge-on sliver: skipped.
SLIVER = 82
# 95th-percentile non-rigid displacement as a fraction of the guide's bounding-box diagonal.
MAX_DISPLACEMENT = 0.04


def short_side(folder, view):
    ys, xs = np.nonzero(load(folder / f'guide_{view}.png')[..., 3] > 0.5)
    return min(ys.max() - ys.min(), xs.max() - xs.min())


def sliver(folder, view):
    """An edge-on view: under SLIVER pixels and under half the widest view's short side (a spear is thin from
    every side, so its views stay)."""
    sides = {v: short_side(folder, v) for v in VIEWS}
    return sides[view] < SLIVER and sides[view] < 0.5 * max(sides.values())


def bbox(alpha):
    ys, xs = np.nonzero(alpha)
    return xs.min(), xs.max() + 1, ys.min(), ys.max() + 1


def sample(image, x, y, order):
    channels = [ndimage.map_coordinates(image[..., c], [y, x], order=order, mode='constant', cval=0.0)
                for c in range(image.shape[-1])]
    return np.stack(channels, -1)


def demons(moving, fixed, levels=(16, 8, 4, 2), iterations=80):
    """Displacement (ux, uy) in full-size pixels such that moving(x + u) ~ fixed(x), coarse to fine.

    Each level runs at 1/level resolution with a blurred silhouette (so a misplaced thin strap still sees its guide)
    and a Gaussian-smoothed field (a smooth, fold-free warp); the finest level stays at half resolution."""
    ux = np.zeros(fixed.shape)
    uy = np.zeros(fixed.shape)
    for level in levels:
        f = ndimage.zoom(ndimage.gaussian_filter(fixed, level * 0.5), 1 / level, order=1)
        m = ndimage.zoom(ndimage.gaussian_filter(moving, level * 0.5), 1 / level, order=1)
        f = ndimage.gaussian_filter(f, 1.5)
        m = ndimage.gaussian_filter(m, 1.5)
        shape = f.shape
        lx = ndimage.zoom(ux, np.array(shape) / ux.shape, order=1) / level
        ly = ndimage.zoom(uy, np.array(shape) / uy.shape, order=1) / level
        gy, gx = np.gradient(f)
        yy, xx = np.mgrid[0:shape[0], 0:shape[1]].astype(np.float64)
        for _ in range(iterations):
            warped = ndimage.map_coordinates(m, [yy + ly, xx + lx], order=1, mode='constant')
            difference = warped - f
            wy, wx = np.gradient(warped)
            # Symmetric (fixed + warped moving) gradient forces.
            sx, sy = gx + wx, gy + wy
            denominator = sx ** 2 + sy ** 2 + difference ** 2
            denominator[denominator < 1e-9] = np.inf
            lx -= 2 * difference * sx / denominator
            ly -= 2 * difference * sy / denominator
            lx = ndimage.gaussian_filter(lx, 2.0)
            ly = ndimage.gaussian_filter(ly, 2.0)
        ux = ndimage.zoom(lx * level, np.array(fixed.shape) / shape, order=1)
        uy = ndimage.zoom(ly * level, np.array(fixed.shape) / shape, order=1)
    return ux, uy


def register(cell, guide_alpha, nearest, cell_size):
    """Warp an RGBA object canvas into the guide frame; returns the image and its measurements."""
    alpha = cell[..., 3] > 0.5
    gx0, gx1, gy0, gy1 = bbox(guide_alpha)
    px0, px1, py0, py1 = bbox(alpha)
    sx, sy = (px1 - px0) / (gx1 - gx0), (py1 - py0) / (gy1 - gy0)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float64)
    ax = px0 + (xx + 0.5 - gx0) * sx - 0.5
    ay = py0 + (yy + 0.5 - gy0) * sy - 0.5
    affine_alpha = ndimage.map_coordinates(alpha.astype(np.float64), [ay, ax], order=1, mode='constant')
    fixed = guide_alpha.astype(np.float64)
    ux, uy = demons(affine_alpha, fixed)
    # Compose: guide pixel -> displaced guide pixel -> affine into the painted cell.
    dx, dy = xx + ux, yy + uy
    cx = px0 + (dx + 0.5 - gx0) * sx - 0.5
    cy = py0 + (dy + 0.5 - gy0) * sy - 0.5
    out = sample(cell, cx, cy, 0 if nearest else 1)
    if nearest:
        out[..., 3] = (out[..., 3] > 0.5).astype(np.float64)
    warped = out[..., 3] > 0.5
    before = affine_alpha > 0.5
    diagonal = float(np.hypot(gx1 - gx0, gy1 - gy0))
    displacement = np.hypot(ux, uy)[ndimage.binary_dilation(guide_alpha, iterations=8)]
    return out, {
        'bbox_ratio': [round(float(sx * SIZE / cell_size), 4), round(float(sy * SIZE / cell_size), 4)],
        'iou_affine': round(float((before & guide_alpha).sum() / (before | guide_alpha).sum()), 4),
        'iou_warped': round(float((warped & guide_alpha).sum() / (warped | guide_alpha).sum()), 4),
        'displacement_p95': round(float(np.percentile(displacement, 95) / diagonal), 4),
        'displacement_max': round(float(displacement.max() / diagonal), 4),
    }


def load(path):
    return np.asarray(Image.open(path).convert('RGBA'), np.float64) / 255.0


def clean_mask(image, design):
    """Imagegen draws fold creases into material masks as black (gem) strokes. Classes a design does not have, and
    with 'gems_in_metal' black regions that are not set in a metal fitting, take the nearest allowed class."""
    allowed = design.get('material_classes')
    if not allowed:
        return image, 0
    inside = image[..., 3] > 0.5
    classes = np.full(inside.shape, -1)
    classes[inside] = masks.classify(image[inside][:, :3])
    valid = inside & np.isin(classes, [masks.NAMES.index(name) for name in allowed])
    if design.get('gems_in_metal'):
        gem = classes == masks.NAMES.index('gem')
        metal = classes == masks.NAMES.index('metal')
        labels, count = ndimage.label(gem)
        for label in range(1, count + 1):
            region = labels == label
            ring = ndimage.binary_dilation(region, iterations=2) & ~region & inside
            if ring.any() and (metal & ring).sum() < 0.5 * ring.sum():
                valid &= ~region
    replace = inside & ~valid
    if replace.any():
        _, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
        palette = masks.PALETTE[np.maximum(classes, 0)]
        image = image.copy()
        image[replace, :3] = palette[iy[replace], ix[replace]]
    return image, int(replace.sum())


def view_cells(sheet):
    """Split a 3-column sheet into its (row, column) objects: imagegen lets objects drift over cell borders, so label the
    connected silhouettes and give each to the cell containing its centroid instead of cropping fixed squares."""
    cell = sheet.shape[1] // 3
    rows = sheet.shape[0] // cell
    assert sheet.shape[0] == cell * rows and rows in (2, 4)
    labels, count = ndimage.label(sheet[..., 3] > 0.5)
    centres = ndimage.center_of_mass(np.ones(labels.shape), labels, range(1, count + 1))
    cells = {}
    for label, (cy, cx) in enumerate(centres, 1):
        key = (min(int(cy // cell), rows - 1), min(int(cx // cell), 2))
        cells.setdefault(key, []).append(label)
    result = {}
    for key, members in cells.items():
        sizes = ndimage.sum(np.ones(labels.shape), labels, members)
        # Stray specks would stretch the silhouette box; real parts of an object are far larger.
        members = [m for m, size in zip(members, sizes) if size >= 0.01 * sizes.max()]
        keep = np.isin(labels, members)
        ys, xs = np.nonzero(keep)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        # Square canvas around the object; only its own components keep their alpha.
        side = max(y1 - y0, x1 - x0) + 8
        canvas = np.zeros((side, side, 4))
        oy, ox = (side - (y1 - y0)) // 2, (side - (x1 - x0)) // 2
        crop = sheet[y0:y1, x0:x1].copy()
        crop[~keep[y0:y1, x0:x1]] = 0
        canvas[oy:oy + y1 - y0, ox:ox + x1 - x0] = crop
        result[key] = canvas
    return result


def main():
    for icon in sys.argv[1:]:
        folder = P / 'codex_tex' / icon
        design = DESIGNS[icon]
        raws = sorted(folder.glob('paint_mask_raw_v*.png')) + sorted(folder.glob('paint_raw_v*.png'))
        assert raws, icon
        sheets = {raw.name: (view_cells(load(raw)), Image.open(raw).width // 3) for raw in raws}
        report, failures = {}, []
        for index, view in enumerate(VIEWS):
            if view in design.get('skip_views', ()):
                continue
            guide_alpha = load(folder / f'guide_{view}.png')[..., 3] > 0.5
            # An edge-on view of a flat item (a blade from the side) is a sliver imagegen cannot place to a few
            # pixels; the other views cover it (codex_texture.py skips it too).
            ys, xs = np.nonzero(guide_alpha)
            if sliver(folder, view):
                report[f'{view}'] = {'skipped': 'sliver'}
                continue
            for kind, row in (('paint', 0), ('mask', 2)):
                if kind == 'mask' and 'surface_material' in design:
                    continue
                candidates = []
                for raw, (cells, cell_size) in sheets.items():
                    if kind == 'mask' and raw.startswith('paint_raw_'):
                        continue
                    crop = cells.get((index // 3 + row, index % 3))
                    if crop is None or (crop[..., 3] > 0.5).sum() < 64:
                        continue
                    image, metrics = register(crop, guide_alpha, kind == 'mask', cell_size)
                    metrics['raw'] = raw
                    metrics['passed'] = (metrics['iou_warped'] >= MIN_IOU
                                         and metrics['displacement_p95'] <= MAX_DISPLACEMENT)
                    candidates.append((metrics['passed'], metrics['iou_warped'], image, metrics))
                if not candidates:
                    failures.append(f'{kind}_{view}: no candidate')
                    continue
                passed, _, image, metrics = max(candidates, key=lambda c: (c[0], c[1]))
                if kind == 'mask':
                    image, metrics['reclassified_pixels'] = clean_mask(image, design)
                Image.fromarray(np.clip(image * 255 + 0.5, 0, 255).astype(np.uint8), 'RGBA').save(
                    folder / f'{kind}_{view}.png')
                metrics['raw_sha256'] = hashlib.sha256((folder / metrics['raw']).read_bytes()).hexdigest()
                metrics['candidates'] = [c[3]['raw'] + f": iou {c[3]['iou_warped']}" for c in candidates]
                report[f'{kind}_{view}'] = metrics
                if not passed:
                    failures.append(f'{kind}_{view}: iou {metrics["iou_warped"]} p95 {metrics["displacement_p95"]}')
        frame = json.loads((folder / 'views.json').read_text())
        frame['paint_layout'] = 'individual'
        frame['mask_layout'] = 'individual'
        (folder / 'views.json').write_text(json.dumps(frame, indent=2) + '\n')
        (folder / 'registration.json').write_text(json.dumps(
            {'min_iou': MIN_IOU, 'max_displacement_p95': MAX_DISPLACEMENT, 'passed': not failures,
             'failures': failures, 'views': report}, indent=2) + '\n')
        for key, metrics in report.items():
            if 'skipped' in metrics:
                continue
            print(f'  {icon} {key:12s} {metrics["raw"]} ratio {metrics["bbox_ratio"]} iou {metrics["iou_affine"]}'
                  f' -> {metrics["iou_warped"]} p95 {metrics["displacement_p95"]}'
                  f' {"ok" if metrics["passed"] else "FAIL"}')
        print(icon, 'REGISTERED' if not failures else 'FAILED: ' + '; '.join(failures), flush=True)


if __name__ == '__main__':
    main()
