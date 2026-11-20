import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];L=P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb';M=P.parents[2]/'anim_library/mixamo/Great Sword Slash (2).fbx';roles={'Standing':'Idle','Walking':'Walk','Running':'Walk','Hit':'GetHitF1','Death':'Death1','Fidget':'IdleAlert1'}
sys.argv=['trace_export.py','--',str(P/globals().get('INPUT','export/mm6_min1_runtime_lod0.glb')),*[f'{r}={L}:2HandAxe{c}' for r,c in roles.items()],f'Attack={M}:Take',f'Cast={M}:Take'];runpy.run_path(str(P/'scripts/trace_export.py'),run_name='__main__')
