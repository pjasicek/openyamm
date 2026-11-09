import bpy,bmesh,sys
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--')+1])
me=bpy.data.objects['Head'].data
bm=bmesh.new();bm.from_mesh(me)
bd=[e for e in bm.edges if e.is_boundary]
print('BD',len(bd))
adj={}
for e in bd:
    a,b=e.verts; adj.setdefault(a,[]).append(b); adj.setdefault(b,[]).append(a)
seen=set()
for v in adj:
    if v in seen: continue
    st=[v];seen.add(v);c=[]
    while st:
        x=st.pop();c.append(x)
        for y in adj[x]:
            if y not in seen: seen.add(y);st.append(y)
    zs=[q.co.z for q in c];xs=[q.co.x for q in c];ys=[q.co.y for q in c]
    print('LOOP',len(c),'z',round(min(zs),3),round(max(zs),3),'x',round(min(xs),3),round(max(xs),3),'y',round(min(ys),3),round(max(ys),3),'deg',max(len(adj[q]) for q in c))
