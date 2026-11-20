"""CPU closeups of the retained hand and actual generated grip surfaces."""
import bpy,bmesh,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/winged_hands.blend'));rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.delete(bm,geom=[v for v in bm.verts if abs(v.co.x)<.18 or v.co.z>.7],context='VERTS');bm.to_mesh(body.data);bm.free()
with bpy.data.libraries.load(str(P/'work/equipment_meshy.blend'),link=False) as (src,dst):dst.objects=['OV_pulse_pistol','OV_collar_rod']
for o in dst.objects:bpy.context.scene.collection.objects.link(o)
g=json.loads((P/'work/grip_pose.json').read_text());s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.device='CPU';s.cycles.samples=8;s.render.resolution_x=s.render.resolution_y=800;s.render.resolution_percentage=100;s.world.color=(.25,.25,.25)
for sd in 'LR':
 for n,q in g[sd]['finger_local'].items():rig.pose.bones[n].rotation_mode='QUATERNION';rig.pose.bones[n].rotation_quaternion=Quaternion(q)
 part='pulse_pistol' if sd=='L' else 'collar_rod';o=bpy.data.objects['OV_'+part];M=Matrix(g[sd]['rotation_bind']).to_4x4();M.translation=g[sd]['center_bind'];o.matrix_world=M
c=bpy.data.cameras.new('GripCamera');cam=bpy.data.objects.new('GripCamera',c);s.collection.objects.link(cam);s.camera=cam;c.type='ORTHO';c.ortho_scale=.3
for pos,power in [((1,-2,2),120),((-2,0,1),80)]:
 d=bpy.data.lights.new('GripLight','AREA');d.energy=power;d.size=2;o=bpy.data.objects.new('GripLight',d);s.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,-.24,.55))-o.location).to_track_quat('-Z','Y').to_euler()
for sd,sg in [('L',1),('R',-1)]:
 target=Vector((sg*.30,-.24,.55));cam.location=target+Vector((sg*.6,-.6,.25));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();s.render.filepath=str(P/'review'/f'grip_{sd}.png');bpy.ops.render.render(write_still=True)

bpy.data.objects['OV_collar_rod'].hide_render=True
C=Vector(g['L']['center_bind']);R=Matrix(g['L']['rotation_bind']);c.ortho_scale=.32
for name,local in [('side',(.7,-.4,.15)),('other',(-.7,-.3,.15)),('back',(.5,.7,.15))]:
 target=C+R@Vector((0,.02,0));cam.location=target+R@Vector(local);forward=(target-cam.location).normalized();right=forward.cross(R@Vector((0,0,1))).normalized();up=right.cross(forward);cam.rotation_euler=Matrix((right,up,-forward)).transposed().to_euler();s.render.filepath=str(P/'review'/f'pistol_grip_{name}.png');bpy.ops.render.render(write_still=True)
