import sys,json;sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tools')
from geom import *
from PIL import ImageFont
def plot(x0,y0,x1,y1,upp,out,rebuilt=None,zmin=-99999,zmax=99999,grid=512):
    W=int((x1-x0)/upp);H=int((y1-y0)/upp)
    im=Image.new('RGB',(W,H),(20,20,24));dr=ImageDraw.Draw(im)
    T=lambda p:((p[0]-x0)/upp,H-(p[1]-y0)/upp)
    import colorsys
    for si,s in enumerate(S):
        for i in s['floor_faces']:
            p=fpts(i);zs=[q[2] for q in p];z=sum(zs)/len(zs)
            if z<zmin or z>zmax: continue
            if max(q[0] for q in p)<x0 or min(q[0] for q in p)>x1 or max(q[1] for q in p)<y0 or min(q[1] for q in p)>y1: continue
            h=((z+2400)/2600)%1.0;walk=nrm(i)[2]>0.9
            c=colorsys.hsv_to_rgb(h*0.8,0.6,0.85 if walk else 0.4)
            dr.polygon([T(q) for q in p],fill=tuple(int(255*v) for v in c),outline=(0,0,0))
    for i,f in enumerate(F):
        if f['is_portal']:
            p=fpts(i);zs=[q[2] for q in p]
            if min(zs)>zmax or max(zs)<zmin: continue
            xs=[q[0] for q in p];ys=[q[1] for q in p]
            if max(xs)-min(xs)<3000 and nrm(i)[2]<0.5:
                dr.line([T((min(xs),min(ys) if (p[0][0]-p[-1][0])*(p[0][1]-p[-1][1])>=0 else max(ys))),T((max(xs),max(ys) if (p[0][0]-p[-1][0])*(p[0][1]-p[-1][1])>=0 else min(ys)))],fill=(255,255,255),width=2)
    g=grid
    for x in range((int(x0)//g)*g,int(x1)+1,g):
        dr.line([T((x,y0)),T((x,y1))],fill=(70,70,70));dr.text((T((x,y0))[0]+2,H-12),str(x),fill=(200,200,200))
    for y in range((int(y0)//g)*g,int(y1)+1,g):
        dr.line([T((x0,y)),T((x1,y))],fill=(70,70,70));dr.text((2,T((x0,y))[1]-11),str(y),fill=(200,200,200))
    for si,s in enumerate(S):
        if not s['floor_faces']: continue
        cx=(s['min'][0]+s['max'][0])/2;cy=(s['min'][1]+s['max'][1])/2
        if x0<cx<x1 and y0<cy<y1 and zmin<=s['min'][2]<=zmax:
            dr.text(T((cx,cy)),f"S{si}",fill=(255,255,255))
    if rebuilt:
        for r in rebuilt:
            pts=[T(q) for q in r['outline']]
            dr.line(pts+[pts[0]],fill=(255,255,0),width=1)
    im.save(out)
if __name__=='__main__':
    a=sys.argv
    x0,y0,x1,y1,upp=map(float,a[1:6]);out=a[6]
    rb=json.load(open(a[7])) if len(a)>7 and a[7]!='-' else None
    zmin=float(a[8]) if len(a)>8 else -99999;zmax=float(a[9]) if len(a)>9 else 99999
    plot(x0,y0,x1,y1,upp,out,rb,zmin,zmax)
