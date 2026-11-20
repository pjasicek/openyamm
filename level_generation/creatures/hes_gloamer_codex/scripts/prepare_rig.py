"""Repair measured surface holes and flatten pore bulbs; project HD views only for joint estimation."""
import bpy,bmesh,json,os,sys,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/gloamer_ingested_v1.blend'))
body=bpy.data.objects['Body']; me=body.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
piece=bm.verts.layers.int['piece']
# Two source pieces share the same seven-edge pore boundary; sew the patch before closing real holes.
patch=[v for v in bm.verts if v[piece] in (35,65)]
for v in patch:v[piece]=35
before=len(bm.verts);bmesh.ops.remove_doubles(bm,verts=patch,dist=1e-7)
assert before-len(bm.verts)==7
region=bm.faces.layers.int.new('region')
parts={}
for v in bm.verts:parts.setdefault(v[piece],[]).append(v)
pores=[]
for key,verts in parts.items():
    c=sum((v.co for v in verts),Vector())/len(verts)
    if key and not (c.y<-.3 and 1.2<c.z<1.34):pores.append(key)
for f in bm.faces:f[region]=0 if f.verts[0][piece]==0 else (2 if f.verts[0][piece] in pores else 1)
remaining={e for e in bm.edges if e.is_boundary};repairs=[]
while remaining:
    stack=[next(iter(remaining))];edges=set()
    while stack:
        e=stack.pop()
        if e not in remaining:continue
        remaining.remove(e);edges.add(e)
        stack.extend(q for v in e.verts for q in v.link_edges if q in remaining)
    verts={v for e in edges for v in e.verts}
    assert all(sum(e in edges for e in v.link_edges)==2 for v in verts)
    co=np.array([v.co[:] for v in verts]);diam=float(np.linalg.norm(co.max(0)-co.min(0)))
    assert diam<.09,(diam,co.mean(0).tolist())
    pid=next(iter(verts))[piece];rid=next(iter(edges)).link_faces[0][region]
    # A centre cap preserves each boundary winding without reusing existing diagonals.
    hub=bm.verts.new(Vector(co.mean(0)));hub[piece]=pid;parts[pid].append(hub)
    for edge in edges:
        loop=next(l for l in edge.link_faces[0].loops if l.edge==edge)
        f=bm.faces.new((loop.link_loop_next.vert,loop.vert,hub));f[region]=rid
    repairs.append({'piece':pid,'edges':len(edges),'diameter':diam,'centre':co.mean(0).tolist()})
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
bm.verts.index_update();bm.faces.index_update()
skinfaces=[tuple(v.index for v in f.verts) for f in bm.faces if f[region]==0]
tree=BVHTree.FromPolygons([v.co[:] for v in bm.verts],skinfaces,all_triangles=True)
for pid in pores:
    verts=parts[pid];centre=sum((v.co for v in verts),Vector())/len(verts)
    loc,n,face,dist=tree.find_nearest(centre)
    assert loc is not None and dist<.04,(pid,dist)
    for v in verts:
        rel=v.co-centre;ax=n*rel.dot(n)
        v.co=loc+n*.002+(rel-ax)*.7+ax*.18
bm.normal_update()
assert all(e.is_manifold for e in bm.edges)
assert all(f.calc_area()>1e-12 for f in bm.faces)
# Each closed component must retain outward winding.
for pid in parts:
    fs=[f for f in bm.faces if f.verts[0][piece]==pid]
    volume=sum(f.verts[0].co.dot(f.verts[1].co.cross(f.verts[2].co))/6 for f in fs)
    if volume<0:bmesh.ops.reverse_faces(bm,faces=fs)
bm.to_mesh(me);bm.free();me.update()
co=np.array([v.co[:] for v in me.vertices]);me.attributes['orig_co'].data.foreach_set('vector',co.ravel())
for f in me.polygons:f.use_smooth=True
uv=me.uv_layers.new(name='RigProjectionOnly');me.materials.clear();projections=[]
for view in ('01_front','02_back'):
    img=bpy.data.images.load(str(P/'references_hd'/(view+'.png')),check_existing=True);img.pack()
    pix=np.array(img.pixels[:]).reshape(img.size[1],img.size[0],4);ys,xs=np.where(pix[:,:,3]>.5)
    projections.append((xs.min()/img.size[0],xs.max()/img.size[0],ys.min()/img.size[1],ys.max()/img.size[1]))
    mat=bpy.data.materials.new('RigProjection_'+view);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=img
    mat.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
width=float(np.ptp(co[:,0]));height=float(np.ptp(co[:,2]))
for f in me.polygons:
    back=f.normal.y>0;f.material_index=int(back);u0,u1,v0,v1=projections[int(back)]
    for li in f.loop_indices:
        v=co[me.loops[li].vertex_index];u=v[0]/width*(-1 if back else 1)+.5
        uv.data[li].uv=(u0+u*(u1-u0),v0+v[2]/height*(v1-v0))
for o in bpy.data.objects:o.select_set(o==body)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/gloamer_clean_v1.blend'))
glb=P/'work/gloamer_rig_upload_v1.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,
    export_animations=False,export_skins=False,export_attributes=False,export_materials='EXPORT')
report={'holes_closed':repairs,'pores_flattened':pores,'teeth_preserved':len(parts)-len(pores)-1,
        'triangles':sum(len(f.vertices)-2 for f in me.polygons),'boundary_edges':0,
        'geometry':'Surface-hole caps and pore flattening only; body, digits and mouth retained. Reduction follows weighting.',
        'upload':str(glb.relative_to(P)),'sha256':hashlib.sha256(glb.read_bytes()).hexdigest()}
(P/'review/geometry/cleanup.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
