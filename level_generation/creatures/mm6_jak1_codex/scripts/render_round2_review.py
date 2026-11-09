"""Refresh the authoring file, actual runtime sheets, closeups and final switch-size comparisons."""
import bpy,runpy,sys,json,subprocess,math
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common,reduction_rebake as red
for script in ['final_authoring.py','render_final.py']:runpy.run_path(str(P/'scripts'/script),run_name='__main__')
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
for name,role,t,focus,scale,direction in [
 ('staff_hand','Standing',0,'B_R_Hand',.36,(.5,-1,.3)),
 ('free_hand','Standing',0,'B_L_Hand',.38,(.5,-1,.2)),
 ('soles','Standing',0,None,.85,(.2,-1,.04)),
 ('fidget_shoulder','Fidget',1.65,'B_L_UpperArm',.8,(.5,-1,.4)),
 ('two_hand_impact','Attack',json.loads((P/'review/blow_gate.json').read_text())[0]['impact_s'],'B_Spine',1.9,(.5,-1,.25)),
 ('death_wrap','Death',1.46,'B_Pelvis',1.5,(.7,-1,1.3))]:
 floor=[]
 if name=='soles':
  for tag,color in [('Ground',(.38,.4,.42,1)),('Grid',(.22,.24,.26,1))]:
   mat=bpy.data.materials.new(tag);mat.diffuse_color=color
   if tag=='Ground':
    bpy.ops.mesh.primitive_plane_add(size=3,location=(0,0,-.0002));ob=bpy.context.object;ob.data.materials.append(mat);floor.append(ob)
   else:
    for axis in range(2):
     for i in range(-10,11):
      location=[0,0,0];location[axis]=i*.1;bpy.ops.mesh.primitive_cube_add(size=1,location=location);ob=bpy.context.object;ob.dimensions=(.001,2,.0002) if axis==0 else (2,.001,.0002);ob.data.materials.append(mat);floor.append(ob)
 action=bpy.data.actions[role];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0];f=t*scene.render.fps;scene.frame_set(int(f),subframe=float(f-int(f)));center=(rig.matrix_world@rig.pose.bones[focus].matrix).translation if focus else Vector((0,-.02,.06));d=Vector(direction).normalized();cam=common.ortho_camera('Review camera',center+d*5,(0,0,0),scale);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');scene.camera=cam;scene.render.resolution_x=900;scene.render.resolution_y=700;scene.render.filepath=str(P/f'review/round2/{name}.png');bpy.ops.render.render(write_still=True);bpy.data.objects.remove(cam,do_unlink=True)
 for ob in floor:bpy.data.objects.remove(ob,do_unlink=True)
selected=json.loads((P/'review/round2/reduction/selection.json').read_text());maps=P/selected['maps'];rows=[]
for row in json.loads((P/'review/round2/reduction/lod_selection.json').read_text()):
 level=row['level'];bpy.ops.wm.open_mainfile(filepath=str(P/selected['blend']));red.render(bpy.data.objects['Jackalman'],bpy.data.objects['Rig'],f'final_reference{level}',maps,row['pixels']);bpy.ops.wm.open_mainfile(filepath=str(P/row['blend']));red.render(bpy.data.objects['Jackalman'],bpy.data.objects['Rig'],f'final_lod{level}',maps,row['pixels'])
 def compare(ref):return json.loads(subprocess.check_output(['/usr/bin/python3',str(P/'scripts/reduction_images.py'),'compare',str(P/'review/round2/reduction'),ref,f'final_lod{level}'],text=True))
 result={'level':level,'pixels':row['pixels'],'reference':f'final_reference{level}'if level<3 else'lod3_incoming','against_reference':compare(f'final_reference{level}'if level<3 else'lod3_incoming')}
 if level==3:result['against_full_lod0']=compare('final_reference3')
 rows.append(result);print('FINAL LOD METRIC',level,result['against_reference']['pooled_iou'],flush=True)
(P/'review/round2/reduction/final_lod_metrics.json').write_text(json.dumps(rows,indent=2))
