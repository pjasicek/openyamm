from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
s=p/'scripts/glb_hand_closeups.py';sys.argv=[str(s),'--',str(p/'export/mm6_ogr_runtime_lod0.glb'),str(p/'review/textured_hands'),'Standing:0','Attack:0.683','Fidget:0.367','Dead:0'];runpy.run_path(str(s),run_name='__main__')
