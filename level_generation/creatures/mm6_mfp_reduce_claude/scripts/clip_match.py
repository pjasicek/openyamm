"""Spliced clip check: joints of the blend's action vs the same clip imported from a GLB, every frame.
Args: -- <glb> <action>   (run with the authoring blend open)"""
import bpy, sys
glb, an = sys.argv[sys.argv.index('--') + 1:]
rig = bpy.data.objects['Rig']; W = rig.matrix_world; sc = bpy.context.scene; sc.render.fps = 30
mine = bpy.data.actions[an]; before = set(bpy.data.actions); bo = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
g = next(o for o in set(bpy.data.objects) - bo if o.type == 'ARMATURE')
ga = next(a for a in set(bpy.data.actions) - before if a.name.split('_')[0].startswith(an) or a.name.startswith(an))
rig.animation_data.action = mine; rig.animation_data.action_slot = mine.slots[0]
g.animation_data.action = ga; g.animation_data.action_slot = ga.slots[0]
worst = 0
for f in range(int(mine.frame_range[0]), int(mine.frame_range[1]) + 1):
    sc.frame_set(f)
    for n in ('B_R_Hand', 'Socket_Knife_Tip', 'B_Head', 'B_L_Hand', 'B_L_Foot', 'Braid_2', 'Skirt_2_11'):
        worst = max(worst, ((W @ rig.pose.bones[n].head) - (g.matrix_world @ g.pose.bones[n].head)).length)
print('MATCH', an, ga.name, 'frames', ga.frame_range[:], 'max joint diff mm', round(worst * 1000, 3), 'knife scale', [round(x, 3) for x in g.pose.bones['Knife'].scale])
