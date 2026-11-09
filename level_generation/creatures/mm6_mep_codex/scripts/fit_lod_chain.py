"""Recheck reduced meshes at every switch size and choose a monotone chain, avoiding pixel-quantisation reversals."""
import bpy,json,sys,subprocess
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import reduce_measured as rm
R=p/'review/reduction';curve=json.loads((R/'curve.json').read_text());sel=json.loads((R/'selected.json').read_text());cross=[]
for part in ['body','staff']:
 candidates=[r for r in curve if r['part']==part and r['pass']];candidates.sort(key=lambda r:r['triangles'])
 previous=-1
 for level in [3,2,1,0]:
  for i,row in enumerate(candidates):
   if row['triangles']<previous or (part=='body' and row['triangles']==previous):continue
   bpy.ops.wm.open_mainfile(filepath=str(p/row['blend']));ob=bpy.data.objects['Body' if part=='body' else 'StaffMesh'];rig=bpy.data.objects['Rig'];tag=f'chain_{part}_l{level}_c{i}'
   rm.render(ob,rig,part,level,tag)
   score=json.loads(subprocess.check_output(['/usr/bin/python3',str(p/'scripts/reduction_metrics.py'),str(R),f'{part}_l{level}_s00',tag],text=True))
   cross.append({'part':part,'level':level,'source':row['blend'],'triangles':row['triangles'],**score})
   if score['pass']:
    chosen=dict(row);chosen.update(score);chosen.update(lod=level,actor_height_pixels=[700,550,220,88][level],cross_check_tag=tag);sel[part][str(level)]=chosen;previous=row['triangles'];print('CHAIN',part,level,previous,score['min_iou'],score['min_ssim'],flush=True);break
  else:raise AssertionError((part,level,'no monotone passing candidate'))
(R/'chain_checks.json').write_text(json.dumps(cross,indent=2));(R/'selected.json').write_text(json.dumps(sel,indent=2))
