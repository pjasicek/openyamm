import bpy,sys,json,shutil,runpy,subprocess
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_rebake import bake
R=P/'review/round2';S=json.loads((R/'reduction/selected.json').read_text());fix=[]
for path in sorted(set(row['blend']for row in S['body'].values())):
 bpy.ops.wm.open_mainfile(filepath=str(P/path));ob=bpy.data.objects['Body']
 for layer in ob.data.uv_layers:
  for i,corner in enumerate(layer.data):
   for axis in range(2):
    value=corner.uv[axis]
    if value<0 or value>1:
     assert -.001<=value<=1.001,(layer.name,value)
     fixed=min(1,max(0,value));corner.uv[axis]=fixed;fix.append({'blend':path,'layer':layer.name,'corner':i,'axis':axis,'before':value,'after':fixed})
 bpy.ops.wm.save_as_mainfile(filepath=str(P/path))
(R/'uv_border_correction.json').write_text(json.dumps(fix,indent=2))
bake('body',P/S['body']['0']['blend'],P/'work/round2/baked_body')
for f in (P/'work/round2/baked_body').glob('*.png'):shutil.copy2(f,P/'textures'/f.name)
runpy.run_path(str(P/'scripts/round2_assemble.py'),run_name='__main__')
for name in ['round2_skin_gate.py','round2_pack_lods.py','pack_runtime.py','round2_tier_maps.py']:
 subprocess.run(['/usr/bin/python3',str(P/'scripts'/name)],check=True)
for name in ['round2_material_metrics.py','round2_endchecks.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
