import bpy, numpy as np, json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));o=bpy.data.objects['Body']
# Meshy overextended the tail; fit its rest silhouette to the selected profile masters.
for v in o.data.vertices:
 if v.co.y>-.8:v.co.y=-.8+(v.co.y+.8)*.50
 v.co.y+=1.45
c=np.array([v.co[:] for v in o.data.vertices]);np.savez(P/'work/fitted_geometry.npz',co=c,tri=np.load(P/'work/geometry.npz')['tri'],parts=np.load(P/'work/geometry.npz')['parts'])
(P/'work/silhouette_fit.json').write_text(json.dumps({'original_length_height':5.19415/2,'fitted_length_height':float(np.ptp(c[:,1])/2),'tail_y_pivot_before':-.8,'tail_length_factor':.5,'origin_y_shift':1.45},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.studiolight_rotate_z=.3;sc.display.shading.show_shadows=True;sc.display.shading.show_cavity=True;sc.display.shading.cavity_type='BOTH';sc.display.shading.color_type='MATERIAL';sc.display.shading.background_type='WORLD';sc.world=bpy.data.worlds.new('World');sc.world.color=(.13,.13,.15)
sc.render.resolution_x=sc.render.resolution_y=800;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
for name,pos,target,scale in [('front',(0,-7,1),(0,0,1),2.3),('side',(7,0,1),(0,.55,1),3.6),('quarter',(5,-7,3),(0,.5,1),3.5),('back',(0,7,1),(0,0,1),2.3),('head',(2,-6,2.4),(0,-.8,1.7),.9),('feet',(0,-7,.25),(0,-.05,.25),1.4)]:
 cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;sc.render.filepath=str(P/'review'/f'fitted_{name}.png');bpy.ops.render.render(write_still=True)
