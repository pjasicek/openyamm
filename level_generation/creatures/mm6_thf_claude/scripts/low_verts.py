import bpy, sys, os, json
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import common
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, a[0]))
arm = bpy.data.objects['Thief_Rig']; mesh = bpy.data.objects['Thief']; me = mesh.data
act = bpy.data.actions[a[1]]; arm.animation_data.action = act; arm.animation_data.action_slot = act.slots[0]
PARTS = json.loads(bpy.context.scene['thf_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
vp = {}
for p in me.polygons:
    for v in p.vertices: vp.setdefault(v, PARTS[part[p.index]])
G = {g.index: g.name for g in mesh.vertex_groups}
f0, f1 = (int(round(x)) for x in act.frame_range)
for f in sorted({f0, (f0 + f1) // 2, f1, int(a[2]) if len(a) > 2 else f1}):
    bpy.context.scene.frame_set(f)
    ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()); m = ev.to_mesh()
    z = np.array([(mesh.matrix_world @ v.co).z for v in m.vertices]); ev.to_mesh_clear()
    idx = np.argsort(z)[:5]
    print('LOW', a[1], f, [(int(i), vp.get(int(i)), round(float(z[i]), 3), max(me.vertices[i].groups, key=lambda g: g.weight).group and G[max(me.vertices[i].groups, key=lambda g: g.weight).group]) for i in idx])
