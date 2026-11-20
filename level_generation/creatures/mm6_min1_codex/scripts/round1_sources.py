import bpy,sys,json,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P.parents[2]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round1_baseline.blend'))
sc=bpy.context.scene;r=bpy.data.objects['Rig'];sf=json.loads((P/'work/source_rest.json').read_text());off={n:{'R_src':sf[n]['rot'] if n in sf else [list(row) for row in b.matrix_local.to_3x3()]} for n,b in r.data.bones.items()};sc['rig_offsets']=json.dumps(off)
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.co.x/=4;k.handle_left.x/=4;k.handle_right.x/=4
 a.frame_end/=4
sc.render.fps=30;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round1_source_base.blend'))
items=[]
for file,name in [('Great Sword Slash (2).fbx','DownSlash'),('Great Sword Slash (4).fbx','PowerSlash'),('Standing Melee Attack Downward.fbx','AxeDown')]:
 for mode in ['plant','turn']:items.append(str(R/'anim_library/mixamo'/file)+':'+name+mode+':'+mode)
sys.argv=['retarget','--',str(P/'work/round1_source_base.blend'),str(P/'work/round1_sources.blend')]+items
runpy.run_path(str(R/'level_generation/creatures/mm6_bar1_claude/scripts/retarget_mixamo.py'),run_name='__main__')
