"""Select v2 anatomy, repair isolated holes/eyes, open the hem and fit its native standing width."""
from pathlib import Path
import bpy,bmesh,json,sys
import numpy as np
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'))
import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/st_v2_parts.blend'))
# Keep the separately generated, concealed legs; no visible anatomy is borrowed from another creature.
with bpy.data.libraries.load(str(p/'work/st_v1_parts.blend'),link=False) as (src,dst):dst.objects=['P03']
legs=dst.objects[0];bpy.context.collection.objects.link(legs);legs.name='P12'
for v in legs.data.vertices:
 t=np.clip((1.085-v.co.z)/.90,0,1);v.co.x*=1-.40*t
 v.co.y-=.025
# The generated solid hem cap must not bridge the ankles during walking.
o=bpy.data.objects['P00'];bm=bmesh.new();bm.from_mesh(o.data)
bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=(0,0,.025),plane_no=(0,0,1),clear_inner=True,clear_outer=False)
bm.to_mesh(o.data);bm.free()
# A connected flood below the belt excludes the separate hanging sleeve tips.
c=np.array([tuple(v.co) for v in o.data.vertices]);adj=[set() for _ in c]
for e in o.data.edges:
 a,b=e.vertices;adj[a].add(b);adj[b].add(a)
cloth=set();todo=[int(np.argmin(c[:,2]))]
while todo:
 i=todo.pop()
 if i in cloth or c[i,2]>1.075:continue
 cloth.add(i);todo.extend(adj[i]-cloth)
assert len(cloth)>400
for i in cloth:
 v=o.data.vertices[i];t=np.clip((1.075-v.co.z)/1.05,0,1)
 v.co.x*=1-.25*t;v.co.y*=1-.28*t
region=o.data.attributes.new('garment_region','INT','POINT')
region.data.foreach_set('value',[1 if i in cloth else 0 for i in range(len(c))])
# Fill only the five-edge thumb defect, preserving the wrist opening.
for part in ['P03','P04','P01','P05']:
 mesh=bpy.data.objects[part].data;bm=bmesh.new();bm.from_mesh(mesh)
 boundary=set(e for e in bm.edges if e.is_boundary)
 while boundary:
  todo=[next(iter(boundary))];component=set()
  while todo:
   e=todo.pop()
   if e not in boundary:continue
   boundary.remove(e);component.add(e);todo.extend(q for v in e.verts for q in v.link_edges if q in boundary)
  if len(component)<=5:bmesh.ops.holes_fill(bm,edges=list(component),sides=5)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
# Smooth eye volumes sit behind the generated eyelid rims; the original fragments were open, jagged fans.
for name,x in [('P10',-.0126),('P11',.0237)]:
 bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=(x,-.1205,1.588))
 eye=bpy.context.object;eye.name=name;eye.scale=(.0118,.010,.0068)
 bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
for o in bpy.data.objects:
 if o.type=='MESH':
  for f in o.data.polygons:f.use_smooth=True
  o.hide_render=False
report={'selected_geometry':'meshy/body_geometry_v2/model_urls_glb.glb','repairs':['filled isolated thumb, hair and tassel holes','replaced jagged eye fans with smooth volumes','opened solid lower hem','narrowed hem to native standing proportions','retained concealed generated v1 legs and fitted their stance'],'robe_vertices':len(cloth),'robe_hem_width_m':float(max(o.co.x for o in bpy.data.objects['P00'].data.vertices if o.co.z<.035)-min(o.co.x for o in bpy.data.objects['P00'].data.vertices if o.co.z<.035))}
(p/'work/geometry_selected.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/clean_parts.blend'))
common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='MATERIAL'
common.render_views(str(p/'review/clean_parts'),.85,1.9,views=('front','left','back','three_quarter'),resolution=(600,900))
