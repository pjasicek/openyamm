"""Remove sub-millimetre slivers left by the fingertip split before freezing topology."""
import bpy,bmesh,sys,numpy as np
src,out=sys.argv[sys.argv.index('--')+1:]
bpy.ops.wm.open_mainfile(filepath=src);o=bpy.data.objects['Body'];me=o.data
bm=bmesh.new();bm.from_mesh(me);pv=bm.verts.layers.int['piece'];dv=bm.verts.layers.deform.active
verts=[v for v in bm.verts if v[pv]==3];before=len(verts)
# Equal near-coincident weights prevent an arbitrary surviving point introducing a new skinning discontinuity.
for v in verts:
 near=[x for x in verts if (x.co-v.co).length<0.0008]
 if len(near)>1:
  keys=set(k for x in near for k in x[dv].keys());avg={k:sum(x[dv].get(k,0) for x in near)/len(near) for k in keys}
  for x in near:
   x[dv].clear()
   for k,w in avg.items():x[dv][k]=w
bmesh.ops.remove_doubles(bm,verts=verts,dist=0.0008)
bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-7)
bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
bm.to_mesh(me);bm.free();me.validate(verbose=True);assert not me.validate()
print('HAND CLEAN',before,'->',sum(a.value==3 for a in me.attributes['piece'].data))
bpy.ops.wm.save_as_mainfile(filepath=out)
