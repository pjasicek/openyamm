import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
code=(P/'scripts/round2_assembled_metrics.py').read_text().replace('review/round2/reduction','review/round3/reduction/selected').replace('for level in [1,2,3]','for level in [3]').replace("W/('unreduced.blend'if label=='high'else f'lod{level}.blend')","(P/'work/round3/unreduced.blend'if label=='high'else P/'work/round3/lod3_bowfit.blend')")
exec(compile(code,str(P/'scripts/round2_assembled_metrics.py'),'exec'),{'__file__':str(P/'scripts/round2_assembled_metrics.py'),'__name__':'__main__'})
code=(P/'scripts/round3_lod_gates.py').read_text().replace('for level in [0,1,2,3]','for level in [3]').replace("P/f'work/round2/lod{level}.blend'","P/'work/round3/lod3_bowfit.blend'").replace("out=P/f'review/round3/lod_gates/lod{level}'","out=P/'review/round3/lod_gates/lod3'")
exec(compile(code,str(P/'scripts/round3_lod_gates.py'),'exec'),{'__file__':str(P/'scripts/round3_lod_gates.py'),'__name__':'__main__'})

import json,shutil,bpy
assert json.loads((P/'review/round3/lod_gates/lod3/status.json').read_text())['pass']
D=P/'review/round3/reduction';new=json.loads((D/'selected/assembled_distance_metrics.json').read_text());assert not new['failures'];old=json.loads((D/'assembled_distance_metrics.json').read_text());old['rows']=[r for r in old['rows']if r['lod']!=3]+new['rows'];old['failures']=[];(D/'assembled_distance_metrics.json').write_text(json.dumps(old,indent=2))
shutil.copy2(P/'work/round2/lod3.blend',P/'work/round3/lod3_before_fit.blend');shutil.copy2(P/'work/round3/lod3_bowfit.blend',P/'work/round2/lod3.blend')
runpy.run_path(str(P/'scripts/round3_export.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_authoring.blend'));bpy.ops.file.pack_all();bpy.ops.wm.save_mainfile()
for name in ['round2_head_probe.py','round3_native_probe.py','round3_shared_compare.py']:
 code=(P/'scripts'/name).read_text().replace('review/round2/','review/round3/');exec(compile(code,str(P/'scripts'/name),'exec'),{'__file__':str(P/'scripts'/name),'__name__':'__main__'})
