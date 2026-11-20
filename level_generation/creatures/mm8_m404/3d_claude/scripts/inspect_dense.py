"""Inspect returned geometry and source proportions without touching the original download."""
from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
src=p.parent/'meshy/multiview_geometry_v2/model_urls_pre_remeshed_glb.glb'
assert src.is_file()
for name,args in [('examine_parts.py',[str(src),'mv_v2_dense']),('source_rest.py',['anim_library/humanoid_set/2Hand Sword.glb']),('proportions.py',['source','anim_library/humanoid_set/2Hand Sword.glb'])]:
    sys.argv=[name,'--',*args]
    runpy.run_path(str(p/'scripts'/name),run_name='__main__')
assert (p/'work/mv_v2_dense_parts.blend').is_file()
