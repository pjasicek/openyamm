import json,sys
s=json.load(open(sys.argv[1]))
defs=s.get('$defs',{}) or s.get('definitions',{})
seen=set()
def typ(n):
    t=n.get('type')
    if 'enum' in n: return 'enum'+json.dumps(n['enum'])
    if '$ref' in n: return 'ref:'+n['$ref'].split('/')[-1]
    if 'oneOf' in n or 'anyOf' in n:
        return '|'.join(typ(x) for x in n.get('oneOf',n.get('anyOf')))
    return str(t)
def walk(n,path,depth=0):
    if depth>12: return
    d=n.get('description','')
    print(f"{path}: {typ(n)}" + (f" -- {d}" if d else ''))
    if '$ref' in n:
        r=n['$ref'].split('/')[-1]
        if r not in seen:
            seen.add(r)
    for k,v in n.get('properties',{}).items():
        walk(v,path+'.'+k,depth+1)
    if 'items' in n and isinstance(n['items'],dict):
        walk(n['items'],path+'[]',depth+1)
    for key in ('oneOf','anyOf'):
        for i,x in enumerate(n.get(key,[])):
            if x.get('properties') or x.get('items'):
                walk(x,path+f'<{i}>',depth+1)
walk(s,'')
for k,v in defs.items():
    print('\n### def',k)
    walk(v,'#'+k)
