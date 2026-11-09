import bpy,json,sys,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_skin.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
act=bpy.data.actions['Attack'];rig.animation_data.action=act
if act.slots:rig.animation_data.action_slot=act.slots[0]
audit=json.loads((P/'work/pilot_audit_skin.json').read_text());r=max(audit['Attack']['samples_detail'],key=lambda r:r['edge_max']);f=r['time']*30;scene.frame_set(math.floor(f),subframe=f%1)
co=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(co[edges[:,1]]-co[edges[:,0]],axis=1)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();posed=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();ratio=np.linalg.norm(posed[edges[:,1]]-posed[edges[:,0]],axis=1)/np.maximum(length,1e-6)
worst=np.argsort(np.where(length>.003,ratio,0))[-8:][::-1]
print('WORST',r['time'],[{'r':float(ratio[i]),'rest':co[edges[i]].tolist(),'posed':posed[edges[i]].tolist()} for i in worst])
common.render_views(str(P/'review/pilot_worst'),1.15,1.65,views=('front','left','three_quarter'),resolution=(1000,1000))
for sd in ['L','R']:
 c=rig.pose.bones[f'B_{sd}_Hand'].head
 common.render_views(str(P/f'review/pilot_worst_{sd}_hand'),c.z,.60,views=('front','left','three_quarter'),resolution=(800,800),target=(c.x,c.y))
