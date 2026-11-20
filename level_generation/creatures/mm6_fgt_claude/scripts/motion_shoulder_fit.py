"""Keep the silver shoulder rim attached to its underlying copper pad in the wider swing."""
import bpy,json,numpy as np
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree

def fit(project):
    rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
    rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    bpy.context.scene.frame_set(0)
    me.calc_loop_triangles();parts=np.array([v.value for v in me.attributes['piece'].data])
    old=np.array([v.co[:] for v in me.vertices]);uv={l.name:np.array([x.uv[:] for x in l.data]) for l in me.uv_layers}
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();posed=[v.co.copy() for v in mesh.vertices];ev.to_mesh_clear()
    faces=[t.vertices[:] for t in me.loop_triangles if all(parts[i]==11 for i in t.vertices)]
    tree=BVHTree.FromPolygons(posed,faces,all_triangles=True)
    transforms={g.name:rig.pose.bones[g.name].matrix@rig.data.bones[g.name].matrix_local.inverted() for g in body.vertex_groups}
    changes=[]
    for i in np.where(parts==7)[0]:
        # Only the outer rim overlaps the copper cap; retain the chest-mounted inner plate.
        lateral=np.clip((-old[i,0]-.15)/.045,0,1)
        height=np.clip((old[i,2]-1.27)/.065,0,1)
        share=float(lateral*height)
        if share<1e-6:continue
        loc,normal,fi,distance=tree.find_nearest(posed[i])
        if distance>.08:continue
        face=faces[fi];pts=np.array([posed[v] for v in face]);point=np.array(loc)
        bary=np.linalg.lstsq(np.vstack([pts.T,np.ones(3)]),np.r_[point,1.],rcond=None)[0]
        bary=np.clip(bary,0,1);bary/=bary.sum()
        weights={}
        for v,a in zip(face,bary):
            for g in me.vertices[v].groups:
                name=body.vertex_groups[g.group].name;weights[name]=weights.get(name,0)+float(a)*g.weight*share
        for g in me.vertices[i].groups:
            name=body.vertex_groups[g.group].name;weights[name]=weights.get(name,0)+g.weight*(1-share)
        weights=dict(sorted(weights.items(),key=lambda item:-item[1])[:4]);total=sum(weights.values())
        weights={n:w/total for n,w in weights.items()}
        skin=Matrix([[sum(w*transforms[n][r][c] for n,w in weights.items()) for c in range(4)] for r in range(4)])
        me.vertices[i].co=skin.inverted()@posed[i]
        for group in body.vertex_groups:group.remove([int(i)])
        for name,w in weights.items():body.vertex_groups[name].add([int(i)],w,'REPLACE')
        changes.append({'vertex':int(i),'before':old[i].tolist(),'after':list(me.vertices[i].co),'weights':weights})
    me.update()
    for change in changes:change['normal']=list(me.vertices[change['vertex']].normal)
    for layer in me.uv_layers:assert np.array_equal(uv[layer.name],np.array([x.uv[:] for x in layer.data]))
    bpy.context.view_layer.update();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
    maximum=max((mesh.vertices[c['vertex']].co-posed[c['vertex']]).length for c in changes);ev.to_mesh_clear()
    assert maximum<1e-5,maximum
    (project/'review/motion_preview/shoulder_fit.json').write_text(json.dumps({'standing_max_error_m':maximum,'changes':changes},indent=2)+'\n')
    print('SHOULDER_FIT',len(changes),'vertices; standing error',maximum,flush=True)
