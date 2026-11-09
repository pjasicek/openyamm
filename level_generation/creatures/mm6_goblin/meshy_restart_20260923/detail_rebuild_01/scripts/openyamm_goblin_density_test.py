import bpy,json,traceback
from pathlib import Path
OUT=Path('/home/pjasicek/github/OpenYAMM/level_generation/creatures/mm6_goblin/meshy_restart_20260923/detail_rebuild_01')
s=bpy.data.scenes['Goblin - Complete Low Mesh Detail Test'];bpy.context.window.scene=s
src=bpy.data.scenes['Goblin - Rebuilt Skirt and Belt v2'].objects['Goblin_Body_WithFittedWaist']
def run():
 try:
  results=[]
  for invert in [False,True]:
   o=src.copy();o.data=src.data.copy();o.name='Goblin_WeightedTrial_'+str(invert);s.collection.objects.link(o);o.hide_set(False);o.hide_render=False;o.hide_viewport=False
   bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
   vg=o.vertex_groups.new(name='Head priority')
   for v in o.data.vertices:
    w=max(0,min(1,(v.co.z-.62)/.07));vg.add([v.index],w,'REPLACE')
   m=o.modifiers.new('Regional trial','DECIMATE');m.ratio=8800/sum(len(p.vertices)-2 for p in o.data.polygons);m.use_collapse_triangulate=True;m.vertex_group=vg.name;m.vertex_group_factor=5;m.invert_vertex_group=invert;bpy.ops.object.modifier_apply(modifier=m.name)
   row={'name':o.name,'head':sum(len(p.vertices)-2 for p in o.data.polygons if p.center.z>.66),'tris':sum(len(p.vertices)-2 for p in o.data.polygons)};results.append(row);o.hide_render=True;o.hide_set(True)
  (OUT/'weighted_trial.json').write_text(json.dumps(results,indent=2))
 except Exception:(OUT/'weighted_error.txt').write_text(traceback.format_exc())
 return None
bpy.app.timers.register(run,first_interval=.1);print('Testing regional head preservation at a fixed body budget.')
