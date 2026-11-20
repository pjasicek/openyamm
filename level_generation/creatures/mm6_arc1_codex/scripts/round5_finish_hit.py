import runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/round5_hit_roll.py'),run_name='__main__')
subprocess.run(['/usr/bin/python3',str(P/'scripts/round5_refresh_animation.py')],check=True)
runpy.run_path(str(P/'scripts/round5_final_audit.py'),run_name='__main__')
