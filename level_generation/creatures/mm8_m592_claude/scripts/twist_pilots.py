"""Use the playbook's soft-skin twist ramps for the Guardian's unarmoured arms."""
from pathlib import Path
import sys,os,runpy
P=Path(__file__).resolve().parents[1];tool=P.parent/'mm6_natm_claude/scripts/twist_bones.py';os.environ['FA']='0.6';os.environ['FA_RAMP']='0.15,0.85';sys.argv=[str(tool),'--',str(P/'work/pilots_authored.blend'),str(P/'work/pilots_fitted.blend')];runpy.run_path(str(tool),run_name='__main__')
