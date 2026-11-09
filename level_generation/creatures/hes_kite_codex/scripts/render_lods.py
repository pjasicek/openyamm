import sys,runpy,os,traceback
from pathlib import Path
try:runpy.run_path(str(Path(__file__).resolve().parents[2]/'lod_repair_claude/scripts/lod_render.py'),run_name='__main__')
except BaseException:traceback.print_exc();sys.stderr.flush();os._exit(1)
sys.stdout.flush();os._exit(0)
