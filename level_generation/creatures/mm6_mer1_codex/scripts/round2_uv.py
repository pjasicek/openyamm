import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for layer,src,job,out in [('UVMap','texture_upload_master','body_round2_texture_v2','body_uv'),('HeadUV','body_uv','head_round2_texture_v2','uv_master')]:
 sys.argv=['transfer_uv.py','--',str(P/f'work/round2/{src}.blend'),str(P/'meshy'/job),str(P/f'work/round2/{out}.blend'),layer]
 runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for layer in ['UVMap','HeadUV']:
 sys.argv=['uv_raster.py','--',str(P/'work/round2/uv_master.blend'),layer,'1024']
 code=(P/'scripts/uv_raster.py').read_text().replace("'work', f'uvraster_", "'work', 'round2', f'uvraster_")
 exec(compile(code,str(P/'scripts/uv_raster.py'),'exec'),{'__file__':str(P/'scripts/uv_raster.py'),'__name__':'__main__'})
