import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C,common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/review_round3_before/work/runtime_lod0.blend'));C.activate('Standing',0);r=bpy.data.objects['Rig'];sc=bpy.context.scene
report={'standing':{b.name:[list(v)for v in b.matrix]for b in r.pose.bones},'rest':{b.name:[list(v)for v in b.matrix_local]for b in r.data.bones}}
report['standing_basis']={b.name:[list(v)for v in b.matrix_basis]for b in r.pose.bones}
C.activate('Attack',21/48);report['old_attack21']={b.name:[list(v)for v in b.matrix]for b in r.pose.bones}
C.reset();body=bpy.data.objects['Body'];parts={}
for v,p in zip(body.data.vertices,body.data.attributes['piece'].data):parts.setdefault(p.value,[]).append(list(v.co))
report['parts']={str(p):{'n':len(v),'min':np.min(v,0).tolist(),'max':np.max(v,0).tolist()}for p,v in parts.items()}
common.clear_scene();bpy.ops.import_scene.gltf(filepath=str(P.parents[2]/'anim_library/humanoid_set/2Hand Spear.glb'));r=next(o for o in bpy.data.objects if o.type=='ARMATURE');a=next(a for a in bpy.data.actions if a.name.endswith('2HandSpearAttack10'));r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];turn=Matrix.Rotation(math.pi,4,'Z')@r.matrix_world;lo,hi=a.frame_range
report['source']={};report['source_rest_pelvis']=list(turn@r.data.bones['B_Pelvis'].head_local)
for i in range(77):
 phase=np.interp(i,[0,21,34,43,76],[0,.25,.5,.65,1]);f=lo+(hi-lo)*phase;sc.frame_set(int(f),subframe=f%1)
 report['source'][str(i)]={b.name:[list(v)for v in turn@b.matrix]for b in r.pose.bones}
(P/'work/round3_pose_reference.json').write_text(json.dumps(report))
