"""Print per-bone lowest vertex z (cm) of work/anim_v1.blend at clip:frame. Usage: probe_pose.py <clip> <frame>"""
import bpy, os, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Scorpion_Rig']; mesh = bpy.data.objects['Scorpion']
act = bpy.data.actions[a[0]]; rig.animation_data.action = act
if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
bpy.context.scene.frame_set(int(a[1]))
dg = bpy.context.evaluated_depsgraph_get(); ev = mesh.evaluated_get(dg); me = ev.to_mesh()
co = np.array([v.co[:] for v in me.vertices]) @ np.array(mesh.matrix_world.to_3x3()).T + np.array(mesh.matrix_world.translation)
names = [g.name for g in mesh.vertex_groups]
dom = np.array([names[max(v.groups, key=lambda g: g.weight).group] for v in mesh.data.vertices])
for n in ('Body', 'Abdomen', 'Tail1', 'Tail2', 'Tail3', 'Tail4', 'Tail5', 'Stinger', 'Chela_L', 'Chela_R'):
    s = co[dom == n]
    print(f'PROBE {n:8s} minz {s[:, 2].min()*100:6.1f} maxz {s[:, 2].max()*100:6.1f} y {s[:, 1].mean():.2f}')
for b in ('Tail1', 'Stinger'):
    print('BONE', b, [round(x, 3) for x in rig.matrix_world @ rig.pose.bones[b].head], [round(x, 3) for x in rig.matrix_world @ rig.pose.bones[b].tail])
