"""How far MM9's jaw opens: per clip, the max displacement (in the Xhead frame) of the jaw vertices relative to the
bind and of the frontmost jaw vertex. Args: <rig blend>"""
import bpy, sys, json
import numpy as np
argv = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=argv[0])
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
body = bpy.data.objects['body.mesh']
jaw = [v.index for v in body.data.vertices if max(v.groups, key=lambda g: g.weight).group == body.vertex_groups['Xjawpiv'].index]
dg = bpy.context.evaluated_depsgraph_get()


def jaw_in_head():
    dg.update()
    me = body.evaluated_get(dg).to_mesh()
    H = (arm.matrix_world @ arm.pose.bones['Xhead'].matrix).inverted()
    P = np.array([tuple(H @ (body.matrix_world @ me.vertices[i].co)) for i in jaw])
    body.evaluated_get(dg).to_mesh_clear()
    return P


arm.animation_data.action = bpy.data.actions['stand']
sc.frame_set(0)
bind = jaw_in_head()   # reference: the closed mouth of stand frame 0 (every clip offsets the jaw from the bind)
yfront = bind[:, 1].argmin()
out = {}
for act in bpy.data.actions:
    arm.animation_data.action = act
    f0, f1 = int(act.frame_range[0]), int(act.frame_range[1])
    best = (0, 0)
    for f in range(f0, f1 + 1):
        sc.frame_set(f)
        d = np.linalg.norm(jaw_in_head() - bind, axis=1).max()
        if d > best[0]:
            best = (d, f)
    out[act.name] = [round(best[0], 4), best[1]]
print('JAW ' + json.dumps(out))
