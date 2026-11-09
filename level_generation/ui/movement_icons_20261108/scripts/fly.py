"""Fly indicator (sp21a10..80): one HD sandal, two HD wings warped per frame to the native wing silhouettes,
procedural sparkles at the native sparkle places. Every pixel outside the wings and sparkles is identical in all frames.

python3 fly.py   (writes ../out/fly/sp21a10.png .. sp21a80.png and ../out/fly/fit.txt)
"""
import numpy as np
from scipy import ndimage as nd
from scipy import optimize

from common import (FRAME_COUNT, OUT_DIR, SCALE, detect_sparkles, draw_sparkle, load_hd, load_native, luma,
                    main_component, over, save_rgba, up)

BASE = "sp21a"


def sparkle_mask(rgb, opaque, static):
    bright = (rgb[..., 0] >= 250) & (rgb[..., 1] >= 240)
    return opaque & bright & ~static


HINGE = (27.0, 31.0)  # native (row, col) where both wings leave the ankle ring
WING_ROWS = 30  # wings live above this native row; below is the sandal


def split_wings(wing):
    """Near (right) and far (left) wing: the wing pixels split at the emptiest direction around the hinge."""
    ys, xs = np.nonzero(wing)
    angles = np.degrees(np.arctan2(HINGE[0] - ys, xs - HINGE[1]))
    hist, edges = np.histogram(angles, bins=90, range=(0, 180))
    smooth = nd.uniform_filter1d(hist.astype(np.float32), 5)
    lo, hi = np.searchsorted(edges, 40), np.searchsorted(edges, 115)
    cut = edges[lo + int(np.argmin(smooth[lo:hi]))]
    near = np.zeros_like(wing)
    near[ys[angles < cut], xs[angles < cut]] = True
    return near, wing & ~near, cut


def native_layers():
    frames = [load_native(BASE, k) for k in range(1, FRAME_COUNT + 1)]
    rgb = np.stack([f[0] for f in frames])
    opaque = np.stack([f[1] for f in frames])
    change = np.abs(rgb - rgb[0]).sum(-1).max(0)
    static = (change <= 24) & opaque.all(0)
    sandal = nd.binary_fill_holes(nd.binary_closing(static, iterations=2))
    rows = np.arange(64)[:, None] < WING_ROWS
    below = ~rows
    layers = []
    for k in range(FRAME_COUNT):
        body = main_component(opaque[k])
        sparkles = sparkle_mask(rgb[k], opaque[k], static) | (opaque[k] & ~body)
        wing = body & ~sandal & ~below & ~sparkles
        wing = main_component(nd.binary_opening(wing) | (wing & nd.binary_dilation(nd.binary_opening(wing))))
        near, far, cut = split_wings(wing)
        layers.append({"rgb": rgb[k], "opaque": opaque[k], "body": body, "sparkles": sparkles,
                       "near": near, "far": far, "cut": cut})
    return sandal, layers


def soft(mask, sigma=1.2):
    return nd.gaussian_filter(up(mask).astype(np.float32), sigma)


def warp(image, params, order=1):
    """params: inverse affine a,b,c,d,tx,ty mapping output (y, x) to input (y, x)."""
    a, b, c, d, ty, tx = params
    matrix = np.array([[a, b], [c, d]])
    offset = np.array([ty, tx])
    if image.ndim == 2:
        return nd.affine_transform(image, matrix, offset, order=order, mode="constant", cval=0.0)
    return np.stack([nd.affine_transform(image[..., i], matrix, offset, order=order, mode="constant", cval=0.0)
                     for i in range(image.shape[-1])], -1)


def moments(mask):
    total = mask.sum()
    yy, xx = np.mgrid[0:mask.shape[0], 0:mask.shape[1]]
    cy = (yy * mask).sum() / total
    cx = (xx * mask).sum() / total
    dy = yy - cy
    dx = xx - cx
    cov = np.array([[(dy * dy * mask).sum(), (dy * dx * mask).sum()],
                    [(dy * dx * mask).sum(), (dx * dx * mask).sum()]]) / total
    return np.array([cy, cx]), cov


def sqrtm(cov):
    w, v = np.linalg.eigh(cov)
    return v @ np.diag(np.sqrt(np.maximum(w, 1e-6))) @ v.T


def inverse_params(forward, source_center, target_center):
    """Forward map t = A (s - cs) + ct as affine_transform's inverse parameters."""
    inv = np.linalg.inv(forward)
    offset = source_center - inv @ target_center
    return np.array([inv[0, 0], inv[0, 1], inv[1, 0], inv[1, 1], offset[0], offset[1]])


def iou(source, target, p):
    w = warp(source, p)
    inter = (w * target).sum()
    return inter / max(w.sum() + target.sum() - inter, 1e-6)


