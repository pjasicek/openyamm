from pathlib import Path
import runpy,shutil
p=Path(__file__).resolve().parent
runpy.run_path(str(p/'add_flames.py'),run_name='__main__')
shutil.copy2(p.parent/'work/flame_master.blend',p.parent/'work/textured_master.blend')
runpy.run_path(str(p/'export_phoenix.py'),run_name='__main__')
runpy.run_path(str(p/'retime_attack.py'),run_name='__main__')
