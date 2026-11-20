"""Resume the preserved library strike with the accepted caste shell and corpse arm fit."""
import bpy,sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];S=P/'scripts';W=P/'work';sys.path.insert(0,str(S))
prepare_only='--prepare-only' in sys.argv
def step(name,*args):
 print('FORGE_REVIEW',name,flush=True);sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(S/name),run_name='__main__')
step('restore_forge_stroke.py')
for role in ('Death','Dead'):
 old=bpy.data.actions.get('Forge_'+role)
 if old:bpy.data.actions.remove(old)
 with bpy.data.libraries.load(str(W/'lancer_complete.blend'),link=False) as (src,dst):dst.actions=['Carbine_'+role]
 a=dst.actions[0];a.name='Forge_'+role;a.use_fake_user=True
out=W/'forge_review.blend';bpy.ops.wm.save_as_mainfile(filepath=str(out))
step('bake_new_twists.py',out,out);step('helper_bones.py',out,out)
step('make_armour.py',out,S/'armour_lancer.json',out);step('fit_forge_shell.py',out,out)
step('add_hull_parts.py',out,'forge',out);step('drop_maul.py',out,out)
if prepare_only:
 bpy.ops.wm.save_as_mainfile(filepath=str(W/'forge_review_base.blend'));sys.stdout.flush();os._exit(0)
clips=['Forge_'+r for r in ('Standing','Walking','Running','Attack','Hit','Fidget','Cast','Death','Dead')]
step('gates.py',out,'forge_review',*clips);step('shell_stretch.py',out,S/'armour_forge.json','forge_review',*clips)
step('shell_leak.py',out,S/'armour_forge.json','forge_review',*clips);step('armour_gate.py',out,'forge_review',S/'armour_forge.json',*clips)
step('equipment_gate.py',out,'forge',*clips)
sys.stdout.flush();os._exit(0)
