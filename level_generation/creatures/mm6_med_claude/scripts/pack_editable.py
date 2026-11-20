import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_med.blend'))
body=bpy.data.objects['Body']
for i,label in enumerate(['body','head']):
    mat=body.data.materials[i];bs=mat.node_tree.nodes.get('Principled BSDF')
    node=bs.inputs['Base Color'].links[0].from_node
    node.image=bpy.data.images.load(str(P/f'textures/med_{label}_native_a.png'),check_existing=True);node.image.pack()
bpy.context.scene.render.fps=30
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_med.blend'))
