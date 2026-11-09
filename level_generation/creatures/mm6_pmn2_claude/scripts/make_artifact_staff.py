"""Boss staff for "Necromancer A": an ebony shaft with gold bands, a gold claw cage and a glowing violet crystal.

Built in the Staff bone's own space, like export/mm6_pmn2_staff.glb from tools/split_attachment.py: the shaft runs
along +Z here (+Y in glTF) from the butt at -1.14 to the crown at 0.5, and the crystal is centred on the bone's
Socket_Staff_Head (0.354), so the cast glow forms inside it. Three materials (ebony, gold, emissive crystal), no
textures; LOD1..LOD3 are decimated copies linked by tools/link_static_model_lods.py.
Usage: blender --background --factory-startup --python make_artifact_staff.py -- out.glb"""
import math
import subprocess
import sys
from pathlib import Path

import bmesh
import bpy

BUTT = -1.14
CRYSTAL = 0.354
TIP = 0.5
LOD_RATIOS = (0.5, 0.22, 0.08)


def material(name, color, metallic, roughness, emission=None, specular=None):
    result = bpy.data.materials.new(name)
    if specular is not None:
        # Exported as the material's extras: the engine's specular and sky-reflection scale.
        result['openyamm_specular'] = specular
    result.use_nodes = True
    shader = next(node for node in result.node_tree.nodes if node.type == 'BSDF_PRINCIPLED')
    shader.inputs['Base Color'].default_value = (*color, 1.0)
    shader.inputs['Metallic'].default_value = metallic
    shader.inputs['Roughness'].default_value = roughness
    if emission is not None:
        shader.inputs['Emission Color'].default_value = (*emission, 1.0)
        shader.inputs['Emission Strength'].default_value = 1.0
    return result


def lathe(bm, profile, segments, twist=0.0, ridges=0, ridge_depth=0.0):
    """Surface of revolution from (radius, z) pairs; optional spiral ridges for a carved look."""
    rings = []
    for radius, z in profile:
        ring = []
        for step in range(segments):
            angle = 2.0 * math.pi * step / segments + twist * z
            local = radius * (1.0 + ridge_depth * math.cos(ridges * angle)) if ridges else radius
            ring.append(bm.verts.new((local * math.cos(angle), local * math.sin(angle), z)))
        rings.append(ring)
    for lower, upper in zip(rings, rings[1:]):
        for step in range(segments):
            following = (step + 1) % segments
            bm.faces.new((lower[step], lower[following], upper[following], upper[step]))
    for ring, flip in ((rings[0], True), (rings[-1], False)):
        if profile[0 if flip else -1][0] > 0.0005:
            bm.faces.new(list(reversed(ring)) if flip else ring)


def add_object(name, build, assigned):
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    build(bm)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    obj.data.materials.append(assigned)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def shaft(bm):
    profile = [(0.0, BUTT), (0.008, BUTT + 0.02), (0.016, BUTT + 0.07)]
    z = BUTT + 0.07
    while z < 0.20:
        profile.append((0.017 - 0.002 * (z - BUTT) / (0.2 - BUTT), z))
        z += 0.05
    profile.append((0.016, 0.21))
    lathe(bm, profile, 10, twist=9.0, ridges=4, ridge_depth=0.18)


