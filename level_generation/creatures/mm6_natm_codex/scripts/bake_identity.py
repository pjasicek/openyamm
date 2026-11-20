import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as R,reduction_bake as B
bpy.ops.wm.open_mainfile(filepath=str(P/'work/authoring_high.blend'));R.reset();report={}
for name,kind in [('Body','body'),('SpearMesh','spear'),('BucklerMesh','buckler')]:
 o=bpy.data.objects[name];report[name]={'before':R.triangles(o),'protection':R.protect(o,kind)};R.reduce(o,1.,False);report[name]['after']=R.triangles(o)
 B.bake(o,P/f'work/reduction/lod0_identity/{kind}')
 for im in bpy.data.images:
  if im.source=='FILE'and im.has_data:im.pack()
 bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/reduced_baked_identity.blend'))
 print('BAKED_PROBE',name,report[name],flush=True)
(P/'review/reduction/probeidentity.json').write_text(json.dumps(report,indent=2))

import subprocess
subprocess.run(['/usr/bin/python3','-B',str(P/'scripts/tier_previews.py'),str(P/'work/reduction/lod0_identity')],check=True)
from reduction_render import render
render(P/'work/reduced_baked_identity.blend',P/'review/reduction/probeidentity',P/'work/reduction/lod0_identity')
