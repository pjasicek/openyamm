"""Freeze the accepted render tessellation before simplification; keep corner UVs and normals."""
import bpy,collections
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'review/round4/before/work/animation_finish.blend'));b=bpy.data.objects['Body'];old=b.data;group_names=[g.name for g in b.vertex_groups]
for f in old.polygons:f.use_smooth=True
old.calc_loop_triangles();tri=list(old.loop_triangles);print('SOURCE_POLYGONS',dict(collections.Counter(len(f.vertices) for f in old.polygons)),flush=True);loops=[i for t in tri for i in t.loops];weights=[[(g.group,g.weight) for g in v.groups] for v in old.vertices];normal=[old.corner_normals[i].vector[:] for i in loops];uv=[old.uv_layers['UVMap'].data[i].uv[:] for i in loops];piece=[v.value for v in old.attributes['piece'].data];cuff=[old.attributes['cuff'].data[t.polygon_index].value for t in tri]
m=bpy.data.meshes.new('Accepted render triangles');m.from_pydata([v.co[:] for v in old.vertices],[],[t.vertices[:] for t in tri]);layer=m.uv_layers.new(name='UVMap')
for d,q in zip(layer.data,uv):d.uv=q
for f in m.polygons:f.use_smooth=True
m.normals_split_custom_set(normal);m.attributes.new('piece','INT','POINT').data.foreach_set('value',piece);m.attributes.new('cuff','INT','FACE').data.foreach_set('value',cuff);b.data=m
for name in group_names:b.vertex_groups.new(name=name)
for i,row in enumerate(weights):
 for group,w in row:b.vertex_groups[group].add([i],w,'REPLACE')
assert len(m.polygons)==12364 and all(len(f.vertices)==3 for f in m.polygons)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/review4_triangulated.blend'))
