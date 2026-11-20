"""Start the death release at the revised ready carry; retain its existing landing."""
import bpy,sys,os,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/forge_chest_fit.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
from mathutils import Vector
a=bpy.data.actions['Forge_Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];sc.frame_set(0)
carry=json.loads((P/'review/forge_carry_fit.json').read_text())['Standing']
turn=armik.W(r,'B_Spine2')@r.data.bones['B_Spine2'].matrix_local.inverted()
delta=turn.to_3x3()@Vector((0,-carry['forward_m'],carry['up_m']))
assert delta.length<.10,delta
keys=[]
for f in np.arange(0,15.001,.25):
 sc.frame_set(int(f),subframe=float(f%1));m=armik.W(r,'Thunder_Maul');k=float(f/15);m.translation+=delta*(1-k*k*(3-2*k));armik.set_world(r,'Thunder_Maul',m);keys.append((float(f),r.pose.bones['Thunder_Maul'].location.copy()))
for f,value in keys:
 b=r.pose.bones['Thunder_Maul'];b.location=value;b.keyframe_insert('location',frame=f)
(P/'review/forge_release.json').write_text(json.dumps({'ready_translation_delta_m':list(delta),'settles_to_existing_drop_seconds':.5},indent=2)+'\n')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/forge_release_fit.blend'));print('RELEASE_READY_DELTA',list(delta),flush=True);sys.stdout.flush();os._exit(0)
