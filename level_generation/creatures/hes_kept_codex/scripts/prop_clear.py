"""Smallest wrist turn that clears the real pick/club from open clothing; smoothed over the whole clip."""
import bpy,sys,os,json,math
from pathlib import Path
import numpy as np
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import armik
src,out=sys.argv[sys.argv.index('--')+1:];bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
G=json.loads((P/'work/male/handle_R.json').read_text());C=Vector(G['handle_centre_hand_local']);A=Vector(G['handle_axis_hand_local'])
S=json.loads((P/'work/male/source_rest.json').read_text());X=Matrix(S['B_R_Hand']['rot']).inverted()@(Vector(S['B_R_Finger2']['head'])-Vector(S['B_R_Hand']['head']));X=(X-A*X.dot(A)).normalized();R=Matrix((X,A.cross(X),A)).transposed().to_4x4();R.translation=C
with bpy.data.libraries.load(str(P/'work/props/props.blend'),link=False) as (data,to):to.objects=[n for n in data.objects if n in ('hes_kept_pick','hes_kept_club')]
pts=[]
for o in to.objects:
 pts += [R@v.co for v in o.data.vertices]
 pts += [R@((o.data.vertices[e.vertices[0]].co+o.data.vertices[e.vertices[1]].co)*.5) for e in o.data.edges]
 pts += [R@(sum((o.data.vertices[i].co for i in p.vertices),Vector())/len(p.vertices)) for p in o.data.polygons]
pc=[v.value for v in body.data.attributes['piece'].data];faces=[tuple(p.vertices) for p in body.data.polygons if pc[p.vertices[0]] not in (3,4)]
def activate(a):
 rig.animation_data.action=a
 if a and a.slots:rig.animation_data.action_slot=a.slots[0]
def cost(tree,H):
 d=0.
 for p in pts:
  q=H@p;loc,n,i,dist=tree.find_nearest(q,.018)
  if loc is not None:d=max(d,.018-dist)
 return d

for name in ('Kept_MaceAttack','Kept_ArmedDeath'):
 a=bpy.data.actions[name];times=np.arange(0,a.frame_range[1]+.01,.5);frames=[];base=[]
 for f in times:
  activate(a);sc.frame_set(int(f),subframe=float(f%1));ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
  tree=BVHTree.FromPolygons([body.matrix_world@v.co for v in me.vertices],faces);ev.to_mesh_clear();H=armik.W(rig,'B_R_Hand')
  frames.append((tree,H.copy(),{p.name:p.matrix_basis.copy() for p in rig.pose.bones}));base.append(cost(tree,H))
 activate(None);u=A.orthogonal().normalized();v=A.cross(u);options=[]
 for k in range(12):
  axis=u*math.cos(k*math.tau/12)+v*math.sin(k*math.tau/12);angles=[];valid=True
  for (tree,H,snap),err in zip(frames,base):
   if err<=1e-7:angles.append(0.);continue
   for p in rig.pose.bones:p.matrix_basis=snap[p.name]
   bpy.context.view_layer.update();found=None
   for angle in range(4,49,4):
    H2=armik.rot_world(H,H.to_3x3()@Quaternion(axis,math.radians(angle)).to_matrix());sw,tw=armik.wrist_cost(rig,'R',H2.to_3x3())
    if sw<=59 and abs(tw)<=90 and cost(tree,H2)<1e-7:found=angle;break
   if found is None:valid=False;break
   angles.append(found)
  if valid:options.append((max(angles),sum(angles),k,axis,angles))
 assert options,('No continuous clearance direction',name)
 _,_,k,axis,angles=min(options,key=lambda x:x[:2]);angles=np.array(angles);expanded=np.array([max(angles[max(i-3,0):i+4]) for i in range(len(angles))])
 g=np.exp(-.5*(np.arange(-3,4)/1.2)**2);g/=g.sum();smoothed=np.convolve(np.pad(expanded,3,mode='edge'),g,'valid');smoothed=np.maximum(smoothed,angles)
 keys=[]
 for f,angle,(_,H,snap) in zip(times,smoothed,frames):
  for p in rig.pose.bones:p.matrix_basis=snap[p.name]
  bpy.context.view_layer.update();H2=armik.rot_world(H,H.to_3x3()@Quaternion(axis,math.radians(float(angle))).to_matrix());armik.set_world(rig,'B_R_Hand',H2)
  keys.append(rig.pose.bones['B_R_Hand'].rotation_quaternion.copy())
 activate(a)
 for i,(f,q) in enumerate(zip(times,keys)):
  if i and q.dot(keys[i-1])<0:q.negate()
  pb=rig.pose.bones['B_R_Hand'];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
 print('PROP_CLEAR',name,'axis',k,'max turn',max(smoothed),'half frames corrected',sum(angles>0),flush=True)
 activate(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
