"""Close omitted component caps in Smart Topology output without changing boundary positions."""
import bmesh,bpy

def repair(obj,voxel=None,budget=5500):
    bm=bmesh.new();bm.from_mesh(obj.data)
    before=sum(e.is_boundary for e in bm.edges)
    # A few generated teeth share a single nonmanifold seam; separate their surfaces before closing each cap.
    excess=[e for e in bm.edges if len(e.link_faces)>2]
    if excess:bmesh.ops.split_edges(bm,edges=excess)
    for _ in range(3):
        edges=[e for e in bm.edges if e.is_boundary]
        if not edges:break
        result=bmesh.ops.holes_fill(bm,edges=edges,sides=0)
        if not result['faces']:break
    bmesh.ops.triangulate(bm,faces=bm.faces[:],quad_method='SHORT_EDGE')
    bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-7)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    remaining=sum(not e.is_manifold for e in bm.edges)
    report={'boundary_before':before,'nonmanifold_split':len(excess),'nonmanifold_after':remaining,
        'faces':len(bm.faces),'method':'local omitted component caps; boundary vertex positions preserved'}
    assert remaining==0 or voxel,report
    bm.to_mesh(obj.data);bm.free();obj.data.update()
    if remaining:
        # Explicit per-design union for intersecting cap edges; the ordinary closed cap repairs retain topology.
        bpy.context.view_layer.objects.active=obj
        mod=obj.modifiers.new('Resolve intersecting component seams','REMESH');mod.mode='VOXEL';mod.voxel_size=voxel
        bpy.ops.object.modifier_apply(modifier=mod.name)
        triangles=sum(len(f.vertices)-2 for f in obj.data.polygons)
        mod=obj.modifiers.new('Preserve silhouette within game budget','DECIMATE');mod.ratio=min(1,budget/triangles);mod.use_collapse_triangulate=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
        report.update(method='local caps then explicit voxel union and silhouette reduction',voxel=voxel)
    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.dissolve_degenerate(bm,edges=bm.edges[:],dist=1e-7);bmesh.ops.triangulate(bm,faces=bm.faces[:]);bmesh.ops.recalc_face_normals(bm,faces=bm.faces[:])
    for _ in range(4):
        tiny=[f for f in bm.faces if f.calc_area()<=1e-10]
        if not tiny:break
        bmesh.ops.collapse(bm,edges=list({min(f.edges,key=lambda e:e.calc_length()) for f in tiny}),uvs=True)
    wire=[e for e in bm.edges if not e.link_faces]
    if wire:bmesh.ops.delete(bm,geom=wire,context='EDGES')
    loose=[v for v in bm.verts if not v.link_edges]
    if loose:bmesh.ops.delete(bm,geom=loose,context='VERTS')
    # Collapse can leave a closed two-face fragment with zero volume; exporters correctly reject its duplicate face.
    visited=set();flat=[]
    for face in bm.faces:
        if face in visited:continue
        group={face};visited.add(face);pending=[face]
        while pending:
            current=pending.pop()
            for e in current.edges:
                for other in e.link_faces:
                    if other not in visited:visited.add(other);group.add(other);pending.append(other)
        if len(group)==2 and len({frozenset(f.verts) for f in group})==1:flat.extend(group)
    if flat:bmesh.ops.delete(bm,geom=flat,context='FACES')
    report['flat_fragment_faces_removed']=len(flat)
    report['minimum_area']=min(f.calc_area() for f in bm.faces)
    report['remaining_edges']=[{'faces':len(e.link_faces),'length':e.calc_length()} for e in bm.edges if not e.is_manifold]
    assert all(e.is_manifold for e in bm.edges),report
    assert all(f.calc_area()>1e-10 for f in bm.faces),report
    report.update(nonmanifold_after=0,faces=len(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
    return report
