"""Bake the short wrap on a 16-column surface cage with skin collisions and continuous loops.
Like the cloak workflows, the garment owns its controls, keeps a fixed waist and resolves collisions outward.
Translation controls preserve the curved surface between columns; the body and original motions stay unchanged.
"""
from pathlib import Path
import bpy,sys,runpy,math,json,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
path=p/'scripts/space_fidget.py';sys.argv=[str(path),'--'];runpy.run_path(str(path),run_name='__main__')
for name in ('wrap_motion.py','waist_weights.py'):
 path=p/'scripts'/name;sys.argv=[str(path),'--',str(p/'work/animated_fixed.blend'),str(p/'work/animated_fixed.blend')];runpy.run_path(str(path),run_name='__main__')
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;scene=bpy.context.scene
ids=[v.index for v in me.vertices if me.attributes['piece'].data[v.index].value==1];assert len(ids)==1200
rest=np.array([v.co[:] for v in me.vertices]);skinfaces=[list(f.vertices) for f in me.polygons if me.attributes['piece'].data[f.vertices[0]].value==0]
assert np.ptp(rest[ids[:80],2])<1e-5
clips=('Standing','Walking','Running','Attack','Hit','Fidget','Death','Dead');captured={}
def activate(act):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
def coords():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=np.array([v.co[:] for v in em.vertices]);ev.to_mesh_clear();return co
for name in clips:
 act=bpy.data.actions[name];activate(act);rows=[]
 for f in range(int(act.frame_range[0]),int(act.frame_range[1])+1):
  scene.frame_set(f);rows.append(coords()[ids])
 captured[name]=rows
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
names=[]
for row in (5,9,14):
 for c in range(16):
  n=f'Wrap_{row}_{c:02d}';b=rig.data.edit_bones.new(n);b.head=Vector(rest[ids[row*80+c*5]]);b.tail=b.head+Vector((0,.05,0));b.parent=rig.data.edit_bones['B_Pelvis'];names.append(n)
bpy.ops.object.mode_set(mode='OBJECT')
groups=[body.vertex_groups.new(name=n) for n in names];W=np.zeros((1200,48))
for i,vi in enumerate(ids):
 row,col=divmod(i,80);c=col//5;t=(col%5)/5;ang=((c,1-t),((c+1)%16,t))
 if row<=5:
  u=float(np.clip((row-2)/3,0,1));u=u*u*(3-2*u);rad=((0,u),)
 elif row<=9:
  u=(row-5)/4;rad=((0,1-u),(1,u))
 else:
  u=(row-9)/5;rad=((1,1-u),(2,u))
 for rr,rw in rad:
  for cc,cw in ang:W[i,rr*16+cc]=rw*cw
 v=me.vertices[vi];old={g.group:g.weight for g in v.groups if not body.vertex_groups[g.group].name.startswith('B_Wrap_')}
 if not old:old={body.vertex_groups['B_Pelvis'].index:1}
 oldtotal=sum(old.values());fixed=max(0,1-W[i].sum())
 new={g:fixed*w/oldtotal for g,w in old.items()}
 new.update({groups[k].index:float(w) for k,w in enumerate(W[i]) if w>0})
 keep=sorted(new.items(),key=lambda q:q[1],reverse=True)[:4];total=sum(w for g,w in keep)
 for g in list(v.groups):body.vertex_groups[g.group].remove([vi])
 for g,w in keep:
  if w>1e-7:body.vertex_groups[g].add([vi],w/total,'REPLACE')
 W[i]=[next((g.weight for g in v.groups if g.group==gg.index),0) for gg in groups]
assert max(len(me.vertices[i].groups) for i in ids)<=4
pinv=np.linalg.pinv(W);active=np.where(W.sum(1)>.05)[0];report={};restpel=rig.data.bones['B_Pelvis'].matrix_local
radial=rest[ids].copy();radial[:,1]-=.027;radial[:,2]=0;radial/=np.linalg.norm(radial,axis=1)[:,None]
def inside(tree,point):
 d=Vector((1,.317,.193)).normalized();start=Vector(point);count=0
 for _ in range(100):
  hit,normal,index,dist=tree.ray_cast(start,d,10)
  if hit is None:return bool(count%2)
  count+=1;start=hit+d*1e-5
 raise AssertionError('Skin parity ray failed')
