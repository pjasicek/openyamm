from pathlib import Path
import runpy
p=Path(__file__).resolve().parents[1]
for s in ('club_clear_full.py','export_full.py'):runpy.run_path(str(p/'scripts'/s),run_name='__main__')
