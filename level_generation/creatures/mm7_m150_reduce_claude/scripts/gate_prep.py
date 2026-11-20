"""Gate copy of an exported Angel GLB (REA_GLB, node M150) for the original project's gates (g6_skirt_poke.py,
waist_stretch.py, shield_gate.py, g6_contacts.py): Body + Rig, exact duplicates with equal weights welded (as
import_source.py), and the master's per-vertex attributes piece / garment carried by nearest master vertex at rest
(../mm7_m150_claude/work/rig_v6.blend, read only). Writes REA_OUT. Usage: blender -b -P gate_prep.py"""
import os, bpy, bmesh
import numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(HERE), 'mm7_m150_claude', 'work', 'rig_v6.blend'))
r = bpy.data.objects['Rig']; r.animation_data_create(); r.animation_data.action = None
for pb in r.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
mb = bpy.data.objects['Body']; mme = mb.data
MC = np.array([tuple(mb.matrix_world @ v.co) for v in mme.vertices])
MP = np.zeros(len(MC), np.int32); mme.attributes['piece'].data.foreach_get('value', MP)
MG = np.zeros(len(MC), np.int32); mme.attributes['garment'].data.foreach_get('value', MG)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(ROOT, os.environ['REA_GLB']))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'M150')
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
body.name = 'Body'; rig.name = 'Rig'
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body:
        bpy.data.objects.remove(o, do_unlink=True)
bm = bmesh.new(); bm.from_mesh(body.data); dl = bm.verts.layers.deform.active
sig = lambda v: tuple(sorted((g, round(w, 4)) for g, w in v[dl].items())) if dl else ()
cls = {}
for v in bm.verts:
    cls.setdefault(sig(v), []).append(v)
for vs in cls.values():
    bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-6)
bm.to_mesh(body.data); bm.free(); body.data.update()
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
kd = kdtree.KDTree(len(MC))
for i, c in enumerate(MC):
    kd.insert(c, i)
kd.balance()
co = [body.matrix_world @ v.co for v in body.data.vertices]
hit = [kd.find(c) for c in co]; idx = np.array([h[1] for h in hit]); dist = np.array([h[2] for h in hit])
for name, arr in (('piece', MP), ('garment', MG)):
    a = body.data.attributes.new(name, 'INT', 'POINT'); a.data.foreach_set('value', arr[idx].astype(np.int32).tolist())
print('GATEPREP', os.environ['REA_GLB'], 'verts', len(co), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons),
      'master match mm p99/max', round(float(np.percentile(dist, 99)) * 1000, 2), round(float(dist.max()) * 1000, 2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, os.environ['REA_OUT']))
