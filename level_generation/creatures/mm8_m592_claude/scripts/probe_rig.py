"""Isolated deformation gates for the fitted Guardian before clip production."""
from pathlib import Path
import bpy,json,math,numpy as np,sys
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_v1.blend'));scene=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];co=np.array([tuple(v.co) for v in body.data.vertices]);E=np.array([tuple(e.vertices) for e in body.data.edges]);L=np.linalg.norm(co[E[:,0]]-co[E[:,1]],axis=1);good=L>1e-5
F=json.loads((P/'work/claws_fit.json').read_text());out=P/'review/rig_probes';out.mkdir(exist_ok=True)
common.workbench_clay(scene)
def reset():
 for b in rig.pose.bones:b.matrix_basis.identity()
 bpy.context.view_layer.update()
def world_rotate(n,axis,deg):
 m=armik.W(rig,n);r=Quaternion(Vector(axis).normalized(),math.radians(deg)).to_matrix()@m.to_3x3().normalized();armik.set_world(rig,n,armik.rot_world(m,r))
def aim(target,direction,pole):
 n='B_R_Hand';R=rig.data.bones[n].matrix_local.to_3x3();f=sum((Vector(x['base']) for x in F['R']),Vector())/3-rig.data.bones[n].head_local;q=f.normalized().rotation_difference(Vector(direction).normalized());armik.solve(rig,'R',target,pole=pole,hand_rot=q.to_matrix()@R)
def pose(name):
 reset()
 if name=='elbow':aim((-.55,-.55,1.12),(0,-1,-.3),(-.9,0,.95))
 elif name=='overhead':aim((-.55,-.2,1.85),(0,0,1),(-.95,.05,1.35))
 elif name=='cross_body':aim((.05,-.75,.95),(.8,-.2,-.6),(-.8,-.4,.95))
 elif name=='forearm_twist':
  axis=rig.pose.bones['B_R_Hand'].head-rig.pose.bones['B_R_Forearm'].head;world_rotate('B_R_Forearm',axis,70)
 elif name=='claw_fan':
  for side in F:
   for i,f in enumerate(F[side]):rig.pose.bones[f['name']].rotation_quaternion=Quaternion((0,0,1),math.radians((i-1)*12))@Quaternion((1,0,0),math.radians(12))
 elif name=='jaw':rig.pose.bones['Jaw'].rotation_quaternion=Quaternion((1,0,0),math.radians(15))
 elif name=='knees':
  for side in ('R','L'):world_rotate('B_'+side+'_Calf',(1,0,0),-35)
 bpy.context.view_layer.update()
def evaluated():
 ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();c=np.array([tuple(body.matrix_world@v.co) for v in me.vertices]);ev.to_mesh_clear();return c
hard=[]
for side in F:
 for f in F[side]:
  ids=set(f['hard_vertices']);hard.extend(i for i,(a,b) in enumerate(E) if a in ids and b in ids)
hard=np.array(sorted(set(hard)),int);assert len(hard)>100
arm=(np.abs(co[E[:,0],0])>.35)&(np.abs(co[E[:,1],0])>.35)&(co[E[:,0],2]>.55)&good
reports=[]
for name in ('neutral','elbow','overhead','cross_body','forearm_twist','claw_fan','jaw','knees'):
 pose(name);v=evaluated();ratio=np.linalg.norm(v[E[:,0]]-v[E[:,1]],axis=1)/np.maximum(L,1e-9)
 r={'pose':name,'arm_edge_p99':float(np.percentile(ratio[arm],99)),'all_edge_p99':float(np.percentile(ratio[good],99)),'max_edge_ratio':float(ratio[good].max()),'hard_claw_max_relative_error':float(np.max(abs(ratio[hard]-1)))}
 common.render_views(str(out/name),1.0,2.8,views=('front','left','three_quarter'),resolution=(700,700))
 if name in ('elbow','overhead','cross_body','forearm_twist','claw_fan'):
  ids=np.concatenate([f['vertices'] for f in F['R']]);c=v[ids].mean(0);common.render_views(str(out/(name+'_hand')),float(c[2]),.70,views=('front','three_quarter'),resolution=(650,650),target=(float(c[0]),float(c[1])))
 if name=='jaw':common.render_views(str(out/'jaw_head'),1.26,.7,views=('front','left','three_quarter'),resolution=(650,650),target=(0,-.4))
 reports.append(r);print('PROBE',r,flush=True)
(out/'probes.json').write_text(json.dumps(reports,indent=2)+'\n')
assert max(r['hard_claw_max_relative_error'] for r in reports)<.01
reset()
