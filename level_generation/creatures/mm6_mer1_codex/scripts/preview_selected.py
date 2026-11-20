"""G1: source mannequin, selected upright clips, side/front/three-quarter evidence."""
import bpy, sys, os, json, math, runpy
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]; ROOT=P.parents[2]
os.chdir(P); sys.path.insert(0,str(P/'scripts'))
import common
L=ROOT/'anim_library/humanoid_set'; MX=ROOT/'anim_library/mixamo'
def run(script,args):
    sys.argv=[script,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
run('source_rest.py',[L/'Armed.glb'])
run('grip_from_source.py',[L/'Armed.glb','ArmedIdle:8'])
SRC=json.loads((P/'work/source_rest.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(L/'Armed.glb'))
src=next(o for o in bpy.data.objects if o.type=='ARMATURE');src.animation_data_clear()
for pb in src.pose.bones:pb.matrix_basis=Matrix()
bpy.context.view_layer.update();scale=src.matrix_world.to_scale()[0]
meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.parent==src]
TURN=Matrix.Rotation(math.pi,4,'Z')
for ob in meshes:
    M=TURN@ob.matrix_world
    ob.data.transform(M);ob.parent=None;ob.matrix_world=Matrix();ob.modifiers.clear()
for ob in list(bpy.data.objects):
    if ob not in meshes:bpy.data.objects.remove(ob,do_unlink=True)
for ac in list(bpy.data.actions):bpy.data.actions.remove(ac)
ad=bpy.data.armatures.new('Rig');rig=bpy.data.objects.new('Rig',ad);bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for n,s in SRC.items():
    eb=ad.edit_bones.new(n);R=Matrix(s['rot']);eb.head=Vector(s['head']);eb.tail=eb.head+R.col[1]*0.08;eb.align_roll(R.col[2])
for n,s in SRC.items():
    if s['parent'] in ad.edit_bones:ad.edit_bones[n].parent=ad.edit_bones[s['parent']]
bpy.ops.object.mode_set(mode='OBJECT')
for ob in meshes:
    ob.parent=rig;m=ob.modifiers.new('Rig','ARMATURE');m.object=rig
bpy.context.scene['rig_offsets']=json.dumps({n:{'q':[1,0,0,0],'R_src':s['rot']} for n,s in SRC.items()})
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/source_mannequin.blend'))
run('retarget.py',['work/source_mannequin.blend','work/source_set.blend',f'{L}/Armed.glb:ArmedIdle:GripRef',f'{L}/Armed.glb:ArmedWalk:Walking',f'{L}/Relax.glb:RelaxRunForward:Running',f'{L}/Unarmed.glb:UnarmedGetHitF1:Hit',f'{L}/Relax.glb:RelaxLaydownLayDown:Death'])
run('retarget_mixamo.py',['work/source_set.blend','work/source_clips.blend',f'{MX}/Standard Idle.fbx:Standing',f'{MX}/Sword And Shield Slash.fbx:Attack:plant',f'{MX}/Standing Idle 03 Examine.fbx:Fidget:plant',f'{MX}/Sword And Shield Slash.fbx:AttackFull:turn',f'{MX}/Standing Idle 03 Examine.fbx:FidgetFull:turn'])
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
g=json.loads((P/'work/grip_source.json').read_text());c=Vector(g['centre_hand'])*scale;axis=Vector(g['axis_hand'])
# A rigid source-grip blade makes slash versus pommel motion visible in G1.
bpy.ops.mesh.primitive_cube_add();sw=bpy.context.object;sw.name='Source sword stand-in'
sw.scale=(0.035,0.006,0.46);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
for v in sw.data.vertices:v.co=Vector((0,0,1)).rotation_difference(axis)@v.co+c+axis*0.42
rows={};posture={}
for name in ['Standing','Walking','Running','Attack','Hit','Death','Fidget']:
 ac=bpy.data.actions[name];rig.animation_data_create();rig.animation_data.action=ac
 if len(ac.slots):rig.animation_data.action_slot=ac.slots[0]
 f0,f1=ac.frame_range;rows[name]=[];posture[name]=[]
 for i in range(5):
  f=f0+(f1-f0)*i/4;scene.frame_set(int(f),subframe=f-int(f));sw.matrix_world=rig.matrix_world@rig.pose.bones['B_R_Hand'].matrix
  a=rig.pose.bones['B_Pelvis'].head;b=rig.pose.bones['B_Neck'].head
  posture[name].append({'frame':f,'pelvis_height':a.z,'trunk_lean_deg':math.degrees((b-a).angle(Vector((0,0,1))))})
  for view in ['front','left','three_quarter']:
   out=P/'review/g1_selected';out.mkdir(exist_ok=True)
   path=common.render_views(str(out/f'{name}_{i}'),1.05,3.1,views=(view,),resolution=(220,340))[0]
   rows[name].append({'view':view,'frame':f,'path':str(Path(path).relative_to(P))})
(P/'review/g1_selected/frames.json').write_text(json.dumps(rows,indent=2));(P/'review/g1_selected/posture.json').write_text(json.dumps(posture,indent=2))
assert len(rows)==7 and all(len(v)==15 for v in rows.values())
print('G1 source preview complete',flush=True)
