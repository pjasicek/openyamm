"""Preview stored Mixamo two-hand performances on the existing fitted Cleric."""
from pathlib import Path
import sys, runpy, json, ast, math, hashlib
import bpy
from mathutils import Vector, Quaternion, Matrix
p=Path(__file__).resolve().parents[1]
root=p.parents[2]
sys.path.insert(0,str(p/'scripts'))
import common
clips=[('Standing 2H Magic Attack 01','CastForward'),
       ('Standing 2H Cast Spell 01','CastUpward'),
       ('Standing 2H Magic Attack 04','CastSustain'),
       ('Two Hand Spell Casting','CastTwoHand')]
template=p.parent/'mm6_natm_claude/scripts/retarget_mixamo.py'
code=template.read_text().replace("names = [b.name for b in rig.data.bones]", "names = [b.name for b in rig.data.bones if b.name in OFF]")
code=code.replace("['B_R_Finger0', 'B_R_Finger0.001', 'B_R_Finger0.002']", "['B_R_Finger0', 'B_R_Finger01', 'B_R_Finger02']")
sys.argv=[str(template),'--',str(p/'work/pre_dual_cast.blend'),str(p/'work/cast_candidates.blend')]+[
    str(root/f'anim_library/mixamo/{name}.fbx')+':'+role+':turn' for name,role in clips]
exec(compile(code,str(template),'exec'),{'__name__':'__main__','__file__':str(template)})
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;scene.render.fps=30
grip=json.loads((p/'work/grip_pose.json').read_text())
FA=.6;UA=.5
tree=ast.parse((p/'scripts/twist_bones.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'twist_about','bake_twist'}],type_ignores=[]),'twist','exec'),globals())
out=p/'review/cast_revision/candidates';out.mkdir(parents=True,exist_ok=True)
report=[]
for name,role in clips:
    a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    for f in range(int(a.frame_range[1])+1):
        scene.frame_set(f)
        for n,q in grip['finger_local'].items():
            pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
    bake_twist(a)
    rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
    common.workbench_clay(scene)
    frames=[]
    for i in range(7):
        f=a.frame_range[1]*i/6;scene.frame_set(int(f),subframe=f%1)
        images=common.render_views(str(out/f'{role}_{i:02d}'),.92,2.6,views=('front','three_quarter'),resolution=(360,440))
        frames.append({'time':f/30,'images':[str(Path(x).relative_to(p)) for x in images]})
    source=root/f'anim_library/mixamo/{name}.fbx'
    report.append({'name':name,'action':role,'source':str(source.relative_to(root)),
        'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'duration':a.frame_range[1]/30,'frames':frames})
    print('CANDIDATE',role,flush=True)
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/cast_candidates.blend'))
(out/'candidates.json').write_text(json.dumps(report,indent=2)+'\n')
