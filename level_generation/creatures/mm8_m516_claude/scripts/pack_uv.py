"""Repack each existing UV set without island rotation; preserve source UVs for texture resampling."""
import bpy,bmesh,numpy as np,json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));o=bpy.data.objects['Body'];me=o.data
source=me.uv_layers.new(name='TextureSourceUV');uv=me.uv_layers['UVMap']
for a,b in zip(source.data,uv.data):a.uv=b.uv.copy()
me.uv_layers.active=uv;attr=me.attributes.new('original_face','INT','FACE');attr.data.foreach_set('value',np.arange(len(me.polygons),dtype=np.int32));report={}
def area(m):
 m.calc_loop_triangles();u=m.uv_layers['UVMap'].data;total=0
 for t in m.loop_triangles:
  a,b,c=[u[l].uv for l in t.loops];v=b-a;w=c-a;total+=abs(v.x*w.y-v.y*w.x)/2
 return total
for slot,name in [(0,'body'),(1,'head')]:
 d=o.copy();d.data=me.copy();bpy.context.collection.objects.link(d);d.modifiers.clear();d.parent=None
 bm=bmesh.new();bm.from_mesh(d.data);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=slot],context='FACES');bm.to_mesh(d.data);bm.free()
 for layer in list(d.data.uv_layers):
  if layer.name!='UVMap':d.data.uv_layers.remove(layer)
 bpy.ops.object.select_all(action='DESELECT');d.select_set(True);bpy.context.view_layer.objects.active=d
 before=area(d.data);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.select_all(action='SELECT');bpy.ops.uv.pack_islands(rotate=False,margin=.002,margin_method='FRACTION');bpy.ops.object.mode_set(mode='OBJECT');after=area(d.data)
 for f in d.data.polygons:
  original=d.data.attributes['original_face'].data[f.index].value;dst=me.polygons[original]
  assert len(f.loop_indices)==len(dst.loop_indices)
  for a,b in zip(dst.loop_indices,f.loop_indices):uv.data[a].uv=d.data.uv_layers['UVMap'].data[b].uv.copy()
 report[name]={'before_area':before,'after_area':after};bpy.data.objects.remove(d,do_unlink=True)
me.attributes.remove(me.attributes['original_face']);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_master.blend'));(P/'work/uv_pack.json').write_text(json.dumps(report,indent=2));print(report)
