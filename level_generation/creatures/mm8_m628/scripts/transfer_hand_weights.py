"""Apply the authoritative connectivity weights to the unchanged glove in the animation master."""
import bpy,json
from pathlib import Path
from mathutils import Vector,kdtree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_complete.blend'))
body=bpy.data.objects['Body'];me=body.data
weights=json.loads((P/'work/right_hand_weights.json').read_text());tree=kdtree.KDTree(len(weights))
for i,w in enumerate(weights):tree.insert(Vector(w['co']),i)
tree.balance();used=set()
for v in me.vertices:
    if me.attributes['piece'].data[v.index].value!=5:continue
    candidates=[(i,d) for _,i,d in tree.find_range(v.co,1e-6) if i not in used]
    assert candidates, v.index
    i,d=min(candidates,key=lambda x:(x[1],x[0]));used.add(i)
    for g in body.vertex_groups:g.remove([v.index])
    for n,w in weights[i]['weights'].items():body.vertex_groups[n].add([v.index],w,'REPLACE')
assert len(used)==len(weights)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/motion_complete.blend'))
print('RIGHT HAND',len(used),'vertices matched exactly and reweighted by connectivity')
