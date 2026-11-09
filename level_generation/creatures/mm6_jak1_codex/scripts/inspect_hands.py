import bpy,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
for side in ['R','L']:
 c=rig.data.bones[f'B_{side}_Hand'].head_local.copy();c+=(c-rig.data.bones[f'B_{side}_Forearm'].head_local).normalized()*.075
 for view,d in [('front',Vector((0,-1,.2))),('back',Vector((0,1,.2))),('side',Vector((-1 if side=='R' else 1,0,0)))]:
  cam=common.ortho_camera('cam',c+d,(0,0,0),.3);cam.rotation_euler=(c-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam;scene.render.resolution_x=scene.render.resolution_y=650;scene.render.filepath=str(P/f'review/rest_hand_{side}_{view}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
