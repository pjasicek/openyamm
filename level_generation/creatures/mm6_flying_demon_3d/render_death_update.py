"""Fixed cameras on reimported final GLBs, with dense motion and material details."""
from pathlib import Path
import bpy, json, hashlib
from mathutils import Vector
P=Path(__file__).resolve().parent
scene=bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o,do_unlink=True)
scene.render.fps=48;scene.render.engine='BLENDER_EEVEE';scene.eevee.taa_render_samples=24
scene.render.resolution_x=scene.render.resolution_y=640;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=92
scene.view_settings.view_transform='Standard';scene.world.color=(.12,.12,.12)
camera=bpy.data.objects.new('Flying_Review_Camera',bpy.data.cameras.new('Flying_Review_Camera'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=3.1
for name,pos,power in [('Key',(-3,-4,5),500),('Fill',(3,1,3),250)]:
 data=bpy.data.lights.new(name,'AREA');data.energy=power;data.size=4
 light=bpy.data.objects.new(name,data);scene.collection.objects.link(light);light.location=pos;light.rotation_euler=(Vector((0,0,1))-light.location).to_track_quat('-Z','Y').to_euler()
VIEWS={'front':(0,-6,0),'diagonal':(4.2,-4.2,0),'profile':(6,0,0),'rear_diagonal':(4.2,4.2,0),'back':(0,6,0)}
CLIPS={'Death':42};out=P/'review/preview_frames';out.mkdir(exist_ok=True);rendered=json.loads((P/'work/render_manifest_before_death.json').read_text())['rendered']
def select(clip,frame):
 for o in scene.objects:
  for owner in (o,o.data.shape_keys if o.type=='MESH' else None):
   if owner and owner.animation_data:
    tracks=[t for t in owner.animation_data.nla_tracks if t.name==clip]
    for t in owner.animation_data.nla_tracks: t.mute=True
    owner.animation_data.action=tracks[0].strips[0].action if tracks else None
    if tracks: owner.animation_data.action_slot=tracks[0].strips[0].action_slot
 scene.frame_set(frame);bpy.context.view_layer.update()
def shot(path,view,center=Vector((0,.12,1.26)),scale=3.1):
 camera.data.ortho_scale=scale;direction=Vector(VIEWS[view]);camera.location=center+direction
 camera.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);rendered.append(str(path.relative_to(P)))
for variant in 'abc':
 old=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(P/'delivery'/f'mm6_flying_demon_{variant}.glb'));imported=set(scene.objects)-old
 select('Flight',0)
 for view in ('front','profile','back'): shot(P/'review'/f'{variant}_{view}.jpg',view)
 shot(P/'review'/f'{variant}_face.jpg','front',Vector((0,-.22,1.895)),.50)
 select('Death',24);shot(P/'review'/f'{variant}_death_peak.jpg','front')
 if variant=='a':
  for clip,end in CLIPS.items():
   for view in VIEWS:
    for frame in (range(end+1) if clip!='Ash_Remains' else [0]):
     select(clip,frame);shot(out/f'{clip}_{view}_{frame:02d}.jpg',view)
   print('Rendered actual export',clip,'dense five-view motion',flush=True)
  for clip,frame,focus,center,scale in [
   ('Flight',12,'wings',Vector((0,.35,1.86)),2.4),('Flight',0,'feet',Vector((0,-.25,.40)),.60),
   ('Attack',18,'hands',Vector((0,-.35,1.36)),1.6),('Attack',24,'wrist',Vector((.02,-.53,1.38)),.7),
   ('Hit',12,'shoulders',Vector((0,-.10,1.66)),1.35)]:
   select(clip,frame);shot(P/'review'/f'detail_{focus}_{clip}_{frame}.jpg','diagonal',center,scale)
 for o in imported: bpy.data.objects.remove(o,do_unlink=True)
(P/'review/render_manifest.json').write_text(json.dumps({'artifact_sha256':{v:hashlib.sha256((P/'delivery'/f'mm6_flying_demon_{v}.glb').read_bytes()).hexdigest() for v in 'abc'},'actual_export_reimport':True,'fixed_camera_scale':3.1,'camera_center':[0,.12,1.26],'views':VIEWS,'dense_fps':48,'rendered':sorted(set(rendered)),'rerendered_clips':['Death'],'unchanged_clip_preservation':'work/death_change_preservation.json'},indent=2)+'\n')
print('Rendered',len(rendered),'actual exported frames and material views.',flush=True)
