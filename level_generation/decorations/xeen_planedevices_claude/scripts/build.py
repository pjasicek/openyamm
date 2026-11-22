#!/usr/bin/env python3
"""The plane devices of P1 and P2 (lane S, 2026-11-21), built from scratch (procedural meshes and textures, no
Meshy, no Codex): the Ember Font (row 4056), the fire-walker's burnt camp (4057) and the balloonist's wrecked
basket (4058). Model space: metres (1 m = 100 units), +Y up, front toward +Z, origin at the bottom centre.

    build.py font|camp|basket|all

Writes work/<id>/xeen_deco_<name>.glb, work/<id>/textures/*.png and work/<id>/report.json."""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import (Glb, Mesh, disc, ellipsoid, grid, lathe, mr_map, noise, normal_map, ramp,  # noqa: E402
                 smoothstep, tube, u8)

HERE = Path(__file__).resolve().parents[1]


def save(out, name, img):
    (out / 'textures').mkdir(parents=True, exist_ok=True)
    Image.fromarray(img).save(out / 'textures' / f'{name}.png')


def finish(name, out, mesh, glb, order, extra=None):
    lo, hi = mesh.bounds()
    path = out / f'xeen_deco_{name}.glb'
    glb.write(path, f'xeen_deco_{name}', mesh, order)
    report = {'glb': str(path), 'triangles': int(mesh.triangles()),
              'per_material': {m: int(sum(len(i) for i in mesh.parts[m]['i'])) for m in order if m in mesh.parts},
              'bounds_min_m': lo.round(4).tolist(), 'bounds_max_m': hi.round(4).tolist(),
              'height_units': round(float(hi[1] - lo[1]) * 100.0, 1),
              'footprint_units': [round(float(hi[0] - lo[0]) * 100, 1), round(float(hi[2] - lo[2]) * 100, 1)]}
    report.update(extra or {})
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


# ================================================================ textures
def basalt(rng, h, w, heat_v=None, v_keys=None):
    """Dark volcanic stone (X7's basalt look): grain, vesicles and fine cracks. Periodic in u; heat_v(v) in 0..1 per
    row tints the stone toward rust and lights its cracks (the font's lip and inner wall)."""
    n1, n2, n3 = noise(rng, h, w, 26), noise(rng, h, w, 6), noise(rng, h, w, 1.4)
    crack_field = noise(rng, h, w, 34)
    cracks = np.exp(-(crack_field / 0.07) ** 2) * smoothstep(-0.5, 0.8, noise(rng, h, w, 60))
    pits = smoothstep(2.0, 2.8, noise(rng, h, w, 2.2))
    height = 0.6 * n1 + 0.35 * n2 + 0.15 * n3 - 2.2 * cracks - 1.6 * pits
    t = np.clip(0.5 + 0.17 * n1 + 0.12 * n2 + 0.08 * n3, 0, 1)
    rgb = ramp(t, [(0.0, (31, 31, 33)), (0.5, (44, 43, 45)), (1.0, (68, 66, 66))])
    rgb = rgb * (1 - 0.35 * cracks[..., None]) * (1 - 0.3 * pits[..., None])
    emis = np.zeros_like(rgb)
    if heat_v is not None:
        heat = heat_v[:, None] * np.ones((1, w))
        rust = ramp(t, [(0.0, (46, 30, 26)), (1.0, (84, 50, 38))])
        rgb = rgb * (1 - 0.4 * heat[..., None]) + rust * 0.4 * heat[..., None]
        glow = cracks * heat ** 1.5
        emis = np.array([255, 92, 22], float) * glow[..., None] * 0.9
        rgb = rgb + np.array([120, 40, 10]) * glow[..., None] * 0.5
    rough = np.clip(0.82 - 0.08 * n2 + 0.1 * cracks, 0.55, 0.95)
    return u8(np.maximum(rgb, 31)), u8(emis), mr_map(rough), normal_map(height, 1.6)


def lava(rng, size):
    n1, n2, n3 = noise(rng, size, size, 30), noise(rng, size, size, 9), noise(rng, size, size, 15)
    t = 0.65 * n1 + 0.35 * n2
    crust = smoothstep(-0.75, -0.05, t)
    veins = np.exp(-(n3 / 0.09) ** 2)
    e = np.clip((1 - crust) ** 1.3 + 0.55 * veins * crust, 0, 1)
    emis = ramp(e, [(0.0, (10, 1, 0)), (0.3, (96, 16, 1)), (0.7, (220, 64, 6)), (1.0, (255, 150, 40))])
    base = ramp(e, [(0.0, (38, 22, 18)), (0.5, (150, 56, 18)), (1.0, (236, 150, 60))])
    height = crust * 3.0 + 0.4 * n2
    rough = np.clip(0.95 - 0.6 * (1 - crust), 0.3, 0.95)
    return u8(base), u8(emis), mr_map(rough), normal_map(height, 2.0)


def heat_haze(rng, h, w):
    """Additive shimmer over the fire (RGBA): soft vertical licks, faded at its foot and top (baked: no v scroll)."""
    streak = noise(rng, h, w, 18, 5)
    v = (np.arange(h) + 0.5) / h                       # image row 0 = texture v 0 = the shell's bottom
    fade = smoothstep(0.0, 0.12, v) * (1 - smoothstep(0.25, 1.0, v)) ** 1.6
    a = np.clip(0.55 + 0.3 * streak, 0, 1) * fade[:, None]
    rgb = np.array([255, 120, 36], float) * np.ones((h, w, 1))
    return u8(np.dstack([rgb, a[..., None] * 255]))


# ================================================================ Ember Font
FONT_PROFILE = [  # (r, y) metres: up the outside, over the lip, down the inside (below the fire's surface)
    (0.80, 0.00), (0.80, 0.09), (0.74, 0.13), (0.54, 0.17), (0.50, 0.32), (0.60, 0.46), (0.80, 0.66),
    (0.90, 0.84), (0.92, 0.94), (0.90, 1.00), (0.84, 1.03), (0.76, 1.03), (0.72, 0.99), (0.70, 0.90),
]
FONT_SURFACE = 0.95
FONT_SIDES = 12


