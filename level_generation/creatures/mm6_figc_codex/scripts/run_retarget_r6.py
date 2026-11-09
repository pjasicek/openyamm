"""Reuse the project Mixamo retargeter with its recorded source frames."""
import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];W=P/'work/round6'
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_motion.blend'))
source=json.loads((P/'work/source_rest.json').read_text());rig=bpy.data.objects['Rig']
bpy.context.scene['rig_offsets']=json.dumps({b.name:{'R_src':source[b.name]['rot'] if b.name in source else [list(r)for r in b.matrix_local.to_3x3()]}for b in rig.data.bones})
bpy.ops.wm.save_as_mainfile(filepath=str(W/'retarget_input.blend'))
sys.argv=['retarget','--',str(W/'retarget_input.blend'),str(W/'run_source.blend'),'anim_library/mixamo/Standard Run.fbx:RunSource:turn']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
