exec(open(__file__.replace('probe_edges.py','probe_rig.py')).read().split("for state in ('standing','rest'):")[0])
deps=bpy.context.evaluated_depsgraph_get();obj=body.evaluated_get(deps);mesh=obj.to_mesh()
bad=[]
for e in body.data.edges:
    a,b=e.vertices;original=(body.data.vertices[a].co-body.data.vertices[b].co).length
    current=(mesh.vertices[a].co-mesh.vertices[b].co).length
    if current>10 and current>original*3:
        bad.append((current,original,[(i,list(body.data.vertices[i].co),[(body.vertex_groups[g.group].name,round(g.weight,3)) for g in body.data.vertices[i].groups]) for i in (a,b)]))
print('STRETCHED',len(bad),sorted(bad,reverse=True)[:12],flush=True)
