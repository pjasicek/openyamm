from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1];R=P.parents[2]
for n,args in [('examine_parts.py',[str(P/'meshy/smart_topology_v1/model_urls_glb.glb'),'st_v1']),('source_rest.py',[str(R/'anim_library/humanoid_set/2Hand Crossbow.glb')]),('proportions.py',['source',str(R/'anim_library/humanoid_set/2Hand Crossbow.glb')])]:
 f=P/'scripts'/n;sys.argv=[str(f),'--',*args];runpy.run_path(str(f),run_name='__main__')
