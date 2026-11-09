"""Freeze corrected library actions and recheck reduction stops against the final motion."""
import bpy,sys,runpy,json,subprocess,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_reduce_mesh as D
R=P/'review/round1/reduction';W=P/'work/reduction'
ctx=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]});render=ctx['render']
def motion():
 r=bpy.data.objects['Rig'];r.animation_data.action=None
 for name in ['Attack','Cast']:bpy.data.actions.remove(bpy.data.actions[name])
 with bpy.data.libraries.load(str(P/'work/round1_timefit.blend'),link=False) as (src,dst):dst.actions=['Attack','Cast']
 for a in dst.actions:a.use_fake_user=True
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update()
def metric(ref,folder):
 subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(ref),str(folder),str(folder/'metrics.json')],check=True);return json.loads((folder/'metrics.json').read_text())
report={'lod0_next_steps':[],'distance_steps':[],'selected':[]}
for label,src in [('body','L0_soft_3.blend'),('axe','L0_AxeMesh_4.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(W/src));motion();dest=W/f'final_stop_{label}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));sys.argv=['gate','--',str(dest.relative_to(P))];runpy.run_path(str(P/'scripts/rig_gates_48.py'));g=json.loads((P/'review/rig_gates.json').read_text());shutil.copy2(P/'review/rig_gates.json',R/f'final_stop_{label}_gates.json');runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':str(dest.relative_to(P)),'REPORT':str((R/f'final_stop_{label}_precision.json').relative_to(P))});pr=json.loads((R/f'final_stop_{label}_precision.json').read_text());row={'object':label,'triangles':D.triangles(bpy.data.objects['Body' if label=='body' else 'AxeMesh']),'pass':all(all(x['pass'].values()) for x in g.values()) and all(x['pass'] for x in pr.values()),'failing_clips':[n for n,x in g.items() if not all(x['pass'].values())]+[n for n,x in pr.items() if not x['pass']]};report['lod0_next_steps'].append(row);print('FINAL STOP',row,flush=True)
for level,cap in [(1,(4813,1130)),(2,(2187,430))]:
 ref=R/f'final_L{level}_reference';bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_high.blend'));render(ref,'Combined',level);best=None
 for step in range(15):
  src=W/f'L{level}_measured_{step}.blend'
  if src.exists():bpy.ops.wm.open_mainfile(filepath=str(src))
  else:
   bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_baked.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
   for pb in r.pose.bones:pb.matrix_basis.identity()
   bpy.context.view_layer.update()
   for name,count in zip(['Body','AxeMesh'],cap):D.reduce(bpy.data.objects[name],r,int(count*.9**step)/D.triangles(bpy.data.objects[name]),level,soft=True)
  motion();dest=W/f'final_L{level}_{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=R/f'final_L{level}_{step}';render(folder,'Combined',level,directory=P/'textures/round1_rebaked');v=metric(ref,folder);row={'level':level,'step':step,'body_triangles':D.triangles(bpy.data.objects['Body']),'axe_triangles':D.triangles(bpy.data.objects['AxeMesh']),'pooled_iou':v['pooled_iou'],'min_ssim':v['min_ssim'],'pass':v['pooled_iou']>=.97,'blend':str(dest.relative_to(P))};report['distance_steps'].append(row);print('FINAL LOD',row,flush=True)
  (R/'final_selection.json').write_text(json.dumps(report,indent=2))
  if not row['pass']:break
  best=row
 assert best is not None
 bpy.ops.wm.open_mainfile(filepath=str(P/best['blend']));bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1_lod{level}.blend'));report['selected'].append(best)
# LOD3 has measured silhouette-fitted vertices; preserve that shape.
bpy.ops.wm.open_mainfile(filepath=str(W/'L3_raster_fit.blend'));motion();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_lod3.blend'));report['selected'].append({'level':3,'body_triangles':D.triangles(bpy.data.objects['Body']),'axe_triangles':D.triangles(bpy.data.objects['AxeMesh']),'blend':'work/round1_lod3.blend','pooled_iou':json.loads((R/'raster_fit.json').read_text())['pooled_iou']})
(P/'review/round1/reduction/final_selection.json').write_text(json.dumps(report,indent=2))
for level,file in [(0,'work/round1_baked.blend'),(-1,'work/round1_high.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/file));motion();bpy.ops.wm.save_as_mainfile(filepath=str(P/('work/production_master.blend' if level==0 else 'work/round1_high_final.blend')))
print('FINAL SELECTION',report,flush=True)
