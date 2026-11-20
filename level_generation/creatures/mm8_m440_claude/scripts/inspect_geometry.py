"""Inspect source Smart Topology geometry without modifying the download."""
from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for name,args in [('proportions.py',['source',str(p.parents[2]/'anim_library/humanoid_set/Relax.glb')]),
                  ('source_rest.py',[str(p.parents[2]/'anim_library/humanoid_set/1Hand.glb')]),
                  ('examine_parts.py',[str(p/'meshy/smart_topology_v1/model_urls_glb.glb'),'st_v1'])]:
    sys.argv=[name,'--',*args]
    runpy.run_path(str(p/'scripts'/name),run_name='__main__')
