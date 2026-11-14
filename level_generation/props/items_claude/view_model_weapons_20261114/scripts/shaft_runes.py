"""The legendary poles' shaft (README.md "Legendary poles"), called by post.py skin for tier 4 of the kinds in POLES.

At idle only the shaft of a pole is on screen, so it carries the tier. Meshy paints the wood from masters at about 30
pixels per unit, softer than the screen shows it (README.md "Shaft sharpness"), so the shaft's look is drawn here from
each texel's 3D position, at the map's full resolution:
- the wood recoloured to near-black ebony with a blue-violet cast, Meshy's brightness kept as faint detail, and a fine
  lengthwise fibre grain;
- inlaid rune channels: `starts` helices up the wood, each a glowing core (cyan at the centre, violet at its rim) in a
  dark groove between two raised platinum lips, widened into a diamond rune every `node` units of height;
- glowing cabochons set round the shaft's collars and bands (metal and brass between the wrap and the head), each in a
  platinum bezel.
Colours, roughness, metalness, emission and the normal are all written here; the shaft axis is the model's +Y (x = z
= 0), the coordinates those of the runtime model.
"""
import numpy as np

POLES = ('spear', 'halberd', 'trident')
# Shaft radius about 1.2 (2.5 across): pitch is the rise of one channel per turn.
# The core 0.5 units wide (about 18 px across at idle near the hand): the narrower first channel (0.22) read as a
# thin pale lilac line outdoors (2026-11-14 review), the legendary bow's channel as a glow.
CHANNEL = {'starts': 2, 'pitch': 26.0, 'core': 0.25, 'groove': 0.34, 'lip': 0.08, 'node': 6.0, 'node_len': 1.3,
           'node_width': 1.7}
# KHR_materials_emissive_strength of the legendary poles, as the legendary bow (oblivion_weapon_skins_20261114): post.py
# writes it on the material; the emissive map holds the glow's colour at up to 1.0.
EMISSIVE_STRENGTH = 2.5
# Bands 0.7-3 units tall (not the halberd's langets); small stones like the masters' beads.
GEMS = {'count': 8, 'radius': 0.24, 'bezel': 0.06, 'min_height': 0.7, 'max_height': 3.0}
EBONY = np.array([0.017, 0.012, 0.038])            # linear; sRGB about (35, 28, 55)
PLATINUM = np.array([0.72, 0.73, 0.76])
CYAN = np.array([0.0, 0.78, 1.0])                 # saturated: violet only at the rim and in the runes
VIOLET = np.array([0.52, 0.26, 1.0])
GEM_CYAN = np.array([0.04, 0.78, 1.0])          # the cabochons alternate cyan and violet
GEM_VIOLET = np.array([0.6, 0.18, 1.0])


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ring_noise(x, cells, seed):
    """Value noise over x in lattice cells, periodic with period `cells` (x = turn fraction times cells)."""
    i = np.floor(x).astype(np.int64)
    f = x - i

    def h(k):
        k = (np.mod(k, cells) * 374761393 + seed * 668265263) & 0xFFFFFFFF
        k = ((k ^ (k >> 13)) * 1274126177) & 0xFFFFFFFF
        return (k & 0xFFFF) / 65535.0 * 2 - 1
    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def line_noise(x, seed):
    i = np.floor(x).astype(np.int64)
    f = x - i

    def h(k):
        k = (k * 374761393 + seed * 668265263) & 0xFFFFFFFF
        k = ((k ^ (k >> 13)) * 1274126177) & 0xFFFFFFFF
        return (k & 0xFFFF) / 65535.0 * 2 - 1
    u = f * f * (3 - 2 * f)
    return h(i) * (1 - u) + h(i + 1) * u


def tilt(n, direction, slope):
    out = n - direction * slope[..., None]
    return out / np.maximum(np.linalg.norm(out, axis=-1, keepdims=True), 1e-9)


