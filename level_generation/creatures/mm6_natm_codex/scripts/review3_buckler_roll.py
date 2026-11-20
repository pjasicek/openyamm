"""Fit forearm pronation so the strapped shield clears the feather mantle at all LODs."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
cfg=json.loads((P/'gates.json').read_text());g=S.Glb(P/'export/mm6_natm.glb');meshes=S.load_meshes(g);props=S.load_meshes(S.Glb(P/'export/mm6_natm_buckler.glb'));surfaces=[]
for m in meshes[:4]:S.configure_mesh(m,cfg,S.Report(cfg));surfaces.append(S.Surface(m,m.solid))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];name='B_L_ForearmTwist';rows=[]
for f in range(109):
 C.activate('Attack',f/48);rows.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
r.animation_data.action=None;fb=r.data.bones['B_L_Forearm'];hb=r.data.bones['B_L_Hand'];axis=(fb.matrix_local.inverted()@hb.head_local).normalized();angles=np.arange(-60,61,3);options=[]
for f in range(20,89):
 for n,m in rows[f].items():r.pose.bones[n].matrix_basis=m
 opts=[]
 for angle in angles:
  r.pose.bones[name].rotation_quaternion=rows[f][name].to_quaternion()@Quaternion(axis,math.radians(float(angle)));bpy.context.view_layer.update();pose=g.rest.copy()
  for bone in r.pose.bones:
   if bone.name in g.names:pose[g.names[bone.name]]=np.array(bone.matrix)
  depth=[]
  for level in [0,1,2,3]:
   points=meshes[level].posed(pose);prop=S.transform(pose[g.names['Buckler']]@np.linalg.inv(S.C),props[level].rest);depth.append(S.penetration(surfaces[level].build(points),prop)[0])
  cost=500*sum(max(0,d-1.2)**2 for d in depth)+.05*angle*angle+(10000*angle*angle if f in [20,88]else 0);opts.append({'cost':cost,'depth':depth,'angle':int(angle)})
 options.append(opts)
 if f%10==0:print('BUCKLER_FIT',f,min(opts,key=lambda o:o['cost']),flush=True)
cost=np.array([o['cost']for o in options[0]]);backs=[]
for opts in options[1:]:
 values=cost[:,None]+8*(angles[:,None]-angles[None,:])**2;back=values.argmin(0);cost=np.array([o['cost']for o in opts])+values[back,np.arange(len(angles))];backs.append(back)
ids=[int(cost.argmin())]
for back in reversed(backs):ids.append(int(back[ids[-1]]))
ids.reverse();selected=[options[k][i]for k,i in enumerate(ids)]
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f,o in zip(range(20,89),selected):
  b=r.pose.bones[name];b.rotation_quaternion=rows[f][name].to_quaternion()@Quaternion(axis,math.radians(o['angle']));b.keyframe_insert('rotation_quaternion',frame=f,group=name)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
(P/'review/round3_buckler_pronation.json').write_text(json.dumps([{'frame':f,**o}for f,o in zip(range(20,89),selected)],indent=2))
