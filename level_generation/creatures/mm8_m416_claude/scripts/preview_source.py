from pathlib import Path
import bpy,sys,math,json
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];R=P.parents[2];sys.path.insert(0,str(R/'level_generation/creatures/mm6_natm_claude/scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/source_crossbow.blend'));scene=bpy.context.scene;arm=next(o for o in bpy.data.objects if o.type=='ARMATURE');bpy.data.objects['Icosphere'].hide_render=True
acts={a.name.split('@')[-1].split('|')[-1]:a for a in bpy.data.actions}
def action(name):
 a=acts[name];arm.animation_data.action=a
 if a.slots:arm.animation_data.action_slot=a.slots[0]
 return a

def palm(s):return arm.matrix_world@((arm.pose.bones[f'B_{s}_Hand'].head+arm.pose.bones[f'B_{s}_Finger2'].head)*.5)
action('2HandCrossbowAiming');scene.frame_set(18)
r,l=palm('R'),palm('L');axis=(l-r).normalized();up=Vector((0,0,1));side=axis.cross(up).normalized();up=side.cross(axis).normalized();basis=Matrix((side,axis,up)).transposed().to_4x4();basis.translation=r
local=(arm.matrix_world@arm.pose.bones['B_R_Hand'].matrix).inverted()@basis
parts=[]
def box(name,center,dim):
 bpy.ops.mesh.primitive_cube_add();o=bpy.context.object;o.name=name;o.scale=Vector(dim)*.5;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.location=center;parts.append(o)
box('stock',(0,.19,.015),(.07,.95,.09));box('bow',(0,.66,.025),(.85,.05,.055));box('string',(0,.43,.02),(.85,.012,.012));box('bolt',(0,.43,.075),(.015,.67,.015))
for o in bpy.context.selected_objects:o.select_set(False)
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();prop=bpy.context.object;prop.matrix_world=basis;prop.color=(.5,.22,.06,1)
mat=bpy.data.materials.new('Wood standin');mat.diffuse_color=(.5,.22,.06,1);prop.data.materials.append(mat)
common.workbench_clay(scene);rows=[];measure={};out=P/'review/g1_source';out.mkdir(exist_ok=True)
clips=['2HandCrossbowIdle','2HandCrossbowAiming','2HandCrossbowAimingFire','2HandCrossbowReload','2HandCrossbowWalk','2HandCrossbowGetHitF1','2HandCrossbowDeath1']
for c in clips:
 act=action(c);f0,f1=act.frame_range;series=[]
 for f in range(round(f0),round(f1)+1):
  scene.frame_set(f);W=arm.matrix_world@arm.pose.bones['B_R_Hand'].matrix@local
  series.append({'frame':f,'pitch':math.degrees(math.asin(max(-1,min(1,(W.to_3x3()@Vector((0,1,0))).normalized().z)))),'support_distance':(palm('L')-(W@Vector((0,(l-r).length,0)))).length})
 measure[c]={'duration':(f1-f0)/30,'samples':series};row=[]
 for i in range(6):
  f=f0+(f1-f0)*i/5;scene.frame_set(int(f),subframe=f-int(f));prop.matrix_world=arm.matrix_world@arm.pose.bones['B_R_Hand'].matrix@local
  for view in ['front','left','three_quarter']:
   file=common.render_views(str(out/f'{c}_{i}'),1.25,3.2,views=(view,),resolution=(240,360))[0];row.append([file,f'{c} {f:.1f} {view}'])
 rows.append(row)
(P/'work/g1_source_measurements.json').write_text(json.dumps(measure,indent=2));(out/'frames.json').write_text(json.dumps(rows));(P/'work/crossbow_source_attachment.json').write_text(json.dumps({'right_hand_matrix':[list(row) for row in local],'support_distance':(l-r).length},indent=2))
print('G1 rendered',len(rows)*18,'frames')
