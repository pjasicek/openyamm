import sys,subprocess,json;sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tools')
from geom import *
def area3(p):
    ax=ay=az=0
    for i in range(1,len(p)-1):
        u=[p[i][k]-p[0][k] for k in range(3)];v=[p[i+1][k]-p[0][k] for k in range(3)]
        ax+=u[1]*v[2]-u[2]*v[1];ay+=u[2]*v[0]-u[0]*v[2];az+=u[0]*v[1]-u[1]*v[0]
    return math.sqrt(ax*ax+ay*ay+az*az)/2
def dom(si):
    w=collections.Counter();f=collections.Counter();c=collections.Counter()
    for i in S[si]['faces']:
        fc=F[i]
        if fc['is_portal']: continue
        t=fc['texture'].lower();a=area3(fpts(i));nz=nrm(i)[2]
        if nz>0.7: f[t]+=a
        elif nz<-0.35: c[t]+=a
        elif abs(nz)<0.3: w[t]+=a
    g=lambda cn: cn.most_common(1)[0][0] if cn else None
    return g(w),g(f),g(c)
if __name__=='__main__':
    names=set();out={}
    for si in range(len(S)):
        if S[si]['faces']:
            d=dom(si);out[si]=d;names|=set(x for x in d if x)
            print(si,d)
    sizes={}
    for n in sorted(names):
        r=subprocess.run(['openyamm-studio/build/oymap','assets',n,'--assets','assets_dev','--world','mm6','--kind','texture','--limit','50'],capture_output=True,text=True)
        for t in json.loads(r.stdout)['textures']:
            if t['name']==n: sizes[n]=t['size']
    json.dump({'dom':out,'sizes':sizes},open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tex.json','w'))
    print(sizes)
