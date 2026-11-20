"""Neutral material review of the final animated body and separately painted head."""
from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'export/mm8_m460.blend'))
rig=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc,textured=True)
for material in bpy.data.materials:
    if not material.use_nodes:continue
    for n in material.node_tree.nodes:
        if n.type=='TEX_IMAGE' and n.image and 'basecolor' in n.image.name:material.node_tree.nodes.active=n
out=p/'review/textured';out.mkdir(exist_ok=True)
for role,f in [('Standing',0),('Walking',6),('Attack',29),('Hit',4),('Death',30),('Dead',0)]:
    a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(f)
    common.render_views(str(out/role),.9,2.4,views=('front','left','back','three_quarter'),resolution=(650,850))
    if role=='Standing':common.render_views(str(out/'head'),1.57,.5,views=('front','left','back','three_quarter'),resolution=(700,700))
