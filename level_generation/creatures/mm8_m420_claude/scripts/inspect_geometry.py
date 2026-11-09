from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
sys.argv=['examine_parts.py','--',str(p/'meshy/body_geometry_v1/model_urls_glb.glb'),'st_v1']
runpy.run_path(str(p/'scripts/examine_parts.py'),run_name='__main__')
sys.argv=['source_rest.py','--',str(repo/'anim_library/humanoid_set/Armed.glb')]
runpy.run_path(str(p/'scripts/source_rest.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/preview_mixamo.py'),run_name='__main__')
