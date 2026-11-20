import bpy,json,sys,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduce_natf as red
bpy.ops.wm.open_mainfile(filepath=str(P/'work/final_lod0.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene;objects=[bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']];sel=json.loads((P/'review/reduction_selected.json').read_text());out=P/'review/final/frames';out.mkdir(exist_ok=True)
common.workbench_clay(sc,True);sc.display.render_aa='32';sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.render.film_transparent=False;sc.display.shading.show_specular_highlight=False
for ob in objects:red.preview(ob,sel[ob.name]['0']['maps'],'natf_b');ob.hide_render=False
rows={}

a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0)
common.render_views(str(P/'review/round4/slim_preview'),.85,1.9,views=('front','left','three_quarter'),resolution=(500,650))
