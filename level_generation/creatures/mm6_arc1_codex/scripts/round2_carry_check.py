import bpy,runpy,sys,shutil,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
runpy.run_path(str(P/'scripts/round2_motion.py'),run_name='__main__')
shutil.copy2(P/'work/rig_textured.blend',P/'work/round2/unreduced.blend')
code=(P/'scripts/gate_equipment.py').read_text();exec(compile(code[:code.index('acts=[a.name')],str(P/'scripts/gate_equipment.py'),'exec'),{'__file__':str(P/'scripts/gate_equipment.py'),'__name__':'__main__'})
sc=bpy.context.scene;common.workbench_clay(sc,True);sc.render.resolution_x=600;sc.render.resolution_y=900;sc.render.resolution_percentage=100
r=bpy.data.objects['Rig'];a=bpy.data.actions['Standing'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
for label,eye in [('front',(0,-5,1)),('left',(5,0,1)),('quarter',(3,-5,1.3))]:
 cam=common.ortho_camera('Preview',eye,(0,0,.86),1.92);sc.camera=cam;sc.render.filepath=str(P/f'review/round2/final_carry_{label}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
print('CARRY_EQUIPMENT',json.loads((P/'work/equipment_gate.json').read_text()),flush=True)
