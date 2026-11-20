"""Toxic Cloud (object 9010, sprite spell90: a skull of green poison smoke) -> work/toxic_cloud_export.glb, installed as
engine/models/projectile_toxic_cloud.glb.

The skull of the project's MM6 skeleton creature (its Head pieces from the MM8 props bone kit,
../../decorations/mm8_3d/props/scripts/bonekit.py, read only), facing the flight (-Y), decimated to TRIANGLES, its own
UVs on toxic_skull_basecolor.png (make_solid_textures.py: the bone texture recoloured poison green, alpha 0.6).
Material Toxic: blended, single-sided, with a faint green glow; the enhanced toxic_cloud flight effect rolls its
poison smoke round it.
Usage: blender --background --python build_toxic.py"""
import os
import sys

import bmesh
import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', '..', 'decorations', 'mm8_3d', 'props', 'scripts'))
import bonekit  # noqa: E402
import projlib as pl  # noqa: E402

TRIANGLES = 600


def main():
    pl.reset()
    kit = bonekit.Kit()
    skull = kit.place(kit.ids('Head'), 'Skull', align=False)
    decimate = skull.modifiers.new('Decimate', 'DECIMATE')
    decimate.ratio = min(1.0, TRIANGLES / max(len(skull.data.polygons), 1))
    with bpy.context.temp_override(object=skull, active_object=skull):
        bpy.ops.object.modifier_apply(modifier=decimate.name)
    bm = bmesh.new()
    bm.from_mesh(skull.data)
    for layer in list(bm.loops.layers.uv)[1:]:
        bm.loops.layers.uv.remove(layer)
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj)
    obj = pl.to_object('ToxicSkull', bm, [pl.material('Toxic', 'toxic_skull', 0.6, alpha=True)], 40)
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    print('SKULL depth', round(max(ys) - min(ys), 4), 'height', round(max(zs) - min(zs), 4))
    pl.export(obj, 'toxic_cloud', {'Toxic': {'blend': True, 'emissive': [0.03, 0.07, 0.02]}})


main()
