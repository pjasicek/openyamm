import bpy,sys,collections
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_common as C
for label,path in [('high','work/round2/master.blend'),('low','work/round2/body_lod0.blend')]:
 bpy.ops.wm.open_mainfile(filepath=str(P/path));C.reset();o=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];a=o.data.attributes['piece'];ns=[g.name for g in o.vertex_groups]
 for pid in [0,1,11]:
  groups=collections.Counter();nums=collections.Counter()
  for v in o.data.vertices:
   if a.data[v.index].value==pid:
    nums[len(v.groups)]+=1
    for g in v.groups:groups[ns[g.group]]+=1
  print(label,pid,'GROUPS',groups,'NUMS',nums)
 common.workbench_clay(bpy.context.scene);bpy.context.scene.display.shading.color_type='SINGLE';bpy.context.scene.display.shading.single_color=(.3,.5,.3)
 common.render_views(str(P/'review/round2'/f'diagnose_{label}_rest'),1.2,1.4,views=('front','left'),resolution=(650,800))
 C.activate('Attack',.4);common.render_views(str(P/'review/round2'/f'diagnose_{label}_attack'),1.2,1.4,views=('front','left'),resolution=(650,800))
