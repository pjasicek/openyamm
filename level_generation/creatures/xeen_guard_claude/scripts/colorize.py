"""Colour the Guard mesh by plate bone (face attribute `bone`); joints and caps dark. For clay review renders."""
import bpy, colorsys


def colorize(mesh):
    me = mesh.data
    me.materials.clear()
    nb = 0
    bone = [me.attributes['bone'].data[i].value for i in range(len(me.polygons))]
    part = [me.attributes['part'].data[i].value for i in range(len(me.polygons))]
    nb = max(bone) + 1
    for i in range(nb):
        m = bpy.data.materials.new(f'c{i}')
        m.diffuse_color = (*colorsys.hsv_to_rgb((i * 0.618) % 1.0, 0.5, 0.95), 1)
        me.materials.append(m)
    d = bpy.data.materials.new('dark'); d.diffuse_color = (0.1, 0.1, 0.12, 1); me.materials.append(d)
    g = bpy.data.materials.new('gem'); g.diffuse_color = (0.9, 0.05, 0.05, 1); me.materials.append(g)
    for p in me.polygons:
        p.material_index = nb if part[p.index] in (2, 3) else nb + 1 if part[p.index] == 1 else bone[p.index]
