"""Ground the new drape and let the boots emerge through its open hem during the fall."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];R=P/'review/feedback_v3'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/feedback_drape.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];s=bpy.context.scene;m=o.data
piece=np.array([x.value for x in m.attributes['piece'].data]);cloth=np.where(np.isin(piece,[1,7]))[0];bones=[b.name for b in r.data.bones if b.name.startswith('Skirt_')];col={n:j for j,n in enumerate(bones)};A=np.zeros((len(cloth),len(bones)));gn={g.index:g.name for g in o.vertex_groups}
for i,vi in enumerate(cloth):
 for g in m.vertices[int(vi)].groups:
  n=gn[g.group]
  while n in col:A[i,col[n]]+=g.weight;n=r.data.bones[n].parent.name
norm=(A*A).sum(1);cf=[list(f.vertices) for f in m.polygons if piece[f.vertices[0]] in (1,7)]
sf={k:[list(f.vertices) for f in m.polygons if piece[f.vertices[0]]==k] for k in (5,6)}
def coords():
 e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();co=np.array([v.co[:] for v in me.vertices]);e.to_mesh_clear();return co
def action(name):
 a=bpy.data.actions[name];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];return a
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
action('Death');rows=[];report=[];calf_axes=[]
for f in range(121):
 s.frame_set(f);r.animation_data.action=None;co=coords();delta=np.zeros(len(bones));z=co[cloth,2]
 for _ in range(40):
  gaps=.003-z-A@delta;bad=np.where((gaps>.00005)&(norm>.001))[0]
  if not len(bad):break
  for i in bad:
   gap=.003-z[i]-A[i]@delta
   if gap>0:delta+=A[i]*gap/norm[i]
 basis={n:(r.pose.bones[n].matrix.to_3x3()@r.pose.bones[n].rotation_quaternion.to_matrix().inverted()).inverted() for n in bones}
 for n,j in col.items():r.pose.bones[n].location+=basis[n]@Vector((0,0,float(delta[j])))
 bpy.context.view_layer.update();co=coords();cb=BVHTree.FromPolygons(co,cf)
 pelvis=r.pose.bones['B_Pelvis'].head;foot=(r.pose.bones['B_L_Foot'].head+r.pose.bones['B_R_Foot'].head)/2;h=foot-pelvis;h.z=0;h.normalize();w=h.cross(Vector((0,0,1)));H=np.array(h);W=np.array(w)
 rest=np.array([v.co[:] for v in m.vertices]);hem=co[(piece==1)&(rest[:,2]<.108)];plane=float(np.median(hem@H));center=float(np.median(hem@W));blend=smooth((f-22)/28)
 for part,side,sign,pitch in [(5,'L',1,-3),(6,'R',-1,-12)]:
  ids=np.where(piece==part)[0];verts=co[ids];cuff=rest[ids,2]>.181;foot=r.pose.bones[f'B_{side}_Foot'].head;toe=r.pose.bones[f'B_{side}_Toe0'].head;direction=toe-foot;direction.z=0;direction.normalize()
  yaw=direction.rotation_difference(h);anchor=np.array(foot);index={int(v):i for i,v in enumerate(ids)};localfaces=[[index[v] for v in face] for face in sf[part]]
  candidates=[(pitch,.018,.08)] if f<50 else sorted([(p,d,span) for p in range(-60,61,3) for d in [.018,.006,.03,.05] for span in [.08,.065,.095,.11]],key=lambda x:abs(x[0]-pitch)+abs(x[1]-.018)*100+abs(x[2]-.08)*100)
  for angle,depth,span in candidates:
   Q=Quaternion(w,math.radians(angle))@yaw;v=(verts-anchor)@np.array(Q.to_matrix()).T+anchor
   shift=H*(plane-depth-np.max(v[cuff]@H))+W*(center+sign*span-np.mean(v[cuff]@W));shift[2]=.006-v[:,2].min()
   if f<50 or not cb.overlap(BVHTree.FromPolygons(v+shift,localfaces,epsilon=.003)):break
  else:raise AssertionError(('No boot fit',f,side))
  Q=Quaternion().slerp(Q,blend);b=r.pose.bones[f'B_{side}_Calf'];M=Q.to_matrix().to_4x4()@b.matrix;M.translation=Vector(anchor)+Q@(b.matrix.translation-Vector(anchor))+Vector(shift)*blend;b.matrix=M;bpy.context.view_layer.update()
  actual=coords();M=b.matrix.copy();M.translation.z+=.006-float(actual[piece==part,2].min());b.matrix=M;bpy.context.view_layer.update()
 rows.append({n:(r.pose.bones[n].rotation_quaternion.copy(),r.pose.bones[n].location.copy()) for n in bones+['B_L_Calf','B_R_Calf']});report.append({'frame':f,'max_floor_lift':float(delta.max())});action('Death')
for f in range(1,len(rows)):
 for n,(q,loc) in rows[f].items():
  if q.dot(rows[f-1][n][0])<0:q.negate()
for f,row in enumerate(rows):
 for n,(q,loc) in row.items():
  b=r.pose.bones[n];b.rotation_quaternion=q;b.location=loc;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
# Resolve only tiny between-key cuff grazes; keep the cuff inside its hem margin.
for iteration in range(3):
 corrections=0
 for f in np.arange(50.5,120,.5):
  s.frame_set(int(f),subframe=f%1);co=coords();cb=BVHTree.FromPolygons(co,cf)
  for part,side in [(5,'L'),(6,'R')]:
   if not cb.overlap(BVHTree.FromPolygons(co,sf[part])):continue
   h=r.pose.bones[f'B_{side}_Foot'].head-r.pose.bones['B_Pelvis'].head;h.z=0;h.normalize()
   for distance in [.0005,.001,.002,.003,.004]:
    candidate=co.copy();candidate[piece==part]+=np.array(h)*distance
    if not cb.overlap(BVHTree.FromPolygons(candidate,sf[part])):break
   else:raise AssertionError(('Subframe cuff fit',f,side))
   for frame in {math.floor(f),math.ceil(f)}:
    s.frame_set(frame);b=r.pose.bones[f'B_{side}_Calf'];M=b.matrix.copy();M.translation+=h*distance;b.matrix=M;bpy.context.view_layer.update();b.keyframe_insert('location',frame=frame)
   corrections+=1
 if not corrections:break
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
action('Death');collision=[]
for f in np.arange(0,120.001,.5):
 s.frame_set(int(f),subframe=f%1);co=coords();cb=BVHTree.FromPolygons(co,cf);sb=BVHTree.FromPolygons(co,sf[5]+sf[6]);overlap=cb.overlap(sb)
 collision.append({'frame':float(f),'pairs':len(overlap),'floor':float(co[:,2].min())})
assert not any(row['pairs'] for row in collision if row['frame']>=50),[row for row in collision if row['frame']>=50 and row['pairs']]
(R/'contacts_fit.json').write_text(json.dumps({'fit':report,'collision':collision},indent=2));print('CONTACTS',collision[::24],flush=True)
action('Standing');s.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/feedback_contacts.blend'))
sys.path.insert(0,str(P/'scripts'));import common
common.workbench_clay(s);s.display.shading.color_type='SINGLE';s.display.shading.single_color=(.6,.6,.6);s.render.resolution_x=900;s.render.resolution_y=900
action('Dead');s.frame_set(0)
for n,eye,target,scale in [('dead_top',(0,.50,4),(0,.50,.1),1.8),('dead_side',(3,.4,.8),(0,.4,.2),1.8),('dead_feet',(0,1.08,4),(0,1.08,.1),.85)]:
 cam=common.ortho_camera('probe',eye,(0,0,0),scale);cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam;s.render.filepath=str(R/f'contacts_{n}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
