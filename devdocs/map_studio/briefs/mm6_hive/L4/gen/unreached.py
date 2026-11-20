import json,yaml
a=json.load(open('/home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_hive/solve.json'))
ids=yaml.safe_load(open('/home/pjasicek/github/OpenYAMM/devdocs/map_studio/briefs/mm6_hive/L4/ids.lock.yml'))['sectors']
inv={v:k for k,v in ids.items()}
def walk(o,path=''):
    if isinstance(o,dict):
        for k,v in o.items(): walk(v,path+'/'+k)
    elif isinstance(o,list):
        if o and all(isinstance(x,int) for x in o) and ('never' in path or 'unreach' in path): print(path,[inv.get(x,x) for x in o])
        else:
            for v in o: walk(v,path)
walk(a)
for st in a.get('steps',[]):
    print('step',st.get('step'),len(st.get('sectors',[])),st.get('needs'),[e.get('text',e) if isinstance(e,dict) else e for e in st.get('events',[])][:6])
