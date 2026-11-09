"""Use the shared projected-shell and skin-weight route; map its islands to the shared ceramic atlas."""
import bpy,json,runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
sys.argv=['make_armour.py','--',str(P/'work/winged_hands.blend'),str(P/'scripts/armour_overseer.json'),str(P/'work/armour_raw.blend')]
runpy.run_path(str(P/'scripts/make_armour.py'),run_name='__main__')
sys.argv=['skin_shell.py','--',str(P/'work/armour_raw.blend'),str(P/'scripts/armour_overseer.json'),str(P/'work/armour_skinned.blend')]
runpy.run_path(str(P/'scripts/skin_shell.py'),run_name='__main__')
# Reuse the Kreegan material set without a new baked colour image per tier.
ours=json.loads((P/'work/armour_layout.json').read_text());original=json.loads((P/'source/kreegan_armour_layout.json').read_text());spec=json.loads((P/'scripts/armour_overseer.json').read_text())
for entry in spec['plates']:
 o=bpy.data.objects['Arm_'+entry['name']];old=ours['plates'][entry['name']]['rect'];new=original['plates'][entry['atlas_source']]['rect'];A=ours['atlas'];B=original['atlas']
 for f in o.data.polygons:
  if f.material_index:continue
  for li in f.loop_indices:
   uv=o.data.uv_layers.active.data[li].uv.copy();x,y=uv.x*A,(1-uv.y)*A
   if old[0]-.1<=x<=old[0]+old[2]+.1 and old[1]-.1<=y<=old[1]+old[3]+.1:
    s,t=(x-old[0])/old[2],(y-old[1])/old[3];o.data.uv_layers.active.data[li].uv=((new[0]+s*new[2])/B,1-(new[1]+t*new[3])/B)
with bpy.data.libraries.load(str(P/'work/equipment.blend'),link=False) as (source,data):data.materials=['OV_Equipment','OV_Glow']
for o in [o for o in bpy.data.objects if o.name.startswith('Arm_')]:
 slots=[f.material_index for f in o.data.polygons];o.data.materials.clear()
 for m in data.materials:o.data.materials.append(m)
 o.data.polygons.foreach_set('material_index',slots)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/armour_skinned.blend'))
print('ARMOUR_DONE',flush=True)
sys.stdout.flush();sys.stderr.flush();os._exit(0)
