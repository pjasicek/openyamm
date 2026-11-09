import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/round5_gates.py'),run_name='__main__')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_arc1_a.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_authoring.blend'))
code=(P/'scripts/release_gate.py').read_text().replace('round3/contact_gates.json','round5/shared_final/gates.json').replace('review/release_gate.json','review/round5/release_gate.json')
exec(compile(code,str(P/'scripts/release_gate.py'),'exec'),{'__file__':str(P/'scripts/release_gate.py'),'__name__':'__main__'})

import common
def cpu(scene,textured=False):
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=8
 scene.render.threads_mode='FIXED';scene.render.threads=4
 if scene.world is None:scene.world=bpy.data.worlds.new('ReviewWorld')
 scene.world.use_nodes=True
 bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.7,.7,.7,1);bg.inputs['Strength'].default_value=.8
 scene.view_settings.view_transform='Standard'
common.workbench_clay=cpu

import numpy as np
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');sc=bpy.context.scene;common.workbench_clay(sc,True);a=bpy.data.actions['Hit'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for i,f in enumerate(np.linspace(*a.frame_range,7)):
 sc.frame_set(int(f),subframe=float(f-int(f)))
 for view in ['front','left','three_quarter']:common.render_views(str(P/f'review/clips/Hit_{i}'),.95,2.6,views=(view,),resolution=(300,420))
