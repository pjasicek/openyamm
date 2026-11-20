"""m270 prop, modelled from the native frames (no Meshy): the lich's staff (m270sa0-4, aa-af: a thin dark wooden shaft
about 0.95 of the lich's height, gold pointed foot, gold collars, a gold crescent cage of two upswept horns holding a
red orb). Gripped 0.63 of the way up from the foot. Writes work/props.blend with 'SwordMesh' (the staff) in prop
space: +Y along the shaft from the handle centre toward the orb (orb top at +0.62, foot at -1.00), X and Z across;
and the props atlas textures/m270_props_{basecolor,normal,metal_rough}.png (512 px; swatch rectangles, own paint).
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
# m270 swatches: 'shaft' dark wood, 'steel' gold fittings, 'pommel' red orb
rng = np.random.default_rng(270)
img = np.zeros((N, N, 3)); spec = np.zeros((N, N)); rough = np.zeros((N, N))


def rect(k):
    u0, v0, u1, v1 = SW[k]
    return slice(int((1 - v1) * N), int((1 - v0) * N)), slice(int(u0 * N), int(u1 * N))


def fill(k, col, noise, s, r):
    ys, xs = rect(k); h, w = ys.stop - ys.start, xs.stop - xs.start
    n = rng.normal(0, noise, (h, w, 1))
    img[ys, xs] = np.clip(np.array(col) / 255 + n, 0, 1); spec[ys, xs] = s; rough[ys, xs] = r


fill('grip', (60, 40, 26), 0.03, 0.2, 0.7)
fill('steel', (214, 150, 52), 0.035, 1.0, 0.3)
fill('pommel', (190, 16, 20), 0.03, 0.9, 0.15)
fill('blade', (196, 198, 205), 0.025, 0.9, 0.3)
fill('edge', (226, 228, 232), 0.02, 1.0, 0.25)
fill('shaft', (64, 42, 28), 0.03, 0.25, 0.7)
fill('fletch', (225, 228, 238), 0.025, 0.15, 0.8)
fill('nock', (120, 128, 150), 0.03, 0.3, 0.6)
# shaft: wood grain along the length (u)
ys, xs = rect('shaft'); h, w = ys.stop - ys.start, xs.stop - xs.start
img[ys, xs] *= (0.85 + 0.15 * np.sin(np.linspace(0, 40, h))[:, None, None] * np.sin(np.linspace(0, 7, w))[None, :, None])
# orb: a soft highlight toward the top of its swatch
ys, xs = rect('pommel'); h, w = ys.stop - ys.start, xs.stop - xs.start
yy, xx = np.mgrid[0:h, 0:w] / max(h, w)
img[ys, xs] = np.clip(img[ys, xs] + 0.35 * np.exp(-((yy - 0.3) ** 2 + (xx - 0.35) ** 2) / 0.02)[..., None] * np.array([1, 0.6, 0.6]), 0, 1)


def save_png(a, name, srgb=True):
    im = bpy.data.images.new(name, N, N, alpha=True)
    im.colorspace_settings.name = 'sRGB' if srgb else 'Non-Color'
    px = np.ones((N, N, 4)); px[..., :3] = np.clip(np.round(a * 255) / 255, 0, 1)
    im.pixels.foreach_set(px[::-1].ravel().astype(np.float32))     # Blender images are stored bottom-up
    im.filepath_raw = os.path.join(T, name); im.file_format = 'PNG'; im.save()


save_png(img, 'm270_props_basecolor.png')
save_png(np.broadcast_to(np.array([0.5, 0.5, 1.0]), (N, N, 3)).copy(), 'm270_props_normal.png', False)
save_png(np.stack([spec, rough, np.zeros_like(spec)], -1), 'm270_props_metal_rough.png', False)
json.dump(SW, open(os.path.join(T, 'm270_props_swatches.json'), 'w'), indent=1)

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
# ---------------------------------------------------------------- staff (prop space)
s = Mesh()
FOOT, TOP = -1.00, 0.50
tube(s, [(Y * y, Y, X) for y in np.linspace(FOOT + 0.06, TOP - 0.03, 9)], [0.0135] * 9, 'shaft', n=8)
tube(s, [(Y * y, Y, X) for y in (FOOT, FOOT + 0.035, FOOT + 0.07)], [0.002, 0.012, 0.016], 'steel', n=8)   # gold foot
for yc in (-0.55, -0.10, 0.12, 0.40):                                              # gold collars
    tube(s, [(Y * y, Y, X) for y in (yc - 0.02, yc, yc + 0.02)], [0.016, 0.02, 0.016], 'steel', n=8)
tube(s, [(Y * y, Y, X) for y in (TOP - 0.04, TOP, TOP + 0.02)], [0.016, 0.026, 0.018], 'steel', n=8)  # cup under the cage
# crescent cage: two horns curving up and in around the orb (in the X-Y plane), a third pair in Z
OC, OR = Y * (TOP + 0.075), 0.042
for ax_ in (X, Z):
    for sgn in (-1, 1):
        pts = []
        for t in np.linspace(0, 1, 6):
            a_ = math.radians(-70 + 160 * t)
            pts.append(OC + (ax_ * (sgn * math.cos(a_)) + Y * math.sin(a_)) * (OR + 0.022) - Y * 0.01 * (1 - t))
        path = [(p, (q - p).normalized(), (Z if ax_ is X else X)) for p, q in zip(pts[:-1], pts[1:])] + [(pts[-1], (pts[-1] - pts[-2]).normalized(), (Z if ax_ is X else X))]
        tube(s, path, [0.008, 0.0075, 0.007, 0.006, 0.005, 0.003], 'steel', n=6)
# the orb: a low-poly UV sphere
lat, lon = 6, 10
rings_ = []
for i in range(1, lat):
    th = math.pi * i / lat
    rings_.append(s.add([OC + (X * (math.sin(th) * math.cos(2 * math.pi * j / lon)) + Z * (math.sin(th) * math.sin(2 * math.pi * j / lon)) + Y * math.cos(th)) * OR for j in range(lon)]))
top_ = s.add([OC + Y * OR]); bot_ = s.add([OC - Y * OR])
for r0, r1 in zip(rings_[:-1], rings_[1:]):
    for j in range(lon):
        s.face((r0 + j, r1 + j, r1 + (j + 1) % lon, r0 + (j + 1) % lon), 'pommel', [(0, 0), (0, 1), (1, 1), (1, 0)])
for j in range(lon):
    s.face((top_, rings_[0] + j, rings_[0] + (j + 1) % lon), 'pommel', [(0.5, 0.0), (0, 1), (1, 1)])
    s.face((bot_, rings_[-1] + (j + 1) % lon, rings_[-1] + j), 'pommel', [(0.5, 1.0), (1, 0), (0, 0)])
sword = s.build('SwordMesh')
print('PROP', sword.name, sum(len(p.vertices) - 2 for p in sword.data.polygons), 'tris')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'props.blend'))
