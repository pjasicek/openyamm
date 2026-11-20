"""Pack one 512 px PBR atlas per icon from the scrolls batch's parchment and the Codex emblem/cover paintings.

Atlas quadrants follow the scrolls batch (`build_scrolls.uv_tile`): front paper top-left, reverse/darker paper
top-right, emblem bottom-left. Envelope paper is the scrolls batch's `7item251` parchment, so these letters match it.
Each emblem cell of `codex/emblems_raw.png` is cut out by its own alpha, fitted into the 256 px emblem quadrant and
written with its binary mask (`textures/<icon>_emblem_mask.png`) — the builder extrudes the 3D emblem from exactly
that mask, so geometry and painting share one mapping. The book atlas holds the Codex cover and spine paintings.
Usage: python3 prepare_textures.py"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

P = Path(__file__).resolve().parents[1]
SCROLLS = P.parent / 'items_wip_scrolls_20261018/textures'
OUT = P / 'textures'
# Emblem order in the Codex sheet, and which painted colours are metal (gold/silver), by hue rule.
EMBLEMS = ['7item252', '7item253', '7item254', '7item255', '7item256', '7item257', '7item258', 'item266']
METAL = {'7item252': 'gold', '7item256': 'all'}


def load(path):
    return np.asarray(Image.open(path).convert('RGBA'), np.float64) / 255


def save(rgb, path):
    Image.fromarray(np.clip(rgb * 255 + .5, 0, 255).astype(np.uint8)).save(path)


def normal_from(rgb, strength):
    lum = rgb @ np.array([.2126, .7152, .0722])
    height = (lum - ndimage.gaussian_filter(lum, 1.5)) * strength
    dy, dx = np.gradient(height)
    n = np.stack([-dx * 3, dy * 3, np.ones_like(dx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True) * .5 + .5


def emblem_cells(sheet):
    """Objects of the 4 x 2 sheet, assigned to cells by centroid (imagegen drifts across cell borders)."""
    alpha = sheet[..., 3] > .5
    if alpha.all():
        # Magenta fallback background.
        alpha = ~((sheet[..., 0] > .85) & (sheet[..., 1] < .25) & (sheet[..., 2] > .85))
    cell = sheet.shape[1] // 4
    labels, count = ndimage.label(alpha)
    sizes = ndimage.sum(alpha, labels, range(1, count + 1))
    centres = ndimage.center_of_mass(alpha, labels, range(1, count + 1))
    cells = {}
    for label, ((cy, cx), size) in enumerate(zip(centres, sizes), 1):
        if size < 200:
            continue
        cells.setdefault((int(cy // cell), int(cx // cell)), []).append(label)
    result = {}
    for (row, column), members in cells.items():
        index = row * 4 + column
        if index >= len(EMBLEMS):
            continue
        keep = np.isin(labels, members)
        ys, xs = np.nonzero(keep)
        crop = sheet[ys.min():ys.max() + 1, xs.min():xs.max() + 1].copy()
        crop[..., 3] = keep[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        result[EMBLEMS[index]] = crop
    return result


def fit(crop, size=256, margin=10):
    """Fit an emblem crop into a size x size tile, keeping its aspect; returns rgb, mask and the fitted box."""
    h, w = crop.shape[:2]
    scale = (size - 2 * margin) / max(h, w)
    nw, nh = max(1, round(w * scale)), max(1, round(h * scale))
    image = Image.fromarray(np.clip(crop * 255, 0, 255).astype(np.uint8), 'RGBA').resize((nw, nh),
                                                                                       Image.Resampling.LANCZOS)
    tile = np.zeros((size, size, 4))
    x0, y0 = (size - nw) // 2, (size - nh) // 2
    tile[y0:y0 + nh, x0:x0 + nw] = np.asarray(image, np.float64) / 255
    mask = ndimage.binary_opening(tile[..., 3] > .5, iterations=1)
    rgb = tile[..., :3].copy()
    # Pad colours outward so filtering at the silhouette never reaches the background.
    _, (iy, ix) = ndimage.distance_transform_edt(~mask, return_indices=True)
    rgb = rgb[iy, ix]
    return rgb, mask, [x0, y0, nw, nh]


def relief_data(mask, path, pool=2):
    """The builder's heightfield input (Blender's Python has no scipy): the mask pooled to its build grid, cleaned,
    and each cell's distance to the silhouette."""
    h, w = mask.shape
    small = mask.reshape(h // pool, pool, w // pool, pool).mean((1, 3)) > .5
    small = ndimage.binary_opening(small, iterations=1)
    # No diagonal-only contacts: they would pinch the stepped surface.
    small = ndimage.binary_closing(small, structure=np.ones((2, 2)))
    distance = ndimage.distance_transform_edt(np.pad(small, 1))[1:-1, 1:-1]
    np.savez(path, small=small, dist=distance, size=np.array([w, h]), pool=np.array(pool))


def metal_mask(icon, rgb, mask):
    rule = METAL.get(icon)
    if rule == 'all':
        return mask
    if rule == 'gold':
        r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
        return mask & (r > b + .15) & (g > b + .05)
    return np.zeros_like(mask)


def paper_atlas():
    base = load(SCROLLS / '7item251_basecolor.png')[..., :3]
    return base


def envelope_icon(icon, emblem):
    base = paper_atlas().copy()
    # Reverse/darker paper (the underside of a folded report), from the front paper.
    base[:256, 256:] = base[:256, :256] * np.array([.82, .76, .7])
    rgb, mask, box = fit(emblem)
    base[256:, :256] = rgb
    mr = np.zeros_like(base)
    mr[..., 0] = 1
    mr[..., 1] = 213 / 255
    metal = metal_mask(icon, rgb, mask)
    tile = mr[256:, :256]
    tile[..., 1] = np.where(metal, .32, .38)
    tile[..., 2] = metal.astype(float)
    normal = np.empty_like(base)
    normal[:256, :256] = normal_from(base[:256, :256], .10)
    normal[:256, 256:] = normal_from(base[:256, 256:], .10)
    normal[256:, :] = normal_from(base[256:, :], .25)
    for suffix, image in (('basecolor', base), ('mr', mr), ('normal', normal)):
        save(image, OUT / f'{icon}_{suffix}.png')
    Image.fromarray((mask * 255).astype(np.uint8)).save(OUT / f'{icon}_emblem_mask.png')
    relief_data(mask, OUT / f'{icon}_relief.npz')
    return {'emblem_box': box, 'metal_pixels': int(metal.sum()), 'emblem_pixels': int(mask.sum())}


def paper_only(icon, tint):
    base = paper_atlas().copy()
    base[:256, :256] *= np.array(tint)
    base[:256, 256:] = base[:256, :256] * .9
    mr = np.zeros_like(base)
    mr[..., 0], mr[..., 1] = 1, 213 / 255
    normal = normal_from(base, .12)
    for suffix, image in (('basecolor', base), ('mr', mr), ('normal', normal)):
        save(image, OUT / f'{icon}_{suffix}.png')


def book():
    """Cover top-left 384 x 256 (u .0-.75, v .5-1), spine strip below it, page edges, plain leather at right."""
    cover = load(P / 'codex/item320_cover.png')[..., :3]
    spine = load(P / 'codex/item320_spine.png')[..., :3]
    base = np.zeros((512, 512, 3))
    base[:256, :384] = np.asarray(Image.fromarray((cover * 255).astype(np.uint8)).resize((384, 256),
                                                                                         Image.Resampling.LANCZOS)) / 255
    base[256:320, :384] = np.asarray(Image.fromarray((spine * 255).astype(np.uint8)).resize((384, 64),
                                                                                           Image.Resampling.LANCZOS)) / 255
    rows = np.arange(64)[:, None]
    columns = np.arange(384)[None, :]
    lines = .84 + .16 * (np.sin(rows * 1.3 + np.sin(columns * .01) * 2) > .2)
    base[320:384, :384] = np.array([.86, .78, .6]) * lines[..., None]
    # Plain leather (board edges, back cover) sampled from the cover's border colour.
    border = np.median(base[4:12, 40:340].reshape(-1, 3), axis=0)
    base[:, 384:] = border
    base[384:, :384] = border
    r, g, b = base[..., 0], base[..., 1], base[..., 2]
    gold = (r > .45) & (g > .3) & (g > b + .12) & (g / np.maximum(r, 1e-3) > .55)
    gold[256:] = False
    mr = np.zeros_like(base)
    mr[..., 0] = 1
    mr[..., 1] = np.where(gold, .35, .62)
    mr[320:384, :384, 1] = .85
    mr[..., 2] = gold.astype(float)
    normal = normal_from(base, .3)
    for suffix, image in (('basecolor', base), ('mr', mr), ('normal', normal)):
        save(image, OUT / f'item320_{suffix}.png')
    # The raised gold snake head: the cover's central gold region, as a mask over the cover tile.
    cover_tile = base[:256, :384]
    # The head is everything that is not red leather inside the central area (its scale lines and red eyes
    # would break up a gold test).
    red = (cover_tile[..., 0] > .25) & (cover_tile[..., 1] < .22) & (cover_tile[..., 0] > 1.8 * cover_tile[..., 1])
    head = ndimage.binary_opening(~red, iterations=2)
    centre = np.zeros_like(head)
    centre[8:248, 80:304] = True
    head &= centre
    labels, count = ndimage.label(head)
    if count:
        sizes = ndimage.sum(head, labels, range(1, count + 1))
        head = labels == (np.argmax(sizes) + 1)
        head = ndimage.binary_closing(head, iterations=4)
        head = ndimage.binary_fill_holes(head)
    Image.fromarray((head * 255).astype(np.uint8)).save(OUT / 'item320_relief_mask.png')
    relief_data(head, OUT / 'item320_relief.npz')
    return {'gold_pixels': int(gold.sum()), 'relief_pixels': int(head.sum()), 'cover_mean': cover_tile.mean(0).mean(0).round(3).tolist()}


def main():
    OUT.mkdir(exist_ok=True)
    report = {}
    sheet = load(P / 'codex/emblems_raw.png')
    cells = emblem_cells(sheet)
    missing = [icon for icon in EMBLEMS if icon not in cells]
    assert not missing, missing
    for icon in EMBLEMS:
        report[icon] = envelope_icon(icon, cells[icon])
    paper_only('item318', (.93, .88, .8))
    report['item320'] = book()
    (P / 'work/textures_report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=1))


if __name__ == '__main__':
    main()