def build_font():
    out = HERE / 'work' / 'font'
    rng = np.random.default_rng(4056)
    prof = np.array(FONT_PROFILE)
    arc = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(prof, axis=0), axis=1))])
    v = arc / arc[-1]
    # Heat by texture row: none on the foot and stem, a scorch toward the lip, full on the inner wall.
    rows = 1024
    rv = (np.arange(rows) + 0.5) / rows
    v_lip_out, v_in = v[8], v[11]
    heat = 0.2 * smoothstep(v_lip_out - 0.12, v_lip_out + 0.05, rv) + 0.65 * smoothstep(v_in - 0.05, v_in + 0.06, rv)
    base, emis, mr, nrm = basalt(rng, rows, 1024, heat)
    lbase, lemis, lmr, lnrm = lava(rng, 512)
    haze = heat_haze(rng, 128, 512)
    for k, img in dict(stone_base=base, stone_emis=emis, stone_mr=mr, stone_normal=nrm, lava_base=lbase,
                       lava_emis=lemis, lava_mr=lmr, lava_normal=lnrm, haze=haze).items():
        save(out, k, img)
    mesh = Mesh()
    lathe(mesh, 'stone', FONT_PROFILE, FONT_SIDES, u_tiles=3.0, v_of=v, flat=True, phase=np.pi / FONT_SIDES)
    # The fire: a 12-gon matching the inner wall (polygon radius at the surface's height, a little into the wall).
    r_in = np.interp(FONT_SURFACE, prof[11:][::-1, 1], prof[11:][::-1, 0]) + 0.01
    disc(mesh, 'lava', (0.0, FONT_SURFACE, 0.0), r_in, FONT_SIDES, inner_fracs=(0.62, 0.3), uv_scale=1 / 0.5,
         phase=np.pi / FONT_SIDES)
    # A low shimmer standing on the fire (additive, two-sided), inside the wall.
    ang = np.linspace(0, 2 * np.pi, 25)
    hz = np.array([0.0, 0.05, 0.12])
    P = np.zeros((3, 25, 3))
    UV = np.zeros((3, 25, 2))
    for i, y in enumerate(hz):
        r = r_in * (0.93 - 0.18 * y / hz[-1])
        P[i, :, 0], P[i, :, 1], P[i, :, 2] = r * np.cos(ang), FONT_SURFACE + y, -r * np.sin(ang)
        UV[i, :, 0] = ang / (2 * np.pi) * 2.0
        UV[i, :, 1] = y / hz[-1]
    P[:, -1] = P[:, 0]
    grid(mesh, 'haze', P, UV, flip=True, smooth=True, wrap_u=True)
    glb = Glb('xeen_planedevices_claude build.py')
    glb.material('xeen_emberfont_basalt', base, mr, nrm, emis, extras={'openyamm_specular': 0.35})
    glb.material('xeen_emberfont_fire', lbase, lmr, lnrm, lemis, strength=1.1,
                 extras={'openyamm_uv_scroll': [0.018, 0.011], 'openyamm_pulse': [0.12, 3.4],
                         'openyamm_specular': 0.6})
    glb.material('xeen_emberfont_shimmer', haze, emissive=haze[..., :3].copy(), blend=True, double=True,
                 extras={'openyamm_additive': True, 'openyamm_uv_scroll': [0.035, 0.0], 'openyamm_specular': 0.0,
                         'openyamm_flicker': [0.25, 2.0]})
    glb.mat_index = {'stone': 0, 'lava': 1, 'haze': 2}
    finish('emberfont', out, mesh, glb, ['stone', 'lava', 'haze'],
           {'fire_surface_units': FONT_SURFACE * 100, 'fire_radius_units': round(r_in * 100, 1)})


# ================================================================ burnt camp
def blanket_tex(rng, w, h):
    """The bedroll (u along its length, head at u 0, burnt end at u 1; v across). Wool, two head stripes, a border,
    soot rising toward the burnt end, char at the edge, scorch holes, a few embers at the very edge."""
    u = (np.arange(w) + 0.5) / w
    v = (np.arange(h) + 0.5) / h
    U, V = np.meshgrid(u, v)
    weave = 0.5 * np.sin(U * w * np.pi / 3) * np.sin(V * h * np.pi / 3)
    fibre = noise(rng, h, w, 0.8, 3.0)
    mottle = noise(rng, h, w, 30)
    t = np.clip(0.5 + 0.12 * mottle + 0.08 * fibre + 0.06 * weave, 0, 1)
    rgb = ramp(t, [(0, (80, 46, 34)), (0.5, (106, 64, 46)), (1, (132, 88, 62))])
    stripe = ((np.abs(U - 0.13) < 0.018) | (np.abs(U - 0.19) < 0.01) | (V < 0.05) | (V > 0.95)).astype(float)
    rgb = rgb * (1 - stripe[..., None]) + ramp(t, [(0, (56, 42, 30)), (1, (86, 66, 46))]) * stripe[..., None]
    ragged = 0.035 * noise(rng, h, w, 14)
    soot = smoothstep(0.3, 0.86, U + ragged * 2)
    rgb = rgb * (1 - 0.88 * soot[..., None]) + np.array([38, 32, 29]) * 0.88 * soot[..., None]
    char = smoothstep(0.8, 0.95, U + ragged * 1.5)
    holes = np.zeros_like(U)
    for _ in range(9):
        cu, cv, r = rng.uniform(0.35, 0.88), rng.uniform(0.15, 0.85), rng.uniform(0.025, 0.06)
        d = np.sqrt(((U - cu) * w / h) ** 2 + (V - cv) ** 2) / r
        holes = np.maximum(holes, 1 - smoothstep(0.6, 1.25, d + 0.2 * noise(rng, h, w, 6)))
    char = np.maximum(char, holes)
    rgb = rgb * (1 - char[..., None]) + np.array([31, 29, 29]) * char[..., None]
    embers = smoothstep(0.955, 0.99, U + ragged) * smoothstep(1.4, 2.2, noise(rng, h, w, 2.5))
    emis = np.array([255, 74, 12], float) * embers[..., None] * 0.7
    rgb = rgb + np.array([70, 20, 5]) * embers[..., None]
    height = 0.6 * weave + 0.3 * fibre - 1.5 * char + 0.5 * mottle
    rough = np.clip(0.92 - 0.1 * char, 0.7, 0.97)
    return u8(np.maximum(rgb, 31)), u8(emis), mr_map(rough), normal_map(height, 1.2)


def iron_tex(rng, s):
    n1, n2 = noise(rng, s, s, 20), noise(rng, s, s, 3)
    rust = smoothstep(0.9, 1.8, noise(rng, s, s, 12))
    t = np.clip(0.5 + 0.15 * n1 + 0.1 * n2, 0, 1)
    rgb = ramp(t, [(0, (36, 35, 35)), (1, (74, 70, 66))])
    rgb = rgb * (1 - rust[..., None]) + ramp(t, [(0, (84, 46, 28)), (1, (120, 70, 40))]) * rust[..., None]
    rough = np.clip(0.62 + 0.2 * rust + 0.05 * n2, 0.4, 0.95)
    metal = np.clip(0.7 - 0.6 * rust, 0, 1)
    return u8(np.maximum(rgb, 31)), mr_map(rough, metal), normal_map(0.6 * n1 + 0.4 * n2 + 2 * rust, 0.8)


def scorched_stone_tex(rng, s):
    n1, n2, n3 = noise(rng, s, s, 16), noise(rng, s, s, 4), noise(rng, s, s, 1.2)
    t = np.clip(0.5 + 0.17 * n1 + 0.1 * n2 + 0.06 * n3, 0, 1)
    rgb = ramp(t, [(0, (40, 38, 37)), (0.5, (70, 66, 62)), (1, (110, 104, 96))])
    soot = smoothstep(0.0, 1.5, noise(rng, s, s, 24))
    rgb = rgb * (1 - 0.5 * soot[..., None]) + np.array([34, 32, 31]) * 0.5 * soot[..., None]
    return u8(np.maximum(rgb, 31)), mr_map(np.clip(0.85 - 0.05 * n2, 0.6, 0.95)), \
        normal_map(0.6 * n1 + 0.35 * n2 + 0.2 * n3, 1.4)


def ash_tex(rng, s):
    """The dead fire's ash (RGBA, its rim fading into the floor); planar UV 0..1 across the patch."""
    c = (np.arange(s) + 0.5) / s
    X, Y = np.meshgrid(c, c)
    r = np.sqrt((X - 0.5) ** 2 + (Y - 0.5) ** 2) * 2
    n1, n2 = noise(rng, s, s, 10), noise(rng, s, s, 2)
    edge = 1 - smoothstep(0.6, 1.0, r + 0.12 * noise(rng, s, s, 20))
    t = np.clip(0.45 + 0.2 * n1 + 0.12 * n2 - 0.25 * r, 0, 1)
    rgb = ramp(t, [(0, (36, 34, 33)), (0.45, (92, 88, 84)), (1, (168, 162, 154))])
    lumps = smoothstep(1.2, 1.7, noise(rng, s, s, 4)) * (1 - r)
    rgb = rgb * (1 - lumps[..., None]) + np.array([32, 30, 30]) * lumps[..., None]
    embers = smoothstep(1.6, 2.4, noise(rng, s, s, 2.0)) * (1 - smoothstep(0.2, 0.6, r))
    emis = np.array([255, 80, 16], float) * embers[..., None] * 0.6
    rgba = np.dstack([np.maximum(rgb, 31), edge[..., None] * 255])
    return u8(rgba), u8(emis), normal_map(0.6 * n1 + 0.4 * n2 + 1.5 * lumps, 1.0, False, False)


