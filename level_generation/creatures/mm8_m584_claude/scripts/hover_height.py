"""Match the native 42-unit transparent hover margin, easing it out into the grounded corpse."""
from pathlib import Path
import bpy,math,json
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];HEIGHT=42/75
def apply(path):
 if not path.exists():return
 bpy.ops.wm.open_mainfile(filepath=str(path))
 rig=bpy.data.objects['Rig'];sc=bpy.context.scene
 if rig.get('native_hover_m')==HEIGHT:return
 assert not rig.get('native_hover_m'), 'Explicitly migrate a previous hover revision'
 for a in list(bpy.data.actions):
  if not a.use_fake_user:continue
  rig.animation_data.action=a
  if a.slots:rig.animation_data.action_slot=a.slots[0]
  end=float(a.frame_range[1]);samples=[]
  for i in range(round(end*2)+1):
   f=i/2;sc.frame_set(int(f),subframe=f-int(f));t=f/30
   amount=0 if a.name=='Dead' else HEIGHT
   if a.name=='Death':
    u=min(1,max(0,t/.9));amount*=1-u*u*(3-2*u)
   pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z+=amount;pb.matrix=m
   samples.append((f,pb.location.copy()))
  for f,value in samples:
   pb=rig.pose.bones['B_Pelvis'];pb.location=value;pb.keyframe_insert(data_path='location',frame=f,group=pb.name)
  for layer in a.layers:
   for strip in layer.strips:
    for bag in strip.channelbags:
     for curve in bag.fcurves:
      for key in curve.keyframe_points:key.interpolation='LINEAR'
 rig['native_hover_m']=HEIGHT;rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis=Matrix()
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
for name in ['rig_final.blend','rig_uv_head.blend','rig_uv_body.blend','textured_uv.blend']:apply(P/'work'/name)
(P/'work/native_placement.json').write_text(json.dumps({'scale':75,'live_hover_game_units':42,'live_hover_model_m':HEIGHT,'death_hover_fade_seconds':.9,'native_body_height_pixels_approx':134,'native_feet_bottom_margin_pixels':42,'native_source':'M584Wa0.bmp'},indent=2)+'\n')
