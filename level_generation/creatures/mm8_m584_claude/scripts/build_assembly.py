from pathlib import Path
import runpy
P=Path(__file__).resolve().parent
for name in ('build_wings.py','assemble_rig.py'):runpy.run_path(str(P/name),run_name='__main__')