def char_tex(rng, s):
    """Charred wood (the burnt-out logs): black with a cracked grain, faint embers in the cracks."""
    grain = noise(rng, s, s, 1.5, 14)
    cracks = np.exp(-(noise(rng, s, s, 7, 3) / 0.1) ** 2)
    t = np.clip(0.5 + 0.2 * grain, 0, 1)
    rgb = ramp(t, [(0, (31, 30, 30)), (1, (58, 52, 48))])
    rgb = rgb * (1 - 0.3 * cracks[..., None])
    emis = np.array([255, 70, 10], float) * (cracks * smoothstep(0.5, 1.5, noise(rng, s, s, 10)))[..., None] * 0.5
    return u8(np.maximum(rgb, 31)), u8(emis), mr_map(np.full((s, s), 0.9)), normal_map(grain - 2 * cracks, 1.2)


def build_camp():
    out = HERE / 'work' / 'camp'
    rng = np.random.default_rng(4057)
    cloth = blanket_tex(rng, 1024, 512)
    iron = iron_tex(rng, 256)
    stone = scorched_stone_tex(rng, 256)
    ash = ash_tex(rng, 512)
    char = char_tex(rng, 256)
    for k, img in dict(cloth_base=cloth[0], cloth_emis=cloth[1], cloth_mr=cloth[2], cloth_normal=cloth[3],
                       iron_base=iron[0], iron_mr=iron[1], iron_normal=iron[2], stone_base=stone[0],
                       stone_mr=stone[1], stone_normal=stone[2], ash_base=ash[0], ash_emis=ash[1],
                       ash_normal=ash[2], char_base=char[0], char_emis=char[1]).items():
        save(out, k, img)
    mesh = Mesh()
    # Bedroll: a sheet lying on the floor along x (head at -x), its edges down on the ground, its foot burnt away
    # along a ragged line; u along the length up to the burn, v across.
    L, W, x0, z0 = 1.80, 0.72, -1.12, -0.12
    nu, nv = 23, 8
    vv = np.linspace(0, 1, nv)
    burn = 0.78 + 0.08 * np.sin(vv * 5.1 + 0.7) + 0.05 * np.sin(vv * 11.3)
    uu = np.linspace(0, 1, nu)
    bump = noise(rng, 32, 32, 3)
    P = np.zeros((nv, nu, 3))
    UV = np.zeros((nv, nu, 2))
    for i, b in enumerate(burn):
        x = x0 + uu * L * b
        across = (2 * vv[i] - 1)
        lift = 0.055 * (1 - across ** 6) * (1 - 0.8 * smoothstep(0.82, 1.0, uu))
        lumps = 0.018 * bump[(np.arange(nu) * 32 // nu), int(vv[i] * 31)] * (1 - across ** 4)
        P[i, :, 0] = x
        P[i, :, 1] = 0.004 + lift + np.maximum(lumps, -lift * 0.5)
        P[i, :, 2] = z0 + (vv[i] - 0.5) * W * (1 + 0.04 * np.sin(uu * 7))
        UV[i, :, 0] = uu
        UV[i, :, 1] = vv[i]
    grid(mesh, 'cloth', P, UV, flip=True, smooth=True)          # rows across (+z), columns along (+x): up
    # Head roll: the blanket's rolled end, across the head of the sheet (UVs in its unburnt stripe area).
    zs = np.linspace(z0 - W * 0.47, z0 + W * 0.47, 6)
    roll = np.stack([np.full(6, x0 + 0.06), np.full(6, 0.085), zs], axis=1)
    m = mesh.marks().get('cloth', 0)
    tube(mesh, 'cloth', roll, 0.085, 10, u_tiles=1.0, v_scale=1.0)
    part = mesh.parts['cloth']
    for k in range(m, len(part['uv'])):
        uv = part['uv'][k]
        part['uv'][k] = np.stack([0.02 + 0.2 * (uv[:, 0] % 1.0), np.clip(uv[:, 1] / (W * 0.94), 0.06, 0.94)], 1)
    # Kettle: a dented iron lathe, a spout and a bail handle, scaled up a little to read at game distance.
    ks = 1.35
    kp = [(0.06, 0.0), (0.098, 0.012), (0.114, 0.05), (0.11, 0.1), (0.086, 0.138), (0.052, 0.152), (0.054, 0.162),
          (0.036, 0.17), (0.016, 0.178), (0.018, 0.196)]
    kp = [(r * ks, y * ks) for r, y in kp]

    def dent(a, r, y):
        return 1 - 0.13 * np.exp(-((np.angle(np.exp(1j * (a - 2.2)))) ** 2) / 0.25) * np.exp(-((y - 0.09 * ks) ** 2)
                                                                                            / (0.03 * ks) ** 2)
    km = mesh.marks()
    lathe(mesh, 'iron', kp, 12, u_tiles=2.0, flat=False, radial=dent)
    disc(mesh, 'iron', (0, kp[-1][1], 0), kp[-1][0], 12, inner_fracs=(), uv_scale=4.0)
    disc(mesh, 'iron', (0, 0.0, 0), kp[0][0], 12, inner_fracs=(0.5,), uv_scale=4.0, up=False)
    spout = np.array([[0.1, 0.07, 0.0], [0.135, 0.085, 0.0], [0.165, 0.11, 0.0], [0.19, 0.14, 0.0]]) * ks
    tube(mesh, 'iron', spout, np.linspace(0.022, 0.012, 4) * ks, 6, u_tiles=1, v_scale=4)
    a = np.linspace(0.15, np.pi - 0.15, 9)
    bail = np.stack([np.zeros(9), 0.14 + 0.11 * np.sin(a), 0.085 * np.cos(a)], axis=1) * ks
    tube(mesh, 'iron', bail, 0.007 * ks, 4, u_tiles=1, v_scale=4)
    kx, kz, tilt, yaw = 0.62, 0.40, np.radians(9), np.radians(35)

    def place_kettle(p):
        c, s = np.cos(tilt), np.sin(tilt)
        q = p.copy()
        q[:, 0], q[:, 1] = p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c
        q[:, 1] += 0.0 + (kp[0][0]) * np.sin(tilt)      # the tipped base's low rim on the floor
        cy, sy = np.cos(yaw), np.sin(yaw)
        r = q.copy()
        r[:, 0], r[:, 2] = q[:, 0] * cy + q[:, 2] * sy, -q[:, 0] * sy + q[:, 2] * cy
        r[:, 0] += kx
        r[:, 2] += kz
        return r
    mesh.transform(place_kettle, 'iron', km)
    # The dead fire: an ash patch, two burnt-out logs crossed on it, a ring of scorched stones.
    fx, fz, fr = 0.66, -0.1, 0.30
    disc(mesh, 'ash', (fx, 0.006, fz), fr, 12, inner_fracs=(0.6, 0.25), uv_scale=1.0)
    part = mesh.parts['ash']
    part['uv'][-1] = (part['p'][-1][:, [0, 2]] - [fx - fr, fz - fr]) / (2 * fr)
    for ang, off in ((0.5, 0.0), (2.2, 0.03)):
        d = np.array([np.cos(ang), 0, -np.sin(ang)])
        pts = np.array([fx, 0.03 + off, fz]) + np.outer(np.linspace(-0.17, 0.17, 4), d)
        pts[:, 1] += np.array([0.0, 0.006, 0.004, -0.004])
        tube(mesh, 'char', pts, np.array([0.03, 0.034, 0.032, 0.022]), 6, u_tiles=1.0, v_scale=3.0)
    for k in range(7):
        a = k / 7 * 2 * np.pi + rng.uniform(-0.2, 0.2)
        rr = fr + 0.04 + rng.uniform(-0.02, 0.02)
        size = rng.uniform(0.85, 1.2)
        ellipsoid(mesh, 'stone', (fx + rr * np.cos(a), 0.035 * size, fz - rr * np.sin(a)),
                  (0.075 * size, 0.06 * size, 0.062 * size), 4, 6, rng=rng, jitter=0.16, flat=True,
                  uv_tiles=(1.0, 0.5), squash_bottom=0.55)
    # Centre the footprint on the origin, its bottom at 0.
    lo, hi = mesh.bounds()
    shift = np.array([-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2])
    mesh.transform(lambda p: p + shift)
    glb = Glb('xeen_planedevices_claude build.py')
    glb.material('xeen_firecamp_bedroll', cloth[0], cloth[2], cloth[3], cloth[1],
                 extras={'openyamm_specular': 0.15, 'openyamm_pulse': [0.35, 2.6]})
    glb.material('xeen_firecamp_kettle', iron[0], iron[1], iron[2], extras={'openyamm_specular': 0.7})
    glb.material('xeen_firecamp_stone', stone[0], stone[1], stone[2], extras={'openyamm_specular': 0.3})
    glb.material('xeen_firecamp_char', char[0], char[2], char[3], char[1],
                 extras={'openyamm_specular': 0.2, 'openyamm_pulse': [0.4, 3.1]})
    glb.material('xeen_firecamp_ash', ash[0], None, ash[2], ash[1], blend=True, wrap=33071,
                 extras={'openyamm_specular': 0.1, 'openyamm_pulse': [0.4, 2.2]})
    glb.mat_index = {'cloth': 0, 'iron': 1, 'stone': 2, 'char': 3, 'ash': 4}
    finish('firecamp', out, mesh, glb, ['cloth', 'iron', 'stone', 'char', 'ash'],
           {'shift_m': shift.round(4).tolist(), 'note': 'kettle at model (%.2f, %.2f) m after the shift'
            % (kx + shift[0], kz + shift[2])})


# ================================================================ wrecked basket
def wicker_tex(rng, s, stakes=8, rows=16):
    """A tile of wicker (u around, v up): vertical stakes under round horizontal weavers going over and under."""
    x = (np.arange(s) + 0.5) / s
    X, Y = np.meshgrid(x, x)
    row = np.floor(Y * rows)
    fy = (Y * rows) % 1.0
    strand = np.sin(np.pi * fy) ** 0.6                      # round weaver across its band
    phase = (row % 2) * np.pi
    over = 0.5 + 0.5 * np.cos(2 * np.pi * X * stakes / 2 + phase)
    gap = 1 - smoothstep(0.0, 0.12, fy) * smoothstep(0.0, 0.12, 1 - fy)
    tint = rng.uniform(-1, 1, rows)[row.astype(int)]
    fibre = noise(rng, s, s, 0.7, 6)
    weather = noise(rng, s, s, 40)
    t = np.clip(0.55 + 0.12 * tint + 0.1 * fibre + 0.5 * (over - 0.5) * strand, 0, 1)
    rgb = ramp(t, [(0, (104, 74, 42)), (0.5, (156, 118, 70)), (1, (196, 158, 100))])
    shade = gap + 0.45 * (1 - over) * (1 - strand)
    rgb = rgb * (1 - 0.65 * np.clip(shade, 0, 1)[..., None]) + np.array([52, 38, 26]) * 0.65 * np.clip(shade, 0, 1)[..., None]
    grey = smoothstep(0.6, 1.8, weather)
    rgb = rgb * (1 - 0.35 * grey[..., None]) + np.array([128, 120, 106]) * 0.35 * grey[..., None]
    height = strand * (0.6 + 0.8 * over) - 1.2 * gap + 0.15 * fibre
    return u8(np.maximum(rgb, 31)), mr_map(np.clip(0.8 + 0.1 * gap, 0, 1)), normal_map(height * 3.0, 1.0)


def rope_tex(rng, s):
    x = (np.arange(s) + 0.5) / s
    X, Y = np.meshgrid(x, x)
    strands = 0.5 + 0.5 * np.sin(2 * np.pi * (X * 3 + Y * 4))
    fibre = noise(rng, s, s, 0.6, 3)
    t = np.clip(0.5 + 0.3 * (strands - 0.5) + 0.1 * fibre, 0, 1)
    rgb = ramp(t, [(0, (92, 72, 46)), (1, (176, 146, 102))])
    return u8(rgb), mr_map(np.full((s, s), 0.9)), normal_map(strands * 4 + fibre * 0.4, 1.0)


def burlap_tex(rng, s):
    x = (np.arange(s) + 0.5) / s
    X, Y = np.meshgrid(x, x)
    weave = np.sin(X * s * np.pi / 2) * np.sin(Y * s * np.pi / 2)
    mottle = noise(rng, s, s, 20)
    t = np.clip(0.5 + 0.12 * weave + 0.15 * mottle, 0, 1)
    rgb = ramp(t, [(0, (112, 88, 58)), (1, (164, 134, 94))])
    seam = (np.abs(X - 0.5) < 0.012).astype(float)
    rgb = rgb * (1 - 0.4 * seam[..., None])
    return u8(rgb), mr_map(np.full((s, s), 0.93)), normal_map(weave * 1.5 - seam * 2, 1.0)


def white_rock_tex(rng, s):
    """P2's wind-carved pale stone: horizontal strata, grit."""
    n1, n2 = noise(rng, s, s, 30, 6), noise(rng, s, s, 2)
    strata = np.sin(np.linspace(0, 2 * np.pi * 9, s))[:, None] * 0.5 + 0.3 * noise(rng, s, s, 3, 40)
    t = np.clip(0.55 + 0.12 * n1 + 0.08 * n2 + 0.1 * strata, 0, 1)
    rgb = ramp(t, [(0, (132, 128, 122)), (0.5, (176, 172, 164)), (1, (212, 208, 198))])
    return u8(rgb), mr_map(np.clip(0.85 - 0.05 * n2, 0, 1)), normal_map(1.2 * strata + 0.5 * n1 + 0.3 * n2, 1.5)


def rounded_square(side, rc, seg):
    """Loop (counter-clockwise seen from above, as the lathe: x -> -z) of a rounded square, start at a straight's
    middle. Returns points (n, 2) as (x, z) and the perimeter length at each."""
    h = side / 2 - rc
    pts = []
    for q, (cx, cz) in enumerate(((h, -h), (-h, -h), (-h, h), (h, h))):
        a0 = q * np.pi / 2
        for k in range(seg + 1):
            a = a0 + k / seg * np.pi / 2
            pts.append((cx + rc * np.cos(a), cz - rc * np.sin(a)))
    pts = np.array(pts)
    pts = np.vstack([pts, pts[:1]])
    per = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(pts, axis=0), axis=1))])
    return pts, per


