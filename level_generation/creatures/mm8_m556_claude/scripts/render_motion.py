"""Fixed-camera pose sheets and portable animated preview."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
rig=bpy.data.objects['Wasp_Rig'];body=bpy.data.objects['Wasp'];sc=bpy.context.scene
sc.render.engine='BLENDER_WORKBENCH';sc.display.shading.light='STUDIO';sc.display.shading.color_type='MATERIAL';sc.display.shading.show_cavity=True;sc.display.shading.show_shadows=False
sc.world=bpy.data.worlds.new('ReviewWorld');sc.world.color=(.15,.15,.15)
sc.render.resolution_x=400;sc.render.resolution_y=400;sc.render.resolution_percentage=100
cam=bpy.data.objects.new('MotionCamera',bpy.data.cameras.new('MotionCamera'));sc.collection.objects.link(cam);sc.camera=cam;cam.data.type='ORTHO'
rows=[]
roles=sys.argv[sys.argv.index('--roles')+1].split(',') if '--roles' in sys.argv else ['Fly','FlyFast','Attack','Hit','Fidget','Death','Dead']
for role in roles:
 if role not in bpy.data.actions:continue
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for view,pos,target,scale in [('front',(0,-4,.5),(0,.03,.47),1.4),('side',(4,0,.5),(0,.03,.47),1.4),('quarter',(2,-3,1.3),(0,.03,.47),1.4)]:
  cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
  row=[]
  for i in range(5):
   t=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*i/4;sc.frame_set(int(t),subframe=t-int(t))
   path=P/'review'/f'{role}_{view}_{i}.png';sc.render.filepath=str(path);bpy.ops.render.render(write_still=True);row.append([str(path),f'{role} {view} {t/48:.3f}s'])
  rows.append(row)
(P/'review/motion_frames.json').write_text(json.dumps(rows))
rig.animation_data.action=bpy.data.actions['Fly'];sc.frame_set(0)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);body.select_set(True);bpy.context.view_layer.objects.active=rig
for mat in body.data.materials:mat.use_backface_culling=True
bpy.ops.export_scene.gltf(filepath=str(P/'export/m556_pilot.glb'),use_selection=True,export_format='GLB',export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_skins=True,export_all_influences=False,export_attributes=False,export_morph=False,export_reset_pose_bones=True,export_anim_slide_to_zero=True)
