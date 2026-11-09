import bpy,json,traceback
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/detail_rebuild_01')
s=bpy.data.scenes['Goblin - Complete Low Mesh Detail Test'];bpy.context.window.scene=s;src=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2'].objects['Goblin_Body_WithFittedWaist']
def run():
 try:
  results=[]
  for weight in [.15,.4]:
   o=src.copy();o.data=src.data.copy();o.name='Goblin_Weighted_'+str(weight);s.collection.objects.link(o);o.hide_set(False);o.hide_render=False;o.hide_viewport=False;bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
   vg=o.vertex_groups.new(name='Reduction weights')
   for v in o.data.vertices:
    t=max(0,min(1,(v.co.z-.62)/.07));w=1-t*(1-weight);vg.add([v.index],w,'REPLACE')
   m=o.modifiers.new('Regional reduction','DECIMATE');m.ratio=8800/sum(len(p.vertices)-2 for p in o.data.polygons);m.use_collapse_triangulate=True;m.vertex_group=vg.name;m.vertex_group_factor=1;bpy.ops.object.modifier_apply(modifier=m.name)
   results.append({'name':o.name,'head':sum(len(p.vertices)-2 for p in o.data.polygons if p.center.z>.66),'tris':sum(len(p.vertices)-2 for p in o.data.polygons)});o.hide_render=True;o.hide_set(True)
  (OUT/'weighted_refine.json').write_text(json.dumps(results,indent=2))
 except Exception:(OUT/'weighted_refine_error.txt').write_text(traceback.format_exc())
 return None
bpy.app.timers.register(run,first_interval=.1);print('Rebalancing nonzero reduction weights.')
