"""Measure corrected hand volume and per-frame hand edge deformation in the delivered master."""
import bpy,json,math
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];report={};rest={};weights={}
for version,file in [('before','textured_source_v2.blend'),('after','textured_hands_v2.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work'/file));obj=bpy.data.objects['Body'];rest[version]=np.array([v.co[:] for v in obj.data.vertices])
 for sd in ['L','R']:
  for f in range(5):
   weights[(sd,f)]=np.array([sum(g.weight for g in v.groups if obj.vertex_groups[g.group].name.startswith(f'B_{sd}_Finger{f}')) for v in obj.data.vertices])
chains=json.loads((P/'work/finger_chains.json').read_text())
for sd in ['L','R']:
 report[sd]=[]
 for f in range(5):
  mask=weights[(sd,f)]>.9;chain=np.array(chains[sd][f]);radii=[]
  for version in ['before','after']:
   co=rest[version][mask];ds=[]
   for a,b in zip(chain,chain[1:]):
    ab=b-a;t=np.clip((co-a)@ab/(ab@ab),0,1);ds.append(np.linalg.norm(co-a-t[:,None]*ab,axis=1))
   radii.append(float(np.median(np.min(ds,axis=0))))
  report[sd].append({'finger':f,'median_diameter_mm_before':radii[0]*2000,'median_diameter_mm_after':radii[1]*2000,'ratio':radii[1]/radii[0]})
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_gar.blend'));body=bpy.data.objects['Gargoyle'];rig=bpy.data.objects['Rig'];scene=bpy.context.scene
co=np.array([v.co[:] for v in body.data.vertices]);e=np.array([ed.vertices[:] for ed in body.data.edges]);hw=np.array([sum(g.weight for g in v.groups if 'Hand' in body.vertex_groups[g.group].name or 'Finger' in body.vertex_groups[g.group].name) for v in body.data.vertices]);e=e[(hw[e[:,0]]>.3)&(hw[e[:,1]]>.3)];length=np.linalg.norm(co[e[:,0]]-co[e[:,1]],axis=1);valid=length>.003;report['clips']={}
for name in ['Flight','Attack','Hit','Death','Dead']:
 act=bpy.data.actions[name];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];values=[]
 for f in range(round(act.frame_end)+1):
  scene.frame_set(f);ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();posed=np.array([v.co[:] for v in m.vertices]);ev.to_mesh_clear();r=np.linalg.norm(posed[e[:,0]]-posed[e[:,1]],axis=1)/np.maximum(length,1e-6);values.append((float(r[valid].max()),float(np.quantile(r[valid],.99))))
 report['clips'][name]={'samples':len(values),'maximum_edge_ratio':max(v[0] for v in values),'maximum_p99':max(v[1] for v in values)}
 assert max(v[0] for v in values)<3.1,(name,report['clips'][name])
(P/'work/hand_revision_audit.json').write_text(json.dumps(report,indent=2));print('HAND_REVISION_AUDIT',report)
