"""Step 2 (Treant): replace Smart Topology's needle teeth with peg teeth (native: few broad, pale, uneven pegs) and drop
three sliver fragments at the mouth corners. work/step1.blend -> work/step2.blend.
- Meshy returned 30 needle teeth (pieces 107-135, 139; 3 cm wide, 10-25 cm long on the 4 m tree): 14 upper, 16 lower.
- Each row's root curve (the gum end of every needle) and tip direction are fitted from those needles; N_UPPER / N_LOWER
  pegs are spaced evenly along it (elliptic section, wider than deep, rounded tip, lengths from the needles).
- Pieces 136-138 (8, 6, 5 vertices, 20-30 cm long slivers) are deleted.
Point attribute 'part': 0 bark, 1 upper tooth, 2 lower tooth; 'piece' keeps the step1 ids (new teeth 200+). Args: none"""
import bpy, bmesh, os, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'step1.blend'))
ob = bpy.data.objects['Body']; me = ob.data
TEETH = list(range(107, 136)) + [139]
JUNK = [136, 137, 138]
N_UPPER, N_LOWER = 9, 10
RADIUS, DEPTH, SIDES = 0.042, 0.72, 8
co = np.array([tuple(v.co) for v in me.vertices])
pv = np.zeros(len(co), np.int32); me.attributes['piece'].data.foreach_get('value', pv)
rows = {1: [], 2: []}
for p in TEETH:
    c = co[pv == p]; upper = c[:, 2].mean() > 0.76
    root = c[np.argmax(c[:, 2])] if upper else c[np.argmin(c[:, 2])]
    tip = c[np.argmin(c[:, 2])] if upper else c[np.argmax(c[:, 2])]
    rows[1 if upper else 2].append((root, tip))
bm = bmesh.new(); bm.from_mesh(me)
lay = bm.verts.layers.int.get('piece')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v[lay] in TEETH + JUNK], context='VERTS')
part = bm.verts.layers.int.new('part')
oco = bm.verts.layers.float_vector.get('orig_co')


def peg(root, tip, r, pid, kind, front):
    axis = (tip - root); L = axis.length; axis.normalize()
    side = axis.cross(front).normalized(); fwd = side.cross(axis).normalized()
    prof = [(0.0, 1.0), (0.15, 1.04), (0.5, 0.92), (0.78, 0.66), (0.93, 0.34)]
    rings = []
    for t, s in prof:
        ring = []
        for k in range(SIDES):
            a = 2 * math.pi * k / SIDES
            p = root + axis * (t * L) + side * (math.cos(a) * r * s) + fwd * (math.sin(a) * r * s * DEPTH)
            v = bm.verts.new(p); ring.append(v)
        rings.append(ring)
    apex = bm.verts.new(root + axis * L)
    faces = []
    for ra, rb in zip(rings[:-1], rings[1:]):
        for k in range(SIDES):
            faces.append(bm.faces.new((ra[k], ra[(k + 1) % SIDES], rb[(k + 1) % SIDES], rb[k])))
    for k in range(SIDES):
        faces.append(bm.faces.new((rings[-1][k], rings[-1][(k + 1) % SIDES], apex)))
    faces.append(bm.faces.new(list(reversed(rings[0]))))
    vs = [v for ring in rings for v in ring] + [apex]
    for v in vs:
        v[lay] = pid; v[part] = kind
        if oco is not None:
            v[oco] = v.co
    return faces


pid = 200; made = 0
for kind, n in ((1, N_UPPER), (2, N_LOWER)):
    R = sorted(rows[kind], key=lambda e: e[0][0])
    roots = np.array([e[0] for e in R]); dirs = np.array([e[1] - e[0] for e in R])
    seg = np.r_[0, np.cumsum(np.linalg.norm(np.diff(roots, axis=0), axis=1))]
    for i in range(n):
        s = seg[-1] * (0.04 + 0.92 * i / (n - 1))
        root = Vector([np.interp(s, seg, roots[:, j]) for j in range(3)])
        d = Vector([np.interp(s, seg, dirs[:, j]) for j in range(3)])
        u = i / (n - 1); length = d.length * (1.25 + 0.25 * math.sin(math.pi * u)) * (0.92 + 0.16 * ((i * 7919) % 5) / 4)
        root -= d.normalized() * 0.03                                 # sink the root into the gum
        front = Vector((root.x * 0.6, -1.0, 0)).normalized()          # mouth arc faces -Y, curving round
        fs = peg(root, root + d.normalized() * (length + 0.03), RADIUS * (0.9 + 0.2 * math.sin(math.pi * u)), pid, kind, front)
        bmesh.ops.recalc_face_normals(bm, faces=fs)
        pid += 1; made += 1
bm.to_mesh(me); bm.free(); me.update()
pa = np.zeros(len(me.vertices), np.int32); me.attributes['part'].data.foreach_get('value', pa)
print('TEETH pegs', made, 'verts', len(me.vertices), 'tris', sum(len(p.vertices) - 2 for p in me.polygons),
      'upper', int((pa == 1).sum()), 'lower', int((pa == 2).sum()))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'step2.blend'))
