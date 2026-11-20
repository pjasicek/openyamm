"""Fit the existing textured wrap to the measured closed hand, then ground subframes."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_round3_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
me=body.data;pv=np.array([x.value for x in me.attributes['piece'].data]);names=[g.name for g in body.vertex_groups];W=np.zeros((len(me.vertices),len(names)))
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();inverse=rig.pose.bones['Bow'].matrix.inverted();xyz=np.array([tuple(inverse@v.co)for v in m.vertices]);ev.to_mesh_clear()
bindinv=rig.data.bones['Bow'].matrix_local.inverted();local=np.array([tuple(bindinv@v.co)for v in me.vertices])
me.calc_loop_triangles();wrapfaces=[tuple(f.vertices)for f in me.loop_triangles if all(pv[i]==201 and abs(local[i,2])<.100 for i in f.vertices)]
bary=np.array([[i,j,6-i-j]for i in range(7)for j in range(7-i)])/6;points={}
for digit in [0,1,2,4]:
 mask=W[:,[i for i,n in enumerate(names)if n.startswith(f'B_L_Finger{digit}')]].sum(1)>.4
 triangles=np.array([tuple(f.vertices)for f in me.loop_triangles if any(mask[i]for i in f.vertices)and all(pv[i]==3 for i in f.vertices)])
 pts=np.einsum('jk,nkl->njl',bary,xyz[triangles]).reshape(-1,3);points[str(digit)]=pts[abs(pts[:,2])<.110][::2]
wrapids=np.where((pv==201)&(abs(local[:,2])<.12))[0];original=local.copy();best=None;trials=[]
for scale in np.arange(1.,1.801,.025):
 candidate=original.copy()
 for i in wrapids:
  amount=np.clip((.12-abs(original[i,2]))/.025,0,1);candidate[i,:2]*=1+(scale-1)*amount
 tree=BVHTree.FromPolygons(candidate.tolist(),wrapfaces);gaps={};penetration=0
 for digit,pts in points.items():
  gaps[digit]=1
  for point in pts:
   v=Vector(point);hit,n,_,d=tree.find_nearest(v);gaps[digit]=min(gaps[digit],d)
   if d<.005 and (v-hit).dot(n)<-.7*d:penetration=max(penetration,d)
 score=max(gaps.values())+max(0,penetration-.0015)*8
 row={'scale':float(scale),'gaps':gaps,'penetration_m':penetration,'score':score};trials.append(row)
 if best is None or score<best[0]:best=(score,candidate,row)
print('GRIP_FIT',best[2],flush=True)
for i in wrapids:me.vertices[int(i)].co=rig.data.bones['Bow'].matrix_local@Vector(best[1][i])
# Keep the leather loin flap outside the thigh surface.
for v in me.vertices:
 if pv[v.index]==15:v.co.y-=.02
report={'loin_flap_forward_clearance_m':.02,'fit':best[2],'trials':trials,'triangles_unchanged':True}
# Hinge the short loin flap at the belt so it rides over the advancing thigh.
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
ids=np.where(pv==15)[0];pts=np.array([tuple(me.vertices[int(i)].co)for i in ids]);pivot=Vector((float(pts[:,0].mean()),float(pts[:,1].mean()),float(pts[:,2].max())))
bpy.ops.object.mode_set(mode='EDIT');bone=rig.data.edit_bones.new('LoinFlap');bone.head=pivot;bone.tail=pivot+Vector((0,0,-.20));bone.parent=rig.data.edit_bones['B_Pelvis'];bpy.ops.object.mode_set(mode='OBJECT')
for group in body.vertex_groups:group.remove([int(i)for i in ids])
vg=body.vertex_groups.new(name='LoinFlap');vg.add([int(i)for i in ids],1,'REPLACE');flap=rig.pose.bones['LoinFlap'];flap.rotation_mode='QUATERNION'
rest=rig.data.bones['LoinFlap'].matrix_local.copy();pelvis=rig.data.bones['B_Pelvis'].matrix_local.inverted();flap_angles={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];angles=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);D=rig.pose.bones['B_Pelvis'].matrix@pelvis;inv=D.to_3x3().inverted();forward=[]
  for side in 'LR':
   v=inv@(rig.pose.bones[f'B_{side}_Calf'].head-rig.pose.bones[f'B_{side}_Thigh'].head);forward.append(math.atan2(-v.y,-v.z))
  angle=max(0,max(forward))+math.radians(8);flap.matrix=D@Matrix.Translation(pivot)@Matrix.Rotation(-angle,4,'X')@Matrix.Translation(-pivot)@rest
  flap.keyframe_insert('rotation_quaternion',frame=f);flap.keyframe_insert('location',frame=f);angles.append(math.degrees(angle))
 flap_angles[a.name]=[min(angles),max(angles)]
report['loin_flap_hinge_degrees']=flap_angles
# Root clearance covers the complete body and prop at quarter frames; hidden nocked-arrow geometry is excluded.
root=rig.pose.bones['B_Pelvis'];rootinv=rig.data.bones[root.name].matrix_local.to_3x3().inverted();floor={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];N=int(a.frame_range[1]);locations=[];corrections=np.full(N+1,-1e9) if a.name in ['Death','Dead'] else np.zeros(N+1)
 for f in range(N+1):sc.frame_set(f);locations.append(root.location.copy())
 for tick in range(N*4+1):
  f=tick/4;sc.frame_set(int(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();low=min(v.co.z for v in m.vertices if pv[v.index]!=202);ev.to_mesh_clear();dz=.0004-low if a.name in ['Death','Dead'] else max(0,.0004-low)
  for i in {int(f),min(N,math.ceil(f))}:corrections[i]=max(corrections[i],dz)
 for f,l in enumerate(locations):root.location=l+rootinv@Vector((0,0,float(corrections[f])));root.keyframe_insert('location',frame=f)
 floor[a.name]={'max_root_correction_m':float(max(corrections))}
report['floor']=floor;rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master.blend'))
(P/'review/round3_grip_fit.json').write_text(json.dumps(report,indent=2))
