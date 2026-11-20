"""Open bark tubes (sculpt species) are single-sided and the engine culls back faces, so every bark face must face
outward: its geometric normal must agree with its corners' outward shading normals. Prints the inverted fraction per
LOD. Usage: blender --background --python check_bark_facing.py -- <work/id/tree.blend>"""
import bpy, sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
for name in ('Tree', 'Tree_LOD1', 'Tree_LOD2'):
    me = bpy.data.objects[name].data
    bark = [i for i, m in enumerate(me.materials) if m.name == 'Bark'][0]
    cn = me.corner_normals
    bad = total = 0
    for p in me.polygons:
        if p.material_index != bark:
            continue
        total += 1
        avg = sum((cn[l].vector for l in p.loop_indices), p.normal * 0)
        bad += avg.dot(p.normal) < 0
    print('FACING', name, 'bark faces', total, 'inverted', bad)
