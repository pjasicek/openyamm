from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parent
for name in ['fit_body_weights.py','join_head.py','retarget_pilots.py','assemble_wand.py']:
 sys.argv=[str(p/name)]
 runpy.run_path(str(p/name),run_name='__main__')
