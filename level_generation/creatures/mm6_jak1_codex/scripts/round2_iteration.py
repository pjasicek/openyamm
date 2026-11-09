import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from timing import phase
import bpy,runpy,sys,traceback
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
try:runpy.run_path(str(P/'scripts/final_gates.py'),run_name='__main__')
except AssertionError:traceback.print_exc()
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_master.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
import common
common.workbench_clay(sc,textured=True)
for mat in bpy.data.materials:
 if mat.node_tree:
  bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
  if bs and bs.inputs['Base Color'].links:mat.node_tree.nodes.active=bs.inputs['Base Color'].links[0].from_node
for clip,times in [('Standing',[0]),('Walking',[.2,.4]),('Attack',[.4,.72,1.0]),('Cast',[.6,1.0]),('Fidget',[1.6]),('Death',[.5,1.1,1.666667])]:
 a=bpy.data.actions[clip];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i,t in enumerate(times):
  f=phase(clip,t)*sc.render.fps;sc.frame_set(int(f),subframe=f-int(f));common.render_views(str(P/f'review/round2/current_{clip}_{i}'),.95,3.5,views=('front','left'),resolution=(400,540))
