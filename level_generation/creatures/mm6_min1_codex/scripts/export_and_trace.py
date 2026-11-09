import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';L=P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb'
runpy.run_path(str(S/'export_geometry.py'),run_name='__main__')
roles={'Standing':'Idle','Walking':'Walk','Running':'Walk','Attack':'Attack2','Cast':'Attack2','Hit':'GetHitF1','Death':'Death1','Fidget':'IdleAlert1'}
sys.argv=['trace_export.py','--',str(P/'work/geometry_review.glb'),*[f'{role}={L}:2HandAxe{clip}' for role,clip in roles.items()]];runpy.run_path(str(S/'trace_export.py'),run_name='__main__')
