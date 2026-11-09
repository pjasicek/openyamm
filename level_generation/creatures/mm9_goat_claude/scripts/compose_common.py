"""Texel helpers for the farm-animal compose scripts (from mm9_wolf_claude/scripts/compose_wolf.py): rasterise the
dump_uv3d.py triangles into texels, pad gutters, write the shared normal/ORM maps, paint the mouth cavity."""
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

W = np.array([0.2126, 0.7152, 0.0722])


def hsv(rgb):
    mx, mn = rgb.max(-1), rgb.min(-1)
    d = mx - mn + 1e-9
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    h = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) * 60
    return h, d / (mx + 1e-9), mx


def raster(npz, size, fields):
    d = np.load(npz)
    uv = d['uv'] * size
    tri = np.full((size, size), -1, np.int32)
    out = {f: np.zeros((size, size), np.float32) for f in fields}
    for t in range(len(uv)):
        p = uv[t]
        x0, x1 = max(int(np.floor(p[:, 0].min())), 0), min(int(np.ceil(p[:, 0].max())), size - 1)
        y0, y1 = max(int(np.floor(p[:, 1].min())), 0), min(int(np.ceil(p[:, 1].max())), size - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a, b, c = p
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gy - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gy - c[1])) / den
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-4) & (l2 >= -1e-4) & (l3 >= -1e-4)
        if not inside.any():
            continue
        iy, ix = np.nonzero(inside)
        rows, cols = size - 1 - (iy + y0), ix + x0
        tri[rows, cols] = t
        for f in fields:
            v = d[f][t]
            out[f][rows, cols] = l1[inside] * v[0] + l2[inside] * v[1] + l3[inside] * v[2]
    return tri, out, d


def pad(img, covered):
    _, (iy, ix) = ndimage.distance_transform_edt(~covered, return_indices=True)
    return img[iy, ix]


def feather(m, covered):
    m = pad(m.astype(np.float32), covered)
    return np.asarray(Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0)),
                      np.float32) / 255


def paint_cavity(rgb, covered, cav, t, low, x, seed=1):
    """Oral cavity paint (sRGB 0..1) on the texels of the bag: lips dark, gums and ridged palate pink, tongue on the
    floor middle, pale lower incisors just behind the lip (ruminants have no upper incisors), throat near black."""
    gum = np.array([0.66, 0.38, 0.40])
    palate = np.array([0.60, 0.34, 0.37])
    tongue = np.array([0.72, 0.43, 0.44])
    rng = np.random.default_rng(seed)
    noise = ndimage.gaussian_filter(rng.normal(size=rgb.shape[:2]), 1.5) * 8
    roof = palate[None, None] * (1 + 0.12 * np.sin(t * 40))[..., None]    # palate ridges
    floor = gum[None, None] + (tongue - gum)[None, None] * np.clip(1.4 - x * 2.0, 0, 1)[..., None]
    c = roof * (1 - low)[..., None] + floor * low[..., None]
    c = c * (1 + 0.05 * noise)[..., None]
    teeth = (low > 0.5) & (t > 0.08) & (t < 0.24) & (x < 0.6)
    c[teeth] = np.array([0.83, 0.79, 0.68])
    dark = np.clip((t - 0.45) / 0.55, 0, 1) ** 1.2
    c = c * (1 - 0.88 * dark)[..., None]
    c = c * (0.55 + 0.45 * np.clip(t / 0.08, 0, 1))[..., None]             # inner lip rim dark
    out = rgb.copy()
    out[cav] = c[cav]
    return out


def write_maps(M, T, name, covered1k, cls_rough, S=1024, covered2k=None):
    """normal 1K (padded), ORM 1K: R baked AO, G roughness (cls_rough(roughness) -> roughness), B 0."""
    nrm = np.asarray(Image.open(M / 'texture_urls_0_normal.png').convert('RGB').resize(covered2k.shape[::-1], Image.LANCZOS),
                     np.float32) / 255
    Image.fromarray((pad(nrm, covered2k) * 255).astype(np.uint8)).resize((S, S), Image.LANCZOS).save(
        T / f'{name}_normal_1k.png')
    rough = np.asarray(Image.open(M / 'texture_urls_0_roughness.png').convert('L').resize((S, S), Image.LANCZOS),
                       np.float32) / 255
    rough = pad(cls_rough(rough), covered1k)
    ao = np.asarray(Image.open(T / f'{name}_ao_2k.png').convert('L').resize((S, S), Image.LANCZOS), np.float32) / 255
    Image.merge('RGB', [Image.fromarray((ao * 255).astype(np.uint8)), Image.fromarray((rough * 255).astype(np.uint8)),
                        Image.new('L', (S, S), 0)]).save(T / f'{name}_metal_rough_1k.png')
