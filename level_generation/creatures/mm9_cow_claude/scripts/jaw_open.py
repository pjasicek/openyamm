"""Per clip: how far the MM9 jaw-weighted vertices move relative to the head bone (mouth opening), and the bones
that own vertices. Args: <mm9 rig blend> <head bone> <jaw bones comma>"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
HEAD, JAW = argv[1], argv[2].split(',')
arm = bpy.data.objects['MM9_Rig']
own = {}
jaw = []
for o in bpy.data.objects:
    if o.type != 'MESH':
        continue
    for v in o.data.vertices:
        g = max(v.groups, key=lambda g: g.weight)
        n = o.vertex_groups[g.group].name
        own[n] = own.get(n, 0) + 1
        if n in JAW:
            jaw.append((o, v.index))
print('OWNERS', json.dumps(own))
sc = bpy.context.scene
dg = bpy.context.evaluated_depsgraph_get()
def jaw_local():
    hm = arm.matrix_world @ arm.pose.bones[HEAD].matrix
    inv = hm.inverted()
    out = []
    cache = {}
    for o, i in jaw:
        if o.name not in cache:
            cache[o.name] = (o, o.evaluated_get(dg).to_mesh())
        out.append(tuple(inv @ (o.matrix_world @ cache[o.name][1].vertices[i].co)))
    for o, m in cache.values():
        o.evaluated_get(dg).to_mesh_clear()
    return np.array(out)
arm.animation_data.action = bpy.data.actions['static_model']
sc.frame_set(0)
ref = jaw_local()
for act in bpy.data.actions:
    arm.animation_data.action = act
    f0, f1 = act.frame_range
    m = 0
    for f in np.linspace(f0, f1, 30):
        sc.frame_set(int(f), subframe=f - int(f))
        m = max(m, np.linalg.norm(jaw_local() - ref, axis=1).max())
    print('JAW %s %.4f' % (act.name, m))
