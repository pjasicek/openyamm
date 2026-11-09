import bpy,bmesh,json,sys
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(P/'meshy/head_geometry_v1/model_urls_glb.glb'))
mesh=next(o for o in bpy.data.objects if o.type=='MESH'); mesh.name='GargoyleHead'
bpy.context.view_layer.objects.active=mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
bm=bmesh.new(); bm.from_mesh(mesh.data); bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=1e-6); bm.to_mesh(mesh.data); bm.free()
co=np.array([v.co[:] for v in mesh.data.vertices]); co-=np.array([(co[:,0].min()+co[:,0].max())/2,(co[:,1].min()+co[:,1].max())/2,co[:,2].min()]); co/=np.ptp(co[:,2])
for v,c in zip(mesh.data.vertices,co): v.co=c
for poly in mesh.data.polygons: poly.use_smooth=True
if mesh.data.has_custom_normals: mesh.data.normals_split_custom_set([(0,0,0)]*len(mesh.data.loops))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/head_geometry_v1.blend'))
scene=bpy.context.scene; scene.world=bpy.data.worlds.new('HeadReview'); common.workbench_clay(scene)
common.render_views(str(P/'review/head_geometry_v1'),.5,1.2,views=('front','left','back','right','three_quarter'),resolution=(900,900))
(P/'work/head_geometry_inspection.json').write_text(json.dumps({'vertices':len(co),'triangles':sum(len(p.vertices)-2 for p in mesh.data.polygons),'bounds':[co.min(0).tolist(),co.max(0).tolist()]}))
print('HEAD_GEOMETRY',len(co),len(mesh.data.polygons),co.min(0),co.max(0))
