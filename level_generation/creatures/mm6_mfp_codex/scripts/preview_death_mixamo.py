"""G1: source mannequin, selected upright clips, side/front/three-quarter evidence."""
import bpy, sys, os, json, math, runpy
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]; ROOT=P.parents[2]; sys.dont_write_bytecode=True
os.chdir(P); sys.path.insert(0,str(P/'scripts'))
import common
L=ROOT/'anim_library/humanoid_set'; MX=ROOT/'anim_library/mixamo'
def run(script,args):
    sys.argv=[script,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/script),run_name='__main__')
run('source_rest.py',[L/'Armed.glb'])

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
run('retarget.py',['work/source_mannequin.blend','work/source_set.blend',f'{L}/2Hand Bow.glb:2HandBowIdle:Standing'])
run('retarget_mixamo.py',['work/source_set.blend','work/source_clips.blend',f'{MX}/Standing Death Forward 01.fbx:Forward1',f'{MX}/Standing Death Forward 02.fbx:Forward2',f'{MX}/Falling Forward Death.fbx:FallForward'])
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;common.workbench_clay(scene)
rows={}
for name in ['Forward1','Forward2','FallForward']:
 ac=bpy.data.actions[name];rig.animation_data.action=ac
 if len(ac.slots):rig.animation_data.action_slot=ac.slots[0]
 rows[name]=[];f0,f1=ac.frame_range
 for i in range(6):
  f=f0+(f1-f0)*i/5;scene.frame_set(int(f),subframe=f-int(f))
  for view in ['front','left','three_quarter']:
   out=P/'review/g1_mixamo';out.mkdir(exist_ok=True)
   path=common.render_views(str(out/f'{name}_{i}'),1.15,3.,views=(view,),resolution=(220,340))[0]
   rows[name].append({'frame':f,'view':view,'path':str(Path(path).relative_to(P))})
(P/'review/g1_mixamo/frames.json').write_text(json.dumps(rows,indent=2))
