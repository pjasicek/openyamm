"""Prevent repairs to an open mesh from reversing its existing visible surfaces."""
import bpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'review/feedback_v3/before/textured_uv.blend'))
original={tuple(sorted(f.vertices)):tuple(f.vertices) for f in bpy.data.objects['Body'].data.polygons}
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
matched=0
for f in bpy.data.objects['Body'].data.polygons:
 key=tuple(sorted(f.vertices))
 if key not in original:continue
 before=original[key];now=tuple(f.vertices);edges=set(zip(now,now[1:]+now[:1]))
 assert all(edge in edges for edge in zip(before,before[1:]+before[:1])),('Reversed existing face',f.index)
 matched+=1
assert matched==len(original),(matched,len(original))
assert not bpy.data.objects['Body'].data.validate()
contacts=json.loads((P/'review/feedback_v3/contacts_fit.json').read_text())['collision']
assert all(x['pairs']==0 for x in contacts if x['frame']>=50)
(P/'review/feedback_v3/repair_validation.json').write_text(json.dumps({'original_faces_preserved':matched,'valid_mesh':True,'settled_boot_clearance_120hz':True,'floor_min_m':min(x['floor'] for x in contacts)},indent=2))
print('REPAIR VALIDATION',matched,'original face windings preserved',flush=True)
