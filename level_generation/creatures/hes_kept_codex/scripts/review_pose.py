"""CPU clay review of a named action/frame; authoring source is read-only."""
import bpy,sys,os,json
from mathutils import Vector,Matrix
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import kept_review_common as common
args=sys.argv[sys.argv.index('--')+1:];src,action,frame,tag=args[:4];prop=args[4]if len(args)>4 else None;kind=os.environ['KEPT_BODY']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
a=bpy.data.actions[action];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
f=float(frame);bpy.context.scene.frame_set(int(f),subframe=f%1)
m=bpy.data.materials.new('clay');m.diffuse_color=(.62,.65,.68,1);body.data.materials.clear();body.data.materials.append(m)
for f in body.data.polygons:f.material_index=0
if prop:
 assert kind=='male' and prop in ('pick','club')
 G=json.loads((P/'work/male/handle_R.json').read_text());A=Vector(G['handle_axis_hand_local']);S=json.loads((P/'work/male/source_rest.json').read_text())
 X=Matrix(S['B_R_Hand']['rot']).inverted()@(Vector(S['B_R_Finger2']['head'])-Vector(S['B_R_Hand']['head']));X=(X-A*X.dot(A)).normalized();R=Matrix((X,A.cross(X),A)).transposed().to_4x4();R.translation=Vector(G['handle_centre_hand_local'])
 with bpy.data.libraries.load(str(P/'work/props/props.blend'),link=False)as(data,to):to.objects=['hes_kept_'+prop]
 o=to.objects[0];bpy.context.scene.collection.objects.link(o);o.matrix_world=r.matrix_world@r.pose.bones['B_R_Hand'].matrix@R
common.workbench_clay(bpy.context.scene)
common.render_views(str(P/'review'/kind/tag),.8,2.2,views=('front','back','three_quarter'),resolution=(512,640))

sys.stdout.flush();sys.stderr.flush();os._exit(0)
