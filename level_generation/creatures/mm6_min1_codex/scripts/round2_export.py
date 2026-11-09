import bpy,runpy,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]
shutil.copy2(P/'work/round2_candidate.blend',P/'work/production_master.blend')
for level in [1,2,3]:
 file=P/f'work/round1_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(file));r=bpy.data.objects['Rig'];r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 with bpy.data.libraries.load(str(P/'work/production_master.blend'),link=False) as (src,dst):dst.actions=src.actions
 for a in dst.actions:a.use_fake_user=True
 bpy.context.scene.render.fps=240;bpy.ops.wm.save_as_mainfile(filepath=str(file))
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__')
