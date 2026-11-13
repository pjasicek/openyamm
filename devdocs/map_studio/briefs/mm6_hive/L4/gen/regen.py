#!/usr/bin/env python3
"""Regenerates the project and lowers the smoothing of bends the build refuses, until validate is quiet about them."""
import subprocess,json,yaml,re,os,sys
B='/home/pjasicek/github/OpenYAMM/';L=B+'devdocs/map_studio/briefs/mm6_hive/L4';O=B+'openyamm-studio/build/oymap'
SM=B+'output/studio_cal/mm6_hive/tools/smooth.json'
for it in range(6):
    r=subprocess.run(['python3',B+'output/studio_cal/mm6_hive/tools/gen.py'],capture_output=True,text=True)
    if r.returncode: print(r.stdout,r.stderr);sys.exit(1)
    notes=r.stdout
    subprocess.run([O,'fmt',L],capture_output=True)
    v=subprocess.run([O,'validate',L,'--assets',B+'assets_dev'],capture_output=True,text=True)
    lines=sorted(set((v.stdout+v.stderr).splitlines()))
    d=yaml.safe_load(open(L+'/rooms.yml'))
    sm=json.load(open(SM)) if os.path.exists(SM) else {}
    changed=False;out=[]
    for l in lines:
        m=re.match(r'rooms.yml: rooms\[(\d+)\]\.(\w+): (.*)',l)
        if m:
            room=d['rooms'][int(m.group(1))]
            if 'crosses itself' in l and room.get('smooth',0)>0:
                sm[room['id']]=room.get('smooth',0)-1;changed=True;continue
            out.append(f"{room['id']} {m.group(2)}: {m.group(3)}  {room.get('path') or ''}")
        else: out.append(l)
    json.dump(sm,open(SM,'w'),indent=0,sort_keys=True)
    if not changed: break
print(notes,end='')
print('\n'.join(out))
