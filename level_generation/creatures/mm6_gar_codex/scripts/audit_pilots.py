"""Evaluate quarter-frame surface and hand trajectories on the actual reduced animation master."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/pilots_skin.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
co=np.array([v.co[:] for v in body.data.vertices]);edges=np.array([e.vertices[:] for e in body.data.edges]);length=np.linalg.norm(co[edges[:,1]]-co[edges[:,0]],axis=1);valid=length>.003
report={}
for name in ['Flight','Attack']:
 act=bpy.data.actions[name];rig.animation_data.action=act
 if act.slots:rig.animation_data.action_slot=act.slots[0]
 rows=[]
 for f in np.arange(0,float(act.frame_end)+.01,.25):
    scene.frame_set(math.floor(f),subframe=f%1);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    posed=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();assert np.isfinite(posed).all()
    ratio=np.linalg.norm(posed[edges[:,1]]-posed[edges[:,0]],axis=1)/np.maximum(length,1e-6)
    rows.append({'time':float(f/30),'edge_p99':float(np.quantile(ratio[valid],.99)),'edge_max':float(ratio[valid].max()),
        'above_3x':int((ratio[valid]>3).sum()),'hands':{sd:list(rig.pose.bones[f'B_{sd}_Hand'].head) for sd in ['L','R']}})
 report[name]={'samples':len(rows),'max_p99':max(r['edge_p99'] for r in rows),'max_edge':max(r['edge_max'] for r in rows),
    'most_extended':{sd:min(rows,key=lambda r:r['hands'][sd][1]) for sd in ['L','R']},'samples_detail':rows}
print('PILOT_AUDIT',{k:{x:v[x] for x in ['samples','max_p99','max_edge']} for k,v in report.items()})
(P/'work/pilot_audit_skin.json').write_text(json.dumps(report,indent=2))
