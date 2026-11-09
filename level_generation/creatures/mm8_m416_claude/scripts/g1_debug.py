from pathlib import Path
import bpy,sys,math,json
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'level_generation/creatures/mm6_natm_claude/scripts'));import common,armik
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_crossbow.blend'));scene=bpy.context.scene;rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');bpy.data.objects['Icosphere'].hide_render=True
print('RIG SCALE',list(rig.scale),[list(r) for r in rig.matrix_world], 'REST',list(rig.data.bones['B_R_Hand'].head_local));acts={a.name.split('@')[-1].split('|')[-1]:a for a in bpy.data.actions}
def act(n):
 a=acts[n];rig.animation_data.action=a
 if a.slots:rig.animation_data.action_slot=a.slots[0]
act('2HandCrossbowAimingFire');scene.frame_set(1)
local=Matrix(json.loads((P/'work/crossbow_source_attachment.json').read_text())['right_hand_matrix']);W0=armik.W(rig,'B_R_Hand')@local
left_rel=W0.inverted()@armik.W(rig,'B_L_Hand');right_rel=local.inverted();pose={p.name:p.matrix_basis.copy() for p in rig.pose.bones}
parts=[]
def box(center,dim):
 bpy.ops.mesh.primitive_cube_add();o=bpy.context.object;o.scale=Vector(dim)*.5;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.location=center;parts.append(o)
box((0,.19,.015),(.07,.95,.09));box((0,.66,.025),(.85,.05,.055));box((0,.43,.02),(.85,.012,.012));box((0,.43,.075),(.015,.67,.015))
for o in bpy.context.selected_objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();prop=bpy.context.object;mat=bpy.data.materials.new('Standin');mat.diffuse_color=(.5,.22,.06,1);prop.data.materials.append(mat)
act('2HandCrossbowIdle');scene.frame_set(1);idle={p.name:p.matrix_basis.copy() for p in rig.pose.bones};left_idle=armik.W(rig,'B_L_Hand').copy()
rig.animation_data.action=None;rig.animation_data.use_nla=False
common.workbench_clay(scene);out=P/'review/g1_authored';out.mkdir(exist_ok=True);rows=[];stats=[]
def smooth(x):return max(0,min(1,x))**2*(3-2*max(0,min(1,x)))
for i in range(34):
 t=i/30;raise_w=smooth(t/.35)*(1-smooth((t-.6)/.5));recoil=max(0,1-abs(t-.433)/.10)*.025
 for p in rig.pose.bones:p.matrix_basis=idle[p.name]
 bpy.context.view_layer.update()
 pitch=math.radians(70*(1-raise_w));direction=Vector((-.10,-math.cos(pitch),math.sin(pitch))).normalized();side=direction.cross(Vector((0,0,1))).normalized();up=side.cross(direction).normalized();B=Matrix((side,direction,up)).transposed().to_4x4()
 B.translation=Vector((-.43,-.18+recoil,1.62)).lerp(W0.translation,raise_w)
 for s,rel in [('R',right_rel),('L',left_rel)]:
  H=B@rel
  if s=='L':
   free=left_idle.copy();free.translation=Vector((.48,-.08,1.20));contact=smooth((t-.1)/.22)*(1-smooth((t-.65)/.3));q=free.to_quaternion().slerp(H.to_quaternion(),contact);M=q.to_matrix().to_4x4();M.translation=free.translation.lerp(H.translation,contact);H=M
  armik.solve(rig,s,H.translation,pole=Vector((-.9 if s=='R' else .9,.02,1.4)),hand_rot=H.to_3x3().normalized())
 prop.matrix_world=B;error=(armik.W(rig,'B_L_Hand').translation-(B@left_rel).translation).length
 stats.append({'time':t,'aim_weight':raise_w,'support_wrist_error':error,'pitch_deg':math.degrees(pitch)})
 if i in [0,5,9,12,15,20,26,33]:
  row=[]
  for view in ['front','left','three_quarter']:
   f=common.render_views(str(out/f'attack_{i:02}'),1.25,3.2,views=(view,),resolution=(240,360))[0];row.append([f,f'{t:.3f}s {view}'])
  rows.append(row)
print('CONTACT',[(r['time'],r['support_wrist_error']) for r in stats if .35<=r['time']<=.6])
(out/'frames.json').write_text(json.dumps(rows));(out/'measurements.json').write_text(json.dumps({'release_seconds':.4,'native_attack_seconds':1,'prototype_duration':1.1,'samples':stats},indent=2));print('G1 authored contact pass')
