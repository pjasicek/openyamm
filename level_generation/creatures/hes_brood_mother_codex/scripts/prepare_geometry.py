"""Normalise the untouched Meshy return and report connected geometry, before local repairs."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/raw_geometry.blend'))
o=next(o for o in bpy.context.scene.objects if o.type=='MESH');o.name='BroodMother';me=o.data
co=np.array([tuple(v.co) for v in me.vertices]);lo=co.min(0);hi=co.max(0);scale=4.5/(hi[2]-lo[2])
me.transform(Matrix.Rotation(math.radians(45),4,'Z') @ Matrix.Diagonal((scale,scale,scale,1)) @ Matrix.Translation((0,0,-lo[2])))
bm=bmesh.new();bm.from_mesh(me)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=0.000005)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.to_mesh(me);bm.free();me.update()
for f in me.polygons:f.use_smooth=True
mat=bpy.data.materials.new('DiagnosticClay');mat.diffuse_color=(0.35,0.40,0.48,1);mat.use_nodes=True
mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(0.35,0.40,0.48,1)
mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.75
me.materials.append(mat)
co=np.array([tuple(v.co) for v in me.vertices]);faces=np.array([tuple(f.vertices) for f in me.polygons])
np.savez(P/'work/normalised_mesh.npz',vertices=co,faces=faces)
bm=bmesh.new();bm.from_mesh(me)
report={'scale_from_meshy':scale,'height_m':float(co[:,2].max()),'vertices':len(co),'triangles':len(faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'bounds':[co.min(0).tolist(),co.max(0).tolist()]}
bm.free();(P/'review/geometry_ingest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/normalised_geometry.blend'))
