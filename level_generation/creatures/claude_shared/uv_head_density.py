"""Give head UV islands more texel density before packing (CLAUDE_CREATURE_TEXTURES.md, small creatures).

Run inside Blender after Smart UV Project and before pack_islands:
    scale_head_islands(mesh_object, ('Head', 'Ear_L', 'Ear_R'), factor=2.5)
An island counts as head when at least half of its UV area lies on faces whose vertices are mostly weighted to the
given groups; the whole island is scaled about its centre, so no island is torn. pack_islands then rescales all
islands uniformly, keeping the head islands `factor` times denser (linear) than the rest."""
import bmesh


def _head_faces(obj, mesh, groups):
    indices = {obj.vertex_groups[name].index for name in groups if name in obj.vertex_groups}
    if not indices:
        raise ValueError(f'none of the head groups {groups} exist on {obj.name}')
    head_weight = [sum(g.weight for g in vertex.groups if g.group in indices) for vertex in obj.data.vertices]
    return {face.index for face in mesh.faces
            if sum(head_weight[v.index] for v in face.verts) / len(face.verts) >= 0.5}


def scale_head_islands(obj, groups, factor=2.5):
    mesh = bmesh.from_edit_mesh(obj.data)
    mesh.faces.ensure_lookup_table()
    uv = mesh.loops.layers.uv.verify()
    head = _head_faces(obj, mesh, groups)

    # UV islands: faces joined across an edge whose two UV endpoints coincide on both sides.
    parent = list(range(len(mesh.faces)))

    def find(index):
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    def key(loop):
        value = loop[uv].uv
        return (round(value.x, 6), round(value.y, 6))

    for edge in mesh.edges:
        if len(edge.link_loops) != 2:
            continue
        first, second = edge.link_loops
        if {key(first), key(first.link_loop_next)} == {key(second), key(second.link_loop_next)}:
            a, b = find(first.face.index), find(second.face.index)
            if a != b:
                parent[a] = b

    islands = {}
    for face in mesh.faces:
        islands.setdefault(find(face.index), []).append(face)
    scaled = 0
    for faces in islands.values():
        areas = [face.calc_area() for face in faces]
        head_area = sum(area for face, area in zip(faces, areas) if face.index in head)
        if head_area < 0.5 * sum(areas):
            continue
        loops = [loop for face in faces for loop in face.loops]
        cx = sum(loop[uv].uv.x for loop in loops) / len(loops)
        cy = sum(loop[uv].uv.y for loop in loops) / len(loops)
        for loop in loops:
            loop[uv].uv.x = cx + (loop[uv].uv.x - cx) * factor
            loop[uv].uv.y = cy + (loop[uv].uv.y - cy) * factor
        scaled += 1
    bmesh.update_edit_mesh(obj.data)
    print(f'HEAD_UV islands scaled: {scaled} of {len(islands)}, head faces {len(head)}, factor {factor}')
    return scaled
