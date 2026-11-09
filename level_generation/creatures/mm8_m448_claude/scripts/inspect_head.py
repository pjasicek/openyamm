"""Inspect head-only geometry before selecting a transfer or graft."""
from pathlib import Path
import sys
import json
import bpy
import numpy as np
p = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_geometry_v1/model_urls_glb.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in meshes)
bpy.context.view_layer.objects.active=meshes[0]
if len(meshes)>1:bpy.ops.object.join()
o=bpy.context.view_layer.objects.active
o.parent=None
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
co=np.array([tuple(v.co) for v in o.data.vertices]);lo=co.min(0);hi=co.max(0)
print('HEAD BOUNDS',lo,hi,'verts',len(co),'triangles',sum(len(f.vertices)-2 for f in o.data.polygons))
for f in o.data.polygons:f.use_smooth=True
o.data.materials.clear()
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/head_return'),float((hi[2]+lo[2])/2),float(max(hi-lo)*1.15),
                    views=('front','three_quarter','left','back'),resolution=(700,700),target=(float((lo[0]+hi[0])/2),float((lo[1]+hi[1])/2)))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_return.blend'))
