"""Ground bounds of every fitted attachment at every half-frame of its applicable clips."""
import bpy,sys,os,json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/male/runtime_ragged.blend'));r=bpy.data.objects['Rig'];scene=bpy.context.scene;report={}
for a in bpy.data.actions:
 if not a.name.startswith('Kept_'):continue
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];parts=['collar']+(['pick','club','plate'] if 'Armed' in a.name or 'Mace' in a.name else []);row={p:[1e9,None] for p in parts}
 for f in np.arange(a.frame_range[0],a.frame_range[1]+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1))
  for part in parts:
   o=bpy.data.objects['hes_kept_'+part];ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();z=min((o.matrix_world@v.co).z for v in me.vertices);ev.to_mesh_clear()
   if z<row[part][0]:row[part]=[z,float(f)]
 report[a.name]=row
(P/'review/attachment_floor.json').write_text(json.dumps(report,indent=2)+'\n');print('PROP_FLOORS',report,flush=True);sys.stdout.flush();sys.stderr.flush();os._exit(0)
