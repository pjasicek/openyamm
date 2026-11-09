import bpy,bmesh,collections,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ['unreduced','lod3_material02']:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round2/reduction/{name}.blend'));o=bpy.data.objects['Jackalman'];m=o.data;print('MESH',name,'vertices',len(m.vertices),'triangles',sum(len(f.vertices)-2 for f in m.polygons),'materials',collections.Counter({i:sum(len(f.vertices)-2 for f in m.polygons if f.material_index==i)for i in range(len(m.materials))}),flush=True)
 if m.attributes.get('piece'):
  parts=[a.value for a in m.attributes['piece'].data];groups=collections.defaultdict(int)
  for f in m.polygons:groups[parts[f.vertices[0]]]+=len(f.vertices)-2
  print('PIECES',dict(groups),flush=True)
 for distance in [1e-6,1e-4,1e-3]:
  bm=bmesh.new();bm.from_mesh(m);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=distance);print('WELD',distance,len(bm.verts),flush=True);bm.free()
