"""Continue the final-motion reduction curve, then rebake the selected complete mesh."""
import bpy,sys,runpy,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_reduce_mesh as D
R=P/'review/round1/reduction';W=P/'work/reduction'
ctx=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]});render=ctx['render'];selection=json.loads((R/'final_selection.json').read_text());steps=[]
bpy.ops.wm.open_mainfile(filepath=str(W/'final_stop_body.blend' if selection['lod0_next_steps'][0]['pass'] else P/'work/production_master.blend'))
if selection['lod0_next_steps'][1]['pass']:
 old=bpy.data.objects['AxeMesh'];bpy.data.objects.remove(old,do_unlink=True)
 with bpy.data.libraries.load(str(W/'final_stop_axe.blend'),link=False) as (src,dst):dst.objects=['AxeMesh']
 ax=dst.objects[0];bpy.context.collection.objects.link(ax);ax.name='AxeMesh';ax.parent=bpy.data.objects['Rig']
 for mod in ax.modifiers:
  if mod.type=='ARMATURE':mod.object=bpy.data.objects['Rig']
best=W/'final_combined_start.blend';bpy.ops.wm.save_as_mainfile(filepath=str(best))
for name,ratio in [('Body',.90),('AxeMesh',.95)]:
 for step in range(12):
  bpy.ops.wm.open_mainfile(filepath=str(best));r=bpy.data.objects['Rig'];r.animation_data.action=None
  for pb in r.pose.bones:pb.matrix_basis.identity()
  bpy.context.view_layer.update();counts=D.reduce(bpy.data.objects[name],r,ratio,0,soft=True);dest=W/f'final_probe_{name}_{step}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=R/f'final_probe_{name}_{step}';folder.mkdir(exist_ok=True)
  runpy.run_path(str(P/'scripts/round1_rebake.py'),init_globals={'INPUT':str(dest.relative_to(P)),'OUTPUT':str(dest.relative_to(P)),'TEXTURES':str((folder/'textures').relative_to(P)),'REPORT':str((folder/'rebake.json').relative_to(P)),'ONLY':name})
  render(folder,name,0,directory=folder/'textures');subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(R/f'L0_{name}_reference'),str(folder),str(folder/'metrics.json')],check=True);v=json.loads((folder/'metrics.json').read_text());row={'object':name,**counts,'min_iou':v['min_iou'],'min_ssim':v['min_ssim'],'visual_pass':v['pass'],'blend':str(dest.relative_to(P))}
  if v['pass']:
   sys.argv=['g','--',str(dest.relative_to(P))];runpy.run_path(str(P/'scripts/rig_gates_48.py'));g=json.loads((P/'review/rig_gates.json').read_text());(folder/'rig_gates.json').write_text(json.dumps(g,indent=2))
   runpy.run_path(str(P/'scripts/round1_precision.py'),init_globals={'INPUT':str(dest.relative_to(P)),'REPORT':str((folder/'precision.json').relative_to(P))});pr=json.loads((folder/'precision.json').read_text());row['rig_pass']=all(all(x['pass'].values()) for x in g.values()) and all(x['pass'] for x in pr.values())
  row['pass']=row['visual_pass'] and row.get('rig_pass',False);steps.append(row);(R/'final_lod0_steps.json').write_text(json.dumps(steps,indent=2));print('FINAL DETAIL PROBE',row,flush=True)
  if not row['pass']:break
  best=dest
 else:raise AssertionError('Reduction has no measured stopping point')
bpy.ops.wm.open_mainfile(filepath=str(best));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_master.blend'))
runpy.run_path(str(P/'scripts/round1_rebake.py'),init_globals={'INPUT':'work/production_master.blend','OUTPUT':'work/production_master.blend'})
# The rebake is the authoritative final visual comparison for both reduced objects.
for name in ['Body','AxeMesh']:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/production_master.blend'));folder=R/f'final_{name}';render(folder,name,0,directory=P/'textures/round1_rebaked');subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(R/f'L0_{name}_reference'),str(folder),str(folder/'metrics.json')],check=True);assert json.loads((folder/'metrics.json').read_text())['pass']
print('FINAL REBAKE COMPLETE',flush=True)
