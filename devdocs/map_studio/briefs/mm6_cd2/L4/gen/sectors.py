from lib import *
out=[]
for si in range(len(S)):
    i=sector_info(si)
    if not S[si]['faces'] and not S[si]['floor_faces']: continue
    fl=sorted(i['floors'].items(),key=lambda t:-t[1])[:4]
    ce=sorted(i['ceils'].items(),key=lambda t:-t[1])[:3]
    tx={}
    for k,v in i['tex'].items(): tx.setdefault(k[0],[]).append((v,k[2:]))
    ts=' '.join(k+'='+','.join(n for v,n in sorted(tx[k],reverse=True)[:3]) for k in sorted(tx))
    foot=i['foot']
    npts=0;fa=0
    if foot is not None:
        fa=foot.area
        g=foot.geoms if hasattr(foot,'geoms') else [foot]
        npts=sum(len(p.exterior.coords)-1 for p in g)
        nparts=len(list(g));holes=sum(len(p.interiors) for p in g)
    else: nparts=holes=0
    print(f"S{si} x[{i['min'][0]},{i['max'][0]}] y[{i['min'][1]},{i['max'][1]}] z[{i['min'][2]},{i['max'][2]}] area={fa/1e6:.2f}M pts={npts} parts={nparts} holes={holes} slope={i['sloped']/1e6:.2f}M")
    print('   floors',' '.join(f'{z}:{a/1e3:.0f}k' for z,a in fl),'| ceils',' '.join(f'{z}:{a/1e3:.0f}k' for z,a in ce),'|',ts)
    print('   portals',' '.join(f"->{p['to']}(w{max(p['max'][0]-p['min'][0],p['max'][1]-p['min'][1])} h{p['max'][2]-p['min'][2]} z{p['min'][2]} @{(p['min'][0]+p['max'][0])//2},{(p['min'][1]+p['max'][1])//2})" for p in i['portals']))
