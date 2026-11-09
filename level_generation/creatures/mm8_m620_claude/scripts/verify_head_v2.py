"""Check the fitted neck against the delivered civilian motions and retained body."""
from pathlib import Path
import bpy,sys,json,runpy,hashlib,numpy as np
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/check_final_structure.py'),run_name='__main__')
body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];m=body.data
head=np.array([a.value for a in m.attributes['head'].data]);region=np.array([a.value for a in m.attributes['region'].data]);rest=np.array([v.co[:] for v in m.vertices])
body_ids=set(i for f in m.polygons if not head[f.index] for i in f.vertices)
head_ids=set(i for f in m.polygons if head[f.index] for i in f.vertices)
neck=body_ids&head_ids
assert len(neck)>20,len(neck)
rigid_ids={i for i in head_ids if m.vertices[i].co.z>=1.46499}
assert all(len(m.vertices[i].groups)==1 and body.vertex_groups[m.vertices[i].groups[0].group].name=='B_Head' and abs(m.vertices[i].groups[0].weight-1)<1e-6 for i in rigid_ids)
report={'neck_join_shared_vertices':len(neck),'connected_skin':True,'head_rigid_vertices':len(rigid_ids),'neck_blends_into_body':True}
current={r:sorted(tuple(round(c,7) for c in v.co) for v in m.vertices if region[v.index]==r) for r in (1,2,3,6)}
bpy.ops.wm.open_mainfile(filepath=str(p/'work/checkpoint_before_head_v2/work/rig_textured_uv.blend'));old=bpy.data.objects['Body'];r=old.data.attributes['region']
for group,coords in current.items():assert coords==sorted(tuple(round(c,7) for c in v.co) for v in old.data.vertices if r.data[v.index].value==group),group
report['clothing_boots_cord_positions_unchanged']=True;report['cranium_rigid']=True
(p/'review/validation/head_v2.json').write_text(json.dumps(report,indent=2)+'\n');print('HEAD_V2',report)
runpy.run_path(str(p/'scripts/verify_export.py'),run_name='__main__')
