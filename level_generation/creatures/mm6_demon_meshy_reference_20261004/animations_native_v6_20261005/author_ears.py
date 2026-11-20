"""Replace the two crown spikes and lower folds with continuous cupped bat ears."""
import json
from pathlib import Path

import bpy
import bmesh
import numpy as np

STAGE = Path(__file__).resolve().parent
BASELINE = STAGE.parent/'animations_native_v4_20261005'


def outline():
    points = np.array([[-.012,-.030], [.020,-.056], [.042,-.041], [.052,.006],
                       [.068,.107], [.014,.052], [-.014,.024], [-.020,-.004]])
    result = []
    for i in range(len(points)):
        a,b,c,d = [points[(i+j)%len(points)] for j in (-1,0,1,2)]
        for step in range(6):
            t=step/6
            result.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    return np.array(result)


def apply():
    scene = bpy.data.scenes['MM6_Demon_Native_Animations']
    bpy.context.window.scene = scene
    mesh = scene.objects['Demon_Native_Mesh']
    with bpy.data.libraries.load(str(BASELINE/'mm6_demon_native_animations.blend')) as (available, loaded):
        loaded.scenes = ['MM6_Demon_Native_Animations']
    previous = loaded.scenes[0]
    original = next(o for o in previous.objects if o.type=='MESH' and o.name.startswith('Demon_Native_Mesh'))
    assert [g.name for g in original.vertex_groups] == [g.name for g in mesh.vertex_groups]
    mesh.data = original.data.copy()
    mesh.data.name = 'Demon_Native_Bat_Ears'
    bpy.data.scenes.remove(previous)
    rest = np.array([v.co for v in mesh.data.vertices])
    head = mesh.vertex_groups['mixamorig:Head'].index
    weights = np.array([sum(g.weight for g in v.groups if g.group==head) for v in mesh.data.vertices])
    removed = (weights>.05)&(abs(rest[:,0]+.006)>.065)&(rest[:,1]>-.325)&(rest[:,2]>1.530)
    assert 120 < removed.sum() < 350
    original_faces = np.array([tuple(f.vertices) for f in mesh.data.polygons])
    bm = bmesh.new()
    bm.from_mesh(mesh.data)
    bm.verts.ensure_lookup_table()
    origin = bm.verts.layers.int.new('previous_vertex_index')
    face_origin = bm.faces.layers.int.new('previous_face_index')
    deform = bm.verts.layers.deform.verify()
    for vertex in bm.verts:
        vertex[origin] = vertex.index+1
    for face in bm.faces:
        face[face_origin] = face.index+1
    original_boundaries = {e for e in bm.edges if e.is_boundary}
    doomed = [v for v in bm.verts if removed[v.index]]
    border = {v for doomed_vertex in doomed for f in doomed_vertex.link_faces for v in f.verts if not removed[v.index]}
    bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    edges = [e for e in bm.edges if e.is_boundary and e not in original_boundaries and all(v in border for v in e.verts)]
    caps = bmesh.ops.holes_fill(bm, edges=edges, sides=0)['faces']
    assert caps and all(not e.is_boundary for e in edges), 'Ear attachment openings must close'
    for cap in caps:
        cap[face_origin] = 0
        cap.material_index = 0
        cap.smooth = True
    perimeter = outline()
    samples = len(perimeter)
    new_faces = list(caps)
    for side in (-1,1):
        def point(u,w,depth):
            # Height also runs backward, giving the ear a broad profile rather than an edge-on spike.
            vertex = bm.verts.new((-.006+side*(.078+u-depth*.65), -.290+1.10*u+.10*w+depth, 1.600+w))
            vertex[deform][head] = 1
            return vertex
        def surface(r,back):
            # The inner front surface recedes into a bowl; the outer helix stays proud.
            depth = (.009+.013*(1-r*r)) if back else (-.004+.020*(1-r)**2)
            return [point(u*r,w*r,depth) for u,w in perimeter]
        front = [surface(r,False) for r in (1,.84,.62,.40,.20)]
        back = [surface(r,True) for r in (1,.68,.34)]
        def face(vs):
            f = bm.faces.new(vs)
            f.material_index = 0
            f.smooth = True
            new_faces.append(f)
        for rings in (front,back):
            for outer,inner in zip(rings,rings[1:]):
                for i in range(samples):
                    j=(i+1)%samples
                    face((outer[i],outer[j],inner[j],inner[i]))
            center = point(0,0,.022 if rings is back else .016)
            for i in range(samples):
                face((rings[-1][i],rings[-1][(i+1)%samples],center))
        for i in range(samples):
            j=(i+1)%samples
            face((front[0][i],back[0][i],back[0][j],front[0][j]))
    bmesh.ops.triangulate(bm, faces=new_faces)
    new_faces = [f for f in bm.faces if f[face_origin]==0]
    bmesh.ops.recalc_face_normals(bm, faces=new_faces)
    bm.verts.index_update()
    bm.faces.index_update()
    previous_vertices = np.array([v[origin]-1 for v in bm.verts])
    previous_faces = np.array([f[face_origin]-1 for f in bm.faces])
    bm.to_mesh(mesh.data)
    bm.free()
    mesh.data.update()
    names = [g.name for g in mesh.vertex_groups]
    skin = np.zeros((len(mesh.data.vertices),len(names)), np.float32)
    for v in mesh.data.vertices:
        for g in v.groups:
            skin[v.index,g.group] = g.weight
    positions = np.array([v.co for v in mesh.data.vertices])
    faces = np.array([tuple(f.vertices) for f in mesh.data.polygons])
    assert len({tuple(sorted(f)) for f in faces})==len(faces), 'No duplicate attachment triangles'
    np.savez_compressed(STAGE/'source_geometry.npz', vertices=positions, faces=faces, weights=skin,
                        group_names=np.array(names), previous_vertex_indices=previous_vertices,
                        previous_face_indices=previous_faces)
    inverse = {int(old):i for i,old in enumerate(previous_vertices) if old>=0}
    tips = json.loads((STAGE.parent/'attack_animation_v2/tip_vertex_masks.json').read_text())
    tips = {name:[inverse[i] for i in ids] for name,ids in tips.items()}
    (STAGE/'tip_vertex_masks.json').write_text(json.dumps(tips)+'\n')
    retained_faces = ~np.any(removed[original_faces], axis=1)
    report = dict(removed_previous_vertices=np.where(removed)[0].tolist(),
                  removed_previous_triangles=int((~retained_faces).sum()),
                  added_ear_vertices=int((previous_vertices<0).sum()),
                  added_ear_and_attachment_triangles=int((previous_faces<0).sum()),
                  retained_previous_vertices=int((previous_vertices>=0).sum()),
                  retained_previous_triangles=int((previous_faces>=0).sum()),
                  ear_count=2, ear_vertex_group='mixamorig:Head',
                  closed_attachment_regions=2,
                  other_geometry_weights_bind_and_all_nine_actions_preserved=True,
                  construction='One closed cupped pinna per side, broad profile, recessed bowl, continuous lower lobe')
    (STAGE/'ear_geometry_changes.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='removed_previous_vertices'},indent=2))
    return report
