"""Every bound clip: actual skinned finger contact and rigid grip centre at quarter frames."""
from pathlib import Path
import bpy,json,sys,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1];blend=Path(sys.argv[sys.argv.index('--')+1]);bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[g.name for g in body.vertex_groups];G={s:json.loads((P/f'work/grip_pose_{s}.json').read_text()) for s in 'LR'}
mask={(s,f):np.array([sum(g.weight for g in v.groups if names[g.group].startswith(f'B_{s}_Finger{f}'))>.5 for v in body.data.vertices]) for s in 'LR' for f in range(5)}
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();v=np.array([list(ob.matrix_world@p.co) for p in me.vertices]);ev.to_mesh_clear();return v
report={'sample_step_frames':.25,'radius_m':.026,'limits':{'max_skin_penetration_m':.004,'max_p10_gap_m':.014,'max_grip_centre_error_m':.00002},'clips':{}}
for a in [a for a in bpy.data.actions if a.name.startswith('Harrower_')]:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];r={'max_skin_penetration_m':0,'max_p10_gap_m':0,'max_grip_centre_error_m':0,'samples':0}
 for f in np.arange(a.frame_range[0],a.frame_range[1]+1e-5,.25):
  sc.frame_set(int(f),subframe=float(f%1));V=coords(body);r['samples']+=1
  for side in 'LR':
   h=rig.matrix_world@rig.pose.bones[f'B_{side}_Hand'].matrix;C=np.array(h@Vector(G[side]['handle_centre_hand_local']));A=np.array(h.to_3x3()@Vector(G[side]['handle_axis_hand_local']));A/=np.linalg.norm(A)
   q=V-C;along=q@A;rad=np.linalg.norm(q-np.outer(along,A),axis=1)
   for finger in range(5):
    rr=rad[mask[side,finger]&(np.abs(along)<.09)]-.026;assert len(rr)>5
    r['max_skin_penetration_m']=max(r['max_skin_penetration_m'],-float(rr.min()));r['max_p10_gap_m']=max(r['max_p10_gap_m'],float(np.percentile(rr,10)))
   for kind in ('Family','Vreth'):
    blade=coords(bpy.data.objects[f'{kind}_Blade_{side}']);r['max_grip_centre_error_m']=max(r['max_grip_centre_error_m'],float(np.linalg.norm(blade[:16].mean(0)-C)))
 r['passed']=all(r[k]<=v for k,v in report['limits'].items());report['clips'][a.name]=r;print('GRIP_GATE',a.name,r,flush=True)
report['passed']=all(r['passed'] for r in report['clips'].values());(P/'review/r2/grip_gate.json').write_text(json.dumps(report,indent=2)+'\n');assert report['passed'],report
