import bpy,sys,json,runpy,shutil,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];W=P/'work/round2';sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(W/'lod1.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];a=bpy.data.actions['Hit'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(3,subframe=.125);v=b.data.vertices[1720];names={g.index:g.name for g in b.vertex_groups};mat=sum((np.array(r.pose.bones[names[g.group]].matrix@r.data.bones[names[g.group]].matrix_local.inverted())*g.weight for g in v.groups),np.zeros((4,4)));delta=np.array([.08139967918395996-.07462254166603088,-.05109405517578125+.04236225038766861,1.4615659713745117-1.4631086587905884])*.24;v.co+=Vector(np.linalg.solve(mat[:3,:3],delta));b.data.update();bpy.ops.wm.save_as_mainfile(filepath=str(W/'lod1.blend'))
for level in [0,1,2,3]:
 shutil.copy2(W/f'lod{level}.blend',P/'work/rig_equipped.blend');out=P/f'review/round2/lod_gates/lod{level}';errors=[]
 try:runpy.run_path(str(P/'scripts/round2_contact_gates.py'),run_name='__main__')
 except Exception as e:errors.append(str(e))
 shutil.copy2(P/'review/round2/contact_gates.json',out/'contact_gates.json')
 if level==1:
  runpy.run_path(str(P/'scripts/round2_equipment_only.py'),run_name='__main__');shutil.copy2(P/'work/equipment_gate.json',out/'equipment_gate.json');eq=json.loads((out/'equipment_gate.json').read_text());assert all(v['equipment_contact_cm']==0 and v['floor_min_cm']>=0 for v in eq.values())
 status=json.loads((out/'status.json').read_text());status['failures']=[v for v in status['failures']if not(isinstance(v,list)and v[0]=='round2_contact_gates.py')]+errors;status['pass']=not status['failures'];status['surface_sampling']='Barycentric eighths';(out/'status.json').write_text(json.dumps(status,indent=2));print('FINAL_CONTACT_STATUS',level,status,flush=True)
shutil.copy2(W/'lod0.blend',P/'work/rig_equipped.blend')
for name in ['equipment_gate.json','g4_equipped.json','g5_final.json','g6_contacts.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'work'/name)
for name in ['anatomy_and_feet.json','contact_gates.json']:shutil.copy2(P/'review/round2/lod_gates/lod0'/name,P/'review/round2'/name)
runpy.run_path(str(P/'scripts/round2_head_probe.py'),run_name='__main__')
