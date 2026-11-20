"""Normalize the immutable Meshy return; inspect clay and connected stalk surfaces."""
from pathlib import Path
import bpy, bmesh, json, sys
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P.parent/'mm6_ooz_claude/scripts'))
import common
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/body_geometry_v1/model_urls_glb.glb'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in bpy.context.scene.objects: o.select_set(o in meshes)
bpy.context.view_layer.objects.active=meshes[0]
bpy.ops.object.join()
o=bpy.context.object; o.name='Nightmare'
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([v.co[:] for v in o.data.vertices]); lo=co.min(0); hi=co.max(0)
print('RAW BOUNDS',lo,hi)
# Normalize upright height to one metre; native scale is applied only in actors.yml.
co=(co-np.array([(lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]]))/(hi[2]-lo[2])
# The service widened the front to a cube and turned only the upper mouths toward the reference camera.
# Restore the native width/height ratio and face both upper pods along the lower mouth's forward axis.
for side,center in [(-1,(-.12,-.035)),(1,(.25,.015))]:
 ids=np.flatnonzero((co[:,2]>.74)&((co[:,0]<.07) if side<0 else (co[:,0]>=.07)))
 t=np.clip((co[ids,2]-.74)/.08,0,1);t=t*t*(3-2*t);a=np.radians(-32)*t
 x=co[ids,0]-center[0];y=co[ids,1]-center[1]
 co[ids,0]=center[0]+x*np.cos(a)-y*np.sin(a);co[ids,1]=center[1]+x*np.sin(a)+y*np.cos(a)
co[:,0]*=.70
for v,c in zip(o.data.vertices,co): v.co=c
bm=bmesh.new();bm.from_mesh(o.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
for f in o.data.polygons:f.use_smooth=True
co=np.array([v.co[:] for v in o.data.vertices]); np.savez_compressed(P/'work/geometry.npz',co=co,edges=np.array([e.vertices[:] for e in o.data.edges]),tri=np.array([f.vertices[:] for f in o.data.polygons]))
summary={'vertices':len(co),'triangles':len(o.data.polygons),'bounds':[co.min(0).tolist(),co.max(0).tolist()],'uv_layers':[u.name for u in o.data.uv_layers]}
(P/'work/geometry.json').write_text(json.dumps(summary,indent=2))
print(summary)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/geometry_v1.blend'))
sc=common.setup_render();common.workbench_clay(sc)
common.render_views(str(P/'review/clay_v1'),.5,1.35,views=('front','left','back','three_quarter'),resolution=(512,640))
