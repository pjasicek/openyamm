import bpy,sys,json,math,itertools
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(p/'work/round1_motion.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];staff=bpy.data.objects['Staff'];scene=bpy.context.scene
import arm_solver as sol
side=sol.Side('B_R_');act=bpy.data.actions['Cast'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];scene.frame_set(108)
base={b.name:b.matrix_basis.copy() for b in rig.pose.bones};rig.animation_data.action=None
pv=np.array([a.value for a in body.data.attributes['piece'].data]);faces=[tuple(f.vertices) for f in body.data.polygons if all(pv[i]!=3 for i in f.vertices)]
axis=Vector((.20,-1,.10)).normalized();out=[]
def evaluate(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();v=[x.co.copy() for x in m.vertices];ev.to_mesh_clear();return v
for x,y,z,pole in itertools.product([-.34,-.39,-.44,-.49],[-.08,-.16,-.24],[1.12,1.20,1.28],[( -.45,-.15,-1),(-1,1,-.5),(-1,0,0),(0,1,-1)]):
 for n,m in base.items():rig.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update();grip=Vector((x,y,z));pole=Vector(pole);r=side.solve(grip,axis,pole,steps=72)
 if r['miss']>.002:continue
 side.apply(r)
 fb,hb=[rig.data.bones['B_R_'+b] for b in ['Forearm','Hand']];seg=(fb.matrix_local.inverted()@hb.head_local).normalized();dq=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion()@(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion().inverted()
 def twist(q,a):return (2*math.atan2(Vector((q.x,q.y,q.z)).dot(a),q.w)+math.pi)%(2*math.pi)-math.pi
 rig.pose.bones['B_R_ForearmTwist'].rotation_quaternion=Quaternion(seg,.5*twist(dq,seg));ub=rig.data.bones['B_R_UpperArm'];seg=(ub.matrix_local.inverted()@fb.head_local).normalized();rig.pose.bones['B_R_UpperArmTwist'].rotation_quaternion=Quaternion(seg,-.5*twist(rig.pose.bones[ub.name].matrix_basis.to_quaternion(),seg));bpy.context.view_layer.update()
 V=evaluate(body);tree=BVHTree.FromPolygons(V,faces);sv=evaluate(staff);depth=0
 for v in sv:
  q,n,fi,d=tree.find_nearest(v,.06)
  if q is not None and (v-q).dot(n)<-.7*d:depth=max(depth,d)
 angle=math.degrees((r['W']-r['E']).angle(axis))
 cost=depth*10000+max(0,r['sw']-60)+max(0,70-angle)+max(0,angle-110)+(grip-Vector((-.39,-.20,1.2))).length*30
 out.append({'grip':list(grip),'pole':list(pole),'depth_mm':depth*1000,'angle':angle,'sw':r['sw'],'tw':r['tw'],'phi':r['phi'],'cost':cost})
out.sort(key=lambda x:x['cost']);print('BEST',json.dumps(out[:12]),flush=True);(p/'work/round1_cast_search.json').write_text(json.dumps(out,indent=2))
