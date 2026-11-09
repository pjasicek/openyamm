from pathlib import Path
import bpy,sys
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_textured_uv.blend'))
r=bpy.data.objects['Rig'];sc=bpy.context.scene;common.workbench_clay(sc)
for o in bpy.data.objects:
    if o.type=='MESH':o.hide_render=o.name!='Body'
for name,frames in [('Attack',[0,15,24,30,38]),('Walking',[0,6,12]),('Death',[12,24,57])]:
    a=bpy.data.actions[name];r.animation_data.action=a
    if a.slots:r.animation_data.action_slot=a.slots[0]
    for f in frames:
        sc.frame_set(f);common.render_views(str(p/f'review/armour_fix/{name}-{f}'),1.2,1.0,views=('front','left'),resolution=(700,700))
