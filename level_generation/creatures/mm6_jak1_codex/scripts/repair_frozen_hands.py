import bpy,sys,json,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
from hand_weights import repair_hand_weights
report={}
for name in ['textured_master','production_body']:
 path=P/f'work/{name}.blend';backup=P/f'work/{name}_before_handfix.blend'
 if not backup.exists():shutil.copy2(path,backup)
 bpy.ops.wm.open_mainfile(filepath=str(backup));report[name]=repair_hand_weights(bpy.data.objects['Body'],bpy.data.objects['Rig']);bpy.ops.wm.save_as_mainfile(filepath=str(path))
(P/'work/hand_weights_correction.json').write_text(json.dumps(report,indent=2));print(report,flush=True)