bone_radial=radial[[row*80+c*5 for row in (5,9,14) for c in range(16)]]
def project(C,base,tree,outward):
 worst=0;count=0
 # Positive radial displacement cannot cancel a neighbouring section's collision response.
 dirs=outward[[row*80+c*5 for row in (5,9,14) for c in range(16)]]
 for iteration in range(20):
  X=base+W@C;inc=np.zeros(48);bad=0
  for i in active:
   loc,normal,face,dist=tree.find_nearest(Vector(X[i]),.25)
   if loc is None:continue
   inward=(Vector(X[i])-loc).dot(normal)<0
   if inward and inside(tree,X[i]):
    d=Vector(outward[i]);hit,_,_,length=tree.ray_cast(Vector(X[i]),d,1.0)
    assert hit is not None,'No outward escape from skin'
    needed=length+margin;worst=max(worst,float(dist))
   elif not inward and dist<margin*.67 and np.dot(normal,outward[i])>.3:
    needed=(margin-dist)/max(.3,np.dot(normal,outward[i]))
   else:continue
   bad+=1;js=np.where(W[i]>0)[0];den=sum(W[i,j]*max(.1,np.dot(dirs[j],outward[i])) for j in js)
   for j in js:inc[j]=max(inc[j],needed/den)
  count=max(count,bad)
  if not bad:break
  C+=dirs*inc[:,None]
 return C,worst,count
for name in clips:
 margin=.05 if name=='Running' else .018
 act=bpy.data.actions[name];activate(act);states=[];solved=[];worst=0;count=0;initial=0;fit=0
 for k,desired in enumerate(captured[name]):
  scene.frame_set(k)
  for n in names:rig.pose.bones[n].location=(0,0,0)
  bpy.context.view_layer.update();co=coords();base=co[ids];delta=rig.pose.bones['B_Pelvis'].matrix@restpel.inverted();R=np.array(delta.to_3x3());tree=BVHTree.FromPolygons(co.tolist(),skinfaces);outward=radial@R.T
  C=pinv@(desired-base);initial=max(initial,float(np.linalg.norm(C,axis=1).max()));fit=max(fit,float(np.linalg.norm(base+W@C-desired,axis=1).max()));C,d,n=project(C,base,tree,outward);worst=max(worst,d);count=max(count,n)
  states.append((base,tree,R,outward));solved.append(C)
 # Smooth the control trajectory, then restore the collision margin.
 smooth=np.array(solved);loop=name in ('Standing','Walking','Running')
 for k in range(len(solved)):
  prev=(k-1)%(len(solved)-1) if loop else max(k-1,0);nxt=(k+1)%(len(solved)-1) if loop else min(k+1,len(solved)-1)
  C=(np.array(solved[prev])+2*np.array(solved[k])+np.array(solved[nxt]))/4
  base,tree,R,outward=states[k];smooth[k]=project(C,base,tree,outward)[0]
 if loop:smooth[-1]=smooth[0]
 for k,C in enumerate(smooth):
  R=states[k][2]
  for j,n in enumerate(names):
   pb=rig.pose.bones[n];pb.location=Vector(np.linalg.solve(R,C[j]));pb.keyframe_insert('location',frame=k)
 for k,C in enumerate(smooth):
  scene.frame_set(k);actual=coords()[ids];expected=states[k][0]+W@C
  assert np.max(np.abs(actual-expected))<2e-5, (name,k,float(np.max(np.abs(actual-expected))))
 report[name]={'initial_control_shift_m':initial,'baseline_fit_max_m':fit,'frames':len(solved),'initial_contact_depth_m':worst,'max_contact_vertices':count,'max_control_shift_m':float(np.linalg.norm(smooth,axis=2).max())}
 print('WRAP_CAGE',name,report[name],flush=True)
# The four original controls are retained as non-deforming history; only the new surface cage carries the wrap.
for n in ('Front','Back','Left','Right'):rig.data.bones['B_Wrap_'+n].use_deform=False
assert len(rig.data.bones)<128
rig.animation_data.action=None
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     if 'Wrap_' in fc.data_path:
      for k in fc.keyframe_points:k.interpolation='LINEAR'
(p/'review/wrap_cage.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/cage.blend'))
