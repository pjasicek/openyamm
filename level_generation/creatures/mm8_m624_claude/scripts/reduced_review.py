import bpy,sys,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.render.resolution_x=sc.render.resolution_y=1100;sc.render.resolution_percentage=100
if not sc.world:sc.world=bpy.data.worlds.new('World')
sc.world.color=(.12,.12,.14);cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for clip,t in [('Standing',0),('Attack',.7),('Attack',1.),('Death',1.5)]:
 rig.animation_data.action=bpy.data.actions[clip];sc.frame_set(round(t*24));bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();coords=[ob.evaluated_get(deps).matrix_world@v.co for ob in bpy.data.objects if ob.type=='MESH' for v in ob.evaluated_get(deps).data.vertices];target=Vector(tuple((min(p[i]for p in coords)+max(p[i]for p in coords))/2 for i in range(3)))
 for view,offset in [('front',(0,-6,1)),('quarter',(4,-6,2)),('side',(6,0,1))]:
  cam.location=target+Vector(offset);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();inv=cam.rotation_euler.to_matrix().transposed();c=[inv@(p-target)for p in coords];cam.data.ortho_scale=1.13*max(max(p[i]for p in c)-min(p[i]for p in c)for i in [0,1]);sc.render.filepath=str(P/'review'/f'reduced_{clip}_{t}_{view}.png');bpy.ops.render.render(write_still=True)
