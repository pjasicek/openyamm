"""Texture inputs from work/anim_v1.blend (bind pose), nothing saved to the blend:
1. work/uv3d.npz: the blob's rest-pose triangles (UV, 3D position, per-corner curvature and normal z; pod and glob
   faces excluded). Curvature: mean of dot(vertex normal, direction to each neighbour within 2 rings), smoothed once;
   positive = concave (crease), negative = convex (lump top). (mm6_ooz_claude/scripts/dump_uv3d.py)
2. work/ao_body.png: short-range AO of the blob alone (pod and globs deleted first: the pod stands fully grown in the
   bind pose and the globs lie around it), Cycles 96 samples, 2 cm reach, 2048 (claude_shared/bake_creature_ao.py
   settings). Args: none"""
import bpy, bmesh, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'anim_v1.blend'))
rig = bpy.data.objects['Ooze_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
obj = bpy.data.objects['Ooze']
me = obj.data
part = np.zeros(len(me.polygons), int)
me.attributes['part'].data.foreach_get('value', part)
# ---- 1. uv3d
me.calc_loop_triangles()
uv = me.uv_layers.active.data
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table()
bm.normal_update()
curv = np.zeros(len(bm.verts))
for v in bm.verts:
    ring = {e.other_vert(v) for e in v.link_edges}
    ring2 = ring | {e.other_vert(u) for u in ring for e in u.link_edges}
    ring2.discard(v)
    ds = [(u.co - v.co) for u in ring2]
    curv[v.index] = np.mean([v.normal.dot(d.normalized()) for d in ds if d.length > 1e-6]) if ds else 0.0
smooth = curv.copy()
for v in bm.verts:
    nb = [e.other_vert(v).index for e in v.link_edges]
    smooth[v.index] = 0.5 * curv[v.index] + 0.5 * np.mean(curv[nb]) if nb else curv[v.index]
nz = np.array([v.normal.z for v in bm.verts])
bm.free()
tris = [t for t in me.loop_triangles if part[t.polygon_index] == 0]
U = np.array([[tuple(uv[l].uv) for l in t.loops] for t in tris], np.float32)
X = np.array([[tuple(obj.matrix_world @ me.vertices[v].co) for v in t.vertices] for t in tris], np.float32)
C = np.array([[smooth[v] for v in t.vertices] for t in tris], np.float32)
NZ = np.array([[nz[v] for v in t.vertices] for t in tris], np.float32)
np.savez(os.path.join(common.WORK, 'uv3d.npz'), uv=U, xyz=X, curv=C, nz=NZ)
print('DUMPED', len(tris), 'top z', float(X[..., 2].max()), 'curv p5/p50/p95', np.percentile(C, [5, 50, 95]).round(3))
# ---- 2. AO of the blob alone
obj.modifiers.clear()
bm = bmesh.new()
bm.from_mesh(me)
bm.faces.ensure_lookup_table()
bmesh.ops.delete(bm, geom=[f for f in bm.faces if part[f.index] != 0], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me)
bm.free()
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = 96
if sc.world is None:
    sc.world = bpy.data.worlds.new('w')
sc.world.light_settings.distance = 0.02
img = bpy.data.images.new('ao', 2048, 2048, alpha=False, float_buffer=False)
mat = bpy.data.materials.new('bake'); mat.use_nodes = True
node = mat.node_tree.nodes.new('ShaderNodeTexImage'); node.image = img; mat.node_tree.nodes.active = node
me.materials.clear(); me.materials.append(mat)
for o in bpy.data.objects:
    o.select_set(o == obj)
bpy.context.view_layer.objects.active = obj
sc.render.bake.margin = 8
sc.render.bake.use_selected_to_active = False
bpy.ops.object.bake(type='AO')
img.filepath_raw = os.path.join(common.WORK, 'ao_body.png'); img.file_format = 'PNG'; img.save()
print('BAKED', img.filepath_raw, len(me.polygons))
