"""55 % goblin -> retexture master (user 2026-10-13: fix the teeth and the shin-guard spikes, regenerate textures).
- `piece` per vertex from the gated master (mm6_gob2_claude/work/rig_v6.blend, same rest space), voted per connected
  piece; `head` per face from the installed merged atlas (head half: u > (1024 + 32) / 2080).
- The 14 teeth (master pieces 60-78, all on B_Head: the goblin has no jaw bone) and the four shin-guard spikes
  (37/62 left, 50/59 right) are rebuilt as clean 6-sided cones on their master bone, root sunk into the gum/plate.
- Two texture sets with fresh smart-project UVs (Goblin_A body, GoblinHead_A head) and the Meshy uploads.
Out: work/gob_master.blend, work/{body,head}_upload.glb, work/gob_build.json."""
import json
import math
import os
import bmesh
import bpy
import numpy as np
from mathutils import Vector, kdtree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = os.path.join(HERE, '..', 'mm6_gob2_claude', 'work', 'rig_v6.blend')
TEETH = {60, 61, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 78}
SPIKES = {37, 62, 50, 59}
HEAD_U = (1024 + 32) / 2080
SIDES = 6
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
rig = bpy.data.objects['Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
cand = bpy.data.objects['Cand_55']
with bpy.data.libraries.load(os.path.abspath(MASTER)) as (src_lib, dst_lib):
    dst_lib.objects = ['Body']
master = dst_lib.objects[0]
mme = master.data
mparts = np.array([a.value for a in mme.attributes['piece'].data])
mco = np.array([v.co[:] for v in mme.vertices])
mgroups = [g.name for g in master.vertex_groups]

# 1. piece per vertex (nearest master vertex, voted per connected piece), head per face (merged atlas half)
tree = kdtree.KDTree(len(mco))
for i, c in enumerate(mco):
    tree.insert(Vector(c), i)
tree.balance()
me = cand.data
near = np.array([mparts[tree.find(v.co)[1]] for v in me.vertices])
uv = me.uv_layers.active.data
head_face = [np.mean([uv[li].uv[0] > HEAD_U for li in p.loop_indices]) > .5 for p in me.polygons]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
headl = bm.faces.layers.int.new('head')
for f in bm.faces:
    f[headl] = int(head_face[f.index])
partl = bm.verts.layers.int.new('piece')
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
seen, kill, removed = set(), [], {}
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x.index)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    vals, counts = np.unique(near[comp], return_counts=True)
    label = int(vals[counts.argmax()])
    for i in comp:
        bm.verts[i][partl] = label
    if label in TEETH | SPIKES:
        kill += comp; removed[label] = removed.get(label, 0) + len(comp)
old_tris = len({f.index for i in kill for f in bm.verts[i].link_faces})
bmesh.ops.delete(bm, geom=[bm.verts[i] for i in kill], context='VERTS')

# 2. cones from the master blobs
deform = bm.verts.layers.deform.verify()
gi = {g.name: g.index for g in cand.vertex_groups}
built = []


def cone(part, base, tip, radius, bone, head):
    axis = (tip - base).normalized(); length = (tip - base).length
    root = base - axis * length * .35
    u = axis.cross(Vector((1, 0, 0)) if abs(axis.x) < .9 else Vector((0, 1, 0))).normalized(); w = axis.cross(u)
    ring = [bm.verts.new(root + radius * (math.cos(k * math.tau / SIDES) * u + math.sin(k * math.tau / SIDES) * w))
            for k in range(SIDES)]
    apex = bm.verts.new(tip)
    for x in ring + [apex]:
        x[partl] = part; x[deform][gi[bone]] = 1.0
    faces = [bm.faces.new((ring[k], ring[(k + 1) % SIDES], apex)) for k in range(SIDES)]
    faces.append(bm.faces.new(list(reversed(ring))))
    for f in faces:
        f[headl] = int(head); f.smooth = True
    built.append({'part': part, 'bone': bone, 'length': round(length, 4), 'radius': round(radius, 4)})


