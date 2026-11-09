import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];import arm_ik as IK
left=IK.Side('L');left.grip_hand=Vector(json.loads((P/'work/round3_left_grip.json').read_text())['handle_centre_hand_local'])
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');m=S.load_meshes(g)[0];cfg=json.loads((P/'gates.json').read_text());S.configure_mesh(m,cfg,S.Report(cfg));pm=S.load_meshes(S.Glb(P/'review/round4_dense_spear.glb'))[0];surf=S.Surface(m,m.solid&~m.regions['hand_R']);rows={}
for f in range(53,74):
 C.activate('Attack',f/48);rows[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones}
r.animation_data.action=None
trials=[]
for axis in [(x,y,z)for x in [-1,0,1]for y in [-1,0,1]for z in [-1,0,1]if (x,y,z)!=(0,0,0)]:
 v=Vector(axis).normalized()
 for amp in [.025,.05,.08]:
  worst=0.;worstf=0
  for f,row in rows.items():
   for n,basis in row.items():r.pose.bones[n].matrix_basis=basis
   bpy.context.view_layer.update();h=r.pose.bones['B_L_Hand'];target=h.matrix@left.grip_hand
   target+=v*amp*(math.sin(math.pi*(f-52)/20)**2 if 52<f<72 else 0)
   left.apply(left.pose_anatomical(target,h.matrix.to_3x3(),r.pose.bones['B_L_Forearm'].head-r.pose.bones['B_L_UpperArm'].head))
   pose=g.rest.copy()
   for b in r.pose.bones:
    if b.name in g.names:pose[g.names[b.name]]=np.array(b.matrix)
   points=m.posed(pose);pp=S.transform(pose[g.names['Spear']]@np.linalg.inv(S.C),pm.rest);d,_=S.penetration(surf.build(points),pp)
   if d>worst:worst=d;worstf=f
   if worst>2:break
  trials.append({'offset':list(v*amp),'depth_mm':worst,'frame':worstf})
 print('SEARCH',axis,sorted(trials,key=lambda x:x['depth_mm'])[:1],flush=True)
trials.sort(key=lambda x:x['depth_mm']);(P/'work/round4_release_search.json').write_text(json.dumps(trials,indent=2));print('RESULT',trials[:12],flush=True)
