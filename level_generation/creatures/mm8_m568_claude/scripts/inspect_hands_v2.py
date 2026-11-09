import bpy, json
from pathlib import Path
from mathutils import Vector
import numpy as np
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/fitted_body.blend'))
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.show_cavity=True;sc.display.shading.color_type='MATERIAL';sc.render.resolution_x=sc.render.resolution_y=900;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('Camera',bpy.data.cameras.new('Camera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
co=np.array([v.co[:] for v in bpy.data.objects['Body'].data.vertices])
for side,sign in [('left',1),('right',-1)]:
 c=co[co[:,0]*sign>.70];print(side,c.min(0).tolist(),c.max(0).tolist())
 target=Vector((sign*.74,-.22,1.15));cam.data.ortho_scale=.50
 for label,delta in [('front',(0,-3,.2)),('palm',(0,3,.1)),('outer',(sign*3,0,.2))]:
  cam.location=target+Vector(delta);cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();sc.render.filepath=str(P/'review'/f'v2_hand_{side}_{label}.png');bpy.ops.render.render(write_still=True)
