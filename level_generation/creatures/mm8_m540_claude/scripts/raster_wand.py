from pathlib import Path
import sys,runpy,bpy,json
p=Path(__file__).resolve().parents[1];s=p/'scripts/uv_raster.py'
sys.argv=[str(s),'--',str(p/'work/rig_uv.blend'),'UVMap','512','Wand'];runpy.run_path(str(s),run_name='__main__')
rig=bpy.data.objects['Rig']
(p/'work/wand_region.json').write_text(json.dumps({'orb_centre':list(rig.data.bones['Socket_WandOrb'].head_local),'orb_radius':.065},indent=2)+'\n')
