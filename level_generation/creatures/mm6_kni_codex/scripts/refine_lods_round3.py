import bpy,sys,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import reduce_round2 as old;import pbr_round3 as pbr
old.R=R;curve=json.loads((R/'lod_curve.json').read_text());selection=json.loads((R/'lod_selection.json').read_text())
for lod,pixels in [(1,550),(2,220),(3,88)]:
 last=next(r for r in selection if r['lod']==lod);hi=last['ratio'];lo=max(r['ratio']for r in curve if r['lod']==lod and not r['silhouette_pass'])
 for j in range(3):
  ratio=(hi+lo)/2;body,rig=old.reset(lod);old.protect(body,rig,lod);old.reduce(body,ratio,lod);body.data.validate(clean_customdata=False);n=sum(len(f.vertices)-2 for f in body.data.polygons);tag=f'lod{lod}_refine{j}';bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));old.render(body,rig,tag,pixels)
  m=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),f'lod{lod}_silhouette_high',tag],text=True));row={'lod':lod,'step':f'bracket{j}','ratio':ratio,'triangles':n,'projected_diameter_pixels':pixels,'min_iou':m['min_iou'],'silhouette_views':[v['iou']for v in m['views']],'silhouette_pass':m['min_iou']>=.99,'blend':f'work/round3/{tag}.blend','reference':f'work/round2/baseline_body_l{lod}.glb','reference_kind':'accepted unreduced matching LOD at switch size'};curve.append(row);(R/'lod_curve.json').write_text(json.dumps(curve,indent=2));print('LOD REFINE',json.dumps(row),flush=True)
  if row['silhouette_pass']:hi=ratio;last=row
  else:lo=ratio
 bpy.ops.wm.open_mainfile(filepath=str(P/last['blend']));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.wm.save_as_mainfile(filepath=str(W/f'rebaked_l{lod}.blend'));bpy.ops.export_scene.gltf(filepath=str(W/f'geometry_body_l{lod}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_all_influences=True,export_attributes=False)
 selection[lod-1]=last;(R/'lod_selection.json').write_text(json.dumps(selection,indent=2))
for lod,pixels in [(0,700),(1,550),(2,220),(3,88)]:
 for tier in 'abc':
  for variant in ['high','low']:
   prefix=f'pbr_{variant}_{tier}'if lod==0 else f'lod{lod}_{variant}_{tier}'
   views=[i for i in range(8)if variant=='low'or not(R/f'{prefix}_{i}.png').exists()]
   if views:pbr.render(variant,tier,prefix,pixels,lod,views=views)
