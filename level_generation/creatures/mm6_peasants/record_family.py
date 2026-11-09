"""Save selected built-in output and exact prompt/input hashes immediately."""
import argparse, json, hashlib, shutil
from PIL import Image
from prepare_family import load

def record(family,batch,path):
    root,config,inv=load(family)
    assert batch in json.loads((root/'batches.json').read_text())
    out=root/f'raw/{batch}.png';assert not out.exists(),'Version existing checkpoint explicitly before replacement'
    shutil.copy2(path,out);(root/'prompts/submitted').mkdir(exist_ok=True)
    submitted=root/f'prompts/submitted/{batch}.txt';shutil.copy2(root/f'prompts/{batch}.txt',submitted)
    def asset(p):return {'path':str(p.relative_to(root)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    refs=[root/f'references/{batch}.png']
    if batch!='standing':refs.append(root/'raw/standing.png')
    file=root/'generation.json';data=json.loads(file.read_text()) if file.exists() else {'tool':'image_gen.imagegen (built-in)','batches':{}}
    data['batches'][batch]={'raw':asset(out),'dimensions':Image.open(out).size,'prompt':asset(submitted),
                           'references':[asset(p) for p in refs],'original_output':path}
    file.write_text(json.dumps(data,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('family');p.add_argument('batch');p.add_argument('path');a=p.parse_args();record(a.family,a.batch,a.path)
