"""Keep the falling tabard from folding back through its belt; preserve both endpoint poses."""
import bpy,sys,json,math,shutil,runpy
from pathlib import Path
from mathutils import Matrix
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round5/lod0.blend'));r=bpy.data.objects['Rig'];sc=bpy.context.scene
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bone=r.pose.bones['LoinFlap'];M=r.data.bones['LoinFlap'].matrix_local.copy();pivot=r.data.bones['LoinFlap'].head_local.copy();rows=[]
for f in range(121):
 sc.frame_set(f);D=r.pose.bones['B_Pelvis'].matrix@r.data.bones['B_Pelvis'].matrix_local.inverted();delta=D.inverted()@bone.matrix@M.inverted();angle=-delta.to_euler('XYZ').x
 rows.append((D,angle,bone.matrix.copy()))
def ease(x):
 x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
trace=[]
for f,(D,angle,original)in enumerate(rows):
 sc.frame_set(f);w=ease((f-30)/12)*(1-ease((f-78)/20));desired=angle+(min(angle,math.radians(45))-angle)*w
 bone.matrix=D@Matrix.Translation(pivot)@Matrix.Rotation(-desired,4,'X')@Matrix.Translation(-pivot)@M
 for ch in ['rotation_quaternion','location','scale']:bone.keyframe_insert(ch,frame=f)
 trace.append({'frame':f,'before_deg':math.degrees(angle),'after_deg':math.degrees(desired)})
for layer in a.layers:
 for strip in layer.strips:
  for bag in strip.channelbags:
   for fc in bag.fcurves:
    for k in fc.keyframe_points:k.interpolation='LINEAR'
for f in [0,120]:
 sc.frame_set(f);assert max(abs(x-y)for row1,row2 in zip(bone.matrix,rows[f][2])for x,y in zip(row1,row2))<1e-5
r.animation_data.action=None
for b in r.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round5/lod0.blend'))
shutil.copyfile(P/'work/round5/lod0.blend',P/'work/master.blend')
runpy.run_path(str(P/'scripts/export_runtime.py'),run_name='__main__');runpy.run_path(str(P/'scripts/patch_string_export.py'),run_name='__main__');shutil.copyfile(P/'export/mm6_lzd_raw.glb',P/'export/mm6_lzd_lod0.glb')
(P/'review/round5/tabard_fall.json').write_text(json.dumps(trace,indent=2))
print('TABARD_FALL',[(r['frame'],r['before_deg'],r['after_deg'])for r in trace[::10]],flush=True)
