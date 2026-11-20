"""Restore the source pair's width after separating touching feet; retain the repaired deep shafts."""
import json,sys
from pathlib import Path
import bpy
P=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(P/'scripts'))
import codex_texture as texture
name='equipment_6boots5'
bpy.ops.wm.open_mainfile(filepath=str(P/f'work/codex_tex/{name}.blend'))
obj=bpy.data.objects[name]
source=json.loads((P/'receipts/scene_audit.json').read_text())['6boots5']['bounds']
width=max(v.co.x for v in obj.data.vertices)-min(v.co.x for v in obj.data.vertices)
target=source[1][0]-source[0][0]
assert 1<width/target<1.15,(width,target)
for vertex in obj.data.vertices:vertex.co.x*=target/width
bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/codex_tex/{name}.blend'))
(P/'receipts/shared_boot_proportions.json').write_text(json.dumps({'reason':'Separating touching feet added 0.09 to pair width. Restore the authoritative source width while preserving source foot depth and shaft height, retaining positive separation and deep lining.','previous_width':width,'source_width':target,'x_scale':target/width},indent=2)+'\n')
texture.guides(name)
