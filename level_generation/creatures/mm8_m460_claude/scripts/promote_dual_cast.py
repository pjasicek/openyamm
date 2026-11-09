"""Verify unchanged geometry/other clips and select the fitted two-handed cast."""
from pathlib import Path
import bpy,json,hashlib
import numpy as np
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
def snapshot():
    result={}
    for name in ['Body','Staff']:
        ob=bpy.data.objects[name];data=[]
        for v in ob.data.vertices:data.append([list(v.co),[(g.group,g.weight) for g in v.groups]])
        result[name]=hashlib.sha256(json.dumps(data).encode()).hexdigest()
    for a in bpy.data.actions:
        if a.name in ['Attack','Cast']:continue
        rows=[]
        for l in a.layers:
            for s in l.strips:
                for b in s.channelbags:
                    for fc in b.fcurves:
                        rows.append([fc.data_path,fc.array_index,[(list(k.co),k.interpolation) for k in fc.keyframe_points]])
        result[a.name]=hashlib.sha256(json.dumps(rows).encode()).hexdigest()
    return result
bpy.ops.wm.open_mainfile(filepath=str(p/'work/pre_dual_cast.blend'));before=snapshot()
bpy.ops.wm.open_mainfile(filepath=str(p/'work/cast_fitted.blend'));after=snapshot()
assert before==after,(before,after)
rig=bpy.data.objects['Rig'];rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Socket_RightPalm');hand=rig.data.edit_bones['B_R_Hand']
b.head=hand.head.lerp(rig.data.edit_bones['B_R_Finger2'].head,.7)
b.tail=b.head+Vector((0,0,.035));b.parent=hand;b.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
assert len(rig.data.bones)==124
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_uv.blend'))
(p/'review/cast_revision/unchanged.json').write_text(json.dumps({'geometry_weights_and_other_clips':before,'verified_identical':True},indent=2)+'\n')
print('UNCHANGED',list(before))
