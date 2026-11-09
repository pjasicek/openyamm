import bpy,bmesh,sys,json,subprocess,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
from reduction_render import render
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));C.activate('Standing',0);o=bpy.data.objects['Body'];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();tree=BVHTree.FromPolygons([v.co.copy()for v in mm.vertices],[f.vertices[:]for f in mm.polygons]);ev.to_mesh_clear();rows=[]
for factor in [.65,1.,1.35]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_feet.blend'));C.activate('Standing',0);r=bpy.data.objects['Rig'];o=bpy.data.objects['Body'];me=o.data;oldn=len(me.vertices);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();edges=[]
 for a,b in [(626,617),(495,490),(617,622),(482,490),(617,628)]:edges.append(next(e for e in bm.verts[a].link_edges if bm.verts[b]in e.verts))
 bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=False);bmesh.ops.triangulate(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();bpy.context.view_layer.update();ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();pos=[v.co.copy()for v in mm.vertices];ev.to_mesh_clear();gn={g.index:g.name for g in o.vertex_groups}
 for v in me.vertices[oldn:]:
  p=pos[v.index];q,n,_,d=tree.find_nearest(p);delta=(q-p)*factor;M=np.zeros((3,3))
  for g in v.groups:
   if gn[g.group]in r.data.bones:M+=np.array((r.pose.bones[gn[g.group]].matrix@r.data.bones[gn[g.group]].matrix_local.inverted()).to_3x3())*g.weight
  v.co+=Vector(np.linalg.solve(M,np.array(delta)))
 me.update();C.reset();tag=f'concave{round(factor*100)}';dest=P/f'work/lod3_{tag}.blend';tri=C.triangles(o);assert tri<=1220,tri;bpy.ops.wm.save_as_mainfile(filepath=str(dest));out=P/f'review/reduction/lod3_{tag}';render(dest,out,P/'work/reduction/lod3_continuous',88)
 v=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/'review/reduction/lod3_reference'),str(out)],text=True));rr=list(v['views'].values());uu=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rr];pooled=sum(x['iou']*u for x,u in zip(rr,uu))/sum(uu);rows.append({'factor':factor,'triangles':tri,'pooled_iou':pooled,'visual':v});(P/'review/reduction/concave_curve.json').write_text(json.dumps(rows,indent=2));print('CONCAVE',factor,tri,pooled,flush=True)
 if pooled>=.971:break
