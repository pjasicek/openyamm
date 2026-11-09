import bpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'));import common
out=P/'review/texture_uploads';out.mkdir(exist_ok=True)
for kind in ('head','body'):
 bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(P/f'texturing/gog_{kind}_upload.glb'))
 obs=[o for o in bpy.data.objects if o.type=='MESH']
 bpy.context.view_layer.update();lo,hi=common.world_bounds(obs)
 common.workbench_clay(bpy.context.scene)
 common.render_views(str(out/kind),(lo.z+hi.z)/2,max(hi.z-lo.z,hi.x-lo.x,hi.y-lo.y)*1.2,views=('front','left','back'),resolution=(512,512),target=((lo.x+hi.x)/2,(lo.y+hi.y)/2))
