from pathlib import Path
import sys,runpy,bpy
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(P/'scripts'));import common
sys.argv=['retarget_mixamo.py','--',str(P/'work/rig_v1.blend'),str(P/'work/extra_sources.blend'),str(R/'anim_library/mixamo/Standard Run.fbx')+':Running',str(R/'anim_library/mixamo/Two Handed Sword Death.fbx')+':Death']
runpy.run_path(str(P/'scripts/retarget_mixamo.py'),run_name='__main__')
r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc)
for nm in ['Running','Death']:
 a=bpy.data.actions[nm];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for i in range(7):
  sc.frame_set(round(a.frame_range[1]*i/6));common.render_views(str(P/f'review/source_{nm}_{i}'),1.0,3.2,views=('front','left'),resolution=(340,480))
