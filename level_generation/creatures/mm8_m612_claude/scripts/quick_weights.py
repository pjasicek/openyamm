import os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
runpy.run_path(str(P/'scripts/author_gog.py'),run_name='__main__')
os.environ['INSPECT_BLEND']='animated_authored.blend'
os.environ['INSPECT_REPORT']='deformation_shoulders.json'
runpy.run_path(str(P/'scripts/inspect_animation.py'),run_name='__main__')
