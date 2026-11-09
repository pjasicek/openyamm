"""Ground the final falling body, cape and held wand; Dead is the exact last Death pose."""
from pathlib import Path
import bpy,ast,json
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_actions.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];wand=bpy.data.objects['Wand'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write'}],type_ignores=[]),'helpers','exec'),globals())
a=bpy.data.actions['Death'];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)];corrections=[]
for f,pose in enumerate(poses):
 apply(pose);low=100
 for ob in [body,wand]:
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(low,min((ob.matrix_world@v.co).z for v in me.vertices));ev.to_mesh_clear()
 b=rig.pose.bones['B_Pelvis'];m=b.matrix.copy();m.translation.z-=low;b.matrix=m;bpy.context.view_layer.update();poses[f]=current();corrections.append(-low)
write('Death',poses);write('Dead',[poses[-1] for _ in range(31)]);set_act(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/full_actions.blend'))
(p/'review/death_floor.json').write_text(json.dumps({'corrections_m':corrections},indent=2)+'\n')
print('DEATH_FLOOR_FINAL',min(corrections),max(corrections),flush=True)
