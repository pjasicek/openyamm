import bpy,sys,runpy,json,math,os
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
import common
L=P.parents[2]/'anim_library/humanoid_set';MX=P.parents[2]/'anim_library/mixamo'
def run(name,args):
    sys.argv=[name,'--']+[str(a) for a in args];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
run('source_rest.py',[L/'Armed.glb'])
run('grip_from_source.py',[L/'Armed.glb','ArmedIdle:8'])
run('rom_extract.py',[f'Walking={L}/Armed.glb:ArmedWalk',f'Running={L}/Relax.glb:RelaxRunForward',f'Hit={L}/Unarmed.glb:UnarmedGetHitF1',f'Death={L}/Armed.glb:ArmedDeath1'])
for setname,clips in [('Armed',['ArmedWalk','ArmedDeath1']),('Relax',['RelaxRunForward']),('Unarmed',['UnarmedGetHitF1'])]:
    for view in ['front','left','three_quarter']:
        run('rpg_preview.py',[L/f'{setname}.glb',P/f'review/g1_{setname}_{view}',view,4]+clips)
# Clone the source mannequin onto its own normalized rest frames, to preview Mixamo using the production retarget.
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(L/'Armed.glb'))
src=next(o for o in bpy.data.objects if o.type=='ARMATURE');src.animation_data_clear()
for pb in src.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(m.type=='ARMATURE' for m in o.modifiers)]
turn=Matrix.Rotation(math.pi,4,'Z')
for ob in meshes:
    M=turn@ob.matrix_world
    for v in ob.data.vertices:v.co=M@v.co
    ob.parent=None;ob.matrix_world=Matrix.Identity(4);ob.modifiers.clear()
for o in list(bpy.data.objects):
    if o not in meshes:bpy.data.objects.remove(o,do_unlink=True)
for a in list(bpy.data.actions):bpy.data.actions.remove(a)
S=json.loads((P/'work/source_rest.json').read_text());ad=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',ad);bpy.context.collection.objects.link(rig);bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for n,s in S.items():
    b=ad.edit_bones.new(n);R=Matrix(s['rot']);b.head=s['head'];b.tail=b.head+R.col[1]*0.05;b.align_roll(R.col[2])
for n,s in S.items():
    if s['parent'] in S:ad.edit_bones[n].parent=ad.edit_bones[s['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
for ob in meshes:ob.parent=rig;ob.modifiers.new('Armature','ARMATURE').object=rig
bpy.context.scene['rig_offsets']=json.dumps({n:{'q':[1,0,0,0],'R_src':s['rot']} for n,s in S.items()});bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/source_mannequin.blend'))
run('retarget_mixamo.py',[P/'work/source_mannequin.blend',P/'work/source_motion.blend',str(MX/'Standard Idle.fbx')+':Standing',str(MX/'Sword And Shield Slash.fbx')+':Attack:plant',str(MX/'Standing Taunt Battlecry.fbx')+':Fidget:plant'])
common.workbench_clay(bpy.context.scene);rig=bpy.data.objects['Rig'];rows=[]
for role in ['Standing','Attack','Fidget']:
    act=bpy.data.actions[role];rig.animation_data.action=act
    if act.slots:rig.animation_data.action_slot=act.slots[0]
    for view in ['front','left','three_quarter']:
        row=[]
        for i in range(5):
            f=act.frame_range[0]+(act.frame_range[1]-act.frame_range[0])*i/4;bpy.context.scene.frame_set(int(f),subframe=f-int(f))
            path=common.render_views(str(P/f'review/g1_mixamo_{role}_{view}_{i}'),1.25,2.9,(view,),resolution=(240,380))[0];row.append([path,f'{role} {view} {f:.0f}'])
        rows.append(row)
(P/'review/g1_mixamo_frames.json').write_text(json.dumps(rows))
print('G1 PREVIEWS COMPLETE',flush=True)
