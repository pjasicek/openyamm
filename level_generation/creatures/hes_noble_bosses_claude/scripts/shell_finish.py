"""Finish a boss's extracted shell on the rig (rest pose): decimate to a budget, orient normals away from the body,
keep a minimum clearance, transfer and smooth the body's skin weights, remove the body skin the shell covers
(Body_<boss>), and export the shell triangles for the xatlas UV pass and the paint projection.

Usage (Blender): shell_finish.py <boss> [--tris 6500] [--clearance 0.006]
Reads work/<boss>/shell_fit.blend; writes work/<boss>/shell_rig.blend, work/<boss>/shell_tris.npz,
work/<boss>/shell_finish.json."""
import bpy, bmesh, sys, json, argparse
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
ap = argparse.ArgumentParser()
ap.add_argument('boss')
ap.add_argument('--tris', type=int, default=6500)
ap.add_argument('--clearance', type=float, default=0.006)
ap.add_argument('--cover', type=float, default=0.045)
ap.add_argument('--anchor', type=float, default=0.02)
ap.add_argument('--min-island', type=int, default=30)
a = ap.parse_args(argv)
P = Path(__file__).resolve().parents[1]
W = P / 'work' / a.boss
bpy.ops.wm.open_mainfile(filepath=str(W / 'shell_fit.blend'))
sc = bpy.context.scene
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; shell = bpy.data.objects['Shell']
fig = bpy.data.objects.get('Figure')
if fig:
    fig.hide_render = True; fig.hide_viewport = True
for c in list(shell.data.color_attributes):
    shell.data.color_attributes.remove(c)

# ---------------------------------------------------------------- rigid add-ons join the shell, marked by bone
rigid = [o for o in sc.objects if o.name.startswith('Rigid_')]
for o in rigid:
    g = o.vertex_groups.new(name='RIGID:' + o['bone']); g.add(list(range(len(o.data.vertices))), 1.0, 'REPLACE')
if rigid:
    bpy.ops.object.select_all(action='DESELECT')
    for o in rigid + [shell]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.join()
# ---------------------------------------------------------------- decimate (borders kept), triangulate
bpy.context.view_layer.objects.active = shell
for o in sc.objects:
    o.select_set(o == shell)
bm = bmesh.new(); bm.from_mesh(shell.data)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.to_mesh(shell.data); bm.free()
n0 = len(shell.data.polygons)
if n0 > a.tris:
    m = shell.modifiers.new('dec', 'DECIMATE'); m.ratio = a.tris / n0; m.use_collapse_triangulate = True
    m.use_symmetry = False
    bpy.ops.object.modifier_apply(modifier='dec')
# drop degenerate slivers left by the collapse, and small loose islands
bm = bmesh.new(); bm.from_mesh(shell.data)
bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-5)
bmesh.ops.triangulate(bm, faces=bm.faces)
bm.faces.ensure_lookup_table(); seen = set(); small = []
for f in bm.faces:
    if f.index in seen:
        continue
    comp = [f]; seen.add(f.index); stack = [f]
    while stack:
        g = stack.pop()
        for e in g.edges:
            for h in e.link_faces:
                if h.index not in seen:
                    seen.add(h.index); stack.append(h); comp.append(h)
    if len(comp) < a.min_island:
        small += comp
bmesh.ops.delete(bm, geom=small, context='FACES')
print('DROPPED small islands', len(small), 'faces')
bm.to_mesh(shell.data); bm.free()

# ---------------------------------------------------------------- body BVH (core body only)
bme = bmesh.new(); bme.from_mesh(body.data); bme.transform(body.matrix_world)
body_bvh = BVHTree.FromBMesh(bme)


def nearest(p):
    loc, n, fi, d = body_bvh.find_nearest(Vector(p))
    return np.array(loc), np.array(n), d


# orient faces away from the body, push vertices to the clearance
me = shell.data
SV = np.array([tuple(v.co) for v in me.vertices])
for _ in range(2):
    pushed = 0
    for i, p in enumerate(SV):
        q, n, d = nearest(p)
        s = np.dot(p - q, n)
        if s < a.clearance:
            SV[i] = q + n * a.clearance; pushed += 1
    me.vertices.foreach_set('co', SV.ravel()); me.update()
flip = []
for poly in me.polygons:
    c = np.array(poly.center); q, n, d = nearest(c)
    if np.dot(np.array(poly.normal), c - q) < 0:
        flip.append(poly.index)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
