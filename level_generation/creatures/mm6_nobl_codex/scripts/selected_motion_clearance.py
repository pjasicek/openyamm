"""Resolve new cloth/body contacts in the two selected clips only."""
import bpy,sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
s=(p/'scripts/limit_cloth_strain.py').read_text().replace('rig_v7p.blend','rig_v15.blend').replace('rig_v7s.blend','rig_v15_clearance.blend')
s=s.replace("['nobl_cloak','nobl_tabard','nobl_skirt_back']","['nobl_cloak','nobl_skirt_back']")
s=s.replace("np.isin(pv,[0,8,9])","np.isin(pv,[0,8])")
s=s.replace("['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']","['Running','Hit']")
s=s.replace("p/'work/cloth_strain_limit.json'","p/'review/selected_motion_20261011/cloth_clearance.json'")
exec(compile(s,str(p/'scripts/limit_cloth_strain.py'),'exec'),{'__file__':str(p/'scripts/limit_cloth_strain.py'),'__name__':'__main__'})
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_v15.blend'))
sys.argv=['g6_contacts.py','--',str(p/'work/rig_v15.blend'),'Running','Hit']
runpy.run_path(str(p/'scripts/g6_contacts.py'),run_name='__main__')
