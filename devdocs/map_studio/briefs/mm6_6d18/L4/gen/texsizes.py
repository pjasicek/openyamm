import subprocess,json,sys
names="vlcwl1 vlcwl1LG vlcwl2 vlcwl3a vlcwl1A vlcwl4B vlcflorA vlcflorE vlcflorC vlcflorB vlctrm3 vlcceilA D2Ceil1 D2Ceil3 D8florH vlcGnrc1 vlcgnrc2 vlcgnrc3 ctwl2 ctwl5 ctFlor1 ctFlor4 ctFlor5 ctCeil1 ctCeil2 ctCeil3 OrFyrLgA D2WlActr BemVwal CVDOR1 sky_nit2 6voltyl OrFyr64B Bookcas2 D2LgDor vlcdorC ch3frntB ch3side ch1frntB ch2FRNTb BemH16a D8wlBLE D8wlB d8wlbxL CTTRIM2 ctwl4LE gset05 vlcwl3u vlcwl1LE".split()
out={}
for n in names:
    r=subprocess.run(['openyamm-studio/build/oymap','assets',n,'--assets','assets_dev','--world','mm6','--kind','texture','--limit','40','--json'],capture_output=True,text=True)
    try:
        j=json.loads(r.stdout)
    except Exception as e:
        print('fail',n,r.stdout[:200],r.stderr[:200]); continue
    items=j.get('textures',[])
    for it in items:
        if it.get('name','').lower()==n.lower(): out[n.lower()]=it
    if n.lower() not in out: print('missing',n,[i.get('name') for i in items][:5])
json.dump(out,open('output/studio_cal/mm6_6d18/texsizes.json','w'),indent=0)
for k,v in out.items(): print(k,{a:b for a,b in v.items() if a!='name'})
