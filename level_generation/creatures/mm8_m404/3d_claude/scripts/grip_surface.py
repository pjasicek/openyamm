"""Refine closed fists against the actual solid sword; publish only a passing pair."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from types import SimpleNamespace
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/claude_shared/gates').resolve()))
import run_gates as gates
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_motion.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sword=bpy.data.objects['SwordMesh']
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
snap={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data.action=None
for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
bpy.context.view_layer.update()
def posed(ob):
 bpy.context.view_layer.update();e=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
 co=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();return co
inv=rig.data.bones['Socket_Sword'].matrix_local.inverted()
local=np.array([tuple(inv@v.co) for v in sword.data.vertices]);sword.data.calc_loop_triangles()
faces=np.array([f.vertices[:] for f in sword.data.loop_triangles]);co=posed(sword)
_,first,weld=np.unique(local,axis=0,return_index=True,return_inverse=True)
mesh=SimpleNamespace(rest=co,faces=faces,weld=weld,weld_first=first,label='sword',find_components=lambda:None,components=np.zeros(len(co),int))
solid=gates.Surface(mesh,np.ones(len(co),bool)).build(co)
assert solid.closed
rest=np.array([v.co[:] for v in body.data.vertices]);labels=np.array([v.value for v in body.data.attributes['finger'].data]);report={};candidates={}
body.data.calc_loop_triangles();triangles=np.array([t.vertices[:] for t in body.data.loop_triangles]);bary=np.r_[np.eye(3),[[.5,.5,0],[0,.5,.5],[.5,0,.5],[1/3]*3]]
for side in 'RL':
 g=json.load(open(p/('work/grip_pose_'+side+'.json')));out={}
 # Bounds exclude the hooked guard and the pommel from contact-gap targets.
 axial=(local[:,1]>=0)&(local[:,1]<=.15) if side=='R' else (local[:,1]>=-.15)&(local[:,1]<=0)
 grip_mask=axial&(abs(local[:,0])<.04)&(abs(local[:,2])<.04)
 gripfaces=faces[grip_mask[faces].all(1)];assert len(gripfaces)>0
 tree=BVHTree.FromPolygons(co.tolist(),gripfaces.tolist(),all_triangles=True)
 for digit in (0,1,2,4):
  mask=(labels==digit+1)&(rest[:,0]*(-1 if side=='R' else 1)>0)
  tri=triangles[mask[triangles].any(1)];assert len(tri)>3
  names=[n for n in g['finger_local'] if n.startswith('B_'+side+'_Finger'+str(digit))];assert len(names)==3
  groups={body.vertex_groups[n].index for n in names}
  hand_groups={v.index for v in body.vertex_groups if v.name=='B_'+side+'_Hand' or v.name.startswith('B_'+side+'_Finger')}
  weights=np.array([sum(e.weight for e in v.groups if e.group in groups) for v in body.data.vertices])
  hand_weight=np.array([sum(e.weight for e in v.groups if e.group in hand_groups) for v in body.data.vertices])
  contact_tri=triangles[(hand_weight[triangles]>.3).all(1)]
  contact_mask=np.einsum('sk,tk->ts',bary,weights[contact_tri]).ravel()>.3
  assert contact_mask.any(), 'No weighted digit samples'
  def metric():
   vertices=posed(body)
   points=np.einsum('sk,tkj->tsj',bary,vertices[tri]).reshape(-1,3)
   contact=np.einsum('sk,tkj->tsj',bary,vertices[contact_tri]).reshape(-1,3)[contact_mask]
   signed,_=solid.signed(points);depth=max(0,-float(signed.min()))
   gap=min(tree.find_nearest(Vector(v))[3] for v in contact)
   return max(0,gap-.001)**2+100*depth**2,gap,depth
  initial=metric()
  for step in (() if initial[1]<.002 and initial[2]<.001 else (8,4,2,1)):
   for repeat in range(3):
    change=0
    for name in names:
     pb=rig.pose.bones[name]
     for axis in ((1,0,0),(0,1,0),(0,0,1)):
      start=pb.rotation_quaternion.copy();best=metric()[0];winner=start
      for angle in (-step,step):
       pb.rotation_quaternion=start@Quaternion(axis,math.radians(angle));cost=metric()[0]
       if cost<best-1e-9:best=cost;winner=pb.rotation_quaternion.copy()
      change+=start.rotation_difference(winner).angle;pb.rotation_quaternion=winner
    if change<1e-4:break
  end=metric();out[str(digit)]={'initial_gap_mm':initial[1]*1000,'gap_mm':end[1]*1000,'penetration_mm':end[2]*1000}
  for n in names:g['finger_local'][n]=list(rig.pose.bones[n].rotation_quaternion)
  print('FINGER_CONTACT',side,digit,out[str(digit)],flush=True)
 g['surface_fit']=out;candidates[side]=g;report[side]=out
 json.dump(g,open(p/('work/grip_pose_candidate_'+side+'.json'),'w'),indent=2)
json.dump(report,open(p/'work/grip_surface_report.json','w'),indent=2)
assert max(v['gap_mm'] for side in report.values() for v in side.values())<3, 'Finger contact gap'
assert max(v['penetration_mm'] for side in report.values() for v in side.values())<3, 'Finger penetration'
for side,g in candidates.items():json.dump(g,open(p/('work/grip_pose_'+side+'.json'),'w'),indent=2)
