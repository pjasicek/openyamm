import bpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_settled.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
pc=np.array([v.value for v in b.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in b.data.vertices]);rows=[]
r.animation_data.action=bpy.data.actions['Attack'];r.animation_data.action_slot=r.animation_data.action.slots[0]
for f in np.arange(0,52.5+.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=np.array([(b.matrix_world@v.co)[:] for v in me.vertices]);ev.to_mesh_clear()
 rows.append({'t':float(f/30),'shoe_m':float(co[(pc==6)&(rest[:,2]<.1),2].min()),'peg_m':float(co[pc==12,2].min())})
out={name:{'min_m':min(r[name] for r in rows),'max_m':max(r[name] for r in rows)} for name in ['shoe_m','peg_m']}
(P/'review/dual_cast/support.json').write_text(json.dumps({'extrema':out,'samples':rows},indent=2)+'\n');print('SUPPORT',out,flush=True)
assert all(v['min_m']>=-.002 and v['max_m']<=.02 for v in out.values())
