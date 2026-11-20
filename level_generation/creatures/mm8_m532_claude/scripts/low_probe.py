"""Lowest body vertices of an action frame with their dominant bones. Usage: blender -b -P low_probe.py -- <blend> <action> <frame>"""
import bpy, sys
from collections import Counter
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=a[0]); sc = bpy.context.scene; rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']
rig.animation_data.action = bpy.data.actions[a[1]]; rig.animation_data.action_slot = rig.animation_data.action.slots[0]; sc.frame_set(int(a[2]))
names = [g.name for g in body.vertex_groups]
ev = body.evaluated_get(bpy.context.evaluated_depsgraph_get()); me = ev.to_mesh()
low = sorted(((body.matrix_world @ v.co).z, v.index) for v in me.vertices)[:40]
dom = lambda i: names[max(body.data.vertices[i].groups, key=lambda g: g.weight).group]
print('LOW', [(round(z * 1000, 1), dom(i)) for z, i in low[:12]], Counter(dom(i) for _, i in low))
