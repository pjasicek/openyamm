import csv
rows=list(csv.DictReader(open('golden_mapping_trunc.csv')))
cf=['easy_normal','unreachable70','maw','hard','hell','nightmare','doom','insanity','madness']
idx={(r['config'],r['party_count'],r['level']):r for r in rows}
levels=[r['level'] for r in rows if r['config']=='maw' and r['party_count']=='5']
def fmt(v):
    v=float(v)
    if v<100: return f'{v:.1f}'
    return f'{v:.0f}'
blocks=[]
titles={'power':'Expected player power (damage per swing-equivalent), getPlayerEstimatedPower',
 'vitality':'Expected player vitality (effective HP), getPlayerEstimatedVitality',
 'attack':'Expected player attack rating, getPlayerEstimatedAttack',
 'monster_hp_b':'Monster HP, B tier, no boss (getMonsterHealth(nil, L))',
 'monster_dmg_b':'Monster damage per hit before mitigation, B tier, no boss (getMonsterDamage(nil, L))'}
for col in ('power','vitality','attack','monster_hp_b','monster_dmg_b'):
    out=[f'#### {titles[col]}','','```']
    hdr=['level']+[f'd{i}' for i in range(1,10)]
    w=[5]+[9]*9
    out.append(','.join(h.rjust(x) for h,x in zip(hdr,w)))
    for L in levels:
        vals=[L]+[fmt(idx[(c,'5',L)][col]) for c in cf]
        out.append(','.join(v.rjust(x) for v,x in zip(vals,w)))
    out.append('```')
    blocks.append('\n'.join(out))
open('golden_md.txt','w').write('\n\n'.join(blocks)+'\n')
# compact per-level MAW detail table
out=['```']
cols=['level','skill','mastery','stat','geared','max_enchant','health','armor_class','resistance','phys_taken','magic_taken','chance_hit','vitality','power','attack']
w=[5,6,3,7,6,6,8,7,7,6,6,6,9,9,6]
short=['level','skill','m','stat','gear','maxEn','health','AC','res','phys','magic','hit','vitality','power','attack']
out.append(','.join(h.rjust(x) for h,x in zip(short,w)))
for L in [l for l in levels if int(l) in (1,2,5,10,15,20,30,40,50,60,70,80,90,100,150,200,250,300,400,500,600,800,1000,1500,2000)]:
    r=idx[('maw','5',L)]
    vals=[L]+[f"{float(r[c]):.3g}" if float(r[c])<10 and c not in ('mastery',) else (r[c] if c=='mastery' else fmt(r[c])) for c in cols[1:]]
    out.append(','.join(str(v).rjust(x) for v,x in zip(vals,w)))
out.append('```')
open('golden_detail.txt','w').write('\n'.join(out)+'\n')
print(max(len(l) for l in open('golden_md.txt').read().split('\n')), max(len(l) for l in open('golden_detail.txt').read().split('\n')))
