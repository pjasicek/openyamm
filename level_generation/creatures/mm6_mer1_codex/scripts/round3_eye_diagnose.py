import bpy,sys,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3/master.blend'));C.activate('Standing');o=bpy.data.objects['Body'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();verts=[v.co.copy()for v in me.vertices];faces=[tuple(f.vertices)for f in me.polygons];tree=BVHTree.FromPolygons(verts,faces);res=[]
for px,py in [(301,287),(297,294),(306,288),(311,300)]:
 x=(px-400)/800*.43;z=1.52+(400-py)/800*.43;h=tree.ray_cast(Vector((x,-5,z)),Vector((0,1,0)));f=o.data.polygons[h[2]];res.append({'pixel':[px,py],'hit':[list(h[0]),list(h[1]),h[2]],'piece':[o.data.attributes['piece'].data[i].value for i in f.vertices],'verts':list(f.vertices),'uv':[list(o.data.uv_layers.active.data[i].uv)for i in f.loop_indices]})
ev.to_mesh_clear();(P/'review/round3/eye_diagnosis.json').write_text(json.dumps(res,indent=2));common.workbench_clay(bpy.context.scene,False)
for m in o.data.materials:m.diffuse_color=(.65,.65,.65,1)
common.render_views(str(P/'review/round3/eye_clay'),1.52,.43,views=('front',),resolution=(800,800))
