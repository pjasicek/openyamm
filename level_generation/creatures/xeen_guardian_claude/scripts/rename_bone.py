"""One-off (2026-11-20): rename the bone 'Skull' to 'Cranium' in work/anim_base.blend (the locked UV master), because
the glTF joint node 'Skull' collided with the mesh node 'Skull' (build_actor_lods.py found the joint). The vertex
group follows the bone. rig.py now names it Cranium directly."""
import bpy, os
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
rig = bpy.data.objects['Guardian_Rig']; mesh = bpy.data.objects['Skull']
rig.data.bones['Skull'].name = 'Cranium'
print('RENAMED', [b.name for b in rig.data.bones], [g.name for g in mesh.vertex_groups])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'anim_base.blend'))
