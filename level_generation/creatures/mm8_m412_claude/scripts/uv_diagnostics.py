import runpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.argv=['transfer_uv_diagnostic.py','--',str(p/'work/master_uv_upload.blend'),str(p/'meshy/body_retexture_v1'),str(p/'work/diagnostic_do_not_save.blend')]
runpy.run_path(str(p/'scripts/transfer_uv_diagnostic.py'),run_name='__main__')
