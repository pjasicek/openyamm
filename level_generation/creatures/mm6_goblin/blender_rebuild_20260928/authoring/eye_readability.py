"""Refine the existing eye surfaces for legible gold irises at full-figure scale."""
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

from mesh_tools import ROOT


def apply():
    folder = ROOT / 'review/eye_readability'
    baseline = folder / 'before/eye_vertices.json'
    names = ['GB15 Irises', 'GB15 Pupils']
    if not baseline.exists():
        baseline.write_text(json.dumps({name: [list(v.co) for v in bpy.data.objects[name].data.vertices]
                                        for name in names}, indent=2) + '\n')
    original = json.loads(baseline.read_text())
    globe = bpy.data.objects['GB15 Eyes'].data
    surface = BVHTree.FromPolygons([v.co for v in globe.vertices], [p.vertices[:] for p in globe.polygons])
    clearances = {}
    for name, factor in zip(names, [1.5, 1.55]):
        mesh = bpy.data.objects[name].data
        assert len(mesh.vertices) == len(original[name])
        for vertex, point in zip(mesh.vertices, original[name]):
            center_x = .0425 if point[0] > 0 else -.0425
            x = center_x + (point[0] - center_x) * factor
            z = 1.563 + (point[2] - 1.563) * factor
            hit, normal, index, distance = surface.ray_cast(Vector((x, -.3, z)), Vector((0, 1, 0)))
            assert hit is not None, (name, vertex.index)
            vertex.co = (x, hit.y - .00018, z)
        mesh.update()
        # A triangle fan can fall below the curved underlying surface between its vertices.
        # Measure that gap before placing the next layer, preserving this mesh's topology.
        mesh.calc_loop_triangles()
        extra = 0.
        for triangle in mesh.loop_triangles:
            a, b, c = [mesh.vertices[i].co.copy() for i in triangle.vertices]
            for i in range(17):
                for j in range(17 - i):
                    point = a + (b - a) * (i / 16) + (c - a) * (j / 16)
                    hit = surface.ray_cast(Vector((point.x, -.3, point.z)), Vector((0, 1, 0)))[0]
                    assert hit is not None
                    extra = max(extra, point.y - hit.y + .00018)
        for vertex in mesh.vertices:
            vertex.co.y -= extra + .00005
        mesh.update()
        clearances[name] = extra + .00005
        # Fit the pupil to the revised iris fan, keeping its entire surface above it.
        surface = BVHTree.FromPolygons([v.co for v in mesh.vertices], [p.vertices[:] for p in mesh.polygons])
    settings = [
        ('GB15 Eyes restored', (.115, .13, .045, 1), .30),
        ('GB15 Amber irises restored', (.58, .32, .015, 1), .25),
        ('GB15 Pupils restored', (.001, .0015, .0007, 1), .20),
    ]
    for name, color, roughness in settings:
        material = bpy.data.materials[name]
        shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        shader.inputs['Base Color'].default_value = color
        shader.inputs['Roughness'].default_value = roughness
        material.diffuse_color = color
        material['gb_eye_readability'] = 'eye_readability_6'
    bpy.data.scenes['MM6 Goblin - Authored 15K']['gb_eye_readability_revision'] = 'eye_readability_6'
    bpy.context.view_layer.update()
    (folder / 'settings.json').write_text(json.dumps({
        'revision': 'eye_readability_6', 'iris_radius_scale': 1.5, 'pupil_radius_scale': 1.55,
        'surface_fit': 'Iris to eyeball; pupil to iris; interior fan clearance sampled before fitting next layer.',
        'additional_fan_clearance_m': clearances,
        'materials': {name: {'base_color_linear': color, 'roughness': roughness}
                      for name, color, roughness in settings},
        'new_triangles': 0, 'uvs_weights_actions_atlas_maps_unchanged': True}, indent=2) + '\n')
    print('Updated two eye surfaces and three eye materials; topology and UVs retained.')
