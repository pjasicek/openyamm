import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
for level in range(4):
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/selected_lod{level}_polished.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];k=bpy.data.objects['KnifeAsset'];sc=bpy.context.scene
 bm=bmesh.new();bm.from_mesh(b.data);pv=bm.verts.layers.int['piece'];edges=[e for e in bm.edges if e.is_boundary and all(v[pv]==5 and .9<v.co.z<1.1 for v in e.verts)]
 if edges:
  ordered=[edges[0].verts[0]];remaining=set(edges)
  while remaining:
   edge=next(e for e in remaining if ordered[-1] in e.verts);remaining.remove(edge);v=edge.other_vert(ordered[-1])
   if v==ordered[0]:break
   ordered.append(v)
  assert not remaining
  face=bm.faces.new(ordered);faces=bmesh.ops.triangulate(bm,faces=[face])['faces'];uv=bm.loops.layers.uv['UVMap']
  # Reserve a 32-pixel patch plus 16-pixel margins in a new 64-pixel strip; never overlap occupied islands.
  if level==0:
   patch_co=np.array([[v.co.x,v.co.z] for v in ordered]);patch_lo=patch_co.min(0);patch_span=np.maximum(patch_co.max(0)-patch_lo,1e-6)
  newfaces=set(faces)
  for face in faces:
   face.material_index=0;face.smooth=True
   for loop in face.loops:
    q=(np.array([loop.vert.co.x,loop.vert.co.z])-patch_lo)/patch_span
    loop[uv].uv=((1040+q[0]*32)/1024,(496+q[1]*32)/1024)
   adjacent=[f for e in face.edges for f in e.link_faces if f not in newfaces]
   if adjacent and face.normal.dot(sum((f.normal for f in adjacent),adjacent[0].normal.copy()*0))<0:face.normal_flip()
  print('CLOSED_FOREARM',level,len(edges),len(faces),flush=True)
 uv=bm.loops.layers.uv['UVMap']
 for face in bm.faces:
  if face.material_index==0:
   for loop in face.loops:loop[uv].uv.x*=1024/1088
 bm.to_mesh(b.data);bm.free();bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1/source_lod{level}.blend'))
 r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();me=b.data;me.calc_loop_triangles();gn=[g.name for g in b.vertex_groups];W=np.zeros((len(me.vertices),len(gn)))
 for v in me.vertices:
  for g in v.groups:W[v.index,g.group]=g.weight
 np.savez_compressed(P/f'work/round1/mesh{level}.npz',co=np.array([v.co[:] for v in me.vertices]),normals=np.array([v.normal[:] for v in me.vertices]),tri=np.array([t.vertices[:] for t in me.loop_triangles]),uv=np.array([[me.uv_layers['UVMap'].data[i].uv[:] for i in t.loops]for t in me.loop_triangles]),mat=np.array([t.material_index for t in me.loop_triangles]),piece=np.array([v.value for v in me.attributes['piece'].data]),weights=W,names=np.array(gn))
