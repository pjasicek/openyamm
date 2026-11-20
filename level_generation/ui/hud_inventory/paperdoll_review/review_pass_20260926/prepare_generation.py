"""Small, explicit repair sheets; all output remains pending user re-review."""
import json
import math
from pathlib import Path
from urllib.parse import unquote
from PIL import Image
from inspect_sources import HERE,OUT,read


def main():
    data=json.loads((OUT/'catalog.original.js').read_text().removeprefix('window.PAPERDOLL_REVIEW_DATA = ').removesuffix(';\n'))
    assets={a['id']:a for a in data['assets'].values()};queue=read(OUT/'repair_queue.json')
    groups={'small_quality':[], 'large_quality':[], 'identity':[]};duplicates={};seen={}
    for target,rec in queue.items():
        a=assets[target]
        if 'quality' not in rec['categories'] and 'identity' not in rec['categories']:continue
        if a['sourceHash'] in seen:
            duplicates[target]=seen[a['sourceHash']];continue
        seen[a['sourceHash']]=target
        group='identity' if 'identity' in rec['categories'] else 'small_quality' if a['size'][1]<75 else 'large_quality'
        groups[group].append(target)
    batches=[]
    for group,targets in groups.items():
        count=16 if group=='small_quality' else 4 if group=='large_quality' else 6
        for start in range(0,len(targets),count):
            selected=targets[start:start+count];cols=4 if group=='small_quality' else 2 if group=='large_quality' else 3
            rows=math.ceil(len(selected)/cols);factor=4 if group=='small_quality' else 2
            width=max(assets[t]['size'][0] for t in selected)*factor+32
            height=max(assets[t]['size'][1] for t in selected)*factor+32
            reference=Image.new('RGBA',(width*cols,height*rows));current=reference.copy();cells=[]
            for i,target in enumerate(selected):
                a=assets[target];native=Image.open(HERE/unquote(a['native'])).convert('RGBA')
                candidate=Image.open(HERE/unquote(a['candidate'])).convert('RGBA')
                native=native.resize((native.width*factor,native.height*factor),Image.Resampling.NEAREST)
                candidate=candidate.resize(native.size,Image.Resampling.LANCZOS)
                x=i%cols*width+(width-native.width)//2;y=i//cols*height+(height-native.height)//2
                reference.alpha_composite(native,(x,y));current.alpha_composite(candidate,(x,y))
                cells.append({'target':target,'name':a['name'],'rect':[x,y,*native.size],
                              'slot':[i%cols*width,i//cols*height,width,height],'note':queue[target]['note']})
            name=f'{group}_{start//count+1:02}'
            folder=OUT/'generated'/name;folder.mkdir(parents=True,exist_ok=True)
            reference.save(folder/'native.png');current.save(folder/'current.png')
            manifest={'name':name,'group':group,'grid':[cols,rows],'size':list(reference.size),'cells':cells,
                      'factor':factor,'reference':'native.png','current':'current.png'}
            (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');batches.append(manifest)
    (OUT/'generated/batches.json').write_text(json.dumps({'batches':batches,'exact_native_duplicates':duplicates},indent=2)+'\n')
    print([(b['name'],len(b['cells']),b['size']) for b in batches])

if __name__=='__main__':main()