for part in sorted(TEETH | SPIKES):
    ids = np.flatnonzero(mparts == part); a = mco[ids]
    wsum = {}
    for i in ids:
        for g in mme.vertices[i].groups:
            wsum[mgroups[g.group]] = wsum.get(mgroups[g.group], 0) + g.weight
    bone = max(wsum, key=wsum.get)
    if part in TEETH:
        upper = a[:, 2].mean() > 1.41          # two rows: lower centred at z 1.40, upper at 1.42
        order = np.argsort(-a[:, 2] if upper else a[:, 2])
        base = Vector(a[order[:max(3, len(ids) // 3)]].mean(0)); tip = Vector(a[order[-1]])
        cone(part, base, tip, float(np.clip(.45 * max(np.ptp(a[:, 0]), np.ptp(a[:, 1])), .0018, .005)), bone, True)
    else:
        # spike: base where it meets its greave (nearest master vertices of another piece), tip farthest from there
        other = np.flatnonzero(~np.isin(mparts, list(SPIKES)) & (np.linalg.norm(mco - a.mean(0), axis=1) < .08))
        d = np.array([np.linalg.norm(mco[other] - x, axis=1).min() for x in a])
        base = Vector(a[np.argsort(d)[:max(3, len(ids) // 3)]].mean(0)); tip = Vector(a[d.argmax()])
        radial = a - np.array(base); axis = np.array((tip - base).normalized())
        r = np.linalg.norm(radial - np.outer(radial @ axis, axis), axis=1)
        cone(part, base, tip, float(np.clip(np.percentile(r[(radial @ axis) < .3 * (tip - base).length], 80), .004, .012)),
             bone, False)
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.verts[0][partl] in TEETH | SPIKES])
bm.to_mesh(me); bm.free(); me.update()
assert all(v.groups for v in me.vertices)
g = cand.vertex_groups.get('ReduceProtect')
if g:
    cand.vertex_groups.remove(g)

# 3. the reduced mesh replaces Body; two materials by the head flag
for o in [o for o in bpy.data.objects if o.type == 'MESH' and o.name.startswith('Body') and o is not cand]:
    bpy.data.objects.remove(o, do_unlink=True)          # the installed source and the appended master
for o in list(bpy.data.objects):
    if o.name.startswith('Cand_') and o is not cand:
        bpy.data.objects.remove(o, do_unlink=True)
cand.name = 'Body'; cand.hide_render = False
me.materials.clear()
for name in ('Goblin_A', 'GoblinHead_A'):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes = True; me.materials.append(m)
heads = np.zeros(len(me.polygons), np.int32); me.attributes['head'].data.foreach_get('value', heads)
for p in me.polygons:
    p.material_index = int(heads[p.index])

# 4. fresh UVs per texture set and the Meshy uploads
bpy.ops.object.select_all(action='DESELECT'); cand.select_set(True); bpy.context.view_layer.objects.active = cand
for slot in range(2):
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for f in me.polygons:
        f.select = f.material_index == slot
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.004, area_weight=0, correct_aspect=True,
                             scale_to_bounds=True)
    bpy.ops.uv.pack_islands(rotate=True, margin=.004, margin_method='FRACTION')
    bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles()
sets = {}
for slot, label in enumerate(['body', 'head']):
    sets[label] = sum(1 for t in me.loop_triangles if t.material_index == slot)
    dup = cand.copy(); dup.data = me.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear()
    bpy.context.collection.objects.link(dup)
    b2 = bmesh.new(); b2.from_mesh(dup.data)
    bmesh.ops.delete(b2, geom=[f for f in b2.faces if f.material_index != slot], context='FACES')
    bmesh.ops.delete(b2, geom=[v for v in b2.verts if not v.link_faces], context='VERTS')
    b2.to_mesh(dup.data); b2.free(); dup.data.materials.clear()
    m = bpy.data.materials.new('Neutral'); m.use_nodes = True; dup.data.materials.append(m)
    bpy.ops.object.select_all(action='DESELECT'); dup.select_set(True); bpy.context.view_layer.objects.active = dup
    bpy.ops.export_scene.gltf(filepath=os.path.join(HERE, 'work', f'{label}_upload.glb'), use_selection=True,
                              export_format='GLB', export_animations=False, export_skins=False,
                              export_attributes=False, export_morph=False)
    bpy.data.objects.remove(dup, do_unlink=True)
bpy.context.view_layer.objects.active = cand
report = {'triangles': len(me.loop_triangles), 'sets': sets, 'removed_vertices': removed,
          'removed_triangles': old_tris, 'cones': built}
json.dump(report, open(os.path.join(HERE, 'work', 'gob_build.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'gob_master.blend'))
print('GOB', {k: v for k, v in report.items() if k != 'cones'})
print('CONES', [(c['part'], c['bone'], c['length'], c['radius']) for c in built])
