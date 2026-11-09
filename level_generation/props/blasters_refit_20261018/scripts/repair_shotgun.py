"""Replace Meshy's five-emitter fan with exactly seven physical flared emitters from the icon."""
import json
import math
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare_models import settle, close_remaining

P = Path(__file__).resolve().parents[1]


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = P / 'work/meshy/blastsg_raw.glb'
    bpy.ops.import_scene.gltf(filepath=str(source))
    obj = next(o for o in bpy.context.scene.objects if o.type == 'MESH')
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-6)
    cut = .333
    result = bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                                   dist=1e-7, plane_co=(0, cut, 0), plane_no=(0, 1, 0),
                                   clear_outer=True, clear_inner=False)
    boundary = [e for e in bm.edges if e.is_boundary]
    uv = bm.loops.layers.uv.active
    cap_flag = bm.faces.layers.int.new('authored_cut_cap')
    prior = {v: [l[uv].uv.copy() for l in v.link_loops] for v in bm.verts}
    caps = bmesh.ops.holes_fill(bm, edges=boundary, sides=0)['faces']
    for f in caps:
        f[cap_flag] = 1
        for loop in f.loops:
            loop[uv].uv = prior[loop.vert][0]
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    close_remaining(bm, uv, prior)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert not any(e.is_boundary for e in bm.edges)
    for face in bm.faces:
        for loop in face.loops:
            if face[cap_flag]:
                loop[uv].uv = (.16+loop.vert.co.x*.35, .06+loop.vert.co.z*.3)
            else:
                loop[uv].uv.y = .125+.875*loop[uv].uv.y
    bm.to_mesh(obj.data)
    bm.free()
    assert max(v.co.y for v in obj.data.vertices) < cut+1e-6
    mat = obj.data.materials[0]
    nodes = mat.node_tree.nodes
    # Imported glTF nodes retain role-specific names.
    shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    base = next(n for n in nodes if n.type == 'TEX_IMAGE' and n.image.colorspace_settings.name == 'sRGB')
    base.image = bpy.data.images.load(str(P / 'textures/shotgun_base.png'))
    for node in nodes:
        if node.type != 'TEX_IMAGE' or node == base:
            continue
        normal = any(link.to_node.type == 'NORMAL_MAP' for link in node.outputs['Color'].links)
        node.image = bpy.data.images.load(str(P / 'textures' / ('shotgun_normal.png' if normal else 'shotgun_mr.png')))
        node.image.colorspace_settings.name = 'Non-Color'
    parts, centres = [obj], []
    for number in range(7):
        i = number-3
        angle = math.radians(i*9)
        axis = Vector((math.sin(angle), math.cos(angle), 0))
        across = Vector((math.cos(angle), -math.sin(angle), 0))
        root = Vector((.012+i*.016, .326, .092))
        profile = [(0, .012), (.130, .018), (.132, .019), (.145, .019), (.145, .0155)]
        verts, coords, faces = [], [], []
        segments = 12
        for ring, (length, radius) in enumerate(profile):
            for k in range(segments):
                a = k*math.tau/segments
                verts.append(root+axis*length+across*(math.cos(a)*radius)+Vector((0, 0, math.sin(a)*radius)))
                coords.append((k/segments, ring/(len(profile)-1)))
        faces.append(tuple(reversed(range(segments))))
        cells = [0]
        for ring in range(len(profile)-1):
            for k in range(segments):
                j = (k+1) % segments
                faces.append((ring*segments+k, ring*segments+j, (ring+1)*segments+j, (ring+1)*segments+k))
                cells.append(0 if ring == 0 else 1)
        faces.append(tuple((len(profile)-1)*segments+k for k in range(segments)))
        cells.append(2)
        mesh = bpy.data.meshes.new(f'emitter_{number+1}')
        mesh.from_pydata(verts, [], faces)
        mesh.update()
        emitter = bpy.data.objects.new(mesh.name, mesh)
        bpy.context.collection.objects.link(emitter)
        mesh.materials.append(mat)
        layer = mesh.uv_layers.new(name='UVMap')
        for face, cell in zip(mesh.polygons, cells):
            face.use_smooth = len(face.vertices) == 4
            for loop_index in face.loop_indices:
                u, v = coords[mesh.loops[loop_index].vertex_index]
                layer.data[loop_index].uv = ((cell+.06+.88*u)/3, .012+.10*v)
        parts.append(emitter)
        centres.append(list(root+axis*.145))
    assert len(centres) == 7 and len({round(c[0], 4) for c in centres}) == 7
    bpy.ops.object.select_all(action='DESELECT')
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=list(bm.faces))
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    assert not any(e.is_boundary for e in bm.edges)
    bm.to_mesh(obj.data)
    bm.free()
    if obj.data.has_custom_normals:
        obj.data.normals_split_custom_set([(0, 0, 0)]*len(obj.data.loops))
    support = settle(obj)
    lo = Vector([min(v.co[a] for v in obj.data.vertices) for a in range(3)])
    hi = Vector([max(v.co[a] for v in obj.data.vertices) for a in range(3)])
    span = max(hi.x-lo.x, hi.y-lo.y)
    for v in obj.data.vertices:
        v.co = (v.co-Vector(((lo.x+hi.x)/2, (lo.y+hi.y)/2, lo.z)))/span
    assert not obj.data.validate(clean_customdata=False)
    bpy.ops.export_scene.gltf(filepath=str(source), export_format='GLB', use_selection=True, export_yup=True)
    receipt = {'emitters': 7, 'replaced_generated_emitters': 5, 'mouth_centres_before_grounding': centres,
               'triangles': len(obj.data.polygons), 'additional_support_rotation': support,
               'body_atlas_height': 896, 'bank_atlas_height': 128, 'material_draws': 1}
    (P / 'receipts/shotgun_bank.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print('SEVEN EMITTERS', receipt, flush=True)


if __name__ == '__main__':
    main()