def gold(bm):
    # Bands along the shaft, the butt ferrule and the collar under the cage.
    for center, height, radius in ((BUTT + 0.05, 0.08, 0.019), (-0.72, 0.03, 0.021), (-0.36, 0.03, 0.021),
                                   (-0.02, 0.035, 0.022), (0.19, 0.05, 0.026)):
        lathe(bm, [(radius * 0.85, center - height / 2), (radius, center - height / 3), (radius, center + height / 3),
                   (radius * 0.85, center + height / 2)], 12)
    lathe(bm, [(0.0, 0.205), (0.03, 0.215), (0.036, 0.235), (0.02, 0.25)], 12)
    # Four claws rising from the collar, curving out around the crystal and back in over it.
    for claw in range(4):
        angle = claw * math.pi / 2 + math.pi / 4
        points = []
        for step in range(9):
            t = step / 8
            z = 0.24 + t * (TIP - 0.035 - 0.24)
            radius = 0.022 + 0.062 * math.sin(math.pi * min(t * 1.08, 1.0)) - 0.014 * t
            twist = angle + 0.45 * t
            points.append((radius * math.cos(twist), radius * math.sin(twist), z, 0.011 * (1.0 - 0.55 * t)))
        previous = None
        for x, y, z, thickness in points:
            ring = [bm.verts.new((x + thickness * math.cos(a) * math.cos(angle),
                                  y + thickness * math.cos(a) * math.sin(angle), z + thickness * math.sin(a)))
                    for a in (2.0 * math.pi * k / 5 for k in range(5))]
            if previous is not None:
                for k in range(5):
                    bm.faces.new((previous[k], previous[(k + 1) % 5], ring[(k + 1) % 5], ring[k]))
            previous = ring
    # Crown spike above the cage and a ring around the crystal's girdle, held by the claws.
    lathe(bm, [(0.014, TIP - 0.045), (0.009, TIP - 0.018), (0.0, TIP)], 8)
    torus(bm, CRYSTAL + 0.005, 0.072, 0.0055, 24, 6)


def torus(bm, z, radius, tube, segments, sides):
    rings = []
    for step in range(segments):
        angle = 2.0 * math.pi * step / segments
        rings.append([bm.verts.new(((radius + tube * math.cos(b)) * math.cos(angle),
                                    (radius + tube * math.cos(b)) * math.sin(angle), z + tube * math.sin(b)))
                      for b in (2.0 * math.pi * k / sides for k in range(sides))])
    for step in range(segments):
        ring, following = rings[step], rings[(step + 1) % segments]
        for k in range(sides):
            bm.faces.new((ring[k], following[k], following[(k + 1) % sides], ring[(k + 1) % sides]))


def crystal(bm):
    # Elongated faceted gem centred on the socket.
    lathe(bm, [(0.0, CRYSTAL - 0.1), (0.044, CRYSTAL - 0.025), (0.05, CRYSTAL + 0.005), (0.036, CRYSTAL + 0.05),
               (0.0, CRYSTAL + 0.115)], 6)


def main():
    out = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    # Ebony: a warm near-black that reflects little sky (it read violet with full reflection). Gold: saturated and
    # rough enough that its own colour, not the blue sky, dominates the reflection.
    ebony = material('ArtifactStaff_Ebony', (0.016, 0.010, 0.008), 0.0, 0.62, specular=0.35)
    gilt = material('ArtifactStaff_Gold', (1.0, 0.56, 0.11), 1.0, 0.45)
    gem = material('ArtifactStaff_Crystal', (0.32, 0.06, 0.62), 0.0, 0.15, emission=(0.55, 0.12, 1.0))
    parts = [add_object('ArtifactStaff', shaft, ebony), add_object('Gold', gold, gilt),
             add_object('Crystal', crystal, gem)]
    for part in parts[1:]:
        part.select_set(True)
    parts[0].select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    base = bpy.context.view_layer.objects.active
    for level, ratio in enumerate(LOD_RATIOS, start=1):
        copy = base.copy()
        copy.data = base.data.copy()
        copy.name = f'{base.name}_LOD{level}'
        bpy.context.scene.collection.objects.link(copy)
        modifier = copy.modifiers.new('decimate', 'DECIMATE')
        modifier.ratio = ratio
        bpy.context.view_layer.objects.active = copy
        bpy.ops.object.modifier_apply(modifier=modifier.name)
    raw = out.with_suffix('.raw.glb')
    bpy.ops.export_scene.gltf(filepath=str(raw), export_format='GLB', export_yup=True, export_apply=True,
                              export_materials='EXPORT', export_image_format='NONE', export_extras=True)
    for obj in bpy.context.scene.objects:
        print('LOD', obj.name, len(obj.data.polygons), sum(len(p.vertices) - 2 for p in obj.data.polygons))
    repo = Path(__file__).resolve().parents[4]
    subprocess.run(['python3', str(repo / 'tools' / 'link_static_model_lods.py'), str(raw), str(out)], check=True)
    raw.unlink()
    print('EXPORTED', out)


if __name__ == '__main__':
    main()
