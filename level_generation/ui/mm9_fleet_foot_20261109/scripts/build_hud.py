"""Fleet Foot HUD movement indicator: eight seamless 128 x 128 RGBA frames fleetfoot01..08.png for the MM9 world.

One HD boot (masters/hud_boot.png, Codex) shared by every frame and one HD wing (masters/hud_wing.png, Codex) used
for both wings. MM9's native indicator (FLEETFOOTANIM.pcx: eight 36 x 36 frames on a cyan key) gives, per frame, the
silhouette of each wing (left and right of the ankle); the HD wing is warped onto each silhouette by an affine fitted
as for the Fly indicator (moment matching over a rotation sweep, then Powell on the soft IoU), with its root held at
the ankle. Whether a wing passes in front of the boot follows the native frame. The boot keeps its pixels in every
frame (the native boot sinks by a third of a native pixel while the wings are up; that is not reproduced, since a
one-pixel HD bob reads as a twitch).

Native frame 8 repeats frame 1 (the native loop holds that pose for two frames); here frame 8 lies halfway between
frames 7 and 1, so 7 -> 8 -> 1 is one even stroke (--native-8 keeps the hold instead).

python3 -I build_hud.py [--native-8]   (writes ../out/fleetfoot01..08.png and ../out/hud_fit.txt)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as nd
from scipy import optimize

STUDY = Path(__file__).resolve().parents[1]
ROOT = STUDY.parents[2]
NATIVE = ROOT / "mm9/extracted/ART/ART/HUD/FLEETFOOTANIM.pcx"
OUT = STUDY / "out"
FRAMES = 8
N = 36  # native frame size
HD = 128  # output frame size
WORK = 512  # composite size, downsampled once to HD
S = HD / N
ANKLE = np.array([16.5, 17.5])  # native (row, col) where both wings leave the boot shaft
SHAFT_ROWS = (11, 18)  # native rows and columns of the boot shaft beside the ankle (wings cross it there)
SHAFT_COLS = (13, 20)
LUMA = np.array([0.299, 0.587, 0.114], np.float32)
BOOT_SATURATION = 0.85


def native_frames():
    image = Image.open(NATIVE)
    index = np.asarray(image)
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    frames = []
    for k in range(FRAMES):
        opaque = index[:, k * N:(k + 1) * N] != 255
        colour = rgb[:, k * N:(k + 1) * N]
        r, b = colour[..., 0], colour[..., 2]
        grey = opaque & (r - b < 25)
        # the wings are the dark unsaturated masses (an edge-on wing is a diagonal line of short horizontal runs); the
        # boot's own dark rim is a one-pixel-wide vertical line and falls to a horizontal opening
        grey = nd.binary_opening(grey, structure=np.ones((1, 2), bool))
        labels, count = nd.label(grey, structure=np.ones((3, 3)))
        sizes = nd.sum(grey, labels, range(1, count + 1))
        wing = np.isin(labels, 1 + np.nonzero(sizes >= 6)[0])
        boot = opaque & ~wing
        frames.append({"opaque": opaque, "rgb": colour, "wing": wing, "boot": boot})
    return frames


def split_wing(wing):
    """Left and right wing: with the shaft beside the ankle masked out the two wings are separate components; the
    masked pixels go to the nearer one."""
    shaft = np.zeros_like(wing)
    shaft[SHAFT_ROWS[0]:SHAFT_ROWS[1] + 1, SHAFT_COLS[0]:SHAFT_COLS[1] + 1] = True
    outside = wing & ~shaft
    labels, count = nd.label(outside, structure=np.ones((3, 3)))
    sizes = nd.sum(outside, labels, range(1, count + 1))
    keep = 1 + np.argsort(sizes)[::-1][:2]
    centres = [np.nonzero(labels == i)[1].mean() for i in keep]
    left_id, right_id = (keep[0], keep[1]) if centres[0] < centres[1] else (keep[1], keep[0])
    seeds = np.where(labels == left_id, 1, np.where(labels == right_id, 2, 0))
    _, (iy, ix) = nd.distance_transform_edt(seeds == 0, return_indices=True)
    nearest = seeds[iy, ix]
    return wing & (nearest == 1), wing & (nearest == 2)


def zoom_mask(mask, size):
    """Native mask to a size x size soft mask (pixel areas preserved)."""
    up = nd.zoom(mask.astype(np.float32), size / N, order=1, grid_mode=True, mode="grid-constant")
    return nd.gaussian_filter(up, 0.35 * size / N)


def warp(image, params, shape, order=1):
    """params: inverse affine a, b, c, d, ty, tx mapping output (y, x) to input (y, x)."""
    a, b, c, d, ty, tx = params
    matrix = np.array([[a, b], [c, d]])
    offset = np.array([ty, tx])
    if image.ndim == 2:
        return nd.affine_transform(image, matrix, offset, output_shape=shape, order=order, mode="constant")
    return np.stack([nd.affine_transform(image[..., i], matrix, offset, output_shape=shape, order=order,
                                         mode="constant") for i in range(image.shape[-1])], -1)


def moments(mask):
    total = mask.sum()
    yy, xx = np.mgrid[0:mask.shape[0], 0:mask.shape[1]]
    cy = (yy * mask).sum() / total
    cx = (xx * mask).sum() / total
    dy, dx = yy - cy, xx - cx
    cov = np.array([[(dy * dy * mask).sum(), (dy * dx * mask).sum()],
                    [(dy * dx * mask).sum(), (dx * dx * mask).sum()]]) / total
    return np.array([cy, cx]), cov


def sqrtm(cov):
    w, v = np.linalg.eigh(cov)
    return v @ np.diag(np.sqrt(np.maximum(w, 1e-6))) @ v.T


def inverse_params(forward, source_center, target_center):
    inv = np.linalg.inv(forward)
    offset = source_center - inv @ target_center
    return np.array([inv[0, 0], inv[0, 1], inv[1, 0], inv[1, 1], offset[0], offset[1]])


def forward_point(params, point):
    """Where the source point lands in the output under inverse params."""
    matrix = params[:4].reshape(2, 2)
    return np.linalg.solve(matrix, point - params[4:])


def fit_wing(source, root, target, ankle):
    """Affine taking the source wing onto the target silhouette with its root near the ankle."""
    cs, covs = moments(source)
    ct, covt = moments(target)
    shape = target.shape

    def score(p):
        matrix = p[:4].reshape(2, 2)
        if np.linalg.det(matrix) <= 1e-4:
            return 10.0
        w = warp(source, p, shape)
        inter = (w * target).sum()
        value = inter / max(w.sum() + target.sum() - inter, 1e-6)
        miss = np.linalg.norm(forward_point(p, root) - ankle) / shape[0]
        return -(value - 2.0 * max(0.0, miss - 0.04))

    best_p, best = None, 1e9
    for degrees in range(0, 360, 6):
        t = np.radians(degrees)
        rot = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        forward = sqrtm(covt) @ rot @ np.linalg.inv(sqrtm(covs))
        p = inverse_params(forward, cs, ct)
        value = score(p)
        if value < best:
            best_p, best = p, value
    result = optimize.minimize(score, best_p, method="Powell",
                               options={"xtol": 1e-4, "ftol": 1e-7, "maxfev": 6000})
    p = result.x if result.fun < best else best_p
    w = warp(source, p, shape)
    inter = (w * target).sum()
    iou = inter / max(w.sum() + target.sum() - inter, 1e-6)
    return p, iou, np.linalg.norm(forward_point(p, root) - ankle)


def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA")).astype(np.float32) / 255.0


def premultiply(rgba):
    out = rgba.copy()
    out[..., :3] *= out[..., 3:4]
    return out


def over(dst, src):
    """Premultiplied over."""
    return src + dst * (1 - src[..., 3:4])


def wing_root(alpha):
    """Root of the master wing: the opaque pixel nearest the bottom-left corner (the wing is painted root lower-left,
    tip upper-right)."""
    ys, xs = np.nonzero(alpha > 0.5)
    h = alpha.shape[0]
    i = int(np.argmin((h - ys) ** 2 + xs ** 2))
    return np.array([ys[i], xs[i]], np.float64)


def place(master, box, size):
    """The master (RGBA) scaled uniformly into box (y0, x0, y1, x1) of a size x size canvas, centred."""
    h, w = master.shape[:2]
    scale = min((box[2] - box[0]) / h, (box[3] - box[1]) / w)
    image = Image.fromarray((master * 255 + 0.5).astype(np.uint8), "RGBA")
    image = image.resize((max(1, round(w * scale)), max(1, round(h * scale))), Image.LANCZOS)
    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    canvas.paste(image, (int(round((box[1] + box[3] - image.width) / 2)),
                         int(round((box[0] + box[2] - image.height) / 2))))
    return np.asarray(canvas).astype(np.float32) / 255.0


def main():
    native_8 = "--native-8" in sys.argv
    frames = native_frames()
    log = []

    # Boot: the master fitted into the bounding box of the native boot silhouette (boot pixels in at least half the
    # frames, filled; the wings hide different parts of it in each frame).
    votes = np.sum([f["boot"] for f in frames], axis=0)
    silhouette = nd.binary_fill_holes(votes >= FRAMES // 2)
    ys, xs = np.nonzero(silhouette)
    w = WORK / N
    boot_box = (ys.min() * w, xs.min() * w, (ys.max() + 1) * w, (xs.max() + 1) * w)
    boot = place(load_rgba(STUDY / "masters/hud_boot.png"), boot_box, WORK)
    grey = (boot[..., :3] @ LUMA)[..., None]
    boot[..., :3] = grey + BOOT_SATURATION * (boot[..., :3] - grey)  # copper-bright leather toned toward the native tan
    boot = premultiply(boot)
    boot_alpha_native = nd.zoom(boot[..., 3], N / WORK, order=1) > 0.5
    log.append(f"boot box native rows {ys.min()}-{ys.max()} cols {xs.min()}-{xs.max()}")

    # Wing: the master at WORK resolution for sampling, its alpha at HD resolution for fitting.
    wing_master = load_rgba(STUDY / "masters/hud_wing.png")
    wing_right = place(wing_master, (0, 0, WORK, WORK), WORK)
    wing_left = wing_right[:, ::-1].copy()
    sources = {}
    for side, image in (("left", wing_left), ("right", wing_right)):
        alpha_hd = nd.zoom(image[..., 3], HD / WORK, order=1)
        root = wing_root(alpha_hd if side == "right" else alpha_hd[:, ::-1])
        if side == "left":
            root[1] = HD - 1 - root[1]
        sources[side] = (premultiply(image), alpha_hd, root)

    ankle_hd = (ANKLE + 0.5) * S - 0.5
    fits = []
    for k, frame in enumerate(frames):
        left, right = split_wing(frame["wing"])
        entry = {}
        for side, mask in (("left", left), ("right", right)):
            if mask.sum() < 4:
                entry[side] = None
                continue
            target = zoom_mask(mask, HD)
            params, iou, miss = fit_wing(sources[side][1], sources[side][2], target, ankle_hd)
            # in front of the boot where the native frame shows this wing over the boot's silhouette
            covers = (mask & boot_alpha_native).sum()
            expected = (nd.zoom(warp(sources[side][1], params, (HD, HD)), N / HD, order=1) > 0.5)
            expected_cover = (expected & boot_alpha_native).sum()
            front = covers >= max(2, 0.5 * expected_cover)
            entry[side] = {"params": params, "front": bool(front)}
            log.append(f"frame {k + 1} {side}: IoU {iou:.3f}, root miss {miss:.1f} HD px, "
                       f"{'front' if front else 'behind'} ({covers}/{expected_cover} boot px)")
        fits.append(entry)

    if not native_8:
        # frame 8 halfway between 7 and 1 (native 8 is a copy of 1)
        mid = {}
        for side in ("left", "right"):
            a, b = fits[6][side], fits[0][side]
            mid[side] = {"params": (a["params"] + b["params"]) / 2, "front": a["front"] and b["front"]}
        fits[7] = mid
        log.append("frame 8: halfway between frames 7 and 1")

    to_work = WORK / HD
    OUT.mkdir(exist_ok=True)
    for k, entry in enumerate(fits):
        canvas = np.zeros((WORK, WORK, 4), np.float32)
        layers = []
        for side in ("left", "right"):
            if entry[side] is None:
                continue
            p = entry[side]["params"]
            matrix = p[:4].reshape(2, 2)
            # HD params to WORK resolution: output o' = 4 o + 1.5, input likewise
            offset = to_work * p[4:] + (to_work - 1) / 2 - matrix @ np.full(2, (to_work - 1) / 2)
            work_params = np.concatenate([p[:4], offset])
            layers.append((entry[side]["front"], warp(sources[side][0], work_params, (WORK, WORK))))
        for front, layer in layers:
            if not front:
                canvas = over(canvas, layer)
        canvas = over(canvas, boot)
        for front, layer in layers:
            if front:
                canvas = over(canvas, layer)
        image = Image.fromarray((np.clip(canvas, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBa").convert("RGBA")
        image = image.resize((HD, HD), Image.LANCZOS)
        path = OUT / f"fleetfoot{k + 1:02d}.png"
        image.save(path)
        path.chmod(0o644)
    (OUT / "hud_fit.txt").write_text("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    main()
