"""Bell buoy 7dec33: a wooden barrel with two dark corroded bands, an open top, six brass straps rising in a tapering
cage with two flat hoops, a copper dome on top, and a brass bell hanging inside from a crossbar with its clapper
below, traced from the restored native frames (x2 pixels at 0.5 units). Every material sways with openyamm_wind (the
native frames rock the whole buoy). Writes work/buoy_export.glb.
Usage: blender --background --python build_buoy.py"""
import math
import os
import sys

from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import firelib as fl  # noqa: E402

pl = fl.pl
pl.reset()
WIND = {'openyamm_wind': 0.1}
mats = {'Staves': fl.material('Staves', 'staves', extras=dict(WIND, openyamm_specular=0.3)),
        'Bands': fl.material('Bands', 'bandiron', extras=dict(WIND)),
        'Brass': fl.material('Brass', 'gold', extras=dict(WIND, openyamm_specular=0.8)),
        'Hoops': fl.material('Hoops', 'gold', extras=dict(WIND, openyamm_specular=0.8)),
        'Bell': fl.material('Bell', 'gold', extras=dict(WIND, openyamm_specular=0.8)),
        'Copper': fl.material('Copper', 'copper', extras=dict(WIND, openyamm_specular=0.9))}

BARREL = [(0, 0.5), (35, 0.5), (37, 0), (39.5, 3), (41, 12), (42, 25), (42.3, 40), (41.5, 55), (40.5, 70),
          (38.5, 85), (36.5, 98), (36, 103), (34.5, 103), (34.3, 96), (0, 96)]
BELL = [(0, 160), (6.5, 158.5), (7.5, 152), (8, 146), (9, 139), (10.5, 134), (12.5, 130.5), (14.5, 128),
        (15, 129.5), (13.5, 131), (11.5, 134), (10, 139), (9.2, 146), (8.8, 153), (8.2, 159), (7, 163.5),
        (4.5, 166), (0, 167)]
BELL = [(r * 1.3, z) for r, z in BELL]          # the native bell is broad: lip about 38 units across
DOME = [(0, 212.5), (17.5, 212.5), (17.5, 216), (16.5, 221), (14, 226), (10, 230.5), (5, 233.8), (0, 235)]
BAR_BOTTOM, BAR_TOP = (34.0, 101.0), (21.0, 212.5)


def barrel_radius(z):
    for (r0, z0), (r1, z1) in zip(BARREL[2:11], BARREL[3:12]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return 36.0


def bar_radius(z):
    t = (z - BAR_BOTTOM[1]) / (BAR_TOP[1] - BAR_BOTTOM[1])
    return BAR_BOTTOM[0] + (BAR_TOP[0] - BAR_BOTTOM[0]) * t


def band(name, z0, z1, mat, seg, radius=None, thickness=1.8, simple=False):
    """A flat band round the barrel (or the cage, with a fixed radius): proud by `thickness`, slightly bevelled."""
    r0 = radius if radius is not None else barrel_radius(z0)
    r1 = radius if radius is not None else barrel_radius(z1)
    inner = 0.0 if radius is None else 1.6
    profile = [(r0 - inner, z0), (r0 + thickness * 0.6, z0), (r0 + thickness, z0 + 0.8),
               (r1 + thickness, z1 - 0.8), (r1 + thickness * 0.6, z1), (r1 - inner, z1)]
    if simple:
        profile = [profile[0], profile[2], profile[3], profile[5]]
    if radius is not None:
        profile.append((r0 - inner, z0))
    return fl.lathe(name, profile, seg, mat, u_repeat=3, v_scale=3)


def build(level):
    seg = (24, 12, 8)[level]
    coarse = level == 2
    solids = [fl.lathe('barrel', BARREL[::2] + [BARREL[-1]] if coarse else BARREL, seg, mats['Staves'],
                       u_repeat=2, v_scale=0.6),
              band('band_low', 27.5, 37.0, mats['Bands'], seg, simple=coarse),
              band('band_top', 93.0, 101.0, mats['Bands'], seg, simple=coarse),
              fl.lathe('dome', DOME[::2] + [DOME[-1]] if coarse else DOME, max(seg - 6, 6), mats['Copper'],
                       u_repeat=2, v_scale=2)]
    hoop_seg = max(seg - 4, 6)
    solids.append(band('hoop_mid', 177.0, 184.0, mats['Hoops'], hoop_seg, radius=bar_radius(180.5) + 0.6,
                       thickness=1.4, simple=level > 0))
    solids.append(band('hoop_top', 206.0, 213.0, mats['Hoops'], hoop_seg, radius=bar_radius(209.5) + 0.6,
                       thickness=1.4, simple=level > 0))
    bars = 6
    for k in range(bars):
        a = 2 * math.pi * k / bars
        p0 = (BAR_BOTTOM[0] * math.cos(a), BAR_BOTTOM[0] * math.sin(a), BAR_BOTTOM[1] - 6)
        p1 = (BAR_TOP[0] * math.cos(a), BAR_TOP[0] * math.sin(a), BAR_TOP[1])
        bar = fl.tube(f'bar{k}', p0, p1, 3.0, 2.6, 3 if coarse else 4, mats['Brass'], caps=level == 0)
        solids.append(bar)
    if level < 2:
        solids.append(fl.lathe('bell', BELL, (16, 10)[level], mats['Bell'], u_repeat=2, v_scale=3))
        solids.append(fl.tube('crossbar', (-bar_radius(180.5), 0, 180.5), (bar_radius(180.5), 0, 180.5), 1.3, 1.3,
                              (6, 4)[level], mats['Brass'], caps=False))
        solids.append(fl.tube('hanger', (0, 0, 166.5), (0, 0, 180.5), 1.1, 1.1, (6, 4)[level], mats['Bell'],
                              caps=False))
        loop = fl.torus('loop', 3.2, 0.9, 0.0, (10, 6)[level], 4, mats['Bell'])
        loop.matrix_world = Matrix.Translation((0, 0, fl.u(171.0))) @ Matrix.Rotation(math.pi / 2, 4, 'X')
        solids.append(fl.apply([loop])[0])
        solids.append(fl.tube('clapper', (0, 0, 159), (0, 0, 113), 0.9, 0.9, (5, 3)[level], mats['Bell'],
                              caps=False))
        ball = fl.lathe('ball', [(0, 108), (2.5, 109), (3.4, 112), (2.5, 115), (0, 116)], (8, 6)[level],
                        mats['Bell'])
        solids.append(ball)
    else:
        solids.append(fl.lathe('bell', BELL[7:][::2] + [BELL[-1]], 6, mats['Bell'], u_repeat=2, v_scale=3))
    return solids, []


# Native colours (7dec33a): orange staves, near-black corroded bands, brown-orange straps, brass hoops and bell,
# pale copper dome.
STAVES = [(0, (150, 88, 38)), (20, (165, 95, 42)), (60, (178, 108, 50)), (90, (186, 116, 56)), (103, (175, 105, 48))]
colours = {'Staves': lambda co, n: fl.stops(STAVES, co.z) if co.z > 96.5 or n.z < 0.5 else (60, 40, 25),
           'Bands': (58, 40, 26),
           'Brass': (150, 92, 45),
           'Hoops': (180, 140, 76),
           'Bell': (190, 150, 82),
           'Copper': (215, 150, 105)}
fl.build_lods('Buoy', 'buoy', build, colours, rays=(32, 20, 12), distance=20.0, strength=0.5, sharp=40,
              merge={'Hoops': 'Brass', 'Bell': 'Brass'})
