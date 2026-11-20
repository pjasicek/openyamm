from pathlib import Path
import runpy
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'fit_rig.py'),run_name='__main__')
runpy.run_path(str(p/'build_motion.py'),run_name='__main__')
