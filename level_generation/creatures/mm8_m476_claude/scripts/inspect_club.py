import bpy,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).parent));import common
p=Path(__file__).resolve().parents[1]
common.clear_scene()
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/club_geometry_v1/model_urls_glb.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH']
co=np.array([tuple(o.matrix_world@v.co) for o in meshes for v in o.data.vertices]);lo=co.min(0);hi=co.max(0)
print('CLUB bounds',lo,hi,'tris',sum(len(o.data.polygons) for o in meshes))
(p/'work/club_bounds.json').write_text(json.dumps({'lo':lo.tolist(),'hi':hi.tolist()}))
scene=bpy.context.scene;common.workbench_clay(scene,True)
common.render_views(str(p/'review/club_raw'),float((lo[2]+hi[2])/2),float(max(hi-lo)*1.2),views=('front','three_quarter','left','back'),resolution=(800,600),target=tuple(((lo+hi)/2)[:2]))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/club_raw.blend'))
