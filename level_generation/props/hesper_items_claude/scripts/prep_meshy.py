"""A downloaded Meshy Smart Topology model (meshy/meshy/<icon>_st_v1/*.glb) as a Hesper item model ready for
hes_texture.py: joined, welded, small loose crumbs dropped, turned into its resting pose (meshy_rest.json: `rot`
Euler degrees applied after import, the glTF's +Y up becoming Blender +Z), scaled so its longest horizontal side is
`length` world units, reduced to `tris` when larger, centred on its footprint with its lowest point at 0. Surface
classes are not known per face here: the object's one class is `auto`, which the bake resolves per texel from the
painted colour (hes_texture.py). A design with an `assembly` (a weapon sent to Meshy as a crop of its head or hilt)
gets its Blender part: the Meshy part, standing, is scaled to `part` units tall; `shaft` adds a dark shaft of `radius`
`rest` units long below it, with gold rings and a butt spike; `blade` adds a tapering emissive blade of `width`, `rest`
units long, above it; then the whole is laid along +Y. Writes work/<icon>.blend.
Usage: blender --background --python prep_meshy.py -- <icon> [icon ...]"""
import glob
import json
import math
import os
import sys

import bmesh
import bpy
from mathutils import Euler, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(HERE, 'work')
REST = json.load(open(os.path.join(HERE, 'meshy_rest.json')))


def class_material(name):
    if name not in bpy.data.materials:
        bpy.data.materials.new(name).use_nodes = True
    return bpy.data.materials[name]


def add_part(obj, bm, name):
    """Appends a bmesh part with surface class `name` to obj."""
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(class_material(name))
    part = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(part)
    for other in bpy.context.scene.objects:
        other.select_set(other in (obj, part))
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.join()


def cylinder(radius, z0, z1, sides=12, radius2=None):
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=radius,
                          radius2=radius if radius2 is None else radius2, depth=z1 - z0)
    bmesh.ops.translate(bm, vec=(0, 0, (z0 + z1) / 2), verts=bm.verts)
    return bm


def assemble(obj, spec):
    """The Blender half of a hybrid weapon (module docstring), in world units, then laid along +Y."""
    points = [v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    scale = spec['part'] / (hi.z - lo.z)
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in obj.data.vertices:
        v.co = (v.co - centre) * scale
    part = spec['part']
    if spec['kind'] == 'shaft':
        radius, length = max(spec['radius'], 1.8), spec['rest']
        add_part(obj, cylinder(radius, -length, part * 0.08, sides=10), 'resin')
        for k in range(1, 4):
            add_part(obj, cylinder(radius * 1.35, -length * k / 4 - 0.8, -length * k / 4 + 0.8, sides=10), 'gold')
        add_part(obj, cylinder(radius * 1.2, -length - 6, -length, sides=10, radius2=radius * 0.2), 'gold')
    else:
        width, length = spec['width'], spec['rest']
        bm = bmesh.new()
        base, tip = part * 0.9, part + length
        ring = [bm.verts.new((x * width / 2, y * width * 0.14, base)) for x, y in ((1, 0), (0, 1), (-1, 0), (0, -1))]
        corners = ((1, 0), (0, 1), (-1, 0), (0, -1))
        top = [bm.verts.new((x * width * 0.3, y * width * 0.1, tip - width)) for x, y in corners]
        point = bm.verts.new((0, 0, tip))
        bm.faces.new(ring[::-1])
        for j in range(4):
            k = (j + 1) % 4
            bm.faces.new((ring[j], ring[k], top[k], top[j]))
            bm.faces.new((top[j], top[k], point))
        add_part(obj, bm, 'glow')
    lay = Euler((math.radians(-90), 0, 0)).to_matrix().to_4x4()
    obj.data.transform(lay)


def prepare(icon):
    rest = REST[icon]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = sorted(glob.glob(os.path.join(HERE, 'meshy', 'meshy', f'{icon}_st_v*', '*.glb')))[-1]
    bpy.ops.import_scene.gltf(filepath=source)
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in bpy.context.scene.objects:
        o.select_set(o in meshes)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for other in list(bpy.context.scene.objects):
        if other != obj:
            bpy.data.objects.remove(other)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    # Drop loose crumbs: islands with under 1 % of the faces (meshy_rest.json `crumbs` sets another fraction).
    islands, seen = [], set()
    for face in bm.faces:
        if face.index in seen:
            continue
        stack, island = [face], []
        seen.add(face.index)
        while stack:
            current = stack.pop()
            island.append(current)
            for edge in current.edges:
                for other in edge.link_faces:
                    if other.index not in seen:
                        seen.add(other.index)
                        stack.append(other)
        islands.append(island)
    crumbs = [f for island in islands if len(island) < len(bm.faces) * rest.get('crumbs', 0.01) for f in island]
    bmesh.ops.delete(bm, geom=crumbs, context='FACES')
    bmesh.ops.transform(bm, matrix=Euler([math.radians(a) for a in rest.get('rot', (0, 0, 0))]).to_matrix().to_4x4(),
                        verts=bm.verts)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.materials.clear()
    obj.data.materials.append(class_material('auto'))
    if 'assembly' in rest:
        assemble(obj, rest['assembly'])
    points = [v.co for v in obj.data.vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    scale = rest['length'] / max(hi.x - lo.x, hi.y - lo.y)
    shift = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    for v in obj.data.vertices:
        v.co = (v.co - shift) * scale
    budget = rest.get('tris', 3000)
    obj.data.calc_loop_triangles()
    if len(obj.data.loop_triangles) > budget:
        modifier = obj.modifiers.new('decimate', 'DECIMATE')
        modifier.ratio = budget / len(obj.data.loop_triangles)
        modifier.use_collapse_triangulate = True
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.ops.object.shade_smooth_by_angle(angle=math.radians(40))
    obj.name = obj.data.name = icon
    os.makedirs(WORK, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(WORK, f'{icon}.blend'))
    obj.data.calc_loop_triangles()
    size = [round(v, 1) for v in (Vector([max(p[i] for p in (v.co for v in obj.data.vertices)) for i in range(3)])
                                  - Vector([min(p[i] for p in (v.co for v in obj.data.vertices)) for i in range(3)]))]
    print('PREPARED', icon, len(obj.data.loop_triangles), 'triangles, size', size, 'from', os.path.basename(source))


def main():
    for icon in sys.argv[sys.argv.index('--') + 1:]:
        prepare(icon)


main()
