"""Export only owned character parts; keep editable topology, bind surface and sampled motion separate."""
import json
import math

import bpy
import bmesh
from mathutils import Vector, Matrix

from mesh_tools import ROOT
import motion


def audit():
    arm = bpy.data.objects['GB15 Goblin rig']
    report = {'blender': bpy.app.version_string, 'limit': 15000, 'joints': len(arm.data.bones), 'parts': []}
    graph = bpy.context.evaluated_depsgraph_get()
    for obj in bpy.data.collections['GB15 Character'].objects:
        if obj.type != 'MESH':
            continue
        evaluated = obj.evaluated_get(graph)
        evaluated.data.calc_loop_triangles()
        sums, influences = [], []
        for v in obj.data.vertices:
            weights = [(obj.vertex_groups[g.group].name, g.weight) for g in v.groups if g.weight > 1e-6]
            assert weights, (obj.name, v.index, 'unweighted')
            assert all(name in arm.data.bones for name, w in weights), (obj.name, weights)
            assert len(weights) <= 4, (obj.name, v.index, weights)
            total = sum(w for name, w in weights)
            assert abs(total - 1) < 1e-5, (obj.name, v.index, total)
            sums.append(total)
            influences.append(len(weights))
        uv = obj.data.uv_layers.active
        assert uv is not None
        assert all(math.isfinite(value) and -.00001 <= value <= 1.00001 for p in uv.data for value in p.uv)
        bm = bmesh.new(); bm.from_mesh(obj.data)
        invalid = sum(not e.is_manifold and not e.is_boundary for e in bm.edges)
        assert invalid == 0, (obj.name, 'non-manifold edges', invalid)
        boundary = sum(e.is_boundary for e in bm.edges)
        unused = sum(not v.link_faces for v in bm.verts)
        bm.free()
        assert unused == 0, (obj.name, 'unused vertices', unused)
        report['parts'].append({'name': obj.name, 'triangles': len(evaluated.data.loop_triangles),
                                'editable_vertices': len(obj.data.vertices), 'max_influences': max(influences),
                                'boundary_edges': boundary, 'uv_layer': uv.name})
    report['evaluated_triangles'] = sum(p['triangles'] for p in report['parts'])
    assert report['evaluated_triangles'] <= 15000
    (ROOT / 'delivery/blender_audit.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def selected(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]


def export():
    import roundtrip
    roundtrip.remove_import()
    output = ROOT / 'delivery'
    output.mkdir(exist_ok=True)
    arm = bpy.data.objects['GB15 Goblin rig']
    motion.activate('standing')
    report = audit()
    objects = list(bpy.data.collections['GB15 Character'].objects)
    selected(objects)
    common = dict(export_format='GLB', use_selection=True, use_active_scene=True, export_apply=True, export_texcoords=True,
                  export_normals=True, export_tangents=True, export_materials='EXPORT',
                  export_all_vertex_colors=False, export_yup=True, export_extras=True)
    bpy.ops.export_scene.gltf(filepath=str(output / 'mm6_goblin_rigged.glb'), **common,
                              export_skins=True, export_influence_nb=4, export_all_influences=False,
                              export_animations=True, export_animation_mode='ACTIONS',
                              export_rest_position_armature=True, export_frame_range=False,
                              export_force_sampling=True, export_frame_step=1, export_anim_single_armature=True)
    # Unrigged copy has the identical bind triangles/UVs, with the separate weapon parked beside the body.
    arm.data.pose_position = 'REST'
    bpy.context.view_layer.update()
    temporary = bpy.data.collections.new('GB15 Temporary texturing export')
    bpy.context.scene.collection.children.link(temporary)
    copies = []
    transforms = {}
    graph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type != 'MESH':
            continue
        data = bpy.data.meshes.new_from_object(obj.evaluated_get(graph), preserve_all_data_layers=True, depsgraph=graph)
        duplicate = bpy.data.objects.new(obj.name + ' texture handoff', data)
        temporary.objects.link(duplicate)
        duplicate['source_part'] = obj.name
        duplicate['gb_role'] = 'texturing_handoff'
        if obj.name == 'GB15 Curved sword':
            info = json.loads((ROOT / 'authoring/weapon.json').read_text())
            rotation = Vector(info['axis']).rotation_difference(Vector((0, 0, 1))).to_matrix().to_4x4()
            duplicate.matrix_world = Matrix.Translation(Vector((-.70, -.04, .75))) @ rotation @ \
                Matrix.Translation(-Vector(info['center']))
            transforms[obj.name] = [list(row) for row in duplicate.matrix_world]
        copies.append(duplicate)
    selected(copies)
    bpy.ops.export_scene.gltf(filepath=str(output / 'mm6_goblin_texturing.glb'), **common,
                              export_skins=False, export_animations=False)
    (output / 'texturing_transforms.json').write_text(json.dumps(transforms, indent=2) + '\n')
    for obj in copies:
        data = obj.data
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.meshes.remove(data)
    bpy.data.collections.remove(temporary)
    arm.data.pose_position = 'POSE'
    motion.activate('standing')
    selected([arm])
    bpy.ops.wm.save_as_mainfile(filepath=str(output / 'mm6_goblin_authored.blend'), compress=True)
    print('Exported', report['evaluated_triangles'], 'triangles;', report['joints'], 'joints')


if __name__ == '__main__':
    export()
