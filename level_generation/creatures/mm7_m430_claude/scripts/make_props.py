"""m430 prop, modelled from the native frames (no Meshy): the dagger (m430sa0-4, aa-af: short straight silver blade
whose lower half is stained red, small dark crossguard, black-brown grip and pommel; blade ~0.26 m at the wight's
scale). Writes work/props.blend with 'SwordMesh' (the dagger) in sword space: +Y along the blade from the handle
centre (tip at +0.31), X across the blade (edges), Z the blade's flat normal; and the props atlas
textures/m430_props_{basecolor,normal,metal_rough}.png (512 px; swatch rectangles, our own paint).
Args: none"""
import bpy, bmesh, os, sys, math, json
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(HERE, 'textures'); os.makedirs(T, exist_ok=True)
N = 512
# ---------------------------------------------------------------- atlas (u0, v0, u1, v1) in 0..1, v up
SW = {'grip': (0.0, 0.0, 0.25, 0.25), 'steel': (0.25, 0.0, 0.5, 0.25), 'pommel': (0.5, 0.0, 0.75, 0.25),
      'blade': (0.0, 0.5, 1.0, 0.75), 'edge': (0.0, 0.75, 1.0, 1.0),
      'shaft': (0.0, 0.25, 1.0, 0.375), 'fletch': (0.0, 0.375, 0.5, 0.5), 'nock': (0.5, 0.375, 0.75, 0.5)}
rng = np.random.default_rng(430)
img = np.zeros((N, N, 3)); spec = np.zeros((N, N)); rough = np.zeros((N, N))


def rect(k):
    u0, v0, u1, v1 = SW[k]
    return slice(int((1 - v1) * N), int((1 - v0) * N)), slice(int(u0 * N), int(u1 * N))


def fill(k, col, noise, s, r):
    ys, xs = rect(k); h, w = ys.stop - ys.start, xs.stop - xs.start
    n = rng.normal(0, noise, (h, w, 1))
    img[ys, xs] = np.clip(np.array(col) / 255 + n, 0, 1); spec[ys, xs] = s; rough[ys, xs] = r


fill('grip', (40, 30, 24), 0.03, 0.2, 0.8)
fill('steel', (60, 50, 44), 0.03, 0.5, 0.45)
fill('pommel', (55, 45, 40), 0.03, 0.5, 0.45)
fill('blade', (196, 198, 205), 0.025, 0.9, 0.3)
fill('edge', (226, 228, 232), 0.02, 1.0, 0.25)
fill('shaft', (176, 160, 128), 0.03, 0.25, 0.7)
fill('fletch', (225, 228, 238), 0.025, 0.15, 0.8)
fill('nock', (120, 128, 150), 0.03, 0.3, 0.6)
# blade: the outer half (toward the tip, u > 0.3; m430sa2: red over ~80 % of the visible blade) soaked red with a ragged boundary, as in the native frames
for k in ('blade', 'edge'):
    ys, xs = rect(k); h, w = ys.stop - ys.start, xs.stop - xs.start
    u = np.linspace(0, 1, w)[None, :]; v = np.linspace(0, 1, h)[:, None]
    edge = 0.3 + 0.06 * np.sin(v * 17 + 1.3) + 0.03 * np.sin(v * 41)
    m = np.clip((u - edge) / 0.05, 0, 1)[..., None] * (0.92 if k == 'blade' else 0.8)
    img[ys, xs] = img[ys, xs] * (1 - m) + np.array([0.62, 0.03, 0.03]) * m
# grip: wrap bands
ys, xs = rect('grip'); h = ys.stop - ys.start
img[ys, xs] *= (0.82 + 0.18 * (np.sin(np.linspace(0, 16 * np.pi, h)) > 0))[:, None, None]
def save_png(a, name, srgb=True):
    im = bpy.data.images.new(name, N, N, alpha=True)
    im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
    px = np.ones((N, N, 4)); px[..., :3] = np.clip(np.round(a * 255) / 255, 0, 1)
    im.pixels.foreach_set(px[::-1].ravel().astype(np.float32))     # Blender images are stored bottom-up
    im.filepath_raw = os.path.join(T, name); im.file_format = 'PNG'; im.save()


save_png(img, 'm430_props_basecolor.png')
save_png(np.broadcast_to(np.array([0.5, 0.5, 1.0]), (N, N, 3)).copy(), 'm430_props_normal.png', False)
save_png(np.stack([spec, rough, np.zeros_like(spec)], -1), 'm430_props_metal_rough.png', False)
json.dump(SW, open(os.path.join(T, 'm430_props_swatches.json'), 'w'), indent=1)