# ---------------------------------------------------------------- the torn envelope (session 13)
def wreck_wicker(wicker):
    """Scuff and darken the wicker tile (its own seed, so the rest of the basket keeps its shapes): grime, dust,
    a few broken weavers (dark gaps with frayed ends) and pale abrasion where the basket dragged on the rocks."""
    base, mr, nrm = wicker
    rng = np.random.default_rng(40582)
    s = base.shape[0]
    x = (np.arange(s) + 0.5) / s
    X, Y = np.meshgrid(x, x)
    grime = smoothstep(-0.3, 1.4, noise(rng, s, s, 30))
    dust = smoothstep(0.4, 1.8, noise(rng, s, s, 12, 40))
    rgb = base.astype(float) * 0.74
    rgb = rgb * (1 - 0.45 * grime[..., None]) + np.array([46, 38, 30]) * 0.45 * grime[..., None]
    rgb = rgb * (1 - 0.25 * dust[..., None]) + np.array([150, 136, 116]) * 0.25 * dust[..., None]
    # Broken weavers: three short gaps in the 16 rows, darker than the gaps between the strands, frayed at the ends.
    rows = 16
    row = np.floor(Y * rows)
    fy = (Y * rows) % 1.0
    broken = np.zeros((s, s))
    for r, u0, u1 in ((3, 0.18, 0.31), (9, 0.62, 0.70), (13, 0.05, 0.12)):
        fray = 0.015 * noise(rng, s, s, 1.0)
        span = smoothstep(u0 - 0.01, u0 + 0.01, X + fray) * (1 - smoothstep(u1 - 0.01, u1 + 0.01, X + fray))
        broken = np.maximum(broken, (row == r) * span * (np.sin(np.pi * fy) > 0.15))
    rgb = rgb * (1 - 0.8 * broken[..., None]) + np.array([24, 18, 14]) * 0.8 * broken[..., None]
    scuff = smoothstep(1.6, 2.4, noise(rng, s, s, 3, 26)) * (1 - broken)
    rgb = rgb * (1 - 0.3 * scuff[..., None]) + np.array([170, 150, 120]) * 0.3 * scuff[..., None]
    # Normal: flatten the broken strands into a hole.
    n = nrm.astype(float) / 127.5 - 1
    n[..., :2] *= (1 - broken[..., None])
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return u8(np.maximum(rgb, 31)), mr, u8((n * 0.5 + 0.5) * 255)


