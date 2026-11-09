"""One shared atlas, fixed export diagonals, and an optional source-normal proof."""
import json
import math
import traceback

import bpy
from mathutils import Vector

from mesh_tools import ROOT


def unwrap():
    import pose
    pose.reset()
    objects = [obj for obj in bpy.data.collections['GB15 Character'].objects if obj.type == 'MESH']
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(68), island_margin=.005,
                             area_weight=.25, correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    import uv_skin
    uv_skin.unwrap()
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode='OBJECT')
    inventory = []
    for obj in objects:
        mesh = obj.data
        uv = mesh.uv_layers.active.data
        parent = list(range(len(mesh.polygons)))

        def root(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        vertex_uv = {}
        for poly in mesh.polygons:
            for li in poly.loop_indices:
                key = (mesh.loops[li].vertex_index, round(uv[li].uv.x, 6), round(uv[li].uv.y, 6))
                if key in vertex_uv:
                    parent[root(poly.index)] = root(vertex_uv[key])
                else:
                    vertex_uv[key] = poly.index
        islands = {}
        for poly in mesh.polygons:
            islands.setdefault(root(poly.index), []).append(poly)
        for polys in islands.values():
            loops = [li for poly in polys for li in poly.loop_indices]
            positions = [mesh.vertices[mesh.loops[li].vertex_index].co for li in loops]
            centroid = sum(positions, Vector()) / len(positions)
            factor = 1.
            if obj.name == 'GB15 Skin body':
                if centroid.z > 1.44:
                    factor = 1.7
                elif abs(centroid.x) > .40 and centroid.z < .97:
                    factor = 1.4
            elif obj.name.startswith(('GB15 Eyes', 'GB15 Irises', 'GB15 Pupils', 'GB15 Teeth')):
                factor = 1.4
            center = sum((uv[li].uv.copy() for li in loops), Vector((0, 0))) / len(loops)
            for li in loops:
                uv[li].uv = center + (uv[li].uv - center) * factor
        inventory.append({'object': obj.name, 'islands': len(islands)})
        mesh.uv_layers.active.name = 'Goblin_Atlas_2K'
        mod = obj.modifiers.get('Fixed export triangulation') or obj.modifiers.new('Fixed export triangulation', 'TRIANGULATE')
        mod.quad_method = 'FIXED'
        mod.ngon_method = 'BEAUTY'
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, rotate_method='ANY', scale=True, margin_method='FRACTION',
                            margin=.004, shape_method='CONCAVE', merge_overlap=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    for obj in objects:
        obj['gb_uv'] = 'Shared non-overlapping 0–1 atlas, 2K, 8px nominal padding; face 1.7x linear density.'
    (ROOT / 'authoring/uv_inventory.json').write_text(json.dumps(inventory, indent=2) + '\n')
    print('UV charts', sum(row['islands'] for row in inventory))


def bake_proof():
    """Bake only the useful face/bare-torso source; hands and costume remain new plain surfaces."""
    output = ROOT / 'textures'
    output.mkdir(exist_ok=True)
    status = output / 'normal_proof_status.json'
    status.write_text(json.dumps({'state': 'scheduled'}))

    def run():
        scene = bpy.context.scene
        source = None
        old_engine = scene.render.engine
        try:
            import pose
            pose.reset()
            skin = bpy.data.objects['GB15 Skin body']
            original = bpy.data.objects['GB15 Dense shape guide'].data
            faces = []
            used = set()
            for poly in original.polygons:
                co = poly.center
                if co.z > 1.444 or (1.016 < co.z < 1.225 and abs(co.x) < .202):
                    face = tuple(poly.vertices)
                    faces.append(face)
                    used.update(face)
            ordered = sorted(used)
            indices = {old: new for new, old in enumerate(ordered)}
            mesh = bpy.data.meshes.new('GB15 temporary isolated bake guide')
            mesh.from_pydata([original.vertices[i].co for i in ordered], [],
                             [[indices[i] for i in face] for face in faces])
            mesh.update()
            for poly in mesh.polygons:
                poly.use_smooth = True
            source = bpy.data.objects.new('GB15 temporary isolated bake guide', mesh)
            bpy.data.collections['GB15 Reference'].objects.link(source)
            image = bpy.data.images.new('Goblin optional source normals 2K', width=2048, height=2048, alpha=False)
            image.colorspace_settings.name = 'Non-Color'
            for mat in skin.data.materials:
                for node in list(mat.node_tree.nodes):
                    if node.type == 'NORMAL_MAP' or (node.type == 'TEX_IMAGE' and node.name.startswith('Optional local')):
                        mat.node_tree.nodes.remove(node)
                node = mat.node_tree.nodes.new('ShaderNodeTexImage')
                node.name = 'Optional local sculpt normal proof'
                node.image = image
                mat.node_tree.nodes.active = node
            bpy.ops.object.select_all(action='DESELECT')
            skin.select_set(True)
            source.select_set(True)
            bpy.context.view_layer.objects.active = skin
            scene.render.engine = 'CYCLES'
            scene.cycles.samples = 1
            status.write_text(json.dumps({'state': 'baking', 'source_triangles': len(faces)}))
            bpy.ops.object.bake(type='NORMAL', normal_space='TANGENT', use_selected_to_active=True,
                                cage_extrusion=.027, max_ray_distance=.045, margin=8, margin_type='EXTEND',
                                use_clear=True)
            # Blend to a flat tangent normal where the new silhouette differs from the source.
            # This second Cycles bake stores the mask in the normal texture, not in a runtime shader.
            def smooth(a, b, x):
                t = max(0, min(1, (x - a) / (b - a)))
                return t * t * (3 - 2 * t)
            mask = skin.data.color_attributes.new(name='GB15 Temporary bake influence', type='FLOAT_COLOR', domain='POINT')
            for vertex in skin.data.vertices:
                x, y, z = vertex.co
                face_weight = smooth(1.451, 1.478, z) * (1 - smooth(1.652, 1.690, z)) * \
                    (1 - smooth(.073, .098, abs(x))) * (1 - smooth(-.02, .015, y))
                if abs(x) < .05 and 1.489 < z < 1.521:
                    face_weight *= .20
                torso_weight = smooth(1.029, 1.068, z) * (1 - smooth(1.19, 1.225, z)) * \
                    (1 - smooth(.13, .20, abs(x))) * (1 - smooth(-.01, .05, y))
                value = .80 * max(face_weight, torso_weight)
                mask.data[vertex.index].color = (value, value, value, 1)
            weighted = bpy.data.images.new('Goblin optional normals masked 2K', width=2048, height=2048, alpha=False)
            weighted.colorspace_settings.name = 'Non-Color'
            temporary_nodes = []
            for mat in skin.data.materials:
                nodes, links = mat.node_tree.nodes, mat.node_tree.links
                source_tex = next(n for n in nodes if n.type == 'TEX_IMAGE' and n.image == image)
                attr = nodes.new('ShaderNodeVertexColor'); attr.layer_name = mask.name
                blend = nodes.new('ShaderNodeMixRGB')
                blend.inputs[1].default_value = (.5, .5, 1, 1)
                links.new(attr.outputs['Color'], blend.inputs[0]); links.new(source_tex.outputs['Color'], blend.inputs[2])
                emission = nodes.new('ShaderNodeEmission'); links.new(blend.outputs[0], emission.inputs['Color'])
                out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
                links.new(emission.outputs[0], out.inputs['Surface'])
                target = nodes.new('ShaderNodeTexImage'); target.image = weighted; nodes.active = target
                temporary_nodes.append((mat, [attr, blend, emission, target]))
            source.select_set(False)
            bpy.ops.object.bake(type='EMIT', use_selected_to_active=False, margin=8, margin_type='EXTEND', use_clear=True)
            skin.data.color_attributes.remove(mask)
            for mat, nodes_to_remove in temporary_nodes:
                nodes, links = mat.node_tree.nodes, mat.node_tree.links
                shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
                out = next(n for n in nodes if n.type == 'OUTPUT_MATERIAL')
                links.new(shader.outputs[0], out.inputs['Surface'])
                for node in nodes_to_remove:
                    nodes.remove(node)
                next(n for n in nodes if n.type == 'TEX_IMAGE' and n.image == image).image = weighted
            image = weighted
            image.filepath_raw = str(output / 'goblin_optional_source_normal.png')
            image.file_format = 'PNG'
            image.save()
            image.pack()
            for mat in skin.data.materials:
                shader = next(n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
                texture = next(n for n in mat.node_tree.nodes if n.type == 'TEX_IMAGE' and n.image == image)
                normal = mat.node_tree.nodes.new('ShaderNodeNormalMap')
                normal.inputs['Strength'].default_value = 1.0
                mat.node_tree.links.new(texture.outputs['Color'], normal.inputs['Color'])
                mat.node_tree.links.new(normal.outputs['Normal'], shader.inputs['Normal'])
            status.write_text(json.dumps({'state': 'complete', 'source_triangles': len(faces),
                                          'scope': 'Optional normal proof only; no final albedo/roughness textures.'}))
        except Exception:
            status.write_text(json.dumps({'state': 'error', 'traceback': traceback.format_exc()}))
        finally:
            scene.render.engine = old_engine
            if source:
                mesh = source.data
                bpy.data.objects.remove(source, do_unlink=True)
                bpy.data.meshes.remove(mesh)
        return None

    bpy.app.timers.register(run, first_interval=.2)
    print('Scheduled isolated normal proof')
