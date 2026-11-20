import runpy,sys,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
runpy.run_path(str(P/'scripts/round2_motion.py'),run_name='__main__')
shutil.copy2(P/'work/rig_textured.blend',P/'work/round2/unreduced.blend')
runpy.run_path(str(P/'scripts/round2_assemble.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round2_lod_gates.py'),run_name='__main__')
