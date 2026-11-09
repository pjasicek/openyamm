import bpy,sys,shutil,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
def pose(path,clip,frame):
 bpy.ops.wm.open_mainfile(filepath=str(P/path));r=bpy.data.objects['Rig'];a=bpy.data.actions[clip];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(frame)
 return {b.name:tuple(x for row in b.matrix for x in row)for b in r.pose.bones}
prior=pose('work/round4/near_runtime.blend','Dead',0)
prior_end=pose('work/round4/near_runtime.blend','Death',120)
dead=pose('work/round5/lod0.blend','Dead',0);end=pose('work/round5/lod0.blend','Death',120)
error=max(abs(a-b)for n in prior for a,b in zip(prior[n],dead[n]));end_error=max(abs(a-b)for n in prior_end for a,b in zip(prior_end[n],end[n]))
assert error<1e-5 and end_error<1e-5,(error,end_error)
(P/'review/round5/end_pose_preservation.json').write_text(json.dumps({'round4_to_round5_dead_max_matrix_error':error,'round4_to_round5_death_end_max_matrix_error':end_error},indent=2))
r=bpy.data.objects['Rig'];r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
def ease(x):
 x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
def time(t,name):
 t/=2 if name=='Death'else 1.5
 if name=='Death':return t+.10*(ease((t-.5)/.17)-ease((t-.5)/1.5))+.25*(ease((t-.95)/.50)-ease((t-.5)/1.5))
 return t+.012*(ease((t-.94)/.12)-ease((t-.7)/.4333333333333333))
assert abs(time(.734375,'Attack')-.4895833333333333)<1e-12 and time(4,'Death')==2
for a in bpy.data.actions:
 if a.name not in ['Attack','Cast','Death']:continue
 end=float(a.frame_range[1])
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.co.x=time(k.co.x/30,a.name)*30
     fc.update()
 a.frame_end=time(end/30,a.name)*30
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round5/retimed_master.blend'))
for path in ['work/master.blend','work/master_export.blend']:shutil.copyfile(P/'work/round5/retimed_master.blend',P/path)
