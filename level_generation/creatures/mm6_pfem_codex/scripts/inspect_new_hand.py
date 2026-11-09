import bpy,bmesh,sys,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/hand_model_v1/model_urls_glb.glb'))
o=next(o for o in bpy.data.objects if o.type=='MESH')
for a in bpy.data.objects:a.select_set(a==o)
bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in o.data.vertices]);lo,hi=co.min(0),co.max(0)
print('HAND source verts',len(co),'tris',sum(len(f.vertices)-2 for f in o.data.polygons),'bounds',lo,hi)
for f in o.data.polygons:f.use_smooth=True
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/hand_source'),float((hi[2]+lo[2])/2),float((hi[2]-lo[2])*1.1),views=('front','back','left'),resolution=(600,900),target=(float((hi[0]+lo[0])/2),float((hi[1]+lo[1])/2)))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/hand_source.blend'))
