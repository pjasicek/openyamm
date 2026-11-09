"""Final posed fist, isolated without changing the saved rig."""
import bpy,bmesh,sys,os
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import kept_review_common as common
src,side=sys.argv[sys.argv.index('--')+1:];kind=os.environ['KEPT_BODY']
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src));r=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];a=bpy.data.actions['Kept_Attack'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];bpy.context.scene.frame_set(12)
h=(r.matrix_world@r.pose.bones[f'B_{side}_Hand'].matrix).translation;k=sum((r.matrix_world@r.pose.bones[f'B_{side}_Finger{i}'].head for i in (1,2,3,4)),Vector())/4;c=h.lerp(k,1.25)
ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());bm=bmesh.new();bm.from_mesh(ev.to_mesh());ev.to_mesh_clear();bm.transform(body.matrix_world);bmesh.ops.delete(bm,geom=[v for v in bm.verts if (v.co-c).length>.16],context='VERTS');m=bpy.data.meshes.new('PosedHand');bm.to_mesh(m);bm.free();o=bpy.data.objects.new('PosedHand',m);bpy.context.scene.collection.objects.link(o)
for x in bpy.data.objects:
 if x.type=='MESH' and x!=o:x.hide_render=True
mat=bpy.data.materials.new('clay');mat.diffuse_color=(.65,.68,.7,1);m.materials.clear();m.materials.append(mat);common.workbench_clay(bpy.context.scene)
# Orbit in the posed hand frame; opposite views expose the thumb and the back of the fist.
H=(r.matrix_world@r.pose.bones[f'B_{side}_Hand'].matrix).to_3x3()
for name,d in [('front',H@Vector((0,0,1))),('back',H@Vector((0,0,-1))),('side',H@Vector((1,0,0)))]:
 cam=common.ortho_camera('hand',c+d.normalized(),(0,0,0),.28);cam.rotation_mode='QUATERNION';cam.rotation_quaternion=(-d).to_track_quat('-Z','Y');sc=bpy.context.scene;sc.camera=cam;sc.render.resolution_x=sc.render.resolution_y=360;sc.render.filepath=str(P/'review'/kind/f'final_fist_{side}_{name}.png');bpy.ops.render.render(write_still=True)

sys.stdout.flush();sys.stderr.flush();os._exit(0)
