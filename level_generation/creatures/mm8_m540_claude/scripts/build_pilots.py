from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parent
for name in ['retarget_pilots.py','assemble_wand.py','author_pilots.py']:
 sys.argv=[str(p/name)]
 runpy.run_path(str(p/name),run_name='__main__')
