"""Keep every rotation track in one quaternion hemisphere before glTF interpolation."""
import bpy,json,math
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
r=bpy.data.objects['Rig'];s=bpy.context.scene;report={}
for a in bpy.data.actions:
 r.animation_data.action=None
 for b in r.pose.bones:b.matrix_basis=Matrix.Identity(4)
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[];prev={};flips={};steps=[]
 step=2 if a.name=='Death' else 1
 for f in range(0,int(a.frame_range[1])+1,step):
  s.frame_set(f);row={}
  for b in r.pose.bones:
   q=b.rotation_quaternion.copy();q.normalize()
   if b.name in prev:
    dot=q.dot(prev[b.name])
    if dot<0:q.negate();flips[b.name]=flips.get(b.name,0)+1
    steps.append((2*math.acos(min(1,abs(dot)))*180/math.pi,b.name,f))
   prev[b.name]=q.copy();row[b.name]=q
  rows.append(row)
 if step==2:
  rows=[{n:rows[i//2][n].slerp(rows[min(i//2+1,len(rows)-1)][n],(i%2)/2) for n in rows[0]} for i in range(121)]
 for f,row in enumerate(rows):
  for n,q in row.items():r.pose.bones[n].rotation_quaternion=q;r.pose.bones[n].keyframe_insert('rotation_quaternion',frame=f)
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[a.name]={'flips':flips,'largest_steps_degrees':sorted(steps,reverse=True)[:12]}
(P/'work/quaternion_continuity.json').write_text(json.dumps(report,indent=2));print(report)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
