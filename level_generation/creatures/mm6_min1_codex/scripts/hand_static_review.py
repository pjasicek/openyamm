import bpy,sys,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/st_v1_parts.blend'));scene=bpy.context.scene;common.workbench_clay(scene)
for side in [-1,1]:
 c=Vector((.54*side,.005,.83))
 for view,off in [('front',(0,-1,0)),('back',(0,1,0)),('outer',(side,0,0))]:
  cam=common.ortho_camera('Camera',c+Vector(off),(0,0,0),.32);cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.resolution_x=scene.render.resolution_y=650;scene.render.filepath=str(P/f'review/hand_static_{side}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam)
