"""Inspect the Cleric geometry with the completed MM6 Ogre's isolated examination tools."""
from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
reference=p.parent/'mm6_ogr_claude/scripts'
sys.path.insert(0,str(reference))
import common
common.PROJECT=str(p);common.WORK=str(p/'work');common.REVIEW=str(p/'review/geometry')
script=reference/'examine_parts.py'
sys.argv=[str(script),'--',str(p/'meshy/body_smart/model_urls_glb.glb'),'st_v1']
runpy.run_path(str(script),run_name='__main__')
