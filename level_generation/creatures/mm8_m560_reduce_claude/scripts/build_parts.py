"""Rebuild the wyvern's teeth and dorsal spikes on the accepted reduction (user review 2026-10-18: "re-do his teeth,
also these [neck spikes] seem ultra sloppy").

Input: work/ladder.blend (Cand_55, the head-80 pick) and work/parts_probe.json. The Meshy teeth and spikes are
separate pieces; they are deleted and replaced:
- teeth: 6-sided cones on an even row per jaw and side (count of the original row, front fang largest, smaller to
  the back), the gum line fitted through the original tooth bases and snapped to the skin, roots sunk into the gum;
  upper teeth hang from the head (rigid on Head), lower rise from the jaw (rigid on Jaw), perpendicular to the snout;
- dorsal spikes: closed 6-sided tubes curving back toward the tail (quadratic curve leaving the skin along its
  normal), root sunk along the normal; the length profile is the original row smoothed along the spine (the small
  head/neck spikes graded up to the body spikes); every spike vertex takes the skin weights at its root, so it
  moves rigidly with that skin point.
Part labels (face attribute `part`: 0 body, 1 wing, 2 eye, 3 mouth, 4 spike, 5 tooth) go to the compose step.
Writes work/rebuild.blend (object `Rebuilt`, rig `Rig`) and work/rebuild.json. Usage: blender -b -P build_parts.py"""
import json, math, os
import bmesh, bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
cand = bpy.data.objects['Cand_55']
probe = json.load(open(os.path.join(HERE, 'work', 'parts_probe.json')))
SIDES = 6
SCALE_PATH = os.path.join(HERE, 'work', 'part_scale.json')
SCALE = json.load(open(SCALE_PATH)) if os.path.exists(SCALE_PATH) else {}


def components(me):
    n = len(me.vertices); parent = np.arange(n)

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for e in me.edges:
        a, b = find(e.vertices[0]), find(e.vertices[1])
        if a != b:
            parent[a] = b
    roots = np.array([find(i) for i in range(n)])
    return np.unique(roots, return_inverse=True)[1]


me = cand.data; lab = components(me)
eyes = [p for p in probe if p['faces'] > 90 and p['length'] < .012]
assert len(eyes) == 2, eyes
xc = float(np.mean([p['centre'][0] for p in eyes]))
wings = {p['piece'] for p in probe if p['faces'] > 150}
mouth = {p['piece'] for p in probe if p['bone'] == 'Jaw' and p['length'] > .03}
assert len(wings) == 2 and len(mouth) == 1
teeth = [p for p in probe if p['centre'][1] < -.435 and p['length'] < .008 and p not in eyes]
spikes = [p for p in probe if p['piece'] not in wings | mouth and p not in eyes and p not in teeth]
print('PIECES teeth', len(teeth), 'spikes', len(spikes), 'eye centre x', round(xc, 4))

# part label per vertex of the kept mesh, then drop the old teeth and spikes
vpart = np.zeros(len(me.vertices), int)
vpart[np.isin(lab, list(wings))] = 1
vpart[np.isin(lab, [p['piece'] for p in eyes])] = 2
vpart[np.isin(lab, list(mouth))] = 3
drop = np.isin(lab, [p['piece'] for p in teeth + spikes])
gname = {g.index: g.name for g in cand.vertex_groups}
bm = bmesh.new(); bm.from_mesh(me)
player = bm.faces.layers.int.new('part')
pidx = bm.faces.layers.int.new('piece')  # rebuilt tooth/spike number, -1 elsewhere
bm.verts.ensure_lookup_table()
for f in bm.faces:
    f[player] = int(vpart[f.verts[0].index]); f[pidx] = -1
dropped_faces = sum(1 for f in bm.faces if drop[f.verts[0].index])
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.flatnonzero(drop)], context='VERTS')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
uvl = bm.loops.layers.uv.active
body_faces = [f for f in bm.faces if f[player] == 0]
tree = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in body_faces])


def skin(point):
    """nearest body surface point, its normal and interpolated skin weights {group index: weight}"""
    loc, nrm, fi, _ = tree.find_nearest(Vector(point))
    f = body_faces[fi]
    cs = [v.co for v in f.verts]
    # barycentric-like inverse-distance weights over the face corners
    d = np.array([max((loc - c).length, 1e-6) for c in cs]); w = (1 / d) / (1 / d).sum()
    acc = {}
    for wt, v in zip(w, f.verts):
        for g, x in v[dl].items():
            acc[g] = acc.get(g, 0) + wt * x
    s = sum(acc.values())
    return loc, nrm.normalized(), {g: x / s for g, x in acc.items() if x / s > 1e-3}


