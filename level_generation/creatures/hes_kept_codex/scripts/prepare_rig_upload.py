"""Local repairs of the two recorded Smart Topology returns; provisional projection for Meshy joint estimation.
Final retexture UVs/materials are deliberately deferred until the fitted rigs and reduction pass.
"""
import bpy,bmesh,sys,os,json,hashlib
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
sex=sys.argv[sys.argv.index('--')+1];assert sex in 'mf'
bpy.ops.wm.open_mainfile(filepath=str(P/'work'/f'kept_{sex}_ingested_v1.blend'))
body=bpy.data.objects['Body'];me=body.data
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bm.faces.ensure_lookup_table()
part=bm.verts.layers.int['piece'];face_part=bm.faces.layers.int.new('source_piece')
for face in bm.faces:face[face_part]=face.verts[0][part]
changes=[]
if sex=='m':
    loose=[v for v in bm.verts if v[part]==14]
    assert len(loose)==5
    bmesh.ops.delete(bm,geom=loose,context='VERTS')
    changes.append('Removed detached four-triangle internal crotch flap (source piece 14).')
    # The lower shirt contains intersecting folded surfaces: rebuild only this short hem from its waist ring.
    shirt=[f for f in bm.faces if f[face_part]==0 and all(abs(v.co.x)<.23 for v in f.verts)]
    shirt_edges={e for f in shirt for e in f.edges};shirt_verts={v for f in shirt for v in f.verts}
    bmesh.ops.bisect_plane(bm,geom=shirt+list(shirt_edges)+list(shirt_verts),dist=1e-7,
                          plane_co=Vector((0,0,1.02)),plane_no=Vector((0,0,1)),clear_inner=True)
    ring_edges={e for e in bm.edges if e.is_boundary and all(abs(v.co.z-1.02)<1e-5 for v in e.verts)
                and e.link_faces[0][face_part]==0}
    adj={}
    for edge in ring_edges:
        a,b=edge.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
    assert len(adj)>12 and all(len(v)==2 for v in adj.values()),len(adj)
    remaining=set(ring_edges);rings=[]
    while remaining:
        edge=next(iter(remaining));loop=next(l for l in edge.link_faces[0].loops if l.edge==edge)
        ring=[loop.link_loop_next.vert,loop.vert]
        while True:
            nxt=next(v for v in adj[ring[-1]] if v!=ring[-2])
            if nxt==ring[0]:break
            assert nxt not in ring
            ring.append(nxt)
        members=set(ring);remaining={e for e in remaining if e.verts[0] not in members}
        rings.append(ring)
    rings.sort(key=lambda r:sum((r[i].co-r[(i+1)%len(r)].co).length for i in range(len(r))),reverse=True)
    ring=rings[0]
    for inner in rings[1:]:
        hub=bm.verts.new(sum((v.co for v in inner),Vector())/len(inner));hub[part]=0
        for i in range(len(inner)):
            face=bm.faces.new((inner[i],inner[(i+1)%len(inner)],hub));face[face_part]=0
    print('SHIRT RINGS',[(len(r),[round(float(x),3) for x in sum((v.co for v in r),Vector())/len(r)]) for r in rings],flush=True)
    for v in ring:
        if v.co.y<0:v.co.y*=.82
    original=[v.co.copy() for v in ring];centre=sum(original,Vector())/len(original)
    for z in (1.00,.94,.865):
        t=(1.02-z)/(1.02-.865);new=[]
        for co in original:
            pt=Vector((centre.x+(co.x-centre.x)*(1+.20*t),centre.y+(co.y-centre.y)*(1+.65*t),z))
            v=bm.verts.new(pt);v[part]=0;new.append(v)
        for i in range(len(ring)):
            j=(i+1)%len(ring);face=bm.faces.new((ring[i],ring[j],new[j],new[i]));face[face_part]=0
        ring=new
    quads=[f for f in bm.faces if len(f.verts)==4]
    bmesh.ops.triangulate(bm,faces=quads)
    changes.append('Rebuilt the self-intersecting lower shirt from its 1.02 m waist ring to the same short 0.865 m hem; upper shirt, sleeves and belt preserved.')

else:
    # This detached triangle exactly fills a forearm opening, so sew it to that arm rather than delete it.
    arm_vertices=[v for v in bm.verts if v[part] in (3,17)]
    n=len(bm.verts);bmesh.ops.remove_doubles(bm,verts=arm_vertices,dist=1e-7)
    assert n-len(bm.verts)==3
    changes.append('Sewed three exact coincident vertices of the detached forearm patch; preserved its face.')
    # The selected master has a tied-back cap and bun; the return invented thick hanging bang cards.
    cards=[v for v in bm.verts if v[part] in (11,15,16)]
    assert len(cards)==118
    bmesh.ops.delete(bm,geom=cards,context='VERTS')
    bm.verts.ensure_lookup_table();bm.verts.index_update()
    skin=[tuple(v.index for v in face.verts) for face in bm.faces if face[face_part]==1]
    tree=BVHTree.FromPolygons([v.co[:] for v in bm.verts],skin,all_triangles=True)
    for v in bm.verts:
        if v[part]!=6:continue
        x,y,z=v.co
        if y<-.04 and z>1.55:
            v.co.z+=.035*min(1,max(0,(-y-.04)/.04))*min(1,max(0,(1.66-z)/.10))
        loc,normal,face,distance=tree.find_nearest(v.co)
        assert loc is not None and distance<.09
        v.co=(loc+normal*.004)*.9+v.co*.1
    changes.append('Removed three invented thick bang/loose-hair cards; fitted the pulled-back cap toward a 4 mm head shell with 10% retained volume, retaining the bun.')
