import bpy,sys,numpy as np,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(p/'meshy/head_geometry_v3/model_urls_glb.glb'))
meshes=[o for o in bpy.data.objects if o.type=='MESH'];co=np.array([(o.matrix_world@v.co)[:] for o in meshes for v in o.data.vertices]);lo=co.min(0);hi=co.max(0);print('SOURCE_BOUNDS',lo.tolist(),hi.tolist());print('SOURCE_MESHES',[(o.name,len(o.data.vertices),len(o.data.polygons)) for o in meshes])
(p/'work/head_v3_bounds.json').write_text(json.dumps({'min':lo.tolist(),'max':hi.tolist()}))
common.setup_render();common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/head_source_v3'),(lo[2]+hi[2])/2,(hi[2]-lo[2])*1.1,views=('front','three_quarter','left','back'),resolution=(768,768),target=((lo[0]+hi[0])/2,(lo[1]+hi[1])/2))
