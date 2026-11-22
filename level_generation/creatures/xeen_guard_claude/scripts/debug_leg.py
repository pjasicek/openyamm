import bpy, os, sys
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_v1.blend'))
rig = bpy.data.objects['Guard_Rig']
act = bpy.data.actions[a[0]]; rig.animation_data.action = act
if len(getattr(act, 'slots', [])): rig.animation_data.action_slot = act.slots[0]
s = a[1]
for f in range(int(act.frame_range[0]), int(act.frame_range[1]) + 1):
    bpy.context.scene.frame_set(f)
    pb = rig.pose.bones
    print('LEG', f, 'hip', [round(x, 3) for x in pb[f'B_{s}_Thigh'].head], 'knee', [round(x, 3) for x in pb[f'B_{s}_Calf'].head],
          'ankle', [round(x, 3) for x in pb[f'B_{s}_Foot'].head], 'pelvis', [round(x, 3) for x in pb['B_Pelvis'].head])
