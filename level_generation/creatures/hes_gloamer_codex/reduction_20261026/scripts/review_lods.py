import os,sys,runpy
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.argv=['lod_render.py','--',str(R/'review/lods'),'hes_gloamer']
runpy.run_path(str(R.parent.parent/'lod_repair_claude/scripts/lod_render.py'),run_name='__main__')
sys.stdout.flush();sys.stderr.flush();os._exit(0)
