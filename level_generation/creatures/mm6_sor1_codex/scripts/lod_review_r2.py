"""Render actual packaged colour LODs at the engine's upper hysteresis switch sizes."""
import bpy,sys,math,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
out=p/'review/round2/reduction';out.mkdir(exist_ok=True,parents=True)
for level in range(4):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/f'work/lod_review_{level}.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
 rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
 common.workbench_clay(scene,textured=True);scene.render.film_transparent=True;scene.render.resolution_percentage=100
 for switch,size in [(1,550),(2,220),(3,88)]:
  if level not in [0,switch]:continue
  scene.render.resolution_x=scene.render.resolution_y=size+32
  cam=common.ortho_camera('LodCamera',(0,-6,.85),(math.pi/2,0,0),1.95*(size+32)/size);scene.camera=cam
  for i in range(8):
   a=i*math.pi/4;cam.location=(6*math.sin(a),-6*math.cos(a),.85);cam.rotation_euler=(math.pi/2,0,a);scene.render.filepath=str(out/f'lod{level}_at{switch}_{i}.png');bpy.ops.render.render(write_still=True)
  bpy.data.objects.remove(cam,do_unlink=True)
print('LOD_SWITCH_RENDERS_DONE',flush=True)
