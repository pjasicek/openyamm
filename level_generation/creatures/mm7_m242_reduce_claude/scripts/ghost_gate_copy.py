"""Gate copy of a ghost GLB for ../mm7_m242_claude/scripts/ghost_gates.py: imports <glb> (welded exactly like the
ladder source), names Body/Rig, and gives each vertex the 'cloth' and 'piece' attributes of the nearest vertex of the
production master (../mm7_m242_claude/work/rig_v6.blend, rest pose; the hood gate reads piece 1 = the cape shell).
Args: -- <glb> <out blend>"""
import bpy, bmesh, sys, os
import numpy as np
from mathutils.kdtree import KDTree
glb, out = sys.argv[sys.argv.index('--') + 1:]
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, '..', 'mm7_m242_claude', 'work', 'rig_v6.blend'))
m = bpy.data.objects['Body']; mr = bpy.data.objects['Rig']; mr.animation_data_create(); mr.animation_data.action = None
mco = np.array([tuple(m.matrix_world @ v.co) for v in m.data.vertices])
cl = np.zeros(len(mco), np.int32); m.data.attributes['cloth'].data.foreach_get('value', cl)
pc = np.zeros(len(mco), np.int32); m.data.attributes['piece'].data.foreach_get('value', pc)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.abspath(glb))
body = next(o for o in bpy.data.objects if o.type == 'MESH' and o.name == 'M242')
rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
for o in list(bpy.data.objects):
    if o.type == 'MESH' and o is not body:
        bpy.data.objects.remove(o, do_unlink=True)
body.name = 'Body'; rig.name = 'Rig'
bm = bmesh.new(); bm.from_mesh(body.data); dl = bm.verts.layers.deform.active
sig = lambda v: tuple(sorted((g, round(w, 4)) for g, w in v[dl].items()))
cls = {}
for v in bm.verts:
    cls.setdefault(sig(v), []).append(v)
for vs in cls.values():
    bmesh.ops.remove_doubles(bm, verts=vs, dist=1e-6)
bm.to_mesh(body.data); bm.free()
kd = KDTree(len(mco))
for i, c in enumerate(mco):
    kd.insert(c, i)
kd.balance()
idx = [kd.find(body.matrix_world @ v.co)[1] for v in body.data.vertices]
body.data.attributes.new('cloth', 'INT', 'POINT').data.foreach_set('value', cl[idx].tolist())
body.data.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', pc[idx].tolist())
print('GATECOPY', os.path.basename(glb), 'verts', len(body.data.vertices), 'tris', sum(len(p.vertices) - 2 for p in body.data.polygons))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
