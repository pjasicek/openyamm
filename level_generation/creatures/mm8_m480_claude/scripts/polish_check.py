from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
for script in ('polish_motion.py','render_pilot.py','motion_probe.py','contacts.py'):runpy.run_path(str(p/script),run_name='__main__')
