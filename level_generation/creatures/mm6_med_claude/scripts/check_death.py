import bpy,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];r.animation_data.action=bpy.data.actions['Death'];bpy.context.scene.frame_set(49);e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();c=np.array([v.co[:] for v in m.vertices]);a=np.array([x.value for x in o.data.attributes['part'].data]);print('DEAD bounds',c.min(0),c.max(0))
for mask,n in [(a==0,'body'),(a==106,'face'),(a>=100,'crown'),(np.isin(a,[1,4]),'hands')]:print(n,c[mask,2].min(),c[mask,2].max(),np.percentile(c[mask,2],[5,25,50]))
for n in ['Root','Serpent_00','B_Pelvis','B_Spine','B_Spine2','B_Neck','B_Head']:print(n,r.pose.bones[n].head[:])

for part in np.unique(a):
 if c[a==part,2].min()<.08:print('LOW',int(part),float(c[a==part,2].min()),c[a==part][c[a==part,2].argmin()].tolist())
e.to_mesh_clear()
