import bpy,sys,json,subprocess,shutil,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));from round2_reduce import render
D=P/'review/round2/reduction';W=P/'work/round2';bpy.ops.wm.open_mainfile(filepath=str(W/'body_l3_factor0.blend'));ob=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];data=json.loads((W/'fit_output.json').read_text())
for v,co in zip(ob.data.vertices,data['rest']):v.co=co
path=W/'body_l3_fitted.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));render(ob,rig,'body',3,'body_l3_fitted',P/'work/round2/metric_tiers/baked/arc1_a')
result=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(D),'body_l3_arc1_a_high','body_l3_fitted'],text=True));(D/'distance_fit_metrics.json').write_text(json.dumps(result,indent=2));print('FITTED_RENDER',result['pooled_iou'],flush=True)
# Inspect the constrained candidate before selecting any runtime replacement.
shutil.copy2(path,P/'work/rig_equipped.blend')
for name in ['round2_gates.py','round2_contact_gates.py']:
 try:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
 except Exception as e:print('FITTED_GATE',name,type(e).__name__,str(e),flush=True)
shutil.copy2(W/'lod0.blend',P/'work/rig_equipped.blend')
