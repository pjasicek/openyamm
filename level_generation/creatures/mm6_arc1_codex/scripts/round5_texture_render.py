"""Eight-view 700-pixel render comparison of compact atlas versus original-density maps."""
import bpy,sys,math,json,subprocess
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];D=P/'review/round5/texture_comparison';D.mkdir(exist_ok=True)
import common
for label,path in [('original',P/'work/round5/texture_reference/mm6_arc1_a.glb'),('compact',P/'review/viewer/mm6_arc1_a.glb')]:
 bpy.ops.wm.read_factory_settings(use_empty=True);sc=bpy.context.scene;sc.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(path));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
 common.workbench_clay(sc,True);sc.render.film_transparent=True;sc.render.image_settings.color_mode='RGBA';sc.render.resolution_x=800;sc.render.resolution_y=824;sc.render.resolution_percentage=100
 for i in range(8):
  angle=i*math.pi/4;direction=Vector((math.sin(angle),-math.cos(angle),0));center=Vector((0,0,.85));cam=common.ortho_camera('TextureReview',center+direction*6,(0,0,0),2.0);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-direction).to_track_quat('-Z','Y');sc.camera=cam;sc.render.filepath=str(D/f'{label}_{i}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
r=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),'original','compact'],text=True));r['purpose']='Same R5 pose and geometry, original-density textures versus final compact atlas at 700 actor pixels';(D/'metrics.json').write_text(json.dumps(r,indent=2));print('TEXTURE_COMPARISON',r,flush=True)
