import bpy,sys,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_sources.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
common.workbench_clay(sc);D=P/'review/round2/sources';D.mkdir(exist_ok=True,parents=True)
report={}
for nm in ['FallBack','DyingSource','SwordDeath']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for i in range(7):
  f=a.frame_range[1]*i/6;sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();rows.append({'frame':f,'pelvis':list(r.pose.bones['B_Pelvis'].head),'floor':float(pts[:,2].min())});common.render_views(str(D/f'{nm}_{i}'),.65,3.5,views=['left'],resolution=(320,320))
 report[nm]=rows
r.animation_data.action=None
verts=[]
for v in b.data.vertices:
 if v.co.z>1.75:
  verts.append({'index':v.index,'co':list(v.co),'weights':{b.vertex_groups[g.group].name:g.weight for g in v.groups if g.weight>.001}})
report['horn_candidates']=verts
(P/'review/round2/source_inspection.json').write_text(json.dumps(report,indent=2))
