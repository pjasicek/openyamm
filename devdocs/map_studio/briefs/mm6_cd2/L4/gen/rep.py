import json,sys
d=json.load(open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_cd2/compare/report.json'))
t=d['totals']; print({k:t[k] for k in ('score','distance_agreement','texture_agreement','texture_agreement_where_distances_agree','mean_floor_difference','mean_ceiling_difference','points','points_without_floor_in_rebuild','rebuild_points_without_floor_in_original')})
ss=sorted(d['sectors'],key=lambda s:-s['points']*(1-s['score']))
tot=sum(s['points']*(1-s['score']) for s in ss)
caves={1,66,71,72,73,74,142,143}
cs=[s for s in d['sectors'] if s['sector'] in caves]; ns=[s for s in d['sectors'] if s['sector'] not in caves]
for nm,g in (('caves',cs),('castle',ns)):
    p=sum(s['points'] for s in g); print(nm,'points',p,'score %.3f dist %.3f tex %.3f'%(sum(s['points']*s['score'] for s in g)/p,sum(s['points']*s['distance_agreement'] for s in g)/p,sum(s['points']*s['texture_agreement'] for s in g)/p))
n=int(sys.argv[1]) if len(sys.argv)>1 else 25
for s in ss[:n]:
    print('S%-3d pts %4d score %.2f dist %.2f tex %.2f floor %+.0f ceil %+.0f  loss %.1f%%'%(s['sector'],s['points'],s['score'],s['distance_agreement'],s['texture_agreement'],s['mean_floor_difference'],s['mean_ceiling_difference'],100*s['points']*(1-s['score'])/tot))
print('texture pairs:',[(p['original'],p['rebuilt'],p['surface'],p['rays']) for p in d['texture_pairs'][:14]])
