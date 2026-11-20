"""Workbench textured views of the HDR mesh with a base-colour image. Args: -- <blend> <basecolor.png> <out_prefix>"""
import bpy, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_hdr as C
a = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a[0]))
m = bpy.data.objects['HDR']
mat = bpy.data.materials.new('prev'); mat.use_nodes = True
tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(os.path.abspath(a[1]))
bsdf = mat.node_tree.nodes['Principled BSDF']; mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
m.data.materials.clear(); m.data.materials.append(mat)
c = (0, 0.0, 0.36)
for name, d in (('left', (1, 0, 0)), ('right', (-1, 0, 0)), ('front', (0, -1, 0)), ('back', (0, 1, 0)),
                ('top', (0, 0.001, 1)), ('q', (0.7, -0.7, 0.45)), ('qr', (-0.7, -0.7, 0.3)), ('under', (0.5, -0.4, -0.8))):
    loc = [c[i] + 3 * d[i] for i in range(3)]
    C.render_ortho(loc, c, float(os.environ.get('SCALE', 0.95)), f'{os.path.abspath(a[2])}_{name}.png', show={'HDR'},
                   res=(int(os.environ.get('RES', 640)), int(int(os.environ.get('RES', 640)) * 0.875)), textured=True)
