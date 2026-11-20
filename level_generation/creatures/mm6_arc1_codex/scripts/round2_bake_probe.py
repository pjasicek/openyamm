import sys,json,subprocess,bpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_rebake import bake
from round2_reduce import render
out=P/'work/round2/bake_probe';records=bake('body',P/'work/round2/body_l0_revised02.blend',out)
for file in out.glob('*.png'):shutil.copy2(file,P/'textures'/file.name)
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2/body_l0_revised02.blend'))
b=bpy.data.objects['Body'];r=bpy.data.objects['Rig']
render(b,r,'body',0,'body_l0_rebaked02')
value=json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/round2_reduction_metrics.py'),str(P/'review/round2/reduction'),'body_l0_revised00','body_l0_rebaked02'],text=True))
(P/'review/round2/rebake_probe.json').write_text(json.dumps({'maps':records,'metrics':value},indent=2));print('REBAKE_PROBE',value,flush=True)
