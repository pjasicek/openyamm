"""Diagnostic: weights of the rigid-armour vertices in work/anim_v4.blend (should be B_Spine2 1.0)."""
import bpy, json
from pathlib import Path
P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work' / 'anim_v4.blend'))
q = bpy.data.objects['Queen']; gi = {g.index: g.name for g in q.vertex_groups}
RM = json.loads((P / 'work' / 'rigid_mask.json').read_text())
bad = 0
for i in RM['metal'] + RM['strap']:
    w = {gi[g.group]: round(g.weight, 2) for g in q.data.vertices[i].groups if g.weight > 0.01}
    if w != {'B_Spine2': 1.0}:
        bad += 1
        if bad < 8:
            print('ARM', i, [round(x, 3) for x in q.data.vertices[i].co], w)
print('ARMBAD', bad, 'of', len(RM['metal'] + RM['strap']))
