"""Resolve measured hull contacts with small hinge rotations and translations."""
import bpy,sys,os,runpy,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];S=P/'scripts';sys.path.insert(0,str(S));import armik
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];smooth='--smooth' in args;result_name='forge_motion_fit' if smooth else 'forge_contact_fit';roles=[x for x in args if not x.startswith('--')] or ['Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead']
src=P/('work/'+result_name+'.blend') if '--resume' in args else P/('work/forge_contact_fit.blend' if smooth else 'work/forge_carry_fit.blend')
if '--resume' not in args and not smooth:
 bpy.ops.wm.open_mainfile(filepath=str(src))
 for v in bpy.data.objects['Apron_Back2'].data.vertices:v.co.x+=math.copysign(.04,v.co.x)
 src=P/'work/forge_contact_base.blend';bpy.ops.wm.save_as_mainfile(filepath=str(src))
sys.argv=['armour_gate.py','--',str(src),'forge_contact_masks',str(S/'armour_forge_concept.json')];g=runpy.run_path(str(S/'armour_gate.py'),run_name='__main__');r=g['rig'];body=g['body'];sc=bpy.context.scene;plates=g['plates'];F=g['pfaces'];PV=g['PV'];inside=g['inside_closed'];names=[o.name for o in plates]
groups=[]
for side in 'LR':
 groups.extend([(f'B_ForgeShoulder_{side}',[f'Arm_pauldron_{side}',f'Arm_pauldron_lower_{side}',f'Apron_Shoulder_{side}']),(f'B_ForgeGauntlet_{side}',[f'Arm_forearm_{side}'])])
for side in ('Front','Back'):
 for k in range(3):
  name=f'Apron_{side}{k}'
  if name in bpy.data.objects:groups.append((bpy.data.objects[name].vertex_groups[0].name,[name]))
def tree(V,F):return BVHTree.FromPolygons(V.tolist(),F)
def nearby(V,W,pad=.006):return np.flatnonzero(np.all((V>W.min(0)-pad)&(V<W.max(0)+pad),axis=1))
def hit(t,points,limit=.5,skip=()):
 d,k=inside(t,points,limit,skip)
 if k<0:return None
 return d,np.array(t.find_nearest(Vector(points[k]))[1])
