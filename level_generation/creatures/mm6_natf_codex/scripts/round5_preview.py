import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduce_natf as red
sel=json.loads((P/'review/reduction_selected.json').read_text());a=27/48;b=64/48
warp=lambda t:t/1.3 if t<=a else a/1.3+t-a if t<=b else a/1.3+b-a+(t-b)/1.3
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
with bpy.data.libraries.load(str(P/'review/round5/before/work/accepted_master.blend'))as(src,dst):dst.actions=['Attack']
old=dst.actions[0];old.name='AttackBefore'
common.workbench_clay(sc,True);sc.display.render_aa='32';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.film_transparent=False;sc.display.shading.show_specular_highlight=False
for n in ['Body','ForearmBlade','LeafShield']:red.preview(bpy.data.objects[n],sel[n]['0']['maps'],'natf_a')
for rev,ac in [('before',old),('after',bpy.data.actions['Attack'])]:
 rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0]
 for frame in [48,56,64]:
  t=frame/48 if rev=='before'else warp(frame/48);f=t*60;sc.frame_set(int(f),subframe=float(f%1));common.render_views(str(P/f'review/round5/{rev}_{frame}'),1.13,1.30,views=('front','right','three_quarter'),resolution=(480,600),target=(.05,-.27))
