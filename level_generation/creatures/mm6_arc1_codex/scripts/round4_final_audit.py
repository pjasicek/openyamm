import bpy,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
runpy.run_path(str(P/'scripts/round4_gates.py'),run_name='__main__')
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_arc1_a.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0)
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/runtime_authoring.blend'))
code=(P/'scripts/release_gate.py').read_text().replace('round3/contact_gates.json','round4/shared_final/gates.json').replace('review/release_gate.json','review/round4/release_gate.json')
exec(compile(code,str(P/'scripts/release_gate.py'),'exec'),{'__file__':str(P/'scripts/release_gate.py'),'__name__':'__main__'})
