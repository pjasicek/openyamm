"""Ground the exposed shoes during the prone fall, retaining the solved cloth and torso."""
import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];s=bpy.context.scene
piece=np.array([x.value for x in o.data.attributes['piece'].data])
def coords():
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();co=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();return co
def action(name):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];return a
act=action('Death');rows=[]
for f in range(121):
 s.frame_set(f);r.animation_data.action=None
 t=np.clip((f-20)/15,0,1);fade=t*t*(3-2*t)
 for part,side in [(5,'L'),(6,'R')]:
  floor=float(coords()[piece==part,2].min());b=r.pose.bones[f'B_{side}_Calf'];M=b.matrix.copy();M.translation.z+=(.006-floor)*fade;b.matrix=M;bpy.context.view_layer.update()
 rows.append({n:r.pose.bones[n].location.copy() for n in ['B_L_Calf','B_R_Calf']});action('Death')
for f,row in enumerate(rows):
 for n,loc in row.items():r.pose.bones[n].location=loc;r.pose.bones[n].keyframe_insert('location',frame=f)
s.frame_set(120);held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in r.pose.bones};r.animation_data.action=None;bpy.data.actions.remove(bpy.data.actions['Dead']);a=bpy.data.actions.new('Dead');a.use_fake_user=True;r.animation_data.action=a
for f in (0,60):
 for n,(q,loc) in held.items():
  b=r.pose.bones[n];b.rotation_quaternion=q;b.location=loc;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
a.use_frame_range=True;a.frame_start=0;a.frame_end=60
for a in bpy.data.actions:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
report={}
for name in ('Standing','Walking','Run','Hit','Fidget','Death','Dead'):
 a=action(name);minimum=1e6;shoes=[]
 for f in np.arange(0,float(a.frame_range[1])+.01,.5):
  s.frame_set(int(f),subframe=f%1);co=coords();minimum=min(minimum,float(co[:,2].min()));shoes.append([float(co[piece==k,1].mean()) for k in [5,6]])
 report[name]={'floor_m':minimum,'samples':len(shoes)}
 assert minimum>-.005,(name,minimum)
 if name=='Walking':
  stride=float(2*np.mean(np.ptp(np.array(shoes),axis=0)));s['walk_stride_m']=stride;report[name]['stride_m']=stride
action('Standing');s.frame_set(0)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
(P/'work/final_motion_contacts.json').write_text(json.dumps(report,indent=2));print(report)
