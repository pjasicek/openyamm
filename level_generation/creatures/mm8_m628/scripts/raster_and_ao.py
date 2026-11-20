"""UV coverage/position/class maps and short-range AO for the three fixed texture sets."""
import bpy,bmesh,json,sys,runpy
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];shared=P.parent/'claude_shared';N=1024
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
body=bpy.data.objects['Body'];me=body.data;rig=bpy.data.objects['Rig'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
piece=np.array([x.value for x in me.attributes['piece'].data]);head=np.array([x.value for x in me.attributes['head'].data]);co=np.array([tuple(v.co)for v in me.vertices])
classes=np.array([x.value for x in me.attributes['material_class'].data])
for f in me.polygons:
    if piece[f.vertices[0]]in[4001,4002]:
        for li,uv in zip(f.loop_indices,[(.004,.24),(.016,.24),(.01,.26)]):me.uv_layers['UVMap'].data[li].uv=uv
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
report=json.loads((P/'work/uv_coverage.json').read_text())if(P/'work/uv_coverage.json').exists()else{}
selected_kinds=sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else['body','head','bow']
for kind,layer in [('body','UVMap'),('head','HeadUV'),('bow','BowUV')]:
    if kind not in selected_kinds:continue
    uv=me.uv_layers[layer].data
    def keep(f):
        pid=piece[f.vertices[0]]
        return (pid<4000 and not head[f.index])or pid in[4001,4002]if kind=='body'else bool(head[f.index])if kind=='head'else pid in[4000,4003,4004]
    selected=[f for f in me.polygons if keep(f)];mask=np.full((N,N),-1,np.int32);pos=np.zeros((N,N,3),np.float32);cl=np.zeros((N,N),np.uint8);overlap=np.zeros((N,N),np.uint16)
    for f in selected:
        V=list(f.vertices);q=np.array([tuple(uv[i].uv)for i in f.loop_indices])*N
        x0,y0=np.maximum(np.floor(q.min(0)).astype(int),0);x1,y1=np.minimum(np.ceil(q.max(0)).astype(int),N-1)
        if x1<x0 or y1<y0:continue
        xs,ys=np.meshgrid(np.arange(x0,x1+1)+.5,np.arange(y0,y1+1)+.5);a,b,c=q
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1]);assert abs(den)>1e-10
        w0=((b[1]-c[1])*(xs-c[0])+(c[0]-b[0])*(ys-c[1]))/den
        w1=((c[1]-a[1])*(xs-c[0])+(a[0]-c[0])*(ys-c[1]))/den;w2=1-w0-w1
        m=(w0>=0)&(w1>=0)&(w2>=0);iy=(N-1-(ys[m]-.5)).astype(int);ix=(xs[m]-.5).astype(int)
        mask[iy,ix]=piece[V[0]];cl[iy,ix]=classes[f.index];pos[iy,ix]=sum(w[m,None]*co[v]for w,v in zip([w0,w1,w2],V));overlap[iy,ix]+=1
    np.savez_compressed(P/f'work/uvraster_{kind}.npz',piece=mask,pos=pos,material_class=cl)
    report[kind]={'coverage':float((mask>=0).mean()),'overlap_pixels':int(((overlap>1)&~np.isin(mask,[4001,4002])).sum()),'faces':len(selected)}
    # Bake a separate subset so other UV layers cannot overwrite the target image.
    ob=body.copy();ob.data=me.copy();scene.collection.objects.link(ob);ob.modifiers.clear();ob.parent=None
    bm=bmesh.new();bm.from_mesh(ob.data);bm.faces.ensure_lookup_table();ids={f.index for f in selected}
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.index not in ids],context='FACES');bm.to_mesh(ob.data);bm.free()
    ob.data.uv_layers.active=ob.data.uv_layers[layer];ob.data.uv_layers[layer].active_render=True
    body.hide_render=True
    sys.argv=['bake','--',ob.name,str(P/f'work/ao_{kind}.png'),'.035',str(N)]
    runpy.run_path(str(shared/'bake_creature_ao.py'),run_name='__main__')
    body.hide_render=False;bpy.data.objects.remove(ob,do_unlink=True)
(P/'work/uv_coverage.json').write_text(json.dumps(report,indent=2));print('UV COVERAGE',report)
