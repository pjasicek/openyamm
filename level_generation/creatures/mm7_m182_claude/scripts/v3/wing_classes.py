"""Wing face classes for the v3 proxy and masks (Blender library + CLI): a wing face is ARM (bone tissue) when its
centre lies within R_ARM of the wing bone chain of its side (Wing0-Wing2 segments, rest pose), else MEMBRANE
(fingers are painted, not boned, in the cdr1 wing). The thin-shell ray test alone missed the fleshy inner panels.
Writes the face attribute 'membrane' (1 / 0) on wing faces. CLI: blender -b <blend> -P wing_classes.py -- <out.png>
renders a top/front check image."""
import bpy, sys
import numpy as np
from mathutils import Vector
R_ARM = 0.055


def seg_dist(p, a, b):
    ab = b - a; t = max(0., min(1., (p - a).dot(ab) / ab.length_squared)); return (a + ab * t - p).length


def classify(o, rig, r_arm=R_ARM):
    me = o.data; bones = rig.data.bones; mw = rig.matrix_world
    segs = {s: [(mw @ bones[f'{s}Wing{i}'].head_local, mw @ bones[f'{s}Wing{i}'].tail_local) for i in range(3)] for s in 'LR'}
    att = me.attributes.get('membrane') or me.attributes.new('membrane', 'FLOAT', 'FACE')
    n = 0
    for p in me.polygons:
        f = 0.
        if p.material_index == 2:
            c = o.matrix_world @ p.center; side = 'L' if c.x > 0 else 'R'
            d = min(seg_dist(c, a, b) for a, b in segs[side]); f = 1. if d > r_arm else 0.
        att.data[p.index].value = f; n += int(f)
    return n


if __name__ == '__main__' and '--' in sys.argv:
    out = sys.argv[sys.argv.index('--') + 1]
    o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']
    if rig.animation_data: rig.animation_data.action = None
    for b in rig.pose.bones: b.matrix_basis.identity()
    print('MEMBRANE faces', classify(o, rig))
    m = bpy.data.materials.new('dbg'); m.use_nodes = True; nt = m.node_tree; a = nt.nodes.new('ShaderNodeAttribute'); a.attribute_name = 'membrane'; a.attribute_type = 'GEOMETRY'
    nt.links.new(a.outputs['Fac'], nt.nodes['Principled BSDF'].inputs['Base Color'])
    o.data.materials.clear(); o.data.materials.append(m)
    sc = bpy.context.scene; sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1200, 600
    cam = bpy.data.objects.new('C', bpy.data.cameras.new('C')); sc.collection.objects.link(cam); sc.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 3.3
    w = bpy.data.worlds.new('W'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[1].default_value = 1.5
    for name, d in (('top', (0, 0.05, 1)), ('front', (0, -1, 0.05))):
        t = Vector((0, -0.4, 0.9)); cam.location = t + Vector(d).normalized() * 20; cam.rotation_euler = (t - cam.location).to_track_quat('-Z', 'Y').to_euler()
        sc.render.filepath = out.replace('.png', f'_{name}.png'); bpy.ops.render.render(write_still=True)
