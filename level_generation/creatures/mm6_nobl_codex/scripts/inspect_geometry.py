import os,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];os.chdir(p);sys.path.insert(0,str(p/'scripts'))
def run(name,args):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('source_rest.py',['/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set/Armed.glb'])
run('proportions.py',['source','/home/pjasicek/github/OpenYAMM/anim_library/humanoid_set/Armed.glb'])
run('examine_parts.py',[p/'meshy/smart_topology_v2/model_urls_glb.glb','st_v1'])
