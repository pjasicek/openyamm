import runpy
from pathlib import Path
S=Path(__file__).resolve().parent
runpy.run_path(str(S/'check_export.py'),run_name='__main__')
import bpy
bpy.ops.wm.read_factory_settings(use_empty=True)
runpy.run_path(str(S/'build_lods.py'),run_name='__main__')
