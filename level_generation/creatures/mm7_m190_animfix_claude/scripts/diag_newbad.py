import sys; sys.path.insert(0,'level_generation/creatures/claude_shared')
import motion_audit, numpy as np
clip=sys.argv[3]; t=float(sys.argv[4])
A=motion_audit.Audit(sys.argv[1]); B=motion_audit.Audit(sys.argv[2])
lab=np.load('level_generation/creatures/mm7_m190_animfix_claude/work/labels.npz')
def bad(a):
    posed,scale,pal,w=a.pose(clip,t); s1,s2,fold,live=a.deformation(posed,scale,pal)
    return live&((s1>1.6)|(s2<0.55)|fold), s1, s2, fold
ba,s1a,s2a,fa=bad(A); bb,s1b,s2b,fb=bad(B)
area=A.rest_area; c=A.rest[A.tris].mean(1)
tb=lab['b'][A.tris].mean(1); tc=lab['cls'][A.tris].max(1)
print('total bad area cm2 before %.0f after %.0f'%(area[ba].sum()*1e4, area[bb].sum()*1e4))
new=bb&~ba; gone=ba&~bb
for nm,s in [('new',new),('gone',gone)]:
    print(nm,'area %.0f'%(area[s].sum()*1e4))
    for yb in [(0,0.64),(0.64,0.74),(0.74,0.84),(0.84,0.94),(0.94,1.04),(1.04,1.5)]:
        for fz,zs in [('front',c[:,2]>0.03),('back',c[:,2]<=0.03)]:
            q=s&(c[:,1]>=yb[0])&(c[:,1]<yb[1])&zs
            if area[q].sum()*1e4>3: print('  y',yb,fz,'%.0f cm2'%(area[q].sum()*1e4),'stretch %d squash %d fold %d'%((s1b[q]>1.6).sum() if nm=='new' else (s1a[q]>1.6).sum(), (s2b[q]<0.55).sum() if nm=='new' else (s2a[q]<0.55).sum(), fb[q].sum() if nm=='new' else fa[q].sum()), 'x', np.round(np.percentile(c[q,0],[10,50,90]),2), 'beardness %.2f'%tb[q].mean(), 'cls', np.bincount(tc[q],minlength=4))
