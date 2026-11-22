import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
# Index: texture (lower case) -> {"world/map.blv": faces} over every shipped MM6-MM8 dungeon, from oymap export.
import json, subprocess, glob, os, collections
R=_REPO_ROOT
out=R+'/output/studio_cal/xd03/tex/blv_texture_use.json'
idx=collections.defaultdict(dict)
for w in ('mm6','mm7','mm8'):
    for f in sorted(glob.glob(f'{R}/assets_dev/worlds/{w}/maps/*.blv')):
        m=os.path.basename(f)
        tmp=R+'/output/studio_cal/xd03/tex/_x.json'
        r=subprocess.run([R+'/openyamm-studio/build/oymap','export',f,'--out',tmp],capture_output=True)
        if r.returncode: continue
        j=json.load(open(tmp))['map']
        c=collections.Counter(fc['texture'].lower() for fc in j['faces'])
        for t,n in c.items(): idx[t][f'{w}/{m}']=n
json.dump(idx,open(out,'w'),indent=0,sort_keys=True)
print(len(idx))
