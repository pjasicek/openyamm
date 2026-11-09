"""Import and inspect the untouched body generation in an isolated Blender scene."""
from pathlib import Path
import runpy
import sys
project=Path(__file__).resolve().parents[1]
for name,args in (
    ('examine_parts.py',[str(project/'meshy/smart_topology_v1/model_urls_glb.glb'),'st_v1']),
    ('source_rest.py',[str(project.parents[2]/'anim_library/humanoid_set/Armed.glb')]),
    ('proportions.py',['source',str(project.parents[2]/'anim_library/humanoid_set/Armed.glb')]),
):
    script=project/'scripts'/name
    sys.argv=[str(script),'--',*args]
    runpy.run_path(str(script),run_name='__main__')
