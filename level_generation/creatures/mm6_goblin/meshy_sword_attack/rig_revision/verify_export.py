import bpy,json,math
import numpy as np
from mathutils import Vector
from pathlib import Path
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_sword_attack/rig_revision');out=ROOT/'review';source=bpy.data.scenes['Goblin Arm Rig Revision'];source_rig=bpy.data.objects['Goblin Arm Revision Rig'];source_action=bpy.data.actions[json.loads(source['authored_actions'])['Attack']]
scene=bpy.data.scenes.new('Delivered Arm Revision Verification');bpy.context.window.scene=scene;before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(ROOT/'goblin_arm_revision.glb'));rig=next(o for o in scene.objects if o.type=='ARMATURE');actions={a.name:a for a in bpy.data.actions if a not in before};action=next(a for a in actions.values() if a.name.startswith('MM6_Attack_Rig_Revision'))
for tr in rig.animation_data.nla_tracks:tr.mute=True
for o in scene.objects:
 if o.type=='MESH' and o.find_armature()!=rig:o.hide_render=True;o.hide_set(True)
for pb in rig.pose.bones:pb.custom_shape=None
checks=[]
def sample(sc,rg,act,frame):
 bpy.context.window.scene=sc;rg.animation_data.action=act;rg.animation_data.action_slot=act.slots[0];sc.frame_set(frame);bpy.context.view_layer.update();bones={b.name:(rg.matrix_world@b.matrix).copy() for b in rg.pose.bones};lo=[];hi=[];dep=bpy.context.evaluated_depsgraph_get()
 for o in sc.objects:
  if o.type!='MESH' or o.find_armature()!=rg:continue
  e=o.evaluated_get(dep);m=e.to_mesh();ar=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',ar);ar=ar.reshape(-1,3);w=np.array(e.matrix_world);ar=ar@w[:3,:3].T+w[:3,3];lo.append(ar.min(axis=0));hi.append(ar.max(axis=0));e.to_mesh_clear()
 return bones,np.min(lo,axis=0),np.max(hi,axis=0)
for frame in range(19):
 b0,l0,h0=sample(source,source_rig,source_action,frame+1);b1,l1,h1=sample(scene,rig,action,frame)
 checks.append({'frame':frame,'max_joint_position_error':max((b0[n].translation-b1[n].translation).length for n in b0),'max_joint_angle_error_degrees':max(math.degrees(b0[n].to_quaternion().rotation_difference(b1[n].to_quaternion()).angle) for n in b0),'max_bounds_error':float(max(abs(l0-l1).max(),abs(h0-h1).max()))})
report={'animation_names':list(actions),'duration_seconds':(action.frame_range[1]-action.frame_range[0])/24,'samples':checks,'grip_morphs':{o.name:{k.name:k.value for k in o.data.shape_keys.key_blocks} for o in scene.objects if o.type=='MESH' and o.data.shape_keys}}
(out/'export_verification.json').write_text(json.dumps(report,indent=2));print(json.dumps({'duration':report['duration_seconds'],'max_position_error':max(c['max_joint_position_error'] for c in checks),'max_bounds_error':max(c['max_bounds_error'] for c in checks),'morphs':report['grip_morphs']}))
# Render the actual delivered export, using the reviewed lighting.
bpy.context.window.scene=scene;rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];scene.frame_set(3)
for o in source.objects:
 if o.type=='LIGHT':scene.collection.objects.link(o)
scene.world=source.world;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.render.image_settings.color_mode='RGBA';scene.view_settings.view_transform='AgX'
camdata=bpy.data.cameras.new('Export verification camera');cam=bpy.data.objects.new('Export verification camera',camdata);scene.collection.objects.link(cam);scene.camera=cam;camdata.type='ORTHO';camdata.ortho_scale=2.65;target=Vector((0,0,1.10));cam.location=target+Vector((0,-5,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(out/'delivered_attack.png');bpy.ops.render.render(write_still=True)
# Standalone sword render from its actual GLB.
weapon=bpy.data.scenes.new('Delivered Standalone Sword Verification');bpy.context.window.scene=weapon;bpy.ops.import_scene.gltf(filepath=str(ROOT/'mm6_goblin_sword.glb'));weapon.world=source.world
for o in source.objects:
 if o.type=='LIGHT':weapon.collection.objects.link(o)
wc=cam.copy();wc.data=cam.data.copy();weapon.collection.objects.link(wc);weapon.camera=wc;wc.data.ortho_scale=1.14;target=Vector((0,.375,.02));wc.location=target+Vector((3,-.25,1));wc.rotation_euler=(target-wc.location).to_track_quat('-Z','Y').to_euler();weapon.render.engine='CYCLES';weapon.cycles.samples=32;weapon.cycles.use_denoising=True;weapon.render.resolution_x=1100;weapon.render.resolution_y=450;weapon.render.resolution_percentage=100;weapon.render.film_transparent=True;weapon.render.image_settings.color_mode='RGBA';weapon.view_settings.view_transform='AgX';weapon.render.filepath=str(out/'sword.png');bpy.ops.render.render(write_still=True)
bpy.context.window.scene=source
