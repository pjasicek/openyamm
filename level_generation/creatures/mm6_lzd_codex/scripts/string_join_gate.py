"""Check that the written runtime string remains joined during draw and snap."""
import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(globals().get('GATE_BLEND',P/'work/export_reimport.blend')));rig=bpy.data.objects['Rig'];a=bpy.data.actions['Attack'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];rows=[]
for start in [18,22]:
 for f in np.linspace(start,start+1,65):
  bpy.context.scene.frame_set(int(f),subframe=float(f%1));points=[rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@Vector((0,0,1))for n in ['StringTop','StringBottom']];rows.append({'frame':float(f),'gap_m':(points[0]-points[1]).length})
result={'sample_rate_hz':1920,'max_gap_m':max(x['gap_m']for x in rows),'worst_frame':max(rows,key=lambda x:x['gap_m'])['frame'],'passed':max(x['gap_m']for x in rows)<=.003}
(P/'review/string_join_gate.json').write_text(json.dumps(result,indent=2));print('STRING_JOIN',result,flush=True);assert result['passed']