def _hull(pts):
    """Convex hull (counter-clockwise in x, z) of points (n, 2)."""
    pts = np.unique(np.round(pts, 5), axis=0)
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]

    def half(ps):
        h = []
        for p in ps:
            while len(h) >= 2 and ((h[-1] - h[-2])[0] * (p - h[-2])[1] - (h[-1] - h[-2])[1] * (p - h[-2])[0]) <= 0:
                h.pop()
            h.append(p)
        return h
    lower, upper = half(pts), half(pts[::-1])
    return np.array(lower[:-1] + upper[:-1])


def _inside(hull, q, pad):
    """q (m, 2) inside the convex hull grown by pad."""
    e = np.roll(hull, -1, axis=0) - hull
    nrm = np.stack([e[:, 1], -e[:, 0]], axis=1)
    nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
    d = np.einsum('mkj,kj->mk', q[:, None, :] - hull[None], nrm)
    return np.all(d < pad, axis=1)


def _ground_top(tris, q):
    """Highest y of the triangles (t, 3, 3) above each point q (m, 2) in x, z; 0 where none."""
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    v0 = (b - a)[:, [0, 2]]
    v1 = (c - a)[:, [0, 2]]
    den = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]
    ok = np.abs(den) > 1e-12
    a, v0, v1, den = a[ok], v0[ok], v1[ok], den[ok]
    ya, yb, yc = tris[ok, 0, 1], tris[ok, 1, 1], tris[ok, 2, 1]
    w = q[:, None, :] - a[None, :, [0, 2]]
    s = (w[..., 0] * v1[:, 1] - w[..., 1] * v1[:, 0]) / den
    t = (v0[:, 0] * w[..., 1] - v0[:, 1] * w[..., 0]) / den
    inside = (s >= -1e-6) & (t >= -1e-6) & (s + t <= 1 + 1e-6)
    y = ya + s * (yb - ya) + t * (yc - ya)
    return np.where(inside, y, 0.0).max(axis=1)


def envelope_tex(rng, size, x0, z0, span, throat, th0, th1, height_at, tears, patches):
    """The envelope's unique map (planar x, z over [x0, x0 + span] x [z0, z0 + span]): gores radiating from the
    throat in faded red and cream, dark seams, load tapes across them, canvas patches with stitched borders, ragged
    tears, grime and dust; fold valleys (from the height field) darkened."""
    s = size
    u = (np.arange(s) + 0.5) / s
    X = x0 + u[None, :] * span * np.ones((s, 1))
    Z = z0 + u[:, None] * span * np.ones((1, s))
    dx, dz = X - throat[0], Z - throat[2]
    rho = np.hypot(dx, dz)
    phi = np.arctan2(dz, dx)
    phi = np.where(phi > th1 + 0.3, phi - 2 * np.pi, phi)
    gores = 9
    gw = (th1 - th0) / gores
    g = (phi - th0) / gw
    gi = np.floor(g).astype(int)
    seam_d = np.abs(g - np.round(g)) * gw * rho                     # metres to the nearest gore seam
    mottle = noise(rng, s, s, 24)
    fine = noise(rng, s, s, 1.0)
    red = np.array([142, 54, 42], float)
    cream = np.array([196, 178, 136], float)
    ochre = np.array([170, 128, 64], float)
    pick = np.where((gi % 2) == 0, 0, 1)
    pick = np.where(gi % 5 == 3, 2, pick)
    col = np.stack([red, cream, ochre])[pick]
    col = col * (1 + 0.07 * mottle[..., None] + 0.03 * fine[..., None])
    weave = np.sin(X * 900) * np.sin(Z * 900)
    seam = np.exp(-(seam_d / 0.012) ** 2)
    tape = np.zeros((s, s))
    for rr in (0.42, 0.9, 1.38, 1.85):
        tape = np.maximum(tape, np.exp(-((rho - rr) / 0.016) ** 2))
    col = col * (1 - 0.55 * seam[..., None]) + np.array([70, 52, 38]) * 0.55 * seam[..., None]
    col = col * (1 - 0.6 * tape[..., None]) + np.array([150, 128, 96]) * 0.6 * tape[..., None]
    patch_edge = np.zeros((s, s))
    for (pcx, pcz, pw, ph, pa, pc) in patches:
        ca, sa = np.cos(pa), np.sin(pa)
        lx = (X - pcx) * ca + (Z - pcz) * sa
        lz = -(X - pcx) * sa + (Z - pcz) * ca
        inside = (np.abs(lx) < pw / 2) & (np.abs(lz) < ph / 2)
        edge = inside & ((np.abs(lx) > pw / 2 - 0.02) | (np.abs(lz) > ph / 2 - 0.02))
        stitch = edge & (np.sin((lx + lz) * 260) > 0.2)
        col[inside] = np.array(pc, float) * (1 + 0.06 * mottle[inside, None])
        col[stitch] *= 0.55
        patch_edge = np.maximum(patch_edge, edge.astype(float))
    # Grime: darker toward the throat (soot of the burner) and the ground edge (dust).
    soot = np.exp(-(rho / 0.45) ** 2) * 0.55 + 0.25 * smoothstep(0.6, 2.0, noise(rng, s, s, 40))
    col = col * (1 - soot[..., None]) + np.array([40, 34, 30]) * soot[..., None]
    dust = smoothstep(1.2, 2.1, rho) * 0.35 + 0.2 * smoothstep(0.5, 1.8, noise(rng, s, s, 14))
    col = col * (1 - dust[..., None]) + np.array([150, 132, 110]) * dust[..., None]
    # Fold valleys: the Laplacian of the height field (positive in a valley).
    hgt = height_at(X, Z)
    lap = (np.roll(hgt, 1, 0) + np.roll(hgt, -1, 0) + np.roll(hgt, 1, 1) + np.roll(hgt, -1, 1) - 4 * hgt)
    lap = lap / (span / s) ** 2
    crease = smoothstep(0.5, 6.0, lap)
    col = col * (1 - 0.45 * crease[..., None])
    hole = np.zeros((s, s))
    for (tx, tz, tr) in tears:
        d = np.hypot((X - tx) / tr[0], (Z - tz) / tr[1]) + 0.35 * noise(rng, s, s, 3)
        hole = np.maximum(hole, 1 - smoothstep(0.85, 1.0, d))
    fray = np.clip(hole * (1 - hole) * 4, 0, 1)
    col = col * (1 - hole[..., None]) + np.array([34, 26, 22]) * hole[..., None]
    col = col * (1 - 0.4 * fray[..., None]) + np.array([210, 196, 160]) * 0.4 * fray[..., None]
    height = 0.25 * weave + 0.4 * fine - 1.6 * seam + 1.2 * tape - 2.5 * hole + 0.8 * patch_edge
    return (u8(np.clip(col, 31, 236)), mr_map(np.clip(0.88 - 0.1 * seam, 0, 1)), normal_map(height * 1.5, 1.0, False,
                                                                                              False))


