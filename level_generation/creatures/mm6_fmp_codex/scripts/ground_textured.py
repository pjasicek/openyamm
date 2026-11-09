"""Fit the visible shoes and cloth to the ground without lifting the torso off its contacts."""
import bpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];s=bpy.context.scene;me=o.data
piece=np.array([x.value for x in me.attributes['piece'].data]);cloth=np.where(np.isin(piece,[1,7]))[0];bones=[b.name for b in r.data.bones if b.name.startswith('Skirt_')];col={n:j for j,n in enumerate(bones)};A=np.zeros((len(cloth),len(bones)));gn={g.index:g.name for g in o.vertex_groups}
for row,vi in enumerate(cloth):
 for g in me.vertices[int(vi)].groups:
  n=gn[g.group]
  while n in col:
   A[row,col[n]]+=g.weight;n=r.data.bones[n].parent.name
# Connected edit bones ignore pose translations; release only that constraint for the cloth correction.
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for n in bones:r.data.edit_bones[n].use_connect=False
bpy.ops.object.mode_set(mode='OBJECT')
norm=(A*A).sum(1)
def coeval():
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();co=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();return co
act=bpy.data.actions['Death'];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];rows=[];report=[];previous=np.zeros(len(bones))
for f in range(121):
 s.frame_set(f);r.animation_data.action=None
 for n in bones:r.pose.bones[n].location=Vector()
 bpy.context.view_layer.update()
 for part,side in [(5,'L'),(6,'R')]:
  floor=float(coeval()[piece==part,2].min());delta=max(0,.006-floor)
  b=r.pose.bones[f'B_{side}_Calf'];M=b.matrix.copy();M.translation.z+=delta;b.matrix=M;bpy.context.view_layer.update()
 co=coeval();z=co[cloth,2];delta=previous*.8
 for _ in range(50):
  gaps=.026-z-A@delta;bad=np.where((gaps>.0001)&(norm>.001))[0]
  if not len(bad):break
  for i in bad:
   gap=.026-z[i]-A[i]@delta
   if gap>0:delta+=A[i]*(gap/norm[i])*.85
 previous=delta.copy()
 for n,j in col.items():
  b=r.pose.bones[n];basis=b.matrix.to_3x3()@b.rotation_quaternion.to_matrix().inverted();b.location=basis.inverted()@Vector((0,0,float(delta[j])))
 bpy.context.view_layer.update();co=coeval();report.append({'frame':f,'floor':float(co[:,2].min()),'max_cloth_offset':float(delta.max())})
 rows.append({n:r.pose.bones[n].location.copy() for n in bones+['B_L_Calf','B_R_Calf']});r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
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
# Zero location tracks prevent a prior Death pose leaking secondary translations into the other clips.
for name in ('Standing','Walking','Run','Hit','Fidget'):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in (0,a.frame_range[1]):
  for n in bones+['B_L_Calf','B_R_Calf']:
   r.pose.bones[n].location=Vector();r.pose.bones[n].keyframe_insert('location',frame=f)
r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];dense=1e6
for f in np.arange(0,120.001,.5):s.frame_set(int(f),subframe=f%1);dense=min(dense,float(coeval()[:,2].min()))
print('DIAGNOSTIC floor after solving', min(x['floor'] for x in report), 'after keying', dense, flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_contact_candidate.blend'))
(p/'work/floor_candidate.json').write_text(json.dumps(report,indent=2))
assert dense>-.004,dense
(p/'work/floor_contacts.json').write_text(json.dumps({'dense_floor_m':dense,'frames':report},indent=2));print('FLOOR CONTACTS',dense,'max cloth local',max(x['max_cloth_offset'] for x in report),flush=True)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured_uv.blend'))
