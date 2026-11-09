import bpy,json,math,traceback
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'rig_review_01/skirt_clearance';src=bpy.data.scenes['Goblin - Upright Rig Review'];oa=next(o for o in src.objects if o.type=='ARMATURE');om=next(o for o in src.objects if o.type=='MESH')
s=bpy.data.scenes.new('Goblin - Skirt Clearance v3');bpy.context.window.scene=s;s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.device='CPU';s.cycles.use_denoising=True;s.world=src.world;s.view_settings.view_transform='AgX';s.render.resolution_x=850;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.fps=24
arm=oa.copy();arm.data=oa.data.copy();arm.name='Goblin_SkirtClearance_Rig';s.collection.objects.link(arm);arm.animation_data_clear();arm.animation_data_create()
mesh=om.copy();mesh.data=om.data.copy();mesh.name='Goblin_SkirtClearance_10577';s.collection.objects.link(mesh);mat=om.matrix_world.copy();mesh.parent=arm;mesh.matrix_world=mat
for m in mesh.modifiers:
 if m.type=='ARMATURE':m.object=arm
for o in src.objects:
 if o.type in ['CAMERA','LIGHT']:
  cp=o.copy();cp.data=o.data.copy();s.collection.objects.link(cp)
  if cp.type=='CAMERA':s.camera=cp
# UV seams split inner and outer shells. Pair each strip by coincident bounds.
parts=json.loads((OUT/'components.json').read_text());parts=[p for p in parts if p['n']<30];strips=[]
while parts:
 a=parts.pop(0);j=min(range(len(parts)),key=lambda j:sum((parts[j]['min'][k]-a['min'][k])**2+(parts[j]['max'][k]-a['max'][k])**2 for k in range(3)));b=parts.pop(j);ids=a['ids']+b['ids'];coords=[mesh.data.vertices[i].co for i in ids];zmax=max(v.z for v in coords);top=[v for v in coords if v.z>zmax-.017];pivot=sum(top,Vector())/len(top);radial=Vector((pivot.x,pivot.y-.035,0)).normalized();axis=Vector((radial.y,-radial.x,0));strips.append({'ids':ids,'pivot':list(pivot),'axis':list(axis),'radial':list(radial),'name':'Skirt_%02d'%len(strips)})
bpy.ops.object.select_all(action='DESELECT');arm.select_set(True);bpy.context.view_layer.objects.active=arm;bpy.ops.object.mode_set(mode='EDIT')
for p in strips:
 b=arm.data.edit_bones.new(p['name']);b.head=p['pivot'];b.tail=Vector(p['pivot'])+Vector((0,0,-.15));b.parent=arm.data.edit_bones['mixamorig:Hips'];b.use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
for p in strips:
 for g in mesh.vertex_groups:g.remove(p['ids'])
 g=mesh.vertex_groups.new(name=p['name']);g.add(p['ids'],1,'REPLACE');arm.pose.bones[p['name']].rotation_mode='QUATERNION'
for key in ['Idle_3','Walking','Running','Right_Hand_Sword_Slash','restpose']:
 a=bpy.data.actions['Goblin_Upright_'+key].copy();a.name='Goblin_Skirt_'+key;a.use_fake_user=True
arm.animation_data.action=bpy.data.actions['Goblin_Skirt_Walking'];arm.animation_data.action_slot=arm.animation_data.action.slots[0];s.frame_start=1;s.frame_end=26;s.frame_set(15)
(OUT/'strips.json').write_text(json.dumps(strips,indent=2));print('Prepared',len(strips),'rigid hinged strips; preserved original geometry and UVs')
