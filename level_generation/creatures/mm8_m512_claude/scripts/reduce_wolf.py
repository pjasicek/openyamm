"""Test 10% triangle-reduction steps on the weighted pilot, protecting muzzle, jaw and paws."""
import bpy
import json
import numpy as np
from pathlib import Path
from mathutils.bvhtree import BVHTree

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'review/reduction';OUT.mkdir(exist_ok=True)
reports=[]
def surface(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    points=[v.co.copy() for v in me.vertices];faces=[list(f.vertices) for f in me.polygons]
    ev.to_mesh_clear();return points,BVHTree.FromPolygons(points,faces,all_triangles=False)

for step in range(1,11):
    bpy.ops.wm.open_mainfile(filepath=str(PROJECT/'work/anim_v1.blend'))
    mesh=bpy.data.objects['Wolf'];rig=bpy.data.objects['Wolf_Rig'];sc=bpy.context.scene
    rig.animation_data.action=None
    for bone in rig.pose.bones:bone.matrix_basis.identity()
    bpy.context.view_layer.update()
    reference=mesh.copy();reference.data=mesh.data.copy();reference.name='Reference';sc.collection.objects.link(reference)
    protect=mesh.vertex_groups.new(name='ReductionProtection')
    fixed=[v.index for v in mesh.data.vertices if sum(g.weight for g in v.groups
            if mesh.vertex_groups[g.group].name in ['Head','Jaw','FrontPaw_L','FrontPaw_R','HindPaw_L','HindPaw_R'])>.4]
    protect.add(fixed,1,'REPLACE')
    bpy.ops.object.select_all(action='DESELECT');mesh.select_set(True);bpy.context.view_layer.objects.active=mesh
    mod=mesh.modifiers.new('Reduce','DECIMATE');mod.ratio=.9**step;mod.vertex_group=protect.name
    mod.invert_vertex_group=True;mod.vertex_group_factor=1000;mod.use_collapse_triangulate=True
    bpy.ops.object.modifier_move_to_index(modifier=mod.name,index=0);bpy.ops.object.modifier_apply(modifier=mod.name)
    mesh.vertex_groups.remove(mesh.vertex_groups['ReductionProtection'])
    bpy.ops.object.vertex_group_limit_total(limit=4);bpy.ops.object.vertex_group_normalize_all(lock_active=False)
    mesh.data.calc_loop_triangles()
    errors=[];minimum=1.;poses={}
    for name,times in [('Standing',[0,1]),('Walking',[.125,.375,.625,.875]),
                       ('Running',[.15625,.46875]),('Attack',[.25,.5,.75,.875]),
                       ('Hit',[.25]),('Death',[.25,.45,.625]),('Dead',[0])]:
        rig.animation_data.action=bpy.data.actions[name]
        for t in times:
            frame=t*24+1;sc.frame_set(int(frame),subframe=frame%1)
            a,at=surface(reference);b,bt=surface(mesh)
            e=[at.find_nearest(v)[3] for v in b]+[bt.find_nearest(v)[3] for v in a]
            errors.extend(e);minimum=min(minimum,min(v.z for v in b));poses[f'{name}:{t}']=np.percentile(e,[99,100]).tolist()
    p99,maximum=np.percentile(errors,[99,100]);passed=p99<=.0015 and maximum<=.008 and minimum>-.015
    report={'step':step,'ratio':.9**step,'triangles':len(mesh.data.loop_triangles),'protected_vertices':len(fixed),
            'surface_error_p99_max_m':[p99,maximum],'minimum_z':minimum,'poses':poses,'numerical_pass':bool(passed),
            'visual_review':'pending'}
    reports.append(report);print('REDUCTION',json.dumps({k:v for k,v in report.items() if k!='poses'}),flush=True)
    bpy.data.objects.remove(reference,do_unlink=True)
    rig.animation_data.action=bpy.data.actions['Standing'];sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/f'step_{step:02d}.blend'))
    (OUT/f'step_{step:02d}.json').write_text(json.dumps(report,indent=2)+'\n')
    if not passed:break
(OUT/'ladder.json').write_text(json.dumps(reports,indent=2)+'\n')