bmesh.ops.reverse_faces(bm, faces=[bm.faces[i] for i in flip])
bm.to_mesh(me); bm.free()
print('SHELL', n0, '->', len(me.polygons), 'tris; flipped', len(flip), 'pushed', pushed)

# ---------------------------------------------------------------- weights from the body, smoothed on the shell
for g in list(shell.vertex_groups):
    if not g.name.startswith('RIGID:'):
        shell.vertex_groups.remove(g)
for g in body.vertex_groups:
    shell.vertex_groups.new(name=g.name)
dt = shell.modifiers.new('dt', 'DATA_TRANSFER'); dt.object = body
dt.use_vert_data = True; dt.data_types_verts = {'VGROUP_WEIGHTS'}; dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'; dt.layers_vgroup_select_dst = 'NAME'
bpy.ops.object.modifier_apply(modifier='dt')
rigid_groups = [g for g in shell.vertex_groups if g.name.startswith('RIGID:')]
rigid_of = {}
for v in me.vertices:
    for g in v.groups:
        gg = shell.vertex_groups[g.group]
        if gg.name.startswith('RIGID:') and g.weight > 0.5:
            rigid_of[v.index] = gg.name[6:]
for g in rigid_groups:
    shell.vertex_groups.remove(g)
names = [g.name for g in shell.vertex_groups]


def read_weights():
    W_ = np.zeros((len(me.vertices), len(names)), np.float32)
    for v in me.vertices:
        for g in v.groups:
            W_[v.index, g.group] = g.weight
    return W_


Wt = read_weights()
# bridges: Meshy fuses a hanging arm with the skirt or the flank; faces joining an arm to a leg (or to the trunk
# below the chest) would stretch whenever the arm moves: cut them
def limb(n):
    for side in 'LR':
        if n.startswith(f'B_{side}_') and any(k in n for k in ('UpperArm', 'Forearm', 'Hand', 'Finger')):
            return 'arm' + side
        if n.startswith(f'B_{side}_') and any(k in n for k in ('Thigh', 'Calf', 'Foot', 'Toe')):
            return 'leg' + side
    return 'trunk'
lab = np.array([limb(names[i]) for i in Wt.argmax(1)])
zv = np.array([(shell.matrix_world @ v.co).z for v in me.vertices])
chest = (rig.matrix_world @ rig.data.bones['B_Spine2'].head_local).z
bridge = []
for poly in me.polygons:
    ls = {lab[i] for i in poly.vertices}
    arms = {l for l in ls if l.startswith('arm')}
    if arms and (any(l.startswith('leg') for l in ls) or ('trunk' in ls and min(zv[i] for i in poly.vertices) < chest - 0.1)
                 or len(arms) > 1):
        bridge.append(poly.index)
if bridge:
    bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.faces[i] for i in bridge], context='FACES')
    bm.to_mesh(me); bm.free(); me.update()
    rigid_of = {}   # indices changed: rigid parts are re-marked below from their groups
print('BRIDGES cut', len(bridge), 'faces')
Wt = read_weights()
wing = np.array([n.startswith('B_Wing_') for n in names])
Wt[:, wing] = 0
E = np.array([tuple(e.vertices) for e in me.edges])
# protrusions (spurs, plate rims, pauldrons) move with their base: only vertices near the skin keep the transferred
# weights; the others take weights diffused through the shell from them (a tip no longer copies the nearest skin's
# bone, which sheared shoulder spurs between arm and torso)
SVn = np.array([tuple(shell.matrix_world @ v.co) for v in me.vertices])
dist = np.array([nearest(p)[2] for p in SVn])
anchor = dist < a.anchor
for _ in range(80):
    acc = np.zeros_like(Wt); cnt = np.zeros(len(Wt))
    np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
    np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
    free = ~anchor & (cnt > 0)
    Wt[free] = acc[free] / cnt[free][:, None]
print('ANCHORED', int(anchor.sum()), 'of', len(anchor))
for _ in range(4):
    acc = np.zeros_like(Wt); cnt = np.zeros(len(Wt))
    np.add.at(acc, E[:, 0], Wt[E[:, 1]]); np.add.at(acc, E[:, 1], Wt[E[:, 0]])
    np.add.at(cnt, E[:, 0], 1); np.add.at(cnt, E[:, 1], 1)
    Wt = 0.6 * Wt + 0.4 * acc / np.maximum(cnt, 1)[:, None]
