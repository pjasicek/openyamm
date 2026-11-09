import sys, glob, os, statistics as st
sys.path.insert(0,'tools/mm9_import_discovery')
import inventory_mm9_rework as inv
by_number, by_picture = inv.load_engine_monsters()
ms = inv.load_map_stats()
for world in ('mm6','mm7','mm8'):
    tot_n=tot_xp=0; rows=[]
    for p in sorted(glob.glob(f'assets_dev/worlds/{world}/maps/*.scene.yml')):
        stem=os.path.basename(p).replace('.scene.yml','')
        fn = stem+('.odm' if os.path.exists(p.replace('.scene.yml','.odm')) else '.blv')
        r=inv.baseline_report(world, fn, ms, by_number, by_picture)
        if not r: continue
        n=sum(r.spawned.values())+sum(r.placed.values()); xp=r.spawned_experience+r.placed_experience
        tot_n+=n; tot_xp+=xp
        rows.append((stem,r.name,int(n),int(xp),(min(r.levels),int(st.median(r.levels)),max(r.levels)) if r.levels else None))
    print(world,'maps',len(rows),'monsters',int(tot_n),'XP',int(tot_xp))
    if world=='mm7':
        for x in rows: print('  ',x)
