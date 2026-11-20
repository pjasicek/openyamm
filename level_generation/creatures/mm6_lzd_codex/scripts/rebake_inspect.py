import bpy,collections,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3_unreduced.blend'))
o=bpy.data.objects['Body'];pieces=[v.value for v in o.data.attributes['piece'].data]
print('PIECES',dict(collections.Counter({k:sum(len(f.vertices)-2 for f in o.data.polygons if pieces[f.vertices[0]]==k) for k in set(pieces)})))
for m in o.data.materials:
 print('MAT',m.name, [(n.name,n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else '') for n in m.node_tree.nodes])
print('UVS', [u.name for u in o.data.uv_layers])
