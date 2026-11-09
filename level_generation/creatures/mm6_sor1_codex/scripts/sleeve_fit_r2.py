"""Candidate sleeve skinning and shaft clearance for the fitted two-handed staff grip."""
import bpy,math,json,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree
class Sleeve:
 def __init__(self,rig,body,side):
  self.rig=rig;self.side=side;names=[g.name for g in body.vertex_groups];me=body.data
  chosen=[]
  for v in me.vertices:
   w=sum(g.weight for g in v.groups if names[g.group].startswith(side) and any(k in names[g.group] for k in ['UpperArm','Forearm']))
   if w>.05 and me.attributes['piece'].data[v.index].value==1:chosen.append(v.index)
  remap={i:j for j,i in enumerate(chosen)};self.faces=[tuple(remap[i] for i in f.vertices) for f in me.polygons if all(i in remap for i in f.vertices)];self.local={}
  for n in names:
   ids=[(j,next((g.weight for g in me.vertices[i].groups if names[g.group]==n),0)) for j,i in enumerate(chosen)]
   if not any(w for j,w in ids):continue
   inv=rig.data.bones[n].matrix_local.inverted();a=np.zeros((len(chosen),4))
   for j,w in ids:
    if w:a[j,:3]=np.array(inv@me.vertices[chosen[j]].co)*w;a[j,3]=w
   self.local[n]=a
  self.staff_local=None
  if side=='B_R_':
   g=json.loads((Path(__file__).resolve().parents[1]/'work/grip_pose.json').read_text());C=Vector(g['handle_centre_hand_local']);A=Vector(g['handle_axis_hand_local']);H=rig.data.bones['B_R_Hand'].matrix_local.inverted()
   self.staff_local=[H@v.co for v in bpy.data.objects['Staff'].data.vertices if -.65<((H@v.co)-C).dot(A)<.25]
  self.var=[side+n for n in ['UpperArm','Forearm','Hand','UpperArmTwist','ForearmTwist']];self.count=len(chosen);self.chosen=chosen
  aw={v.index:sum(g.weight for g in v.groups if names[g.group].startswith(side) and any(k in names[g.group] for k in ['UpperArm','Forearm','Hand'])) for v in me.vertices}
  ee=[e.vertices[:] for e in me.edges if all(i in remap and aw[i]>.3 for i in e.vertices)];self.edges=np.array([[remap[i] for i in e] for e in ee]);self.length=np.array([(me.vertices[a].co-me.vertices[b].co).length for a,b in ee])
 def begin(self):
  self.fixed=sum((a@np.array(self.rig.pose.bones[n].matrix).T for n,a in self.local.items() if n not in self.var),np.zeros((self.count,4)))
 def cost(self,r,C,A,refs):
  rig=self.rig;s=self.side;M={}
  for n,R,head in [('UpperArm',r['Ra'],r['S']),('Forearm',r['Rf'],r['E']),('Hand',r['Rh'],r['W'])]:
   m=R.to_4x4();m.translation=head;M[s+n]=m
  def twist(q,axis):return (2*math.atan2(Vector((q.x,q.y,q.z)).dot(axis),q.w)+math.pi)%(2*math.pi)-math.pi
  def helper(n,axis,a):
   b=rig.data.bones[n]
   if n in refs:a+=round((refs[n]*(-.5 if 'UpperArm' in n else .5)-a)/math.pi)*math.pi
   parent=M.get(b.parent.name,rig.pose.bones[b.parent.name].matrix);M[n]=parent@b.parent.matrix_local.inverted()@b.matrix_local@Quaternion(axis,a).to_matrix().to_4x4()
  f,h,u=[rig.data.bones[s+n] for n in ['Forearm','Hand','UpperArm']]
  axis=(f.matrix_local.inverted()@h.head_local).normalized();dq=(M[f.name].inverted()@M[h.name]).to_quaternion()@(f.matrix_local.inverted()@h.matrix_local).to_quaternion().inverted();helper(s+'ForearmTwist',axis,.5*twist(dq,axis))
  axis=(u.matrix_local.inverted()@f.head_local).normalized();local=(rig.pose.bones[u.parent.name].matrix@u.parent.matrix_local.inverted()@u.matrix_local).inverted()@M[u.name];helper(s+'UpperArmTwist',axis,-.5*twist(local.to_quaternion(),axis))
  co=self.fixed.copy()
  for n in self.var:
   if n in self.local:co+=self.local[n]@np.array(M[n]).T
  self.last_co=co[:,:3];self.last_m=M;self.stretch=float(np.percentile(np.linalg.norm(self.last_co[self.edges[:,0]]-self.last_co[self.edges[:,1]],axis=1)/np.maximum(self.length,1e-6),99))
  tree=BVHTree.FromPolygons(co[:,:3].tolist(),self.faces);penalty=0
  points=[r['Rh']@v+r['W'] for v in self.staff_local] if self.staff_local else [C+A*float(t) for t in np.linspace(-.55,.22,48)]
  for pt in points:
   q,n,ix,d=tree.find_nearest(pt,.075)
   if q is not None:
    signed=-d if (pt-q).dot(n)<-.7*d else d
    penalty=max(penalty,(.003 if self.staff_local else .014)-signed)
  return max(0,penalty)
