"""Inspect source topology, normals, UV seams and density for the worker's twelve sculptural meshes."""
import json, math
from pathlib import Path
import bpy, bmesh
P=Path(__file__).resolve().parents[1]
rows={}
for name,d in json.loads((P/'designs.json').read_text()).items():
 if d['shape']!='meshy':continue
 bpy.ops.wm.open_mainfile(filepath=str(P/'work/codex_tex'/f'{name}.blend'))
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();uv=bm.loops.layers.uv.active
 sharp=[]
 for e in bm.edges:
  if len(e.link_faces)!=2:continue
  if e.calc_face_angle()>math.radians(40):
   a,b=e.link_faces
   lookup=lambda f:{l.vert.index:l[uv].uv.copy() for l in f.loops}
   au,bu=lookup(a),lookup(b)
   if all((au[v.index]-bu[v.index]).length<1e-5 for v in e.verts):sharp.append({'edge':e.index,'angle':math.degrees(e.calc_face_angle()),'uv_delta':[(au[v.index]-bu[v.index]).length for v in e.verts],'face_areas':[f.calc_area() for f in e.link_faces],'seam':e.seam})
 area=sum(f.calc_area() for f in bm.faces);uvarea=0
 for f in bm.faces:
  coords=[l[uv].uv for l in f.loops]
  uvarea+=abs(sum(a.x*b.y-b.x*a.y for a,b in zip(coords,coords[1:]+coords[:1])))/2
 rows[name]={'custom_normals':o.data.has_custom_normals,'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True),'area':area,'uv_area':uvarea,'texels_per_authoring_metre':1024*math.sqrt(uvarea/area),'hard_edges_without_uv_seam':len(sharp),'seam_details':sharp}
 bm.free()
print(json.dumps(rows,indent=2));(P/'review/meshy_geometry_audit.json').write_text(json.dumps(rows,indent=2)+'\n')
assert all(v['hard_edges_without_uv_seam']==0 for v in rows.values()), 'A hard edge has joined UVs'
