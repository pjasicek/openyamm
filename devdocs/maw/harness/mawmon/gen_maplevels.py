import json
OUT='/home/pjasicek/github/OpenYAMM/devdocs/maw/data/map_levels.yml'
r=json.load(open('resolve.json'))
maw=[]
for ln in open('zmawT/mapstats.txt',encoding='latin1').read().replace('\r','').split('\n'):
    c=ln.split('\t')
    if c and c[0].strip().isdigit(): maw.append((int(c[0]),c[1],c[2].strip()))
oyfiles={}
for ln in open('/home/pjasicek/github/OpenYAMM/assets_dev/engine/data_tables/map_stats.txt',encoding='latin1').read().split('\n'):
    c=ln.split('\t')
    if c and c[0].strip().isdigit() and int(c[0])<1000: oyfiles[c[2].strip().lower()]=(int(c[0]),c[1])
byname={}
for i,n,f in maw: byname.setdefault(n,[]).append((i,f))
P=[];M={};S=[];H=[]
for ln in open('lua/maps.tsv'):
    p=ln.rstrip('\n').split('\t')
    if p[0]=='P': P.append((p[1],p[2],int(p[3])))
    if p[0]=='M': M[p[1]]=float(p[2])
    if p[0]=='S': S.append(p[1])
    if p[0]=='H': H.append(p[1])
def q(s):
    return '"' + s.replace('\\','\\\\').replace('"','\\"') + '"'
def n(x):
    return str(int(x)) if float(x).is_integer() else repr(float(x))
L=[]
L.append('# draft extracted from MAW ef23ee17')
L.append('# Per-map monster level bands (mapLevels), horizontal starter maps and Beyond Madness level progression.')
L.append('# Source: Maw-Mod-MMMerge Scripts/General/zzMaw-Monsters.lua')
L.append('#   horizontalMaps 946-955, madnessStartingMaps 957-961, mapLevels 963-1592,')
L.append('#   mm6/mm7/mm8MapProgression 1594-1785, madnessLevel 1787-1792, madnessMapLevels 1794-1811.')
L.append('# MAW keys these tables by map DISPLAY name (Game.MapStats[i].Name, from MAW\'s own mapstats.txt in')
L.append('# Data/zMaw.T.lod). This draft re-keys them by map FILE name. Where several maps share a display name they')
L.append('# share one MAW entry; such maps are listed individually here with `shared_key`. Values are the EFFECTIVE')
L.append('# ones (a Lua table constructor keeps the last duplicate key); `maw_intended` records an overwritten entry.')
L.append('# low/mid/high: the B-tier level the 1st/2nd/3rd native monster family (sorted by base B level) is pinned to.')
L.append('# See devdocs/maw/BALANCE_MODEL.md section 7 for how these feed monster levels in each progression mode.')
L.append('format: 1')
L.append('source: {repo: Maw-Mod-MMMerge, commit: ef23ee17, file: Scripts/General/zzMaw-Monsters.lua}')
L.append('')
L.append('map_levels:')
seen=set()
for i,name,f in maw:
    e=r.get(name)
    if not e: 
        L.append(f'  # {f}: no mapLevels entry for {q(name)} (would raise a Lua error in recalculateMonsterTable)')
        continue
    lo,mi,hi=e['eff']
    occ=e['occ']
    files=byname[name]
    extra=[]
    if len(files)>1: extra.append(f'shared_key: {q(name)}')
    last=occ[-1]
    extra.append(f'line: {last[0]}')
    if f.lower() not in oyfiles: extra.append('openyamm: missing')
    elif oyfiles[f.lower()][1]!=name: extra.append(f'openyamm_name: {q(oyfiles[f.lower()][1])}')
    L.append(f'  {f}: {{name: {q(name.rstrip())}, mapstats_id: {i}, low: {n(lo)}, mid: {n(mi)}, high: {n(hi)}, ' + ', '.join(extra) + '}')
    intended={'d22.blv':1064,'zdtl02.blv':1568}
    if f in intended:
        o=[x for x in occ if x[0]==intended[f]][0][2]
        L[-1]=L[-1][:-1]+f', maw_intended: {{low: {n(o["Low"])}, mid: {n(o["Mid"])}, high: {n(o["High"])}, line: {intended[f]}}}}}'
L.append('')
L.append('# Display names in the MAW table that OpenYAMM\'s map_stats.txt cannot resolve:')
L.append('#   "The Breach" -> Breach.odm (204), BrAlvar.odm (205); "Basement of the Breach" -> BrBase.blv (206):')
L.append('#     these three maps do not exist in OpenYAMM (map_stats.txt has no rows 204-206).')
L.append('#   "The Abandoned Temple" -> 6d02.blv (153): MAW renames row 153 in its mapstats.txt; OpenYAMM still names')
L.append('#     both d05.blv and 6d02.blv "Abandoned Temple", so a lookup by display name would give 6d02 the d05 band.')
L.append('')
L.append('# Horizontal progression starter maps: monsters stay near their vanilla level (zzMaw-Monsters.lua:946-955).')
L.append('horizontal_starter_maps:')
for h in sorted(H):
    for i,f in byname[h]: L.append(f'  - {f}  # {h}')
L.append('')
L.append('madness:')
L.append('  # Beyond Madness fixes every listed map at a level along its game\'s campaign (zzMaw-Monsters.lua:1784-1811).')
L.append('  top_level: 500        # MADNESS_TOP_LEVEL')
L.append('  curve: 1.2            # MADNESS_CURVE')
L.append('  level_formula: "round(top_level * (position / campaign_length) ^ curve)"   # round() = half up')
L.append('  campaign_length: {mm6: 54, mm7: 52, mm8: 58}')
L.append('  # Maps where the fixed madness level is NOT applied: monsters follow the horizontal starter-map rule')
L.append('  # and unique monsters get 3x their base level (zzMaw-Monsters.lua:289-303, 431-433).')
L.append('  starting_maps:')
for s in sorted(S):
    for i,f in byname[s]: L.append(f'    - {f}  # {s}')
L.append('  # Explicit overrides assigned after the formula (lines 1806-1811).')
L.append('  fixed_levels:')
for nm,lv in (('Basement of the Breach',1100),('The Breach',1100),('The Arena',1),('NWC',1)):
    for i,f in byname[nm]: L.append(f'    {f}: {lv}   # {nm}')
L.append('    # "Pending" (capital P) = 1 is also set; no map has that name (the placeholder maps are "pending").')
L.append('  # position along the campaign -> fixed level. A name in two tables takes the later loop (mm8 after mm6).')
L.append('  progression:')
for w in ('mm6','mm7','mm8'):
    L.append(f'    {w}:')
    rows=sorted([(pos,nm) for ww,nm,pos in P if ww==w])
    for pos,nm in rows:
        lvl=M.get(nm)
        for i,f in byname[nm]:
            note=''
            if nm=='Temple of the Sun': note='; mm8 entry (24 of 58) wins'
            L.append(f'      {f}: {{position: {pos}, level: {n(lvl)}}}   # {nm.rstrip()}{note}')
open(OUT,'w').write('\n'.join(L)+'\n')
print(len(L))
