from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1]
sys.argv=['retarget.py','--',str(P/'work/pilots_cloth_onehand_v1.blend'),str(P/'work/twohand_source.blend'),str(P.parents[2]/'anim_library/humanoid_set/2Hand Axe.glb')+':2HandAxeAttack1:AttackTwoHandSource'];runpy.run_path(str(P/'scripts/retarget.py'),run_name='__main__')
