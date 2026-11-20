"""Corpse skin texture (runs inside Blender, numpy only): recolour a copy of the peasant's base colour atlas by texel
class and paint blood where it would be on the posed body.
- Texel classes: the strongest bone of the triangle covering the texel (rasterised from the posed full-detail mesh)
  plus its colour: skin (and, with `pale_cloth`, the pale trousers) becomes a cold, bloodless grey-white with
  bluish shadows; `hair` and `tier` (the region-mask cloth) and `leather` take the configured colours.
- Blood: the posed mesh is rasterised in texture space to a world position per texel, so wounds (where the stakes
  pass through the body, plus listed points) get a soaked patch, with runs flowing downward in world space below
  them. Texels that no triangle covers keep the recoloured padding."""
import math
import numpy as np


def srgb_to_linear(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def linear_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def rasterise(obj, size, bone_index):
    """Per texel: world position (H, W, 3), bone id (H, W) (-1 uncovered). Rows bottom-up like Blender's pixels."""
    W, H = size
    me = obj.data
    me.calc_loop_triangles()
    uv = np.zeros(len(me.loops) * 2, np.float32); me.uv_layers.active.data.foreach_get('uv', uv)
    uv = uv.reshape(-1, 2)
    co = np.zeros(len(me.vertices) * 3, np.float32); me.vertices.foreach_get('co', co); co = co.reshape(-1, 3)
    tris = np.zeros(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('loops', tris)
    tris = tris.reshape(-1, 3)
    verts = np.zeros(len(me.loop_triangles) * 3, np.int32); me.loop_triangles.foreach_get('vertices', verts)
    verts = verts.reshape(-1, 3)
    rest = co.copy()
    if 'rest' in me.attributes:
        rest = np.zeros(len(me.vertices) * 3, np.float32); me.attributes['rest'].data.foreach_get('vector', rest)
        rest = rest.reshape(-1, 3)
    pos = np.zeros((H, W, 3), np.float32)
    rest_z = np.zeros((H, W), np.float32)
    bone = np.full((H, W), -1, np.int32)
    for t in range(len(tris)):
        p = uv[tris[t]] * (W, H) - 0.5
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0 = max(x0, 0), max(y0, 0); x1, y1 = min(x1, W - 1), min(y1, H - 1)
        if x1 < x0 or y1 < y0:
            continue
        xs, ys = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        d = (p[1, 1] - p[2, 1]) * (p[0, 0] - p[2, 0]) + (p[2, 0] - p[1, 0]) * (p[0, 1] - p[2, 1])
        if abs(d) < 1e-12:
            continue
        a = ((p[1, 1] - p[2, 1]) * (xs - p[2, 0]) + (p[2, 0] - p[1, 0]) * (ys - p[2, 1])) / d
        b = ((p[2, 1] - p[0, 1]) * (xs - p[2, 0]) + (p[0, 0] - p[2, 0]) * (ys - p[2, 1])) / d
        c = 1 - a - b
        inside = (a >= -0.02) & (b >= -0.02) & (c >= -0.02)
        if not inside.any():
            continue
        w = np.stack([a[inside], b[inside], c[inside]], -1)
        pos[ys[inside], xs[inside]] = w @ co[verts[t]]
        rest_z[ys[inside], xs[inside]] = w @ rest[verts[t]][:, 2]
        bone[ys[inside], xs[inside]] = bone_index[verts[t][0]]
    return pos, bone, rest_z


def dilate(pos, bone, rest_z, steps=6):
    """Spread positions, bones and rest heights into uncovered texels round each island (mip/filter padding)."""
    for _ in range(steps):
        empty = bone < 0
        if not empty.any():
            break
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            src_b = np.roll(bone, (dy, dx), (0, 1)); src_p = np.roll(pos, (dy, dx), (0, 1))
            src_z = np.roll(rest_z, (dy, dx), (0, 1))
            take = empty & (src_b >= 0)
            bone[take] = src_b[take]; pos[take] = src_p[take]; rest_z[take] = src_z[take]
            empty = bone < 0
    return pos, bone, rest_z


def box_blur(a, r):
    """Separable box blur with wrap-around (r texels each way)."""
    for axis in (0, 1):
        a = sum(np.roll(a, k, axis) for k in range(-r, r + 1)) / (2 * r + 1)
    return a


def value_noise(pos, scale, seed):
    """Cheap smooth 3D noise from summed sines (deterministic)."""
    rng = np.random.default_rng(seed)
    out = np.zeros(pos.shape[:-1], np.float32)
    for _ in range(6):
        k = rng.normal(size=3) * scale; ph = rng.uniform(0, 2 * math.pi)
        out += np.sin(pos @ k + ph)
    return out / 6 * 0.5 + 0.5


def blood_mask(pos, covered, wounds, seed=3):
    """wounds: [(centre, radius, run_length)] in world metres. Each is a ragged soaked patch (noise-cut edge), a ring
    of spatter, and runs: narrow streaks straight down from points round it."""
    mask = np.zeros(pos.shape[:-1], np.float32)
    rng = np.random.default_rng(seed)
    ragged = value_noise(pos, 70.0, seed) * 0.6 + value_noise(pos, 25.0, seed + 1) * 0.4
    spatter = value_noise(pos, 300.0, seed + 2)
    for centre, radius, run in wounds:
        c = np.asarray(centre, np.float32)
        d = np.linalg.norm(pos - c, axis=-1) / radius
        mask = np.maximum(mask, np.clip((1.0 + 0.9 * (ragged - 0.5) - d) * 6, 0, 1))
        mask = np.maximum(mask, (spatter > 0.84) * np.clip(2.0 - d, 0, 1))
        for _ in range(9):
            a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(0.0, 0.8) * radius
            sx, sy = c[0] + math.cos(a) * r0, c[1] + math.sin(a) * r0
            top = c[2] - rng.uniform(0, 0.3) * radius
            length = run * rng.uniform(0.4, 1.0); width = rng.uniform(0.008, 0.018)
            horizontal = np.hypot(pos[..., 0] - sx, pos[..., 1] - sy)
            below = (pos[..., 2] < top) & (pos[..., 2] > top - length)
            taper = np.clip((pos[..., 2] - (top - length)) / max(length, 1e-3), 0, 1) ** 0.4
            mask = np.maximum(mask, below * np.clip((width * taper - horizontal) / (width * 0.35), 0, 1))
    return mask * covered


def recolour(base_srgb, bone, bone_names, spec, pos, rest_z):
    """base_srgb (H, W, 3) floats; returns linear colour."""
    lin = srgb_to_linear(base_srgb)
    r, g, b = base_srgb[..., 0], base_srgb[..., 1], base_srgb[..., 2]
    mx = base_srgb.max(-1); mn = base_srgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    hue = np.zeros_like(mx)
    delta = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / delta) % 6, hue)
    hue = np.where(mx == g, (b - r) / delta + 2, hue)
    hue = np.where(mx == b, (r - g) / delta + 4, hue)
    hue = hue * 60
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    names = np.array(bone_names + [''])
    bone_name = names[bone]
    is_head = np.char.startswith(bone_name, 'mixamorig:Head') | np.char.startswith(bone_name, 'Braid')
    # shoes: everything below the ankle in the rest pose (the shoe uppers are weighted to the shins)
    is_foot = (rest_z < spec.get('shoe_top', 0.12)) & (bone >= 0)
    warm = (hue > 5) & (hue < 45)
    skin = warm & (sat > 0.18) & (sat < 0.7) & (mx > 0.5) & ~is_foot
    hair = warm & (mx <= 0.5) & is_head & (sat > 0.25)
    leather = warm & (mx <= 0.5) & ~is_head & (sat > 0.25)
    pale_cloth = (hue > 25) & (hue < 70) & (sat < 0.32) & (mx > 0.55) & ~is_head & ~is_foot
    tier = spec['tier_mask']
    out = lin.copy()
    # cold, bloodless skin: keep the shading, replace the hue; a little bruising
    bruise = value_noise(pos, 9.0, 11)
    pale = np.array(spec.get('pale', (0.52, 0.52, 0.58)))
    bruising = (1 - 0.18 * np.clip((bruise - 0.55) * 4, 0, 1))[..., None]
    purple = np.array([0.04, 0.0, 0.05]) * np.clip((bruise - 0.6) * 4, 0, 1)[..., None]
    classes = [skin & ~tier]
    if spec.get('pale_cloth'):
        classes.append(pale_cloth & ~tier & ~skin)
    if spec.get('pale_leather'):
        classes.append((leather | is_foot) & ~tier & ~skin)
    smooth_lum = box_blur(lum, 4)
    for k, m in enumerate(classes):
        if not m.any():
            continue
        # each class keeps its own shading round its own mean, so pale trousers read as the same skin; cloth
        # classes use blurred shading so the weave does not show through the skin
        source = lum if k == 0 else smooth_lum
        shade = np.clip(source / float(np.median(source[m])), 0.25, 1.35)[..., None] ** 0.8
        out[m] = (pale * shade * bruising + purple)[m]
    skin_like = np.logical_or.reduce(classes)
    if spec.get('hair') is not None:
        h = np.asarray(spec['hair'])
        out[hair] = (h * np.clip(lum / 0.06, 0.3, 2.0)[..., None])[hair]
    if spec.get('tier') is not None:
        t = np.asarray(spec['tier'])
        out[tier] = (t * np.clip(lum / 0.09, 0.3, 2.2)[..., None])[tier]
    if spec.get('leather') is not None:
        l = np.asarray(spec['leather'])
        m = leather & ~tier & ~hair
        out[m] = (l * np.clip(lum / 0.05, 0.3, 2.2)[..., None])[m]
    if spec.get('feet') is not None:
        f = np.asarray(spec['feet'])
        m = is_foot & ~skin_like & ~tier
        out[m] = (f * np.clip(lum / 0.08, 0.3, 2.0)[..., None])[m]
    if spec.get('cloth') is not None:
        # pale linen -> the configured (greyer) cloth colour, stained by smooth dirt
        dirt = value_noise(pos, 6.0, 17)
        white = (sat < 0.22) & (mx > 0.5) & ~skin_like & ~tier
        tone = np.asarray(spec['cloth']) * np.clip(lum / 0.55, 0.3, 1.3)[..., None]
        tone *= (1 - spec.get('cloth_dirt', 0.0) * dirt)[..., None]
        out[white] = tone[white]
    return out


def paint_blood(lin, mask, pos):
    tone = np.array([0.42, 0.012, 0.006])
    dark = np.array([0.08, 0.004, 0.003])
    vary = (value_noise(pos, 60.0, 23) ** 2)[..., None]
    blood = tone * (1 - vary) + dark * vary
    m = np.clip(mask, 0, 1)[..., None]
    return lin * (1 - m) + blood * m
