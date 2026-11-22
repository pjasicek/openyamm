import pathlib  # noqa: E402
_REPO_ROOT = str(pathlib.Path(__file__).resolve().parents[6])  # the repository root
import json,re,sys
R=_REPO_ROOT + '/'
use=json.load(open(R+'output/studio_lead/blv_texture_use.json'))
names=json.load(open(R+'output/studio_lead/blv_names.json'))
txt=open(R+'devdocs/xeen/briefs/xd03/L4/rooms.yml').read()+open(R+'devdocs/xeen/briefs/xd03/L4/objects.yml').read()
tex=sorted(set(t.lower() for t in re.findall(r"texture: ([A-Za-z0-9_\-]+)",txt)))
for t in tex:
    u=use.get(t,{})
    top=sorted(u.items(),key=lambda kv:-kv[1])[:5]
    print(f"{t:11s} {len(u):3d}:", "; ".join(f"{m} {names.get(m,'?')[:20]} {n}" for m,n in top))
