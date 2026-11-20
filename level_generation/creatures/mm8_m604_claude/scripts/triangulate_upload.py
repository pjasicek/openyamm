"""Use the upload's exact triangles, preserving master vertices, weights, actions and per-corner head UVs."""
from pathlib import Path
import bpy,bmesh,sys,numpy as np
from mathutils.kdtree import KDTree
src,out=sys.argv[sys.argv.index('--')+1:];p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=src);body=bpy.data.objects['Body'];me=body.data
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(p/'texturing/m604_body_upload.glb'))
upload=next(o for o in set(bpy.data.objects)-before if o.type=='MESH')
kd=KDTree(len(me.vertices))
for v in me.vertices:kd.insert(body.matrix_world@v.co,v.index)
kd.balance();mapping=[];worst=0
for v in upload.data.vertices:
 _,i,d=kd.find(upload.matrix_world@v.co);mapping.append([j for _,j,dj in kd.find_range(upload.matrix_world@v.co,0.000001)]);worst=max(worst,d)
assert worst<0.00001,('upload position mismatch',worst)
oldfaces={f.index:set(f.vertices) for f in me.polygons}
incident={v.index:set() for v in me.vertices}
for f,verts in oldfaces.items():
 for v in verts:incident[v].add(f)
uvs={layer.name:{f.index:{v:tuple(layer.data[l].uv) for v,l in zip(f.vertices,f.loop_indices)} for f in me.polygons} for layer in me.uv_layers}
head=[x.value for x in me.attributes['head'].data];smooth=[f.use_smooth for f in me.polygons];materials=[f.material_index for f in me.polygons]
tris=[];dropped=0;duplicates=0;seen=set()
for f in upload.data.polygons:
 candidates=[mapping[v] for v in f.vertices];assert len(candidates)==3
 a,b,c=[upload.data.vertices[v].co for v in f.vertices]
 if (b-a).cross(c-a).length<1e-10:dropped+=1;continue
 owners=set.intersection(*(set.union(*(incident[v] for v in vs)) for vs in candidates))
 assert owners,('triangle has no source polygon',candidates)
 owner=min(owners);ids=[next(v for v in vs if v in oldfaces[owner]) for vs in candidates]
 assert len(set(ids))==3
 key=tuple(sorted(ids))
 if key in seen:duplicates+=1;continue
 seen.add(key);tris.append((ids,owner))
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();verts=list(bm.verts)
bmesh.ops.delete(bm,geom=list(bm.faces),context='FACES_ONLY')
hd=bm.faces.layers.int['head'];layers={n:bm.loops.layers.uv[n] for n in uvs}
for ids,owner in tris:
 f=bm.faces.new([verts[v] for v in ids]);f[hd]=head[owner];f.material_index=materials[owner];f.smooth=smooth[owner]
 for loop,v in zip(f.loops,ids):
  for n,l in layers.items():loop[l].uv=uvs[n][owner][v]
bm.to_mesh(me);bm.free();me.update()
for o in set(bpy.data.objects)-before:bpy.data.objects.remove(o,do_unlink=True)
assert len(me.polygons)==len(tris)
print('UPLOAD TRIANGLES',len(tris),'zero-area discarded',dropped,'coincident duplicate triangles discarded',duplicates,'maximum vertex mismatch mm',worst*1000)
bpy.ops.wm.save_as_mainfile(filepath=out)
