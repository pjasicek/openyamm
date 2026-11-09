import bpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'))
for mat in bpy.data.materials:
 if not mat.use_nodes:continue
 for n in mat.node_tree.nodes:
  if n.type=='TEX_IMAGE' and n.image and n.image.filepath:
   f=Path(bpy.path.abspath(n.image.filepath))
   if f.parent==p/'textures':n.image=bpy.data.images.load(str(f),check_existing=False);n.image.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured.blend'))
