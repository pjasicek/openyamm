import json,sys
r=json.load(open(sys.argv[1]+'/report.json'))
t=r['totals']; print({k:t[k] for k in ('score','distance_agreement','texture_agreement','mean_floor_difference','mean_ceiling_difference','points_without_floor_in_rebuild','rebuild_points_without_floor_in_original')})
print('sectors by score:')
for s in sorted(r['sectors'],key=lambda s:s['score'])[:int(sys.argv[2]) if len(sys.argv)>2 else 25]:
    print('  S%d pts%d score %.2f dist %.2f tex %.2f err %d dfl %.0f dceil %.0f'%(s['sector'],s['points'],s['score'],s['distance_agreement'],s['texture_agreement'],s['mean_distance_error'],s['mean_floor_difference'],s['mean_ceiling_difference']))
print('texture pairs:')
for p in r['texture_pairs'][:30]: print('  ',p['original'],'->',p['rebuilt'],p['surface'],p['rays'])
print('worst:')
for w in r['worst_points'][:int(sys.argv[3]) if len(sys.argv)>3 else 12]:
    print('  ',w['at'],'S%d'%w['sector'],w['score'],w['differs'][:230])
print('missing floor', r['floor_missing_in_rebuild']); print('only rebuild', r['floor_only_in_rebuild'])
