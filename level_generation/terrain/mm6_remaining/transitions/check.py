"""Exhaustive compatible joins plus actual placements; save flat review fixtures."""
import collections,csv,json,sys
import numpy as np
from PIL import Image,ImageDraw
from build import P,R,T,ROOT,D,OLD,OUT,read,sha,edge,seams
sys.path.insert(0,str(ROOT/'util'))
from map_export import parse_odm_file

def ratios(joined,columns):
    energy=np.mean(np.diff(joined,axis=1)**2,axis=2)
    e=energy[:,np.asarray(columns)-1]
    near=np.stack([np.mean(np.concatenate([energy[:,c-5:c-1],energy[:,c:c+4]],1),1) for c in columns],1)
    def windows(a):
        integral=np.concatenate([np.zeros((1,a.shape[1])),np.cumsum(a,0)],0);s=np.arange(0,241,4)
        return (integral[s+16]-integral[s])/16
    return np.sqrt(windows(e))/np.maximum(1,np.sqrt(windows(near)))

def main():
    report=json.loads((P/'reports/build.json').read_text());inv=json.loads((R/'inventory.json').read_text())
    tiles={p.stem:read(p) for p in OUT.glob('*.png')}
    meta={r['tile']:(r['family'],r['edge_topology']) for r in report['tiles']}
    for g in inv['groups']:
        if g['base']:meta[g['base']]=(g['id'],dict.fromkeys('NSEW','11'))
    meta['6dirttyl']=('dirt',dict.fromkeys('NSEW','00'))
    for p in (D/'masks/connected_v4').glob('6drsr*.png'):
        a=np.asarray(Image.open(p),float)/255
        meta[p.stem]=('roads',{s:'opening' if np.mean(edge(a,s)[180:330])>.5 else '0' for s in 'NSEW'})
    opposite={'E':'W','S':'N'}
    def compatible(a,s,b):
        if a not in meta or b not in meta:return None
        ga,ea=meta[a];gb,eb=meta[b];ka=ea[s];kb=eb[opposite[s]]
        if ka in ('0','00') and kb in ('0','00'):return True
        return ga==gb and ka==kb
    pairs=collections.Counter();locations={};grids={}
    table=list(csv.DictReader((ROOT/'assets_dev/engine/data_tables/terrain_tile_data_3.txt').open(),delimiter='\t'))
    for m in inv['maps']:
        path=ROOT/m['source'];assert sha(path)==m['source_sha256']
        data=parse_odm_file(path)['payload'];lookup=data['tile_set_lookup_indices'];names=[]
        for raw in data['tile_map']:
            idx=raw if raw<90 else lookup[(raw-90)//36]+(raw-90)%36
            names.append(table[idx]['texture_name'].lower())
        grid=np.asarray(names).reshape(128,128)[:127,:127];grids[m['id']]=grid.tolist()
        for y in range(127):
            for x in range(127):
                a=grid[y,x]
                for side,ny,nx in [('E',y,x+1),('S',y+1,x)]:
                    if ny>=127 or nx>=127:continue
                    b=grid[ny,nx]
                    if a not in meta and b not in meta:continue
                    pair=(a,side,b);pairs[pair]+=1;locations.setdefault(pair,dict(map=m['id'],row=y,column=x))
    actual=set(pairs)
    # Exhaust every valid combination, not merely the currently occurring examples.
    for a in meta:
        for b in meta:
            for side in ('E','S'):
                if compatible(a,side,b):pairs.setdefault((a,side,b),0)
    checks=[];incompatible=[];worst=[]
    for (a,side,b),count in sorted(pairs.items()):
        valid=compatible(a,side,b)
        if valid is not True:
            if valid is False:incompatible.append(dict(a=a,side=side,b=b,placements=count,example=locations[(a,side,b)]))
            continue
        aa,bb=tiles[a],tiles[b]
        if side=='S':aa=aa.transpose(1,0,2);bb=bb.transpose(1,0,2)
        joined=np.concatenate([aa,bb],1)
        boundary=ratios(joined,[256]).ravel();inside=ratios(joined,[c for c in range(16,497,16) if c!=256]).ravel()
        bp=float(np.percentile(boundary,95));bm=float(boundary.max());ip=float(np.percentile(inside,95));im=float(np.percentile(inside,99.9))
        passed=bp<1.25*ip and bm<1.25*im
        checks.append(dict(a=a,side=side,b=b,actual_placements=count,boundary_p95=bp,boundary_max=bm,interior_p95=ip,interior_p999=im,passed=passed))
        worst.append((bm,f'{a} {side} {b}',int(boundary.argmax())*4,joined))
        worst=sorted(worst,key=lambda v:-v[0])[:32]
    sheet=Image.new('RGB',(1024,160*8),'#202933');draw=ImageDraw.Draw(sheet)
    for i,(score,label,start,joined) in enumerate(sorted(worst,key=lambda v:-v[0])[:32]):
        x=i%4*256;y=i//4*160;start=max(0,min(start-8,224))
        draw.text((x+2,y+2),label,fill='white');draw.text((x+2,y+17),'ratio %.2f'%score,fill='white')
        sheet.paste(Image.fromarray(seams.byte(joined[start:start+32,224:288])).resize((256,128)),(x,y+32))
    sheet.save(P/'reports/worst_joins.png')
    # Closed material island and inverted dirt hole include all twelve variants.
    fixtures={}
    for g in inv['groups'][:5]:
        pre=g['prefix'];base=g['base'];d='6dirttyl'
        island=[[d]*5,[d,pre+'nw',pre+'n',pre+'ne',d],[d,pre+'w',base,pre+'e',d],[d,pre+'sw',pre+'s',pre+'se',d],[d]*5]
        hole=[[base]*5,[base,pre+'xse',pre+'s',pre+'xsw',base],[base,pre+'e',d,pre+'w',base],[base,pre+'xne',pre+'n',pre+'xnw',base],[base]*5]
        fixtures[g['id']]=[island,hole]
        sheet=Image.new('RGB',(1280,664),'#202933');draw=ImageDraw.Draw(sheet)
        for z,grid in enumerate((island,hole)):
            draw.text((z*640+5,4),g['id']+(' island' if z==0 else ' dirt hole'),fill='white')
            for y,row in enumerate(grid):
                for x,n in enumerate(row):sheet.paste(Image.fromarray(seams.byte(tiles[n])).resize((128,128)),(z*640+x*128,24+y*128))
        sheet.save(P/'contexts'/(g['id']+'_flat.png'))
    # Every generated tile also gets its real native 3x3 placement beside the original.
    for g in inv['groups']:
        members=[r for r in inv['tiles'] if r['family']==g['id'] and r['kind']!='base']
        sheet=Image.new('RGB',(768,len(members)*408),'#202933');draw=ImageDraw.Draw(sheet)
        for row,r in enumerate(members):
            draw.text((3,row*408+3),r['name']+'  original / restored; native map placement',fill='white')
            for z in (0,1):
                for y,line in enumerate(r['example']['context']):
                    for x,n in enumerate(line):
                        im=Image.open(ROOT/'assets_dev/worlds/mm6/textures'/(n+'.bmp')).convert('RGB') if z==0 else Image.fromarray(seams.byte(tiles[n]))
                        sheet.paste(im.resize((128,128)),(z*384+x*128,row*408+24+y*128))
        sheet.save(P/'contexts'/(g['id']+'_native.png'))
    (P/'reports/flat_fixtures.json').write_text(json.dumps(fixtures,indent=2)+'\n')
    failures=[r for r in checks if not r['passed']]
    result=dict(compatible_joins=len(checks),actual_unique_pairs=len(actual),checks=checks,failures=failures,native_incompatible_placements=incompatible,old_pack_byte_identical=all(sha(p)==sha(OUT/p.name) for p in OLD.glob('*.png')))
    result['files']={p.name:sha(p) for p in OUT.glob('*.png')}
    (P/'reports/validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(compatible_joins=len(checks),failures=len(failures),native_incompatible=len(incompatible),worst_failures=failures[:8]),indent=2))
if __name__=='__main__':main()
