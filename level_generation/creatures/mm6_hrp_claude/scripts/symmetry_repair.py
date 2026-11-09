"""Rebuild the fused right wing/arm from the clean left anatomy, preserving digit topology."""
import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/anatomy.blend'));o=bpy.data.objects['Body'];me=o.data
bm=bmesh.new();bm.from_mesh(me);layer=bm.verts.layers.int['part']
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=.00001,plane_co=(-.01,0,0),plane_no=(1,0,0),clear_inner=True)
res=bmesh.ops.duplicate(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces));vs=[x for x in res['geom'] if isinstance(x,bmesh.types.BMVert)];fs=[x for x in res['geom'] if isinstance(x,bmesh.types.BMFace)]
for v in vs:
 v.co.x=-.02-v.co.x;v[layer]={1:10,2:5,3:6,4:7,8:9}.get(v[layer],v[layer])
bmesh.ops.reverse_faces(bm,faces=fs)
seam=[v for v in bm.verts if abs(v.co.x+.01)<.00002]
bmesh.ops.remove_doubles(bm,verts=seam,dist=.00003);bmesh.ops.triangulate(bm,faces=list(bm.faces));bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
co=np.array([v.co[:] for v in me.vertices]);pa=np.array([v.value for v in me.attributes['part'].data]);wing=np.isin(pa,[1,10]);np.save(P/'work/wing_mask.npy',wing)
assert wing.sum()>2200
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/anatomy_symmetric.blend'));print('SYMMETRY',len(co),len(me.polygons),flush=True)
(P/'work/symmetry_repair.json').write_text(json.dumps({'reason':'Meshy right wing fused into upper arm; mirror the separate left wing and intact left body surface','triangles':len(me.polygons),'vertices':len(co)},indent=2))
