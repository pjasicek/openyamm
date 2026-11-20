import sys;sys.path.insert(0,'/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/tools')
from geom import *
si=int(sys.argv[1]);kinds=sys.argv[2].split(',');minarea=float(sys.argv[3]) if len(sys.argv)>3 else 0
for k in kinds:
    for i in S[si][k+'_faces']:
        p=fpts(i);a=abs(area2(p))
        zs=[q[2] for q in p]
        if a<minarea and k!='wall' : continue
        n=[round(x,2) for x in nrm(i)]
        print(k,i,F[i]['texture'].lower(),n,f"A={a/1e3:.0f}k z={min(zs)}..{max(zs)}",[q[:2] if min(zs)==max(zs) else q for q in p][:14], 'ev=%d'%F[i]['cog_triggered'] if F[i]['cog_triggered'] else '', 'P->%d'%(F[i]['room_behind'] if F[i]['room']==si else F[i]['room']) if F[i]['is_portal'] else '')
