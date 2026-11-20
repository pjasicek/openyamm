import bpy,sys,numpy as np,json
from pathlib import Path
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/master_uv.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene
pc=np.array([a.value for a in b.data.attributes['piece'].data]);rest=np.array([v.co[:] for v in b.data.vertices]);jaw=r.data.bones['B_Head'].head_local.z-.02
hf=[list(f.vertices) for f in b.data.polygons if all(pc[i]==1 and rest[i,2]>jaw for i in f.vertices)]
cf=[list(f.vertices) for f in b.data.polygons if all(pc[i]==0 and abs(rest[i,0])>.12 and rest[i,2]>1.2 for i in f.vertices)]
report={};common.workbench_clay(sc)
for name,frames in [('Attack',[31,34.375,36.875,38.125,47,53.75]),('Hit',[7.5]),('Death',[25])]:
 r.animation_data.action=bpy.data.actions[name];r.animation_data.action_slot=r.animation_data.action.slots[0]
 for f in frames:
  sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[b.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();pairs=BVHTree.FromPolygons(co,hf).overlap(BVHTree.FromPolygons(co,cf))
  report[f'{name}:{f}']=len(pairs);print('HEAD_TRIANGLES',name,f,len(pairs))
  common.render_views(str(P/'review'/f'headcheck_{name}_{f}'),1.35,.8,views=('front','left'),resolution=(500,500))
(P/'review/head_intersection_probe.json').write_text(json.dumps(report,indent=2))
