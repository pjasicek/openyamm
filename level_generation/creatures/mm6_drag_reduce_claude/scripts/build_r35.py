"""35 % step -> retexture master: replaces the ragged Meshy teeth with clean rigid cones, restores the `part`
attribute the texture pipeline uses (nearest source vertex), gives both texture sets fresh UVs and writes the Meshy
uploads. In: work/ladder.blend (Cand_35 + source Body). Out: work/r35_master.blend, work/{body,head}_upload.glb,
work/teeth.json."""
import json
import math
import os
import bmesh
import bpy
import numpy as np
from mathutils import Vector, kdtree
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAND = os.environ.get('REA_CAND', 'Cand_35')
TEETH = {16, 18, 19} | set(range(21, 38))
SIDES = 6
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'ladder.blend'))
src = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; new = bpy.data.objects[CAND]
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
sme = src.data
sparts = np.array([a.value for a in sme.attributes['part'].data]); sco = np.array([v.co[:] for v in sme.vertices])

# 1. part per vertex of the reduced mesh
tree = kdtree.KDTree(len(sco))
for i, c in enumerate(sco):
    tree.insert(Vector(c), i)
tree.balance()
me = new.data
nparts = np.array([sparts[tree.find(v.co)[1]] for v in me.vertices], np.int32)

# 2. teeth from the source blobs: each stays on the bone it was weighted to in the accepted model
hidx, jidx = src.vertex_groups['Head'].index, src.vertex_groups['Jaw'].index
teeth = []
for p in sorted(TEETH):
    ids = np.flatnonzero(sparts == p); a = sco[ids]
    wsum = {g: sum(gg.weight for i in ids for gg in sme.vertices[i].groups if gg.group == g) for g in (hidx, jidx)}
    bone = hidx if wsum[hidx] >= wsum[jidx] else jidx
    # upper teeth hang down from the top of their blob, lower teeth rise from its bottom (the jaw is shut at rest;
    # the farthest-from-gum point picked the wrong end for 3 of the 20 blobs)
    order = np.argsort(-a[:, 2] if bone == hidx else a[:, 2])
    base = a[order[:max(3, len(ids) // 4)]].mean(0); tip = a[order[-1]]
    axis = Vector(tip - base); length = axis.length; axis.normalize()
    radial = a - base; along = radial @ np.array(axis)
    width = np.linalg.norm(radial - np.outer(along, axis), axis=1)
    radius = float(np.clip(np.percentile(width[along < length * .4], 80), .0012, .0035))
    mat = next(f.material_index for f in sme.polygons if sparts[f.vertices[0]] == p)
    teeth.append({'part': int(p), 'bone': 'Head' if bone == hidx else 'Jaw', 'points_down': bool(tip[2] < base[2]),
                  'base': base.tolist(), 'tip': tip.tolist(), 'length': round(length, 4),
                  'radius': round(radius, 4), 'material': mat})

# 3. remove the reduced teeth (connected pieces that are mostly teeth) and add the cones
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
seen = set(); removed = 0; kill = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack, comp = [v], []
    seen.add(v.index)
    while stack:
        x = stack.pop(); comp.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen:
                seen.add(y.index); stack.append(y)
    # every source part is one connected piece: label whole pieces by majority (per-vertex nearest labels gave skin
    # beside spines and teeth the ivory parts)
    vals, counts = np.unique(nparts[[x.index for x in comp]], return_counts=True)
    nparts[[x.index for x in comp]] = vals[counts.argmax()]
    if vals[counts.argmax()] in TEETH:
        kill += [x.index for x in comp]; removed += 1
partl = bm.verts.layers.int.get('part') or bm.verts.layers.int.new('part')   # a new layer invalidates held verts
bm.verts.ensure_lookup_table(); kill = [bm.verts[i] for i in kill]
for x in bm.verts:
    x[partl] = int(nparts[x.index])
old_tris = sum(len(f.verts) - 2 for f in {f for x in kill for f in x.link_faces})
bmesh.ops.delete(bm, geom=kill, context='VERTS')
deform = bm.verts.layers.deform.verify()
gi = {g.name: g.index for g in new.vertex_groups}
for t in teeth:
    base, tip = Vector(t['base']), Vector(t['tip']); axis = (tip - base).normalized()
    root = base - axis * t['length'] * .35          # sink the root into the gum: no gap at any jaw angle
    u = axis.cross(Vector((1, 0, 0)) if abs(axis.x) < .9 else Vector((0, 1, 0))).normalized(); w = axis.cross(u)
    ring = [bm.verts.new(root + t['radius'] * (math.cos(k * math.tau / SIDES) * u + math.sin(k * math.tau / SIDES) * w))
            for k in range(SIDES)]
    apex = bm.verts.new(tip)
    for x in ring + [apex]:
        x[partl] = t['part']; x[deform][gi[t['bone']]] = 1.0
    for k in range(SIDES):
        f = bm.faces.new((ring[k], ring[(k + 1) % SIDES], apex)); f.material_index = t['material']; f.smooth = True
    f = bm.faces.new(list(reversed(ring))); f.material_index = t['material']
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if all(x[partl] in TEETH for x in f.verts)])
bm.to_mesh(me); bm.free(); me.update()
assert all(v.groups for v in me.vertices)

# 4. the reduced mesh replaces Body
g = new.vertex_groups.get('ReduceProtect')
if g:
    new.vertex_groups.remove(g)
bpy.data.objects.remove(src, do_unlink=True)
new.name = 'Body'; new.hide_render = False
for o in list(bpy.data.objects):
    if o.name.startswith('Cand_'):
        bpy.data.objects.remove(o, do_unlink=True)

# 5. fresh UVs per texture set (the project's settings: smart project 66 degrees) and the Meshy uploads
bpy.ops.object.select_all(action='DESELECT'); new.select_set(True); bpy.context.view_layer.objects.active = new
for slot in range(2):
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
    for f in me.polygons:
        f.select = f.material_index == slot
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=.004, area_weight=0, correct_aspect=True,
                             scale_to_bounds=True)
    bpy.ops.uv.pack_islands(rotate=True, margin=.004, margin_method='FRACTION')
    bpy.ops.object.mode_set(mode='OBJECT')
me.calc_loop_triangles(); uv = me.uv_layers.active.data; stats = {}
for slot, label in enumerate(['body', 'head']):
    n = sum(1 for t in me.loop_triangles if t.material_index == slot)
    stats[label] = n
    dup = new.copy(); dup.data = me.copy(); dup.parent = None; dup.modifiers.clear(); dup.vertex_groups.clear()
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
bpy.context.view_layer.objects.active = new
report = {'triangles': len(me.loop_triangles), 'per_set': stats, 'teeth_pieces_removed': removed,
          'teeth_old_triangles': old_tris, 'teeth_new_triangles': len(teeth) * (SIDES + SIDES - 2), 'teeth': teeth}
json.dump(report, open(os.path.join(HERE, 'work', 'teeth.json'), 'w'), indent=1)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'r35_master.blend'))
print('R35', {k: v for k, v in report.items() if k != 'teeth'})
print('TEETH', [(t['part'], t['bone'], 'down' if t['points_down'] else 'up', t['length'], t['radius']) for t in teeth])
