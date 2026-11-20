"""Correct the reported hand anatomy and belt intersection on a new authoring revision."""
import bpy,numpy as np,json,sys,math
from pathlib import Path
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v9.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;sc=bpy.context.scene
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
co=np.array([v.co[:] for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
ids=np.flatnonzero(pv==5);wr=np.array(r.data.bones['B_L_Hand'].head_local)
d=np.array([.54,0,-.841665]);d/=np.linalg.norm(d);u=np.array([-d[2],0,d[0]]);n=np.array([0,-1,0])
old=json.loads((p/'work/finger_joints.json').read_text())['L']
source=[];target=[];newj={}
def add(a,b):source.append(np.array(a));target.append(np.array(b))
# Preserve the cuff interface and proximal wrist volume.
for t in [-.018,0,.02]:
 for angle in np.linspace(0,2*np.pi,12,endpoint=False):
  v=wr+d*t+u*(.022*np.cos(angle))+n*(.014*np.sin(angle));add(v,v)
# Reposition each knuckle onto the normal shallow arc, lengthen the fingers, and reduce the fan.
for f in range(5):
 names=[f'B_L_Finger{f}',f'B_L_Finger{f}1',f'B_L_Finger{f}2']
 src=np.array([old[name] for name in names]+[old[names[-1]+'_tip']])
 if f==0:
  base=wr+d*.044+u*.028+n*.006;dire=d*.63+u*.77;dire/=np.linalg.norm(dire);length=.047
 else:
  along=[.083,.089,.086,.077][f-1];across=[.026,.008,-.011,-.028][f-1]
  base=wr+d*along+u*across
  angle=math.radians([5,1,-2,-8][f-1]);dire=d*math.cos(angle)+u*math.sin(angle)
  length=[.070,.078,.072,.054][f-1]
 dst=np.array([base+dire*length*t+n*(.006*t*t) for t in [0,.45,.75,1]])
 for a,b in zip(src,dst):
  add(a,b)
  # Surface anchors preserve cross sections while the finger is lengthened.
  for off in [u*.008,-u*.008,n*.006,-n*.006]:add(a+off,b+off)
 for name,a,b in zip(names,dst[:-1],dst[1:]):newj[name]=(a,b)
# Polyharmonic deformation moves the connected web/palm continuously between the anatomical landmarks.
S=np.array(source);T=np.array(target)
D=np.linalg.norm(S[:,None]-S[None,:],axis=2)
A=np.c_[np.ones(len(S)),S];K=np.block([[D+np.eye(len(S))*1e-6,A],[A.T,np.zeros((4,4))]])
coef=np.linalg.solve(K,np.r_[T-S,np.zeros((4,3))])
X=co[ids];R=np.linalg.norm(X[:,None]-S[None,:],axis=2);delta=np.c_[R,np.ones(len(X)),X]@coef
assert np.isfinite(delta).all() and np.linalg.norm(delta,axis=1).max()<.09
co[ids]+=delta
# Preserve the entire wrist/cuff boundary even outside the control ring.
t=(X-wr)@d;blend=np.clip((t-.008)/.022,0,1);co[ids]=X+delta*blend[:,None]
# Restore glove volume along the longer phalanges; the original short fingers were too thin after reshaping.
paths={}
for finger in range(5):
 names=[f'B_L_Finger{finger}',f'B_L_Finger{finger}1',f'B_L_Finger{finger}2']
 paths[finger]=np.array([newj[name][0] for name in names]+[newj[names[-1]][1]])
for i in ids:
 point=co[i];best=None
 for finger,line in paths.items():
  for segment,(a,b) in enumerate(zip(line[:-1],line[1:])):
   direction=b-a;t=float(np.clip((point-a)@direction/(direction@direction),0,1));center=a+direction*t
   dist=float(np.linalg.norm(point-center));entry=(dist,finger,segment,t,center,direction)
   if best is None or dist<best[0]:best=entry
 dist,finger,segment,t,center,direction=best
 if dist>.023:continue
 fraction=(segment+t)/3;fade=float(np.clip(fraction/.22,0,1))
 radial=point-center;radial-=direction*((radial@direction)/(direction@direction))
 co[i]+=radial*((.35 if finger==0 else .18)*fade)

# Shirt and trouser surfaces beneath the belt share its pelvis motion and sit inside its leather shell.
vg={g.index:g.name for g in o.vertex_groups}
for i in np.flatnonzero(np.isin(pv,[1,2])&(np.abs(co[:,0])<.22)&(co[:,2]>.965)&(co[:,2]<1.14)):
 z=co[i,2];w=float(np.clip((1.14-z)/.045,0,1)*np.clip((z-.965)/.035,0,1))
 co[i,0]*=1-.08*w;co[i,1]=-.05+(co[i,1]+.05)*(1-.12*w)
 oldw={e.group:e.weight for e in me.vertices[i].groups}
 for g,weight in oldw.items():o.vertex_groups[g].add([int(i)],weight*(1-w),'REPLACE')
 group=o.vertex_groups['B_Pelvis'];group.add([int(i)],oldw.get(group.index,0)*(1-w)+w,'REPLACE')
for i,v in enumerate(me.vertices):v.co=co[i]
# Fit the actual finger bones to the repaired geometry.
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for name,(a,b) in newj.items():
 bone=r.data.edit_bones[name];bone.head=a;bone.tail=b;bone.align_roll(Vector(n))
bpy.ops.object.mode_set(mode='OBJECT')
# The free hand rests with a gentle, progressively deeper curl toward the little finger.
# Its shape has been corrected in rest geometry; pose keys only articulate the new finger joints.
for act in bpy.data.actions:
 if act.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if 'B_L_Finger' in fc.data_path:bag.fcurves.remove(fc)
 for f in range(5):
  curls=[[4,8,4],[5,10,5],[7,13,6],[9,16,8],[12,19,9]][f]
  for name,angle in zip([f'B_L_Finger{f}',f'B_L_Finger{f}1',f'B_L_Finger{f}2'],curls):
   b=r.pose.bones[name];b.rotation_mode='QUATERNION';b.rotation_quaternion=Quaternion((1,0,0),math.radians(angle));b.location=(0,0,0);b.scale=(1,1,1)
   for frame in [0,int(act.frame_range[1])]:
    b.keyframe_insert('rotation_quaternion',frame=frame);b.keyframe_insert('location',frame=frame)
# Existing split normals no longer describe moved glove vertices.
if me.has_custom_normals:
 normals=[(0,0,0) if pv[loop.vertex_index]==5 else tuple(me.corner_normals[i].vector) for i,loop in enumerate(me.loops)]
 me.normals_split_custom_set(normals)
me.update()
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v10_geometry.blend'))
out=p/'review/feedback_20261011'
common.workbench_clay(sc,textured=False);sc.display.shading.show_cavity=False
def render(name,c,direction,scale):
 cam=common.ortho_camera(name,Vector(c)+Vector(direction),(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-Vector(direction)).to_track_quat('-Z','Y')
 sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=700;sc.render.filepath=str(out/(name+'.png'));bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
render('hand_corrected_rest',wr+d*.09,(0,-1,0),.26)
a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
c=(r.pose.bones['B_L_Hand'].head+r.pose.bones['B_L_Finger2'].tail)/2
render('hand_corrected_standing',c,(0,-1,.2),.25)
render('hand_corrected_back',c,(0,1,.2),.25)
(out/'hand_geometry_repair.json').write_text(json.dumps({'maximum_vertex_move_mm':float(np.linalg.norm(delta,axis=1).max()*1000),'new_joints':{k:[a.tolist(),b.tolist()] for k,(a,b) in newj.items()}},indent=1))
