import bpy,sys,runpy,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
sys.argv=['sync_actions.py','--',str(P/'work/rig_equipped.blend'),str(P/'work/round3/unreduced.blend')];runpy.run_path(str(P/'scripts/sync_actions.py'),run_name='__main__')
code=(P/'scripts/round2_assembled_metrics.py').read_text().replace('review/round2/reduction','review/round3/reduction').replace('for level in [1,2,3]','for level in [3]').replace("W/('unreduced.blend'if label=='high'else f'lod{level}.blend')","(P/'work/round3/unreduced.blend'if label=='high'else W/f'lod{level}.blend')")
exec(compile(code,str(P/'scripts/round2_assembled_metrics.py'),'exec'),{'__file__':str(P/'scripts/round2_assembled_metrics.py'),'__name__':'__main__'})
metrics=json.loads((P/'review/round3/reduction/assembled_distance_metrics.json').read_text());start=next(r['pooled_iou']for r in metrics['rows']if r['clip']=='Standing')
if start<.97:
 code=(P/'scripts/round3_far_bowfit.py').read_text().replace('work/round3/lod3_refined.blend','work/round2/lod3.blend').replace('work/round3/lod3_bowfit.blend','work/round3/lod3_final_fit.blend').replace('exact_bow_fit.json','final_bow_fit.json').replace("'initial_iou':.9683734939759037",f"'initial_iou':{start}")
 exec(compile(code,str(P/'scripts/round3_far_bowfit.py'),'exec'),{'__file__':str(P/'scripts/round3_far_bowfit.py'),'__name__':'__main__'})
 result=json.loads((P/'review/round3/reduction/final_bow_fit.json').read_text())
 if result['final_iou']>start:shutil.copy2(P/'work/round3/lod3_final_fit.blend',P/'work/round2/lod3.blend')
runpy.run_path(str(P/'scripts/round3_verify_render.py'),run_name='__main__')