# Only identified skin cut ends and unwanted cloth tears are capped. Hair, eye backs and hems stay open.
boundary={e for e in bm.edges if e.is_boundary};loops=[]
while boundary:
    stack=[next(iter(boundary))];edges=set()
    while stack:
        e=stack.pop()
        if e not in boundary:continue
        boundary.remove(e);edges.add(e);stack.extend(q for v in e.verts for q in v.link_edges if q in boundary)
    verts={v for e in edges for v in e.verts};co=np.array([v.co[:] for v in verts]);piece=next(iter(edges)).link_faces[0][face_part]
    loops.append((edges,verts,co.mean(0),piece))
patches=[]
for edges,verts,centre,piece in loops:
    x,y,z=centre;n=len(edges);reason=None
    if piece in (3,4) and z>1.0:reason='hidden forearm cut under sleeve'
    elif piece==1 and z<1.45:reason='hidden neck cut inside shirt'
    elif sex=='m' and piece==1 and n==5:reason='small eyelid surface tear'
    elif sex=='m' and piece==0 and z>1.02:reason='shirt waist gap'
    elif sex=='m' and piece==2 and n in (4,10):reason='trouser surface tear'
    elif sex=='f' and piece==0 and n in (4,70):reason='shirt surface tear/waist gap'
    if not reason:continue
    assert all(e.is_boundary for e in edges)
    # A new hub avoids reusing diagonals already present in the folded source surface.
    hub=bm.verts.new(Vector(centre));hub[part]=piece;triangles=[]
    for edge in edges:
        loop=next(loop for loop in edge.link_faces[0].loops if loop.edge==edge)
        face=bm.faces.new((loop.link_loop_next.vert,loop.vert,hub));face[face_part]=piece
        triangles.append(face)
    patches.append({'source_piece':piece,'boundary_edges':n,'centroid':centre.tolist(),'reason':reason,'added_triangles':len(triangles)})
bm.normal_update()
bad_edges=[e for e in bm.edges if not e.is_manifold and not e.is_boundary]
assert not bad_edges, [(len(e.link_faces),[list(v.co) for v in e.verts]) for e in bad_edges]
assert all(f.calc_area()>1e-12 for f in bm.faces)
bm.to_mesh(me);bm.free();me.update()
# Preserve edited positions for Meshy weight/joint correspondence, as in the playbook's step1_clean.py.
co=np.array([v.co[:] for v in me.vertices]);me.attributes['orig_co'].data.foreach_set('vector',co.ravel())
for face in me.polygons:face.use_smooth=True
uv=me.uv_layers.new(name='RigProjectionOnly')
me.materials.clear()
sex_folder='male_freed' if sex=='m' else 'female_freed'
projections=[]
for view in ('01_front','02_back'):
    image=bpy.data.images.load(str(P/'references_hd'/sex_folder/(view+'.png')),check_existing=True);image.pack()
    pixels=np.array(image.pixels[:]).reshape(image.size[1],image.size[0],4)
    ys,xs=np.where(pixels[:,:,3]>.5)
    projections.append((xs.min()/image.size[0],xs.max()/image.size[0],ys.min()/image.size[1],ys.max()/image.size[1]))
    mat=bpy.data.materials.new('RigProjection_'+view);mat.use_nodes=True
    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.85;bsdf.inputs['Metallic'].default_value=0
    node=mat.node_tree.nodes.new('ShaderNodeTexImage');node.image=image
    mat.node_tree.links.new(node.outputs['Color'],bsdf.inputs['Base Color'])
    mat.use_backface_culling=True;me.materials.append(mat)
width=float(np.ptp(co[:,0]));height=float(np.ptp(co[:,2]))
for face in me.polygons:
    back=face.normal.y>0;face.material_index=int(back);u0,u1,v0,v1=projections[int(back)]
    for li in face.loop_indices:
        v=co[me.loops[li].vertex_index];u=(v[0]/width)*(-1 if back else 1)+.5
        uv.data[li].uv=(u0+u*(u1-u0),v0+(v[2]/height)*(v1-v0))
# Use only this body in the upload; export preserves the metre scale and glTF +Z facing.
for ob in bpy.data.objects:ob.select_set(ob==body)
bpy.context.view_layer.objects.active=body
blend=P/'work'/f'kept_{sex}_clean_v1.blend';glb=P/'work'/f'kept_{sex}_clean_v1.glb'
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,
    export_animations=False,export_skins=False,export_attributes=False,export_materials='EXPORT',export_image_format='AUTO')
report={'source_blend':f'work/kept_{sex}_ingested_v1.blend','geometry_changes':changes,'patches':patches,
        'vertices':len(me.vertices),'triangles':sum(len(f.vertices)-2 for f in me.polygons),
        'provisional_materials':'Two unmodified HD body references projected front/back for the rig service only; no final UV acceptance.',
        'upload':str(glb.relative_to(P)),'sha256':hashlib.sha256(glb.read_bytes()).hexdigest(),
        'blend':str(blend.relative_to(P)),'blend_sha256':hashlib.sha256(blend.read_bytes()).hexdigest(),
        'nonmanifold_edges_excluding_boundary':0,'degenerate_faces':0,'visual_review':'pending'}
(P/'review/geometry'/sex/'cleanup.json').write_text(json.dumps(report,indent=2)+'\n')
print('CLEAN',sex,report['vertices'],report['triangles'],'patches',len(patches),flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
