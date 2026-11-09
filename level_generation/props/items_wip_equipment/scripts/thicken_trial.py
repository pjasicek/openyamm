"""Add clamped physical thickness to open item surfaces; preserve closed hardware."""
import json
from pathlib import Path
import sys

import bmesh
import bpy
from mathutils import Vector

project = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project / '../projectiles_claude/scripts'))
import projlib as pl

def thicken(obj, thickness=0.004, lining=None):
    assert 0 < thickness <= 0.02
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    seen, open_faces = set(), []
    for face in bm.faces:
        if face in seen:
            continue
        stack, component = [face], []
        seen.add(face)
        while stack:
            current = stack.pop()
            component.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other not in seen:
                        seen.add(other)
                        stack.append(other)
        if any(edge.is_boundary for face in component for edge in face.edges):
            open_faces.extend(component)
    assert open_faces, obj.name
    for face in bm.faces:
        face.select_set(False)
    for face in open_faces:
        face.select_set(True)
    bm.to_mesh(obj.data)
    bm.free()
    existing = set(bpy.data.objects)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.separate(type='SELECTED')
    bpy.ops.object.mode_set(mode='OBJECT')
    shell = next(other for other in bpy.data.objects if other not in existing and other.type == 'MESH')
    bpy.context.view_layer.objects.active = shell
    if lining:
        assert lining['kind'] in ('leather', 'cloth') and len(shell.data.materials) == 1
        colour = lining['colour']
        assert len(colour) == 3 and all(0 <= value <= 1 for value in colour)
        material = bpy.data.materials.new('physical_' + lining['kind'] + '_lining')
        material.use_nodes = True
        shader = next(node for node in material.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
        shader.inputs['Base Color'].default_value = (*colour, 1)
        shader.inputs['Metallic'].default_value = 0
        shader.inputs['Roughness'].default_value = 0.6 if lining['kind'] == 'leather' else 0.85
        shell.data.materials.append(material)
    modifier = shell.modifiers.new('Physical surface thickness', 'SOLIDIFY')
    modifier.thickness = thickness
    modifier.offset = 0
    modifier.use_even_offset = False
    modifier.thickness_clamp = 1
    if lining:
        modifier.material_offset = 1
        modifier.material_offset_rim = 1
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    if len(obj.data.polygons):
        for other in bpy.context.scene.objects:
            other.select_set(other in [obj, shell])
        bpy.ops.object.join()
    else:
        bpy.data.objects.remove(obj)
    obj = shell
    obj.data.calc_loop_triangles()
    before = len(obj.data.loop_triangles)
    if before > 3500:
        modifier = obj.modifiers.new('Silhouette budget', 'DECIMATE')
        modifier.ratio = 3200 / before
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    low = Vector([min(vertex.co[i] for vertex in obj.data.vertices) for i in range(3)])
    high = Vector([max(vertex.co[i] for vertex in obj.data.vertices) for i in range(3)])
    shift = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    for vertex in obj.data.vertices:
        vertex.co -= shift
    obj.data.calc_loop_triangles()
    assert len(obj.data.loop_triangles) <= 3500 and obj.data.uv_layers
    print('PHYSICAL_THICKNESS', 'thick faces', before, 'reduced', len(obj.data.loop_triangles), flush=True)
    return obj


def main():
    pl.WORK = str(project / 'work/codex_tex')
    designs = json.loads((project / 'designs.json').read_text())
    for name in sys.argv[sys.argv.index('--') + 1:]:
        assert name in designs
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(Path(pl.WORK) / f'{name}_export.glb'))
        obj = next(obj for obj in bpy.context.scene.objects if obj.type == 'MESH')
        obj = thicken(obj)
        pl.export(obj, name + '_thickness_trial')


if __name__ == '__main__':
    main()
