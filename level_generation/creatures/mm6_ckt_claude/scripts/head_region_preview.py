"""Preview candidate head-face sets (faces mostly weighted to the given groups) in red. Args: out_png groups,groups..."""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
args = sys.argv[sys.argv.index('--') + 1:]
out, sets = args[0], args[1:]
mesh = bpy.data.objects['Cockatrice']; rig = bpy.data.objects['Ckt_Rig']
rig.animation_data.action = None
for b in rig.pose.bones: b.matrix_basis.identity()
red = bpy.data.materials.new('red'); red.diffuse_color = (0.9, 0.1, 0.1, 1)
grey = bpy.data.materials.new('grey'); grey.diffuse_color = (0.7, 0.7, 0.7, 1)
mesh.data.materials.clear(); mesh.data.materials.append(grey); mesh.data.materials.append(red)
sc = bpy.context.scene; sc['use_material'] = 1; cells = []
for spec in sets:
    groups = {mesh.vertex_groups[n].index for n in spec.split(',')}
    w = [sum(g.weight for g in v.groups if g.group in groups) for v in mesh.data.vertices]
    n = 0
    for p in mesh.data.polygons:
        p.material_index = int(sum(w[v] for v in p.vertices) / len(p.vertices) >= 0.5); n += p.material_index
    print('SET', spec, 'faces', n)
    for view, loc in (('s', (-3, 0, 0.3)), ('q', (-1.8, -2.2, 1.0))):
        p = out.replace('.png', f'_{len(cells)}.png')
        C.render_ortho(loc, (0, -0.35, 0.32), 0.45, p, res=(400, 400)); cells.append(p)
        sc.display.shading.color_type = 'MATERIAL'
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; o=Image.new('RGB',(400*len(ims),400))
[o.paste(im,(i*400,0)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