def ring(centre, axis, radius, phase=0.0):
    axis = axis.normalized()
    ref = Vector((1, 0, 0)) if abs(axis.x) < .9 else Vector((0, 1, 0))
    u = axis.cross(ref).normalized(); v = axis.cross(u)
    return [centre + (u * math.cos(phase + k * math.tau / SIDES) + v * math.sin(phase + k * math.tau / SIDES)) * radius
            for k in range(SIDES)]


def add_tube(rings, tip, weights, part):
    """closed tube: rings of SIDES points from root to tip, a tip vertex and a root cap"""
    vs = [[bm.verts.new(p) for p in r] for r in rings]; tv = bm.verts.new(tip)
    new = []
    for a, b in zip(vs, vs[1:]):
        for k in range(SIDES):
            new.append(bm.faces.new((a[k], a[(k + 1) % SIDES], b[(k + 1) % SIDES], b[k])))
    for k in range(SIDES):
        new.append(bm.faces.new((vs[-1][k], vs[-1][(k + 1) % SIDES], tv)))
    new.append(bm.faces.new(list(reversed(vs[0]))))
    for v in [x for r in vs for x in r] + [tv]:
        for g, w in weights.items():
            v[dl][g] = w
    for f in new:
        f[player] = part; f[pidx] = add_tube.count
    add_tube.count += 1
    return new


add_tube.count = 0


gidx = {g.name: g.index for g in cand.vertex_groups}
report = {'dropped_faces': dropped_faces, 'teeth': [], 'spikes': []}

# --- teeth --------------------------------------------------------------------------------------------------------
hb = rig.data.bones['Head']; axis = (hb.tail_local - hb.head_local).normalized()
up = Vector((0, -axis.z, axis.y)) if axis.y < 0 else Vector((0, axis.z, -axis.y))
if up.z < 0:
    up = -up
rows = {}
for p in teeth:
    side = 1 if p['centre'][0] > xc else -1
    rows.setdefault((p['bone'], side), []).append(p)
for (bone, side), row in sorted(rows.items()):
    row.sort(key=lambda p: p['base'][1])
    base = np.array([p['base'] for p in row]); y = base[:, 1]
    deg = 2 if len(row) >= 5 else 1
    fx, fz = np.polyfit(y, base[:, 0], deg), np.polyfit(y, base[:, 2], deg)
    n = len(row); lower = bone == 'Jaw'
    # lower row offset by half a gap so the teeth interlock
    ts = (np.arange(n) + (.5 if lower else 0)) / (n - (.5 if lower else 1))
    ys = y.min() + (y.max() - y.min()) * np.clip(ts, 0, 1)
    out = Vector((side, 0, 0))
    d = ((up if lower else -up) + out * .3).normalized()
    for i, yy in enumerate(ys):
        t = i / max(n - 1, 1)
        L = (.0068 if i == 0 else .0058 if i == 1 else .0052 - .0018 * t)
        L *= SCALE.get(str(add_tube.count), 1.0)  # per-tooth clearance from parts_gate.py (clearance.py)
        r = max(.0011, .3 * L)
        gum = Vector((np.polyval(fx, yy), yy, np.polyval(fz, yy)))
        loc, nrm, _ = skin(gum)
        root, b0 = loc - d * (.35 * L), loc - d * (.05 * L)
        tip = loc + d * L
        add_tube([ring(root, d, r * 1.05), ring(b0, d, r)], tip, {gidx[bone]: 1.0}, 5)
        report['teeth'].append({'bone': bone, 'side': side, 'gum': [round(c, 4) for c in loc], 'length': round(L, 4)})
    print('TEETH row', bone, side, n)

# --- dorsal spikes ------------------------------------------------------------------------------------------------
chain = ['Head', 'Neck5', 'Neck4', 'Neck3', 'Neck2', 'Neck1', 'Spine2', 'Spine1', 'Tail1', 'Tail2', 'Tail3', 'Tail4',
         'Tail5', 'Tail6', 'Tail7', 'Tail8', 'Tail9']
