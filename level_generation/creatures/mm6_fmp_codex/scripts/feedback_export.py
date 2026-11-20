import bpy,json,runpy
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/feedback_face_fixed.blend'))
r=bpy.data.objects['Rig'];s=bpy.context.scene;flips={}
for a in bpy.data.actions:
 r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis=Matrix()
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[];prev={};count=0
 for f in range(int(a.frame_range[1])+1):
  s.frame_set(f);row={}
  for b in r.pose.bones:
   q=b.rotation_quaternion.copy().normalized()
   if b.name in prev and q.dot(prev[b.name])<0:q.negate();count+=1
   prev[b.name]=q.copy();row[b.name]=q
  rows.append(row)
 for f,row in enumerate(rows):
  for n,q in row.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
 flips[a.name]=count
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/'review/feedback_v3/quaternion_flips.json').write_text(json.dumps(flips,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
for name in ['export_model.py','verify_export.py','audit_final_deformation.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
