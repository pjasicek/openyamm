import bpy,sys,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import reduction_common as C
for level in range(4):
 path=P/f'work/runtime_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(path));C.reset()
 if level>=2:
  m=bpy.data.objects['Body'].data.materials[0];bs=m.node_tree.nodes.get('Principled BSDF');node=bs.inputs['Base Color'].links[0].from_node;node.image=bpy.data.images.load(str(P/f'export/textures_lod{level}/body/0_basecolor.png'),check_existing=False);node.image.pack()
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
 if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
