import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as R,reduction_bake as B
from reduction_render import render
curve=[]
for ratio in [.85,.825]:
 tag=f'lod0_{round(ratio*1000)}charts';tex=P/'work/reduction'/tag;dest=P/f'work/{tag}.blend';out=P/'review/reduction'/tag
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/authoring_high.blend'));R.reset();row={'ratio':ratio,'meshes':{}}
 for name,kind in [('Body','body'),('SpearMesh','spear'),('BucklerMesh','buckler')]:
  o=bpy.data.objects[name];prot=R.protect(o,kind);before=R.triangles(o);R.reduce(o,ratio if kind=='body'else .9,True);row['meshes'][kind]={'before':before,'triangles':R.triangles(o),'protection':prot};B.bake(o,tex/kind)
 bpy.ops.wm.save_as_mainfile(filepath=str(dest));subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True);render(dest,out,tex)
 visual=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/'review/reduction/reference700'),str(out)],text=True));row.update(blend=str(dest.relative_to(P)),textures=str(tex.relative_to(P)),visual=visual);curve.append(row);(P/'review/reduction/lod0_fine_curve.json').write_text(json.dumps(curve,indent=2));print('CURVE',ratio,row['meshes']['body']['triangles'],visual['min_iou'],visual['min_ssim'],visual['pass'],flush=True)
