import bpy,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import final_refinements
exec((p/'scripts/acceleration_gate.py').read_text().split("bpy.ops.wm.open_mainfile")[0])
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured.blend'));r=bpy.data.objects['Rig'];final_refinements.smooth_attack(r);print('SMOOTHED_ATTACK_ACCELERATION',measure(r,bpy.data.actions['Attack']),flush=True)
