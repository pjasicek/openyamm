"""Eight-view silhouette comparisons at actual LOD switch sizes, body and staff independently."""
import bpy,sys,math
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
frames={}
for level in range(1,4):
 for source in [0,level]:
  bpy.ops.wm.open_mainfile(filepath=str(p/'work'/f'runtime_lod{source}_r3.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];rig.animation_data.action=None
  for pb in rig.pose.bones:pb.matrix_basis.identity()
  bpy.context.view_layer.update();rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=bpy.data.actions['Standing'].slots[0];scene.frame_set(0);common.workbench_clay(scene,textured=True);scene.render.film_transparent=True
  for part in ['Body','Staff','Actor']:
   objects=[bpy.data.objects[x] for x in (['Body','Staff'] if part=='Actor' else [part])]
   for o in bpy.data.objects:
    if o.type=='MESH':o.hide_render=o not in objects
   lo,hi=common.world_bounds(objects);centre=(lo+hi)/2;h=hi.z-lo.z;res=int(round([0,550,220,88][level]*1.1));scene.render.resolution_x=scene.render.resolution_y=res;scene.render.resolution_percentage=100;cam=common.ortho_camera('LODCamera',(0,-6,centre.z),(math.pi/2,0,0),h*1.1);scene.camera=cam
   # Identical reference framing across levels is derived from the full-resolution object bounds.
   if source==0:frames[(level,part)]=(centre.copy(),h)
   else:centre,h=frames[(level,part)];cam.data.ortho_scale=h*1.1
   for i in range(8):
    a=i*math.pi/4;cam.location=(centre.x+6*math.sin(a),centre.y-6*math.cos(a),centre.z);cam.rotation_euler=(math.pi/2,0,a);scene.render.filepath=str(p/'review/round3/reduction'/f'switch{level}_{part}_{source}_{i}.png');bpy.ops.render.render(write_still=True)
