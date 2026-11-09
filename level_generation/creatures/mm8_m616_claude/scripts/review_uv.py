from pathlib import Path
import bpy,runpy,json
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/uv_master.blend'))
me=bpy.data.objects['BoneDragon'].data.copy()
changed=me.validate(verbose=True,clean_customdata=False)
print('MESH_VALIDATE_CHANGED',changed)
assert not changed
for name in ['review_checker.py','measure_scale.py']:runpy.run_path(str(P/'scripts'/name),run_name='__main__')
