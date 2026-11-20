import bpy,json,traceback,shutil
from pathlib import Path
from mathutils import Vector
ROOT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923');OUT=ROOT/'rig_review_01';OUT.mkdir(exist_ok=True)
p=Path('/home/pjasicek/Downloads/Meshy_AI_mm6_goblin_10577_mesh_All_Animations.glb');shutil.copyfile(p,OUT/'meshy_returned.glb')
s=bpy.data.scenes.new('Goblin - Meshy Rig Diagnosis');bpy.context.window.scene=s;before=set(bpy.data.actions);bpy.ops.import_scene.gltf(filepath=str(p));actions=[a for a in bpy.data.actions if a not in before]
meshes=[o for o in s.objects if o.type=='MESH'];arms=[o for o in s.objects if o.type=='ARMATURE'];arm=arms[0];mesh=max(meshes,key=lambda o:len(o.data.polygons))
for o in meshes:
 if o!=mesh:o.hide_render=True
if arm.animation_data:
 for t in arm.animation_data.nla_tracks:t.mute=True
arm.data.pose_position='REST';s.frame_set(1)
verts=[mesh.matrix_world@v.co for v in mesh.data.vertices];lo=Vector(tuple(min(v[i] for v in verts) for i in range(3)));hi=Vector(tuple(max(v[i] for v in verts) for i in range(3)));center=(lo+hi)/2;height=hi.z-lo.z
report={'scene':s.name,'armature':arm.name,'mesh':mesh.name,'bounds':[list(lo),list(hi)],'actions':[{'name':a.name,'range':list(a.frame_range),'slots':[sl.identifier for sl in a.slots]} for a in actions],'bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'head':list(arm.matrix_world@b.head_local),'tail':list(arm.matrix_world@b.tail_local)} for b in arm.data.bones]};(OUT/'blender_inventory.json').write_text(json.dumps(report,indent=2))
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=True;s.cycles.device='CPU';s.render.resolution_x=850;s.render.resolution_y=1000;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.view_settings.view_transform='AgX';s.render.fps=30
s.world=bpy.data.worlds.new('Rig review world');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.15,.17,.20,1);s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.5
cd=bpy.data.cameras.new('Rig review camera');cam=bpy.data.objects.new('Rig review camera',cd);s.collection.objects.link(cam);s.camera=cam;cd.type='ORTHO';cd.ortho_scale=height*1.35;cam.location=center+Vector((0,-height*3,height*.08));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
for name,off,power,size in [('Key',(-3,-4,5),650,3),('Fill',(4,-2,2),400,4),('Rim',(1,3,4),800,3)]:
 ld=bpy.data.lights.new('Rig '+name,'AREA');ld.energy=power*(height/1.9)**2;ld.size=size*height/1.9;ob=bpy.data.objects.new('Rig '+name,ld);s.collection.objects.link(ob);ob.location=center+Vector(off)*height/1.9;ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
clay=bpy.data.materials.new('Rig diagnostic clay');clay.use_nodes=True;clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.32,.34,.36,1);clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.7
jobs=[('rest','material',None,1),('rest','clay',None,1)]
for key in ['Idle_3','Walking','Right_Hand_Sword_Slash']:
 a=next(a for a in actions if key in a.name)
 for t in [.25,.6]:jobs.append((key+'_'+str(t),'material',a,a.frame_range[0]+t*(a.frame_range[1]-a.frame_range[0])))

def step():
 try:
  bpy.context.window.scene=s
  if not jobs:
   bpy.data.libraries.write(str(OUT/'rig_diagnosis.blend'),{s},fake_user=True,compress=True);(OUT/'render_done.txt').write_text('complete');return None
  name,mode,a,frame=jobs.pop(0);(OUT/'progress.txt').write_text(name+' '+mode)
  arm.data.pose_position='REST' if a is None else 'POSE'
  if a:
   arm.animation_data_create();arm.animation_data.action=a
   if a.slots:arm.animation_data.action_slot=a.slots[0]
  s.frame_set(int(frame),subframe=frame-int(frame));s.view_layers[0].material_override=clay if mode=='clay' else None;s.render.filepath=str(OUT/(name+'_'+mode+'.png'));bpy.ops.render.render(write_still=True);return .1
 except Exception:(OUT/'error.txt').write_text(traceback.format_exc());return None
bpy.app.timers.register(step,first_interval=.1);print(json.dumps(report))