def fit(source, target):
    """Affine that maps the source wing onto the target silhouette: moment matching over a rotation sweep, then
    Powell on the soft IoU."""
    cs, covs = moments(source)
    ct, covt = moments(target)
    base = sqrtm(covt) @ np.linalg.inv(sqrtm(covs))
    best_p, best_iou = None, -1.0
    for degrees in range(-60, 61, 4):
        t = np.radians(degrees)
        rot = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        forward = sqrtm(covt) @ rot @ np.linalg.inv(sqrtm(covs))
        p = inverse_params(forward, cs, ct)
        value = iou(source, target, p)
        if value > best_iou:
            best_p, best_iou = p, value
    del base
    r = optimize.minimize(lambda p: -iou(source, target, p), best_p, method="Powell",
                          options={"xtol": 1e-4, "ftol": 1e-7, "maxfev": 8000})
    return (r.x, -r.fun) if -r.fun > best_iou else (best_p, best_iou)


def inpaint(rgba, hole, iterations=40):
    """Fills hole pixels from their opaque neighbours (straight alpha kept from the neighbourhood)."""
    out = rgba.copy()
    known = ~hole
    pm = out[..., :3] * out[..., 3:4]
    for _ in range(iterations):
        k = known.astype(np.float32)
        num = np.stack([nd.uniform_filter(pm[..., i] * k, 3) for i in range(3)], -1)
        anum = nd.uniform_filter(out[..., 3] * k, 3)
        den = nd.uniform_filter(k, 3)
        fill = hole & (den > 0)
        pm[fill] = num[fill] / den[fill][:, None]
        out[..., 3][fill] = anum[fill] / den[fill]
        known = known | fill
        hole = hole & ~fill
    out[..., :3] = np.where(out[..., 3:4] > 1e-4, pm / np.maximum(out[..., 3:4], 1e-4), 0)
    return out


def master_layers(layers, sandal, index, key):
    """One HD layer of the given native mask taken from HD frame index (frame's own sparkles inpainted)."""
    frame = layers[index]
    hd = load_hd(BASE, index + 1)
    hd = inpaint(hd, nd.binary_dilation(up(frame["sparkles"] & frame["body"]), iterations=2))
    alpha = hd[..., 3]
    if key == "sandal":
        mask = (nd.binary_dilation(up(sandal), iterations=2)
                & ~nd.binary_dilation(up(frame["near"] | frame["far"]), iterations=1)) | up(sandal)
    elif key == "near":
        mask = nd.binary_dilation(up(frame["near"]), iterations=2) & ~up(sandal)
    else:
        mask = nd.binary_dilation(up(frame["far"]), iterations=2) & ~up(sandal) & ~up(frame["near"])
    m = nd.gaussian_filter(mask.astype(np.float32), 0.6)
    out = hd.copy()
    out[..., 3] = alpha * np.clip(m * 1.4, 0, 1)
    # drop off-body sparkles of that HD frame (they lie outside the body mask anyway)
    return out


def warped(layer_rgba, params):
    pm = layer_rgba.copy()
    pm[..., :3] *= pm[..., 3:4]
    w = warp(pm, params, order=1)
    rgb = np.where(w[..., 3:4] > 1e-4, w[..., :3] / np.maximum(w[..., 3:4], 1e-4), 0)
    return np.concatenate([rgb, np.clip(w[..., 3:4], 0, 1)], -1)


def main():
    out_dir = OUT_DIR / "fly"
    sandal, layers = native_layers()
    # Each wing comes from the frame where it shows most (widest), so other frames only compress it.
    near_master = int(np.argmax([f["near"].sum() for f in layers]))
    far_master = int(np.argmax([f["far"].sum() for f in layers]))
    sandal_layer = master_layers(layers, sandal, 0, "sandal")
    near_layer = master_layers(layers, sandal, near_master, "near")
    far_layer = master_layers(layers, sandal, far_master, "far")
    source_near = soft(layers[near_master]["near"])
    source_far = soft(layers[far_master]["far"])
    identity = np.array([1.0, 0, 0, 1.0, 0, 0])
    log = [f"near wing master frame {near_master + 1}, far wing master frame {far_master + 1}"]
    for k, frame in enumerate(layers):
        p_near, iou_near = (identity, 1.0) if k == near_master else fit(source_near, soft(frame["near"]))
        p_far, iou_far = (identity, 1.0) if k == far_master else fit(source_far, soft(frame["far"]))
        log.append(f"frame {k + 1}: near IoU {iou_near:.3f} far IoU {iou_far:.3f}")
        canvas = np.zeros((64 * SCALE, 64 * SCALE, 4), np.float32)
        canvas = over(canvas, warped(far_layer, p_far))
        canvas = over(canvas, warped(near_layer, p_near))
        canvas = over(canvas, sandal_layer)
        for cx, cy, extent, colour, peak, diagonal in detect_sparkles(frame["rgb"], frame["sparkles"],
                                                                      np.zeros_like(frame["body"])):
            canvas = draw_sparkle(canvas, cx, cy, extent, colour, peak, diagonal=diagonal)
        save_rgba(canvas, out_dir / f"{BASE}{k + 1}0.png")
    (out_dir / "fit.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()
