"""Copy of mm8_m600_claude/scripts/build_lods.py (bent-stalk LOD pass, rigid eyes protected) with ratios rescaled for the
8,792-triangle LOD0: 0.65 / 0.50 / 0.40 (LOD3 about the installed LOD3 count; the 2,124 protected eye triangles
left LOD3 at 0.22 almost no body: it lost half its length; 0.40 / 0.33 lost the teeth and streaked the base)
run on the reduced LOD0: work/r55_lod0.glb -> work/r55_lods.glb (lods.json beside it). Usage: blender -b -P build_lods.py"""
import sys,copy,json,struct
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parents[2]/'tools'))
from build_actor_lods import read_glb,write_glb,accessor_bytes,append_accessor,merge_shadow,weld_skin_seams
def generate(source, destination, node_name, ratios=(0.5, 0.18, 0.06), max_influences=8, protected_points=(),
             material_ratios=None):
    import bpy
    import bmesh
    from mathutils import Matrix
    from mathutils.kdtree import KDTree
    protected = KDTree(len(protected_points)) if len(protected_points) else None
    if protected is not None:
        for index, point in enumerate(protected_points):
            protected.insert(point, index)
        protected.balance()
    before, original = read_glb(source)
    node = next(n for n in before['nodes'] if n.get('name') == node_name)
    mesh_index = node['mesh']
    if before['meshes'][mesh_index].get('extras', {}).get('openyamm_lods'):
        raise ValueError('Generate from the original level-zero runtime export')
    joint_names = [before['nodes'][i]['name'] for i in before['skins'][node['skin']]['joints']]
    bind_matrices = list(struct.iter_unpack('<16f', accessor_bytes(
        before, original, before['skins'][node['skin']]['inverseBindMatrices'])))
    bpy.ops.import_scene.gltf(filepath=str(source))
    body = bpy.data.objects[node_name]
    armature = next(m.object for m in body.modifiers if m.type == 'ARMATURE')
    armature.animation_data_clear()
    for bone in armature.pose.bones:
        bone.matrix_basis = Matrix.Identity(4)
    objects = []
    budgets = material_ratios or {}
    if set(budgets) - {material.name for material in body.data.materials}:
        raise ValueError('LOD budget names an unknown material')
    for budget in (ratios, *budgets.values()):
        if len(budget) != 3 or not 1 > budget[0] > budget[1] > budget[2] > 0:
            raise ValueError('Choose three decreasing LOD ratios between zero and one')
    for level in range(1, 4):
        for slot in range(len(body.data.materials)):
            obj = body.copy(); obj.data = body.data.copy(); obj.animation_data_clear()
            obj.name = f'LOD{level}_{slot}'
            bpy.context.collection.objects.link(obj)
            bm = bmesh.new(); bm.from_mesh(obj.data)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index != slot], context='FACES')
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
            # glTF splits vertices at UV/normal seams. Decimate the connected surface;
            # BMesh keeps the distinct per-corner UVs when joining coincident vertices.
            weld_skin_seams(bm)
            faces = len(bm.faces)
            bm.to_mesh(obj.data); bm.free()
            if not faces:
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            # Reduce with each stalk curved so longitudinal rings survive; carry rest coordinates through collapse.
            rest=np.array([v.co[:] for v in obj.data.vertices])
            carried=obj.data.attributes.new('rest_co','FLOAT_VECTOR','POINT')
            carried.data.foreach_set('vector',rest.ravel())
            for bone in armature.pose.bones:
                if bone.name.startswith(('Neck','Eye')) and not bone.name.endswith('Tip'):
                    bone.rotation_mode='XYZ';bone.rotation_euler=(.20,.12,0)
            bpy.context.view_layer.update()
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());posed=ev.to_mesh()
            bent=np.array([v.co[:] for v in posed.vertices]);ev.to_mesh_clear()
            assert len(bent)==len(rest)
            for bone in armature.pose.bones:bone.matrix_basis=Matrix.Identity(4)
            obj.data.vertices.foreach_set('co',bent.ravel());obj.data.update()
            modifier = obj.modifiers.new('Offline_LOD', 'DECIMATE')
            slot_ratio = budgets.get(body.data.materials[slot].name, ratios)[level - 1]
            modifier.ratio = min(1.0, max(24 / faces, slot_ratio))
            modifier.use_collapse_triangulate = True
            allowance_name = None
            contact_weights = {}
            if protected is not None:
                # Preserve authored contact vertices in model-space Z-up coordinates.
                allowance = obj.vertex_groups.new(name='LOD_ReductionAllowance')
                allowance.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
                for vertex in obj.data.vertices:
                    _, point_index, distance = protected.find(obj.matrix_world @ vertex.co)
                    if distance < 1e-5:
                        weights = {g.group: g.weight for g in vertex.groups if g.group != allowance.index}
                        if point_index in contact_weights and contact_weights[point_index] != weights:
                            raise ValueError('A protected contact identifies different skin weights')
                        contact_weights[point_index] = weights
                        allowance.add([vertex.index], 0.0, 'REPLACE')
                modifier.vertex_group = allowance.name
                modifier.vertex_group_factor = 1.0
                allowance_name = allowance.name
            if allowance_name is None:
                # Small eyes must retain their spherical surface and iris UVs at distance.
                allowance = obj.vertex_groups.new(name='LOD_ReductionAllowance')
                allowance.add(list(range(len(obj.data.vertices))), 1.0, 'REPLACE')
                eye_groups = {g.index for g in obj.vertex_groups
                              if g.name.startswith('EmbeddedEye') or (g.name.startswith('Eye') and g.name.endswith('_Tip'))}
                protected_eyes = [v.index for v in obj.data.vertices
                                  if any(g.group in eye_groups and g.weight > .999 for g in v.groups)]
                assert len(protected_eyes) > 500
                allowance.add(protected_eyes, 0.0, 'REPLACE')
                modifier.vertex_group = allowance.name
                modifier.vertex_group_factor = 1.0
            while obj.modifiers[0] != modifier:
                bpy.ops.object.modifier_move_up(modifier=modifier.name)
            bpy.ops.object.modifier_apply(modifier=modifier.name)
            restored=np.zeros(len(obj.data.vertices)*3)
            obj.data.attributes['rest_co'].data.foreach_get('vector',restored)
            obj.data.vertices.foreach_set('co',restored)
            obj.data.attributes.remove(obj.data.attributes['rest_co']);obj.data.update()
            if allowance_name is None:
                obj.vertex_groups.remove(obj.vertex_groups["LOD_ReductionAllowance"])
            if allowance_name is not None:
                obj.vertex_groups.remove(obj.vertex_groups[allowance_name])
                found = set()
                for vertex in obj.data.vertices:
                    _, point_index, distance = protected.find(obj.matrix_world @ vertex.co)
                    if distance < 1e-5 and point_index in contact_weights:
                        for group in list(vertex.groups):
                            obj.vertex_groups[group.group].remove([vertex.index])
                        for group, weight in contact_weights[point_index].items():
                            obj.vertex_groups[group].add([vertex.index], weight, 'REPLACE')
                        found.add(point_index)
                if found != contact_weights.keys():
                    raise ValueError('LOD reduction moved a protected contact')
            # Collapsing vertices combines joint sets; preserve the requested influence budget.
            bpy.ops.object.vertex_group_limit_total(limit=max_influences)
            bpy.ops.object.vertex_group_normalize_all(lock_active=False)
            objects.append(obj)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects + [armature]: obj.select_set(True)
    temporary = destination.with_suffix('.geometry.glb')
    bpy.ops.export_scene.gltf(filepath=str(temporary), use_selection=True, export_format='GLB',
        export_animations=False, export_skins=True, export_all_influences=True)
    exported, payload = read_glb(temporary)
    document = copy.deepcopy(before); binary = bytearray(original)
    material_indices = {m['name']: i for i, m in enumerate(document['materials'])}
    lod_indices = []
    for level in range(1, 4):
        mesh = {'name': f'{node_name}_LOD{level}', 'primitives': []}
        for lower_node in exported['nodes']:
            if not lower_node.get('name', '').startswith(f'LOD{level}_') or 'mesh' not in lower_node:
                continue
            # Names identify joints; exporting a selected armature can change their glTF order.
            skin = exported['skins'][lower_node['skin']]
            remap = [joint_names.index(exported['nodes'][i]['name']) for i in skin['joints']]
            matrices = list(struct.iter_unpack('<16f', accessor_bytes(exported, payload, skin['inverseBindMatrices'])))
            if any(abs(a - b) > 1e-4 for index, matrix in zip(remap, matrices)
                   for a, b in zip(bind_matrices[index], matrix)):
                raise ValueError('Blender changed the LOD bind space')
            for key, default in [('translation', [0, 0, 0]), ('rotation', [0, 0, 0, 1]), ('scale', [1, 1, 1])]:
                if any(abs(a - b) > 1e-4 for a, b in zip(node.get(key, default), lower_node.get(key, default))):
                    raise ValueError('Blender changed the LOD mesh transform')
            for primitive in exported['meshes'][lower_node['mesh']]['primitives']:
                attributes = {}
                for semantic, index in primitive['attributes'].items():
                    accessor = exported['accessors'][index]
                    packed = accessor_bytes(exported, payload, index)
                    if semantic.startswith('JOINTS_'):
                        code = {5121: 'B', 5123: 'H'}[accessor['componentType']]
                        values = [remap[v[0]] for v in struct.iter_unpack('<' + code, packed)]
                        packed = struct.pack('<' + code * len(values), *values)
                    attributes[semantic] = append_accessor(document, binary, accessor, packed)
                index = primitive['indices']
                mesh['primitives'].append({'attributes': attributes,
                    'indices': append_accessor(document, binary, exported['accessors'][index],
                                               accessor_bytes(exported, payload, index)),
                    'material': material_indices[exported['materials'][primitive['material']]['name']]})
        if not mesh['primitives']:
            raise ValueError('Blender did not export the selected LOD')
        lod_indices.append(len(document['meshes'])); document['meshes'].append(mesh)
    shadows = []
    for index in [mesh_index] + lod_indices:
        shadow = merge_shadow(document, binary, document['meshes'][index])
        shadows.append(len(document['meshes'])); document['meshes'].append(shadow)
    document['meshes'][mesh_index].setdefault('extras', {}).update(
        openyamm_lods=lod_indices, openyamm_shadow_lods=shadows)
    counts = [sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][i]['primitives'])
              for i in [mesh_index] + lod_indices]
    if not all(a > b for a, b in zip(counts, counts[1:])):
        raise ValueError('LOD triangle counts must decrease')
    write_glb(destination, document, binary)
    (destination.parent / 'lods.json').write_text(json.dumps({'triangles': counts, 'colour_meshes': [mesh_index] + lod_indices,
        'shadow_meshes': shadows, 'source': str(source), 'destination': str(destination),
        'original_geometry_rig_clips_images_retained': True}, indent=2) + '\n')
    print('LOD triangles:', counts)


generate(P/'work/r55_lod0.glb',P/'work/r55_lods.glb','Nightmare',ratios=(.65,.50,.40),max_influences=4)
