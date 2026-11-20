"""Find native indexed-pixel identity candidates in completed other-world restorations."""
from pathlib import Path
import collections,hashlib,json
from PIL import Image
ROOT=Path(__file__).resolve().parents[1];REPO=ROOT.parents[1]
def digest(record):
    im=Image.open(REPO/record['path'])
    if im.mode=='P':
        alpha=im.point(lambda x:255 if x else 0).convert('L');box=alpha.getbbox()
        if box:im=im.crop(box)
    return hashlib.sha256(str((im.mode,im.size)).encode()+im.tobytes()).hexdigest()
def run():
    lookup=collections.defaultdict(list);scanned=0
    for p in ROOT.glob('*/manifest.json'):
        if p.parent.name.startswith('mm8_'):continue
        sp=p.parent/'sources.json'
        if not sp.exists():continue
        d=json.loads(sp.read_text())
        for name,src in d.get('sources',{}).items():
            if not isinstance(src,dict) or 'path' not in src:continue
            lookup[digest(src)].append([p.parent.name,name]);scanned+=1
    results={}
    for p in ROOT.glob('mm8_*/sources.json'):
        if (p.parent/'manifest.json').exists():continue
        d=json.loads(p.read_text());matches={}
        for name,src in d['sources'].items():
            h=digest(src)
            if h in lookup:matches[name]=lookup[h]
        if matches:results[p.parent.name]={'matches':len(matches),'total':len(d['sources']),'frames':matches}
    report={'method':'Exact native BMP indexed pixels after visible-bound crop; canvas origins require explicit remapping; palette compatibility and accepted art coverage need separate review.','completed_source_frames_scanned':scanned,'families':results}
    (ROOT/'mm8_remaining/cross_world_reuse_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print({k:{x:v[x] for x in ['matches','total']} for k,v in results.items()})
if __name__=='__main__':run()
