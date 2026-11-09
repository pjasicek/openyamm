"""Compress the flexible calf feathers during the deep lunge; feet and corpse poses are untouched."""
import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
sys.path.insert(0,str(P.parent/'claude_shared/gates'));import run_gates as S
g=S.Glb(P/'export/mm6_natm.glb');meshes=S.load_meshes(g);bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];names=['Feather_B_R_Calf','Feather_B_L_Calf'];masks={}
for name in names:
 masks[name]=[]
 for m in meshes:
  ids=np.array([n==name for n in m.bone_names]);masks[name].append((ids[m.joints]*m.weights).sum(1)>.99)
required={n:np.zeros(109)for n in names}
for f in range(109):
 C.activate('Attack',f/48);pose=g.rest.copy()
 for b in r.pose.bones:
  if b.name in g.names:pose[g.names[b.name]]=np.array(b.matrix)
 posed=[m.posed(pose)for m in meshes]
 for n in names:
  z=min(float(p[mask,2].min())for p,mask in zip(posed,masks[n])if mask.any());pivot=pose[g.names[n],2,3]
  if z<.002:required[n][f]=max(0,1-(pivot-.002)/(pivot-z))
fold={n:np.max(np.array([d*np.maximum(0,1-abs(np.arange(109)-i)/12)for i,d in enumerate(values)]),axis=0)for n,values in required.items()}
for n,v in fold.items():assert v.max()<.5 and v[0]==v[-1]==0,(n,v.max(),v[0],v[-1])
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in range(109):
  for n,v in fold.items():b=r.pose.bones[n];b.scale=(1-v[f],)*3;b.keyframe_insert('scale',frame=f,group=n)
 C.reset();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/runtime_lod{level}.blend'))
(P/'review/round3_calf_feathers.json').write_text(json.dumps({n:{'max_compression':float(v.max()),'values':v.tolist()}for n,v in fold.items()},indent=2));print('CALF_FEATHER_FIT',{n:float(v.max())for n,v in fold.items()},flush=True)
