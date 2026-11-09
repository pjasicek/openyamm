"""Spend geometry on the face, projecting its subdivided surface back to the detailed head."""
from pathlib import Path
import bpy,bmesh,numpy as np,sys,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/head_weighted.blend'));head=bpy.data.objects['HeadSource']
with bpy.data.libraries.load(str(p/'work/head_voxel.blend'),link=False) as (src,dst):dst.objects=['HeadSource']
dense=dst.objects[0];bm=bmesh.new();bm.from_mesh(dense.data);tree=BVHTree.FromBMesh(bm);bm.free();bpy.data.objects.remove(dense,do_unlink=True)
def face(v):return abs(v.co.x)<.57 and v.co.y<-.26 and -.64<v.co.z<.74
bm=bmesh.new();bm.from_mesh(head.data);faces=[f for f in bm.faces if all(face(v) for v in f.verts)];edges={e for f in faces for e in f.edges}
print('REFINE_FACE',len(faces),len(edges),flush=True)
bmesh.ops.subdivide_edges(bm,edges=list(edges),cuts=1,use_grid_fill=True)
bm.normal_update();distances=[]
for v in bm.verts:
 if not face(v):continue
 hit=tree.find_nearest(v.co)[0]
 distance=(hit-v.co).length
 if distance<.12:v.co=hit;distances.append(distance)
print('FACE_TOPOLOGY_BEFORE_TRIANGULATION',sum(e.is_boundary for e in bm.edges),sum(not e.is_manifold and not e.is_boundary for e in bm.edges),flush=True)
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bmesh.ops.triangulate(bm,faces=list(bm.faces))
loose=[e for e in bm.edges if not e.link_faces]
if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
print('NONMANIFOLD_LINKS',[len(e.link_faces) for e in bm.edges if not e.is_manifold],flush=True)
report={'face_patch_before':len(faces),'projected_vertices':len(distances),'max_displacement_source_units':max(distances),'triangles':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold and not e.is_boundary for e in bm.edges)}
print('FACE_REPORT',report,flush=True)
bm.to_mesh(head.data);bm.free()
for f in head.data.polygons:f.use_smooth=True
co=np.array([tuple(v.co) for v in head.data.vertices]);lo=co.min(0);hi=co.max(0)
(p/'work/head_detailed.json').write_text(json.dumps(report,indent=2));print('HEAD_DETAIL',report)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/head_detailed.blend'))
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/head_detailed'),float((lo[2]+hi[2])/2),float(np.ptp(co,axis=0).max()*1.1),views=('front','left','back','three_quarter'),resolution=(650,650),target=tuple((lo[:2]+hi[:2])/2))

assert report['boundary_edges']==report['nonmanifold_edges']==0
