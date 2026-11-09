from pathlib import Path
import runpy,subprocess
p=Path(__file__).resolve().parents[1]
for name in ['review2_graft_head.py','review2_bake_head.py']:runpy.run_path(str(p/'scripts'/name),run_name='__main__')
subprocess.run(['python3',str(p/'scripts/review2_compose_head.py')],check=True)
