"""FD-04's lizard, stage 2 (Blender): MM8's Thunder Lizard (mm8_m516) posed from one clip frame, each of its four LOD
meshes baked into a static mesh, scaled to the decoration's size, feet on z 0, with plain PBR materials from
scripts/textures.py (skin A baked). Writes work/xeen_deco_lizard_raw.glb (LOD nodes for link_static_model_lods.py) and,
with --preview, work/preview_<tag>.png renders.
Usage: blender -b --python build.py -- <action> <frame> <height_units> [--preview <tag>] [--no-export]"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'level_generation/decorations/xeen_sleeper_claude/scripts'))
import posing  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
action, frame, height = argv[0], float(argv[1]), float(argv[2])
preview = argv[argv.index('--preview') + 1] if '--preview' in argv else None
work = os.path.join(PROJECT, 'work')
tex = os.path.join(work, 'tex')

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(work, 'm516_lods.glb'))
scene = bpy.context.scene
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
if arm.animation_data is None:
    arm.animation_data_create()
posing.apply_pose(arm, {'base': [action, frame]})
LODS = {'Body': 0, 'Lizard_LOD1': 1, 'Lizard_LOD2': 2, 'Lizard_LOD3': 3}
dg = bpy.context.evaluated_depsgraph_get()
bodies = {}
for o in list(scene.objects):
    if o.type == 'MESH' and o.name in LODS:
        ev = o.evaluated_get(dg)
        me = bpy.data.meshes.new_from_object(ev, preserve_all_data_layers=True, depsgraph=dg)
        me.transform(o.matrix_world)
        bodies[LODS[o.name]] = me
assert sorted(bodies) == [0, 1, 2, 3], sorted(bodies)
for o in list(scene.objects):
    bpy.data.objects.remove(o, do_unlink=True)

co0 = [v.co for v in bodies[0].vertices]
lo = Vector([min(c[i] for c in co0) for i in range(3)])
hi = Vector([max(c[i] for c in co0) for i in range(3)])
s = (height / 100.0) / (hi.z - lo.z)
xf = Matrix.Scale(s, 4) @ Matrix.Translation((0, 0, -lo.z))
for me in bodies.values():
    me.transform(xf)


def material(key):
    m = bpy.data.materials.new(f'lizard_body{key}')
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED')

    def img(path, colour):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = bpy.data.images.load(path)
        n.image.colorspace_settings.name = 'sRGB' if colour else 'Non-Color'
        return n
    nt.links.new(img(os.path.join(tex, f'set{key}_A_basecolor.png'), True).outputs['Color'], bsdf.inputs['Base Color'])
    mr = img(os.path.join(tex, f'set{key}_mr.png'), False)
    sep = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(mr.outputs['Color'], sep.inputs['Color'])
    nt.links.new(sep.outputs['Green'], bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = 0.0
    nm = nt.nodes.new('ShaderNodeNormalMap')
    nt.links.new(img(os.path.join(tex, f'set{key}_normal.png'), False).outputs['Color'], nm.inputs['Color'])
    nt.links.new(nm.outputs['Normal'], bsdf.inputs['Normal'])
    m.use_backface_culling = False
    return m


mats = {k: material(k) for k in ('0', '2', '3')}
objs = []
counts = []
for lod in range(4):
    me = bodies[lod]
    me.materials.clear()
    me.materials.append(mats['0' if lod < 2 else str(lod)])
    for p in me.polygons:
        p.material_index = 0
    name = 'xeen_lizard' if lod == 0 else f'xeen_lizard_LOD{lod}'
    me.name = name
    ob = bpy.data.objects.new(name, me)
    scene.collection.objects.link(ob)
    for a in [a for a in me.attributes if a.name.startswith('Col')]:
        me.attributes.remove(a)
    while len(me.uv_layers) > 1:
        me.uv_layers.remove(me.uv_layers[-1])
    counts.append(sum(len(p.vertices) - 2 for p in me.polygons))
    objs.append(ob)
co = [v.co for v in objs[0].data.vertices]
lo = [min(c[i] for c in co) * 100 for i in range(3)]
hi = [max(c[i] for c in co) * 100 for i in range(3)]
info = {'action': action, 'frame': frame, 'lod_triangles': counts, 'bounds_units': [lo, hi]}
print('INFO', json.dumps(info))

if preview:
    for ob in objs[1:]:
        ob.hide_render = True
    cam_data = bpy.data.cameras.new('cam')
    cam = bpy.data.objects.new('cam', cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sun = bpy.data.objects.new('sun', bpy.data.lights.new('sun', 'SUN'))
    sun.data.energy = 4
    sun.rotation_euler = (math.radians(50), 0, math.radians(30))
    scene.collection.objects.link(sun)
    scene.world = bpy.data.worlds.new('w')
    scene.world.color = (0.25, 0.25, 0.27)
    scene.render.engine = 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [
        e.identifier for e in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
    scene.render.resolution_x, scene.render.resolution_y = 640, 480
    c = Vector([(lo[i] + hi[i]) / 200 for i in range(3)])
    r = max(hi[i] - lo[i] for i in range(3)) / 100 * 1.6
    for tag, az, el in (('q', 35, 15), ('side', 90, 5), ('front', 0, 5), ('high', 30, 40)):
        # glTF +Z is the creature's front; in Blender (Z up) that is -Y
        d = Vector((math.sin(math.radians(az)) * math.cos(math.radians(el)),
                    -math.cos(math.radians(az)) * math.cos(math.radians(el)), math.sin(math.radians(el))))
        cam.location = c + d * r
        cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = os.path.join(work, f'preview_{preview}_{tag}.png')
        bpy.ops.render.render(write_still=True)
    for ob in objs[1:]:
        ob.hide_render = False
    bpy.data.objects.remove(cam, do_unlink=True)
    bpy.data.objects.remove(sun, do_unlink=True)

if '--no-export' not in argv:
    json.dump(info, open(os.path.join(work, 'lods.json'), 'w'), indent=1)
    for o in scene.objects:
        o.select_set(o in objs)
    bpy.context.view_layer.objects.active = objs[0]
    out = os.path.join(work, 'xeen_deco_lizard_raw.glb')
    bpy.ops.export_scene.gltf(filepath=out, use_selection=True, export_format='GLB', export_yup=True,
                              export_extras=True, export_normals=True, export_tangents=False,
                              export_animations=False, export_skins=False, export_morph=False,
                              export_image_format='AUTO', export_apply=True, export_vertex_color='NONE')
    print('EXPORTED', out)
