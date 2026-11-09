import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['model_backface_split.py','--report',str(P/'review/backface_split.json'),str(P/'export/mm6_hrp.glb')]
runpy.run_path('tools/model_backface_split.py',run_name='__main__')
