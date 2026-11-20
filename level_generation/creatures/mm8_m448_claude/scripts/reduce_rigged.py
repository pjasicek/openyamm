"""Triangle budget AFTER the weights (TEST_DRIVE.md: reducing before the Meshy weight transfer moved vertices up to
23 mm, mismatched weights and pushed the attack's arm stretch from 4.3x to 9.7x). Collapse decimation interpolates
vertex groups, so the finished weights survive. Per shell (piece) targets; on the skin the head (Head/Neck weight
> 0.3) and the hands (hand/finger weight > 0.3) are protected. Shells are separated, reduced and joined back with
the armature modifier. Args: -- <in blend> <out blend>"""
import bpy, sys, os
import numpy as np
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Rig']; body = bpy.data.objects['Body']; me = body.data
# Preserve the complete head surface, ears, eyes, whiskers and incisors; reduce detached neck/fur shells.
co=np.array([tuple(v.co) for v in me.vertices]);piece=np.array([x.value for x in me.attributes['piece'].data])
garment=np.where(piece==0,0,np.where(piece==1,1,np.where(piece==3,3,2)))
garment[piece==201]=201
adj=[[] for _ in me.vertices]
for e in me.edges:
    a,b=e.vertices;adj[a].append(b);adj[b].append(a)
seen=set()
for v in me.vertices:
    if piece[v.index]!=200 or v.index in seen:continue
    stack=[v.index];ids=[]
    while stack:
        i=stack.pop()
        if i in seen:continue
        seen.add(i);ids.append(i);stack.extend(j for j in adj[i] if j not in seen)
    c=co[ids]
    is_whisker=len(ids)<500 and c[:,1].min()<-.27 and max(c.max(0)-c.min(0))>.045
    is_detail=len(ids)>500 or (c[:,1].max()<-.27 and not is_whisker)
    garment[ids]=200 if len(ids)>500 else (204 if is_detail else (203 if is_whisker else 202))
attr=me.attributes.get('garment') or me.attributes.new('garment','INT','POINT');attr.data.foreach_set('value',garment.tolist())
counts={}
for f in me.polygons:
    g=int(garment[f.vertices[0]]);counts[g]=counts.get(g,0)+len(f.vertices)-2
body_budget=14400-counts.get(200,0)-counts.get(201,0)-800-600-180-600-400-250
assert body_budget>=2800,counts
TARGET={0:4800,1:800,2:600,3:180,202:600,203:400,204:250}
print('BUDGET',counts,'targets',TARGET)
before = sum(len(p.vertices) - 2 for p in me.polygons)
names = [g.name for g in body.vertex_groups]
prot = body.vertex_groups.new(name='_protect')
keys = [i for i, n in enumerate(names) if 'Hand' in n or 'Finger' in n or 'Foot' in n]
pv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', pv)
for v in me.vertices:
    w = sum(e.weight for e in v.groups if e.group in keys)
    if w > 0.3 and pv[v.index] == 0:                       # only the face/hand SKIN; teeth and ear hoops ride the head
        prot.add([v.index], 0.6, 'REPLACE')
for o in bpy.data.objects:
    o.select_set(o == body)
bpy.context.view_layer.objects.active = body
bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='DESELECT'); bpy.ops.object.mode_set(mode='OBJECT')
parts = {}
for p, tgt in TARGET.items():
    for v in me.vertices:
        v.select = bool(pv[v.index] == p)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.separate(type='SELECTED'); bpy.ops.object.mode_set(mode='OBJECT')
    me = body.data
    pv = np.zeros(len(me.vertices), np.int32); me.attributes['garment'].data.foreach_get('value', pv)
    new = [o for o in bpy.context.selected_objects if o is not body]
    parts[p] = new[-1]
    for o in bpy.data.objects:
        o.select_set(o == body)
report = {}
for p, o in parts.items():
    tris = sum(len(f.vertices) - 2 for f in o.data.polygons)
    if tris > TARGET[p]:
        m = o.modifiers.new('dec', 'DECIMATE'); m.decimate_type = 'COLLAPSE'; m.ratio = TARGET[p] / tris
        m.vertex_group = '_protect'; m.invert_vertex_group = True
        bpy.context.view_layer.objects.active = o
        for x in bpy.data.objects:
            x.select_set(x == o)
        bpy.ops.object.modifier_move_to_index(modifier='dec', index=0)
        bpy.ops.object.modifier_apply(modifier='dec')
    report[p] = (tris, sum(len(f.vertices) - 2 for f in o.data.polygons))
for x in bpy.data.objects:
    x.select_set(x is body or x in parts.values())
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
body.vertex_groups.remove(body.vertex_groups['_protect'])
me = body.data
pc = np.zeros(len(me.vertices), np.int32); me.attributes['piece'].data.foreach_get('value', pc)
per = {}
for f in me.polygons:
    k = int(pc[f.vertices[0]]); per[k] = per.get(k, 0) + len(f.vertices) - 2
thin = sorted(k for k, n in per.items() if n < 4)
print('REDUCE pieces', len(per), 'with < 4 tris:', len(thin), thin[:20])
print('REDUCE', {p: f'{a}->{b}' for p, (a, b) in report.items()}, 'total', before, '->', sum(len(f.vertices) - 2 for f in body.data.polygons))
# Match the engine's four-weight skinning before the visual checks and UV handoff.
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL',lock_active=False)
tri=body.modifiers.new('triangulate','TRIANGULATE');bpy.ops.object.modifier_move_to_index(modifier=tri.name,index=0);bpy.ops.object.modifier_apply(modifier=tri.name)
body.data.validate(verbose=True, clean_customdata=False)
assert not body.data.validate(clean_customdata=False)
final=sum(len(f.vertices)-2 for f in body.data.polygons)
assert final<=14700,final
import json
from pathlib import Path
(Path(__file__).resolve().parents[1]/'work/reduction.json').write_text(json.dumps({'before':before,'after':final,'targets':TARGET,'actual':report,'head_core_triangles_preserved':counts[200]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
