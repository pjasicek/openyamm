"""Procedural Water Walk disc: caustic water in the disc's own plane coloured from the native disc's palette, a ragged
rim with spray, and the drip curtain hanging from the front rim. Everything is a function of the disc angle, so a
turned disc is the same disc: the loop is seamless by construction.

disc(angle_degrees) -> 128x128 RGBA float (straight alpha).
"""
import numpy as np

SIZE = 128
SUPER = 4
CENTRE = (78.0, 63.5)  # HD (row, col) of the surface centre
HALF_WIDTH = 60.0
RATIO = 0.43
DRIP_MAX = 17.0
# native disc palette, darkest to brightest (from sp27a frames)
RAMP = np.array([[32, 30, 64], [49, 48, 120], [64, 61, 128], [76, 72, 148], [110, 108, 182], [190, 190, 245]],
                np.float32) / 255
RAMP_AT = np.array([0.0, 0.25, 0.5, 0.7, 0.88, 1.0], np.float32)

_rng = np.random.default_rng(20261108)
RIM_TERMS = [(k, _rng.uniform(0, 2 * np.pi), _rng.uniform(0.4, 1.0) / k ** 0.6) for k in (5, 9, 14, 21, 29, 37)]
DRIP_TERMS = [(k, _rng.uniform(0, 2 * np.pi), _rng.uniform(0.5, 1.0)) for k in (23, 31, 47, 61, 79)]
SPRAY = [(_rng.uniform(0, 2 * np.pi), _rng.uniform(0.99, 1.16), _rng.uniform(0.9, 2.0)) for _ in range(110)]


def periodic(theta, terms):
    return sum(a * np.sin(k * theta + p) for k, p, a in terms) / sum(a for _, _, a in terms)


def caustic(u, v):
    """Tileable water caustic (the classic iterated-sine pattern), values roughly 0..1."""
    scale = 2 * np.pi / 46.0
    px = np.mod(u * scale, 2 * np.pi) - 250
    py = np.mod(v * scale, 2 * np.pi) - 250
    ix, iy = px.copy(), py.copy()
    c = np.ones_like(px)
    intensity = 0.005
    t = 3.7
    for n in range(5):
        tt = t * (1 - 3.5 / (n + 1))
        ix, iy = (px + np.cos(tt - ix) + np.sin(tt + iy), py + np.sin(tt - iy) + np.cos(tt + ix))
        c += 1.0 / np.sqrt((px / (np.sin(ix + tt) / intensity)) ** 2 + (py / (np.cos(iy + tt) / intensity)) ** 2)
    c /= 5
    c = 1.17 - c ** 1.4
    return np.clip(np.abs(c) ** 5, 0, 1)


def ramp(value):
    value = np.clip(value, 0, 1)
    out = np.zeros(value.shape + (3,), np.float32)
    for i in range(3):
        out[..., i] = np.interp(value, RAMP_AT, RAMP[:, i])
    return out


def disc(angle_degrees):
    n = SIZE * SUPER
    yy, xx = (np.mgrid[0:n, 0:n].astype(np.float32) + 0.5) / SUPER - 0.5
    u = xx - CENTRE[1]
    v = (yy - CENTRE[0]) / RATIO
    r = np.sqrt(u * u + v * v)
    theta = np.arctan2(v, u)
    turn = np.radians(angle_degrees)
    ts = theta - turn
    us, vs = r * np.cos(ts), r * np.sin(ts)
    # water: caustic highlights over a soft large-scale swell
    swell = 0.5 + 0.5 * np.sin(us * 0.11 + 1.3) * np.cos(vs * 0.09 - 0.4)
    light = caustic(us, vs)
    value = 0.26 + 0.28 * swell + 0.78 * light
    value -= 0.18 * np.clip((r / HALF_WIDTH) - 0.75, 0, 1) / 0.25  # darker towards the rim
    colour = ramp(value)
    rim = HALF_WIDTH * (1 + 0.045 * periodic(ts, RIM_TERMS))
    alpha = np.clip((rim - r) / 1.2, 0, 1)
    # spray: droplets just outside the rim, turning with the disc
    for a, rr, size in SPRAY:
        ang = a + turn
        cy = CENTRE[0] + np.sin(ang) * HALF_WIDTH * rr * RATIO
        cx = CENTRE[1] + np.cos(ang) * HALF_WIDTH * rr
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        drop = np.clip((size * 0.5 - d) / 0.5 + 0.5, 0, 1)
        alpha = np.maximum(alpha, drop * 0.85)
    # drip curtain below the front rim: lengths follow the rim angle, so the drips travel with the turn
    front = np.clip(u / HALF_WIDTH, -1, 1)
    front_theta = np.arccos(-front)  # angle of the front rim point above this column (0..pi along the front)
    front_y = CENTRE[0] + RATIO * HALF_WIDTH * np.sqrt(np.clip(1 - front * front, 0, 1))
    depth = yy - front_y
    length = DRIP_MAX * np.clip(0.5 + 0.7 * periodic(front_theta - turn, DRIP_TERMS), 0, 1) ** 1.6
    length *= np.sqrt(np.clip(1 - front * front, 0, 1))
    drip = (depth > -1) & (depth < length) & (np.abs(u) < HALF_WIDTH)
    drip_alpha = np.clip((length - depth) / 1.2, 0, 1) * drip
    drip_colour = ramp(0.38 - 0.25 * np.clip(depth / DRIP_MAX, 0, 1) + 0.25 * caustic(xx * 1.7, depth * 3.0))
    below = (alpha < 1) & (drip_alpha > alpha)
    colour = np.where(below[..., None], drip_colour, colour)
    alpha = np.maximum(alpha, drip_alpha)
    rgba = np.concatenate([colour * alpha[..., None], alpha[..., None]], -1)
    rgba = rgba.reshape(SIZE, SUPER, SIZE, SUPER, 4).mean((1, 3))
    rgb = np.where(rgba[..., 3:4] > 1e-4, rgba[..., :3] / np.maximum(rgba[..., 3:4], 1e-4), 0)
    return np.concatenate([rgb, rgba[..., 3:4]], -1)


if __name__ == "__main__":
    from PIL import Image
    import sys
    frames = [disc(45 * k) for k in range(8)]
    sheet = Image.new("RGBA", (256 * 4, 256 * 2), (22, 24, 30, 255))
    for k, f in enumerate(frames):
        im = Image.fromarray((np.clip(f, 0, 1) * 255).astype(np.uint8), "RGBA").resize((256, 256), Image.LANCZOS)
        sheet.alpha_composite(im, ((k % 4) * 256, (k // 4) * 256))
    sheet.convert("RGB").save(sys.argv[1])
