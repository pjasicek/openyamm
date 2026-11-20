import json,sys
r=json.load(open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/compare/report.json'))
t=r['totals'];print('TOTAL score %.3f dist %.3f tex %.3f missing_floor %d only_rebuild %d ceil_diff %s floor_diff %s'%(t['score'],t['distance_agreement'],t['texture_agreement'],t['points_without_floor_in_rebuild'],t['rebuild_points_without_floor_in_original'],t['mean_ceiling_difference'],t['mean_floor_difference']))
ss=sorted(r['sectors'],key=lambda s:(1-s['score'])*s['points'],reverse=True)
print('worst sectors by (1-score)*points:')
for s in ss[:int(sys.argv[1]) if len(sys.argv)>1 else 25]:
    print(' S%d pts %d nofloor %d score %.2f dist %.2f tex %.2f dfloor %s dceil %s'%(s['sector'],s['points'],s['without_floor'],s['score'],s['distance_agreement'],s['texture_agreement'],s['mean_floor_difference'],s['mean_ceiling_difference']))
print('texture pairs:',[(p['original'],p['rebuilt'],p['surface'],p['rays']) for p in r['texture_pairs'][:24]])
import collections
print('missing floor by sector',collections.Counter(p['sector'] for p in r['floor_missing_in_rebuild']).most_common())
