from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parent
sys.argv=['gate_motion.py']
for script in ('motion_probe.py','contacts.py'):runpy.run_path(str(p/script),run_name='__main__')
