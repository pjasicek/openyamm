"""Refresh the assembled and packed authoring files after the texture-only export."""
from pathlib import Path
import bpy,runpy
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/thug_final.blend'))
images=[i for i in bpy.data.images if i.name.startswith('fgt_basecolor_1k')]
assert images,'Assembled master has no body colour image'
for image in images:
 if image.packed_file:image.unpack(method='REMOVE')
 image.filepath=str(p/'textures/fgt_basecolor_1k.png');image.reload()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/thug_final.blend'))
runpy.run_path(str(p/'scripts/pack_authoring.py'),run_name='__main__')
