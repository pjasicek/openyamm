"""Keep the presenting palm forward while angling the fingers clear of the forearm buckler."""
import bpy,sys,json,math,shutil,runpy
from pathlib import Path
from mathutils import Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
fit=json.loads((P/'work/round2_cast_fit.json').read_text());degrees=-46  # Refined at 48 Hz to clear the buckler throughout wind-up and recovery.
palm=Vector(json.loads((P/'gates.json').read_text())['hands']['L']['palm_axis'])
def smooth(a,b,x):
    t=min(1,max(0,(x-a)/(b-a)));return t*t*(3-2*t)
for level in range(4):
    file=P/f'work/runtime_lod{level}.blend';backup=P/f'work/round2_pre_roll_lod{level}.blend'
    if not backup.exists():shutil.copy2(file,backup)
    bpy.ops.wm.open_mainfile(filepath=str(backup));C.reset();r=bpy.data.objects['Rig'];a=bpy.data.actions['Cast'];C.activate('Cast')
    snapshots=[]
    for f in range(int(a.frame_range[1])+1):
        bpy.context.scene.frame_set(f);snapshots.append({b.name:b.matrix_basis.copy()for b in r.pose.bones})
    r.animation_data.action=None;rotations=[]
    for f,row in enumerate(snapshots):
        for b in r.pose.bones:b.matrix_basis=row[b.name]
        bpy.context.view_layer.update();h=r.pose.bones['B_L_Hand'];axis=(h.matrix.to_3x3()@palm).normalized()
        weight=smooth(4,23,f)*(1-smooth(38,68,f));q=Quaternion(axis,math.radians(degrees*weight))
        m=(q@h.matrix.to_quaternion()).to_matrix().to_4x4();m.translation=h.head;h.matrix=m
        rotations.append(h.rotation_quaternion.copy())
    r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];previous=None
    for f,q in enumerate(rotations):
        if previous and previous.dot(q)<0:q.negate()
        previous=q.copy();h=r.pose.bones['B_L_Hand'];h.rotation_quaternion=q;h.keyframe_insert('rotation_quaternion',frame=f,group=h.name)
    for layer in a.layers:
        for strip in layer.strips:
            for fc in strip.channelbag(a.slots[0]).fcurves:
                for k in fc.keyframe_points:k.interpolation='LINEAR'
    C.reset();r.location=(0,0,0)
    bone=r.data.bones['Buckler'].matrix_local
    for v in bpy.data.objects['BucklerMesh'].data.vertices:
        local=bone.inverted()@v.co
        if local.y>.075 and -.02<local.z<.08:
            local.y+=.0015*max(0,1-abs(local.x)/.09);v.co=bone@local
    if level==3:
        changes=[]
        for v in bpy.data.objects['BucklerMesh'].data.vertices:
            local=bone.inverted()@v.co
            if (local.x/.189)**2+(local.z/.244)**2>.75 and .013<local.y<.026:
                before=local.y;local.y=.012;v.co=bone@local;changes.append({'vertex':v.index,'shift_m':before-.012})
        assert changes and max(c['shift_m']for c in changes)<.015
        (P/'review/round2_far_buckler.json').write_text(json.dumps({'reason':'Restore the coarse back rim to the near mesh rear plane; inflated far rim touched the upper arm during Cast.', 'changes':changes},indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(file))
    if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
runpy.run_path(str(P/'scripts/quick_export.py'),run_name='__main__')
