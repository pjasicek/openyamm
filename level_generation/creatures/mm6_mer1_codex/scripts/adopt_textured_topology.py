"""Adopt the exact returned triangle/UV topology, carrying the fitted skin by identical rest positions."""
import bpy,bmesh,json,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/texture_weighted.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();T=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);heads=np.isin(pv,[0,11,14,15]);bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();original=list(bm.verts)
for f in list(bm.faces):bm.faces.remove(f)
uv=bm.loops.layers.uv.get('UVMap')or bm.loops.layers.uv.new('UVMap');huv=bm.loops.layers.uv.get('HeadUV')or bm.loops.layers.uv.new('HeadUV');hf=bm.faces.layers.int.get('head')or bm.faces.layers.int.new('head');report={};added=set()
for layer,job,ishead in [('UVMap','body_retexture_v1',False),('HeadUV','head_retexture_v1',True)]:
 before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy'/job/'model_urls_glb.glb'));src=max((o for o in bpy.data.objects if o not in before and o.type=='MESH'),key=lambda o:len(o.data.polygons));S=np.array([tuple(src.matrix_world@v.co)for v in src.data.vertices]);ids=np.where(heads)[0]if ishead else np.arange(len(T));target=T[ids];scale=np.ptp(target,axis=0).max()/np.ptp(S,axis=0).max();S=S*scale+(target.max(0)+target.min(0))/2-(S.max(0)+S.min(0))/2*scale;tree=KDTree(len(ids))
 for i in ids:tree.insert(T[i],int(i))
 tree.balance();mapping=[];error=[]
 for p in S:
  _,j,d=tree.find(p);mapping.append(j);error.append(d)
 assert max(error)<1e-4,(layer,max(error));suv=src.data.uv_layers.active.data;count=0;duplicates=0
 for f in src.data.polygons:
  assert len(f.vertices)==3
  vi=[mapping[i]for i in f.vertices]
  if not ishead and all(heads[i]for i in vi):continue
  assert len(set(vi))==3,(layer,'collapsed triangle',vi)
  signature=tuple(sorted(vi))
  if signature in added:duplicates+=1;continue
  added.add(signature);nf=bm.faces.new([original[i]for i in vi]);nf[hf]=int(ishead);nf.smooth=True
  for lp,li in zip(nf.loops,f.loop_indices):lp[huv if ishead else uv].uv=suv[li].uv
  count+=1
 for o in list(bpy.data.objects):
  if o not in before:bpy.data.objects.remove(o,do_unlink=True)
 report[layer]={'vertex_position_max_mm':max(error)*1000,'triangles':count,'duplicate_triangles_removed':duplicates};print('TEXTURE TOPOLOGY',layer,report[layer],flush=True)
# Drop only orphaned elements left by the exact triangle replacement.
bmesh.ops.delete(bm,geom=[e for e in bm.edges if not e.link_faces],context='EDGES');bm.to_mesh(me);bm.free();me.uv_layers.active=me.uv_layers['UVMap'];(P/'review/texture_topology_handoff.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
