import bpy,numpy as np,json
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/"work/rig_uv.blend"))
co=np.array([v.co[:] for o in bpy.data.objects if o.type=="MESH" for v in o.data.vertices]);info={}
sc=bpy.context.scene;sc.render.engine='BLENDER_WORKBENCH'
sc.display.shading.light='STUDIO';sc.display.shading.color_type='SINGLE';sc.display.shading.single_color=(0.64,0.55,0.6)
sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(0.12,0.12,0.12)
sc.render.resolution_x=1000;sc.render.resolution_y=1000;sc.render.resolution_percentage=100
c=Vector((co.min(0)+co.max(0))/2);ext=float((co.max(0)-co.min(0)).max())
cam=bpy.data.objects.new('ReviewCamera',bpy.data.cameras.new('ReviewCamera'));sc.collection.objects.link(cam);sc.camera=cam
cam.data.type='ORTHO';cam.data.ortho_scale=ext*1.15
for name,d in [('front',(0,-1,.02)),('side',(1,0,.02)),('back',(0,1,.02)),('quarter',(1,-1,.3))]:
    cam.location=c+Vector(d).normalized()*4*ext;cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler()
    sc.render.filepath=str(P/'review/rig'/f'{name}.png');bpy.ops.render.render(write_still=True)
print('GEOMETRY',json.dumps(info),flush=True)
