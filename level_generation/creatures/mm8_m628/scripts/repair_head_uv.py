"""Move only overlapping head triangles into empty atlas space, keeping pixel scale and paint correspondence."""
import bpy,json
import numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];N=1024
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_uv.blend'))
me=bpy.data.objects['Body'].data;uv=me.uv_layers['HeadUV'].data
faces=[f for f in me.polygons if me.attributes['head'].data[f.index].value]
q={f.index:np.array([tuple(uv[i].uv)for i in f.loop_indices])*N for f in faces}
def raster(excluded):
    canvas=np.full((N,N),-1,np.int32);pairs=set();overlap=0
    for f in faces:
        n=f.index
        if n in excluded:continue
        t=q[n];lo=np.maximum(np.floor(t.min(0)).astype(int),0);hi=np.minimum(np.ceil(t.max(0)).astype(int),N-1)
        x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=t
        den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        w0=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den;w1=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        m=(w0>1e-4)&(w1>1e-4)&(w0+w1<1-1e-4);xx=x[m].astype(int);yy=y[m].astype(int);old=canvas[yy,xx]
        overlap+=int((old>=0).sum());pairs.update((int(k),n)for k in old if k>=0);canvas[yy,xx]=n
    return canvas,pairs,overlap
canvas,pairs,count=raster(set());original=sorted(pairs);selected=set()
while pairs:
    candidates={n for pair in pairs for n in pair}
    def score(n):return sum(n in pair for pair in pairs)/max(1,float(np.prod(np.ptp(q[n],axis=0)+4)))
    best=max(candidates,key=score);selected.add(best);pairs={pair for pair in pairs if best not in pair}
canvas,_,_=raster(selected);occupied=canvas>=0;patches=[]
for n in sorted(selected,key=lambda n:-np.prod(np.ptp(q[n],axis=0)+6)):
    t=q[n];lo=np.maximum(np.floor(t.min(0)).astype(int)-3,0);hi=np.minimum(np.ceil(t.max(0)).astype(int)+3,N-1)
    w,h=hi-lo+1;integral=np.pad(occupied.astype(np.int32),((1,0),(1,0))).cumsum(0).cumsum(1)
    sums=integral[h:,w:]-integral[:-h,w:]-integral[h:,:-w]+integral[:-h,:-w]
    candidates=np.argwhere(sums==0);assert len(candidates),(n,w,h)
    dy,dx=map(int,candidates[0]);occupied[dy:dy+h,dx:dx+w]=True
    delta=np.array([dx-lo[0],dy-lo[1]])/N
    for li in me.polygons[n].loop_indices:uv[li].uv=tuple(np.array(uv[li].uv)+delta)
    q[n]=q[n]+delta*N
    patches.append({'face':n,'source':[int(lo[0]),int(N-1-hi[1]),int(w),int(h)],'destination':[dx,int(N-dy-h)],'uv_translation':delta.tolist()})
_,after_pairs,after=raster(set());assert after==0,(after,after_pairs)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/textured_uv.blend'))
(P/'work/head_uv_repairs.json').write_text(json.dumps({'before_overlap_pixels':count,'after_overlap_pixels':after,
    'affected_face_pairs':original,'patches':patches,'method':'Translate charts and copy the same source texture pixels, without rescaling or changing geometry.'},indent=2));print('UV REPAIR',count,'pixels',len(patches),'triangles, final',after)
