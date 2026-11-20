"""Refresh editable export, colour comparisons and existing shared clip sheets."""
import bpy,sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parents[1];R=P/'review/round6';sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
runpy.run_path(str(P/'scripts/run_jitter_r6.py'),run_name='__main__')
# Editable inspection/export scene uses the same fully assembled tier-A GLB as the viewer.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(P/'review/viewer/mm6_figc_a.glb'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig';rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
bpy.context.scene['runtime_source']='export/mm6_figc.glb; separate axe/shield with region ramps, all LODs. This editable scene is assembled LOD0, tier A.'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_figc_authoring.blend'))
for stage in ['round1','current','new']:
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30;bpy.ops.import_scene.gltf(filepath=str(R/f'palette_{stage}.glb'));rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(0);common.workbench_clay(bpy.context.scene,True)
 common.render_views(str(R/f'steel_{stage}'),.99,2.2,views=['front','three_quarter'],resolution=(600,800))
 # Same close-up camera on the axe carried by the accepted Standing pose.
 axe=next(o for o in bpy.data.objects if o.type=='MESH' and o.name.lower().startswith('axe'));lo,hi=common.world_bounds([axe]);c=(lo+hi)*.5
 common.render_views(str(R/f'axe_{stage}'),c.z,.82,views=['three_quarter'],resolution=(600,600),target=(c.x,c.y))
runpy.run_path(str(P/'scripts/render_final.py'),run_name='__main__')

runpy.run_path(str(P/'scripts/run_render_r6.py'),run_name='__main__')