def envelope(mesh, corners, rim_pts):
    """The collapsed envelope behind and left of the basket (model -z and -x: away from the find in front, +z, and
    the cache chest to the right-back, +x -z), draped over the back-left rock, gores radiating from its throat by
    the basket, two torn flaps lifting from its edge; the rigging from the rim to the throat's load ring and load
    lines along two seams. Returns the envelope's (base, mr, normal) textures."""
    rng = np.random.default_rng(40581)
    wick = mesh.arrays('wicker')[0]
    hull = _hull(wick[:, [0, 2]])
    rp, _, _, ri = mesh.arrays('rock')
    rock_tris = rp[ri]
    throat = np.array([-0.30, 0.0, -0.98])
    th_c = np.arctan2(-0.80, -0.62)
    th0, th1 = th_c - np.radians(88), th_c + np.radians(70)
    cols, rows = 36, 13
    th = np.linspace(th0, th1, cols)
    # Outer radius per column: longest straight back, ragged; clipped where the ray meets the basket.
    R = 1.35 + 0.5 * np.exp(-((th - th_c - 0.15) / 0.75) ** 2) + 0.07 * rng.uniform(-1, 1, cols)
    R[[0, -1]] *= 0.75
    r0 = 0.10
    for j in range(cols):
        d = np.array([np.cos(th[j]), np.sin(th[j])])
        rs = np.linspace(r0, R[j], 60)
        q = throat[[0, 2]][None] + rs[:, None] * d
        hit = _inside(hull, q, 0.07)
        if hit.any():
            R[j] = max(rs[np.argmax(hit)] - 0.03, r0 + 0.25)
    srow = np.linspace(0, 1, rows) ** 0.85
    Rg = r0 + (R[None, :] - r0) * srow[:, None]                     # (rows, cols)
    TH = np.ones((rows, 1)) * th[None, :]

    def height_polar(rr, tt, rmax):
        rel = (tt - th_c) / (th1 - th0) * 2                         # about -1..1 across the fan
        bubble = 0.40 * np.exp(-((rr - 0.78) / 0.42) ** 2) * np.exp(-((rel + 0.1) / 0.75) ** 2)
        bubble2 = 0.24 * np.exp(-((rr - 1.45) / 0.3) ** 2) * np.exp(-((rel - 0.45) / 0.35) ** 2)
        throat_h = 0.16 * np.exp(-((rr - 0.08) / 0.22) ** 2)
        folds = (0.045 + 0.05 * np.clip(rr, 0, 1.6)) * (1 - np.abs(np.sin((tt - th0) / (th1 - th0) * np.pi * 7.5
                                                                          + 0.6 * np.sin(rr * 3.1))))
        wrinkle = 0.02 * np.sin(rr * 13 + 3 * tt) * np.clip(rr - 0.3, 0, 1)
        edge = smoothstep(0.0, 0.32, rmax - rr)
        return np.maximum((0.03 + bubble + bubble2 + throat_h + folds + wrinkle) * edge, 0.008)

    Hg = height_polar(Rg, TH, R[None, :])
    Hg[-1] = 0.006
    X = throat[0] + Rg * np.cos(TH)
    Z = throat[2] + Rg * np.sin(TH)
    # Drape over the rocks: never below a rock's top plus the cloth's clearance, blended up the rock's flanks.
    top = _ground_top(rock_tris, np.stack([X.ravel(), Z.ravel()], 1)).reshape(X.shape)
    Hg = np.where(top > 0, np.maximum(Hg, top + 0.04), Hg)
    Hg[0] = np.maximum(Hg[0], 0.12)
    P = np.stack([X, Hg, Z], axis=-1)
    # Texture domain: a square over the envelope and its flaps' unfolded extent.
    ext = np.concatenate([P.reshape(-1, 3)[:, [0, 2]],
                          throat[[0, 2]][None] + (R.max() + 0.7) * np.stack([np.cos(th), np.sin(th)], 1)])
    x0, z0 = ext.min(axis=0) - 0.05
    span = float((ext.max(axis=0) - ext.min(axis=0)).max() + 0.1)
    UV = np.stack([(X - x0) / span, (Z - z0) / span], axis=-1)
    # Rows run outward, columns by angle (z grows with it): cross(dcol, drow) points up without a flip.
    grid(mesh, 'envelope', P, UV, flip=False, smooth=True)
    nn = mesh.parts['envelope']['n'][-1]
    if nn[:, 1].mean() < 0:                                         # safety: the sheet faces up
        raise SystemExit('envelope faces down')

    # Torn flaps: panels continuing past the edge, lifted by the wind; ragged ends. (angle, width rad, length, lift)
    for fth, fw, flen, lift, lean in ((th_c + 0.25, 0.20, 0.62, 0.46, 0.25), (th_c - 0.95, 0.16, 0.45, 0.30, -0.3)):
        cs = np.linspace(fth - fw / 2, fth + fw / 2, 4)
        sr = np.linspace(0, 1, 6)
        rb = np.interp(cs, th, R) - 0.16
        Pf = np.zeros((len(sr), len(cs), 3))
        UVf = np.zeros((len(sr), len(cs), 2))
        rag = 1 + 0.18 * rng.uniform(-1, 1, len(cs))
        for j, c in enumerate(cs):
            base_h = height_polar(rb[j], c, rb[j] + 0.16)
            L = flen * rag[j]
            along = rb[j] + L * np.sin(sr * 1.3) / np.sin(1.3)
            up = base_h + lift * np.sin(np.pi * sr * 0.8) * (0.85 + 0.15 * np.cos(j))
            ang = c + lean * sr ** 2 * 0.25
            Pf[:, j, 0] = throat[0] + along * np.cos(ang)
            Pf[:, j, 1] = up
            Pf[:, j, 2] = throat[2] + along * np.sin(ang)
            unfold = rb[j] + L * sr                                 # the texture as if lying flat
            UVf[:, j, 0] = (throat[0] + unfold * np.cos(c) - x0) / span
            UVf[:, j, 1] = (throat[2] + unfold * np.sin(c) - z0) / span
        grid(mesh, 'envelope', Pf, UVf, flip=False, smooth=True)

    def surface_at(x, z):
        rr = np.hypot(x - throat[0], z - throat[2])
        tt = np.arctan2(z - throat[2], x - throat[0])
        tt = np.where(tt > th1 + 0.3, tt - 2 * np.pi, tt)
        rm = np.interp(tt, th, R)
        h = height_polar(rr, tt, rm)
        return h

    # Load ring at the throat, ropes from the rim to it, load lines lying along two gore seams.
    ring_r = 0.13
    ra = np.linspace(0, 2 * np.pi, 13)
    ring = np.stack([throat[0] + ring_r * np.cos(ra), np.full(13, 0.17) + 0.03 * np.sin(ra * 2),
                     throat[2] + ring_r * np.sin(ra)], 1)
    tube(mesh, 'rope', ring, 0.02, 5, v_scale=1 / 0.12, caps=False)
    # Rim anchors: the back-left corner, two on the back wall, one on the left wall (rim points nearest each).
    want = [corners[1], (corners[0] + corners[1]) / 2 + [0.25, 0, 0], (corners[0] + corners[1]) / 2 - [0.2, 0, 0],
            (corners[1] + corners[2]) / 2 + [0, 0, -0.15]]
    for k, wpt in enumerate(want):
        a = rim_pts[np.argmin(np.linalg.norm(rim_pts - wpt, axis=1))] + [0, 0.02, 0]
        outward = np.array([a[0], 0.0, a[2]])
        outward /= np.linalg.norm(outward)
        b = throat + [ring_r * np.cos(1.2 * k + 1.0), 0.17, ring_r * np.sin(1.2 * k + 1.0)]
        sN = np.linspace(0, 1, 9)
        pts = a[None] * (1 - sN[:, None]) + b[None] * sN[:, None]
        pts += outward[None] * (0.06 * np.sin(np.pi * sN))[:, None]          # off the wall
        pts[:, 1] -= 0.16 * np.sin(np.pi * sN) * (1 - sN * 0.5)              # slack
        floor = surface_at(pts[:, 0], pts[:, 2]) + 0.025
        pts[:, 1] = np.maximum(pts[:, 1], np.where(np.hypot(pts[:, 0] - throat[0], pts[:, 2] - throat[2]) < 2.5,
                                                   floor, 0.02))
        tube(mesh, 'rope', pts, 0.017, 5, v_scale=1 / 0.12)
    for g in (3, 6):
        tt = th0 + (th1 - th0) * g / 9
        rr = np.linspace(ring_r + 0.02, 1.0 + 0.25 * g / 9, 7)
        x, z = throat[0] + rr * np.cos(tt), throat[2] + rr * np.sin(tt)
        y = surface_at(x, z) + 0.018
        y = np.maximum(y, _ground_top(rock_tris, np.stack([x, z], 1)) + 0.055)
        tube(mesh, 'rope', np.stack([x, y, z], 1), 0.012, 4, v_scale=1 / 0.12)
    # Splintered stakes sticking up from the rim at the low corner and the back wall.
    for idx in (5, 14, 23):
        a = rim_pts[idx % len(rim_pts)]
        d = np.array([0.02 * rng.uniform(-1, 1), 1.0, 0.02 * rng.uniform(-1, 1)])
        lean = np.array([a[0], 0, a[2]]) / np.linalg.norm([a[0], a[2]]) * 0.35
        pts = np.stack([a - [0, 0.04, 0], a + (d + lean) * 0.07, a + (d + lean * 1.4) * 0.13])
        tube(mesh, 'wicker', pts, np.array([0.011, 0.009, 0.003]), 4, v_scale=1 / 0.42)

    tears = [(throat[0] + r * np.cos(t), throat[2] + r * np.sin(t), (rx, rz))
             for r, t, rx, rz in ((1.05, th_c + 0.5, 0.13, 0.08), (0.62, th_c - 0.45, 0.09, 0.06),
                                  (1.6, th_c - 0.15, 0.16, 0.07), (1.25, th_c - 1.05, 0.08, 0.1))]
    patches = [(throat[0] + r * np.cos(t), throat[2] + r * np.sin(t), w_, h_, a_, c_)
               for r, t, w_, h_, a_, c_ in ((0.8, th_c + 0.1, 0.22, 0.16, 0.3, (150, 128, 90)),
                                            (1.3, th_c + 0.65, 0.18, 0.24, -0.4, (120, 96, 70)),
                                            (1.15, th_c - 0.6, 0.26, 0.14, 0.9, (168, 150, 112)),
                                            (0.45, th_c + 0.9, 0.14, 0.12, 0.1, (110, 70, 52)),
                                            (1.7, th_c + 0.2, 0.2, 0.2, 0.6, (176, 160, 120)))]

    def height_xz(x, z):
        return surface_at(x, z)
    return envelope_tex(rng, 1024, x0, z0, span, throat, th0, th1, height_xz, tears, patches)


