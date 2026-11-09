"""Find the smallest free-arm adjustment that clears the cloak during the selected recoil."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));from volume_contact import inside
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_v15_clearance.blend'))
r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];sc=bpy.context.scene;me=o.data
pv=np.zeros(len(me.vertices),np.int32);me.attributes['piece'].data.foreach_get('value',pv)
cf=[tuple(f.vertices) for f in me.polygons if all(pv[i]==0 for i in f.vertices)]
ids=[]
for v in me.vertices:
 if sum(g.weight for g in v.groups if o.vertex_groups[g.group].name.startswith(('B_L_Forearm','B_L_Hand','B_L_Finger')))> .5:ids.append(v.index)
a=bpy.data.actions['Hit'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];end=a.frame_range[1]
frames=np.arange(0,end+.001,.625);samples=[]
for f in frames:
 sc.frame_set(int(f),subframe=float(f%1));samples.append({b.name:b.matrix_basis.copy() for b in r.pose.bones})
def apply(ua,fa,f):
 D=r.pose.bones['B_Spine2'].matrix@r.data.bones['B_Spine2'].matrix_local.inverted()
 axis=(D.to_3x3()@Vector((0,-1,0))).normalized();w=math.sin(math.pi*f/end)
 for index,(name,deg) in enumerate([('B_L_UpperArm',ua),('B_L_UpperArm',fa)]):
  if index==1:axis=(D.to_3x3()@Vector((-1,0,0))).normalized()
  pb=r.pose.bones[name];M=pb.matrix.copy();N=(Matrix.Rotation(math.radians(deg)*w,3,axis)@M.to_3x3()).to_4x4();N.translation=M.translation;pb.matrix=N;bpy.context.view_layer.update()
results=[]
for ua,fa in sorted([(u,f) for u in [0,5,10] for f in [0,5,10,15,20,25,30]],key=lambda x:sum(x)):
 worst=0.
 for f,pose in zip(frames,samples):
  sc.frame_set(int(f),subframe=float(f%1))
  for b in r.pose.bones:b.matrix_basis=pose[b.name]
  bpy.context.view_layer.update();apply(ua,fa,f)
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();X=[v.co.copy() for v in m.vertices];ev.to_mesh_clear()
  tree=BVHTree.FromPolygons(X,cf)
  for i in ids:
   loc,n,fi,d=tree.find_nearest(X[i],.05)
   if loc is not None and d>worst and (X[i]-loc).dot(n)<-.7*d and inside(tree,X[i]):worst=d
 results.append({'upper_arm_deg':ua,'shoulder_forward_deg':fa,'depth_mm':worst*1000})
 print('SPACING',results[-1],flush=True)
 if worst<.00001:break
(p/'review/selected_motion_20261011/arm_spacing_forward.json').write_text(json.dumps(results,indent=2))
assert results[-1]['depth_mm']<.01,results[-1]
