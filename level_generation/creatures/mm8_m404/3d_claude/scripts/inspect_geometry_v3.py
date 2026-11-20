"""Inspect returned geometry and source proportions without touching the original download."""
from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
src=p.parent/'meshy/front_geometry_v3/model_urls_glb.glb'
assert src.is_file()
for name,args in [('examine_parts.py',[str(src),'front_v3']),('source_rest.py',['anim_library/humanoid_set/2Hand Sword.glb']),('proportions.py',['source','anim_library/humanoid_set/2Hand Sword.glb'])]:
    sys.argv=[name,'--',*args]
    runpy.run_path(str(p/'scripts'/name),run_name='__main__')
assert (p/'work/front_v3_parts.blend').is_file()

import bpy,math
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/sword.blend'))
o=bpy.data.objects['SwordMesh'];o.rotation_euler[0]=math.pi/2
bpy.context.view_layer.update()
common.workbench_clay(bpy.context.scene,textured=True)
common.render_views(str(p/'review/sword'),.53,1.9,views=('front','three_quarter','left'),resolution=(600,900))
