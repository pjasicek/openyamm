"""Measure generated UV density and strict texel overlap before using the return."""
import bpy,json,math,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_textured.blend'));me=bpy.data.objects['Body'].data;pv=np.array([a.value for a in me.attributes['piece'].data]);layer=__import__('os').environ['ARC1_UV_LAYER'];uv=me.uv_layers[layer].data;dens={};areas={};hits=np.zeros((1024,1024),np.uint16);collapsed=[];owner=np.full((1024,1024),-1,np.int32);unexpected_overlap=0
me.calc_loop_triangles()
for t in me.loop_triangles:
 if bool(me.attributes['head'].data[t.polygon_index].value)!=(layer=='HeadUV'):continue
 p=np.array([tuple(uv[i].uv) for i in t.loops]);a2=abs(np.cross(p[1]-p[0],p[2]-p[0]))/2;p3=np.array([tuple(me.vertices[i].co) for i in t.vertices]);a3=np.linalg.norm(np.cross(p3[1]-p3[0],p3[2]-p3[0]))/2;k=int(pv[t.vertices[0]])
 if a3>1e-10:
  dens.setdefault(k,[]).append(math.sqrt(a2/a3)*10.24);areas[k]=areas.get(k,0)+a2
  if a2<1e-12:collapsed.append(t.index)
 p*=1024;lo=np.maximum(np.floor(p.min(0)).astype(int),0);hi=np.minimum(np.ceil(p.max(0)).astype(int),1023)
 if np.any(hi<lo):continue
 x,y=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5);a,b,c=p;det=np.cross(b-a,c-a)
 if abs(det)<1e-10:continue
 w1=((x-a[0])*(c[1]-a[1])-(y-a[1])*(c[0]-a[0]))/det;w2=((b[0]-a[0])*(y-a[1])-(b[1]-a[1])*(x-a[0]))/det;m=(w1>1e-6)&(w2>1e-6)&(w1+w2<1-1e-6);prior=owner[lo[1]:hi[1]+1,lo[0]:hi[0]+1];unexpected_overlap+=int((m&(prior!=-1)&(~(np.isin(prior,[200,201,202]) & (k in [200,201,202])))).sum());prior[m]=k;hits[lo[1]:hi[1]+1,lo[0]:hi[0]+1]+=m
report={'parts':{str(k):{'density_px_cm_p10_p50_p90':np.percentile(v,[10,50,90]).tolist(),'uv_area':areas[k]} for k,v in dens.items()},'collapsed_triangles':collapsed,'covered_texels':int((hits>0).sum()),'overlap_texels':int((hits>1).sum()),'unexpected_overlap_texels':unexpected_overlap}
(P/f'review/uv_gate_{layer}.json').write_text(json.dumps(report,indent=2));print('UV GATE',report['covered_texels'],report['overlap_texels'],'overlap',len(collapsed),'collapsed')
assert not collapsed;assert report['unexpected_overlap_texels']/max(report['covered_texels'],1)<.01
