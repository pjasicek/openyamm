import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/weapon_probe.py'),run_name='__main__')
sys.argv=['hands','--',str(P/'export/mm6_jak1_runtime_lod0.glb'),str(P/'review/contact'),'Attack:0.770833','Cast:0.895833','Death:1.395833']
runpy.run_path(str(P/'scripts/glb_hand_closeups.py'),run_name='__main__')
