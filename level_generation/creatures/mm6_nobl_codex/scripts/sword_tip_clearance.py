import bpy,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(p/'export/mm6_nobl_lod0.glb'))
r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc=bpy.context.scene;rows=[]
for f in np.arange(a.frame_range[0],a.frame_range[1]+1e-5,sc.render.fps/120):
 sc.frame_set(int(f),subframe=float(f%1));rows.append(np.array(r.matrix_world@r.pose.bones['Sword'].matrix)[2])
T=np.array(rows)
for a in [.62,.64,.66,.68,.69,.70,.715]:
 floor=T[:,1]*a+T[:,3]-np.maximum(abs(T[:,0])*.043,abs(T[:,2])*.005)
 print('TIP_FLARE',a,'floor',floor.min()*1000)

for a in [.64,.66,.675,.69,.70,.715,.74,.758]:
 bound=np.min((T[:,1]*a+T[:,3]+.047021)/np.maximum(abs(T[:,0]),1e-9));print('WIDTH_LIMIT',a,bound)
