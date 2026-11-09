from pathlib import Path
import bpy,sys,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_reduced.blend'))
rig=bpy.data.objects['Rig'];rig.animation_data.action=bpy.data.actions['Walking'];rig.animation_data.action_slot=bpy.data.actions['Walking'].slots[0];bpy.context.scene.frame_set(19)
common.workbench_clay(bpy.context.scene)
common.render_views(str(p/'review/walk_contact19'),.85,1.85,views=('front','left','back'),resolution=(700,800))
print('WRIST',tuple(rig.pose.bones['B_L_Hand'].head),flush=True)
for fn,clip in [('1Hand.glb','SwordAttackR1'),('Armed.glb','ArmedDeath1')]:
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=30
    bpy.ops.import_scene.gltf(filepath=str(p.parents[2]/'anim_library/humanoid_set'/fn))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.name='Rig'
    a=next(a for a in bpy.data.actions if a.name.split('@')[-1].split('|')[-1]==clip);a.name=clip
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    path=p/'work/source_diagnostic.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
    sys.argv=['jerk','--',str(path),clip];runpy.run_path(str(p/'scripts/jerk_probe.py'),run_name='__main__')
