import bpy,sys,runpy,shutil,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
runpy.run_path(str(P/'scripts/round3_export.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round3_lod_gates.py'),run_name='__main__')
for name in ['round2_head_probe.py','uv_gate_run.py','release_gate.py','export_trace_run.py','round2_export_gates.py','final_review.py']:
 code=(P/'scripts'/name).read_text().replace('review/round2/','review/round3/')
 if name=='round2_export_gates.py':code=code.replace("views=('front',),resolution=(680,1000)","views=('front','left'),resolution=(680,1000)")
 exec(compile(code,str(P/'scripts'/name),'exec'),{'__file__':str(P/'scripts'/name),'__name__':'__main__'})
sys.argv=['sync_actions.py','--',str(P/'work/rig_equipped.blend'),str(P/'work/round3/unreduced.blend')];runpy.run_path(str(P/'scripts/sync_actions.py'),run_name='__main__')
code=(P/'scripts/round2_assembled_metrics.py').read_text().replace('review/round2/reduction','review/round3/reduction').replace("W/('unreduced.blend'if label=='high'else f'lod{level}.blend')","(P/'work/round3/unreduced.blend'if label=='high'else W/f'lod{level}.blend')")
exec(compile(code,str(P/'scripts/round2_assembled_metrics.py'),'exec'),{'__file__':str(P/'scripts/round2_assembled_metrics.py'),'__name__':'__main__'})

for name in ['round3_native_probe.py','round3_shared_compare.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
