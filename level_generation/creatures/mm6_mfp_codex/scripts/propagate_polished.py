import bpy,sys,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];roles=['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget'];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_polished.blend'));r=bpy.data.objects['Rig'];a=bpy.data.actions['Hit']
if a.frame_range[1]<16:
 for l in a.layers:
  for st in l.strips:
   for bag in st.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:
      for co in [k.co,k.handle_left,k.handle_right]:co.x*=1.25
 a.frame_end=18.75
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_polished.blend'));rest={b.name:np.array(b.matrix_local)for b in r.data.bones};sel=json.loads((P/'review/reduction_soft/selection.json').read_text())
for level,row in sel.items():
 source=P/row['blend'];bpy.ops.wm.open_mainfile(filepath=str(source));r=bpy.data.objects['Rig'];assert max(abs(rest[b.name]-np.array(b.matrix_local)).max()for b in r.data.bones)<1e-5;r.animation_data.action=None
 for a in list(bpy.data.actions):bpy.data.actions.remove(a)
 for pb in r.pose.bones:pb.matrix_basis.identity()
 with bpy.data.libraries.load(str(P/'work/rig_polished.blend'),link=False)as(src,dst):dst.actions=list(roles)
 for a in dst.actions:a.use_fake_user=True
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];bpy.context.scene.frame_set(0);path=P/f'work/selected_lod{level}_polished.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));row['previous_motion_blend']=row['blend'];row['blend']=str(path.relative_to(P))
(P/'review/reduction_soft/selection.json').write_text(json.dumps(sel,indent=2))
