"""Fit every accepted LOD at its switch size; all tiers share the rebaked atlas."""
import bpy,sys,os,runpy,subprocess,json,shutil,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round3';R=P/'review/round3';sys.path.insert(0,str(P/'scripts'));import reduce_round2 as old;import pbr_round3 as pbr
old.R=R
os.environ['BAKE_INPUT']='body_s04.blend';os.environ['KEEP_ATLAS']='1'
runpy.run_path(str(P/'scripts/bake_round3.py'),run_name='__main__');subprocess.check_call(['/usr/bin/python3',str(P/'scripts/tier_maps_round3.py')])
curve=[];selected=[]
for lod,pixels in [(1,550),(2,220),(3,88)]:
 body,rig=old.reset(lod);old.render(body,rig,f'lod{lod}_silhouette_high',pixels);last=None
 for step in range(1,25):
  body,rig=old.reset(lod);prot=old.protect(body,rig,lod);n=old.reduce(body,.9**step,lod);body.data.validate(clean_customdata=False);n=sum(len(f.vertices)-2 for f in body.data.polygons);tag=f'lod{lod}_s{step:02d}';bpy.ops.wm.save_as_mainfile(filepath=str(W/f'{tag}.blend'));old.render(body,rig,tag,pixels)
  m=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_metrics_round2.py'),str(R),f'lod{lod}_silhouette_high',tag],text=True));row={'lod':lod,'step':step,'ratio':.9**step,'triangles':n,'projected_diameter_pixels':pixels,'min_iou':m['min_iou'],'silhouette_views':[v['iou']for v in m['views']],'silhouette_pass':m['min_iou']>=.99,'blend':f'work/round3/{tag}.blend','reference':f'work/round2/baseline_body_l{lod}.glb','reference_kind':'accepted unreduced matching LOD at its switch size'};curve.append(row);(R/'lod_curve.json').write_text(json.dumps(curve,indent=2));print('LOD CURVE',json.dumps(row),flush=True)
  if not row['silhouette_pass']:break
  last=row
 if last is None:
  body,rig=old.reset(lod);last={'lod':lod,'triangles':sum(len(f.vertices)-2 for f in body.data.polygons),'step':0,'ratio':1.,'min_iou':1.,'blend':f'work/round3/lod{lod}_unchanged.blend','reference':f'work/round2/baseline_body_l{lod}.glb'};bpy.ops.wm.save_as_mainfile(filepath=str(P/last['blend']))
 bpy.ops.wm.open_mainfile(filepath=str(P/last['blend']));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];rig.animation_data.action=None
 for pb in rig.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');body.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=body
 bpy.ops.wm.save_as_mainfile(filepath=str(W/f'rebaked_l{lod}.blend'));bpy.ops.export_scene.gltf(filepath=str(W/f'geometry_body_l{lod}.glb'),use_selection=True,export_format='GLB',export_animations=False,export_all_influences=True,export_attributes=False)
 selected.append(last);(R/'lod_selection.json').write_text(json.dumps(selected,indent=2))
# Material comparisons for all selected LODs and all three tier ramps.
for lod,pixels in [(0,700),(1,550),(2,220),(3,88)]:
 for tier in 'abc':
  for variant in ['high','low']:
   prefix=f'pbr_{variant}_{tier}'if lod==0 else f'lod{lod}_{variant}_{tier}'
   views=[i for i in range(8)if variant=='low'or not(R/f'{prefix}_{i}.png').exists()]
   if views:pbr.render(variant,tier,prefix,pixels,lod,views=views)
