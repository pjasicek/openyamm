import bpy,sys,json,math,subprocess,shutil,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,reduction_bake as B
from reduction_render import render
rows=[]
for radius in [.0125,.013,.014,.015]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod3_edge88clip15.blend'));C.reset();r=bpy.data.objects['Rig'];o=bpy.data.objects['SpearMesh'];M=r.data.bones['Spear'].matrix_local;inv=M.inverted();changed=0
 for v in o.data.vertices:
  p=inv@v.co;rad=math.hypot(p.x,p.y)
  if abs(rad-.012)<.00001:p.x*=radius/rad;p.y*=radius/rad;v.co=M@p;changed+=1
 assert changed==16,changed
 tag=f'shaft{round(radius*10000)}';tex=P/f'work/reduction/lod3_{tag}';shutil.copytree(P/'work/reduction/lod3_continuous',tex,dirs_exist_ok=True);B.bake(o,tex/'spear');subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(tex)],check=True);dest=P/f'work/lod3_{tag}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));out=P/f'review/reduction/lod3_{tag}';render(dest,out,tex,88)
 d=json.loads(subprocess.check_output(['/usr/bin/python3','-B',str(P/'scripts/reduction_metrics.py'),str(P/'review/reduction/lod3_reference'),str(out)],text=True));rr=list(d['views'].values());uu=[(x['reference_pixels']+x['candidate_pixels'])/(1+x['iou'])for x in rr];pooled=sum(x['iou']*u for x,u in zip(rr,uu))/sum(uu);rows.append({'radius':radius,'blend':str(dest.relative_to(P)),'textures':str(tex.relative_to(P)),'pooled_iou':pooled,'visual':d});(P/'review/reduction/shaft_curve.json').write_text(json.dumps(rows,indent=2));print('SHAFT',radius,pooled,flush=True)
 if pooled>=.9705:break
