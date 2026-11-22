import yaml, re, sys, os
root='assets_dev/worlds/xeen'
mon=yaml.safe_load(open(f'{root}/source/monsters.yml'))
act=yaml.safe_load(open(f'{root}/models/actors.yml'))
b={}
for e in act['actors']:
    if isinstance(e,dict) and 'descriptor' in e: b[e['descriptor']]=e
words=r'water|acid|fire|frost|ice|energy|earth|air|storm|poison|shadow|dark|light|gold|silver|iron|bronze|crystal|diamond|onyx|lava|swamp|ghost|blood|green|red|blue|white|black|grey|gray|cloud|phase|sky|sand|stone|snow|mud|bog|copper|steel|ruby|jade|emerald|obsidian|ash|cinder|flame|thunder|lightning|electr|spirit|bone|plague|toxic|venom|rust|sun|moon|night|star|death|doom|lich|yellow|purple|violet|magma|ember|dust|mist|fog|glass|marble|clay|wood|cave|grave|deep|sea|ocean|crimson|pale|wraith|spectr|phantom|shade'
fams=mon.get('families') or {k:v for k,v in mon.items() if isinstance(v,dict) and 'tiers' in v}
out=[]
for key,f in fams.items():
    if not isinstance(f,dict) or 'tiers' not in f: continue
    pic=f.get('picture')
    for L,t in f['tiers'].items():
        d=f'{pic} {L}'
        e=b.get(d,{})
        out.append((key,L,t.get('name'),t.get('id', f.get('block',0)+'ABCDEFGHIJ'.index(L) if L in 'ABCDEFGHIJ' else 0),d,os.path.basename(e.get('model','-')),e.get('skin','-')))
    for bo in f.get('bosses',[]) or []:
        d=bo.get('picture') or f"Xeen {bo['name']}"
        e=b.get(d,{})
        out.append((key,'boss',bo['name'],bo.get('id'),d,os.path.basename(e.get('model','-')),e.get('skin','-')))
flag='-a' in sys.argv
for r in out:
    m=re.search(words,str(r[2]),re.I)
    if flag or m: print('\t'.join(map(str,r)))
