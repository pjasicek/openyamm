"""Full actual equipment review at five poses per clip, with a denser release strip."""
import bpy,sys,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/export_reimport.blend'));rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene,textured=True);rows=[]
# Reload the final colour correction into this geometry-only reimport checkpoint.
for mat in bpy.data.materials:
 if mat.use_nodes:
  for node in mat.node_tree.nodes:
   if node.type=='TEX_IMAGE' and node.image and node.image.name.startswith('head_basecolor_1k'):
    node.image=bpy.data.images.load(str(P/'textures/head_basecolor_1k.png'),check_existing=True)

for an in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Dead','Fidget']:
 act=bpy.data.actions[an];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];row=[]
 for i,f in enumerate(np.linspace(*act.frame_range,5)):
  scene.frame_set(int(f),subframe=float(f%1));paths=common.render_views(str(P/f'review/master_frames/{an}_{i}'),.87,3.25 if an in ('Death','Dead')else 2.45,views=('front','left','three_quarter'),resolution=(440,500));row.append({'frame':float(f),'paths':paths})
 rows.append({'action':an,'frames':row})
act=bpy.data.actions['Attack'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f in [13,16,19,21,22,23,24,27]:
 scene.frame_set(f);common.render_views(str(P/f'review/release_{f}'),1.25,1.4,views=('front','left','three_quarter'),resolution=(720,720),target=(0,-.28))
(P/'review/master_frames/index.json').write_text(json.dumps(rows,indent=2))

act=bpy.data.actions['Cast'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f in [0,9,15,22,27,39,51]:
 scene.frame_set(f);common.render_views(str(P/f'review/cast_key_{f}'),.87,2.45,views=('front','left','three_quarter'),resolution=(560,650))
