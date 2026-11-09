"""Check the reduced skin against the source surface in every action, plus UV coverage."""
import bpy,json,runpy,numpy as np
from pathlib import Path
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];samples={};report={}
def points(role,f):
 r=bpy.data.objects['Rig'];r.animation_data.action=bpy.data.actions[role];bpy.context.scene.frame_set(int(f),subframe=f-int(f));ev=bpy.data.objects['Body'].evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();a=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();return a
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_v1.blend'))
for a in list(bpy.data.actions):
 for f in np.linspace(*a.frame_range,9):samples[(a.name,float(f))]=points(a.name,f)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anim_uv.blend'))
for (role,f),before in samples.items():
 after=points(role,f);tree=KDTree(len(before))
 for i,v in enumerate(before):tree.insert(v,i)
 tree.balance();dist=np.array([tree.find(v)[2] for v in after]);item=report.setdefault(role,{'min_z':1e9,'p95_vertex_distance':0,'maximum_vertex_distance':0});item['min_z']=min(item['min_z'],float(after[:,2].min()));item['p95_vertex_distance']=max(item['p95_vertex_distance'],float(np.percentile(dist,95)));item['maximum_vertex_distance']=max(item['maximum_vertex_distance'],float(dist.max()))
 assert dist.max()<.08,(role,f,dist.max())
 assert after[:,2].min()>-.015,(role,f,after[:,2].min())
(P/'work/reduction_deformation_check.json').write_text(json.dumps(report,indent=2)+'\n');print('REDUCED CHECK',json.dumps(report))
runpy.run_path(str(P/'scripts/uv_gate.py'));runpy.run_path(str(P/'scripts/uv_raster.py'))
