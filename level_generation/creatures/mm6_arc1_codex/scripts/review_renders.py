import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
runpy.run_path(str(P/'scripts/render_final.py'),run_name='__main__')
sys.argv=['glb_hand_closeups.py','--',str(P/'review/viewer/mm6_arc1_a.glb'),str(P/'review/hand'),'Standing:0','Attack:1.2','Cast:1.2','Death:0.7'];runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
