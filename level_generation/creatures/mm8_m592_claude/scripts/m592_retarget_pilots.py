"""Retarget the reviewed completed Ogre locomotion using the existing world-rotation tool."""
from pathlib import Path
import sys,runpy,os,json
import bpy
P=Path(__file__).resolve().parents[1];ogre=P.parent/'mm6_ogr_claude/export/mm6_ogr.glb';tool=P.parent/'mm8_m540_claude/scripts/retarget.py'
os.environ['SOURCE_TURN_DEG']='0'
sys.argv=[str(tool),'--',str(P/'work/rig_v1.blend'),str(P/'work/pilot_sources.blend')]+[f'{ogre}:{n}:{n}' for n in ('Walking','Running')]
runpy.run_path(str(tool),run_name='__main__')
sys.path.insert(0,str(P.parent/'mm6_natm_claude/scripts'));import common
out=P/'review/raw_locomotion';out.mkdir(exist_ok=True);rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
for name in ('Walking','Running'):
 a=bpy.data.actions[name];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i in range(5):
  f=a.frame_range[0]+(a.frame_range[1]-a.frame_range[0])*i/4;scene.frame_set(int(f),subframe=f%1)
  common.render_views(str(out/f'{name}_{i}'),1.0,2.8,views=('front','left'),resolution=(700,700))