HF=[tuple(f.vertices) for f in body.data.polygons if all(sum(e.weight for e in body.data.vertices[i].groups if body.vertex_groups[e.group].name in {'B_Head','Bone_025','headfront','Bone_041','Bone_036'})>.5 for i in f.vertices)]
report=json.loads((P/('review/'+result_name+'.json')).read_text()) if '--resume' in args else {}
for role in roles:
 if role in report:continue
 a=bpy.data.actions['Forge_'+role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];keys=[];counts=0;worst=0
 frames=list(np.arange(a.frame_range[0],a.frame_range[1]+.001,.5));sample_count=len(frames);prev_world={};prev_parents={}
 if smooth and role in ('Standing','Walking','Running'):frames=frames*2
 for f in frames:
  sc.frame_set(int(f),subframe=float(f%1));B,_=g['ev'](body);BT=tree(B,g['BFK']);HT=tree(B,HF);HC=B[np.array(sorted({i for f in HF for i in f}))].mean(0);G,_=g['ev'](g['gun']);V={o.name:g['ev'](o)[0] for o in plates};T={n:tree(v,F[n]) for n,v in V.items()};M={bn:armik.W(r,bn).copy() for bn,_ in groups};original={bn:m.copy() for bn,m in M.items()}
  if smooth and prev_world:
   for bn,ns in groups:
    parent=r.data.bones[bn].parent.name;parent_now=M[parent] if parent in M else armik.W(r,parent);parent_before=prev_world[parent] if parent in prev_world else prev_parents[bn];seed=parent_now@parent_before.inverted()@prev_world[bn];target=M[bn];q=seed.to_quaternion().slerp(target.to_quaternion(),.06);candidate=q.to_matrix().to_4x4();candidate.translation=seed.translation.lerp(target.translation,.06);transform=candidate@target.inverted()
    for n in ns:V[n]=V[n]@np.array(transform.to_3x3()).T+np.array(transform.translation);T[n]=tree(V[n],F[n])
    M[bn]=candidate
  motion_start={bn:m.copy() for bn,m in M.items()}

  def constraints(ns,verts):
   ts={n:tree(verts[n],F[n]) for n in ns};out=[]
   for n in ns:
    v=verts[n];c=hit(BT,v[g['BASE_PLATE'][n]],1.2,g['HIDFK'])
    if c:out.append((c[0],c[1]))
    ids=g['cand'][n]
    if n.startswith(('Apron_Front','Apron_Back')):ids=np.flatnonzero(g['HID']==0)
    elif n.startswith('Apron_'):ids=np.union1d(ids,g['ARMV'])
    ids=ids[nearby(B[ids],v)] if len(ids) else ids;c=hit(ts[n],B[ids]) if len(ids) else None
    if c:out.append((c[0],-c[1]))
    for other in names:
     if other in ns:continue
     w=V[other]
     if np.any(v.min(0)>w.max(0)+.006) or np.any(w.min(0)>v.max(0)+.006):continue
     c=hit(T[other],v[PV[n]]);cc=hit(ts[n],w[PV[other]])
     if c:out.append((c[0],c[1]))
     if cc:out.append((cc[0],-cc[1]))
    if n.startswith('Apron_') and HT.overlap(tree(v,[tuple(f.vertices) for f in bpy.data.objects[n].data.polygons])):
     direction=v.mean(0)-HC;direction/=np.linalg.norm(direction);out.append((.005,direction))
    if smooth and v[:,2].min()<.006:out.append((.006-float(v[:,2].min()),np.array([0.,0.,1.])))
    ix=nearby(G,v);c=hit(ts[n],G[ix]) if len(ix) else None
    if c:out.append((c[0],-c[1]))
   return [x for x in out if x[0]>.0029]
  def project(ns,base):
   vs={n:v.copy() for n,v in base.items()};delta=np.zeros(3);best=None
   for _ in range(16):
    cs=constraints(ns,vs);depth=max((c[0] for c in cs),default=0.);score=sum(c[0]**2 for c in cs)
    if best is None or score<best[0]:best=(score,depth,delta.copy(),{n:v.copy() for n,v in vs.items()})
    if not cs:break
    d,normal=max(cs,key=lambda c:c[0]);move=normal*min(.02,d+.003);delta+=move
    if np.linalg.norm(delta)>.05:break
    for n in vs:vs[n]+=move
   return best
  for sweep in range(8 if smooth else 5):
   changed=False
   for bn,ns in groups:
    cs=constraints(ns,{n:V[n] for n in ns})
    if not cs:continue
    candidates=[];base={n:V[n].copy() for n in ns};anchor=np.array(M[bn].translation)
    turn=armik.W(r,'B_Spine2')@r.data.bones['B_Spine2'].matrix_local.inverted();outward=np.array(turn.to_3x3()@Vector((0,1 if 'Back' in bn else -1,0)))
    for deg in ((0,.5,-.5,1,-1,2,-2,4,-4,8,-8,12,-12) if smooth else (0,5,-5,15,-15,30,-30,45,-45,60,-60,80,-80)):
     for axis in ('X','Z','Y') if deg else ('X',):
      if abs(deg)>30 and axis!='X':continue
      Q=M[bn].to_3x3()@Matrix.Rotation(math.radians(deg),3,axis)@M[bn].to_3x3().inverted();R=np.array(Q)
      for distance in (0,.015):
       initial=outward*distance;vs={n:(v-anchor)@R.T+anchor+initial for n,v in base.items()};score,dep,delta,solved=project(ns,vs);delta+=initial;cost=1e6*score+float(delta@delta)+math.radians(deg)**2*.002;candidates.append((cost,dep,delta,Q,solved,deg,axis))
       if dep<=.0029:break
      if candidates[-1][1]<=.0029:break
     if candidates[-1][1]<=.0029:break
    cost,dep,delta,Q,vs,deg,axis=min(candidates,key=lambda x:x[0]);m=(Q@M[bn].to_3x3()).to_4x4();m.translation=M[bn].translation+Vector(delta);M[bn]=m
    for n in ns:V[n]=vs[n];T[n]=tree(V[n],F[n])
    changed=True;counts+=1
   residual=[(max(c[0] for c in cs),bn) for bn,ns in groups if (cs:=constraints(ns,{n:V[n] for n in ns}))]
   if not residual:break
  assert not residual,('UNRESOLVED',role,float(f),residual)
  if smooth and prev_world:
   for bn,m in M.items():
    distance=(m.translation-motion_start[bn].translation).length;angle=math.degrees(m.to_quaternion().rotation_difference(motion_start[bn].to_quaternion()).angle);angle=min(angle,360-angle)
    assert distance<.075 and angle<25,('MOTION_JUMP',role,float(f),bn,distance,angle)
  prev_world={bn:m.copy() for bn,m in M.items()};prev_parents={bn:armik.W(r,r.data.bones[bn].parent.name).copy() for bn,_ in groups}
  pose={}
  for bn,_ in groups:armik.set_world(r,bn,M[bn]);pose[bn]=r.pose.bones[bn].matrix_basis.copy()
  keys.append((float(f),pose))
  if int(f*2)%20==0:print('CONTACT_CLEAR',role,f,flush=True)
 previous={}
 for f,pose in keys[-sample_count:]:
  for bn,m in pose.items():
   b=r.pose.bones[bn];q=m.to_quaternion()
   if bn in previous and q.dot(previous[bn])<0:q=-q
   previous[bn]=q.copy();b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.location=m.translation;b.keyframe_insert('rotation_quaternion',frame=f);b.keyframe_insert('location',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for curve in bag.fcurves:
     for key in curve.keyframe_points:key.interpolation='LINEAR'
 report[role]={'samples':len(keys),'corrections':counts};bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/'+result_name+'.blend')));(P/('review/'+result_name+'.json')).write_text(json.dumps(report,indent=2)+'\n')
sys.stdout.flush();os._exit(0)
