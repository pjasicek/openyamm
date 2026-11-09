"""Keep the good wing and mirror its measured anatomy; preserve the open native skeleton."""
import bpy,bmesh,json
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/import_v1.blend'))
o=next(o for o in bpy.data.objects if o.type=='MESH');o.name='BoneDragon'
bpy.context.view_layer.objects.active=o
for ob in bpy.context.scene.objects:ob.select_set(ob==o)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for v in o.data.vertices:v.co.x+=.105;v.co.z+=.341553
bm=bmesh.new();bm.from_mesh(o.data)
# The far wing was reconstructed in a different pose and lost membrane panels.
bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.co.x<-.065 and v.co.z>.307) or (v.co.x<-.12 and v.co.z>.26)],context='VERTS')
wing=[f for f in bm.faces if all((v.co.x>.063 and v.co.z>.305) or (v.co.x>.12 and v.co.z>.26) for v in f.verts)]
verts=set(v for f in wing for v in f.verts);edges=set(e for f in wing for e in f.edges)
r=bmesh.ops.duplicate(bm,geom=list(wing)+list(verts)+list(edges))
for v in r['geom']:
 if isinstance(v,bmesh.types.BMVert):v.co.x=-v.co.x
mirrored=[f for f in r['geom'] if isinstance(f,bmesh.types.BMFace)]
bmesh.ops.reverse_faces(bm,faces=mirrored)
# Merge only the mirrored wing's shoulder contact, not the anatomical rib gaps.
bmesh.ops.remove_doubles(bm,verts=[v for v in bm.verts if abs(abs(v.co.x)-.065)<.012 and .29<v.co.z<.33],dist=.001)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(o.data);bm.free();o.data.update()
for f in o.data.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/static_v1.blend'))
co=np.array([v.co[:] for v in o.data.vertices]);np.save(P/'work/static_coordinates.npy',co)
sc=bpy.context.scene;sc.render.resolution_x=1200;sc.render.resolution_y=1000
cam=sc.camera;cam.data.ortho_scale=1.3
for name,direction in [('front',(0,-1,0)),('side',(1,0,0)),('back',(0,1,0)),('quarter',(1,-1.5,.5))]:
 target=Vector((0,-.02,.28));cam.location=target+Vector(direction)*3;cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler()
 sc.render.filepath=str(P/'review'/f'static_{name}.png');bpy.ops.render.render(write_still=True)
print('GEOMETRY',len(o.data.vertices),sum(len(f.vertices)-2 for f in o.data.polygons))
