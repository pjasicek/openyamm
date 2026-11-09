import bpy,sys,runpy,json,math,os
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
import common
L=P.parents[2]/'anim_library/humanoid_set';MX=P.parents[2]/'anim_library/mixamo'
def run(name,args):
    sys.argv=[name,'--']+[str(a) for a in args];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
run('retarget_mixamo.py',[P/'work/source_motion.blend',P/'work/source_death.blend',str(MX/'Standing React Death Backward.fbx')+':Death',str(MX/'Sword And Shield Death.fbx')+':DeathSword'])
common.workbench_clay(bpy.context.scene);rig=bpy.data.objects['Rig'];rows=[]
for role in ['Death','DeathSword']:
    act=bpy.data.actions[role];rig.animation_data.action=act
    if act.slots:rig.animation_data.action_slot=act.slots[0]
    for view in ['front','left','three_quarter']:
        row=[]
        for i in range(5):
            f=act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/4;bpy.context.scene.frame_set(int(f),subframe=f-int(f))
            path=common.render_views(str(P/f'review/g1_mixamo_{role}_{view}_{i}'),1.25,2.9,(view,),resolution=(240,380))[0];row.append([path,f'{role} {view} {f:.0f}'])
        rows.append(row)
(P/'review/g1_death_frames.json').write_text(json.dumps(rows))
print('G1 PREVIEWS COMPLETE',flush=True)
