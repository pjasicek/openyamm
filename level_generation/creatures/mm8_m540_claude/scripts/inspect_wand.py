"""Inspect the generated rigid wand before assembly."""
from pathlib import Path
import bpy,sys,numpy as np,json
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/wand_v1/model_urls_glb.glb'))
objects=[o for o in bpy.data.objects if o.type=='MESH']
co=np.array([tuple(o.matrix_world@v.co) for o in objects for v in o.data.vertices]);lo=co.min(0);hi=co.max(0)
common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/geometry/wand'),float((hi[2]+lo[2])/2),float((hi-lo).max()*1.2),views=('front','left','back','three_quarter'),resolution=(500,700))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/wand_original.blend'))
print('WAND',lo.tolist(),hi.tolist(),sum(len(f.vertices)-2 for o in objects for f in o.data.polygons))
