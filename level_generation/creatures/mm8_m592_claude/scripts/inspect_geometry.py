"""Inspect the original Smart Topology return without changing it."""
from pathlib import Path
import runpy,sys
P=Path(__file__).resolve().parents[1]
R=P.parent/'mm6_ogr_claude/scripts'
sys.path.insert(0,str(R));import common
common.PROJECT=str(P);common.WORK=str(P/'work');common.REVIEW=str(P/'review/geometry')
script=R/'examine_parts.py'
sys.argv=[str(script),'--',str(P/'meshy/body_smart/model_urls_glb.glb'),'st_v1']
runpy.run_path(str(script),run_name='__main__')
