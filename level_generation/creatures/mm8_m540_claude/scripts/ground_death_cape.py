"""Fit the final cape to the ground plane without suspending the fallen body above it."""
from pathlib import Path
import bpy,ast,json,math,numpy as np
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
source=p/'work/rig_uv.blend'; backup=p/'work/rig_uv_before_ground.blend'
if not backup.exists():
 import shutil;shutil.copyfile(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(backup))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];wand=bpy.data.objects['Wand'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
helpers=ast.unparse(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write'}],type_ignores=[]))
helpers=helpers.replace("if n == 'B_Pelvis':","if n in ['B_Pelvis','Cape0','Cape1','Cape2']:")
exec(helpers,globals())
piece=np.array([x.value for x in body.data.attributes['piece'].data]);skin=np.isin(piece,[0,2,3,4]);cape=np.array([x.value for x in body.data.attributes['cape'].data])>0
faces=[tuple(f.vertices) for f in body.data.polygons if all(skin[i] for i in f.vertices)]
axis=rig.data.bones['Cape0'].matrix_local.to_3x3().inverted()@Vector((1,0,0))
def coords(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[ob.matrix_world@v.co for v in me.vertices];ev.to_mesh_clear();return pts


act=bpy.data.actions['Death'];poses=[sample(act,f) for f in range(int(act.frame_range[1])+1)];reports=[]
angles={'Cape0':2,'Cape1':-14,'Cape2':-35};axes={n:rig.data.bones[n].matrix_local.to_3x3().inverted()@Vector((1,0,0)) for n in angles}
for f,pose in enumerate(poses):
 phase=np.clip((f-23)/10,0,1);phase=phase*phase*(3-2*phase)
 for n,degree in angles.items():
  q,l=pose[n];pose[n]=(q@Quaternion(axes[n],math.radians(degree*phase+(3*math.sin(math.pi*np.clip((f-23)/10,0,1))**2 if n=='Cape0' else 0))),l)
 apply(pose);low=min(v.z for ob in [body,wand] for v in coords(ob));pb=rig.pose.bones['B_Pelvis'];m=pb.matrix.copy();m.translation.z-=low;pb.matrix=m;bpy.context.view_layer.update();poses[f]=current();P=np.array([tuple(v) for v in coords(body)])
 reports.append({'frame':f,'skin_floor':float(P[skin,2].min()),'cape_floor':float(P[cape,2].min()),'phase':float(phase)})
write('Death',poses);write('Dead',[poses[-1] for _ in range(31)]);set_act(None)
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(source))
(p/'review/grounded_death.json').write_text(json.dumps({'samples':reports,'settled_hinges_degrees':angles},indent=2)+'\n');print('GROUNDED_FINAL',reports[-1],flush=True)
