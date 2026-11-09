"""Screen all stepping stones and native Alvar placements, preserving intentional gaps."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import json
from collections import Counter
from scipy.ndimage import label, binary_fill_holes
from PIL import ImageDraw
from common import *
from check_land import checks

F = Path(__file__).resolve().parent
# Counts reviewed against each native reference, not inferred from generated masks.
EXPECTED = dict(plrdew=11, plrdn_e=11, plrdn_w=11, plrdncap=8, plrdne1=11,
                plrdne2=9, plrdns=11, plrdnw1=8, plrdnw2=11, plrds_e=10,
                plrds_w=12, plrdwcap=9)


def main():
    build = json.loads((F/'build.json').read_text())
    assert {r['name'] for r in build['tiles']} == set(EXPECTED)
    tiles, files, components = {}, {}, []
    for r in build['tiles']:
        n = r['name']; path = F/'runtime'/(n+'.png')
        assert sha(path) == r['runtime_sha256']
        assert Image.open(path).size == (256,256)
        mask = read(F/'masks'/(n+'.png')).mean(2)>127
        count = label(mask)[1]
        holes = int(np.count_nonzero(binary_fill_holes(mask)&~mask))
        assert count == EXPECTED[n] and holes == 0, n
        # Every physical face lies within the tile. Soil is the shared border
        # material; faint antialiasing may approach it. No disconnected gap fill.
        assert not any(e.any() for e in (mask[0],mask[-1],mask[:,0],mask[:,-1])), n
        components.append(dict(name=n,components=count,holes=holes))
        tiles[n], files[n] = read(path), path
    tiles['plntyl'] = read(M/'runtime/plains.png')
    files['plntyl'] = M/'runtime/plains.png'
    results = []
    for a in sorted(tiles):
        for b in sorted(tiles):
            for side in ('E','S'):
                m,_,_ = checks.metrics(tiles[a],tiles[b],side)
                results.append(dict(a=a,b=b,side=side,**m))
    grids = json.loads((P/'effective_grids.json').read_text())
    pairs, locations = Counter(), {}
    for map_name,g in grids.items():
        for y,row in enumerate(g):
            for x,a in enumerate(row):
                for dx,dy,side in ((1,0,'E'),(0,1,'S')):
                    if y+dy>=len(g) or x+dx>=len(g[y+dy]): continue
                    b = g[y+dy][x+dx]
                    if a not in EXPECTED and b not in EXPECTED: continue
                    key = (a,side,b);pairs[key]+=1
                    locations.setdefault(key,dict(map=map_name,x=x,y=y))
    native_results=[]
    for (a,side,b),count in sorted(pairs.items()):
        for n in (a,b):
            if n not in tiles:
                path=OUT/(n+'.png')
                assert path.is_file(),n
                tiles[n],files[n]=read(path),path
        m,_,_=checks.metrics(tiles[a],tiles[b],side)
        old,_,_=checks.metrics(read(P/'references'/(a+'.png'),256),read(P/'references'/(b+'.png'),256),side)
        native_results.append(dict(a=a,b=b,side=side,placements=count,example=locations[(a,side,b)],
                                   original_metrics=old,**m))
    # Contact sheets retain native orientation; no transformed art is used at runtime.
    for group in range(4):
        names=sorted(EXPECTED)[group*3:group*3+3]
        sheet=Image.new('RGB',(1536,540),'#202933');draw=ImageDraw.Draw(sheet)
        for i,n in enumerate(names):
            draw.text((i*512+4,4),n+' 2x2 repeat',fill='white')
            im=Image.open(files[n])
            for y in range(2):
                for x in range(2):sheet.paste(im,(i*512+x*256,24+y*256))
        sheet.save(F/('repeats_%d.png'%(group+1)))
    failures=[r for r in results if not r['passed']]
    native_failures=[r for r in native_results if not r['passed']]
    report=dict(scope='12 stepping tiles, shared earth borders, and every native pair touching these tiles',
                compatible_checks=len(results),failures=failures,checks=results,components=components,
                native_unique_pairs=len(native_results),native_placements=sum(pairs.values()),
                native_failures=native_failures,native_checks=native_results,
                files={str(path.relative_to(P)):sha(path) for path in files.values()},
                build_sha256=sha(F/'build.json'),grids_sha256=sha(P/'effective_grids.json'),
                script_sha256=sha(Path(__file__)),metric_source_sha256=sha(T/'mm7/check.py'))
    (F/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('Compatible:',len(results),'checks,',len(failures),'failures; native:',len(native_results),
          'pairs,',sum(pairs.values()),'placements,',len(native_failures),'failures')
    print([(r['a'],r['side'],r['b']) for r in native_failures])


if __name__=='__main__':main()
