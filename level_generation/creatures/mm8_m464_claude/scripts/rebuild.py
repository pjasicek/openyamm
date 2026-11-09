import runpy,subprocess
from pathlib import Path
P=Path(__file__).parent
for name in ['adapt_motion.py','repair_weights.py','export_model.py']:runpy.run_path(str(P/name),run_name='__main__')
for name in ['finish_runtime.py','validate_arm_fit.py']:
 subprocess.run(['/usr/bin/python3',str(P/name)],check=True)
runpy.run_path(str(P/'shared_gates.py'),run_name='__main__')
