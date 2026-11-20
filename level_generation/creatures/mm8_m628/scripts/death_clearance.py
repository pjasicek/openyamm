"""Keep the released bow outside the falling body; preserve all body motion and other actions."""
import bpy,json,sys,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
report={}
for filename in ['motion_complete','textured_uv']:
    bpy.ops.wm.open_mainfile(filepath=str(P/f'work/{filename}.blend'))
    rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;me=body.data
    piece=np.array([x.value for x in me.attributes['piece'].data]);bodyfaces=[tuple(f.vertices)for f in me.polygons if piece[f.vertices[0]]<4000]
    bowedges=[tuple(e.vertices)for e in me.edges if piece[e.vertices[0]]in[4000,4004]and piece[e.vertices[1]]in[4000,4004]]
    bowids=np.where(np.isin(piece,[4000,4004]))[0];rest=rig.data.bones['Bow'].matrix_local.copy();local={i:rest.inverted()@me.vertices[int(i)].co for i in bowids}
    tips=[Vector(v)for v in json.loads(scene['bow_local'])['tips']]
    def action(a):
        rig.animation_data.action=a
        if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
    def pose(a,f):
        action(a);scene.frame_set(int(f),subframe=float(f%1));p={b.name:b.matrix_basis.copy()for b in rig.pose.bones}
        action(None)
        for n,m in p.items():rig.pose.bones[n].matrix_basis=m
        bpy.context.view_layer.update()
    a=bpy.data.actions['Death'];pose(a,8);start=rig.pose.bones['Bow'].matrix.copy();pose(a,31);end=rig.pose.bones['Bow'].matrix.copy();end.translation.y-=.60
    rows=[];final={};previous={}
    for f in np.arange(0,31.001,.25):
        pose(a,float(f))
        if f>8:
            t=min(1,(f-8)/15);s=t*t*(3-2*t);q=start.to_quaternion().slerp(end.to_quaternion(),s)
            M=q.to_matrix().to_4x4();M.translation=start.translation.lerp(end.translation,t)
            M.translation.z=end.translation.z+(start.translation.z-end.translation.z)*(1-t*t)
            low=min((M@v).z for v in local.values());M.translation.z+=max(0,.002-low)
            rig.pose.bones['Bow'].matrix=M;bpy.context.view_layer.update()
        M=rig.pose.bones['Bow'].matrix.copy();pts=[M@v for v in tips];mid=pts[0].lerp(pts[1],(.6317-.065)/(.6317+.6868))
        for n,pt in zip(['StringTop','StringBottom'],pts):
            d=mid-pt;sm=d.to_track_quat('Z','Y').to_matrix().to_4x4();sm.translation=pt;rig.pose.bones[n].matrix=sm@Matrix.Scale(d.length,4)
        bpy.context.view_layer.update()
        ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();co=[v.co.copy()for v in em.vertices];ev.to_mesh_clear()
        tree=BVHTree.FromPolygons(co,bodyfaces,all_triangles=False);hits=0
        for ia,ib in bowedges:
            d=co[ib]-co[ia]
            if d.length<1e-6:continue
            hit=tree.ray_cast(co[ia],d.normalized(),d.length)
            if hit[0]is not None and 1e-5<hit[3]<d.length-1e-5:hits+=1
        rows.append({'frame':float(f),'body_edge_intersections':hits,'bow_floor':min(co[int(i)].z for i in bowids)})
        final={n:rig.pose.bones[n].matrix_basis.copy()for n in ['Bow','StringTop','StringBottom']};action(a)
        for n,m in final.items():
            b=rig.pose.bones[n];b.matrix_basis=m;q=b.rotation_quaternion.copy()
            if n in previous and q.dot(previous[n])<0:q.negate();b.rotation_quaternion=q
            previous[n]=q.copy()
            for prop in ['rotation_quaternion','location','scale']:b.keyframe_insert(prop,frame=float(f))
    dead=bpy.data.actions['Dead'];action(dead)
    for f in range(31):
        for n,m in final.items():
            b=rig.pose.bones[n];b.matrix_basis=m
            for prop in ['rotation_quaternion','location','scale']:b.keyframe_insert(prop,frame=f)
    for act in [a,dead]:
        for l in act.layers:
            for s in l.strips:
                for cb in s.channelbags:
                    for fc in cb.fcurves:
                        for k in fc.keyframe_points:k.interpolation='LINEAR'
    report[filename]=rows
    if filename=='textured_uv':
        common.workbench_clay(scene)
        for f in [8,12,16,23,31]:
            action(a);scene.frame_set(f);common.render_views(str(P/f'review/death_clear_{f}'),.6,4,
                views=('front','three_quarter'),resolution=(800,500))
    bad=[r for r in rows if r['frame']>=12 and r['body_edge_intersections']]
    print(filename,'INTERSECTIONS',[(r['frame'],r['body_edge_intersections'])for r in rows if r['body_edge_intersections']])
    assert not bad,bad
    action(None)
    for b in rig.pose.bones:b.matrix_basis.identity()
    bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/{filename}.blend'))
(P/'work/death_clearance.json').write_text(json.dumps(report,indent=2))
