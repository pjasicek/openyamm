"""Distribute counter-rotation through the neck and keep the jaw rigid on the head."""
import bpy,sys,json,numpy as np,runpy
from pathlib import Path
from mathutils import Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
def smooth(a,b,x):
    t=min(1,max(0,(x-a)/(b-a)));return t*t*(3-2*t)
for level in range(4):
    bpy.ops.wm.open_mainfile(filepath=str(P/f'work/review_round2_before/work/runtime_lod{level}.blend'))
    body=bpy.data.objects['Body'];original=[{body.vertex_groups[g.group].name:g.weight for g in v.groups}for v in body.data.vertices]
    file=P/f'work/runtime_lod{level}.blend';bpy.ops.wm.open_mainfile(filepath=str(file));C.reset();r=bpy.data.objects['Rig'];body=bpy.data.objects['Body']
    for v,part in zip(body.data.vertices,body.data.attributes['piece'].data):
        if part.value!=0 or v.co.z<1.32:continue
        x,y,z=v.co;old=original[v.index].copy()
        # Shoulder skin is not part of the neck; eliminate the old head/neck bleed over the trapezius.
        outside=smooth(.05,.09,abs(x))*(1-smooth(1.455,1.49,z));moved=0
        for n in ['B_Neck','B_Head']:
            w=old.get(n,0)*outside;old[n]=old.get(n,0)-w;moved+=w
        old['B_Spine2']=old.get('B_Spine2',0)+moved
        mix=smooth(1.32,1.40,z)*(1-smooth(.12,.19,abs(x)));mix=max(mix,smooth(1.46,1.50,z))
        front=smooth(.11,.155,-y);head=smooth(1.385-.025*front,1.53-.03*front,z)
        neck=(1-head)*smooth(1.32,1.42,z);new={'B_Spine2':1-head-neck,'B_Neck':neck,'B_Head':head}
        final={n:old.get(n,0)*(1-mix)+new.get(n,0)*mix for n in set(old)|set(new)};total=sum(final.values());assert abs(total-1)<1e-4
        for g in list(v.groups):body.vertex_groups[g.group].remove([v.index])
        for n,w in final.items():
            if w>1e-7:body.vertex_groups[n].add([v.index],w/total,'REPLACE')
    for a in bpy.data.actions:
        if a.name in ['Death','Dead']:continue
        C.activate(a.name);samples=[]
        for frame in range(int(a.frame_range[1])+1):
            bpy.context.scene.frame_set(frame);samples.append(({b.name:b.matrix_basis.copy()for b in r.pose.bones},r.pose.bones['B_Head'].matrix.to_quaternion().copy()))
        r.animation_data.action=None;out=[]
        for row,head_rotation in samples:
            for b in r.pose.bones:b.matrix_basis=row[b.name]
            bpy.context.view_layer.update();spine=r.pose.bones['B_Spine2'];delta=(spine.matrix.to_3x3()@spine.bone.matrix_local.to_3x3().inverted()).to_quaternion()
            n=r.pose.bones['B_Neck'];m=(Quaternion().slerp(delta,.55)@n.bone.matrix_local.to_quaternion()).to_matrix().to_4x4();m.translation=n.head;n.matrix=m;n.location=(0,0,0);n.scale=(1,1,1);bpy.context.view_layer.update()
            h=r.pose.bones['B_Head'];m=head_rotation.to_matrix().to_4x4();m.translation=h.head;h.matrix=m;h.location=(0,0,0);h.scale=(1,1,1);out.append((n.rotation_quaternion.copy(),h.rotation_quaternion.copy()))
        r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];previous={}
        for frame,rots in enumerate(out):
            for name,q in zip(['B_Neck','B_Head'],rots):
                if name in previous and previous[name].dot(q)<0:q.negate()
                previous[name]=q.copy();b=r.pose.bones[name];b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=frame,group=name)
        for layer in a.layers:
            for strip in layer.strips:
                for fc in strip.channelbag(a.slots[0]).fcurves:
                    for k in fc.keyframe_points:k.interpolation='LINEAR'
    C.reset();r.location=(0,0,0);bpy.ops.wm.save_as_mainfile(filepath=str(file))
    if level==0:bpy.ops.wm.save_as_mainfile(filepath=str(P/'export/mm6_natm.blend'))
runpy.run_path(str(P/'scripts/quick_export.py'),run_name='__main__')
