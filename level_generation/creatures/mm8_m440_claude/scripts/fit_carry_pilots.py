from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
for n in ['build_pilots.py','preview_pilots.py']:
 sys.argv=[n,'--'];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
