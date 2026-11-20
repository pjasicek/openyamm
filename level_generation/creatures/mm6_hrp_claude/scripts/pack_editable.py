"""Pack the same native A plumage seen in the runtime and review viewer."""
import bpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'export/mm6_hrp.blend'))
for image in bpy.data.images:
 if image.source=='FILE':
  path=Path(bpy.path.abspath(image.filepath));assert path.is_file() and P in path.parents
  if image.packed_file:image.unpack(method='REMOVE')
  image.reload();image.pack()
for name in ['HarpyBody_A','HarpyWings_A']:
 mat=bpy.data.materials[name];node=mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].links[0].from_node
 node.image=bpy.data.images.load(str(P/'textures'/('native_a_'+name+'.png')),check_existing=True);node.image.pack()
for image in list(bpy.data.images):
 if image.users==0:bpy.data.images.remove(image)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_hrp.blend'))
