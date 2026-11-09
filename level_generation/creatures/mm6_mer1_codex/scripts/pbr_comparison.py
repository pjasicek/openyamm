import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import search_reduction as R
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));R.C.cleanup();R.render(P/'review/reduction/pbr_probe/reference','body',0)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/reduction/body_lod0_3.blend'));R.C.cleanup();R.render(P/'review/reduction/pbr_probe/reduced','body',0,P/'work/reduction/body_lod0_3_textures')
r=R.metrics(P/'review/reduction/pbr_probe/reference',P/'review/reduction/pbr_probe/reduced');(P/'review/reduction/pbr_probe/metrics.json').write_text(json.dumps(r,indent=2));print('PBR COMPARISON',r['min_iou'],r['min_ssim'],r['pass'],flush=True)
