import bpy,sys,runpy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_reduce_mesh as D
ctx=runpy.run_path(str(P/'scripts/round1_reduction_curve.py'),init_globals={'LEVELS':[]});render=ctx['render'];R=P/'review/round1/reduction';curve=json.loads((R/'curve.json').read_text());trials=[]
for factor in [0,2,10,100]:
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_high.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();D.LOD_FACTOR=factor;counts={}
 for n,c in [('Body',739),('AxeMesh',135)]:counts[n]=D.reduce(bpy.data.objects[n],r,c/D.triangles(bpy.data.objects[n]),3,soft=True)
 dest=P/f'work/reduction/L3_direct_{factor}.blend';bpy.ops.wm.save_as_mainfile(filepath=str(dest));folder=R/f'L3_direct_{factor}';render(folder,'Combined',3,directory=P/'textures/round1_rebaked')
 import subprocess
 subprocess.run(['/usr/bin/python3',str(P/'scripts/round1_reduce_metric.py'),str(R/'L3_combined_reference'),str(folder),str(folder/'metrics.json')],check=True);v=json.loads((folder/'metrics.json').read_text());e={'level':3,'method':'silhouette-prioritized distant mesh','factor':factor,'body_triangles':counts['Body']['after'],'axe_triangles':counts['AxeMesh']['after'],'pooled_iou':v['pooled_iou'],'min_iou':v['min_iou'],'min_ssim':v['min_ssim'],'pass':v['pooled_iou']>=.97,'blend':str(dest.relative_to(P))};trials.append(e);print('COARSE',e,flush=True)
(R/'direct_trials.json').write_text(json.dumps(trials,indent=2))
