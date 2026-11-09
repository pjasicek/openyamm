import bpy,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('export_parity.py')
run('stride.py',P/'work/master_settled.blend','Walking','Running')
rig=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);ob=bpy.data.objects['Body'];ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=[(ob.matrix_world@v.co).z for v in me.vertices];ev.to_mesh_clear()
height=max(z)-min(z);(P/'work/scale.json').write_text(json.dumps({'standing_body_height_m':height,'native_body_height_px':190,'scale':190/height},indent=2));print('SCALE',190/height,height)
bpy.ops.wm.read_factory_settings(use_empty=True);sys.path.insert(0,str(R/'tools'));import build_actor_lods
build_actor_lods.generate(P/'export/mm8_m656_prepared.glb',P/'export/mm8_m656_lods_raw.glb','Mercenary',ratios=(.5,.25,.125),max_influences=4)