def build_basket():
    out = HERE / 'work' / 'basket'
    rng = np.random.default_rng(4058)
    wicker = wicker_tex(rng, 512)
    rope = rope_tex(rng, 128)
    burlap = burlap_tex(rng, 256)
    rock = white_rock_tex(rng, 512)
    for k, img in dict(wicker_base=wicker[0], wicker_mr=wicker[1], wicker_normal=wicker[2], rope_base=rope[0],
                       rope_normal=rope[2], burlap_base=burlap[0], burlap_normal=burlap[2], rock_base=rock[0],
                       rock_normal=rock[2]).items():
        save(out, k, img)
    mesh = Mesh()
    tile = 0.42                                             # metres of wicker per texture tile
    H, rc, seg = 1.04, 0.15, 4
    levels = [(0.0, 1.18), (0.5, 1.26), (H, 1.30)]

    def ring(side, y, inset=0.0):
        pts, per = rounded_square(side - 2 * inset, rc - inset, seg)
        return np.stack([pts[:, 0], np.full(len(pts), y), pts[:, 1]], axis=1), per

    outer = [ring(s, y) for y, s in levels]
    P = np.stack([o[0] for o in outer])
    per = outer[-1][1]
    UV = np.stack([np.stack([per / tile, np.full(len(per), y / tile)], 1) for y, _ in levels])
    grid(mesh, 'wicker', P, UV, flip=False, smooth=True, wrap_u=True)
    t = 0.045
    inner_levels = [(H, 1.30), (0.5, 1.26), (0.06, 1.19)]
    inner = [ring(s, y, t) for y, s in inner_levels]
    P = np.stack([o[0] for o in inner])
    UV = np.stack([np.stack([per / tile, np.full(len(per), y / tile)], 1) for y, _ in inner_levels])
    grid(mesh, 'wicker', P, UV, flip=False, smooth=True, wrap_u=True)
    # Floor inside (up) and the base under (down): rings of the rounded square shrinking to a strip-split centre.
    for y, side, up in ((0.06, 1.19 - 2 * t, True), (0.0, 1.18, False)):
        loops = [ring(side * f, y)[0][:-1] for f in (1.0, 0.55)]
        pts = np.vstack(loops)
        n = len(loops[0])
        tris = []
        for j in range(n):
            a, b = j, (j + 1) % n
            tris += [(a, b, n + b), (a, n + b, n + a)]
        left, right, order = 0, n - 1, []
        while left <= right:
            order.append(left)
            if left != right:
                order.append(right)
            left += 1
            right -= 1
        tris += [(n + order[k], n + order[k + 1], n + order[k + 2]) for k in range(len(order) - 2)]
        T = np.array(tris)
        fn = np.cross(pts[T[:, 1]] - pts[T[:, 0]], pts[T[:, 2]] - pts[T[:, 0]])
        bad = fn[:, 1] * (1 if up else -1) < 0
        T[bad] = T[bad][:, ::-1]
        mesh.add('wicker', pts, np.tile([0, 1.0 if up else -1.0, 0], (len(pts), 1)), pts[:, [0, 2]] / tile, T)
    # The rim: a thick rope binding over the wall's top.
    rim, _ = ring(1.30, H + 0.012, t / 2)
    tube(mesh, 'rope', rim[:-1].tolist() + [rim[0].tolist(), rim[1].tolist()], 0.036, 6, u_tiles=1.0, v_scale=1 / 0.12,
         caps=False)
    corners_local = [ring(1.30, H + 0.03, 0.03)[0][k * (seg + 1) + seg // 2] for k in range(4)]
    # Tilt: wedged, one side (+x) raised about 17 degrees on a rock, a little roll forward as well.
    roll, pitch = np.radians(17.0), np.radians(5.0)

    def tilt(p):
        q = p.copy()
        c, s = np.cos(roll), np.sin(roll)
        q[:, 0], q[:, 1] = p[:, 0] * c - p[:, 1] * s, p[:, 0] * s + p[:, 1] * c
        c2, s2 = np.cos(pitch), np.sin(pitch)
        r = q.copy()
        r[:, 1], r[:, 2] = q[:, 1] * c2 - q[:, 2] * s2, q[:, 1] * s2 + q[:, 2] * c2
        return r
    mesh.transform(tilt)
    lo, _ = mesh.bounds()
    drop = -lo[1] - 0.01                                    # the low corner a centimetre into the ground
    mesh.transform(lambda p: p + [0, drop, 0])
    corners = tilt(np.array(corners_local)) + [0, drop, 0]
    # Ropes at the four corners (world space after the tilt): two snapped short above the rim, two hanging over the
    # side to the ground.
    for k, c in enumerate(corners):
        out_dir = np.array([c[0], 0.0, c[2]])
        out_dir /= np.linalg.norm(out_dir)
        if k == 1:
            continue                                    # the back-left corner's rope runs to the envelope (below)
        if k in (0, 2):
            length = 0.2 if k == 0 else 0.13
            s = np.linspace(0, 1, 6)
            pts = c + np.outer(s, [0.0, length, 0.0]) + np.outer(s ** 2, out_dir * 0.08 + [0, -0.04, 0])
            tube(mesh, 'rope', pts, np.linspace(0.016, 0.011, 6), 5, v_scale=1 / 0.12)
        else:
            s = np.linspace(0, 1, 8)
            reach = 0.16 + 0.05 * k
            ground = max(c[1] - 0.02, 0.05)
            pts = np.stack([c[0] + out_dir[0] * reach * np.sin(s * np.pi / 2) * 1.0,
                            c[1] - ground * s ** 1.6 + 0.04 * np.sin(s * np.pi),
                            c[2] + out_dir[2] * reach * np.sin(s * np.pi / 2)], axis=1)
            pts[-1, 1] = 0.02
            tube(mesh, 'rope', pts, 0.015, 5, v_scale=1 / 0.12)
    # Sandbags: one hanging on its rope over the raised side's wall, one dropped on the ground at the low side.
    high = tilt(np.array([[0.70, H - 0.02, -0.25]]))[0] + [0, drop, 0]
    bag1 = high + [0.17, -0.42, 0.0]
    ellipsoid(mesh, 'burlap', bag1, (0.12, 0.17, 0.11), 6, 8, rng=rng, jitter=0.05, uv_tiles=(1.0, 1.0))
    tube(mesh, 'rope', np.array([high + [0.02, 0.03, 0], high + [0.11, 0.02, 0], bag1 + [0, 0.24, 0],
                                 bag1 + [0, 0.15, 0]]), 0.012, 5, v_scale=1 / 0.12)
    ellipsoid(mesh, 'burlap', (-0.92, 0.09, 0.36), (0.18, 0.11, 0.13), 6, 8, rng=rng, jitter=0.06,
              uv_tiles=(1.0, 1.0), squash_bottom=0.75)
    # Rocks: the one the raised side rests on, a smaller one wedged at the low side.
    # The base's height under the wedge rock (the tilted bottom plane at x, z): the rock's top reaches 3 cm into it.
    rx, rz = 0.42, 0.0
    base = tilt(np.array([[rx, 0.0, rz]]))[0] + [0, drop, 0]
    ry = (base[1] + 0.03) / 1.0
    ellipsoid(mesh, 'rock', (base[0] + 0.05, 0.0, base[2]), (0.36, ry, 0.62), 6, 8, rng=rng, jitter=0.12, flat=True,
              uv_tiles=(3.0, 1.2), squash_bottom=0.02)
    ellipsoid(mesh, 'rock', (base[0] + 0.42, 0.0, base[2] + 0.3), (0.2, 0.17, 0.22), 4, 6, rng=rng, jitter=0.2,
              flat=True, uv_tiles=(1.5, 0.6), squash_bottom=0.02)
    # The highest corner (+x, -z: the roll and the pitch both lift it) gets its own stone under it.
    corner = tilt(np.array([[0.5, 0.0, -0.5]]))[0] + [0, drop, 0]
    ellipsoid(mesh, 'rock', (corner[0] + 0.04, 0.0, corner[2] - 0.02), (0.24, corner[1] + 0.04, 0.26), 4, 6, rng=rng,
              jitter=0.12, flat=True, uv_tiles=(1.5, 0.8), squash_bottom=0.02)
    ellipsoid(mesh, 'rock', (-0.62, 0.0, -0.78), (0.34, 0.24, 0.26), 5, 7, rng=rng, jitter=0.2, flat=True,
              uv_tiles=(2.0, 0.8), squash_bottom=0.02)
    lo, hi = mesh.bounds()
    shift = np.array([-(lo[0] + hi[0]) / 2, -lo[1], -(lo[2] + hi[2]) / 2])
    mesh.transform(lambda p: p + shift)
    # Session 13: the torn envelope, its rigging and the splintered rim, added after the shift so the basket, its
    # rocks and the origin stay where the map lanes placed them (the bounds' centre moves; the origin does not).
    env = envelope(mesh, corners + shift, rim_pts=tilt(np.array(rim[:-1]))[:, :] + [0, drop, 0] + shift)
    wicker = wreck_wicker(wicker)
    save(out, 'wicker_base', wicker[0])
    save(out, 'wicker_normal', wicker[2])
    glb = Glb('xeen_planedevices_claude build.py')
    glb.material('xeen_basket_wicker', wicker[0], wicker[1], wicker[2], extras={'openyamm_specular': 0.25})
    glb.material('xeen_basket_rope', rope[0], rope[1], rope[2], extras={'openyamm_specular': 0.15})
    glb.material('xeen_basket_burlap', burlap[0], burlap[1], burlap[2], extras={'openyamm_specular': 0.1})
    glb.material('xeen_basket_rock', rock[0], rock[1], rock[2], extras={'openyamm_specular': 0.3})
    glb.material('xeen_basket_envelope', env[0], env[1], env[2], double=True, extras={'openyamm_specular': 0.2})
    for k, img in dict(envelope_base=env[0], envelope_normal=env[2]).items():
        save(out, k, img)
    glb.mat_index = {'wicker': 0, 'rope': 1, 'burlap': 2, 'rock': 3, 'envelope': 4}
    finish('balloonbasket', out, mesh, glb, ['wicker', 'rope', 'burlap', 'rock', 'envelope'],
           {'shift_m': shift.round(4).tolist()})


if __name__ == '__main__':
    which = sys.argv[1] if len(sys.argv) > 1 else 'all'
    for name, fn in (('font', build_font), ('camp', build_camp), ('basket', build_basket)):
        if which in (name, 'all'):
            fn()
