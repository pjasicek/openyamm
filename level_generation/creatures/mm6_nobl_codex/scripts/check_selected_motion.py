"""Focused gates on the installed-format Run B and Hit A exports."""
import bpy,sys,runpy,os,json
from pathlib import Path
p=Path(__file__).resolve().parents[1];out=p/'review/selected_motion_20261011';sys.path.insert(0,str(p/'scripts'))
def run(name,args=()):
 sys.argv=[name,'--']+[str(x) for x in args];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('g6_contacts.py',[p/'export/mm6_nobl_runtime_lod0.glb','Running','Hit'])
contacts=json.loads((p/'work/g6_contacts.json').read_text())
assert all(not row for row in contacts.values()),contacts
(out/'contacts.json').write_text(json.dumps(contacts,indent=2))
os.environ['CLIPS']='Running,Hit'
run('g6_sword_mesh.py',[p/'export/mm6_nobl_runtime_lod0.glb'])
os.environ.pop('CLIPS',None)
run('loop_audit.py')
for name in ['feet_cloak_check.py','shoulder_buckle_check.py']:
 code=(p/'scripts'/name).read_text().replace('for a in bpy.data.actions:',"for a in [bpy.data.actions[n] for n in ['Running','Hit']]:")
 if name=='feet_cloak_check.py':code=code.replace("out=p/'review/feet_cloak_20261011'","out=p/'review/selected_motion_20261011'")
 else:code=code.replace("(out/'export_gate.json')","(p/'review/selected_motion_20261011/shoulder_gate.json')")
 exec(compile(code,str(p/'scripts'/name),'exec'),{'__file__':str(p/'scripts'/name),'__name__':'__main__'})
run('g6_head_clearance.py',[p/'work/rig_v15.blend','Running','Hit'])
run('g5_hand_stretch.py',[p/'work/rig_v15.blend','Running','Hit'])
os.environ['CLIP']='Running';run('cloak_poke.py',['rig_v15.blend']);os.environ.pop('CLIP',None)
