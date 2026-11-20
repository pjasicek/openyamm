import bpy,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import round4_search as S
W=P/'work/round5'
bpy.ops.wm.open_mainfile(filepath=str(W/'ray_detail_trial/baked6/candidate.blend'));S.reset()
for name in ['Body','Axe']:
 me=bpy.data.objects[name].data;n=[x.vector[:]for x in me.corner_normals];me.normals_split_custom_set(n);me.update()
bpy.ops.wm.save_as_mainfile(filepath=str(W/'frozen.blend'))
r=runpy.run_path(str(P/'scripts/round5_render.py'),run_name='renderer');r['render'](W/'frozen.blend',P/'review/round5/frozen',W/'ray_detail_trial/baked6')
r['render'](W/'ray_detail_trial/baked6/candidate.blend',P/'review/round5/ray_pbr',W/'ray_detail_trial/baked6')
