"""Continuous quaternion keys, fractional string release and subframe floor checks."""
import bpy,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1]
blend=Path(sys.argv[sys.argv.index('--')+1]) if '--' in sys.argv else P/'work/motion_complete.blend'
bpy.ops.wm.open_mainfile(filepath=str(blend))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene

def curves(a):return [fc for l in a.layers for s in l.strips for c in s.channelbags for fc in c.fcurves]
def continuous():
    for a in bpy.data.actions:
        qs={}
        for fc in curves(a):
            for k in fc.keyframe_points:k.interpolation='LINEAR'
            if fc.data_path.endswith('rotation_quaternion'):qs.setdefault(fc.data_path,{})[fc.array_index]=fc
        for cs in qs.values():
            assert len(cs)==4
            prev=None
            for j in range(len(cs[0].keyframe_points)):
                q=[cs[i].keyframe_points[j].co.y for i in range(4)]
                if prev and sum(x*y for x,y in zip(q,prev))<0:
                    for i in range(4):cs[i].keyframe_points[j].co.y*=-1
                    q=[-x for x in q]
                prev=q
        for fc in curves(a):fc.update()
def action(a):
    rig.animation_data.action=a
    if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def freeze(a,f):
    action(a);scene.frame_set(int(f),subframe=float(f%1));snap={b.name:b.matrix_basis.copy()for b in rig.pose.bones}
    action(None)
    for n,m in snap.items():rig.pose.bones[n].matrix_basis=m
    bpy.context.view_layer.update()
def mesh():
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    co=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',co);ev.to_mesh_clear();return co.reshape(-1,3)
def smooth(x):x=float(np.clip(x,0,1));return x*x*(3-2*x)
continuous();piece=np.array([x.value for x in body.data.attributes['piece'].data])
faces=[tuple(f.vertices)for f in body.data.polygons if all(piece[i]==5 for i in f.vertices)]
data=json.loads(scene['bow_local']);a=bpy.data.actions['Attack'];release=float(scene['attack_impact_seconds'])*30
retimed=bool(scene.get('attack_opening_retimed'))
end=22. if retimed else float(a.frame_range[1])
boundaries=[17.999,18.001,release-.001,release+.001]
if retimed:
    boundaries=[(f-13)*22/9 if f<22 else f for f in boundaries]
    # The stretched keys expose old interpolation gaps; rebuild only the opening's prop contacts.
    for fc in curves(a):
        if any('pose.bones["'+n+'"]' in fc.data_path for n in ['Arrow','StringTop','StringBottom']):
            for i in range(len(fc.keyframe_points)-1,-1,-1):
                if fc.keyframe_points[i].co.x<end:fc.keyframe_points.remove(fc.keyframe_points[i],fast=True)
            fc.update()
frames=sorted(set([float(x)for x in np.arange(0,end+.01,.125)]+[f for f in boundaries if 0<=f<=end]))
for f in frames:
    freeze(a,f);bm=rig.pose.bones['Bow'].matrix.copy()
    tips=[rig.pose.bones[n].matrix@rig.data.bones[n].matrix_local.inverted()@rig.data.bones['Bow'].matrix_local@Vector(v)
        for n,v in zip(json.loads(scene['bow_tip_bones']),data['tips'])]
    mid=tips[0].lerp(tips[1],(.6317-.065)/(.6317+.6868))
    target=rig.pose.bones['B_R_Finger11'].head.lerp(rig.pose.bones['B_R_Finger12'].head,.5)
    direction=(bm.translation-target).normalized();xyz=mesh()
    tree=BVHTree.FromPolygons([Vector(v)for v in xyz],faces,all_triangles=False)
    hit=tree.ray_cast(target+direction*.06,-direction,.10)
    if hit[0]is not None:target=hit[0]+direction*.0006
    source_frame=13+f*9/22 if retimed and f<22 else f
    nock=mid.lerp(target,smooth((source_frame-18)/3)*(1-smooth((source_frame-release+.5)/.5)))
    for name,start in zip(['StringTop','StringBottom'],tips):
        d=nock-start;M=d.to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=start
        rig.pose.bones[name].matrix=M@Matrix.Scale(d.length,4)
    d=bm@Vector((0,-.02,.065))-nock;M=d.to_track_quat('Z','Y').to_matrix().to_4x4();M.translation=nock
    rig.pose.bones['Arrow'].matrix=M@Matrix.Scale(1 if 18<=source_frame<release else .00001,4)
    bpy.context.view_layer.update();action(a)
    for name in ['Arrow','StringTop','StringBottom']:
        b=rig.pose.bones[name]
        for prop in ['rotation_quaternion','location','scale']:b.keyframe_insert(prop,frame=f)
continuous()
# Only add root keys where interpolation puts a surface below the floor.
gn={g.index:g.name for g in body.vertex_groups}
feet=np.array([v.index for v in body.data.vertices if sum(g.weight for g in v.groups if
    gn[g.group]in ['B_L_Foot','B_R_Foot','B_L_Toe0','B_R_Toe0'])>.7])
body_ids=np.where(piece<4000)[0];report={}
for a in bpy.data.actions:
    corrections=[]
    for f in np.arange(0,float(a.frame_range[1])+.01,.25):
        freeze(a,float(f));co=mesh();low=float(co[body_ids if a.name in ['Death','Dead']else feet,2].min())
        if low<-.001:
            b=rig.pose.bones['B_Pelvis'];M=b.matrix.copy();M.translation.z+=.001-low;b.matrix=M
            bpy.context.view_layer.update();action(a);b.keyframe_insert('location',frame=float(f))
            corrections.append({'frame':float(f),'lift':.001-low})
    report[a.name]=corrections
continuous();action(None)
for b in rig.pose.bones:b.matrix_basis.identity()
(P/'work/subframe_motion.json').write_text(json.dumps({'release_frame':release,'prop_frames':frames,'floor_corrections':report},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
print('SUBFRAME FLOOR', {n:len(x)for n,x in report.items()})
