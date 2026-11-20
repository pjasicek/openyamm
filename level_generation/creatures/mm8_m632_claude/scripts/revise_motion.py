"""Re-author motion and carry only the three revised actions into the verified UV master."""
import bpy,os,runpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
os.environ['M632_FAST_CHECK']='1'
for name in ('author_motion.py','finish_motion.py'):
    runpy.run_path(str(P/'scripts'/name),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
names=('Walking','Running','Attack')
for name in names:bpy.data.actions.remove(bpy.data.actions[name])
with bpy.data.libraries.load(str(P/'work/motion_timed.blend'),link=False) as (src,dst):
    dst.actions=list(names)
for a in dst.actions:a.use_fake_user=True
assert set(a.name for a in bpy.data.actions)=={'Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'}
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
