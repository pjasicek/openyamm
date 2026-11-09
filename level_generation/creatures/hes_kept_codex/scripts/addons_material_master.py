import bpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for name in ('equipped','final'):
 path=P/'work/addons_v2'/f'{name}.blend';bpy.ops.wm.open_mainfile(filepath=str(path))
 for m in bpy.data.materials:
  if not m.name.startswith('KeptV2_') or not m.use_nodes:continue
  bs=m.node_tree.nodes.get('Principled BSDF');sep=next((n for n in m.node_tree.nodes if n.type=='SEPARATE_COLOR'),None)
  if bs and sep:m.node_tree.links.new(sep.outputs['Blue'],bs.inputs['Metallic'])
 bpy.ops.wm.save_as_mainfile(filepath=str(path))
sys.stdout.flush();sys.stderr.flush();os._exit(0)
