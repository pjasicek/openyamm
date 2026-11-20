"""Clear the reduced front panel and verify the retained rig before painting."""
from pathlib import Path
import bpy,ast,math,runpy
from mathutils import Vector,Quaternion
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_reduced.blend'))
rig=bpy.data.objects['Rig'];scene=bpy.context.scene;names=[b.name for b in rig.data.bones]
tree=ast.parse((p/'scripts/author_pilots.py').read_text())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'set_act','sample','apply','current','write'}],type_ignores=[]),'helpers','exec'),globals())
a=bpy.data.actions['Running'];poses=[sample(a,f) for f in range(int(a.frame_range[1])+1)]
axis=rig.data.bones['LoinFront'].matrix_local.to_3x3().inverted()@Vector((1,0,0))
for pose in poses:
 q,l=pose['LoinFront'];pose['LoinFront']=(q@Quaternion(axis,math.radians(-5)),l)
write('Running',poses);set_act(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_reduced.blend'))
runpy.run_path(str(p/'scripts/check_reduced_actions.py'),run_name='__main__')
