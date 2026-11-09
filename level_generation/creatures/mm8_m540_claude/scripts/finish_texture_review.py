from pathlib import Path
import runpy,os
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/ground_death_cape.py'),run_name='__main__')
os.environ['MAGE_BLEND']=str(p/'work/rig_uv.blend');os.environ['MAGE_CHECK_STAGE']='settled'
s=p/'scripts/full_contacts.py';code=s.read_text().replace("['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']","['Death','Dead']")
exec(compile(code,str(s),'exec'),{'__file__':str(s),'__name__':'__main__'})
runpy.run_path(str(p/'scripts/bake_head_normal.py'),run_name='__main__')
