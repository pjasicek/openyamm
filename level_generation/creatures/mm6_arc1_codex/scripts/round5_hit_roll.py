import bpy,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];code=(P/'scripts/round5_motion.py').read_text();exec(code[:code.index('baseline={')])
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_equipped.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;names=[b.name for b in rig.pose.bones]
a=bpy.data.actions['Hit'];before=[sample(a,f) for f in range(int(a.frame_range[1])+1)];out=[]
for p in before:
 put(p);props={n:wm(n)for n in ['Bow','BowNock','Arrow','Socket_Arrow_Release']};balance_carry_roll()
 for n,M in props.items():rig.pose.bones[n].matrix=M;bpy.context.view_layer.update()
 rig.pose.bones['Arrow'].scale=p['Arrow'][2];out.append(get())
write('Hit',out)
FA,UA=.6,.5
code=(P/'scripts/twist_bones.py').read_text().replace('twist_about(dq, seg_local) * FA', 'twist_about(dq, seg_local) * (.4 if act.name == "Hit" and s == "L" and f0 < f < f1 else FA)');exec(code[code.index('def twist_about'):code.index('for act in [a for a in bpy.data.actions')]);bake_twist(bpy.data.actions['Hit'])
for layer in bpy.data.actions['Hit'].layers:
 for strip in layer.strips:
  for cb in strip.channelbags:
   for fc in cb.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
action(bpy.data.actions['Standing']);sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
for dst in [P/'work/rig_textured.blend']+[P/f'work/round2/lod{i}.blend'for i in range(4)]:
 sys.argv=['sync_actions.py','--',str(P/'work/rig_equipped.blend'),str(dst)];runpy.run_path(str(P/'scripts/sync_actions.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/round3_export.py'),run_name='__main__')
