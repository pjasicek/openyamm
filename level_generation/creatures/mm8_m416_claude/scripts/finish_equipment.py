from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
s=P/'scripts/finish_master.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
s=P/'scripts/equipment_checks.py';sys.argv=[str(s)];runpy.run_path(str(s),run_name='__main__')
