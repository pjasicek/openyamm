"""Head close-ups as exported (body 1K + head set), rest pose: front, three-quarter, side. Args: out_png"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
out = sys.argv[sys.argv.index('--') + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.import_scene.gltf(filepath=os.path.join(HERE, 'export', 'mm6_ckt_lod0.glb'))
for o in bpy.data.objects:
    if o.type == 'MESH':
        o.name = 'Cockatrice'
    if o.type == 'ARMATURE':
        o.name = 'Ckt_Rig'; o.animation_data_clear() if o.animation_data else None
cells = []
for name, loc, tgt in (('front', (0, -1.5, 0.37), (0, -0.45, 0.35)), ('q', (-0.9, -1.4, 0.55), (0, -0.44, 0.35)),
                       ('side', (-1.5, -0.44, 0.36), (0, -0.44, 0.35))):
    p = out.replace('.png', f'_{name}.png'); C.render_ortho(loc, tgt, 0.3, p, res=(450, 450), textured=True); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; o=Image.new('RGB',(450*len(ims),450))
[o.paste(im,(i*450,0)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
for p in cells: os.remove(p)
