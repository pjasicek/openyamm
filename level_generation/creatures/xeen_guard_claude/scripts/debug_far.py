"""Per bone: posed bounding box at one clip frame (find stray pieces)."""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Guard_Rig']; mesh = bpy.data.objects['Guard']
act = bpy.data.actions[a[0]]; rig.animation_data.action = act
if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[1]))
ev = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
P = np.array([v.co[:] for v in ev.vertices]); R = np.array([v.co[:] for v in mesh.data.vertices])
gi = {g.index: g.name for g in mesh.vertex_groups}
vb = np.array([gi[v.groups[0].group] for v in mesh.data.vertices])
me = mesh.data
part = np.zeros(len(me.vertices), int)
for p in me.polygons:
    for i in p.vertices: part[i] = me.attributes['part'].data[p.index].value
for b in sorted(set(vb)):
    for pt in sorted(set(part[vb == b])):
        m = (vb == b) & (part == pt)
        print(f'BOX {b:15s} part {pt} n {m.sum():4d} pose min {P[m].min(0).round(2)} max {P[m].max(0).round(2)}  rest min {R[m].min(0).round(2)} max {R[m].max(0).round(2)}')
