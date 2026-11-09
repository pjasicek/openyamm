from pathlib import Path
import bpy,ast,math
from mathutils import Vector,Quaternion,Matrix
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/authored.blend'));rig=bpy.data.objects['Rig'];FA=UA=.5
module=ast.parse((p/'scripts/twist_bones.py').read_text());nodes=[n for n in module.body if isinstance(n,ast.FunctionDef) and n.name in ('twist_about','bake_twist')]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'twist_bones.py','exec'),globals())
for act in [a for a in bpy.data.actions if a.use_fake_user]:bake_twist(act)
for act in bpy.data.actions:
    for layer in act.layers:
        for strip in layer.strips:
            for bag in strip.channelbags:
                for fc in bag.fcurves:
                    for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/authored.blend'))
