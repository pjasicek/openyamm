"""Face geometry repair on the rest mesh (rig/UVs/weights untouched): remove Meshy eyeball shells, relax the
lumpy eye sockets, nostrils and mouth crease, and soften skin vertex normals (custom normals from a smoothed
copy) so low-poly surface noise does not show as triangle facets under sun light. Eye centres are stored for
texture painting (scene['pfem_eyes'])."""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

mesh = bpy.data.objects['Peasant']; me = mesh.data
rig = bpy.data.objects['Peasant_Rig']; rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)

bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
eyes = {}
for name in ('EyeLeft', 'EyeRight'):
    vs = {v for f in bm.faces if PARTS[part[f.index]] == name for v in f.verts}
    if vs:
        co = np.array([tuple(v.co) for v in vs])
        eyes[name] = {'centre': co.mean(0).tolist(), 'front_y': float(co[:, 1].min()),
                      'size': (co.max(0) - co.min(0)).tolist()}
if eyes:
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if PARTS[part[f.index]] in ('EyeLeft', 'EyeRight')], context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bpy.context.scene['pfem_eyes'] = json.dumps(eyes)
else:
    eyes = json.loads(bpy.context.scene['pfem_eyes'])
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
layer = bm.faces.layers.int.get('part')
uvl = bm.loops.layers.uv.active
# close small holes (Meshy pinholes, e.g. at the sternum); UVs/part come from neighbouring faces
sternum = [v for e in bm.edges if e.is_boundary for v in e.verts
           if abs(v.co.x + 0.02) < 0.03 and abs(v.co.z - 1.2) < 0.03 and v.co.y < -0.08]
bmesh.ops.remove_doubles(bm, verts=list(set(sternum)), dist=0.007)
bm.edges.ensure_lookup_table()
region_edges = [e for e in bm.edges if e.is_boundary and all(abs(v.co.x + 0.02) < 0.03 and abs(v.co.z - 1.2) < 0.03
                                                            and v.co.y < -0.08 for v in e.verts)]
filled = bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=8)['faces']
if region_edges and all(e.is_valid and e.is_boundary for e in region_edges):
    filled += bmesh.ops.edgenet_fill(bm, edges=region_edges)['faces'] if hasattr(bmesh.ops, 'edgenet_fill') else []
    filled += bmesh.ops.contextual_create(bm, geom=region_edges)['faces']
for f in filled:
    for l in f.loops:
        others = [o for o in l.vert.link_loops if o.face not in filled]
        if others:
            l[uvl].uv = others[0][uvl].uv.copy()
    nb = [o.face for l in f.loops for o in l.vert.link_loops if o.face not in filled]
    if nb:
        f[layer] = nb[0][layer]
bmesh.ops.recalc_face_normals(bm, faces=filled)
print('HOLES filled', len(filled))
body = PARTS.index('Body')
body_verts = {v for f in bm.faces if f[layer] == body for v in f.verts}


def region_weight(co):
    """Smoothing strength: eye sockets 1, mouth crease 0.8, nostril rims 0.6, rest of face 0."""
    w = 0.0
    for e in eyes.values():
        c = Vector(e['centre'])
        d = Vector(((co.x - c.x) / 0.022, (co.y - c.y) / 0.03, (co.z - c.z) / 0.014))
        w = max(w, max(0.0, 1.0 - d.length) ** 0.7)
    if co.y < -0.06:
        mouth = Vector(((co.x) / 0.03, 0, (co.z - 1.410) / 0.010))
        w = max(w, 0.8 * max(0.0, 1.0 - mouth.length))
        nose = Vector(((co.x) / 0.022, 0, (co.z - 1.432) / 0.010))
        w = max(w, 0.6 * max(0.0, 1.0 - nose.length))
    return w


def sternum_weight(co):
    d = Vector((co.x / 0.025, 0, (co.z - 1.215) / 0.05))
    return 0.9 * max(0.0, 1.0 - d.length) if co.y < -0.04 else 0.0


weights = {v: max(region_weight(v.co) if v.co.z > 1.38 else 0.0, sternum_weight(v.co)) for v in body_verts}
weights = {v: w for v, w in weights.items() if w > 0 and not v.is_boundary}
for _ in range(8):
    new = {}
    for v, w in weights.items():
        nb = [e.other_vert(v).co for e in v.link_edges]
        avg = sum(nb, Vector()) / len(nb)
        new[v] = v.co.lerp(avg, 0.5 * w)
    for v, c in new.items():
        v.co = c
bm.to_mesh(me); bm.free(); me.update()
print('FACE smoothed', len(weights), 'verts; eyes', {k: [round(x, 3) for x in v['centre']] for k, v in eyes.items()})

# Soft skin normals: smoothed copy -> custom normals (skin + bodice only; hair/skirt keep their own).
src = mesh.copy(); src.data = me.copy(); src.name = 'NormalSource'
bpy.context.scene.collection.objects.link(src)
for m in list(src.modifiers):
    src.modifiers.remove(m)
sm = src.modifiers.new('smooth', 'LAPLACIANSMOOTH'); sm.iterations = 6; sm.lambda_factor = 0.8
sm.use_volume_preserve = True
g = mesh.vertex_groups.get('normal_soften') or mesh.vertex_groups.new(name='normal_soften')
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
skin_v = {vi for p in me.polygons if part[p.index] == body for vi in p.vertices}
for vi in skin_v:
    z = me.vertices[vi].co.z; y = me.vertices[vi].co.y
    face = z > 1.38 and y < 0.0
    g.add([vi], 0.45 if face else 1.0, 'REPLACE')
dt = mesh.modifiers.new('soft_normals', 'DATA_TRANSFER')
dt.object = src; dt.use_loop_data = True; dt.data_types_loops = {'CUSTOM_NORMAL'}
dt.loop_mapping = 'TOPOLOGY'; dt.vertex_group = g.name; dt.mix_factor = 1.0
for i in range(len(mesh.modifiers) - 1):
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.modifier_move_up(modifier=dt.name)
bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.modifier_apply(modifier=dt.name)
bpy.data.objects.remove(src, do_unlink=True)
if 'normal_soften' in mesh.vertex_groups:
    mesh.vertex_groups.remove(mesh.vertex_groups['normal_soften'])
print('NORMALS custom', me.has_custom_normals)
bpy.ops.wm.save_mainfile()
