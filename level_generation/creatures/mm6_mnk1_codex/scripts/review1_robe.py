"""A closed robe: twelve four-link rigid chains, baked with floor and leg clearance."""
import bpy,math,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/animation_finish.blend'))
r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.zeros(len(co),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
faces=[tuple(f.vertices) for f in me.polygons if pv[f.vertices[0]]==1]
tree=BVHTree.FromPolygons(co.tolist(),faces);axis=Vector((-.006,-.03,0));zs=[1.04,.79,.54,.29,.045];chains=[]
for c in range(12):
 a=c*math.tau/12;d=Vector((math.sin(a),math.cos(a),0));pts=[]
 for z in zs:
  o=Vector((axis.x,axis.y,z));hit=tree.ray_cast(o+d*.7,-d,1.0)[0]
  assert hit is not None,(c,z)
  pts.append(hit)
 chains.append(pts)
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for c,pts in enumerate(chains):
 parent=r.data.edit_bones['B_Pelvis']
 for k in range(4):
  b=r.data.edit_bones.get(f'Robe_{c}_{k}') or r.data.edit_bones.new(f'Robe_{c}_{k}');b.head=pts[k];b.tail=pts[k+1];b.parent=parent;b.use_connect=k>0;parent=b
bpy.ops.object.mode_set(mode='OBJECT')
for c in range(12):
 for k in range(4):body.vertex_groups.get(f'Robe_{c}_{k}') or body.vertex_groups.new(name=f'Robe_{c}_{k}')
for v in me.vertices:
 if pv[v.index]!=1:continue
 for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
 ang=(math.atan2(v.co.x-axis.x,v.co.y-axis.y)%math.tau)/math.tau*12;c=int(ang);u=ang-c
 z=v.co.z;t=max(0,min(3,(1.04-z)/.25-.5));k=int(t);w=t-k
 top=max(0,min(1,(1.06-z)/.13));top=top*top*(3-2*top)
 weights={'B_Pelvis':(1-top)*.75,'B_Spine':(1-top)*.25}
 for ci,cw in [(c,1-u),((c+1)%12,u)]:
  for ki,kw in [(k,1-w),(min(3,k+1),w)]:
   n=f'Robe_{ci}_{ki}';weights[n]=weights.get(n,0)+top*cw*kw
 for n,w in weights.items():
  if w>1e-7:body.vertex_groups[n].add([v.index],w,'REPLACE')
prest=r.data.bones['B_Pelvis'].matrix_local.copy();srest=r.data.bones['B_Spine1'].matrix_local.copy()
report={}
for act in list(bpy.data.actions):
 if act.name!='Death':continue
 r.animation_data.action=act
 if len(act.slots):r.animation_data.action_slot=act.slots[0]
 prev={};worst=0
 for f in np.arange(0,int(act.frame_range[1])+.01,.5):
  sc.frame_set(int(f),subframe=float(f%1));pm=r.pose.bones['B_Pelvis'].matrix@prest.inverted();sm=r.pose.bones['B_Spine1'].matrix@srest.inverted();up=sm.to_3x3()@Vector((0,0,1))
  tilt=math.acos(max(-1,min(1,up.z)));lying=max(0,min(1,(tilt-math.radians(25))/math.radians(50))) if act.name=='Death' else 0
  lying=lying*lying*(3-2*lying);fw=pm.to_3x3()@Vector((0,-1,0));yaw=Matrix.Rotation(math.atan2(fw.x,-fw.y),3,'Z')
  floor=.072+(.11*(1-lying)*max(0,min(1,(.98-r.pose.bones['B_Pelvis'].head.z)/.12)) if act.name=='Death' else 0)
  caps=[]
  for sd in ['L','R']:
   for a,b,rad in [('Thigh','Calf',.105),('Calf','Foot',.085)]:caps.append((r.pose.bones[f'B_{sd}_{a}'].head.copy(),r.pose.bones[f'B_{sd}_{b}'].head.copy(),rad))
  grid=[]
  for c,pts in enumerate(chains):
   root=pm@pts[0];chain=[root]
   for k in range(4):
    off=pts[k+1]-pts[0];hanging=root+yaw@off;laid=root+sm.to_3x3()@off
    target=hanging.lerp(laid,lying);target.z=(1-lying)*target.z+lying*min(target.z,.065+.14*(1-(k+1)/4));target.z=max(floor,target.z)
    for a,b,rad in caps:
     ab=b-a;t=max(0,min(1,(target-a).dot(ab)/ab.length_squared));q=a+ab*t;delta=target-q
     if delta.length<rad:
      if delta.length<.0001:delta=Vector((math.sin(c*math.tau/12),math.cos(c*math.tau/12),0))
      target=q+delta.normalized()*rad
    L=(pts[k+1]-pts[k]).length;d=(target-chain[-1]).normalized();end=chain[-1]+d*L
    if end.z<floor:
     dz=floor-chain[-1].z;horizontal=Vector((d.x,d.y,0))
     if horizontal.length<.001:horizontal=Vector((math.sin(c*math.tau/12),math.cos(c*math.tau/12),0))
     if abs(dz)<L:end=chain[-1]+horizontal.normalized()*math.sqrt(L*L-dz*dz)+Vector((0,0,dz))
    chain.append(end)
   grid.append(chain)
  grid=np.array([[tuple(v) for v in row] for row in grid])
  for attempt in range(10):
   for iteration in range(18):
    for k in range(1,5):
     for c in range(12):
      d=(c+1)%12;vec=grid[d,k]-grid[c,k];length=np.linalg.norm(vec);limit=(chains[d][k]-chains[c][k]).length*1.08
      if length>limit:
       delta=vec*(length-limit)/length*.5;grid[c,k]+=delta;grid[d,k]-=delta
    for c,pts in enumerate(chains):
     for k in range(4):
      vec=grid[c,k+1]-grid[c,k];L=(pts[k+1]-pts[k]).length;vec=vec/max(np.linalg.norm(vec),1e-9)*L
      if grid[c,k,2]+vec[2]<floor:
       dz=floor-grid[c,k,2]
       if abs(dz)<L:
        xy=vec[:2];xy/=max(np.linalg.norm(xy),1e-9);vec=np.r_[xy*math.sqrt(L*L-dz*dz),dz]
      grid[c,k+1]=grid[c,k]+vec
   for c,pts in enumerate(chains):
    for k in range(4):
     n=f'Robe_{c}_{k}';b=r.data.bones[n];pb=r.pose.bones[n]
     q=(pts[k+1]-pts[k]).rotation_difference(Vector(grid[c,k+1]-grid[c,k]))@b.matrix_local.to_quaternion();m=q.to_matrix().to_4x4();m.translation=pb.head;pb.rotation_mode='QUATERNION';pb.matrix=m;bpy.context.view_layer.update()
     q=pb.rotation_quaternion.copy()
     if n in prev and q.dot(prev[n])<0:q.negate()
     prev[n]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f))
     worst=max(worst,abs((pb.tail-pb.head).length-(pts[k+1]-pts[k]).length))
   ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());deformed=ev.to_mesh()
   low=min(v.co.z for v in deformed.vertices if pv[v.index]==1);ev.to_mesh_clear()
   if low>=.004:break
   floor+=min(.08,.006-low)
  assert low>=-.001,(act.name,float(f),low,floor)
 report[act.name]={'max_chain_length_error_m':worst}
# Hold the complete corpse including the robe.
death=bpy.data.actions['Death'];r.animation_data.action=death;r.animation_data.action_slot=death.slots[0];sc.frame_set(int(death.frame_range[1]))
held={b.name:(b.rotation_quaternion.copy(),b.location.copy()) for b in r.pose.bones}
bpy.data.actions.remove(bpy.data.actions['Dead']);dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;r.animation_data.action=dead
for f in [0,30]:
 for n,(q,l) in held.items():
  pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
sc['robe_chains']=json.dumps([[list(p) for p in c] for c in chains]);(p/'work/review1_robe_bake.json').write_text(json.dumps(report,indent=2))
assert max(e['max_chain_length_error_m'] for e in report.values())<1e-5
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/animation_finish.blend'))