pts = [rig.data.bones['Head'].tail_local] + [rig.data.bones[b].head_local for b in chain] + [rig.data.bones['Tail9'].tail_local]
pts = [Vector(p) for p in pts]
seg = np.cumsum([0] + [(b - a).length for a, b in zip(pts, pts[1:])])


def along(point):
    """arc parameter of the point's projection on the spine polyline, and the tailward tangent there"""
    best = (1e9, 0, Vector((0, 1, 0)))
    for i, (a, b) in enumerate(zip(pts, pts[1:])):
        ab = b - a; t = max(0, min(1, (point - a).dot(ab) / ab.length_squared))
        q = a + ab * t; dist = (point - q).length
        if dist < best[0]:
            best = (dist, seg[i] + t * ab.length, ab.normalized())
    return best[1], best[2]


info = []
for p in spikes:
    loc, nrm, w = skin(p['base'])
    s, tan = along(loc)
    info.append((s, p, loc, nrm, tan, w))
info.sort(key=lambda x: x[0])
L = np.array([x[1]['length'] for x in info])
# the flat broken piece on the tail (Tail7, 5 cm long, 2 cm wide) takes its neighbours' size
flat = [i for i, x in enumerate(info) if x[1]['base_radius'] > .015]
for i in flat:
    L[i] = np.median([L[j] for j in range(max(0, i - 2), min(len(L), i + 3)) if j != i])
med = np.array([np.median(L[max(0, i - 1):i + 2]) for i in range(len(L))])
Ls = np.array([np.mean(med[max(0, i - 1):i + 2]) for i in range(len(L))])
# head/neck spikes graded up to the body spikes: no spike shorter than 75 % of the row's upper quartile, except the
# first behind the head
floor = .75 * np.percentile(Ls, 75)
# only ahead of the largest neck spike; the tail row keeps its taper toward the tip
k = int(np.argmax(Ls[:len(Ls) // 3 + 1]))
Ls[:k] = np.maximum(Ls[:k], floor); Ls[0] = .85 * Ls[1]
for (s, p, loc, nrm, tan, w), length in zip(info, Ls):
    nrm = Vector(nrm)
    if nrm.z < -.2:  # spine normals point up; guard against a back-facing nearest face
        nrm = -nrm
    side = tan - nrm * tan.dot(nrm)
    tipdir = (nrm + side.normalized() * .4).normalized()
    r0 = max(.0022, .24 * length)
    tip = loc + tipdir * length
    ctrl = loc + nrm * (.45 * length)
    curve = lambda t: loc * (1 - t) ** 2 + ctrl * 2 * t * (1 - t) + tip * t * t
    tang = lambda t: ((ctrl - loc) * 2 * (1 - t) + (tip - ctrl) * 2 * t).normalized()
    rings = [ring(loc - nrm * (.6 * r0), nrm, r0 * 1.02)]
    for t in (0.0, .35, .65, .88):
        rings.append(ring(curve(t), tang(t), r0 * (1 - t) ** .85))
    add_tube(rings, tip, w, 4)
    report['spikes'].append({'arc': round(float(s), 4), 'root': [round(c, 4) for c in loc], 'length': round(float(length), 4),
                             'radius': round(r0, 4), 'original_length': p['length']})
print('SPIKES', len(info), 'lengths', np.round(Ls, 4).tolist())

for f in bm.faces:
    f.smooth = True
bm.normal_update()
out = bpy.data.meshes.new('Rebuilt'); bm.to_mesh(out); bm.free()
obj = bpy.data.objects.new('Rebuilt', out); bpy.context.scene.collection.objects.link(obj)
obj.parent = cand.parent; obj.matrix_parent_inverse = cand.matrix_parent_inverse.copy(); obj.matrix_basis = cand.matrix_basis.copy()
for g in cand.vertex_groups:
    obj.vertex_groups.new(name=g.name)
for m in cand.data.materials:
    out.materials.append(m)
a = obj.modifiers.new('Armature', 'ARMATURE'); a.object = rig
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o.name.startswith('Cand_'):
        bpy.data.objects.remove(o, do_unlink=True)
tris = sum(len(p.vertices) - 2 for p in out.polygons)
report.update(triangles=tris, candidate_triangles=sum(len(p.vertices) - 2 for p in me.polygons))
json.dump(report, open(os.path.join(HERE, 'work', 'rebuild.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rebuild.blend'))
print('REBUILT', tris, 'triangles; dropped', dropped_faces, 'old teeth/spike faces')
