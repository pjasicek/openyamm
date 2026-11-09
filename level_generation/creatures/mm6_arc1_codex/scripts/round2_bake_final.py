import sys,json,shutil,bpy,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
from round2_reduce import *
from round2_rebake import bake
S=json.loads((R/'selected.json').read_text())
ob,rig=reset('body');count,protection=reduce(ob,rig,'body',3,.95);path=W/'body_l3_revised_half.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
S['body']['3']={**S['body']['3'],'ratio':.95,'triangles':count,'blend':str(path.relative_to(P)),'rig_gates':'pending'}
(R/'selected.json').write_text(json.dumps(S,indent=2))
# Restore the unreduced maps so every bake has a stable source and live material defaults.
for file in (W/'high_textures').glob('*.png'):shutil.copy2(file,P/'textures'/file.name)
records=bake('body',P/S['body']['0']['blend'],W/'baked_body')
for file in (W/'baked_body').glob('*.png'):shutil.copy2(file,P/'textures'/file.name)
runpy.run_path(str(P/'scripts/round2_assemble.py'),run_name='__main__')
records+=bake('bow',W/'lod0.blend',W/'baked_bow')
for file in (W/'baked_bow').glob('*.png'):shutil.copy2(file,P/'textures/bow'/file.name)
(R/'rebake.json').write_text(json.dumps({'method':'Cycles selected-to-active, CPU four threads; retained UV layout reprojected from unreduced reference; lower LODs reuse the same baked surface maps and are independently validated','maps':records},indent=2))
for name in ['round2_gates.py','round2_contact_gates.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