# skirt rule: shell between the legs below the crotch takes one pelvis/thighs mix (a front or back panel spanning
# both legs would otherwise tear between the left and right inner-thigh weights)
crotch = (rig.matrix_world @ rig.data.bones['B_Pelvis'].head_local).z - 0.02
SVf = np.array([tuple(shell.matrix_world @ v.co) for v in me.vertices])
fx = np.clip(1 - np.abs(SVf[:, 0]) / 0.12, 0, 1) * np.clip((crotch - SVf[:, 2]) / 0.05, 0, 1)
mix = np.zeros(len(names)); 
for n, w in (('B_Pelvis', 0.5), ('B_L_Thigh', 0.25), ('B_R_Thigh', 0.25)):
    mix[names.index(n)] = w
Wt = Wt * (1 - fx[:, None]) + mix[None, :] * fx[:, None]
print('SKIRT vertices', int((fx > 0.05).sum()))
for vi, bone in rigid_of.items():
    Wt[vi] = 0; Wt[vi, names.index(bone)] = 1.0
# four influences, normalised
top = np.argsort(-Wt, axis=1)[:, :4]
keep = np.zeros_like(Wt); rows = np.arange(len(Wt))[:, None]
keep[rows, top] = Wt[rows, top]
keep /= np.maximum(keep.sum(1, keepdims=True), 1e-9)
for j, g in enumerate(shell.vertex_groups):
    g.remove(list(range(len(me.vertices))))
    idx = np.flatnonzero(keep[:, j] > 1e-4)
    for i in idx:
        g.add([int(i)], float(keep[i, j]), 'REPLACE')
shell.parent = rig
if not any(m.type == 'ARMATURE' for m in shell.modifiers):
    am = shell.modifiers.new('Armature', 'ARMATURE'); am.object = rig

# ---------------------------------------------------------------- hide the skin the shell covers
sbm = bmesh.new(); sbm.from_mesh(me); sbm.transform(shell.matrix_world)
shell_bvh = BVHTree.FromBMesh(sbm)
bm = bmesh.new(); bm.from_mesh(body.data); bm.faces.ensure_lookup_table()
covered = []
for f in bm.faces:
    c = body.matrix_world @ f.calc_center_median(); n = (body.matrix_world.to_3x3() @ f.normal).normalized()
    if n.length < 0.5:
        continue
    t1 = n.orthogonal().normalized(); t2 = n.cross(t1)
    hits = [shell_bvh.ray_cast(c + n * 0.0005, d, a.cover)[0] is not None
            for d in (n, (n + 0.4 * t1).normalized(), (n - 0.4 * t1).normalized(), (n + 0.4 * t2).normalized(),
                      (n - 0.4 * t2).normalized())]
    if hits[0] and sum(hits[1:]) >= 3:
        covered.append(f)
print('COVERED body faces', len(covered), 'of', len(bm.faces))
body2 = body.copy(); body2.data = body.data.copy(); body2.name = f'Body_{a.boss}'; sc.collection.objects.link(body2)
bm2 = bmesh.new(); bm2.from_mesh(body2.data); bm2.faces.ensure_lookup_table()
bmesh.ops.delete(bm2, geom=[bm2.faces[f.index] for f in covered], context='FACES')
bm2.to_mesh(body2.data); bm2.free()
body.hide_render = True; body.hide_viewport = True

# ---------------------------------------------------------------- export triangles for UV and projection
me.calc_loop_triangles()
V = np.array([tuple(v.co) for v in me.vertices], np.float32)
T = np.array([tuple(t.vertices) for t in me.loop_triangles], np.int32)
N = np.array([tuple(v.normal) for v in me.vertices], np.float32)
np.savez(W / 'shell_tris.npz', positions=V, triangles=T, normals=N)
if fig:
    fm = fig.data; fm.calc_loop_triangles()
    np.savez(W / 'figure_tris.npz', positions=np.array([tuple(fig.matrix_world @ v.co) for v in fm.vertices], np.float32),
             triangles=np.array([tuple(t.vertices) for t in fm.loop_triangles], np.int32))
stats = {'shell_tris_in': n0, 'shell_tris': len(T), 'flipped': len(flip), 'covered_body_faces': len(covered),
         'body_tris_left': sum(len(p.vertices) - 2 for p in body2.data.polygons)}
(W / 'shell_finish.json').write_text(json.dumps(stats, indent=1))
print('STATS', stats)
bpy.ops.wm.save_as_mainfile(filepath=str(W / 'shell_rig.blend'))
