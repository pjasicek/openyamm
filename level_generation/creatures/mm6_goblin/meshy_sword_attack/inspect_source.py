import bpy,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack')
scene=bpy.data.scenes.get('Meshy Goblin Sword and Native Attack')
if scene is None:
 scene=bpy.data.scenes.new('Meshy Goblin Sword and Native Attack');bpy.context.window.scene=scene;before=set(bpy.data.actions)
 bpy.ops.import_scene.gltf(filepath='/home/pjasicek/github/OpenYAMM/output/meshy_goblin_v2_review/goblin_2_head_corrected.glb')
 names=['Running','Walking','Attack','Fall_Dead_from_Abdominal_Injury','Hit_Reaction_1','Idle_11','Idle_3','Right_Hand_Sword_Slash','walking_2','restpose']
 scene['source_actions']=json.dumps({k:a.name for a in bpy.data.actions if a not in before for k in names if a.name==k or a.name.startswith(k+'.')})
else:bpy.context.window.scene=scene
rig=next(o for o in scene.objects if o.type=='ARMATURE');rig.name='MM6 Meshy Goblin Rig'
for tr in rig.animation_data.nla_tracks:tr.mute=True
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity();pb.custom_shape=None
mesh=next(o for o in scene.objects if o.type=='MESH' and o.find_armature()==rig);mesh.name='Meshy Goblin Body'
for o in scene.objects:
 if o.type=='MESH' and o!=mesh:o.hide_render=True;o.hide_set(True)
print(json.dumps({'matrix':list(map(list,rig.matrix_world)), 'bones':{b.name:{'head':list(b.head_local),'tail':list(b.tail_local),'length':b.length,'matrix':list(map(list,b.matrix_local))} for b in rig.data.bones if any(x in b.name for x in ['RightArm','ForeArm','RightHand','Shoulder','Hips','Head','Spine','Foot'])}},indent=2))
