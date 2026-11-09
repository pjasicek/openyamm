from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1]
sys.argv=['bake_ao.py','--',str(p/'work/rig_textured_uv.blend'),'1024']
runpy.run_path(str(p/'scripts/bake_ao.py'),run_name='__main__')