# ---------------------------------------------------------------- geometry helpers
bpy.ops.wm.read_factory_settings(use_empty=True)


class Mesh:
    def __init__(s):
        s.v, s.f, s.uv, s.k, s.g = [], [], [], [], []

    def add(s, ps, g=None):
        s.v.extend(ps); s.g.extend([g] * len(ps)); return len(s.v) - len(ps)

    def face(s, idx, k, uvs):
        s.f.append(tuple(idx)); s.k.append(k); s.uv.append(uvs)

    def build(s, name):
        me = bpy.data.meshes.new(name); me.from_pydata([tuple(p) for p in s.v], [], s.f); me.update()
        uvl = me.uv_layers.new(name='UVMap').data
        for p, k, uvs in zip(me.polygons, s.k, s.uv):
            u0, v0, u1, v1 = SW[k]
            for li, (a, b) in zip(p.loop_indices, uvs):
                uvl[li].uv = (u0 + (u1 - u0) * (0.04 + 0.92 * a), v0 + (v1 - v0) * (0.04 + 0.92 * b))
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        for p, k in zip(me.polygons, s.k):
            p.use_smooth = k in ('grip', 'pommel', 'shaft')
        return ob


def tube(m, path, radii, k, n=8, g=None, caps=True):
    """path: list of (centre Vector, axis Vector, side Vector); rings of n vertices"""
    rings = []
    for (c, ax, sd), r in zip(path, radii):
        w = ax.cross(sd)
        rings.append(m.add([c + (sd * math.cos(2 * math.pi * i / n) + w * math.sin(2 * math.pi * i / n)) * r for i in range(n)], g))
    for j, (i0, i1) in enumerate(zip(rings[:-1], rings[1:])):
        for i in range(n):
            a, b = i / n, (i + 1) / n; t0, t1 = j / (len(rings) - 1), (j + 1) / (len(rings) - 1)
            m.face((i0 + i, i1 + i, i1 + (i + 1) % n, i0 + (i + 1) % n), k, [(t0, a), (t1, a), (t1, b), (t0, b)])
    if caps:
        m.face([rings[0] + i for i in range(n)][::-1], k, [(0.5 + 0.4 * math.cos(2 * math.pi * i / n), 0.5) for i in range(n)][::-1])
        m.face([rings[-1] + i for i in range(n)], k, [(0.5 + 0.4 * math.cos(2 * math.pi * i / n), 0.5) for i in range(n)])


X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
# ---------------------------------------------------------------- dagger (sword space)
s = Mesh()
tube(s, [(Y * y, Y, X) for y in (-0.05, -0.02, 0.0, 0.02, 0.042)], [0.011, 0.012, 0.012, 0.012, 0.0115], 'grip')
tube(s, [(Y * y, Y, X) for y in (-0.068, -0.06, -0.05)], [0.012, 0.015, 0.011], 'pommel')
for sgn in (-1, 1):
    tube(s, [(Y * 0.048 + X * (sgn * x), X * sgn, Z) for x in (0.0, 0.025, 0.042)], [0.009, 0.008, 0.006], 'steel', n=6)
L0, L1, TIP = 0.054, 0.27, 0.31
rings = []
for j, t in enumerate(np.linspace(0, 1, 6)):
    y = L0 + (L1 - L0) * t; w = 0.016 - 0.004 * t; th = 0.0035 - 0.001 * t
    rings.append((s.add([Y * y + X * w, Y * y + Z * th, Y * y - X * w, Y * y - Z * th]), t))
tip = s.add([Y * TIP])
for (r0, t0), (r1, t1) in zip(rings[:-1], rings[1:]):
    for i in range(4):
        k = 'edge' if i in (0, 3) else 'blade'
        s.face((r0 + i, r1 + i, r1 + (i + 1) % 4, r0 + (i + 1) % 4), k, [(t0, 0.1 + 0.2 * i), (t1, 0.1 + 0.2 * i), (t1, 0.3 + 0.2 * i), (t0, 0.3 + 0.2 * i)])
for i in range(4):
    s.face((rings[-1][0] + i, tip, rings[-1][0] + (i + 1) % 4), 'edge', [(0.92, 0.2), (1.0, 0.5), (0.92, 0.8)])
s.face([rings[0][0] + i for i in range(4)][::-1], 'steel', [(0.5, 0.2), (0.8, 0.5), (0.5, 0.8), (0.2, 0.5)])
sword = s.build('SwordMesh')
print('PROP', sword.name, sum(len(p.vertices) - 2 for p in sword.data.polygons), 'tris')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'props.blend'))
