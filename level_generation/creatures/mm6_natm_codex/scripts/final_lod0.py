import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/lod0_850charts.blend'));r=bpy.data.objects['Rig'];r.animation_data.action=None
for name in ['Attack','Cast','Hit']:bpy.data.actions.remove(bpy.data.actions[name])
with bpy.data.libraries.load(str(P/'work/motion_soft.blend'),link=False)as(src,dst):dst.actions=['Attack','Cast','Hit']
receipt={}
for name,target in [('Attack',76),('Cast',76),('Death',160)]:
 a=bpy.data.actions[name];end=float(a.frame_range[1]);factor=target/end
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for k in fc.keyframe_points:k.co.x*=factor;k.handle_left.x*=factor;k.handle_right.x*=factor
     fc.update()
 a.frame_end=target;receipt[name]={'old_seconds':end/48,'seconds':target/48,'factor':factor}
for a in bpy.data.actions:a.use_fake_user=True
for pb in r.pose.bones:pb.matrix_basis.identity()
for im in bpy.data.images:
 if im.source=='FILE'and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/final_lod0.blend'));(P/'review/action_retiming.json').write_text(json.dumps(receipt,indent=2))
