from pathlib import Path
import bpy,sys,json
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene
common.workbench_clay(scene)
rows=[]
for view in ('front','left'):
    rows=[]
    for role in ('Standing','Walking','Running','Attack','Hit','Death','Fidget'):
        act=bpy.data.actions[role];rig.animation_data.action=act
        if len(act.slots):rig.animation_data.action_slot=act.slots[0]
        row=[]
        for i in range(5):
            f=act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/4
            scene.frame_set(int(f),subframe=f-int(f))
            path=common.render_views(str(p/f'review/pilot/{view}_{role}_{i}'),.82,2.25,views=(view,),resolution=(280,420))[0]
            row.append([path,f'{role} {f/scene.render.fps:.2f}s'])
        rows.append(row)
    (p/f'review/pilot/{view}.json').write_text(json.dumps(rows))
