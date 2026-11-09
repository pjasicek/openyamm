import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];lg=json.loads((P/'work/round3_left_grip.json').read_text());base=json.loads((P/'work/round3_pose_reference.json').read_text())['standing_basis'];names=[n for n in lg['finger_local']if n.startswith('B_L_Finger')]
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');m=S.load_meshes(g)[0];cfg=json.loads((P/'gates.json').read_text());S.configure_mesh(m,cfg,S.Report(cfg));pm=S.load_meshes(S.Glb(P/'review/round4_dense_spear.glb'))[0];surf=S.Surface(m,m.solid&~m.regions['hand_R']);rows={}
for f in range(28,43):
 C.activate('Attack',f/48);rows[f]={b.name:b.matrix_basis.copy()for b in r.pose.bones}
r.animation_data.action=None
trials=[]
for start in [32,34,36,38]:
 for duration in [4,6,8]:
  worst=0;wf=0
  for f,row in rows.items():
   for n,basis in row.items():r.pose.bones[n].matrix_basis=basis
   t=max(0,min(1,(f-start)/duration));t=t*t*(3-2*t)
   for n in names:r.pose.bones[n].rotation_quaternion=Matrix(base[n]).to_quaternion().slerp(Quaternion(lg['finger_local'][n]),t)
   bpy.context.view_layer.update();pose=g.rest.copy()
   for b in r.pose.bones:
    if b.name in g.names:pose[g.names[b.name]]=np.array(b.matrix)
   points=m.posed(pose);pp=S.transform(pose[g.names['Spear']]@np.linalg.inv(S.C),pm.rest);d,_=S.penetration(surf.build(points),pp)
   if d>worst:worst=d;wf=f
  trials.append({'start':start,'duration':duration,'depth_mm':worst,'frame':wf});print('THUMB',trials[-1],flush=True)
trials.sort(key=lambda x:x['depth_mm']);(P/'work/round4_grasp_search.json').write_text(json.dumps(trials,indent=2));print('RESULT',trials[:5],flush=True)