def apply(p, n, region, inside, lin, rough, metallic, emission, normal, tx, ty, ids):
    """Changes lin, rough, metallic, emission and normal (tangent space) in place on the shaft; returns stats (with
    the material's emissive_strength)."""
    # The head's runes and stones (post.py) scaled so that with the material's strength they glow 1.25x as before.
    emission *= 1.25 / EMISSIVE_STRENGTH
    y = p[..., 1]
    r = np.maximum(np.hypot(p[..., 0], p[..., 2]), 1e-3)
    theta = np.arctan2(p[..., 2], p[..., 0])
    turn = theta / (2 * np.pi) % 1.0
    e_theta = np.stack([-np.sin(theta), np.zeros_like(theta), np.cos(theta)], -1)
    e_y = np.array([0.0, 1.0, 0.0])
    wood = (region == ids['wood']) & inside
    hide = (region == ids['leather']) & inside
    fitted = np.isin(region, (ids['metal'], ids['brass'])) & inside
    wrap_top = y[hide].max() if hide.any() else y[wood].min()
    wood_top = y[wood].max()
    world_n = n.copy()

    # Ebony: Meshy's brightness as faint detail, a lengthwise fibre grain.
    lum = lin @ np.array([0.2126, 0.7152, 0.0722])
    detail = np.clip(lum / max(np.median(lum[wood]), 1e-4), 0.55, 1.7) ** 0.45
    warp = 0.9 * line_noise(y / 5.0, 31) + 0.35 * line_noise(y / 1.7, 32)
    fibre = (0.6 * ring_noise(turn * 90 + warp * 3, 90, 33) + 0.4 * ring_noise(turn * 230 + warp * 7, 230, 34))
    streak = smoothstep(0.55, 0.95, ring_noise(turn * 40 + warp, 40, 35) * 0.5 + 0.5
                        + 0.25 * line_noise(y / 0.6, 36))
    ebony = EBONY * (detail * (1 + 0.32 * fibre) * (1 - 0.35 * streak))[..., None]
    lin[wood] = ebony[wood]
    rough[wood] = np.clip(0.34 + 0.08 * fibre + 0.12 * streak, 0.2, 0.6)[wood]
    metallic[wood] = 0.0

    # Rune channels.
    c = CHANNEL
    s = c['starts'] * (turn + y / c['pitch'])
    fs = s - np.round(s)
    rate = c['starts'] * np.sqrt((1 / (2 * np.pi * r)) ** 2 + (1 / c['pitch']) ** 2)
    d = np.abs(fs) / rate
    along = (y + 0.5 * c['node'] * np.round(s)) / c['node']
    node = np.clip(1 - np.abs(along - np.round(along)) * c['node'] / (0.5 * c['node_len']), 0, 1)
    width = 1 + (c['node_width'] - 1) * node
    core, groove, lip = c['core'] * width, c['groove'] * width, c['lip'] * np.sqrt(width)
    glow = (1 - smoothstep(0.7 * core, core, d)) * wood
    lips = (smoothstep(groove - 0.012, groove + 0.012, d) * (1 - smoothstep(groove + lip - 0.012, groove + lip + 0.012, d))
            * wood)
    pit = smoothstep(core, core + 0.01, d) * (1 - smoothstep(groove - 0.012, groove + 0.012, d)) * wood
    rel = np.clip(d / np.maximum(core, 1e-4), 0, 1)
    hue = np.maximum(smoothstep(0.72, 1.0, rel), node * smoothstep(0.3, 0.65, rel))
    drift = 0.5 + 0.5 * np.sin(y / 7.0 + np.round(s) * 1.3)
    rim = VIOLET * (0.75 + 0.25 * drift[..., None])
    glow_col = CYAN * (1 - hue[..., None]) + rim * hue[..., None]
    lin[:] = lin * (1 - pit[..., None] * 0.7)
    lin[:] = lin * (1 - lips[..., None]) + PLATINUM * lips[..., None]
    lin[:] = lin * (1 - glow[..., None]) + glow_col * 0.55 * glow[..., None]
    rough[:] = rough * (1 - lips) + 0.2 * lips
    rough[:] = rough * (1 - glow) + 0.3 * glow
    metallic[:] = metallic * (1 - lips) + lips
    metallic[:] = metallic * (1 - glow)
    emission[:] = emission + glow_col * glow[..., None] * 1.0
    # The groove glows faintly violet round the core.
    emission[:] = emission + rim * (pit * 0.3)[..., None]
    lin[:] = lin + rim * (pit * 0.05)[..., None]
    # Relief: lips raised, groove sunk; the slope across the channel, along the surface gradient of s.
    grad = (c['starts'] / (2 * np.pi * r))[..., None] * e_theta + (c['starts'] / c['pitch']) * e_y
    grad /= np.maximum(np.linalg.norm(grad, axis=-1, keepdims=True), 1e-9)
    grad *= np.sign(fs)[..., None]

    def height(dd):
        lip_mid = groove + 0.5 * lip
        bump = np.clip(1 - np.abs(dd - lip_mid) / (0.5 * lip + 0.02), 0, 1)
        sink = 1 - smoothstep(core * 0.6, groove, dd)
        return 0.035 * bump ** 0.7 - 0.03 * sink
    slope = (height(d + 0.01) - height(d - 0.01)) / 0.02
    channel_zone = wood & (d < (groove + lip) * 1.4)
    world_n = np.where(channel_zone[..., None], tilt(world_n, grad, slope), world_n)

    # Cabochons round the collars and bands of the shaft.
    g = GEMS
    band = fitted & (r > 1.05) & (r < 1.9) & (y > wrap_top - 1.5) & (y < wood_top + 1.5)
    gems = np.zeros(inside.shape)
    bezel = np.zeros(inside.shape)
    tint = np.zeros(inside.shape)
    shade = np.zeros(inside.shape)
    placed = 0
    if band.any():
        rows = np.unique(np.round(y[band] / 0.25).astype(int))
        runs, start = [], rows[0]
        for a, b in zip(rows[:-1], rows[1:]):
            if b - a > 2:
                runs.append((start, a))
                start = b
        runs.append((start, rows[-1]))
        for k, (lo, hi) in enumerate(runs):
            y0, y1 = lo * 0.25, hi * 0.25
            if not g['min_height'] <= y1 - y0 <= g['max_height']:
                continue
            here = band & (y >= y0 - 0.2) & (y <= y1 + 0.2)
            radius = min(g['radius'], 0.4 * (y1 - y0))
            mid = 0.5 * (y0 + y1)
            rr = np.median(r[here])
            for j in range(g['count']):
                a = (j + 0.5 * (k % 2)) / g['count']
                du = ((turn - a + 0.5) % 1.0 - 0.5) * 2 * np.pi * rr
                dy = y - mid
                dist = np.hypot(du, dy)
                dome = here & (dist < radius)
                ring = here & (dist >= radius) & (dist < radius + g['bezel'])
                if not dome.any():
                    continue
                placed += 1
                gems = np.maximum(gems, dome.astype(float))
                shade = np.where(dome, 1 - 0.6 * (dist / radius) ** 2, shade)
                tint = np.where(dome, float(j % 2), tint)
                bezel = np.maximum(bezel, ring.astype(float))
                outward = (du / radius)[..., None] * e_theta + (dy / radius)[..., None] * e_y
                world_n = np.where(dome[..., None], tilt(world_n, -outward, np.full(dist.shape, 0.9)), world_n)
                world_n = np.where(ring[..., None], tilt(world_n, outward, np.full(dist.shape, 0.4)), world_n)
        gem_col = GEM_CYAN * (1 - tint[..., None]) + GEM_VIOLET * tint[..., None]
        lin[:] = lin * (1 - bezel[..., None]) + PLATINUM * bezel[..., None]
        lin[:] = lin * (1 - gems[..., None]) + gem_col * (0.45 * shade * gems)[..., None]
        rough[:] = rough * (1 - bezel) + 0.18 * bezel
        rough[:] = rough * (1 - gems) + 0.12 * gems
        metallic[:] = metallic * (1 - gems)
        metallic[:] = metallic * (1 - bezel) + bezel
        emission[:] = emission + gem_col * ((0.35 + 0.65 * shade) * gems)[..., None]

    # Normal back to tangent space where the relief changed it.
    changed = channel_zone | (gems > 0) | (bezel > 0)
    ts = np.stack([np.sum(world_n * tx, -1), np.sum(world_n * ty, -1), np.sum(world_n * n, -1)], -1)
    ts /= np.maximum(np.linalg.norm(ts, axis=-1, keepdims=True), 1e-9)
    normal[changed] = ts[changed]
    return {'emissive_strength': EMISSIVE_STRENGTH, 'shaft_glow_share': round(float((glow > 0.5)[wood].mean()), 4), 'shaft_gems': placed,
            'wrap_top': round(float(wrap_top), 1), 'wood_top': round(float(wood_top), 1)}
