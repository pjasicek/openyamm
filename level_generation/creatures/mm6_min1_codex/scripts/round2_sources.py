import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round2_baseline.blend'))
r=bpy.data.objects['Rig'];sf=json.loads((P/'work/source_rest.json').read_text());bpy.context.scene['rig_offsets']=json.dumps({n:{'R_src':sf[n]['rot'] if n in sf else [list(row) for row in b.matrix_local.to_3x3()]} for n,b in r.data.bones.items()})
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round2_source_base.blend'))
items=[str(R/'anim_library/mixamo'/file)+':'+name for file,name in [('Falling Back Death.fbx','FallBack'),('Dying.fbx','DyingSource'),('Two Handed Sword Death.fbx','SwordDeath')]]
sys.argv=['retarget','--',str(P/'work/round2_source_base.blend'),str(P/'work/round2_sources.blend')]+items
runpy.run_path(str(R/'level_generation/creatures/mm6_bar1_claude/scripts/retarget_mixamo.py'),run_name='__main__')
